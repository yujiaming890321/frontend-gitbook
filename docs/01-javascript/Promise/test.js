/*
 * @Author: yujiaming
 * @Date: 2021-08-16 17:55:03
 * @LastEditTime: 2021-08-18 17:39:51
 * @LastEditors: yujiaming
 */
new Promise(function (resolve, reject) {
    console.log(1)
    resolve('success')
    console.log(2)
    reject('error')
    console.log(3)
})
    .then(function (value) {
        console.log('then', value)
    })
    .catch(function (err) {
        console.err('error:', err)
    })

// 1
// 2
// 3
// then success
