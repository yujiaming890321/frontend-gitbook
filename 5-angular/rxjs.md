# [rxjs](https://cn.rx.js.org/)

RxJS 是使用 Observables 的响应式编程的库，它使编写异步或基于回调的代码更容易。

在 RxJS 中用来解决异步事件管理的的基本概念是：

- Observable (可观察对象): 表示一个概念，这个概念是一个可调用的未来值或事件的集合。
- Observer (观察者): 一个回调函数的集合，它知道如何去监听由 Observable 提供的值。
- Subscription (订阅): 表示 Observable 的执行，主要用于取消 Observable 的执行。
- Operators (操作符): 采用函数式编程风格的纯函数 (pure function)，使用像 map、filter、concat、flatMap 等这样的操作符来处理集合。
- Subject (主体): 相当于 EventEmitter，并且是将值或事件多路推送给多个 Observer 的唯一方式。
- Schedulers (调度器): 用来控制并发并且是中央集权的调度员，允许我们在发生计算时进行协调，例如 setTimeout 或 requestAnimationFrame 或其他。

```js
this.timeSlotChooseSubject = new Subject<AdvisorDashboardItem>();
this.timeSlotChooseSubject.pipe(
  switchMap((item) => this.getTimeSlots(item))
).subscribe(resp => {
  this.remark = resp.Notes;
});
```

## 