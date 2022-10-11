# webpack 常用配置

webpack4 2018 Feb release. major change: remove commonsChunk.

webpack5 2020 Oct release. major change: Long Term Caching.

## 获取commitHash

```js
const { execSync } = require('child_process');
let commitHash;

try {
  commitHash = execSync('git rev-parse --short HEAD').toString();
} catch (error) {
  console.log(error);
  commitHash = 'N/A';
}
```

## 静态资源使用强缓存

文件名使用`消息摘要算法`

```js
output: {
    filename: 'bundle.[name][hash:8].js',
    publicPath,
}
```

## HtmlWebpackPlugin CDN配置

HtmlWebpackPlugin 修改为 cdn 路径

```js
// webpack.config.js
const CDN_HOST = process.env.CDN_HOST;// CDN 域名
const CDN_PATH = process.env.CDN_PATH; // CDN 路径
const ENV = process.env.ENV; // 当前的环境等等
const VERSION = process.env.VERSION; // 当前发布的版本

const getPublicPath = () => {
    // Some code here
    return `${CDN_HOST}/${CDN_PATH}/${ENV}/`;// 依据 ENV 等动态构造 publicPath
}

const publicPath = process.env.NODE_ENV === 'production' ? getPublicPath() : '.';

module.exports = {
    output: {
        filename: 'bundle.[name][hash:8].js',
        publicPath,
    },
    plugins: [
        new HtmlWebpackPlugin()
    ]
}
```

## CommonsChunkPlugin（webpack 4 removed）

负责将多次被使用的 JS 模块打包在一起

- 传入字符串参数

```js
// 提供公共代码
new webpack.optimize.CommonsChunkPlugin('common.js'), // 默认会把所有入口节点的公共代码提取出来,生成一个common.js
```

- 有选择的提取

```js
// 提供公共代码
// 默认会把所有入口节点的公共代码提取出来,生成一个common.js
// 只提取main节点和index节点
new webpack.optimize.CommonsChunkPlugin('common.js',['main','index']),
```

- 有选择性的提取（对象方式传参）

```js
// 通过CommonsChunkPlugin，我们把公共代码专门抽取到一个common.js，这样业务代码只在index.js，main.js，user.js
new webpack.optimize.CommonsChunkPlugin({
  name:'common', // 注意不要.js后缀
  chunks:['main','user','index']
}),
```

## DefinePlugin 定义全局变量

```js
new webpack.DefinePlugin({
    NAME1: JSON.stringify(process.env.NAME1),
    NAME2: JSON.stringify(process.env.NAME2)
})
```

## BannerPlugin 版权声明

```js
new webpack.BannerPlugin(
  `
  Bundle: Standalone
  Version: ${commitHash}
  `
),
```

## MiniCssExtractPlugin css-in-js css提取file

```js
const plugins = [
  new MiniCssExtractPlugin({
    filename: '[name].styles.min.css?[contenthash]',
  }),
]

rules: [
  {
    test: /\.(scss|css)$/,
    use: [
      MiniCssExtractPlugin.loader,
      'css-loader',
      'postcss-loader',
    ],
  },
]
```

## [TerserPlugin](https://webpack.js.org/plugins/terser-webpack-plugin) 压缩JS

```js
const TerserPlugin = require("terser-webpack-plugin");

module.exports = {
  optimization: {
    minimize: true,
    minimizer: [new TerserPlugin({
      parallel: true,
      exclude: /node_modules/,
      terserOptions: {
        toplevel: true,
      },
    })],
  },
};
```

## [CssMinimizerWebpackPlugin](https://webpack.js.org/plugins/css-minimizer-webpack-plugin/) 压缩css

```js
const CssMinimizerPlugin = require("css-minimizer-webpack-plugin");

module.exports = {
  optimization: {
    minimize: true,
    minimizer: [new CssMinimizerPlugin()],
  },
};
```

## webpack-bundle-analyzer 文件可视化分析工具

```js
plugins: [
  new BundleAnalyzerPlugin(),
],
```

## speed-measure-webpack-plugin 优化耗时分析

```js
const SpeedMeasurePlugin=require('speed-measure-webpack-plugin')

const smp = new SpeedMeasurePlugin();
smp.wrap( webpackConfig )
```

## @babel/plugin-proposal-optional-chaining 可选链操作符 ?.

```js
plugins: [
  @babel/plugin-proposal-optional-chaining
],
```

## @babel/plugin-proposal-nullish-coalescing-operator 空位合并运算符 ??

```js
plugins: [
  @babel/plugin-proposal-nullish-coalescing-operator
],
```

## @babel/plugin-proposal-pipeline-operator 管道运算符 |>

```js
plugins: [
  ["@babel/plugin-proposal-pipeline-operator", { "topicToken": "^^" }]
],

// Status quo
jQuery.merge( this, jQuery.parseHTML(
  match[ 1 ],
  context && context.nodeType ? context.ownerDocument || context : document,
  true
) );

// With pipes
context
  |> (^^ && ^^.nodeType ? ^^.ownerDocument || ^^ : document)
  |> jQuery.parseHTML(match[1], ^^, true)
  |> jQuery.merge(^^);
```
