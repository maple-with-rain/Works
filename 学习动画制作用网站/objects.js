const scene = new THREE.Scene();
//创建背景
const geometry = new THREE.BoxGeometry(0.01, 0.3, 0.01);
//创建几何体
const material = new THREE.MeshBasicMaterial({ color: 'blue' });
//创建材质
const mesh = new THREE.Mesh(geometry, material);
//创建网格
scene.add(mesh);

//Camera
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
//创建该类型的相机，第一个参数为视野角度，第二个参数为宽高比，第三个参数为近裁剪面，第四个参数为远裁剪面
camera.position.z = 3;
camera.position.y = 1;
camera.position.x = -1;
scene.add(camera);
//将相机加入场景
scene.add(mesh)

//Sizes这里就是指定一个
const sizes = {
    width: window.innerWidth,
    height: window.innerHeight
}

//Render使用WebGl渲染器渲染，创建渲染器元素
const renderer = new THREE.WebGLRenderer({
    canvas: document.querySelector('#webgl')//指定画布元素，如果存在与属性名相同变量，可以只给出属性名

})
renderer.setSize(sizes.width, sizes.height);//指定renderer尺寸
renderer.render(scene, camera);//渲染场景和相机