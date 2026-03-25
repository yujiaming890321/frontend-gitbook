# redux

-   applyMiddleware: function()

    ```js
    const logger = ({ getState }) => {
        return (next) => (action) => {
            console.log('MIDDLEWAVE', getState(), action)
            return next(action)
        }
    }
    const secondStore = craeteStore(reducer, applyMiddleware(logger))
    ```

-   bingActionCreators: function()

    ```js
    const dispatchAdd = bingActionCreators(add, store.dispatch)

    const handrollDispatch = store.dispatch(add(4))

    const bingActionCreators = (actions, dispatch) => {
        return Object.keys(actions).reduce((boundActions, key) => {
            boundActions[key] = bingActionCreator(actions[key], dispatch)
        })
    }
    ```

-   combineReducers: function()

    将 reducer 组合起来

-   compose: function()

    将方法组合起来。louder、threetimes，compose(louder, threetimes) = louderThreetimes

-   createStore: function()

    创建一个 store, store 有 dispatch、subscribe、getState、replaceReducer

    ```js
    const middleware = [thunkMiddleware]
    if (process.env.NODE_ENV === 'development') {
        const { logger } = require('redux-logger')
        middleware.push(logger)
    }
    const reducers = combineReducers({
        calculator: calculatorReducer,
    })
    const store = createStore(reducers, applyMiddleware(...middleware))
    ```

## redux 数据流

组件通过 store.dispatch(action) 发起一个 action

store 接收到 action 通过 reducer 计算出新的 state

store 返回新的 state 值给组件

## 数据流

作为 Flux 的一种实现形式，Redux 自然保持着数据流的单向性，用一张图来形象说明的话，可以是这样：

