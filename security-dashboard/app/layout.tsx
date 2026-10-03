import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AEGIS-AI SHIELD // Neural Security Command Center',
  description:
    'Deep Learning-Driven API Attack Detection and Real-Time Mitigation System. Protects victim e-commerce microservices with hybrid CNN+BiLSTM threat classification and Autoencoder anomaly detection.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
