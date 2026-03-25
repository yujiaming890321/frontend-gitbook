# webpack

## webpack build

-   初始化

    创建 Compiler 对象

-   解析入口

    从配置文件中指定的入口文件开始，解析出所有的依赖关系

-   构建模块依赖

    递归地解析每个依赖项，直到找到所有的依赖项

-   模块编译

    根据模块依赖图，逐个编译每个模块

-   生成文件

    打包成一个或多个 bundle，同时进行去除冗余代码、压缩代码

-   输出

    将生成的 bundle 输出

webpack4 2018 Feb release. major change: remove commonsChunk.

webpack5 2020 Oct release. major change: Long Term Caching.

https://www.cnblogs.com/dashnowords/category/1284284.html

## Config

### 获取 commitHash

```js
const { execSync } = require('child_process')
let commitHash

try {
    commitHash = execSync('git rev-parse --short HEAD').toString()
} catch (error) {
    console.log(error)
    commitHash = 'N/A'
}
```

### 静态资源使用强缓存

文件名使用`消息摘要算法`

```js
output: {
    filename: 'bundle.[name][hash:8].js',
    publicPath,
}
```

## Loader

1.文件

val-loader：将代码作为模块执行，并将其导出为 js 代码
ref-loader：用于手动建立文件之间的依赖关系
raw-loader：加载文件原始内容(utf-8)

2.JSON

cson-loader：加载并转换 CSON 文件

3.语法转换

babel-loader：使用 babel 加载 es5+代码转换为 es5
buble-loader：使用 buble 加载 es5+代码转换为 es5
traceur-loader：使用 traceur 加载 es5+代码转换为 es5
ts-loader：像加载 js 一样加载 ts2.0+
coffee-loader：像加载 js 一样加载 coffeeScript
fengari-loader：使用 fengari 加载 lua 代码
elm-webpack-loader：像加载 js 一样加载 Elm

4.模板

html-loader：将 html 导出为字符串，需要传入静态资源引用路径
pug-loader：加载 pug 和 jade 模板并返回一个函数
markdown-loader：将 markdown 编译为 html
react-markdown-loader：使用 markdown-parse 解析器将 markdown 编译为 React 组件
posthtml-loader：使用 posthtml 加载并转换为 html 文件
handlebars-loader：将 handlebars 文件编译为 html
markup-inline-loader：将 svg/mathML 文件嵌套到 html 中
twing-loader：编译 twig 模板并返回一个函数
remark-loader：通过 remark 加载 markdown，且支持解析内容中的图片

5.样式

style-loader：将模块导出的内容作为样式并添加到 dom 中
css-loader：加载 css 文件并解析 import 的 css 文件，最终返回 css 代码
less-loader：加载并编译 less 文件
sass-loader：加载并编译 sass/scss 文件
postcss-loader：使用 postcss 加载并转换 css/sss 文件
stylus-loader：加载并编译 stylus 文件

6.框架

vue-loader：加载并编译 vue 组件
angular2-template-loader：加载并编译 angular 组件

## Plugin

### HtmlWebpackPlugin CDN 配置

HtmlWebpackPlugin 修改为 cdn 路径

```js
// webpack.config.js
const CDN_HOST = process.env.CDN_HOST // CDN 域名
const CDN_PATH = process.env.CDN_PATH // CDN 路径
const ENV = process.env.ENV // 当前的环境等等
const VERSION = process.env.VERSION // 当前发布的版本

const getPublicPath = () => {
    // Some code here
    return `${CDN_HOST}/${CDN_PATH}/${ENV}/` // 依据 ENV 等动态构造 publicPath
}

const publicPath = process.env.NODE_ENV === 'production' ? getPublicPath() : '.'

module.exports = {
    output: {
        filename: 'bundle.[name][hash:8].js',
        publicPath,
    },
    plugins: [new HtmlWebpackPlugin()],
}
```

### CommonsChunkPlugin（webpack 4 removed）

负责将多次被使用的 JS 模块打包在一起

-   传入字符串参数

```js
// 提供公共代码
new webpack.optimize.CommonsChunkPlugin('common.js'), // 默认会把所有入口节点的公共代码提取出来,生成一个common.js
```

-   有选择的提取

```js
// 提供公共代码
// 默认会把所有入口节点的公共代码提取出来,生成一个common.js
// 只提取main节点和index节点
new webpack.optimize.CommonsChunkPlugin('common.js',['main','index']),
```

-   有选择性的提取（对象方式传参）

```js
// 通过CommonsChunkPlugin，我们把公共代码专门抽取到一个common.js，这样业务代码只在index.js，main.js，user.js
new webpack.optimize.CommonsChunkPlugin({
  name:'common', // 注意不要.js后缀
  chunks:['main','user','index']
}),
```

### DefinePlugin 定义全局变量

```js
new webpack.DefinePlugin({
    NAME1: JSON.stringify(process.env.NAME1),
    NAME2: JSON.stringify(process.env.NAME2),
})
```

### [ProvidePlugin](https://webpack.js.org/plugins/provide-plugin/#root) 在使用时将不再需要 import 和 require 进行引入，直接使用即可

```js
plugins: [
    new webpack.ProvidePlugin({
        api: 'api',
    }),
]
```

### BannerPlugin 版权声明

```js
new webpack.BannerPlugin(
  `
  Bundle: Standalone
  Version: ${commitHash}
  `
),
```

### [MiniCssExtractPlugin](https://www.npmjs.com/package/mini-css-extract-plugin) css-in-js css 提取 file

```js
const plugins = [
  new MiniCssExtractPlugin({
    filename: '[name].styles.min.css?[contenthash]',
  }),
]

plugins: plugins,
module: {
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
},
```

### [TerserPlugin](https://webpack.js.org/plugins/terser-webpack-plugin) 压缩 JS

```js
const TerserPlugin = require('terser-webpack-plugin')

module.exports = {
    optimization: {
        minimize: true,
        minimizer: [
            new TerserPlugin({
                parallel: true,
                exclude: /node_modules/,
                terserOptions: {
                    toplevel: true,
                },
            }),
        ],
    },
}
```

### [CssMinimizerWebpackPlugin](https://webpack.js.org/plugins/css-minimizer-webpack-plugin/) 压缩 css

```js
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin')

module.exports = {
    optimization: {
        minimize: true,
        minimizer: [new CssMinimizerPlugin()],
    },
}
```

### [OptimizeCSSAssetsPlugin](https://github.com/NMFR/optimize-css-assets-webpack-plugin) 压缩 css

webpack v4
For webpack v5 or above please use css-minimizer-webpack-plugin instead.

```js
const OptimizeCSSAssetsPlugin = require('optimize-css-assets-webpack-plugin')

module.exports = {
    optimization: {
        minimize: true,
        minimizer: [new OptimizeCSSAssetsPlugin()],
    },
}
```

### webpack-bundle-analyzer 文件可视化分析工具

```js
plugins: [
  new BundleAnalyzerPlugin(),
],
```

### speed-measure-webpack-plugin 优化耗时分析

```js
const SpeedMeasurePlugin = require('speed-measure-webpack-plugin')

const smp = new SpeedMeasurePlugin()
smp.wrap(webpackConfig)
```

### @babel/plugin-proposal-optional-chaining 可选链操作符 ?.

```js
plugins: [
  "@babel/plugin-proposal-optional-chaining"
],
```

### @babel/plugin-proposal-nullish-coalescing-operator 空位合并运算符 ??

```js
plugins: [
  "@babel/plugin-proposal-nullish-coalescing-operator"
],
```

### @babel/plugin-proposal-pipeline-operator 管道运算符 |>

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
