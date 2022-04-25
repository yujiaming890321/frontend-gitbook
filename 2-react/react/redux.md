# redux

## redux 数据流

组件通过 store.dispatch(action) 发起一个 action

store 接收到 action 通过 reducer 计算出新的 state

store 返回新的 state 值给组件

## 数据流

作为 Flux 的一种实现形式，Redux 自然保持着数据流的单向性，用一张图来形象说明的话，可以是这样：

![image](https://gw.alicdn.com/tps/TB1SsWQLFXXXXXMXVXXXXXXXXXX-1170-514.jpg_600x600.jpg)

## Store

Store — 数据存储中心，同时连接着 Actions 和 Views（React Components）。

连接的意思大概就是：

1. Store 需要负责接收 Views 传来的 Action
2. 然后，根据 Action.type 和 Action.payload 对 Store 里的数据进行修改
3. 最后，Store 还需要通知 Views，数据有改变，Views 便去获取最新的 Store 数据，通过 setState 进行重新渲染组件（re1.render）。

## Store 总结

1. Store 的数据修改，本质上是通过 Reducer 来完成的。
2. Store 只提供 get 方法（即 getState），不提供 set 方法，所以数据的修改一定是通过 dispatch(action)来完成，即：action -> reducers -> store
3. Store 除了存储数据之外，还有着消息发布/订阅（pub/sub）的功能，也正是因为这个功能，它才能够同时连接着 Actions 和 Views。
   - dispatch 方法 对应着 pub
   - subscribe 方法 对应着 sub

### Reducer

Reducer，这个名字来源于数组的一个函数 — reduce，它们俩比较相似的地方在于：接收一个旧的 prevState，返回一个新的 nextState。

在上文讲解 Store 的时候，得知：Reducer 是一个纯函数，用来修改 Store 数据的。

### 数据不可变

React 在利用组件（Component）构建 Web 应用时，其实无形中创建了两棵树：虚拟 dom 树和组件树

为了避免这样的性能浪费，往往我们都会利用组件的生命周期函数 shouldComponentUpdate 进行判断是否有必要进行对该组件进行更新

对于对象引用（object，array），就糟糕了

最后对于对象引用的比较，就引出了不可变数据（immutable data）这个概念，大体的意思就是：一个数据被创建了，就不可以被改变（mutation）。

Reducer 函数在修改数据的时候，正是这样做的，最后返回的都是一个新的引用，而不是直接修改引用的数据

```javascript
function eReducer(state = [2, 3], action) {
  switch (action.type) {
    case 'ADD':
      return [...state, 4]; // 并没有直接地通过 state.push(4)，修改引用的数据
    default:
      return state;
  }
}
```

最后，因为 combineReducers 的存在，之前的那个 object tree 的整体数据结构就会发生变化，就像下面这样：

![image](https://img.alicdn.com/tps/TB1_319LFXXXXbfXVXXXXXXXXXX-1200-458.jpg_600x600.jpg)

现在，你就可以在 shouldComponentUpdate 函数中，肆无忌惮地比较对象引用了，因为数据如果变化了，比较的就会是两个不同的对象！

总结一点：Redux 通过一个个 reducer 实现了不可变数据（immutability）。

## Middleware

在 Redux 中，Middlerwares 要处理的对象则是：Action。

中间件提供的是位于 action 被发起之后，到达 reducer 之前的扩展点。

![image](https://img2022.cnblogs.com/blog/2347599/202201/2347599-20220121183010890-1303712922.png)

## react-redux：将 store 通过 props 传入 React 最外层组件

![image](https://img2020.cnblogs.com/blog/2347599/202112/2347599-20211203182754726-1163674991.jpg)
