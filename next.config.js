/** @type {import('next').NextConfig} */
const nextConfig = {
  webpack: (config, { isServer }) => {
    // Fix canvas dependency issues for react-pdf
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        path: false,
        os: false,
        stream: false,
        util: false,
        buffer: false,
        url: false,
        querystring: false,
        canvas: false,
      };
    }
    
    // Handle canvas module
    config.externals = config.externals || [];
    config.externals.push({
      'canvas': 'canvas'
    });
    
    return config;
  },
}

module.exports = nextConfig
