/*
 * @Author: yujiaming
 * @Date: 2021-08-18 17:39:52
 * @LastEditTime: 2021-08-18 17:40:06
 * @LastEditors: yujiaming
 */
let a = Promise.reject('a')
  .then(() => {
    console.log('a passed')
  })
  .catch(() => {
    console.log('a failed')
  })

Promise.reject('b')
  .catch(() => {
    console.log('b failed')
  })
  .then(() => {
    console.log('b passed')
  })
