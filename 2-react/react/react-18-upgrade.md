# react 18 更新文档

## 新的 root api，可以调用并发模式 concurrent rendering

```
// Before
import { render } from 'react-dom';
const container = document.getElementById('app');
render(<App tab="home" />, container);

// After
import { createRoot } from 'react-dom/client';
const container = document.getElementById('app');
const root = createRoot(container);
root.render(<App tab="home" />);
```

## unmountComponentAtNode 修改为 root.unmount:

```
// Before
unmountComponentAtNode(container);

// After
root.unmount();
```

## 删除 render 回调

```
// Before
const container = document.getElementById('app');
ReactDOM.render(<App tab="home" />, container, () => {
  console.log('rendered');
});

// After
function AppWithCallbackAfterRender() {
  useEffect(() => {
    console.log('rendered');
  });

  return <App tab="home" />
}

const container = document.getElementById('app');
const root = ReactDOM.createRoot(container);
root.render(<AppWithCallbackAfterRender />);
```

## SSR hydrate to hydrateRoot

```
// Before
import { hydrate } from 'react-dom';
const container = document.getElementById('app');
hydrate(<App tab="home" />, container);

// After
import { hydrateRoot } from 'react-dom/client';
const container = document.getElementById('app');
const root = hydrateRoot(container, <App tab="home" />);
// Unlike with createRoot, you don't need a separate root.render() call here.
```

# Automatic Batching 自动批处理

React 18 之前只在 React 事件处理程序中批量更新

Promise, setTimeout, native event handlers, or any other event 则不会批量更新

```
// Before React 18 only React events were batched

function handleClick() {
  setCount(c => c + 1);
  setFlag(f => !f);
  // React will only re-render once at the end (that's batching!)
}

setTimeout(() => {
  setCount(c => c + 1);
  setFlag(f => !f);
  // React will render twice, once for each state update (no batching)
}, 1000);
```

Starting in React 18 with createRoot，这些都可以批量更新了。

```
// After React 18 updates inside of timeouts, promises,
// native event handlers or any other event are batched.

function handleClick() {
  setCount(c => c + 1);
  setFlag(f => !f);
  // React will only re-render once at the end (that's batching!)
}

setTimeout(() => {
  setCount(c => c + 1);
  setFlag(f => !f);
  // React will only re-render once at the end (that's batching!)
}, 1000);
```

## 可以使用 flushSync 退出批处理

```
import { flushSync } from 'react-dom';

function handleClick() {
  flushSync(() => {
    setCounter(c => c + 1);
  });
  // React has updated the DOM by now
  flushSync(() => {
    setFlag(f => !f);
  });
  // React has updated the DOM by now
}
```

# [adding startTransition for slow renders](https://github.com/reactwg/react-18/discussions/65)

# [Concurrent React for Library Maintainers](https://github.com/reactwg/react-18/discussions/70)

# [useMutableSource → useSyncExternalStore](https://github.com/reactwg/react-18/discussions/86)

# New APIs

## startTransition、useTransition

- startTransition 包裹的更新被当作非紧急事件来处理，如果有更紧急的更新，如点击或按键，则会被打断。

- startTransition 中的延迟更新，不会触发 Suspens 组件的 fallback，便于用户在更新期间的交互

将函数中的内容过渡

```
const [isPending, startTransition] = useTransition();

// isPending:过度任务状态,true 代表过渡中,false 过渡结束
```

- Yielding(屈服)，每 5 毫秒，React 将停止工作以允许浏览器执行其他工作

- Interrupting(打断)，如果我们已经在渲染上次更新的结果。在 React 再次开始工作时，它会安排了一个新的紧急更新，并停止处理待处理的结果。

- Skipping old results(跳过旧结果)，当它从打断中恢复时，它将从头开始渲染最新的值。 这意味着 React 只在用户实际需要看到渲染的 UI 上工作，而不是 old state。

## useDeferredValue

- 过渡单个状态值,让状态滞后变化
- 避开紧急任务的渲染,让出优先级
- 如果当前渲染是一个紧急更新的结果，比如用户输入，React 将返回之前的值，然后在紧急渲染完成后渲染新的值。
- React 将在其他工作完成后立即进行更新(而不是等待任意的时间)，并且像 startTransition 一样，延迟值可以挂起，而不会触发现有内容的意外回退。

```
const pendingValue = useDeferredValue(value)
```

## useTranstion 和 useDeferredValue 异同:

相同点:

1. useDeferredValue 与 useTransition 一样都是标记成非紧急任务。

不同点:

1. useDeferredValue 本质上在 useEffect 内部执行，而 useEffect 内部逻辑是异步执行的，所以它一定程度上更滞后于 useTransition，startTransition 的回调函数是同步执行的。
1. 在 startTransition 之中任何更新，都会标记上 transition。React 将在更新的时候，判断这个标记来决定是否完成此次更新。
1. transition 可以理解成比 setTimeout 更早的更新。但是同时要保证 ui 的正常响应，在性能好的设备上，transition 两次更新的延迟会很小，但是在慢的设备上，延时会很大，但是不会影响 UI 的响应。

## useId

生成唯一 ID

## useSyncExternalStore

并发读取
