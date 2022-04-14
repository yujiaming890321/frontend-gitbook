/*
 * @Author: yujiaming
 * @Date: 2021-08-18 17:39:52
 * @LastEditTime: 2021-08-18 17:55:13
 * @LastEditors: yujiaming
 */
Promise.resolve(1)
  .then((res) => {
    console.log(res)
    return 2
  })
  .catch((err) => 3)
  .then((res) => console.log(res))
