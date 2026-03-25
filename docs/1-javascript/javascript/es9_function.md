# es9 - ES2018

## 异步迭代

在async/await的某些时刻，我们可能尝试在同步循环中调用异步函数。

```js
async function process(array) {
  for (let i of array) {
    await doSomething(i);
  }
}

async function process(array) {
  array.forEach(async i => {
    await doSomething(i);
  });
}
```

这段代码中，循环本身依旧保持同步，并在在内部异步函数之前全部调用完成。

ES2018引入异步迭代器（asynchronous iterators），这就像常规迭代器，除了next()方法返回一个Promise。因此await可以和for...of循环一起使用，以串行的方式运行异步操作。

## Promise.finally()

## Rest/Spread 属性

ES2015引入了Rest参数和扩展运算符。三个点（...）仅用于数组。Rest参数语法允许我们将一个布丁数量的参数表示为一个数组。

```js
const obj1 = { a: 1, b: 2, c: 3 };
const obj2 = { ...obj1, z: 26 };
// obj2 is { a: 1, b: 2, c: 3, z: 26 }
```

## 正则表达式命名捕获组

```js
const reDate = /([0-9]{4})-([0-9]{2})-([0-9]{2})/,
  match  = reDate.exec('2018-04-30'),
  year   = match[1], // 2018
  month  = match[2], // 04
  day    = match[3]; // 30

const reDate = /(?<year>[0-9]{4})-(?<month>[0-9]{2})-(?<day>[0-9]{2})/,
  match  = reDate.exec('2018-04-30'),
  year   = match.groups.year,  // 2018
  month  = match.groups.month, // 04
  day    = match.groups.day;   // 30

const reDate = /(?<year>[0-9]{4})-(?<month>[0-9]{2})-(?<day>[0-9]{2})/,
  d      = '2018-04-30',
usDate = d.replace(reDate, '$<month>-$<day>-$<year>');
```

## 正则表达式反向断言 lookbehind

JavaScript在正则表达式中支持先行断言（lookahead）。
例如从价格中捕获货币符号：

```js
const reLookahead = /\D(?=\d+)/,
match = reLookahead.exec('$123.89');
console.log( match[0] ); // $
```

ES2018引入以相同方式工作但是匹配前面的反向断言（lookbehind），这样我就可以忽略货币符号，单纯的捕获价格的数字：

```js
const reLookbehind = /(?<=\D)\d+/,
match = reLookbehind.exec('$123.89');
console.log( match[0] ); // 123.89
```

## 正则表达式dotAll模式

正则表达式中点.匹配除回车外的任何单字符，标记s改变这种行为，允许行终止符的出现，例如：

```js
/hello.world/.test('hello\nworld');  // false
/hello.world/s.test('hello\nworld'); // true
```

## 正则表达式 Unicode 转义

到目前为止，在正则表达式中本地访问 Unicode 字符属性是不被允许的。
ES2018添加了 Unicode 属性转义——形式为\p{...}和\P{...}，在正则表达式中使用标记 u (unicode) 设置，在\p块儿内，可以以键值对的方式设置需要匹配的属性而非具体内容。例如：

```js
const reGreekSymbol = /\p{Script=Greek}/u;
reGreekSymbol.test('π'); // true
```

## 非转义序列的模板字符串

ES2018 移除对 ECMAScript 在带标签的模版字符串中转义序列的语法限制。
之前，\u开始一个 unicode 转义，\x开始一个十六进制转义，\后跟一个数字开始一个八进制转义。这使得创建特定的字符串变得不可能，例如Windows文件路径 C:\uuu\xxx\111。
