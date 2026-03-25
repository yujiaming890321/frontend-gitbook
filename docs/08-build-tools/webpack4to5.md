# webpack 4 -> 5 upgrade

## ManifestPlugin is not a constructor

调整为

```js
const { WebpackManifestPlugin } = require('webpack-manifest-plugin');
```

## Invalid options object. Ignore Plugin has been initialized using an options object that does not match the API schema.

IgnorePlugin 插件报错

```js
 - options should be one of these:
   object { resourceRegExp, contextRegExp? } | object { checkResource }
   Details:
    * options misses the property 'resourceRegExp'. Should be:
      RegExp
      -> A RegExp to test the request against.
    * options misses the property 'checkResource'. Should be:
      function
      -> A filter function for resource and context.
error Command failed with exit code 1.
```

调整为

```js
new webpack.IgnorePlugin({
    resourceRegExp: /^\.\/locale$/,
    contextRegExp: /moment$/
}),
```

Node 配置错误

```js
    * configuration.node has an unknown property 'module'. These properties are valid:
      object { __dirname?, __filename?, global? }
      -> Options object for node compatibility features.
```

[Node](https://webpack.js.org/configuration/node/)

> For Webpack version 5,
> in the webpack.config file, exclude node.js only modules using: resolve: { fallback: { fs: false } }
> For older versions of Webpack,
> in the webpack.config file, exclude node.js only modules using: node: { module: "empty", net: "empty", fs: "empty" }

在 webpack 4 中，多个 webpack 运行时可能会在同一个 HTML 页面上发生冲突，因为它们使用同一个全局变量进行代码块加载。为了解决这个问题，需要为 output.jsonpFunction 配置提供一个自定义的名称。
`output.jsonpFunction 更名为 output.chunkLoadingGlobal​​​​​​​`

`futureEmitAssets 由于Webpack5 已内置该功能，故移除配置。`
