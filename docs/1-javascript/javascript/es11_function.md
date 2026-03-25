# es11 - ECMA2020

## 动态 import ()

在 ES 2015 定义的模块语法中，所有模块导入语法都是静态声明的：

```js
import aExport from "./module"
import * as exportName from "./module"
import { export1, export2 as alias2 } from "./module"
import "./module"
```

```js
import('lodash').then(_ => {
    // other
})

// utils
export default 'hello lxm';
export const x = 11;
export const y = 22;

// 导入
import('a').then(module => {
    console.info(module)
})

// 结果：
{
   default: 'hello lxm'',
   x: 11,
   y: 22,
}
```

## 空值合并运算符（?? ）

大家可能遇到过，如果一个变量是空，需要给它赋值为一个默认值的情况。通常我们会这样写：

```js
let num = number || 222
let num = (number !== undefined) ? number : 222
```

现在可以使用了??运算符了，它只有当操作符左边的值是null或者undefined的时候，才会取操作符右边的值
而且该运算符也支持短路特性
但需要注意一点，该运算符不能与 AND 或 OR 运算符共用，否则会抛出语法异常
这个操作符的主要设计目的是为了给可选链操作符提供一个补充运算符，因此通常是和可选链操作符一起使用的

```js
let num = number ?? 222

const x = a ?? getDefaultValue()

a && b ?? "default"    // SyntaxError
(a && b) ?? "default"

const x = a?.b ?? 0;
```

## 可选链接

建议只在必要的时候才使用可选链操作符。

```js
a?.b
a?.()
a?.b?.[0]?.()?.d
```

## BigInt

在 ES 中，所有 Number 类型的值都使用 64 位浮点数格式存储，因此 Number 类型可以有效表示的最大整数为 2^53。而使用新的 BigInt 类型，可以操作任意精度的整数。

两种使用方式：1、在数字字面量的后面添加后缀n；2、使用其构造函数BigInt

```js
const bigInt = 9007199254740993n
const bigInt = BigInt(9007199254740992)

// 在超过 Number 最大整数限制时，我们也可以改为传入一个可能被正确解析的字符串
const bigInt = BigInt('9007199254740993')
```

BigInt 也支持+、-、*、**、%运算符

```js
3n + 2n    // => 5n
3n * 2n    // => 6n
3n ** 2n   // => 9n
3n % 2n    // => 1n
```

因为 BigInt 是纯粹的整数类型，无法表示小数位，因此 BigInt 的除法运算（/）的结果值依然还是一个整数，即向下取整

```js
const bigInt = 3n;
bigInt / 2n;    // => 1n，而不是 1.5n
```

支持位运算符，除了无符号右移运算符

```js
1n & 3n    // => 1n
1n | 3n    // => 3n
1n ^ 3n    // => 2n
~1n        // => -2n
1n << 3n   // => 8n
1n >> 3n   // => 0n

1n >>> 3n  // Uncaught TypeError: BigInts have no unsigned right shift, use >> instead
```

BigInt 可以和字符串之间使用+运算符连接

```js
1n + ' Number'   // => 1 Number
'Number ' + 2n   // => Number 2
```

下面这些场景不支持使用BigInt：

BigInt 无法和 Number 一起运算，会抛出类型异常

```js
1n + 1
// Uncaught TypeError: Cannot mix BigInt and other types, use explicit conversions
```

一些内置模块如 Math 也不支持 BigInt，同样会抛出异常

```js
Math.pow(2n, 64n)
// Uncaught TypeError: Cannot convert a BigInt value to a number
```

BigInt 和 Number 相等，但并不严格相等，但他们之间可以比较大小

```js
1n == 1    // => true
1n === 1   // => false

1n < 2     // => true
1n < 1     // => false

2n > 1     // => true
2n > 2     // => false
```

转换为 Boolean 值时，也和 Number 一样，0n 转为 false，其它值转为 true

```js
!!0n       // => false
!!1n       // => true
```

两者之间只能使用对方的构造函数进行转换，但两者之间的转换也都有一些边界问题

```js
Number(1n) // => 1
BigInt(1)  // => 1n

// 当 BigInt 值的精度超出 Number 类型可表示的范围时，会出现精度丢失的问题
Number(9007199254740993n)
// => 9007199254740992

// 当 Number 值中有小数位时，BigInt 会抛出异常
BigInt(1.1)
// VM4854:1 Uncaught RangeError: The number 1.1 cannot be converted to a BigInt because it is not an integer
```

配套地，在类型化数组中也提供了与 BigInt 对应的两个数组类型：BigInt64Array和BigUint64Array

```js
const array = new BigInt64Array(4);

array[0]   // => 0n

array[0] = 2n
array[0]   // => 2n
```

