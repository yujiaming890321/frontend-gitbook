# 先上一张经典图为敬

![image](https://img2022.cnblogs.com/blog/2347599/202201/2347599-20220119155201282-1402950773.webp)

## redux-saga 是一个用于管理 redux 应用异步操作代替 redux-thunk 的中间件

- 集中处理 redux 副作用问题。reducer 负责处理 action 的更新，saga 负责协调那些复杂或者异步的操作
- 使用 generator 函数执行异步，generator 不是线程
- watch/worker（监听->执行） 的工作形式

redux-saga 启动的任务可以在任何时候通过手动来取消，也可以把任务和其他的 Effects 放到 race 方法里以自动取消

### createSagaMiddleware(...sagas:[])

createSagaMiddleware 的作用是创建一个 redux 中间件，并将 sagas 与 Redux store 建立链接

### effect

只要是被 yield 的值，都可以被称为 effect。例如 yield 1 中，数字 1 就是 effect。
所有的 effect 都是通过 yield 语法传递给 effect-runner 的，effect-runner 处理该 effect 并决定什么时候恢复生成器。
redux-saga 里所有 effect 返回的值，都是一个带类型的纯 object 对象。
generator 的特点是执行到某一步时，可以把控制权交给外部代码，由外部代码拿到返回结果后，决定该怎么做。

**put**
作用和 redux 中的 dispatch 相同。

```
yield put({ type: 'CLICK_BTN' });
```

**take**
等待 redux dispatch 匹配某个 pattern 的 action 。

在这个例子中，先等待一个按钮点击的 action ，然后执行按钮点击的 saga：

```
while (true) {
  yield take('CLICK_BUTTON');
  yield fork(clickButtonSaga);
}
```

**fork**
当接收到 BEGIN_COUNT 的 action，则开始倒数，而接收到 STOP_COUNT 的 action， 则停止倒数。

```
function* count(number) {
  let currNum = number;

  while (currNum >= 0) {
    console.log(currNum--);
    yield delay(1000);
  }
}

function countSaga* () {
  while (true) {
    const { payload: number } = yield take(BEGIN_COUNT);
    const countTaskId = yield fork(count, number);

    yield take(STOP_TASK);
    yield cancel(countTaskId);
  }
}
```

**call**
有阻塞地调用 saga 或者返回 promise 的函数。

```
const project = yield call(fetch, { url: UrlMap.fetchProject });
const members = yield call(fetchMembers, project.id);
```

**select**
作用和 redux thunk 中的 getState 相同。

```
const id = yield select(state => state.id);
```

**阻塞调用和无阻塞调用**
其中 fork 是无阻塞型调用，call 是阻塞型调用。

### channel

channel 是对事件源的抽象，作用是先注册一个 take 方法，当 put 触发时，执行一次 take 方法，然后销毁 take。

```
export function channel(buffer = buffers.expanding()) {
  let closed = false
  let takers = []

  function put(input) {
    if (closed) {
      return
    }
    if (takers.length === 0) {
      return buffer.put(input)
    }
    const cb = takers.shift()
    cb(input)
  }

  function take(cb) {
    if (closed && buffer.isEmpty()) {
      cb(END)
    } else if (!buffer.isEmpty()) {
      cb(buffer.take())
    } else {
      takers.push(cb)
      cb.cancel = () => {
        remove(takers, cb)
      }
    }
  }

  function flush(cb) {
    if (closed && buffer.isEmpty()) {
      cb(END)
      return
    }
    cb(buffer.flush())
  }

  function close() {
    if (closed) {
      return
    }

    closed = true

    const arr = takers
    takers = []

    for (let i = 0, len = arr.length; i < len; i++) {
      const taker = arr[i]
      taker(END)
    }
  }

  return {
    take,
    put,
    flush,
    close,
  }
}
```

当 put 触发时，如果 channel 里已经有注册了的 taker，taker 就会执行。

我们需要在 put 触发之前，先调用 channel 的 take 方法，注册实际要运行的方法。

```
const chan = channel();
btn.addEventListener('click', () => {
  const action =`action data${i++}`;
  chan.put(action);
}, false);

function* mainSaga() {
  const action = yield take();
  console.log(action);
}
```

这个 take 是 saga 里的一种 effect 类型。

### task

task 是 generator 方法的执行环境，所有 saga 的 generator 方法都跑在 task 里。
简易实现如下：

```
function task(iterator) {
  const iter = iterator();
  function next(args) {
    const result = iter.next(args);
    if (!result.done) {
      const effect = result.value;
      if (effect.type === 'take') {
        runEffect(result.value, next);
      }
    }
  }
  next();
}
```

## 数据流转

![image](https://img2022.cnblogs.com/blog/2347599/202201/2347599-20220125164251396-758936865.png)

```
// saga.js
// 它是一个 generator function
// fn 中同样包含了业务数据请求代码逻辑
function* fetchData(action) {
  const { payload: { someValue } } = action;
  try {
    const result = yield call(myAjaxLib.post, "/someEndpoint", { data: someValue });
    yield put({ type: "REQUEST_SUCCEEDED", payload: response });
  } catch (error) {
    yield put({ type: "REQUEST_FAILED", error: error });
  }
}

// watcher saga
// 监听每一次 dispatch(action)
// 如果 action.type === 'REQUEST'，那么执行 fetchData
export function* watchFetchData() {
  yield takeEvery('REQUEST', fetchData);
}


// component.js
// View 层 dispatch(action) 触发异步请求
// 这里的 action 依然可以是一个 plain object
this.props.dispatch({
  type: 'REQUEST',
  payload: {
    someValue: { hello: 'saga' }
  }
});
```

## 对比 thunk

thunk 采用的是扩展 action 的方式：使得 redux 的 store 能 dispatch 的内容从普通对象扩展到函数

saga 采用的方案更接近于 redux 的全局思想
saga 采用发布订阅模式，需要一个经纪人 Broker，用于监听组件发出的 action，将监听到的 action1 转发给对应的订阅者，再由订阅者执行具体任务，任务执行完后，再发出另一个 action2 交由 reducer 修改 state
