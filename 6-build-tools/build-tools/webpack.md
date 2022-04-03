# webpack 常用配置

### 静态资源使用强缓存
文件名使用`消息摘要算法`
```
output: {
    filename: 'bundle.[name][hash:8].js',
    publicPath,
}
```

### HtmlWebpackPlugin CDN配置
HtmlWebpackPlugin 修改为 cdn 路径
```
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

### CommonsChunkPlugin（webpack 4 removed）

负责将多次被使用的 JS 模块打包在一起

- 传入字符串参数

```
// 提供公共代码
new webpack.optimize.CommonsChunkPlugin('common.js'), // 默认会把所有入口节点的公共代码提取出来,生成一个common.js
```

- 有选择的提取

```
// 提供公共代码
// 默认会把所有入口节点的公共代码提取出来,生成一个common.js
// 只提取main节点和index节点
new webpack.optimize.CommonsChunkPlugin('common.js',['main','index']),
```

- 有选择性的提取（对象方式传参）

```
// 通过CommonsChunkPlugin，我们把公共代码专门抽取到一个common.js，这样业务代码只在index.js，main.js，user.js
new webpack.optimize.CommonsChunkPlugin({
  name:'common', // 注意不要.js后缀
  chunks:['main','user','index']
}),
```

### DefinePlugin 定义全局变量

```
new webpack.DefinePlugin({
    NAME1: JSON.stringify(process.env.NAME1),
    NAME2: JSON.stringify(process.env.NAME2)
})
```

### webpack-bundle-analyzer 文件可视化分析工具

```
plugins: [
  new BundleAnalyzerPlugin(),
],
```

### speed-measure-webpack-plugin 优化耗时分析

```
const SpeedMeasurePlugin=require('speed-measure-webpack-plugin')

const smp = new SpeedMeasurePlugin();
smp.wrap( webpackConfig )
```

### @babel/plugin-proposal-optional-chaining 可选链操作符 ?.

```
plugins: [
  @babel/plugin-proposal-optional-chaining
],
```

### @babel/plugin-proposal-nullish-coalescing-operator 空位合并运算符 ??

```
plugins: [
  @babel/plugin-proposal-nullish-coalescing-operator
],
```

### @babel/plugin-proposal-pipeline-operator 管道运算符 |>

```
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
