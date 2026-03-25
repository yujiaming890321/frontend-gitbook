# [Formilyjs](https://www.formilyjs.org/zh-CN)

抽象了表单领域模型的 MVVM 表单解决方案

## @formily/reactive

核心思想参考 Mobx

### Observable

可订阅对象，每次操作该对象的属性数据，会自动通知订阅者

### Reaction

相当于是可订阅对象的订阅者

### Computed

computed 是一个可以缓存计算结果的 Reaction

要求 computed 函数必须是纯函数，内部依赖的数据如果是外部常量数据(非 observable)，那外部变量数据发生变化，computed 是不会重新执行计算的。

### Batch

@formily/reactive 是基于 Proxy 劫持来实现的响应式编程模型，所以任何一个原子操作都会触发 Reaction 执行，这样明显是浪费了计算资源的

```js
import { observable, autorun } from '@formily/reactive'
const obs = observable({})
const handler = () => {
    obs.aa = 123
    obs.bb = 321
}

autorun(() => {
    console.log(obs.aa, obs.bb)
})

handler()
```

这样就会执行 3 次打印，autorun 默认执行一次，加上 obs.aa 赋值执行一次，obs.bb 赋值执行一次

推荐使用 batch 模式，将更新进行合并

```js
import { observable, autorun, batch } from '@formily/reactive'
const obs = observable({})
const handler = () => {
    obs.aa = 123
    obs.bb = 321
}

autorun(() => {
    console.log(obs.aa, obs.bb)
})

batch(() => {
    handler()
})
```

也可以使用 action 进行高阶包装

```js
import { observable, autorun, action } from '@formily/reactive'
const obs = observable({})
const handler = action.bound(() => {
    obs.aa = 123
    obs.bb = 321
})

autorun(() => {
    console.log(obs.aa, obs.bb)
})

handler()
```

最终执行次数就是 2 次了，即便 handler 内部的操作再多也还是 2 次
