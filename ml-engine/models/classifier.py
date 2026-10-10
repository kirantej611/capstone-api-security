import torch
import torch.nn as nn
import torch.nn.functional as F


class ResidualMLPBlock(nn.Module):
    """
    Residual block for tabular data.
    Linear → LayerNorm → GELU → Dropout → Linear → skip
    """
    def __init__(self, in_dim: int, hidden_dim: int, dropout: float = 0.3):
        super().__init__()
        self.proj = nn.Linear(in_dim, hidden_dim) if in_dim != hidden_dim else nn.Identity()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
        )
        self.act = nn.GELU()
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = self.proj(x)
        return self.act(self.dropout(self.net(x)) + residual)


class FeatureGroupAttention(nn.Module):
    """
    Multi-head self-attention over feature groups.
    Splits features into groups and applies attention to learn
    inter-group dependencies (e.g., SQL features vs encoding features).
    """
    def __init__(self, feature_dim: int, num_heads: int = 4, dropout: float = 0.1):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = feature_dim // num_heads
        assert feature_dim % num_heads == 0, f"feature_dim ({feature_dim}) must be divisible by num_heads ({num_heads})"

        self.q_proj = nn.Linear(feature_dim, feature_dim)
        self.k_proj = nn.Linear(feature_dim, feature_dim)
        self.v_proj = nn.Linear(feature_dim, feature_dim)
        self.out_proj = nn.Linear(feature_dim, feature_dim)
        self.dropout = nn.Dropout(dropout)
        self.norm = nn.LayerNorm(feature_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (B, feature_dim)"""
        B = x.size(0)
        residual = x

        # Reshape to (B, num_heads, head_dim) for multi-head attention
        q = self.q_proj(x).view(B, self.num_heads, self.head_dim)
        k = self.k_proj(x).view(B, self.num_heads, self.head_dim)
        v = self.v_proj(x).view(B, self.num_heads, self.head_dim)

        # Scaled dot-product attention across heads
        scale = self.head_dim ** 0.5
        attn = torch.matmul(q, k.transpose(-2, -1)) / scale  # (B, H, H)
        attn = F.softmax(attn, dim=-1)
        attn = self.dropout(attn)

        out = torch.matmul(attn, v)  # (B, H, head_dim)
        out = out.reshape(B, -1)     # (B, feature_dim)
        out = self.out_proj(out)

        return self.norm(out + residual)


class DeepResidualClassifier(nn.Module):
    """
    Deep Residual MLP with Feature-Group Attention for API threat classification.

    Architecture:
        Input(42) → ResBlock(128) → ResBlock(256) → Attention(256) →
        ResBlock(128) → ResBlock(64) → Classifier Head → num_classes

    Improvements over the original CNN+BiLSTM:
    - Proper tabular architecture (not forcing sequence-model on fixed features)
    - Residual connections for stable deep training
    - LayerNorm + GELU (more stable than BatchNorm + ReLU for tabular)
    - Multi-head feature attention for learned feature interactions
    - Focal loss compatible (outputs raw logits)
    """
    def __init__(self, input_dim: int = 42, num_classes: int = 6, dropout: float = 0.3):
        super().__init__()

        # Input projection
        self.input_proj = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.LayerNorm(128),
            nn.GELU(),
            nn.Dropout(dropout),
        )

        # Residual tower (ascending)
        self.res1 = ResidualMLPBlock(128, 128, dropout)
        self.res2 = ResidualMLPBlock(128, 256, dropout)

        # Feature-group attention
        self.attention = FeatureGroupAttention(256, num_heads=4, dropout=dropout * 0.5)

        # Residual tower (descending)
        self.res3 = ResidualMLPBlock(256, 128, dropout)
        self.res4 = ResidualMLPBlock(128, 64, dropout)

        # Classification head
        self.head = nn.Sequential(
            nn.Linear(64, 32),
            nn.LayerNorm(32),
            nn.GELU(),
            nn.Dropout(dropout * 0.5),
            nn.Linear(32, num_classes),
        )

        # Store attention weights for explainability
        self._last_attn_weights = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass returning logits. Input: (B, input_dim)."""
        # Handle legacy 3D input from old pipeline (B, 1, D) → (B, D)
        if x.dim() == 3:
            x = x.squeeze(1)

        h = self.input_proj(x)          # (B, 128)
        h = self.res1(h)                # (B, 128)
        h = self.res2(h)                # (B, 256)
        h = self.attention(h)           # (B, 256)
        h = self.res3(h)                # (B, 128)
        h = self.res4(h)                # (B, 64)
        logits = self.head(h)           # (B, num_classes)
        return logits

    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """Returns softmax probabilities."""
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            probs = F.softmax(logits, dim=1)
        return probs

    def get_embeddings(self, x: torch.Tensor) -> torch.Tensor:
        """Returns the 64-dim penultimate layer embeddings for downstream use."""
        self.eval()
        with torch.no_grad():
            if x.dim() == 3:
                x = x.squeeze(1)
            h = self.input_proj(x)
            h = self.res1(h)
            h = self.res2(h)
            h = self.attention(h)
            h = self.res3(h)
            h = self.res4(h)
        return h


class FocalLoss(nn.Module):
    """
    Focal Loss for addressing class imbalance.
    Reduces the loss contribution from easy examples and focuses on hard ones.

    FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)

    Supports optional label smoothing which prevents the model from
    becoming overconfident and improves calibration.
    """
    def __init__(self, alpha: torch.Tensor = None, gamma: float = 2.0,
                 reduction: str = 'mean', label_smoothing: float = 0.0):
        super().__init__()
        self.alpha = alpha  # per-class weights
        self.gamma = gamma
        self.reduction = reduction
        self.label_smoothing = label_smoothing

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        ce_loss = F.cross_entropy(
            logits, targets, weight=self.alpha, reduction='none',
            label_smoothing=self.label_smoothing
        )
        pt = torch.exp(-ce_loss)  # p_t = exp(-CE)
        focal_loss = (1 - pt) ** self.gamma * ce_loss

        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        return focal_loss


# ── Backward compatibility alias ──────────────────────────────────────
HybridClassifier = DeepResidualClassifier
