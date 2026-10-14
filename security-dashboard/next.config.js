/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/proxy/gateway/:path*',
        destination: `${process.env.INTERNAL_GATEWAY_URL || 'http://api-gateway:8080'}/gateway/:path*`,
      },
      {
        source: '/api/proxy/gateway-root/:path*',
        destination: `${process.env.INTERNAL_GATEWAY_URL || 'http://api-gateway:8080'}/:path*`,
      },
      {
        source: '/api/proxy/ml/:path*',
        destination: 'http://ml-engine:8001/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
