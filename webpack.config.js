const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const { VueLoaderPlugin } = require('vue-loader');
const TerserPlugin = require('terser-webpack-plugin');

module.exports = (env = {}, argv = {}) => {
  const mode = argv.mode || process.env.NODE_ENV || 'development';
  const isProduction = mode === 'production';

  return {
    mode,
    entry: {
      'site-base': './assets/site-base.js',  // base styles shared between frameworks
      'site-bulma': './assets/site-bulma.js',  // required for bulma styles
      site: './assets/javascript/site.js',  // global site javascript
      app: './assets/javascript/app.js',  // logged-in javascript
      pegasus: './assets/javascript/pegasus/pegasus.js',
      'react-object-lifecycle': './assets/javascript/pegasus/examples/react/react-object-lifecycle.js',
      'vue-object-lifecycle': './assets/javascript/pegasus/examples/vue/vue-object-lifecycle.js',
      'chat': './assets/javascript/chat/chat.js',
    },
    output: {
      path: path.resolve(__dirname, './static'),
      filename: 'js/[name]-bundle.js',
      library: ['SiteJS', '[name]'],
      clean: false,  // keep existing assets while watching
    },
    cache: {
      type: 'filesystem',
      buildDependencies: {
        config: [__filename],
      },
    },
    resolve: {
      extensions: ['.js', '.jsx', '.ts', '.tsx'],
    },
    module: {
      rules: [
        {
          test: /\.vue$/,
          loader: 'vue-loader',
        },
        {
          test: /\.(js|jsx|ts|tsx)$/,
          exclude: /node_modules/,
          use: {
            loader: 'babel-loader',
            options: {
              cacheDirectory: true,
              cacheCompression: false,
              presets: [
                '@babel/preset-env',
                '@babel/preset-react',
                '@babel/preset-typescript',
              ],
            },
          },
        },
        {
          test: /\.scss$/,
          use: [
            MiniCssExtractPlugin.loader,
            {
              loader: 'css-loader',
              options: {
                sourceMap: !isProduction,
              },
            },
            {
              loader: 'sass-loader',
              options: {
                sourceMap: !isProduction,
              },
            },
          ],
        },
      ],
    },
    plugins: [
      new MiniCssExtractPlugin({
        filename: 'css/[name].css',
      }),
      new VueLoaderPlugin(),
    ],
    optimization: isProduction
      ? {
          minimizer: [
            new TerserPlugin({
              extractComments: false,  // disable generation of license.txt files
            }),
          ],
        }
      : {
          removeAvailableModules: false,
          runtimeChunk: false,
        },
    watchOptions: {
      ignored: [
        '**/node_modules/**',
        '**/static/**',
        '**/media/**',
      ],
    },
    stats: 'errors-warnings',
    devtool: isProduction ? 'source-map' : 'eval-cheap-module-source-map',
    infrastructureLogging: {
      level: 'warn',
    },
  };
};
