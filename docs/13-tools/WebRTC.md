# webRTC(Web Real-Time Communications)

RTC 实时通信：点对点视频、音频流或者其他任意数据的传输，考虑的是低延时
IM 即时通信：通过文字聊天、语音消息发送、文件传输等方式通信，考虑的是可靠性

## 主要由三部分组成：API、音视频引擎和网络 IO

### API

用于采集摄像头和麦克风生成媒体流，并处理音视频通信相关的编码、解码、传输过程

- - getUserMedia: 获取麦克风和摄像头的许可，使得 WebRTC 可以拿到本地媒体流；
- RTCPeerConnection: 建立点对点连接的关键，提供了创建，保持，监控，关闭连接的方法的实现。像媒体协商、收集候选地址都需要它来完成；
- RTCDataChannel: 支持点对点数据传输，可用于传输文件、文本消息等。

### 音视频引擎

WebRTC 内置了强大的音视频引擎，可以对媒体流进行编解码、回声消除、降噪、防止视频抖动等处理

- OPUS: 一个开源的低延迟音频编解码器，WebRTC 默认使用；
- G711: 国际电信联盟 ITU-T 定制出来的一套语音压缩标准，是主流的波形声音编解码器；
- VP8: VP8，VP9，都是 Google 开源的视频编解码器，现在主要用于 WebRTC 视频编码；
- H264: 视频编码领域的通用标准，提供了高效的视频压缩编码，之前 WebRTC 最先支持的是自己家的 VP8，后面也支持了 H264、H265 等。
回声消除AEC(Acoustic Echo Chancellor)、背景噪音抑制ANS(Automatic Noise Suppression)和Jitter buffer用来防止视频抖动

### 网络 IO

WebRTC 传输层用的是 UDP 协议，因为音视频传输对及时性要求更高

- RTP/SRTP: 传输音视频数据流时，我们并不直接将音视频数据流交给 UDP 传输，而是先给音视频数据加个 RTP 头，然后再交给 UDP 进行，但是由于浏览器对安全性要求比较高，增加了加密这块的处理，采用 SRTP 协议；
- RTCP: 通过 RTCP 可以知道各端的网络质量，这样对方就可以做流控处理；
- P2P(ICE + STUN + TURN): 这是 WebRTC 最核心的技术，利用 ICE、STUN、TURN 等技术，实现了浏览器之间的直接点对点连接，解决了 NAT 穿透问题，实现了高质量的网络传输。

STUN 协议
全称 Session Traversal Utilities for NAT（NAT 会话穿越应用程序），是一种网络协议，它允许位于 NAT 后的客户端找出自己的公网地址，也就是遵守这个协议就可以拿到自己的公网 IP。

TURN 协议
全称 Traversal Using Relays around NAT（使用中继穿透 NAT），STUN 的中继扩展。简单的说，TURN 与 STUN 的共同点都是通过修改应用层中的私网地址达到 NAT 穿透的效果，异同点是 TURN 是通过两方通讯的“中间人”方式实现穿透。

ICE
全称 Interactive Connectivity Establishment（交互式连通建立方式），ICE 协议通过一系列的技术（如 STUN、TURN 服务器）帮助通信双方发现和协商可用的公共网络地址，从而实现 NAT 穿越，也就是上面说的获取所有候选者类型的过程，即：在本机收集所有的 host 类型的 Candidate，通过 STUN 协议收集 srflx 类型的 Candidate，使用 TURN 协议收集 relay 类型的 Candidate。

## 连接步骤

### 音视频采集

note: WebRTC 相关的 API 需要 Https（或者 localhost）环境支持，因为在浏览器上通过 HTTP 请求下来的 JavaScript 脚本是不允话访问音视频设备的，只有通过 HTTPS 请求的脚本才能访问音视频设备。

```js
const constraints = { video: true, audio: true }
const localStream = navigator.mediaDevices.getUserMedia(constraints)
```

navigator.mediaDevices.enumerateDevices()

MediaDevices 该接口提供访问连接媒体输入的设备（如摄像头、麦克风）以及获取屏幕共享等方法
MediaDeviceInfo 用于表示每个媒体输入/输出设备的信息，包含以下 4 个属性：

- deviceId: 设备的唯一标识；
- groupId: 如果两个设备属于同一物理设备，则它们具有相同的组标识符 - 例如同时具有内置摄像头和麦克风的显示器；
- label: 返回描述该设备的字符串，即设备名称（例如“外部 USB 网络摄像头”）；
- kind: 设备种类，可用于识别出是音频设备还是视频设备，是输入设备还是输出设备：audioinput/audiooutput/videoinput
可以在浏览器控制台直接输入

### 信令交互

信令可以简单理解为消息，在协调通讯的过程中，为了建立一个 webRTC 的通讯过程，在通信双方彼此连接、传输媒体数据之前，它们要通过信令服务器交换一些信息，如加入房间、离开房间及媒体协商等