![image](https://gw.alicdn.com/tps/TB1SsWQLFXXXXXMXVXXXXXXXXXX-1170-514.jpg_600x600.jpg)

## 单一数据源 Store

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

### 使用纯函数来执行修改，Reducer

Reducer，这个名字来源于数组的一个函数 — reduce，它们俩比较相似的地方在于：接收一个旧的 prevState，返回一个新的 nextState。

在上文讲解 Store 的时候，得知：Reducer 是一个纯函数，用来修改 Store 数据的。

### State 是只读的，数据不可变

React 在利用组件（Component）构建 Web 应用时，其实无形中创建了两棵树：虚拟 dom 树和组件树

为了避免这样的性能浪费，往往我们都会利用组件的生命周期函数 shouldComponentUpdate 进行判断是否有必要进行对该组件进行更新

对于对象引用（object，array），就糟糕了

最后对于对象引用的比较，就引出了不可变数据（immutable data）这个概念，大体的意思就是：一个数据被创建了，就不可以被改变（mutation）。

Reducer 函数在修改数据的时候，正是这样做的，最后返回的都是一个新的引用，而不是直接修改引用的数据

```javascript
function eReducer(state = [2, 3], action) {
    switch (action.type) {
        case 'ADD':
            return [...state, 4] // 并没有直接地通过 state.push(4)，修改引用的数据
        default:
            return state
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

## react-redux：将 store 通过 props 传入 React 最外层组件 (Redux devtool)

```js
import { createStore } from 'redux'
import { Provider } from 'react-redux'

/* actions/calculatorAction */
const INCREMENT = 'INCREMENT'

const incrementValue = () => ({
    type: INCREMENT,
})

/* reducer/calculatorReducer */
const initialState = {
    count: 0,
}

const reducer = (state = initialState, action) => {
    if (action.type === INCREMENT) {
        return {
            count: state.count + 1,
        }
    }
    return state
}

/* reducer/index */
const rootReducer = combineReducers({
    calculator: calculatorReducer,
})

/* app */
const store = createStore(
    rootReducer,
    window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__()
)

React.render(
    <Provider store={store}>
        <APP />
    </Provider>,
    document.getElementById('root')
)
```

## react-redux：通过 connect 将组件和 redux 连接起来

### mapStateToProps

```js
import { connect } from 'react-redux';
/* component/calculator */
const Counter = ({ count, increment }) => {

}

/**
 * pass state to props into component
 */
const mapStateToProps = ( state ) => { return state }
const mapDispatchToProps = ( dispatch ) => {
  return {
    increment() {
      dispatch(incrementValue())
    }
  }
}

// 将组件和redux绑定
const CounterContainer = connect(
  mapStateToProps,
  mapDispatchToProps
)(Counter)


/* Lists */
const ListsContainer = connect(
  mapStateToProps: (state) => {
    return {
      lists: state.lists.ids,
    }
  }
)(Lists)

{lists.map((listId) => {
  return <ListContainer listId={listId} />
})}

/* List */
const ListContainer = connect(
  mapStateToProps: (state, ownProps) => {
    return {
      lists: state.lists.entities[ownProps.listId],
    }
  }
)(List)
```

![image](https://img2020.cnblogs.com/blog/2347599/202112/2347599-20211203182754726-1163674991.jpg)

### mapDispatchToProps

```js
/* CreateCardsCountainer */
const defaultCardData = {
  title: "",
  description: "",
  assignedTo: "",
}

const mapDispatchToProps = dispatch => {
  return {
    createCard(listId, cardData) {
      const cardId = Date.now().toString();
      const card = {
        id: cardId,
        ...defaultCardData,
        ...cardData,
      }
      dispatch({
        type: 'CARD_CREATE',
        payload: { card, listId, cardId }
      })
    }
  }
}

export default connect(null, mapDispatchToProps)(CreateCard)

/* CreateCard */
const { createCard, listId } = this.props
if (createCard) {
  createCard(listId, title, description)
}

/* CardList */
<CreateCardsCountainer listId={listId} />
<div>
  {list.cards.map(cardId => (
    <CardContainer key={cardId} cardId={cardId}/>
  )}
</div>

/* cardReducer, add card to store */
const cardReducer = (cards = defaultCards, action) => {
  if( action.type === "CARD_CREATE"){
    const { card, cardId } = action.payload;
    {/* return {
      entities: { ...cards.entities, [cardId]: card },
      ids: [ ...cards.ids, cardId ]
    } */}
    return addEntity(cards, card, cardId)
  }
}

/* listReducer, add card into list */
import set from 'lodash/fp/set';
/* set(chainOfProperties, whatYouWantToReplace, object) */
const listReducer = (lists = defaultCards, action) => {
  if( action.type === "CARD_CREATE"){
    const { listId, cardId } = action.payload;
    const cards = lists.entities[listId].cards.concat(cardId)
    return set(['entities', listId, 'cards'], cards, lists)
    {/* the part replaced by set
    const entities = { ...lists.entities }
    entities[listId] = {
      ...entities[listId],
      cards: entities[listId].cards.concat(cardId)
    }

    return {
      ...lists,
      entities
    } */}
  }
}
/* util */
import set from 'lodash/fp/set';
import pipe from 'lodash/fp/pipe';
export const addEntity = (state, entity, id) => {
  return pipe(
    set(['entities', id], entity),
    set('ids', state.ids.concat(id)),
  )(state);
}
```

## reselect

```js
import {createSelector} from "reselect";

export const getProductList = (state: ApplicationState): Optional<ProductListState> => state.productList;
export const getSelectedId = (state: ApplicationState): Optional<string> => state.selectedId;

export const getSelectProductList = createSelector(
  getProductList,
  getSelectedId
  (productList, selectedId): Array<string> => {
    return (
      productList.find(item => item.id === selectedId)
    );
  },
);
export const getSelectProductList = createSelector(
  [getProductList,  getSelectedId],
  (productList, selectedId): Array<string> => {
    return (
      productList.find(item => item.id === selectedId)
    );
  },
);
```

### Terminology

Selector Function : A function that accepts one or more JavaScript values as arguments, and derives a result.
Input Selectors : Basic selector functions used as building blocks for creating a memoized selector.
Output Selector : The actual memoized selectors created by createSelector.
Result Function : The function that comes after the input selectors.
Dependencies : Same as input selectors.

```js
const outputSelector = createSelector(
  [inputSelector1, inputSelector2, inputSelector3], // synonymous with `dependencies`.
  resultFunc // Result function
)
```

### Cascading Memoization

Reselect uses a two-stage "cascading" approach to memoizing functions:

The way Reselect works can be broken down into multiple parts:

1. Initial Run: On the first call, Reselect runs all the input selectors, gathers their results, and passes them to the result function.

2. Subsequent Runs: For subsequent calls, Reselect performs two levels of checks:

- First Level: It compares the current arguments with the previous ones (done by argsMemoize).

  - If they're the same, it returns the cached result without running the input selectors or the result function.

  - If they differ, it proceeds ("cascades") to the second level.

- Second Level: It runs the input selectors and compares their current results with the previous ones (done by memoize).

  - If the results are the same, it returns the cached result without running the result function.

  - If the results differ, it runs the result function.

This behavior is what we call Cascading Memoization.
