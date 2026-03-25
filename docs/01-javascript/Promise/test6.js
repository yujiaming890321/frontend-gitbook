/*
 * @Author: yujiaming
 * @Date: 2021-08-18 17:39:52
 * @LastEditTime: 2021-08-20 10:53:17
 * @LastEditors: yujiaming
 */
Promise.resolve(1)
    .then((x) => x + 1)
    .then((x) => Promise.reject(2))
    .then((x) => console.log('x:' + x))
    .catch((error) => console.log('error:' + error))

// error:1