### RTCPeerConnection、媒体协商

RTCPeerConnection是一个由本地计算机到远端的 WebRTC 连接，该接口提供创建，保持，监控，关闭连接的方法的实现，可以简单理解为功能强大的 socket 连接。
主要负责与各端建立连接（NAT 穿越），接收、发送音视频数据

```js
const localPc = new RTCPeerConnection(rtcConfig)
// 将音视频流添加到 RTCPeerConnection 对象中
localStream.getTracks().forEach((track) => {
  localPc.addTrack(track, localStream)
})
```

媒体协商的作用是找到双方共同支持的媒体能力，如双方各自支持的编解码器，音频的参数采样率，采样大小，声道数、视频的参数分辨率，帧率等等。

媒体协商过程： 一对一通信中，发起方发送的 SDP 称为Offer(提议)，接收方发送的 SDP 称为Answer(应答)。每端保持两个描述：描述本身的本地描述LocalDescription，描述呼叫的远端的远程描述RemoteDescription。

- 发起方创建 Offer 类型的 SDP，保存为本地描述后再通过信令服务器发送到对端；
- 接收方接收到 Offer 类型的 SDP，将 Offer 保存为远程描述；
- 接收方创建 Answer 类型的 SDP，保存为本地描述，再通过信令服务器发送到发起方，此时接收方已知道连接双方的配置；
- 发起方接收到 Answer 类型的 SDP 后保存到远程描述，此时发起方也已知道连接双方的配置；

```js
// 配置
export const rtcConfig = null
const localPc = new RTCPeerConnection(rtcConfig)

// 发起方/接收方创建 Offer 保存为本地描述
let offer = await localPc.createOffer()
// 保存为本地描述
await localPc.setLocalDescription(offer)
// 通过信令服务器发送到对端
socket.emit('offer', offer)

// 接受 Offer 后 创建 Answer 并发送
socket.on('offer', offer) => {
  // 将 Offer 保存为远程描述；
  remotePc = new RTCPeerConnection(rtcConfig)
  await remotePc.setRemoteDescription(offer)
  let remoteAnswer = await remotePc.createAnswer()
  await remotePc.setLocalDescription(remoteAnswer)
  socket.emit('answer', remoteAnswer)
});

// 接受 Answer 存储为远程描述
socket.on('answer', answer) => {
  // 将 Answer 保存为远程描述；
  await localPc.setRemoteDescription(answer);
});
```

### 端与端建立连接

媒体协商结束后，双端统一了传输协议、编解码器等，此时就需要建立连接开始音视频通信了。但 WebRTC 既要保持音视频通信的质量，又要保证联通性。当同时存在多个有效连接时，它首先选择传输质量最好的线路，如能用内网连通就不用公网，优先 P2P 传输，如果 P2P 不通才会选择中继服务器（relay），因为中继方式会增加双端传输的时长。

Candidate: 表示 WebRTC 与远端通信时使用的协议、IP 地址和端口，结构如下

```js
{
  address: xxx.xxx.xxx.xxx, // 本地IP地址
  port: number, // 本地端口号
  type: 'host/srflx/relay', // 候选者类型
  priority: number, // 优先级
  protocol: 'udp/tcp', // 传输协议
  usernameFragment: string // 访问服务的用户名
  ...
}
```

host 类型: host 类型的 Candidate 是最好收集的，就是本机的 ip 地址 和端口。
srflx 和 relay 类型: srflx 类型的 Candidate 就是内网通过 NAT（Net Address Translation，作用是进行内外网的地址转换，位于内网的网关上）映射后的外网地址。

```js
localPc.onicecandidate = function (event) {
  // 回调时，将自己candidate发给对方，对方可以直接addIceCandidate(candidate)添加可以获取流
  if (event.candidate) socket.emit('candidate', event.candidate)
}

socket.on('candidate', candidate) => {
    await localPc.addIceCandidate(candidate)
});
```

### 显示远端流

通信双方通过 RTCPeerConnection 建立连接后，本地的音视频数据源源不断的传输，要想在远端展示出来，就需要将 RTCPeerConnection 对象与<video>或<audio>进行绑定。

当远端创建好 RTCPeerConnection 对象后，会为 RTCPeerConnection 绑定ontrack事件，当有音视频数据流到来时，输入参数 event 中包含了远端的音视频流，即 MediaStream 对象，此时将此对象赋值给<video>或<audio>的srcObject字段，这样 RTCPeerConnection 对象就与<video>或<audio>进行了绑定，音频或视频就能展示出来。

```js
localPc.ontrack = (e) => {
  video.srcObject = e.streams[0]
  video.oncanplay = () => video.play()
}
```

至此，一个完整的 WebRTC 通信过程就结束了。