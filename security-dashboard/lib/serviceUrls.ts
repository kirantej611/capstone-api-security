const configuredGatewayUrl =
  process.env.NEXT_PUBLIC_GATEWAY_URL || 'http://localhost:8080';
const localVictimUrl = 'http://127.0.0.1:8081';

function getBrowserServiceUrl(port: number, fallbackUrl: string): string {
  if (typeof window === 'undefined') {
    return fallbackUrl;
  }

  const url = new URL(window.location.origin);
  url.port = String(port);
  return url.origin;
}

export function getGatewayUrl(): string {
  return getBrowserServiceUrl(8080, configuredGatewayUrl);
}

export function getVictimUrl(): string {
  return localVictimUrl;
}
