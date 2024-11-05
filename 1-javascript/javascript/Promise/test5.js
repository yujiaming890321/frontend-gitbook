/*
 * @Author: yujiaming
 * @Date: 2021-08-18 17:39:52
 * @LastEditTime: 2021-08-20 10:52:54
 * @LastEditors: yujiaming
 */
Promise.resolve(1)
    .then((x) => x + 1)
    .then((x) => {
        throw new Error('My Error')
    })
    .catch(() => 1)
    .then((x) => x + 1)
    .then((x) => console.log('console', x))
    .catch((error) => console.log('error', error))

// console 2
