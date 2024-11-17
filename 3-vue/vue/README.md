# Vue

## Vue2

状态管理工具 Vuex

## Vue3

状态管理工具 pinia
构建工具 Vite（开发使用，生产 build rollup）

相比与 react，vue 没有 scheduler 的过程。
使用 proxy 通过订阅依赖来实现，track 阶段做依赖收集、trigger 去做依赖更新
