# thunk

## "thunk" 是什么?

单词“thunk”是一个编程术语，意思是“一段做延迟工作的代码”。不需要现在执行一些逻辑，我们可以编写一个函数体或代码，用于以后执行这些工作。

特别是对于 Redux 来说，“thunks”是一种编写带有内部逻辑的函数的模式，它可以与 Redux 存储的调度和 getState 方法交互。

使用 thunks 需要将 Redux -thunk 中间件作为配置的一部分添加到 Redux 存储中。

Thunks 是在 Redux 应用程序中编写异步逻辑的标准方法，通常用于获取数据。但是，它们可以用于各种任务，并且可以包含同步和异步逻辑。

## 如何使用

thunk 函数是接受两个参数的函数:Redux store 分派方法和 Redux store getState 方法。应用程序代码不会直接调用 Thunk 函数。相反，它们被传递给 store.dispatch():

```javascript
const thunkFunction = (dispatch, getState) => {
    // logic here that can dispatch actions or read state
}

store.dispatch(thunkFunction)
```

一个 thunk 函数可以包含任何逻辑，同步或异步，并且可以在任何时候调用 dispatch 或 getState。
Redux 代码通常使用动作创建者来生成动作对象以进行分派，而不是手工编写动作对象，我们通常使用 thunk 动作创建者来生成被分派的 thunk 函数，这与 Redux 代码通常使用动作创建者来生成动作对象的方式相同。一个 thunk 动作创建者是一个函数，它可能有一些参数，并返回一个新的 thunk 函数。重击通常会关闭传递给动作创建者的任何参数，所以它们可以在逻辑中使用:

```javascript
// fetchTodoById is the "thunk action creator"
export function fetchTodoById(todoId) {
    // fetchTodoByIdThunk is the "thunk function"
    return async function fetchTodoByIdThunk(dispatch, getState) {
        const response = await client.get(`/fakeApi/todo/${todoId}`)
        dispatch(todosLoaded(response.todos))
    }
}
```

Thunk 函数和动作创建者可以使用 function 关键字或箭头函数来编写——这里没有什么有意义的区别。同样的 fetchTodoById thunk 也可以用箭头函数来写，像这样:

```javascript
export const fetchTodoById = (todoId) => async (dispatch) => {
    const response = await client.get(`/fakeApi/todo/${todoId}`)
    dispatch(todosLoaded(response.todos))
}
```

在这两种情况下，thunk 都是通过调用动作创建者来发送的，与你发送任何其他 Redux 动作的方式相同:

```javascript
function TodoComponent({ todoId }) {
    const dispatch = useDispatch()

    const onFetchClicked = () => {
        // Calls the thunk action creator, and passes the thunk function to dispatch
        dispatch(fetchTodoById(todoId))
    }
}
```

## 使用场景

由于 thunks 是一种通用工具，可以包含任意逻辑，因此可以用于各种各样的目的。最常见的用例有:

-   将复杂的逻辑移出组件
-   发出异步请求或其他异步逻辑
-   编写需要在一行或一段时间内调度多个操作的逻辑
-   编写需要访问的逻辑在`getState`中做出决定或包含其他状态值

## 源码逻辑

```javascript
function createThunkMiddleware(extraArgument) {
    const middleware = ({ dispatch, getState }) => (next) => (action) => {
        // The thunk middleware looks for any functions that were passed to `store.dispatch`.
        // If this "action" is really a function, call it and return the result.
        if (typeof action === 'function') {
            // Inject the store's `dispatch` and `getState` methods, as well as any "extra arg"
            return action(dispatch, getState, extraArgument)
        }

        // Otherwise, pass the action down the middleware chain as usual
        return next(action)
    }
    return middleware
}
```

根据[自定义一个 redux 中间件](https://redux.js.org/tutorials/fundamentals/part-4-store#writing-custom-middleware)

```javascript
function createThunkMiddleware(extraArgument) {
  // ThunkMiddleware
  return ({ dispatch, getState }: <storeAPI>) => {
    // wrapDispatch
    next =>
    // handleAction
    action => {
      if (typeof action === 'function') {
        // Inject the store's `dispatch` and `getState` methods, as well as any "extra arg"
        return action(dispatch, getState, extraArgument)
      }

      // Otherwise, pass the action down the middleware chain as usual
      return next(action)
    }
  }
}
```

![image](https://img2020.cnblogs.com/blog/2347599/202201/2347599-20220118101858833-959563829.webp)

## 缺点

无法抽出逻辑进行测试
