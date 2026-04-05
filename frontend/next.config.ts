import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: process.env.NEXT_OUTPUT === 'standalone' ? 'standalone' : undefined,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.API_URL ?? 'http://localhost:8000'}/api/:path*`,
      },
    ]
  },
}

export default nextConfig