但因为每个元素限定只有 64 位，因此即便使用无符号类型，最大也只能表示 2^64 - 1

```js
const array = new BigUint64Array(4);

array[0] = 2n ** 64n
array[0]   // => 0n

array[0] = 2n ** 64n - 1n
array[0]   // => 18446744073709551615n
```

## globalThis

> 浏览器：window、worker：self、node：global

在浏览器环境中，我们可以有多种方式访问到全局对象，最常用到的肯定是 window，但除此之外还有 self，以及在特殊场景下使用的 frames、paraent 以及 top。

早先，我们可以通过下面这段代码较为方便地拿到全局对象：

```js
const globals = (new Function('return this;'))()
```

但受到 Chrome APP 内容安全策略的影响（为缓解跨站脚本攻击的问题，该政策要求禁止使用 eval 及相关的功能），上面这段代码将无法在 Chrome APP 的运行环境中正常执行。

无奈之下，像 es6-shim 这种库就只能穷举所有可能的全局属性：

```js
ar getGlobal = function () {
    // the only reliable means to get the global object is
    // `Function('return this')()`
    // However, this causes CSP violations in Chrome apps.
    if (typeof self !== 'undefined') { return self; }
    if (typeof window !== 'undefined') { return window; }
    if (typeof global !== 'undefined') { return global; }
    throw new Error('unable to locate global object');
};

var globals = getGlobal();

if (!globals.Reflect) {
    defineProperty(globals, 'Reflect', {}, true);
}
```

通过 globalThis，我们终于可以使用一种标准的方法拿到全局对象，而不用关心代码的运行环境。对于 es6-shim 这种库来说，这是一个极大的便利特性：

```js
if (!globalThis.Reflect) {
    defineProperty(globalThis, 'Reflect', {}, true);
}
```

## Promise.allSettled

> 在Promise上有提供一组组合方法（比如最常用到的Promise.all），它们都是接收多个 promise 对象，并返回一个表示组合结果的新的 promise，依据所传入 promise 的结果状态，组合后的 promise 将切换为不同的状态。

目前为止这类方法一共有如下四个，这四个方法之间仅有判断逻辑上的区别，也都有各自所适用的场景
* Promise.all 返回一个组合后的 promise，当所有 promise 全部切换为 fulfilled 状态后，该 promise 切换为 fulfilled 状态；但若有任意一个 promise 切换为 rejected 状态，该 promise 将立即切换为 rejected 状态；
* Promise.race 返回一个组合后的 promise，当 promise 中有任意一个切换为 fulfilled 或 rejected 状态时，该 promise 将立即切换为相同状态；
* Promise.allSettled 返回一个组合后的 promise，当所有 promise 全部切换为 fulfilled 或 rejected 状态时，该 promise 将切换为 fulfilled 状态；
* Promise.any 返回一个组合后的 promise，当 promise 中有任意一个切换为 fulfilled 状态时，该 promise 将立即切换为 fulfilled 状态，但只有所有 promise 全部切换为 rejected 状态时，该 promise 才切换为 rejected 状态。（ECMAScript2021 ）

因为结果值是一个数组，所以你可以很容易地过滤出任何你感兴趣的结果信息

```js
// 获取所有 fulfilled 状态的结果信息
results.filter( result => result.status === "fulfilled" )
// 获取所有 rejected 状态的结果信息
results.filter( result => result.status === "rejected" )
// 获取第一个 rejected 状态的结果信息
results.find( result => result.status === "rejected" )
```

## for-in 结构

> 用于规范for-in语句的遍历顺序

之前的 ES 规范中几乎没有指定 for-in 语句在遍历时的顺序，但各 ES 引擎的实现在大多数情况下都是趋于一致的，只有在一些边界情况时才会有所差别。

我们很难能够要求各引擎做到完全一致，主要原因在于 for-in 是 ES 中所有遍历 API 中最复杂的一个，再加上规范的疏漏，导致各大浏览器在实现该 API 时都有很多自己特有的实现逻辑，各引擎的维护人员很难有意愿去重新审查这部分的代码。

规范中还提供了一份示例代码，以供各引擎在实现 for-in 逻辑时参考使用

```js
function* EnumerateObjectProperties(obj) {
    const visited = new Set();

    for (const key of Reflect.ownKeys(obj)) {
        if (typeof key === "symbol") continue;
        const desc = Reflect.getOwnPropertyDescriptor(obj, key);
        if (desc) {
            visited.add(key);
            if (desc.enumerable) yield key;
        }
    }

    const proto = Reflect.getPrototypeOf(obj);
    if (proto === null) return;

    for (const protoKey of EnumerateObjectProperties(proto)) {
        if (!visited.has(protoKey)) yield protoKey;
    }
}
```
