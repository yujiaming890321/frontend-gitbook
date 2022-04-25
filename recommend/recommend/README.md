# 推荐读物

## JavaScript

[You-Dont-Know-JS](https://github.com/JoeHetfield/You-Dont-Know-JS)

[Rethinking Asynchronous JavaScript 视频](https://frontendmasters.com/courses/rethinking-async-js/)

[compiler 原理](https://github.com/jamiebuilds/the-super-tiny-compiler)

[ECMAScript6 入门-ruanyifeng](https://es6.ruanyifeng.com/)

[你说你会 ES6？那你倒是用啊！！！](https://mp.weixin.qq.com/s/JTSYcs3GEHjeAodSnBXqCQ)

[ECMAScript](https://tc39.es/ecma262/)

[前端基础视频课-frontendmasters](https://frontendmasters.com/learn/)

[视频下载-frontendmasters](http://www.zwsub.com/course/Rethinking-Asynchronous-JavaScript.html)

[JavaScript 深入系列-yayu](https://github.com/mqyqingfeng/Blog)

[es module](https://hacks.mozilla.org/2018/03/es-modules-a-cartoon-deep-dive/)

[ES6 的解构赋值是深拷贝 or 浅拷贝?](https://mp.weixin.qq.com/s/qq90CbqQscltVwJXTY3qDw)

## React

[react 词汇表](https://reactjs.org/docs/glossary.html)

[react fiber 架构](https://github.com/acdlite/react-fiber-architecture)

[react lanes 设计](https://github.com/facebook/react/pull/18796)

[react 源码解析](https://react.jokcy.me/)

[react 源码小书](https://react.iamkasong.com/) [视频版](https://www.bilibili.com/video/BV1iV411b7L1)

[Build your own React](https://pomb.us/build-your-own-react/)

[eager State](https://mp.weixin.qq.com/s/zbDW3pBj-w9m59o_4SIfZA)

如果状态更新前后没有变化，则可以略过剩下的步骤。这个优化策略被称为 `eagerState`。

当前组件不存在更新，那么首次触发状态更新时，就能立刻计算出最新状态，进而与当前状态比较。

[react 18 更新优先级与 react 17区别](https://mp.weixin.qq.com/s/rb5qRsxmfG2bmYKRezX3OA)

[Demo](https://codesandbox.io/s/react-eager-state-4q8s1f)

第一次点击 div，打印

```javscript
App render 1
child render
```

1. current 与 wip 同时标记更新，render 后 wip 的「更新标记」清除。（current 有，wip 无）
2. 完成渲染后 current proess 与 wip 交换位置。（current 无，wip 有）
   第二次点击 div，打印

```javscript
App render 1
```

第二次点击 div 时，由于 wip 存在更新标记，没有命中 eagerState 3. render 后 wip 的「更新标记」清除。 （current 无，wip 无）

如果组件的子孙节点没有状态变化，可以跳过子孙组件的 render。这个优化策略被称为 `bailout`

[Dva](https://dvajs.com/)

[Umi](https://umijs.org/zh-CN)

[应用 connected-react-router 和 redux-thunk 打通 react 路由孤立](https://blog.csdn.net/qq_37648307/article/details/106456549)

[mobx 和 redux 区别](https://mp.weixin.qq.com/s/zWp-qSVeOjzHKiOYLi2s0g)

[使用 React-DnD 打造简易低代码平台](https://mp.weixin.qq.com/s/F-kUdzg7ZAKUqANd8wH6KA)

[拖拽组件：React-DnD 用法及源码解析](https://juejin.cn/post/6885511137236877325#heading-9)

[在 Vscode 里调试 React](https://mp.weixin.qq.com/s/4GZ6eB_h3ELp8qhLw8vowQ)

## Taro

[Taro 源码阅读](https://github.com/a1029563229/blogs/tree/master/Source-Code/taro)

## Vue

[从 16 个方向逐步搭建基于 vue3 的前端架构](https://zhuanlan.zhihu.com/p/428497238)

## Vue 2

[Vben Admin 一个开箱即用的前端框架](https://vvbin.cn/doc-next/)

## Css

[vanilla-extract](https://github.com/seek-oss/vanilla-extract)

## Algorithm

[算法-labuladuo](https://github.com/labuladong/fucking-algorithm)

[你管这破玩意叫哨兵？](https://mp.weixin.qq.com/s/5gj9iw3dgPlAOfrvbobzJQ)

## Python

[屏蔽自动编码器](https://github.com/facebookresearch/mae)

## [Rust](https://kaisery.github.io/trpl-zh-cn/ch01-01-installation.html)

[使用 Rust 编写更快的 React 组件](https://mp.weixin.qq.com/s/ATOySeIPWJCf9dmoxMQUIw)

[Rust 是 JS 基建的未来](https://mp.weixin.qq.com/s/hamfQVdish_0oCo6XkunhQ)

## miniprogram

[从源码看微信小程序启动过程](https://tech.youzan.com/weapp-booting/)

## 自动化测试

[2022 软件测试学习路线图](http://bbs.itheima.com/thread-405757-1-1.html)
[用 Enzyme 测试使用 Hooks 的 React 函数组件](https://zhuanlan.zhihu.com/p/148233487)
以 70%、20%、10% 的比例分别投入单元测试，集成测试和端到端测试。

- 最小化单元测试，如基础类方法、utils 工具库等
- Redux actions、reducers、effects 测试
- React 组件测试
- 端内测试（考虑到后端可能没有全流程的沙箱链路，所以使用 mock 数据测试）

[用 Enzyme 测试使用 Hooks 的 React 函数组件](https://juejin.cn/post/6844904122412433422)
[UI 自动化测试神器 Cypress](https://www.jianshu.com/p/55ed1d40f40f)

[编写第一个 React 集成测试 en](https://frontend-digest.com/write-your-first-react-integration-test-1721a8173ade)
[编写第一个 React 集成测试 cn](https://blog.csdn.net/weixin_26735933/article/details/109069784)

## Grocery 杂货铺

[clean-code](https://github.com/ryanmcdermott/clean-code-javascript)

[developer roadmap](https://roadmap.sh/roadmaps)

[前端知识总结-github](https://github.com/yujiaming890321/webKnowledge)

[TCP 系列](https://juejin.cn/post/6844904070889603085)

[HTTP 系列](https://juejin.cn/post/6844904100035821575)

[浏览器工作原理与实践-极客时间](https://time.geekbang.org/column/article/151370)

[7 分钟学会写一个浏览器插件](https://king-hcj.github.io/2021/10/17/browser-extension/)

[玩转 webpack-极客时间](https://time.geekbang.org/course/detail/100028901-109971)

[axios](https://mp.weixin.qq.com/s/Wbcjp3Lh44nrInFc3IX85w)

[前端回放系统](https://github.com/rrweb-io/rrweb/blob/master/guide.zh_CN.md)

[团队代码规范](https://juejin.cn/post/7033210664844066853)

[微前端框架-qiankun-微前端](https://mp.weixin.qq.com/s/sxmsWEq3xy8Hw-0w9cluug)
