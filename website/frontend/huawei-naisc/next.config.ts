/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone', // Optimizes for Docker
  reactStrictMode: true,
  
  async rewrites() {
    return [
      {
        // Proxying API requests to the backend
        source: '/api/:path*',
        destination: process.env.BACKEND_API_URL + '/:path*'
      }
    ]
  },
  
  // Optional: Configure image domains if using Next.js Image
  images: {
    domains: ['localhost'],
  },
}

module.exports = nextConfig