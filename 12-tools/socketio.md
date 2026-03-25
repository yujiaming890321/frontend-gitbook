# [Socket.io](https://socket.io/zh-CN/)

默认情况下，客户端使用 HTTP 长轮询传输建立连接。

握手 (包含会话 ID — 此处, zBjrh...AAAK — 用于后续请求)
发送数据 (HTTP 长轮询)
接收数据 (HTTP 长轮询)
升级 (WebSocket)
接收数据 (HTTP 长轮询, WebSocket 连接建立成功后关闭)

## 断线检测

Engine.IO 连接在以下情况下被视为关闭：

一个 HTTP 请求（GET 或 POST）失败（例如，当服务器关闭时）
WebSocket 连接关闭（例如，当用户关闭其浏览器中的选项卡时）
socket.disconnect() 在服务器端或客户端调用
还有一个心跳机制检查服务器和客户端之间的连接是否仍然正常运行：

在给定的时间间隔（ pingInterval 握手中发送的值），服务器发送一个 PING 数据包，客户端有几秒钟（该 pingTimeout 值）发送一个 PONG 数据包。如果服务器没有收到返回的 PONG 数据包，则认为连接已关闭。反之，如果客户端在 pingInterval + pingTimeout 内没有收到 PING 包，则认为连接已关闭。

断开连接的原因在此处 （服务器端）和 此处 （客户端）列出。

## Socket.IO

Socket.IO 通过 Engine.IO 连接提供了一些附加功能：

自动重连
数据包缓冲
收到后的回调
广播 到所有客户端 或 客户端的子集（我们称之为“房间”）
多路复用（我们称之为“命名空间”）

## engine.IO

```js
0{"sid":"N-YWtQT1K9uQsb15AAAD","upgrades":["websocket"],"pingInterval":25000,"pingTimeout":5000}

0           => "open" packet type
{"sid":...  => the handshake data

4hey

4           => "message" packet type
hey         => the actual message

4hello\x1e4world

4           => "message" packet type
hello       => the 1st message
\x1e        => separator
4           => "message" message type
world       => the 2nd message
```

### Socket.IO 断线重连机制

  Socket.IO 的断线重连涉及 检测断开 和 自动重连 两个阶段。

  1. 检测断开：心跳机制 (Ping/Pong)

  Socket.IO Engine.IO 层内置了心跳探测：

  - Server 定期向 Client 发送 ping 包（默认间隔 pingInterval = 25000ms）
  - Client 必须在 pingTimeout（默认 20000ms）内回复 pong
  - 如果超时未收到 pong，Server 判定连接断开，触发 disconnect 事件
  - Client 侧同理，如果超时未收到 Server 的 ping，也会判定连接丢失

  2. 自动重连：Client 端指数退避

  断开连接后，Socket.IO Client 内置了自动重连逻辑（基于 reconnection 选项，默认开启）：
  ┌──────────────────────┬──────────┬──────────────┐
  │        配置项        │  默认值  │     说明     │
  ├──────────────────────┼──────────┼──────────────┤
  │ reconnection         │ true     │ 是否自动重连 │
  ├──────────────────────┼──────────┼──────────────┤
  │ reconnectionAttempts │ Infinity │ 最大重连次数 │
  ├──────────────────────┼──────────┼──────────────┤
  │ reconnectionDelay    │ 1000ms   │ 初始重连延迟 │
  ├──────────────────────┼──────────┼──────────────┤
  │ reconnectionDelayMax │ 5000ms   │ 最大重连延迟 │
  ├──────────────────────┼──────────┼──────────────┤
  │ randomizationFactor  │ 0.5      │ 随机抖动因子 │
  └──────────────────────┴──────────┴──────────────┘
  重连延迟使用 指数退避 + 随机抖动：

  delay = min(reconnectionDelay * 2^attempt * (1 ± randomizationFactor), reconnectionDelayMax)

  例如：第1次 ~1s，第2次 ~2s，第3次 ~4s，之后被 5s 上限截断。