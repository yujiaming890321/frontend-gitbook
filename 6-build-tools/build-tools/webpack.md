# webpack 常用插件

## CommonsChunkPlugin（webpack 4 removed）

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

# webpack 插件

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
