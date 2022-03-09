# Promise

Promise 有三种状态，这个 Promise 一旦从等待状态变成为其他状态就永远不能更改状态了。

- 等待中（pending）
- 完成了（resolved）
- 拒绝了（rejected）

当我们在构造 Promise 的时候，构造函数内部的代码是立即执行的。

```js
new Promise((resolve, reject) => {
	console.log('new Promise')
	resolve('success')
})
console.log('finifsh')

// 先打印new Promise， 再打印 finifsh
```

Promise 实现了链式调用，也就是说每次调用 then 之后返回的都是一个全新 Promise，原因也是因为状态不可变。
如果你在 then 中 使用了 return，那么 return 的值会被 Promise.resolve() 包装。

```js
Promise.resolve(1)
	.then((res) => {
		console.log(res) // => 1
		return 2 // 包装成 Promise.resolve(2)
	})
	.then((res) => {
		console.log(res) // => 2
	})
```

当然了，Promise 也很好地解决了回调地狱的问题

```js
ajax(url)
	.then((res) => {
		console.log(res)
		return ajax(url1)
	})
	.then((res) => {
		console.log(res)
		return ajax(url2)
	})
	.then((res) => console.log(res))
```

其实它也是存在一些缺点的，比如无法取消 Promise，错误需要通过回调函数捕获。
