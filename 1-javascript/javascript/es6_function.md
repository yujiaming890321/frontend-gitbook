# es6 - ES2015

## ECMAScript 和 JavaScript 到底是什么关系？

ECMAScript 和 JavaScript 的关系是，前者是后者的规格，后者是前者的一种实现

## ES6 与 ECMAScript 2015 的关系

标准委员会最终决定，标准在每年的 6 月份正式发布一次，作为当年的正式版本。
ES6 的第一个版本，就这样在 2015 年 6 月发布了，正式名称就是《ECMAScript 2015 标准》（简称 ES2015）

提到 ES6 的地方，一般是指 ES2015 标准，但有时也是泛指“下一代 JavaScript 语言”

https://github.com/tc39/ecma262

https://262.ecma-international.org/6.0/

## let、const

## 结构赋值 Destructuring

let [a,b,c]=[1,2,3]

## 判断集合是否有空值

初始值是true，r 上一次结果，r && !isEmpty(i) 判断是否有空值。

```js
if (Array.isArray(v) && v.length === 4) {
    return v.reduce((r, i) => r && !isEmpty(i), true);
}
```

## arrow function 箭头函数

## Set、Map

## string

includes()
startsWith()
endsWith()

## parameter default value 参数默认值

```js
function opt(a, b = "123") {
  // 参数默认值只能在后面
}
```

## Rest 剩余参数

```js
function opt(a, ...rest) {
  // 参数默认值只能在后面
}
```

## Spread 展开数组

```js
const arr = [1, 2, 3, 1];
console.log.apply(console, arr);
// 等价于
console.log(...arr);
```

## Promise

## Proxy 代理对象

## Reflect 统一对象操作 API

## Symbol

全新的原始数据类型，用来表示一个独一无二的值

## Iterable

对象要实现 Iterable 可迭代接口的方法，Iterable 要有 [Symbol.iterator] 的方法，这个方法返回一个 Iterator 对象，Iterator 要有用于迭代的 next 方法，next 方法执行返回的是迭代结果 IterationResult 对象，这个对象要有 value 和 done 属性来表示当前被迭代的数据，value 可以是任意类型，done 要是布尔类型

```js
const obj = {
  store: ["foo", "bar", "baz"],
​
  [Symbol.iterator]: function () {
    let index = 0;
    const self = this;
​
    return {
      next: function () {
        const res = {
          value: self.store[index],
          done: index >= self.store.length
        };
        index++;
        return res;
      }
    };
  }
};
​
for (const item of obj) {
  console.log("循环", item);
}
// 循环 foo
// 循环 bar
// 循环 baz
```

## Generator

在 function 后面加一个 * 就是一个 generator 函数了

生成器对象也实现了 iterator 接口

generator 函数要配合 yield 关键字去使用

generator 对象是惰性执行的，调用一次才会继续向下执行到 yield 的语句，直到执行完

