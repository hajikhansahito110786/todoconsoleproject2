/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: false, // Disable app directory for now to use pages
  },
  output: 'export', // Export as static files
  trailingSlash: true, // Add trailing slashes to URLs
  images: {
    unoptimized: true, // Disable image optimization for export
  },
};

module.exports = nextConfig;