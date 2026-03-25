# Vue

命令式：关注过程 （js）
声明式：关注结果（Vue，React）

运行时：runtime，利用 render 函数，直接把虚拟 DOM 转为真实 DOM
编译时：compiler，直接把 template 模板中的内容转化为真是 DOM
运行时+编译时：先利用 template 模板转为 render 函数，再利用 render 函数转为真实 DOM

## Vue2

状态管理工具 Vuex

## Vue3

状态管理工具 pinia
构建工具 Vite（开发使用，生产 build rollup）

相比与 react，vue 没有 scheduler 的过程。
使用 proxy 通过订阅依赖来实现，track 阶段做依赖收集、trigger 去做依赖更新
