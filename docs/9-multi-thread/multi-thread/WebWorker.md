# Web Worker 的特点

1. 同源限制

   分配给 Worker 线程运行的脚本文件，必须与主线程的脚本文件同源。

2. DOM 限制

   Worker 线程所在的全局对象，与主线程不一样，无法读取主线程所在网页的 DOM 对象，也无法使用 document、window、parent 这些对象。但是，Worker 线程可以 navigator 对象和 location 对象。

3. 通信联系

   Worker 线程和主线程不在同一个上下文环境，它们不能直接通信，必须通过消息完成。

4. 脚本限制

   Worker 线程不能执行 alert()方法和 confirm()方法，但可以使用 XMLHttpRequest 对象发出 AJAX 请求。

5. 文件限制

   Worker 线程无法读取本地文件，即不能打开本机的文件系统（file://），它所加载的脚本，必须来自网络。

# 基本用法

## 主线程

- 主线程采用 new 命令，调用 Worker()构造函数，新建一个 Worker 线程。

```
var worker = new Worker('work.js');
```

- 主线程调用 worker.postMessage()方法，向 Worker 发消息。

```
worker.postMessage('Hello World');
worker.postMessage({method: 'echo', args: ['Work']});
```

- 主线程通过 worker.onmessage 指定监听函数，接收子线程发回来的消息。

```
worker.onmessage = function (event) {
  console.log('Received message ' + event.data);
  doSomething();
}

function doSomething() {
  // 执行任务
  worker.postMessage('Work done!');
}
```

- 主线程关掉 worker 线程

```
worker.terminate();
```

- 主线程可以监听 Worker 是否发生错误，Worker 会触发主线程的 error 事件。

```
worker.onerror(function (event) {
  console.log([
    'ERROR: Line ', e.lineno, ' in ', e.filename, ': ', e.message
  ].join(''));
});

// 或者
worker.addEventListener('error', function (event) {
  // ...
});
```

## worker 线程

- Worker 线程内部需要有一个监听函数，监听 message 事件。

```
// self代表子线程自身，即子线程的全局对象。等同于写法一，写法二
self.addEventListener('message', function (e) {
  self.postMessage('You said: ' + e.data);
}, false);

// 写法一
this.addEventListener('message', function (e) {
  this.postMessage('You said: ' + e.data);
}, false);

// 写法二
addEventListener('message', function (e) {
  postMessage('You said: ' + e.data);
}, false);
```

- self.close() 用于在 Worker 线程内部关闭自身。

```
self.addEventListener('message', function (e) {
  var data = e.data;
  switch (data.cmd) {
    case 'start':
      self.postMessage('WORKER STARTED: ' + data.msg);
      break;
    case 'stop':
      self.postMessage('WORKER STOPPED: ' + data.msg);
      self.close(); // Terminates the worker.
      break;
    default:
      self.postMessage('Unknown command: ' + data.msg);
  };
}, false);
```

- Worker 加载脚本

```
importScripts('script1.js', 'script2.js');
```

## 使用完毕，为了节省系统资源，必须关闭 Worker。

```
// 主线程
worker.terminate();

// Worker 线程
self.close();
```
