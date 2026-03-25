# es8 - ES2017

## async/await

## Object.values()

Object.values()是一个与Object.keys()类似的新函数，但返回的是Object自身属性的所有值，不包括继承的值。

## Object.entries()

Object.entries()函数返回一个给定对象自身可枚举属性的键值对的数组。

## String padding

允许将空字符串或其他字符串添加到原始字符串的开头或结尾

```js
String.padStart(targetLength,[padString])

console.log('0.0'.padStart(4,'10')) //10.0 
console.log('0.0'.padStart(20))// 0.00

String.padEnd(targetLength,padString])
console.log('0.0'.padEnd(4,'0')) //0.00    
console.log('0.0'.padEnd(10,'0'))//0.00000000
```

## 函数参数列表结尾允许逗号

方便使用git进行多人协作开发时修改同一个函数减少不必要的行变更。

## Object.getOwnPropertyDescriptors()

用来获取一个对象的所有自身属性的描述符,如果没有任何自身属性，则返回空对象。

```js
const obj = {
	name: 'lxm',
	get age() { return '28' }
};
Object.getOwnPropertyDescriptors(obj)
```

## SharedArrayBuffer 对象

用来表示一个通用的，固定长度的原始二进制数据缓冲区，类似于 ArrayBuffer 对象，它们都可以用来在共享内存（shared memory）上创建视图。与 ArrayBuffer 不同的是，SharedArrayBuffer 不能被分离。

## Atomics 对象

提供了一组静态方法用来对 SharedArrayBuffer 对象进行原子操作。这些原子操作属于 Atomics 模块。与一般的全局对象不同，Atomics 不是构造函数，因此不能使用 new 操作符调用，也不能将其当作函数直接调用。Atomics 的所有属性和方法都是静态的（与 Math 对象一样）

