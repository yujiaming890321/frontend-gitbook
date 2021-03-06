# 手写 Promise

## 1.promise/A+规范规定

promise 是一个拥有 then 方法的对象或函数，其行为符合本规范；
一个 Promise 的当前状态必须为以下三种状态中的一种：等待态（Pending）、执行态（Fulfilled）和拒绝态（Rejected）。
`
const PENDING = 'pending'
const FULFILLED = 'fulfilled'
const REJECTED = 'rejected'

function MyPromise(executor) {
var \_this = this
this.state = PENDING; //状态
this.value = undefined; //成功结果
this.reason = undefined; //失败原因
function resolve(value) {}
function reject(reason) {}
}

MyPromise.prototype.then = function (onFulfilled, onRejected) {
};

module.exports = MyPromise;
`

## 2.当我们实例化 Promise 时，构造函数会马上调用传入的执行函数 executor。

因此在 Promise 中构造函数立马执行，同时将 resolve 函数和 reject 函数作为参数传入

但是 executor 也会可能存在异常，因此通过 try/catch 来捕获一下异常情况。

```
const PENDING = 'pending'
const FULFILLED = 'fulfilled'
const REJECTED = 'rejected'

function MyPromise(executor) {
    var _this = this
    this.state = PENDING; //状态
    this.value = undefined; //成功结果
    this.reason = undefined; //失败原因
    function resolve(value) {}
    function reject(reason) {}

    try {
        executor(resolve, reject);
    } catch (e) {
        reject(e);
    }
}

MyPromise.prototype.then = function (onFulfilled, onRejected) {
};

module.exports = MyPromise;
```

## 3.promise/A+规范中规定

当 Promise 对象已经由等待态（Pending）改变为执行态（Fulfilled）或者拒绝态（Rejected）后，就不能再次更改状态，且终值也不可改变。

```
const PENDING = 'pending'
const FULFILLED = 'fulfilled'
const REJECTED = 'rejected'

function MyPromise(executor) {
    var _this = this
    this.state = PENDING; //状态
    this.value = undefined; //成功结果
    this.reason = undefined; //失败原因
    function resolve(value) {
        if(_this.state === PENDING){
            _this.state = FULFILLED
            _this.value = value
        }
    }
    function reject(reason) {
        if(_this.state === PENDING){
            _this.state = REJECTED
            _this.reason = reason
        }
    }

    try {
        executor(resolve, reject);
    } catch (e) {
        reject(e);
    }
}

MyPromise.prototype.then = function (onFulfilled, onRejected) {
};

module.exports = MyPromise;
```

## 4.当 Promise 的状态改变之后，不管成功还是失败，都会触发 then 回调函数。因此，then 的实现也很简单，就是根据状态的不同，来调用不同处理终值的函数。

```
const PENDING = 'pending'
const FULFILLED = 'fulfilled'
const REJECTED = 'rejected'

function MyPromise(executor) {
    var _this = this
    this.state = PENDING; //状态
    this.value = undefined; //成功结果
    this.reason = undefined; //失败原因
    function resolve(value) {
        if(_this.state === PENDING){
            _this.state = FULFILLED
            _this.value = value
        }
    }
    function reject(reason) {
        if(_this.state === PENDING){
            _this.state = REJECTED
            _this.reason = reason
        }
    }

    try {
        executor(resolve, reject);
    } catch (e) {
        reject(e);
    }
}

MyPromise.prototype.then = function (onFulfilled, onRejected) {
    if(this.state === FULFILLED){
        typeof onFulfilled === 'function' && onFulfilled(this.value)
    }
    if(this.state === REJECTED){
        typeof onRejected === 'function' && onRejected(this.reason)
    }
};

module.exports = MyPromise;
```

## 5.当 then 里面函数运行时，resolve 由于是异步执行的，还没有来得及修改 state，此时还是 PENDING 状态；因此我们需要对异步的情况做一下处理。

参考发布订阅模式，在执行 then 方法的时候，如果当前还是 PENDING 状态，就把回调函数寄存到一个数组中，当状态发生改变时，去数组中取出回调函数；

```
const PENDING = 'pending'
const FULFILLED = 'fulfilled'
const REJECTED = 'rejected'

function MyPromise(executor) {
    var _this = this
    this.state = PENDING; //状态
    this.value = undefined; //成功结果
    this.reason = undefined; //失败原因
    this.onFulfilled = [];//成功的回调
    this.onRejected = []; //失败的回调
    function resolve(value) {
        if(_this.state === PENDING){
            _this.state = FULFILLED
            _this.value = value
            _this.onFulfilled.forEach(fn => fn(value))
        }
    }
    function reject(reason) {
        if(_this.state === PENDING){
            _this.state = REJECTED
            _this.reason = reason
            _this.onRejected.forEach(fn => fn(reason))
        }
    }

    try {
        executor(resolve, reject);
    } catch (e) {
        reject(e);
    }
}

MyPromise.prototype.then = function (onFulfilled, onRejected) {
    if(this.state === FULFILLED){
        typeof onFulfilled === 'function' && onFulfilled(this.value)
    }
    if(this.state === REJECTED){
        typeof onRejected === 'function' && onRejected(this.reason)
    }
    if(this.state === PENDING){
        typeof onFulfilled === 'function' && this.onFulfilled.push(onFulfilled)
        typeof onRejected === 'function' && this.onRejected.push(onRejected)
    }
};

module.exports = MyPromise;
```

