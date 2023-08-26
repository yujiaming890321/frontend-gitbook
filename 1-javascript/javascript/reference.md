# reference 参考

## 将对象转数组

```js
const products = {
  bread: 1,
  milk: 2,
  cheese: 2,
  chicken: 1,
}

const output = Object.entries(products).flatMap(([k, v]) => Array(v).fill(k))

console.log(output)
```

## 获取对象中字段的集合

```js
var collection = [
    {name: '', age:45}
];
_.pluck(collection, 'age');  // [45]

// 也可以这样写：
_.map(collection, 'age');  // [45]
```

获取多个字段

```js
const collection = [
   { name: '', age: 45 },
   { name: 'tt', age: 23, hua: 'hua' },
];

const tt = _.map(collection, (item) => {
   return _.pick(item, ['name', 'age']);
});
console.log(tt);  // [ {name: "", age: 45}, {name: "tt", age: 23} ]
```
