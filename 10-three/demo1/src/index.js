import * as THREE from '../libs/Three.js'

const scene = new THREE.Scene();
console.log("🚀 ~ file: index.js ~ line 3 ~ scene", scene)
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
