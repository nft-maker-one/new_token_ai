const path = require('path');

module.exports = {
  webpack: {
    configure: (webpackConfig, { env, paths }) => {
      // 修复allowedHosts问题
      if (webpackConfig.devServer) {
        webpackConfig.devServer.allowedHosts = 'all';
        webpackConfig.devServer.host = 'localhost';
        webpackConfig.devServer.port = 3000;
        webpackConfig.devServer.client = {
          webSocketURL: {
            hostname: 'localhost',
            pathname: '/ws',
            port: 3000,
          },
        };
      }
      return webpackConfig;
    },
  },
  devServer: {
    allowedHosts: 'all',
    host: 'localhost',
    port: 3000,
  },
};
