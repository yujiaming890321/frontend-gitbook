# 服务端渲染

服务端渲染 SSR (Server-Side Rendering)，是指在服务端完成页面的 html 拼接处理， 然后再发送给浏览器，将不具有交互能力的 html 结构绑定事件和状态，在客户端展示为具有完整交互能力的应用程序。

## 适用场景

- 需更快的到达时间，优势在于慢网络和运行缓慢的设备场景。
- 需更好的支持 SEO

## 不适用场景

- 同构资源的处理，结合 Vue 的钩子来说，能在 SSR 中调用的生命周期只有 beforeCreate 和 created，这就导致在使用三方 API 时必须保证运行不报错。
- 部署构建配置资源的支持，劣势在于运行环境单一。程序需处于 node.js server 运行环境。
- 服务器更多的缓存准备，劣势在于高流量场景需采用缓存策略。

服务端渲染 ( SSR ) 是一个同构程序，是否使用 SSR 取决于内容到达时间对应用程序的重要程度。
