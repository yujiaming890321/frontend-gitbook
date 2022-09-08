# es6

## 判断集合是否有空值

初始值是true，r 上一次结果，r && !isEmpty(i) 判断是否有空值。

```js
if (Array.isArray(v) && v.length === 4) {
    return v.reduce((r, i) => r && !isEmpty(i), true);
}
```