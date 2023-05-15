const { defineConfig } = require('@vue/cli-service')
// const CompressionPlugin = require("compression-webpack-plugin");
module.exports = defineConfig({
  publicPath: '/mpr/',
  transpileDependencies: true,
  productionSourceMap: false,
  devServer: {
    host: 'localhost',
    port: 8080,
    open: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:5000",
        ws: true, // websockets
        changOrigin: true,
        pathRewrite: {
          '^/api': ''
        }
      }
    }
  },
  // configureWebpack: {
  //   plugins: [
  //     new CompressionPlugin({
  //       algorithm: 'gzip',
  //       test: /\.js$|\.html$|\.css$/,
  //       filename: '[path][base].gz[query]',
  //       minRatio: 1,
  //       threshold: 10240,
  //       deleteOriginalAssets: false,
  //     }),
  //   ]
  // }
})
