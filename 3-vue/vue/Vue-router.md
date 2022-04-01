# Vue-router

支持 HTML5History、HashHistory、AbstractHistory 三种模式

## HTML5History

```
window.addEventListener('popstate', handleRoutingEvent)

const handleRoutingEvent = () => {
    const current = this.current
    if (!ensureSlash()) {
        return
    }
    this.transitionTo(getHash(), route => {
        if (supportsScroll) {
            handleScroll(this.router, route, current, true)
        }
        if (!supportsPushState) {
            replaceHash(route.fullPath)
        }
    })
}

export function runQueue (queue: Array<?NavigationGuard>, fn: Function, cb: Function) {
  const step = index => {
    if (index >= queue.length) {
      cb()
    } else {
      if (queue[index]) {
        fn(queue[index], () => {
          step(index + 1)
        })
      } else {
        step(index + 1)
      }
    }
  }
  step(0)
}
// queue
const queue: Array<?NavigationGuard> = [].concat(
    // in-component leave guards
    extractLeaveGuards(deactivated),
    // global before hooks
    this.router.beforeHooks,
    // in-component update hooks
    extractUpdateHooks(updated),
    // in-config enter guards
    activated.map(m => m.beforeEnter),
    // async components
    resolveAsyncComponents(activated)
)
// fn
const iterator = (hook: NavigationGuard, next) => {
    if (this.pending !== route) {
    return abort(createNavigationCancelledError(current, route))
    }
    try {
    hook(route, current, (to: any) => {
        if (to === false) {
        // next(false) -> abort navigation, ensure current URL
        this.ensureURL(true)
        abort(createNavigationAbortedError(current, route))
        } else if (isError(to)) {
        this.ensureURL(true)
        abort(to)
        } else if (
        typeof to === 'string' ||
        (typeof to === 'object' &&
            (typeof to.path === 'string' || typeof to.name === 'string'))
        ) {
        // next('/') or next({ path: '/' }) -> redirect
        abort(createNavigationRedirectedError(current, route))
        if (typeof to === 'object' && to.replace) {
            this.replace(to)
        } else {
            this.push(to)
        }
        } else {
        // confirm transition and pass on the value
        next(to)
        }
    })
    } catch (e) {
    abort(e)
    }
}

runQueue(queue, iterator, () => {
    // wait until async components are resolved before
    // extracting in-component enter guards
    const enterGuards = extractEnterGuards(activated)
    const queue = enterGuards.concat(this.router.resolveHooks)
    runQueue(queue, iterator, () => {
        if (this.pending !== route) {
            return abort(createNavigationCancelledError(current, route))
        }
        this.pending = null
        onComplete(route)
        if (this.router.app) {
            this.router.app.$nextTick(() => {
                handleRouteEntered(route)
            })
        }
    })
})
```

## HashHistory

如果支持`popstate`，使用`popstate`。否则使用`hashchange` 监听。

```
const eventType = supportsPushState ? 'popstate' : 'hashchange'
window.addEventListener(
    eventType,
    handleRoutingEvent
)

const handleRoutingEvent = () => {
    const current = this.current
    if (!ensureSlash()) {
        return
    }
    this.transitionTo(getHash(), route => {
        if (supportsScroll) {
            handleScroll(this.router, route, current, true)
        }
        if (!supportsPushState) {
            replaceHash(route.fullPath)
        }
    })
}
```

## AbstractHistory

自己内存中模拟路由跳转
