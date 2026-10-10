import torch
import torch.nn as nn
import torch.nn.functional as F


class ResidualBlock(nn.Module):
    """Residual block with LayerNorm and GELU."""
    def __init__(self, dim: int, dropout: float = 0.2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, dim),
            nn.LayerNorm(dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(dim, dim),
            nn.LayerNorm(dim),
        )
        self.act = nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.act(self.net(x) + x)


class VariationalAutoencoder(nn.Module):
    """
    Variational Autoencoder (VAE) for anomaly detection in API traffic.

    Improvements over the original DeepAutoencoder:
    - KL-divergence regularisation for smoother latent space
    - Residual blocks for deeper, more stable training
    - Multi-scale reconstruction loss (intermediate decoder layers)
    - Skip connections between matched encoder/decoder layers
    - Separate mu/logvar heads (proper variational inference)
    - Gaussian noise injection during training (denoising VAE)
    - Tighter bottleneck (latent_dim=8) for better anomaly separation
    """

    def __init__(self, input_dim: int = 42, latent_dim: int = 8, dropout: float = 0.2):
        super().__init__()
        self.input_dim = input_dim
        self.latent_dim = latent_dim

        # ── Encoder ──────────────────────────────────────────
        self.enc1 = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.LayerNorm(128),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.enc_res1 = ResidualBlock(128, dropout)

        self.enc2 = nn.Sequential(
            nn.Linear(128, 64),
            nn.LayerNorm(64),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.enc_res2 = ResidualBlock(64, dropout)

        self.enc3 = nn.Sequential(
            nn.Linear(64, 32),
            nn.LayerNorm(32),
            nn.GELU(),
        )

        # Variational heads
        self.fc_mu = nn.Linear(32, latent_dim)
        self.fc_logvar = nn.Linear(32, latent_dim)

        # ── Decoder (mirrors encoder) ────────────────────────
        self.dec0 = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.LayerNorm(32),
            nn.GELU(),
        )

        # Skip connections add encoder dims to decoder input dims
        self.dec1 = nn.Sequential(
            nn.Linear(32 + 32, 64),  # +32 from enc3 skip
            nn.LayerNorm(64),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.dec_res1 = ResidualBlock(64, dropout)

        self.dec2 = nn.Sequential(
            nn.Linear(64 + 64, 128),  # +64 from enc2 skip
            nn.LayerNorm(128),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.dec_res2 = ResidualBlock(128, dropout)

        self.dec3 = nn.Linear(128 + 128, input_dim)  # +128 from enc1 skip

        # Multi-scale reconstruction heads (for auxiliary losses)
        self.ms_head_64 = nn.Linear(64, input_dim)
        self.ms_head_128 = nn.Linear(128, input_dim)

    def encode(self, x: torch.Tensor):
        """Encode input and return mu, logvar, and intermediate activations for skip connections."""
        h1 = self.enc_res1(self.enc1(x))        # (B, 128)
        h2 = self.enc_res2(self.enc2(h1))        # (B, 64)
        h3 = self.enc3(h2)                       # (B, 32)
        mu = self.fc_mu(h3)                       # (B, latent_dim)
        logvar = self.fc_logvar(h3)               # (B, latent_dim)
        return mu, logvar, (h1, h2, h3)

    def reparameterize(self, mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        """Reparameterisation trick: z = mu + eps * sigma."""
        if self.training:
            std = torch.exp(0.5 * logvar)
            eps = torch.randn_like(std)
            return mu + eps * std
        return mu  # deterministic at inference

    def decode(self, z: torch.Tensor, skips: tuple):
        """Decode latent vector using skip connections. Returns final + multi-scale reconstructions."""
        h1_enc, h2_enc, h3_enc = skips

        d0 = self.dec0(z)                                    # (B, 32)
        d1 = self.dec_res1(self.dec1(torch.cat([d0, h3_enc], dim=1)))  # (B, 64)
        d2 = self.dec_res2(self.dec2(torch.cat([d1, h2_enc], dim=1)))  # (B, 128)
        reconstruction = self.dec3(torch.cat([d2, h1_enc], dim=1))     # (B, input_dim)

        # Multi-scale reconstructions
        ms_64 = self.ms_head_64(d1)    # (B, input_dim) from 64-dim
        ms_128 = self.ms_head_128(d2)  # (B, input_dim) from 128-dim

        return reconstruction, ms_64, ms_128

    def forward(self, x: torch.Tensor, noise_std: float = 0.0):
        """
        Full forward pass.

        Args:
            x: Input tensor (B, input_dim)
            noise_std: Standard deviation of Gaussian noise to inject into the
                       input during training.  Acts as a denoising regulariser —
                       the model must reconstruct the clean signal from a
                       corrupted input, which increases reconstruction error
                       for out-of-distribution (attack) samples at inference.

        Returns: reconstruction, mu, logvar, ms_64, ms_128
        """
        # Inject Gaussian noise during training for denoising robustness
        if self.training and noise_std > 0:
            x_input = x + torch.randn_like(x) * noise_std
        else:
            x_input = x

        mu, logvar, skips = self.encode(x_input)
        z = self.reparameterize(mu, logvar)
        reconstruction, ms_64, ms_128 = self.decode(z, skips)
        return reconstruction, mu, logvar, ms_64, ms_128

    def get_reconstruction_error(self, x: torch.Tensor) -> torch.Tensor:
        """
        Compute per-sample anomaly score.
        Combines main reconstruction MSE + KL divergence as a composite score.
        """
        self.eval()
        with torch.no_grad():
            reconstruction, mu, logvar, _, _ = self.forward(x)
            # Per-sample MSE
            mse = torch.mean((x - reconstruction) ** 2, dim=1)
            # Per-sample KL divergence (averaged over latent dims)
            kl = -0.5 * torch.mean(1 + logvar - mu.pow(2) - logvar.exp(), dim=1)
            # Composite anomaly score (weighted)
            anomaly_score = mse + 0.1 * kl
        return anomaly_score

    def get_latent(self, x: torch.Tensor) -> torch.Tensor:
        """Returns the latent mu representation (deterministic)."""
        self.eval()
        with torch.no_grad():
            mu, _, _ = self.encode(x)
        return mu


def vae_loss(reconstruction, x, mu, logvar, ms_64, ms_128, beta: float = 1.0):
    """
    Combined VAE loss with multi-scale reconstruction.

    L = L_recon_main + 0.3*L_recon_64 + 0.3*L_recon_128 + beta * L_KL
    """
    # Main reconstruction loss
    recon_main = F.mse_loss(reconstruction, x, reduction='mean')

    # Multi-scale reconstruction losses (auxiliary)
    recon_64 = F.mse_loss(ms_64, x, reduction='mean')
    recon_128 = F.mse_loss(ms_128, x, reduction='mean')

    # KL divergence
    kl = -0.5 * torch.mean(1 + logvar - mu.pow(2) - logvar.exp())

    total = recon_main + 0.3 * recon_64 + 0.3 * recon_128 + beta * kl
    return total, recon_main, kl


# ── Backward compatibility alias ──────────────────────────────────────
# Keep DeepAutoencoder as alias so existing code doesn't break during migration
DeepAutoencoder = VariationalAutoencoder
