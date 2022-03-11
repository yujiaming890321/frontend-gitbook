# 前言

React 和 Redux 都遵守组件状态为`不可变（immutable）`的理念，使用 immer 可将对象设置为 immutable，防止意外的修改。
Immer 是一个支持柯里化，仅支持同步计算的工具，所以非常适合作为 redux 的 reducer 使用。

```
import produce from "immer"

const baseState = [
    {
        title: "Learn TypeScript",
        done: true
    },
    {
        title: "Try Immer",
        done: false
    }
]

const nextState = produce(baseState, draftState => {
    draftState.push({title: "Tweet about it"})
    draftState[1].done = true
})
```

# immer 原理

## draft 代理对象的一些描述字段

```
{
  modified, // 是否被修改过
  finalized, // 是否已经完成（所有 setter 执行完，并且已经生成了 copy）
  parent, // 父级对象
  base, // 原始对象（也就是 obj）
  copy, // base（也就是 obj）的浅拷贝，使用 Object.assign(Object.create(null), obj) 实现
  proxies, // 存储每个 propertyKey 的代理对象，采用懒初始化策略
}
```

## produce 创建代理对象

produce 方法里面会通过 createProxy 这个方法创建一个代理对象

```
produce: IProduce = (base: any, recipe?: any, patchListener?: any) => {
    /* 如果第一个参数传入的是函数而不是一个对象且第二个参数不是函数，则采用curried函数的方式。*/
    if (typeof base === "function" && typeof recipe !== "function") {
        /* 第二个参数就变成了初始值 */
        const defaultBase = recipe
        /* 第一个参数变成了recipe函数 */
        recipe = base

        const self = this
        return function curriedProduce(
            this: any,
            base = defaultBase,
            ...args: any[]
        ) {
             /* 将修改后的参数从新传入正常的produce函数 代理对象 draft 实际是recipe函数的第一个参数，初始值取的是produce的第二个参数 */
            return self.produce(base, (draft: Drafted) => recipe.call(this, draft, ...args)) // prettier-ignore
        }
    }

    if (typeof recipe !== "function")
        /** die 函数封装error，通过key调用抛出异常信息 */
        die(6)
    if (patchListener !== undefined && typeof patchListener !== "function")
        die(7)

    let result

    /* 只有对象 数组 和 "immerable classes" 可以进行代理 */
    if (isDraftable(base)) {
        /* scope 是 immer 的一个内部概念，当目标对象有复杂嵌套时，利用 scope 区分和跟踪嵌套处理的过程 */
        const scope = enterScope(this)
        const proxy = createProxy(this, base, undefined)
        let hasError = true
        try {
            result = recipe(proxy)
            hasError = false
        } finally {
            // finally instead of catch + rethrow better preserves original stack
            if (hasError) revokeScope(scope)
            else leaveScope(scope)
        }
        if (typeof Promise !== "undefined" && result instanceof Promise) {
            return result.then(
                result => {
                    usePatchesInScope(scope, patchListener)
                    return processResult(result, scope)
                },
                error => {
                    revokeScope(scope)
                    throw error
                }
            )
        }
        usePatchesInScope(scope, patchListener)
        return processResult(result, scope)
    } else if (!base || typeof base !== "object") {
        result = recipe(base)
        if (result === undefined) result = base
        if (result === NOTHING) result = undefined
        if (this.autoFreeze_) freeze(result, true)
        if (patchListener) {
            const p: Patch[] = []
            const ip: Patch[] = []
            getPlugin("Patches").generateReplacementPatches_(base, result, p, ip)
            patchListener(p, ip)
        }
        return result
    } else die(21, base)
}
```

## createProxy 创建代理

createProxy 设计模式为`策略模式`
判断传入的对象类型来采取不同的代理模式，一般情况下都是会使用 createProxyProxy 也就是 Proxy 进行代理

```
export function createProxy<T extends Objectish>(
    immer: Immer,
    value: T,
    parent?: ImmerState
): Drafted<T, ImmerState> {
    /* 根据传入的对象类型来采取不同的代理模式 */
    const draft: Drafted = isMap(value)
        ? getPlugin("MapSet").proxyMap_(value, parent)/* 传入的base对象是Map类型 */
        : isSet(value)
        ? getPlugin("MapSet").proxySet_(value, parent)/* 传入的base对象是Set类型 */
        : immer.useProxies_
        ? createProxyProxy(value, parent)/* 当前环境支持Proxy则使用Proxy进行代理 */
        : getPlugin("ES5").createES5Proxy_(value, parent) /* 当前环境不支持Proxy则使用Object.defineProperty() */

    const scope = parent ? parent.scope_ : getCurrentScope()
    scope.drafts_.push(draft)
    return draft
}
```

## createProxyProxy

```
export function createProxyProxy<T extends Objectish>(
    base: T,
    parent?: ImmerState
): Drafted<T, ProxyState> {
    /** 定义初始对象 */
    ...
    let target: T = state as any
    let traps: ProxyHandler<object | Array<any>> = objectTraps
    if (isArray) {
        target = [state] as any
        traps = arrayTraps
    }

    const {revoke, proxy} = Proxy.revocable(target, traps)
    state.draft_ = proxy as any
    state.revoke_ = revoke
    return proxy as any
}
```

通过 Proxy.revocable() 方法可以用来创建一个可撤销的代理对象.
在这个代理对象上，绑定了自定义（objectTraps/arrayTraps）的 getter setter，然后直接将其扔给 produce 执行。

## setter

当对 draft 代理对象修改时，会对原始值进行浅拷贝，保存到 copy 属性，同时将 modified 属性设置为 true。
将 draft 代理对象的 copy 属性对象 [props] 修改。

## getter

当 draft 代理对象修改后，会读取 copy 属性的对象
