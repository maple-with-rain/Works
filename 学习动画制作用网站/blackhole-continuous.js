/*
 * 黑洞 3D 粒子（伪三维 + 持续补新）
 * 纯 2D Canvas，零依赖，复制即用
 */

/* ====== 可调参数 ====== */
const CONFIG = {
  mass: 3000,            // 引力强度
  spin: 0.7,             // 拖拽强度
  eventHorizon: 30,      // 黑洞半径（像素）
  maxRadius: 600,        // 初始球壳半径
  damp: 0.995,           // 径向阻尼
  baseSpeedMul: 0.7,
  particleCount: 4000,   // 初始粒子
  respawnPerFrame: 3,    // 每帧补新粒子
  particleSize: 2,       // 基础大小
};

/* ====== 运行 ====== */
(() => {
  const cvs = document.createElement('canvas');
  const ctx = cvs.getContext('2d');
  document.body.appendChild(cvs);
  cvs.style.position = 'fixed'; cvs.style.top = cvs.style.left = 0;
  cvs.style.width = cvs.style.height = '100%';

  const resize = () => {
    cvs.width  = innerWidth;
    cvs.height = innerHeight;
  };
  addEventListener('resize', resize); resize();

  const cx = () => cvs.width / 2;
  const cy = () => cvs.height / 2;

  /* ===== 粒子 ===== */
  const pool = [];
  function spawn(p) {
    const r = CONFIG.eventHorizon + Math.random() * (CONFIG.maxRadius - CONFIG.eventHorizon);
    const theta = Math.random() * Math.PI * 2;
    const phi   = Math.acos(2 * Math.random() - 1);
    p.x = r * Math.sin(phi) * Math.cos(theta);
    p.y = r * Math.sin(phi) * Math.sin(theta);
    p.z = r * Math.cos(phi);

    const vKep = Math.sqrt(CONFIG.mass / r) * CONFIG.baseSpeedMul;
    p.vx = -vKep * Math.sin(theta);
    p.vy =  vKep * Math.cos(theta);
    p.vz = (Math.random() - 0.5) * vKep * 0.2;
  }
  for (let i = 0; i < CONFIG.particleCount; i++) {
    const p = {}; spawn(p); pool.push(p);
  }

  /* ===== 物理 ===== */
  const G = 0.3;
  function step() {
    /* 1. 每帧补新粒子 */
    for (let k = 0; k < CONFIG.respawnPerFrame; k++) {
      const idx = Math.floor(Math.random() * pool.length);
      spawn(pool[idx]);
    }

    for (const p of pool) {
      const r2 = p.x ** 2 + p.y ** 2 + p.z ** 2;
      const r  = Math.sqrt(r2);
      if (r <= CONFIG.eventHorizon) { spawn(p); continue; }

      const acc = G * CONFIG.mass / r2;
      p.vx -= acc * p.x / r;
      p.vy -= acc * p.y / r;
      p.vz -= acc * p.z / r;

      const drag = CONFIG.spin * 0.012 / r;
      p.vx += -p.y * drag;
      p.vy +=  p.x * drag;

      p.vx *= CONFIG.damp;
      p.vy *= CONFIG.damp;
      p.vz *= CONFIG.damp;

      p.x += p.vx;
      p.y += p.vy;
      p.z += p.vz;
    }
  }

  /* ===== 绘制 ===== */
  function draw() {
    ctx.fillStyle = 'rgba(0,0,0,0.15)';
    ctx.fillRect(0, 0, cvs.width, cvs.height);

    /* 黑洞核心阴影 */
    const g = ctx.createRadialGradient(cx(), cy(), 0, cx(), cy(), CONFIG.eventHorizon);
    g.addColorStop(0, 'rgba(0,0,0,1)');
    g.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(cx(), cy(), CONFIG.eventHorizon, 0, Math.PI * 2);
    ctx.fill();

    /* 粒子（根据 z 深度缩放 + 透明度） */
    for (const p of pool) {
      const perspective = 700 / (700 + p.z);
      const sx = cx() + p.x * perspective;
      const sy = cy() + p.y * perspective;
      const size = CONFIG.particleSize * perspective;
      const alpha = 1 - Math.sqrt(p.x**2 + p.y**2 + p.z**2) / CONFIG.maxRadius;
      if (alpha <= 0) continue;

      ctx.fillStyle = `rgba(255,255,255,${alpha})`;
      ctx.beginPath();
      ctx.arc(sx, sy, size, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  /* ===== 主循环 ===== */
  function loop() {
    step();
    draw();
    requestAnimationFrame(loop);
  }
  loop();
})();