# es10 - ECMA2019

## Array.flat()和Array.flatMap()

数组展平

```js
[1, 2, [3, 4]].flat();
// [ 1, 2, 3, 4 ]
[1, 2, [3, 4, [5, 6]]].flat(2);
// [ 1, 2, 3, 4, 5, 6 ]

[1, 2, [3, 4]].flatMap(v => {
  if (typeof v === 'number') {
    return v * 2
  } else {
    return v.map(v => v * 2)
  }
})
// [2, 4, 6, 8]
```

## String.trimStart()和String.trimEnd()

把头尾的空格文本去掉，来规避展示的不受控情况。自ES5来，String.prototype.trim() 被用于去除头尾上的空格、换行符等，现在通过 trimStart()，trimEnd() 来头和尾进行单独控制。
trimLeft()、trimRight() 是他们的别名

## String.prototype.matchAll

matchAll（）为所有匹配的匹配对象返回一个迭代器

```js
const raw_arr = 'test1  test2  test3'.matchAll((/t(e)(st(\d?))/g));
const arr = [...raw_arr];
```

## Symbol.prototype.description

Symbol 是ES6中引入的基本数据类型，可以用作对象属性的标识符。描述属性是只读的，可用于获取符号对象的描述，更好了解它的作用。

```js
const symbol = Symbol('This is a Symbol');
symbol;
// Symbol(This is a Symbol)
Symbol.description;
// 'This is a Symbol'
```

## Object.fromEntries()

我们知道ES8引入了Object.entries把一个对象转为[key, value]键值对的形式，可以运用于像 Map 这种结构中。凡事有来有回，Object.fromEntries()用于把键值对还原成对象结构。

```js
const entries = [ ['foo', 'bar'] ];
const object = Object.fromEntries(entries);
// { foo: 'bar' }
```

## 可选 Catch

在进行try...catch错误处理过程中，如果没有给catch传参数的话，代码就会报错。有时候我们并不关心错误情况

## JSON Superset 超集

之前如果JSON字符串中包含有行分隔符(\u2028) 和段落分隔符(\u2029)，那么在解析过程中会报错。现在ES2019对它们提供了支持。

## JSON.stringify() 加强格式转化

## Array.prototype.sort() 更加稳定

## Function.prototype.toString() 重新修订
