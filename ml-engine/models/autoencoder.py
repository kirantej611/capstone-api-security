import torch
import torch.nn as nn

class DeepAutoencoder(nn.Module):
    """
    A Deep Autoencoder for anomaly detection in API traffic.
    """
    def __init__(self, input_dim: int = 18):
        super(DeepAutoencoder, self).__init__()
        
        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.BatchNorm1d(64),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.BatchNorm1d(32),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 8)  # Latent space
        )
        
        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.BatchNorm1d(16),
            nn.Linear(16, 32),
            nn.ReLU(),
            nn.BatchNorm1d(32),
            nn.Dropout(0.2),
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.Linear(64, input_dim)
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass of the autoencoder.
        """
        latent = self.encoder(x)
        reconstruction = self.decoder(latent)
        return reconstruction
    
    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """
        Returns the latent representation.
        """
        return self.encoder(x)
    
    def get_reconstruction_error(self, x: torch.Tensor) -> torch.Tensor:
        """
        Computes the Mean Squared Error (MSE) per sample.
        This serves as the anomaly score.
        """
        self.eval()
        with torch.no_grad():
            reconstruction = self.forward(x)
            mse = torch.mean((x - reconstruction) ** 2, dim=1)
        return mse
