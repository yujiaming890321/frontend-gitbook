# 目录

- [useRef](./useRef.md) & [useCallback](./useCallback.md) & [useMemo](./useMemo.md) & [memo](./memo.md)

useRef 创建缓存对象，useCallback 创建缓存方法，useMemo 创建缓存方法的结果（=vue computed）

memo 缓存组件，对组件进行 props 潜比较

- [useEffect](./useEffect.md) & [useLayoutEffect](./useLayoutEffect.md)

useEffect & useLayoutEffect 底层调用方法一样，useLayoutEffect 执行优先级低。

- [useState](./useState.md)

返回数组对象，方便命名。

- [Redux](./redux.md)

- [Immer](./immer.md)

- [Thunk](./thunk.md)

- [Saga](./saga.md)

- [react-intl 国际化](https://formatjs.io/docs/getting-started/installation/)

## 如何拆分组件

目的：简化代码，单一职责

## React-basic

[react-basic](https://github.com/reactjs/react-basic)

- Transformation

```js
function NameBox(name) {
  return { fontWeight: 'bold', labelContent: name };
}

'Sebastian Markbåge' ->
{ fontWeight: 'bold', labelContent: 'Sebastian Markbåge' };
```

- Abstraction

```js
function FancyUserBox(user) {
  return {
    borderStyle: '1px solid blue',
    childContent: [
      'Name: ',
      NameBox(user.firstName + ' ' + user.lastName)
    ]
  };
}

{ firstName: 'Sebastian', lastName: 'Markbåge' } ->
{
  borderStyle: '1px solid blue',
  childContent: [
    'Name: ',
    { fontWeight: 'bold', labelContent: 'Sebastian Markbåge' }
  ]
};
```

- Composition

```js
function FancyBox(children) {
  return {
    borderStyle: '1px solid blue',
    children: children
  };
}

function UserBox(user) {
  return FancyBox([
    'Name: ',
    NameBox(user.firstName + ' ' + user.lastName)
  ]);
}
```

- Memoization

```js
function memoize(fn) {
  var cachedArg;
  var cachedResult;
  return function(arg) {
    if (cachedArg === arg) {
      return cachedResult;
    }
    cachedArg = arg;
    cachedResult = fn(arg);
    return cachedResult;
  };
}

var MemoizedNameBox = memoize(NameBox);

function NameAndAgeBox(user, currentTime) {
  return FancyBox([
    'Name: ',
    MemoizedNameBox(user.firstName + ' ' + user.lastName),
    'Age in milliseconds: ',
    currentTime - user.dateOfBirth
  ]);
}
```

- List

```js
function UserList(users, likesPerUser, updateUserLikes) {
  return users.map(user => FancyNameBox(
    user,
    likesPerUser.get(user.id),
    () => updateUserLikes(user.id, likesPerUser.get(user.id) + 1)
  ));
}

var likesPerUser = new Map();
function updateUserLikes(id, likeCount) {
  likesPerUser.set(id, likeCount);
  rerender();
}

UserList(data.users, likesPerUser, updateUserLikes);
```

- Continuations

```js
function FancyUserList(users) {
  return FancyBox(
    UserList.bind(null, users)
  );
}

const box = FancyUserList(data.users);
const resolvedChildren = box.children(likesPerUser, updateUserLikes);
const resolvedBox = {
  ...box,
  children: resolvedChildren
};
```

- State Map

```js
function FancyBoxWithState(
  children,
  stateMap,
  updateState
) {
  return FancyBox(
    children.map(child => child.continuation(
      stateMap.get(child.key),
      updateState
    ))
  );
}

function UserList(users) {
  return users.map(user => {
    continuation: FancyNameBox.bind(null, user),
    key: user.id
  });
}

function FancyUserList(users) {
  return FancyBoxWithState.bind(null,
    UserList(users)
  );
}

const continuation = FancyUserList(data.users);
continuation(likesPerUser, updateUserLikes);
```

- Memoization Map

```js
function memoize(fn) {
  return function(arg, memoizationCache) {
    if (memoizationCache.arg === arg) {
      return memoizationCache.result;
    }
    const result = fn(arg);
    memoizationCache.arg = arg;
    memoizationCache.result = result;
    return result;
  };
}

function FancyBoxWithState(
  children,
  stateMap,
  updateState,
  memoizationCache
) {
  return FancyBox(
    children.map(child => child.continuation(
      stateMap.get(child.key),
      updateState,
      memoizationCache.get(child.key)
    ))
  );
}

const MemoizedFancyNameBox = memoize(FancyNameBox);
```

- Algebraic Effects

```js
function ThemeBorderColorRequest() { }

function FancyBox(children) {
  const color = raise new ThemeBorderColorRequest();
  return {
    borderWidth: '1px',
    borderColor: color,
    children: children
  };
}

function BlueTheme(children) {
  return try {
    children();
  } catch effect ThemeBorderColorRequest -> [, continuation] {
    continuation('blue');
  }
}

function App(data) {
  return BlueTheme(
    FancyUserList.bind(null, data.users)
  );
}
```

## 子传父

useImperativeHandle

## useReducer

const initState = {
    a: { userId: null, show: false }
};
const reducer = (state, action) => {
    switch (action.type) {
        case 'a':
            return { ...state, a: { show: false, userId: null } };
        default :
            return { ...state };
    }
};
const [ state, dispatch ] = useReducer(reducer, initState);

## dynamic

```js
  const componentName = "card";
  const dynamicLoadComponent = (component: string) => {
    return require(`../components/${component}/index`).default;
  };
  const DynamicDetail = dynamicLoadComponent(componentName);

  return (
    <div className="App">
      <DynamicDetail />
    </div>
  );
```