## 6. then 的逻辑就开始复杂了

promise/A+规范

then 方法必须返回一个 promise 对象
then 的执行过程：

如果 onFulfilled 或者 onRejected 返回一个值 x ，则运行下面的 Promise 解决过程：[[Resolve]](promise2, x)
如果 onFulfilled 或者 onRejected 抛出一个异常 e ，则 promise2 必须拒绝执行，并返回拒因 e
如果 onFulfilled 不是函数且 promise1 成功执行， promise2 必须成功执行并返回相同的值
如果 onRejected 不是函数且 promise1 拒绝执行， promise2 必须拒绝执行并返回相同的据因
第一点，我们知道 onFulfilled 和 onRejected 执行之后都会有一个返回值 x，对返回值 x 处理就需要用到 Promise 解决过程；

第二点，需要对 onFulfilled 和 onRejected 进行异常处理，没什么好说的；

第三和第四点，说的其实是一个问题，如果 onFulfilled 和 onRejected 两个参数没有传，则继续往下传（值的传递特性）

/\*\*

- Promise 解决过程
- 是对新的 promise2 和上一个执行结果 x 的处理，规范中定义的第一点
- 操作说明：
  1.x 与 promise 相等 1.如果 promise 和 x 指向同一对象，以 TypeError 为据因拒绝执行 promise
  2.x 为 Promise 1.如果 x 处于等待态， promise 需保持为等待态直至 x 被执行或拒绝 2.如果 x 处于执行态，用相同的值执行 promise 3.如果 x 处于拒绝态，用相同的据因拒绝 promise
  3.x 为对象或函数 1.把 x.then 赋值给 then 2.如果取 x.then 的值时抛出错误 e ，则以 e 为据因拒绝 promise 3.如果 then 是函数，将 x 作为函数的作用域 this 调用之。传递两个回调函数作为参数，第一个参数叫做 resolvePromise ，第二个参数叫做 rejectPromise: 1.如果 resolvePromise 以值 y 为参数被调用，则运行 [Resolve] 2.如果 rejectPromise 以据因 r 为参数被调用，则以据因 r 拒绝 promise 3.如果 resolvePromise 和 rejectPromise 均被调用，或者被同一参数调用了多次，则优先采用首次调用并忽略剩下的调用 4.如果 then 不是函数，以 x 为参数执行 promise 4.如果 x 不为对象或者函数，以 x 为参数执行 promise
- @param promise2 新的 Promise 对象
- @param x 上一个 then 的返回值
- @param resolve promise2 的 resolve
- @param reject promise2 的 reject
  \*/

```
function resolvePromise(promise2, x, resolve, reject) {

}

MyPromise.prototype.then = function (onFulfilled, onRejected) {
   var _this = this
   onFulfilled = typeof onFulfilled === 'function' ? onFulfilled : value => value
   onRejected = typeof onRejected === 'function' ? onRejected : reason => { throw reason }
   var promise2 = new Promise((resolve, reject)=>{
       if(_this.state === FULFILLED){
           setTimeout(()=>{
               try {
                   let x = onFulfilled(_this.value)
                   resolvePromise(promise2, x, resolve, reject)
               } catch (error) {
                   reject(error)
               }
           })
       } else if(_this.state === REJECTED){
           setTimeout(()=>{
               try {
                   let x = onRejected(_this.reason)
                   resolvePromise(promise2, x ,resolve, reject)
               } catch (error) {
                   reject(error)
               }
           })
       } else if(_this.state === PENDING){
           _this.onFulfilled.push(()=>{
               setTimeout(()=>{
                   try {
                       let x = onFulfilled(_this.value)
                       resolvePromise(promise2, x, resolve, reject)
                   } catch (error) {
                       reject(error)
                   }
               })
           })
           _this.onRejected.push(()=>{
               setTimeout(()=>{
                   try {
                       let x = onRejected(_this.reason)
                       resolvePromise(promise2, x ,resolve, reject)
                   } catch (error) {
                       reject(error)
                   }
               })
           })
       }
   })
   return promise2
};
```

定义好函数后，根据规范写出实现

