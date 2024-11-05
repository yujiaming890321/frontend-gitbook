# [$nextTick](https://cn.vuejs.org/api/general.html#nexttick)

等待下一次 DOM 更新刷新的工具方法。

由于 vue 异步更新策略，数据变化 Vue不会立即更新dom，而是开启一个队列，把组件更新函数保存到队列中，在同一事件循环中发生的所有数据变更会异步的批量更新。
这一次策略导致我们修改的数据不会立刻出现在DOM上，如果需要更新就使用 nextTick，类似react useState

```js
vue 更新是通过把副作用函数放入更新队列中更新数据
new ReactiveEffect(componentUpdateFn, () => queueJob(update), instance.scope)
更新队列 queueFlush() 通过 Promise.then 更新任务 flushJobs
nextTick 在 Promise.then 的后面加了一个 .then, 将 fn 放入里面执行回调，就一定是在更新数据队列后执行回调。
```
