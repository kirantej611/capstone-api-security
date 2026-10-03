/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/proxy/gateway/:path*',
        destination: 'http://localhost:8080/gateway/:path*',
      },
      {
        source: '/api/proxy/victim/:path*',
        destination: 'http://localhost:8081/api/:path*',
      },
      {
        source: '/api/proxy/ml/:path*',
        destination: 'http://localhost:8001/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
