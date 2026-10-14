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
        source: '/api/proxy/victim/:path*',
        destination: `${process.env.INTERNAL_VICTIM_URL || 'http://victim-ecommerce:8081'}/api/:path*`,
      },
      {
        source: '/api/proxy/victim-root/:path*',
        destination: `${process.env.INTERNAL_VICTIM_URL || 'http://victim-ecommerce:8081'}/:path*`,
      },
      {
        source: '/api/proxy/ml/:path*',
        destination: 'http://ml-engine:8001/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
