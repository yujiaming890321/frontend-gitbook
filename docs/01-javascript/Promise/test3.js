/*
 * @Author: yujiaming
 * @Date: 2021-08-18 17:39:52
 * @LastEditTime: 2021-08-18 17:55:03
 * @LastEditors: yujiaming
 */
setTimeout(function () {
    console.log(1)
}, 0)

new Promise(function (resolve) {
    console.log(2)
    for (var i = 0; i < 100; i++) {
        i == 99 && resolve()
    }
    console.log(3)
}).then(function () {
    console.log(4)
})
console.log(5)

// 2
// 3
// 5
// 4
// 1
