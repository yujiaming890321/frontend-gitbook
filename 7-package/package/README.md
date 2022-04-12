### 未整理

```
"dependencies": {
    "@babel/plugin-proposal-optional-chaining": "^7.11.0", // 将可选的链式运算符转换为一系列的nil检查
    "@better-scroll/core": "^2.1.1", // 极简主义 for BetterScroll
    "@jdcfe/yep-gesture": "^0.0.3", // react 手势 component
    "@rematch/core": "^1.2.0", // A Redux Framework
    "@types/better-scroll": "^1.12.3",
    "@types/classnames": "^2.2.9",
    "@types/jest": "24.0.23",
    "@types/lodash": "^4.14.168",
    "@types/node": "12.12.7",
    "@types/raf": "^3.4.0",
    "@types/ramda": "^0.27.4",
    "@types/react": "16.9.11",
    "@types/react-dom": "16.9.4",
    "@types/react-helmet": "^5.0.14",
    "@types/react-redux": "^7.1.5",
    "@types/react-router-dom": "^5.1.3",
    "@types/react-transition-group": "^4.2.3",
    "@types/smoothscroll-polyfill": "^0.3.1",
    "@types/swiper": "^5.4.1",
    "@types/video.js": "^7.3.11",
    "add": "^2.0.6", // 跨浏览器，数值稳定的算法，以添加浮点数准确
    "antd-mobile": "^2.3.3", // antd-mobile
    "babel-plugin-import": "^1.12.2", // Component modular import plugin for babel
    "classnames": "^2.2.6", // 条件地将classname连接在一起
    "es6-promise": "^4.2.8", // This is a polyfill of the ES6 Promise
    "fetch-detector": "^1.0.1", // 本库的作用是只在 Chrome >= 46，Firefox >= 39 时才开启原生 Fetch，否则使用 XHR polyfill。 一定要与 fetch-ie8 一起使用， 并且放到 fetch-ie8 前引用。
    "fetch-ie8": "^1.5.0", // This fork supports IE8 with es5-shim, es5-sham and es6-promise.
    "fetch-jsonp": "^1.1.3", // JSONP is NOT supported in standard Fetch API
    "postcss-aspect-ratio-mini": "^1.0.1", //基于 PostCSS 生态系统，将元素的尺寸固定为纵横比
    "postcss-write-svg": "^3.0.1", // 基于 PostCSS 生态系统 css 中编写 svg
    "raf": "^3.4.1", // requestAnimationFrame polyfill for node and the browser.
    "ramda": "^0.26.1", // 函数库
    "react": "^16.12.0", // react
    "react-copy-to-clipboard": "^5.0.2", // Copy to clipboard React component
    "react-dom": "^16.12.0", // 这个包作为React的DOM和服务器呈现器的入口点。
    "react-helmet": "^5.2.1", // React component will manage all of document head.
    "react-redux": "^7.1.3", // React bindings for Redux
    "react-router-dom": "^5.1.2", // DOM bindings for React Router
    "react-scripts": "3.2.0", // This package includes scripts and configuration used by CRA.
    "redux": "^4.0.4", // redux
    "rmc-pull-to-refresh": "^1.0.13", // React Mobile PullToRefresh Component.
    "smoothscroll-polyfill": "^0.4.4", // The scroll-behavior CSS property polyfill
    "swiper": "^6.4.5", // Swiper
    "ts-jest": "^26.1.2", // lets you use Jest to test projects written in TypeScript.
    "typescript": "3.7.2", // ts
    "typescript-estree": "^18.1.0", // deprecated，将TypeScript源代码转换为ESTree兼容格式的解析器 This package was moved to @typescript-eslint/typescript-estree, please install the latest version from there instead
    "video.js": "^7.10.2", // HTML5 Video Player
    "whatwg-fetch": "^3.0.0", // window.fetch polyfill
    "yarn": "^1.19.1"
  },
  "devDependencies": {
    "@commitlint/cli": "^8.2.0", //代码检测
    "@commitlint/config-conventional": "^8.2.0", //代码检测
    "husky": "^3.1.0", // 代码检测
    "lint-staged": "^9.4.3", // git 钩子
    "prettier": "^1.19.1", // 代码美化工具


    "@types/enzyme": "^3.10.5",  // react js 测试工具
    "enzyme": "3.10.0", // react 组件 js 测试工具
    "enzyme-adapter-react-16": "1.14.0", // react 组件 js 测试工具
    "ts-jest": "^26.1.2", //测试工具
    "jest-enzyme": "7.0.2",  // react 组件 js 测试工具


    "cross-env": "^6.0.3", //跨平台运行设置和使用环境变量的脚本
    "customize-cra": "^0.9.1", //自定义CRA配置
    "react-app-rewire-less": "^2.1.3",
    "react-app-rewire-postcss": "^3.0.2",
    "react-app-rewired": "^2.1.5", //自定义CRA配置

    "speed-measure-webpack-plugin": "^1.5.0", // 优化耗时分析

    "cssnano": "^4.1.10", // 基于 PostCSS 生态系统的 CSS 压缩工具
    "cssnano-preset-advanced": "^4.0.7", // cssnano 优化工具
    "http-proxy-middleware": "^1.0.3", //代理服务器


    "redux-mock-store": "^1.5.4", // deprecated ， A mock store for testing Redux async action creators and middleware.
    "react-transition-group": "^4.4.0", // deprecated ，A set of components for managing component states (including mounting and unmounting) over time, specifically designed with animation in mind.

    "jsencrypt": "^3.0.0-rc.1",// 用于执行OpenSSL RSA加密、解密和密钥生成的Javascript库
    "lottie-web": "^5.6.8", // 移动端动画工具 Lottie is a mobile library for Web, and iOS that parses Adobe After Effects animations exported as json with Bodymovin and renders them natively on mobile!


    "webpack-scp-upload-plugin": "^1.1.0", // webpack secret copy 秘钥上传组件
    "less": "^3.10.3", // The dynamic stylesheet language.
    "less-loader": "^5.0.0", // webpack loader. Compiles Less to CSS
    "mockjs-webpack-plugin": "^3.0.1", // webpack mock plugin
    "node-cmd": "^3.0.0", //Node.js 命令行/终端
    "node-sass": "^4.13.0", // deprecated ，样式表预处理器Sass的C版本，Node sass是一个库，Node.js to LibSass
    "node-ssh-modify-nginx": "^1.1.7", // A node ssh upload&reload nginx plugin
    "postcss-cssnext": "^3.1.0",// deprecated ，基于 PostCSS 生态系统的 CSS 转换工具
    "postcss-px-to-viewport": "^1.1.1", // 将px单位转换为视口单位的 (vw, vh, vmin, vmax) 的 PostCSS 插件.
    "postcss-viewport-units": "^0.1.6", // Automatically append content property for viewport-units-buggyfill.
    "source-map-explorer": "^2.1.1",// Analyze and debug space usage through source maps
    "viewport-units-buggyfill-w": "^0.1.1", // 提供了在旧IE和Android浏览器中使用viewport单元的方法


    "babel-runtime": "^6.26.0",  // 一个编译后文件引用的公共库，可以有效减少编译后的文件体积
    "flatten": "^1.0.2", // 一个将多个数组值合并成一个数组的库
    "global": "^4.3.2",// 用于提供全局函数比如 document 的引用
    "invariant": "^2.2.1",// 一个有趣的断言库
    "is-plain-object": "^2.0.3", // 判断是否是一个对象
    "redux": "^3.7.1", // redux ，管理 react 状态的库
    "redux-saga": "^0.15.4", // 处理异步数据流
    "warning": "^3.0.0" // 同样是个断言库，不过输出的是警告
  },
```
