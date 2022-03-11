# debonce 防抖，在 wait 时间内只执行最后一次

高频率触发的事件,在指定的单位时间内，只响应最后一次

```
function myDebounce(fn, wait = 0) {
  let timer = null;

  function debounce() {
    let _context = this;
    let args = [...arguments];
    clearTimeout(timer);
    timer = setTimeout(function () {
      fn.apply(_context, args);
    }, wait);
  }
  return debounce;
}
```

# throttle 节流，在 wait 秒内最多执行一次

高频率触发的事件,在指定的单位时间内，只响应第一次

```
const MyThrottle=(fn,delay)=>{
   let lastTime = 0;
   return () => {
      var nowTime = Date.now();
      if(nowTime - lastTime > delay){
        fn();
        lastTime = nowTime;
      }
   }
}
```