```
function resolvePromise(promise2, x, resolve, reject) {
    if (promise2 === x) {
        reject(new TypeError('Chaining cycle'));
    }
    if (x !== null && (typeof x === 'object' || typeof x === 'function')) {
        //函数或对象
        // 只执行一次resolve/reject
        let used;
        // 取then的时候也需要try/catch
        try {
            let then = x.then
            // 取出then后，回到3.3，判断如果是一个函数，就将 x 作为函数的作用域 this 调用，同时传入两个回调函数作为参数。
            if(typeof then === 'function'){
                then.call(x, (y)=>{
                    if (used) return;
                    used = true
                    resolvePromise(promise2, y, resolve, reject)
                }, (r) =>{
                    if (used) return;
                    used = true
                    reject(r)
                })
            } else {
                if (used) return;
                used = true
                resolve(x)
            }
        } catch(e){
            if (used) return;
            used = true
            reject(e)
        }
    } else {
        //普通值
        resolve(x)
    }
}
```

## 最终版

```
/**
* Promise 解决过程
* 是对新的promise2和上一个执行结果 x 的处理，规范中定义的第一点
* 操作说明：
   1.x 与 promise 相等
       1.如果 promise 和 x 指向同一对象，以 TypeError 为据因拒绝执行 promise
   2.x 为 Promise
       1.如果 x 处于等待态， promise 需保持为等待态直至 x 被执行或拒绝
       2.如果 x 处于执行态，用相同的值执行 promise
       3.如果 x 处于拒绝态，用相同的据因拒绝 promise
   3.x 为对象或函数
       1.把 x.then 赋值给 then
       2.如果取 x.then 的值时抛出错误 e ，则以 e 为据因拒绝 promise
       3.如果 then 是函数，将 x 作为函数的作用域 this 调用之。传递两个回调函数作为参数，第一个参数叫做 resolvePromise ，第二个参数叫做 rejectPromise:
           1.如果 resolvePromise 以值 y 为参数被调用，则运行 [Resolve]
           2.如果 rejectPromise 以据因 r 为参数被调用，则以据因 r 拒绝 promise
           3.如果 resolvePromise 和 rejectPromise 均被调用，或者被同一参数调用了多次，则优先采用首次调用并忽略剩下的调用
           4.如果 then 不是函数，以 x 为参数执行 promise
   4.如果 x 不为对象或者函数，以 x 为参数执行 promise
* @param promise2 新的Promise对象
* @param x 上一个then的返回值
* @param resolve promise2的resolve
* @param reject promise2的reject
*/
function resolvePromise(promise2, x, resolve, reject) {
   if (promise2 === x) {
       reject(new TypeError('Chaining cycle'));
   }
   if (x !== null && (typeof x === 'object' || typeof x === 'function')) {
       //函数或对象
       // 只执行一次resolve/reject
       let used;
       // 取then的时候也需要try/catch
       try {
           let then = x.then
           // 取出then后，回到3.3，判断如果是一个函数，就将 x 作为函数的作用域 this 调用，同时传入两个回调函数作为参数。
           if(typeof then === 'function'){
               then.call(x, (y)=>{
                   if (used) return;
                   used = true
                   resolvePromise(promise2, y, resolve, reject)
               }, (r) =>{
                   if (used) return;
                   used = true
                   reject(r)
               })
           } else {
               if (used) return;
               used = true
               resolve(x)
           }
       } catch(e){
           if (used) return;
           used = true
           reject(e)
       }
   } else {
       //普通值
       resolve(x)
   }
}

MyPromise.prototype.then = function (onFulfilled, onRejected) {
   var _this = this
   onFulfilled = typeof onFulfilled === 'function' ? onFulfilled : value => value
   onRejected = typeof onRejected === 'function' ? onRejected : reason => { throw reason }
   var promise2 = new Promise((resolve, reject)=>{
       if(_this.state === FULFILLED){
           setTimeout(()=>{
               try {
                   let x = onFulfilled(_this.value)
                   resolvePromise(promise2, x, resolve, reject)
               } catch (error) {
                   reject(error)
               }
           })
       } else if(_this.state === REJECTED){
           setTimeout(()=>{
               try {
                   let x = onRejected(_this.reason)
                   resolvePromise(promise2, x ,resolve, reject)
               } catch (error) {
                   reject(error)
               }
           })
       } else if(_this.state === PENDING){
           _this.onFulfilled.push(()=>{
               setTimeout(()=>{
                   try {
                       let x = onFulfilled(_this.value)
                       resolvePromise(promise2, x, resolve, reject)
                   } catch (error) {
                       reject(error)
                   }
               })
           })
           _this.onRejected.push(()=>{
               setTimeout(()=>{
                   try {
                       let x = onRejected(_this.reason)
                       resolvePromise(promise2, x ,resolve, reject)
                   } catch (error) {
                       reject(error)
                   }
               })
           })
       }
   })
   return promise2
};
```
