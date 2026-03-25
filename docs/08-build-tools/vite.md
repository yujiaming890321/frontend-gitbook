# [vite](https://vite.dev/)

[CN](https://cn.vite.dev/)

Vite (French word for "quick", pronounced /vit/, like "veet") is a build tool that aims to provide a faster and leaner development experience for modern web projects. It consists of two major parts:

A dev server that provides rich feature enhancements over native ES modules, for example extremely fast Hot Module Replacement (HMR).

A build command that bundles your code with Rollup, pre-configured to output highly optimized static assets for production.

## vite fast reason

当冷启动开发服务器时

-   依赖 和 源码

    依赖 大多为在开发时不会变动的纯 JavaScript。Vite 将会使用 esbuild 预构建依赖。
    源码 通常包含一些并非直接是 JavaScript 的文件，Vite 以 原生 ESM 方式提供源码。

更新

基于打包启动时，当源文件被修改后，重新构建整个包是低效的。所以打包器支持了动态模块热替换（HMR）：允许一个模块 “热替换” 它自己。即使采用了 HMR 模式，其热更新速度也会随着应用规模的增长而显著下降。
在 Vite 中，HMR 是在原生 ESM 上执行的。当编辑一个文件时，Vite 只需要精确地使已编辑的模块与其最近的 HMR 边界之间的链失活[1]（大多数时候只是模块本身），使得无论应用大小如何，HMR 始终能保持快速更新。

打包

Vite 目前的插件 API 与使用 esbuild 作为打包器并不兼容。尽管 esbuild 速度更快，但 Vite 采用了 Rollup 灵活的插件 API 和基础建设。Rollup 切换到 SWC 改进性能

-   基于 ES Modules 的本地构建

    Vite 利用了现代浏览器对 ES Modules 的原生支持，直接在浏览器中加载和解析 ES Modules，而不需要先将所有模块打包成一个大文件

-   按需编译

    在开发模式下，Vite 只编译当前页面需要的模块，而不是整个应用程序

-   使用 Rollup 进行生产环境构建

    在开发模式下，Vite 使用了 ES Modules 的本地构建和按需编译，但在生产环境构建中，Vite 则使用了 Rollup。Rollup 是一个专门针对 ES Modules 的打包工具，能够生成更小、更快的 bundle。与传统的构建工具相比，Rollup 的打包速度通常更快。

-   预构建依赖

    在构建过程中，Vite 会预先构建依赖项，并将结果缓存起来

-   并行处理

    Vite 在构建过程中，会尽可能地并行处理多个任务，例如同时进行多个模块的编译和优化

-   使用缓存

    Vite 在构建过程中，会使用缓存来存储中间结果，避免重复计算

## vite build

-   预处理和依赖分析

    ES6 模块转换：将所有的 ES6 模块转换成 CommonJS 模块
    依赖分析：通过扫描源代码，识别出所有的依赖项

-   模块打包

    按需加载：只打包被引用的模块
    Tree Shaking
    Code Splitting：将大型模块拆分成更小的块，以便于并行加载和缓存。

-   生成静态资源

    HTML 模板处理：将 HTML 模板文件中的 <script> 标签替换为指向打包后的 JavaScript 文件的链接。
    CSS 处理：将 CSS 文件打包并最小化，生成一个单独的 CSS 文件。
    Asset 处理：处理其他类型的静态资源，如图片、字体等，确保它们可以正确地被应用程序使用。

-   优化和压缩

-   输出

## install demo

```js
// create project
npm create vite@latest // choose template
// run
npm run dev
```

## [config](https://v4.vite.dev/config/)

When running vite from the command line, Vite will automatically try to resolve a config file named vite.config.js inside project root (other JS and TS extensions are also supported).

Note Vite supports using ES modules syntax in the config file even if the project is not using native Node ESM

```js
// package.json
"type": "module",

// 如果你在 package.json 中添加了 type: "module", Node.js 将默认解析 .js 文件作为 ESM 模块。然而，这也意味着你需要使用 .mjs 扩展名来明确标记 CommonJS 模块。
```

### entry

By default, Vite will crawl all your .html files to detect dependencies that need to be pre-bundled (ignoring node_modules, build.outDir, **tests** and coverage). If build.rollupOptions.input is specified, Vite will crawl those entry points instead.

```js
//package.json
"build:test": "vite build --mode test",

//vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
    const isDev = mode === 'dev'
    return {
        plugins: [react()],
        build: {
            rollupOptions: {
                input: 'src/main.js', // 明确指定入口文件
            },
        },
    }
})
```

### esbuild

Type: ESBuildOptions | false

ESBuildOptions extends [esbuild's own transform options](https://esbuild.github.io/api/#build).

#### [drop](https://esbuild.github.io/api/#drop)

```js
export default defineConfig({
    esbuild: {
        drop: ['console', 'debugger'],
    },
})
```

## [Plugins](https://github.com/rollup/awesome)

https://tanstack.com/

### [vite-plugin-html](https://github.com/vbenjs/vite-plugin-html)

A vite plugin for processing html. It is developed based on lodash template

```js
import { defineConfig, Plugin } from 'vite'
import vue from '@vitejs/plugin-vue'

import { createHtmlPlugin } from 'vite-plugin-html'

export default defineConfig({
    plugins: [
        createHtmlPlugin({
            minify: true,
            /**
             * After writing entry here, you will not need to add script tags in `index.html`, the original tags need to be deleted
             * @default src/main.ts
             */
            entry: 'src/main.ts',
        }),
    ],
})
```

### [vite-plugin-css-injected-by-js](https://github.com/marco-prontera/vite-plugin-css-injected-by-js)

A Vite plugin that takes the CSS and adds it to the page through the JS. For those who want a single JS file.

```js
import cssInjectedByJsPlugin from 'vite-plugin-css-injected-by-js'

export default {
    plugins: [cssInjectedByJsPlugin()],
}
```

### [vite-plugin-dts](https://github.com/qmhc/vite-plugin-dts)

A Vite plugin for generating `.d.ts` files.

```js
import dts from 'vite-plugin-dts'

export default defineConfig({
    plugins: [dts()],
})
```

### [vite-plugin-svgr](https://github.com/pd4d10/vite-plugin-svgr)

Vite plugin to transform SVGs into React components.

```js
// vite.config.js
import svgr from 'vite-plugin-svgr'

export default {
    // ...
    plugins: [svgr()],
}
```

### [rollup-plugin-external-globals](https://github.com/eight04/rollup-plugin-external-globals)
