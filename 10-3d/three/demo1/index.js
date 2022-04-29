import * as THREE from '../libs/Three.js'

// 渲染第一个三维对象
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const render = new THREE.WebGLRenderer()
render.setSize(window.innerWidth , window.innerHeight)
document.getElementById('root').appendChild(render.domElement)

// 正方形几何体
const geometry = new THREE.BoxGeometry()
// 网络基础材质
const material = new THREE.MeshBasicMaterial({color: 0xff2288})
// 网络
const cube = new THREE.Mesh(geometry, material)
scene.add(cube)

camera.position.z = 5
cube.rotation.x += 0.50
cube.rotation.y += 0.50

render.render(scene, camera)