/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export for Azure Static Web Apps (optimal performance)
  output: 'export',

  // Disable image optimization for static hosting
  images: {
    unoptimized: true,
  },

  // Add trailing slashes for better CDN caching
  trailingSlash: true,

  // Performance optimizations
  swcMinify: true, // Use SWC for faster minification

  // Compression
  compress: true,

  // Production optimizations
  reactStrictMode: true,

  // Security headers
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin'
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()'
          }
        ],
      },
    ]
  },

  // Disable x-powered-by header for security
  poweredByHeader: false,

  // Environment variables available to the browser
  env: {
    NEXT_PUBLIC_APP_NAME: 'Boloo Admin',
    NEXT_PUBLIC_APP_VERSION: '1.0.0',
  },
}

module.exports = nextConfig
