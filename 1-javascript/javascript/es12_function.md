# es12 - ECMA2021

## replaceAll

> 模式的所有匹配都会被替代项替换。模式可以是字符串或正则表达式，而替换项可以是字符串或针对每次匹配执行的函数。并返回一个全新的字符串

```js
const str = "student is a real student";
const newStr = str.replace(/student/g, "hahaha");

const str = "student is a real student";
const newStr = str.replaceAll('student', "hahaha");
console.log(newStr);
```

## Promise.any

可以把 Promise.any 理解成 Promise.all 的相反操作。
Promise.any 也可以接受一个 Promise 数组，当其中任何一个 Promise 完成（fullfill）时，就返回那个已经有完成值的 Promise。
如果所有的 Promise 都拒绝（reject），则返回一个拒绝的 Promise，该 Promise 的返回值是一个 AggregateError 对象。

```js
const p1 = new Promise((resolve, reject) => {
  setTimeout(() => resolve("A"), Math.floor(Math.random() * 1000));
});
const p2 = new Promise((resolve, reject) => {
  setTimeout(() => resolve("B"), Math.floor(Math.random() * 1000));
});
const p3 = new Promise((resolve, reject) => {
  setTimeout(() => resolve("C"), Math.floor(Math.random() * 1000));
});

(async function () {
  const result = await Promise.any([p1, p2, p3]);
  console.log(result); // 输出结果可能是 "A", "B" 或者 "C"
})();

const p = new Promise((resolve, reject) => reject());

try {
  (async function () {
    const result = await Promise.any([p]);
    console.log(result);
  })();
} catch (error) {
  console.log(error.errors);
}
```

## 逻辑赋值操作符 ??=、&&=、 ||=

```js
let a = 1;
a = a + 2;

let a = 1;
a += 2;

let num = number || 222
let num = number ?? 222

// 等同于 a = a || b
a ||= b;
// 等同于 c = c && d
c &&= d;
// 等同于 e = e ?? f
e ??= f;
```

## WeakRef

WeakRef是一个 Class，一个WeakRef对象可以让你拿到一个对象的弱引用。这样，就可以不用阻止垃圾回收这个对象了。 可以使用其构造函数来创建一个WeakRef对象。
我们可以用WeakRef.prototype.deref()来取到anObject的值。但是，在被引用对象被垃圾回收之后，这个函数就会返回undefined。

```js
// anObject 不会因为 ref 引用了这个对象，而不会被垃圾回收
let ref = new WeakRef(anObject);

// 如果 someObj 被垃圾回收了，则 obj 就会是 undefined
let obj = ref.deref();
```

## 下划线 (_) 分隔符

当你要写一个很长的数字的时候，数字太长会导致可读性很差。使用了数字分隔符 _ （下划线），就可以让数字读的更清晰

```js
let x = 233333333

let x = 2_3333_3333
// x 的值等同于 233333333，只是这样可读性更强，不用一位一位数了
```

## Intl.ListFormat

Intl.ListFormat 是一个构造函数，用来处理和多语言相关的对象格式化操作。

```js
const list = ['Apple', 'Orange', 'Banana']
new Intl.ListFormat('en-GB', { style: 'long', type: 'conjunction' }).format(list);
// "Apple, Orange and Banana"
new Intl.ListFormat('zh-cn', { style: 'short', type: 'conjunction' }).format(list);
// 会根据语言来返回相应的格式化操作
// "Apple、Orange和Banana"
```

## Intl.DateTimeFormat API 中的 dateStyle 和 timeStyle 的配置项

Intl.ListFormat 是一个用来处理多语言下的时间日期格式化的函数。ES2021 中给这个函数添加了两个新的参数：dateStyle 和 timeStyle。
dateStyle 和 timeStyle 选项可用于请求给定长度的，特定于语言环境的日期和时间。

```js
let a = new Intl.DateTimeFormat("en" , {
  timeStyle: "short"
});
console.log('a = ', a.format(Date.now())); // "13:31"
let b = new Intl.DateTimeFormat("en" , {
  dateStyle: "short"
});
console.log('b = ', b.format(Date.now())); // "21.03.2012"
// 可以通过同时传入 timeStyle 和 dateStyle 这两个参数来获取更完整的格式化时间的字符串
let c = new Intl.DateTimeFormat("en" , {
  timeStyle: "medium",
  dateStyle: "short"
});
console.log('c = ', c.format(Date.now())); // "21.03.2012, 13:31"
```

timeStyle 和 dateStyle 配置项有三个（下面以timeStyle为例）：

short：11:27 PM
medium：11:27:57 PM
long：11:27:57 PM GMT+11
