import * as THREE from '../libs/Three.js'

// 添加three. js坐标轴、光源和阴影效果
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const render = new THREE.WebGLRenderer()
render.setSize(window.innerWidth , window.innerHeight)
render.shadowMap.enabled = true
document.getElementById('root').appendChild(render.domElement)

// 辅助坐标线
const axes = new THREE.AxesHelper(50)
// axes.setColors('#ccc', '#fff', '#ededed')
scene.add(axes)

// 正方形几何体
const geometry = new THREE.BoxGeometry(8,8,8)
// 基础网格材质
// const material = new THREE.MeshBasicMaterial({color: 0xff2288})
const material = new THREE.MeshLambertMaterial({color: 0xff2288})
// 物体-网格
const cube = new THREE.Mesh(geometry, material)
scene.add(cube)
cube.castShadow = true
// 移动
cube.position.x = 4
cube.position.y = 10
cube.position.z = 20
// 旋转角度
// cube.rotation.x += 0.50
// cube.rotation.y += 0.50
// 平面缓冲几何体
const planeGeometry =  new THREE.PlaneGeometry(100,100)
// Lambert网格材质
// const lamberMaterial = new THREE.MeshLambertMaterial({color: 0x222222})
const lamberMaterial = new THREE.MeshLambertMaterial({color: 0xcccccc})
// 物体-网格
const plane = new THREE.Mesh(planeGeometry, lamberMaterial)
scene.add(plane)
// 接收阴影
plane.receiveShadow = true
// 旋转角度
plane.rotation.x = -0.50 * Math.PI
plane.position.set(15,0,0)
// 环境光
const ambientLight = new THREE.AmbientLight(0xAAAAAA)
scene.add(ambientLight)
// 聚光灯
const spotLight = new THREE.SpotLight( 0xffffff );
// 投射阴影
spotLight.castShadow = true;
spotLight.shadow.mapSize = new THREE.Vector2(1024,1024)

spotLight.shadow.camera.far = 130;
spotLight.shadow.camera.near = 40;

spotLight.position.set(-60,40,-65)
scene.add(spotLight)
// 相机方向
camera.position.x = -30
camera.position.y = 45
camera.position.z = 35
camera.lookAt(scene.position)




render.render(scene, camera)