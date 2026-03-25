# useRef

## 初始化

创建缓存对象

```javascript
function mountRef<T>(initialValue: T): {current: T} {
  const hook = mountWorkInProgressHook();
  const ref = {current: initialValue};
  hook.memoizedState = ref;
  return ref;
}
```

## 更新

返回缓存对象

```javascript
function updateRef<T>(initialValue: T): {current: T} {
  const hook = updateWorkInProgressHook();
  return hook.memoizedState;
}
```
