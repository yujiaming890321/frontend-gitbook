/*
 * @Author: yujiaming
 * @Date: 2021-08-16 17:51:27
 * @LastEditTime: 2021-08-20 16:36:11
 * @LastEditors: yujiaming
 */
const PENDING = 'pending'
const FULFILLED = 'fulfilled'
const REJECTED = 'rejected'

function MyPromise(executor) {
  var _this = this
  this.state = PENDING //状态
  this.value = undefined //成功结果
  this.reason = undefined //失败原因
  this.onFulfilled = [] //成功的回调
  this.onRejected = [] //失败的回调
  function resolve(value) {
    if (_this.state === PENDING) {
      _this.state = FULFILLED
      _this.value = value
      _this.onFulfilled.forEach((fn) => fn(value))
    }
  }
  function reject(reason) {
    if (_this.state === PENDING) {
      _this.state = REJECTED
      _this.reason = reason
      _this.onRejected.forEach((fn) => fn(reason))
    }
  }

  try {
    executor(resolve, reject)
  } catch (e) {
    reject(e)
  }
}

/**
 * Promise 解决过程
 * 是对新的promise2和上一个执行结果 x 的处理，规范中定义的第一点
 * 操作说明：
    1.x 与 promise 相等
        如果 promise 和 x 指向同一对象，以 TypeError 为据因拒绝执行 promise
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
    reject(new TypeError('Chaining cycle'))
  }
  if (x !== null && (typeof x === 'object' || typeof x === 'function')) {
    //函数或对象
    // 只执行一次resolve/reject
    let used
    // 取then的时候也需要try/catch
    try {
      let then = x.then
      // 取出then后，回到3.3，判断如果是一个函数，就将 x 作为函数的作用域 this 调用，同时传入两个回调函数作为参数。
      if (typeof then === 'function') {
        then.call(
          x,
          (y) => {
            if (used) return
            used = true
            resolvePromise(promise2, y, resolve, reject)
          },
          (r) => {
            if (used) return
            used = true
            reject(r)
          }
        )
      } else {
        if (used) return
        used = true
        resolve(x)
      }
    } catch (e) {
      if (used) return
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
  onFulfilled =
    typeof onFulfilled === 'function' ? onFulfilled : (value) => value
  onRejected =
    typeof onRejected === 'function'
      ? onRejected
      : (reason) => {
          throw reason
        }
  var promise2 = new Promise((resolve, reject) => {
    if (_this.state === FULFILLED) {
      setTimeout(() => {
        try {
          let x = onFulfilled(_this.value)
          resolvePromise(promise2, x, resolve, reject)
        } catch (error) {
          reject(error)
        }
      })
    } else if (_this.state === REJECTED) {
      setTimeout(() => {
        try {
          let x = onRejected(_this.reason)
          resolvePromise(promise2, x, resolve, reject)
        } catch (error) {
          reject(error)
        }
      })
    } else if (_this.state === PENDING) {
      _this.onFulfilled.push(() => {
        setTimeout(() => {
          try {
            let x = onFulfilled(_this.value)
            resolvePromise(promise2, x, resolve, reject)
          } catch (error) {
            reject(error)
          }
        })
      })
      _this.onRejected.push(() => {
        setTimeout(() => {
          try {
            let x = onRejected(_this.reason)
            resolvePromise(promise2, x, resolve, reject)
          } catch (error) {
            reject(error)
          }
        })
      })
    }
  })
  return promise2
}

module.exports = MyPromise

// new MyPromise((resolve) => {
//     resolve('p1')
// }).then(() => {
//     return new MyPromise((resolve) => {
//         resolve(new MyPromise((resolve) => {
//             resolve('p2')
//         }))
//     })
// }).then((res) => {
//     console.log(res)
// })

// new MyPromise((resolve, reject) => {
//     reject('p1')
// }).then(null, (res) => {
//     return new MyPromise((resolve) => {
//         resolve(new MyPromise((resolve, reject) => {
//             reject('p2')
//         }))
//     })
// }).then((res) => {
//     console.log("resolve:" + res)
// }, (res) => {
//     console.log("reject:" + res)
// })

let promise1 = new Promise((resolve, reject) => {
  reject('p1')
})
let thenable1 = promise1.then(null, (res) => {
  let promise2 = new Promise((resolve, reject) => {
    let promise3 = new Promise((resolve, reject) => {
      reject('p2')
    })
    resolve(promise3)
  })
  return promise2
})

thenable1.then(
  (res) => {
    console.log('resolve:' + res)
  },
  (res) => {
    console.log('reject:' + res)
  }
)

let thenable2 = promise1.then(null, (res) => {
  let promise2 = new Promise((resolve, reject) => {
    let promise3 = new Promise((resolve, reject) => {
      resolve('p2')
    })
    reject(promise3)
  })
  return promise2
})

thenable2.then(
  (res) => {
    console.log('resolve:' + res)
  },
  (res) => {
    console.log('reject:' + res)
  }
)
