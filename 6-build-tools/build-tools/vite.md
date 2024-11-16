# [vite](https://vite.dev/)

[CN](https://cn.vite.dev/)

Vite (French word for "quick", pronounced /vit/, like "veet") is a build tool that aims to provide a faster and leaner development experience for modern web projects. It consists of two major parts:

A dev server that provides rich feature enhancements over native ES modules, for example extremely fast Hot Module Replacement (HMR).

A build command that bundles your code with Rollup, pre-configured to output highly optimized static assets for production.

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

## Plugins

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
