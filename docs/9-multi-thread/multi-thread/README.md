# multi-thread

[WebWorker](https://developer.mozilla.org/zh-CN/docs/Web/API/Web_Workers_API)

通过使用 Web Workers，Web 应用程序可以在独立于主线程的后台线程中，运行一个脚本操作。这样做的好处是可以在独立线程中执行费时的处理任务，从而允许主线程（通常是 UI 线程）不会因此被阻塞/放慢。

[ServiceWorker](https://developer.mozilla.org/zh-CN/docs/Web/API/Service_Worker_API)

Service workers 本质上充当 Web 应用程序、浏览器与网络（可用时）之间的代理服务器。这个 API 旨在创建有效的离线体验，它会拦截网络请求并根据网络是否可用来采取适当的动作、更新来自服务器的的资源。它还提供入口以推送通知和访问后台同步 API。

[互斥锁-Mutext]()

[读写锁-ReadWriteRock]()
