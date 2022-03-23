# Service Worker API

Service workers 本质上充当 Web 应用程序、浏览器与网络（可用时）之间的代理服务器。
这个 API 旨在创建有效的离线体验，它会拦截网络请求并根据网络是否可用来采取适当的动作、更新来自服务器的的资源。它还提供入口以推送通知和访问后台同步 API。

# Service worker 的概念和用法

Service worker 是一个注册在指定源和路径下的事件驱动 worker。
它采用 JavaScript 控制关联的页面或者网站，拦截并修改访问和资源请求，细粒度地缓存资源。你可以完全控制应用在特定情形（最常见的情形是网络不可用）下的表现。

Service worker 运行在 worker 上下文，因此它不能访问 DOM。相对于驱动应用的主 JavaScript 线程，它运行在其他线程中，所以不会造成阻塞。它设计为完全异步，同步 API（如 XHR 和 localStorage）不能在 service worker 中使用。

出于安全考量，Service workers 只能由 HTTPS 承载，毕竟修改网络请求的能力暴露给中间人攻击会非常危险。

## 注册

ServiceWorkerContainer.register() 方法首次注册 service worker。如果注册成功，service worker 就会被下载到客户端并尝试安装或激活（见下文），这将作用于整个域内用户可访问的 URL，或者其特定子集。

## 下载、安装和激活

你的服务工作者(service worker)将遵守以下生命周期：

1. 下载
2. 安装
3. 激活

用户首次访问 service worker 控制的网站或页面时，service worker 会立刻被下载。
无论它与现有 service worker 不同（字节对比），还是第一次在页面或网站遇到 service worker，如果下载的文件是新的，安装就会尝试进行。
如果这是首次启用 service worker，页面会首先尝试安装，安装成功后它会被激活。

如果现有 service worker 已启用，新版本会在后台安装，但不会被激活，这个时序称为 worker in waiting。
直到所有已加载的页面不再使用旧的 service worker 才会激活新的 service worker。只要页面不再依赖旧的 service worker，新的 service worker 会被激活（成为 active worker）。
