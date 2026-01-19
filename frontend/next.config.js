/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8889/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig
