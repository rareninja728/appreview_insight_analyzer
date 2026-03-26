/** @type {import('next').NextConfig} */
const nextConfig = {
  // Add domain allows if using external images, but none here.
  typescript: {
    // !! WARN !!
    // Dangerously allow production builds to successfully complete even if
    // your project has type errors.
    // !! WARN !!
    ignoreBuildErrors: true,
  },
}
module.exports = nextConfig
