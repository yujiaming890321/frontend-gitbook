# [three.js](https://github.com/mrdoob/three.js)

之前的 3D 渲染都是基于 OpenGl 和 DirectX ，为了移动端OpenGl 开发了 OpenGl ES。
OpenGl ES 2.0标准开发了 WebGL 标准。
WebGL 标准 是一种3D绘图协议，允许把 javascript 和 OpenGl ES 2.0结合在一起。

## 场景

在 Three.js 中添加的物体都是添加到场景中的，因此它相当于一个大容器。
在程序最开始的时候进行实例化，然后将物体添加到场景中即可。

```javascript
const scene = new THREE.Scene();
```

## 相机

WebGL 和 Three.js 使用的坐标系是右手坐标系，即右手伸开，拇指为X，四指为Y，手心为Z。

相机就像人的眼睛一样，人站在不同位置，抬头或者低头都能够看到不同的景色。

### 透视相机 THREE.PerspectiveCamera

```javascript
PerspectiveCamera( fov: Number, aspect: Number, near: Number, far: Number )
fov — 摄像机视锥体垂直视野角度
aspect — 摄像机视锥体长宽比
near — 摄像机视锥体近端面
far — 摄像机视锥体远端面

const camera = new THREE.PerspectiveCamera(45, 4 / 3, 1, 1000);
camera.position.set(0, 0, 5);
scene.add(camera);
```

## 渲染器

