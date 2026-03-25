# PromiseQueue

支持限制并发数

```js
class PromiseQueue {
  limit: number
  active: number
  queue: Array<() => Promise<any>>

  constructor(limit = 3) {
    // 并发限制
    this.limit = limit;
    // 当前活跃数
    this.active = 0;
    // 异步队列
    this.queue = [];
  }

  push(p: () => Promise<any>) {
    this.queue.push(p);
    this.next();
    return this;
  }

  next() {
    if (this.active >= this.limit || !this.queue.length) {
      return;
    }
    this.active++;
    const promiseFac = this.queue.shift();
    if(promiseFac) {
        let promise = promiseFac();
        promise.then((res) => {
            console.log(res)
            this.active--;
            this.next();
        },(error) => {
            console.log(error)
            this.active--;
            this.next();
        })
    }
  }
}
```

[demo 测试地址](https://www.typescriptlang.org/zh/play?#code/MYGwhgzhAEAKBOB7AtgSwgUwIoFcN+gG8AoaaEVNAFwC5oA7HZAIw3lOjGCtQDcM6jFmw4BHPHjoBBePDABPADwAKAJTQAvAD44SNJkVh68rVuIdgiehCrwc3RPGUVqm6AGZ1JMmQD0v6EA3PUBF5UAFNMA2JQ4yKgALdAA6F1QqNySqAG4o6H9oQGV9QFklQG5bQGHYwAdTLNiErh5+NwAGTJ9sgMAgfUBTa0B8NMB0JQq4iHjxfAw3AG0AXUboAF9zMgAHHAgY5Tm6NU0dBBR0DENjLS9ehMG8eIWlldVJ6L74+gwADyo1a+h4DCoceHpoSohJmYce5PdbeHyoABm0GUf3i1T4wy0Gl+tzS0AAPujoABCWEnDCJDD0ADmsUOTTI70+31eMyasPh-AA1EzXpZrCk5nodgAxLhuPESAlLSHPK5ZSErbmYPnAckUsggD7QLnbTBuVX6DCyl5ZJqanbxWJE5TKd4QdTaIh6hXQdkQRBKxKIYlmjAWm0KhncBEAWl9r1tKISwLFgZ8UwANMo2Eh4JadGCg2R7Y6CSAXTHZI5VJ6Kd6ahh-eGvbdQ7qg1Nc006T4ODNAUqUsgwA8ACqUYbIgCMdT7xCb0DQ9A7yC70F7dQHyrk9AAJihR9qcD9kWpBExWPANtamlSvj85mB4JgAJL0Z6mlvtzvQX1D1AjzvqABU0AAsmBYvFZwvkOsmQfJ8x1UI1EAAZVsR9XVUXNGxnIw-3AjAlR9Kw3HXaBmEQNMjB3T9v1-FB1kUaA6niAAWcx7RSfE3HuAB3XQ1WwIVlAo3NpxSVhiUfDCE13HwIUcaFB1Qep0mgcTSN7STUBZeUFXxM5FmWaEBKTZNByI5AlzcHSlx5Fc1DzPcPgPBgMCYrYtVNc0M34SM3gwAArDBuA05MvOgUzvKaTAqCXRAcEvDTfL8hUdOQ1CeCsdYAH5nIgByMGUAADAASQhUCmf0IHsYB3Qgf0soMzspjS9Q6HeNzuHSrKcv9CEwFQEASsIMqxwq6sIq8qM3kQxdn3C5MqzzMaa2IQEeMfNQgA)
