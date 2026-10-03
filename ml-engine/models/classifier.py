import torch
import torch.nn as nn
import torch.nn.functional as F

class HybridClassifier(nn.Module):
    """
    Hybrid CNN + BiLSTM classifier for API threat type classification.
    """
    def __init__(self, input_dim: int = 18, num_classes: int = 5):
        super(HybridClassifier, self).__init__()
        
        # CNN Block
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm1d(32)
        self.conv2 = nn.Conv1d(in_channels=32, out_channels=64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm1d(64)
        self.dropout1 = nn.Dropout(0.3)
        
        # BiLSTM Block
        self.lstm = nn.LSTM(
            input_size=64, 
            hidden_size=128, 
            num_layers=2, 
            bidirectional=True, 
            dropout=0.3, 
            batch_first=True
        )
        
        # Attention Layer
        self.attention = nn.Sequential(
            nn.Linear(256, 128),
            nn.Tanh(),
            nn.Linear(128, 1)
        )
        
        # Classifier Head
        self.fc1 = nn.Linear(256, 128)
        self.dropout2 = nn.Dropout(0.3)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, num_classes)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass returning logits.
        """
        # Reshape for Conv1d: (batch, channels, seq_len)
        if x.dim() == 2:
            x = x.unsqueeze(1)
            
        # CNN
        x = F.relu(self.bn1(self.conv1(x)))
        x = F.relu(self.bn2(self.conv2(x)))
        x = self.dropout1(x)
        
        # Prepare for LSTM: (batch, seq_len, channels)
        x = x.permute(0, 2, 1)
        
        # BiLSTM
        lstm_out, _ = self.lstm(x)  # lstm_out: (batch, seq_len, 256)
        
        # Attention
        attn_weights = self.attention(lstm_out)  # (batch, seq_len, 1)
        attn_weights = F.softmax(attn_weights, dim=1)
        
        # Weighted sum over seq_len
        context = torch.sum(attn_weights * lstm_out, dim=1)  # (batch, 256)
        
        # Classifier
        x = F.relu(self.fc1(context))
        x = self.dropout2(x)
        x = F.relu(self.fc2(x))
        logits = self.fc3(x)
        
        return logits
        
    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """
        Returns softmax probabilities.
        """
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            probs = F.softmax(logits, dim=1)
        return probs
        
    def get_attention_weights(self, x: torch.Tensor) -> torch.Tensor:
        """
        Returns attention weights for explainability.
        """
        self.eval()
        with torch.no_grad():
            if x.dim() == 2:
                x = x.unsqueeze(1)
            x = F.relu(self.bn1(self.conv1(x)))
            x = F.relu(self.bn2(self.conv2(x)))
            x = self.dropout1(x)
            x = x.permute(0, 2, 1)
            lstm_out, _ = self.lstm(x)
            attn_weights = self.attention(lstm_out)
            attn_weights = F.softmax(attn_weights, dim=1)
        return attn_weights
