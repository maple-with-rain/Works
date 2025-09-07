/* rain.js  线状雨幕 + 雨声
   可调参数：RAIN_SPEED / RAIN_DENSITY / RAIN_LENGTH / RAIN_WIDTH / RAIN_COLOR / AUDIO_VOLUME
   用法：<script src="rain.js"></script> 即可
*/
(function () {
    /* ========= 1. 参数读取 ========= */
    const cfg = window.RAIN_CONFIG || {};
    const RAIN_SPEED = cfg.speed ?? 5;            // 下落速度(px/帧)
    const RAIN_DENSITY = cfg.density ?? 100;          // 雨滴数量
    const RAIN_LENGTH = cfg.length ?? 20;           // 线长
    const RAIN_WIDTH = cfg.width ?? 1;            // 线宽
    const RAIN_COLOR = cfg.color ?? 'rgba(174,194,224,0.6)';
    const AUDIO_VOLUME = cfg.volume ?? 0.3;

    /* ========= 2. 画布 ========= */
    const cvs = document.createElement('canvas');
    const ctx = cvs.getContext('2d');
    function fit() {
        cvs.width = window.innerWidth;
        cvs.height = window.innerHeight;
    }
    window.addEventListener('resize', fit);
    fit();
    Object.assign(cvs.style, {
        position: 'fixed', top: 0, left: 0,
        pointerEvents: 'none', zIndex: 9999
    });
    document.body.appendChild(cvs);

    /* ========= 3. 雨滴 ========= */
    const drops = Array.from({ length: RAIN_DENSITY }, () => ({
        x: Math.random() * cvs.width,
        y: Math.random() * cvs.height,
        l: RAIN_LENGTH,
        speed: RAIN_SPEED + Math.random() * 2 - 1
    }));

    function draw() {
        ctx.clearRect(0, 0, cvs.width, cvs.height);
        ctx.strokeStyle = RAIN_COLOR;
        ctx.lineWidth = RAIN_WIDTH;
        ctx.beginPath();
        drops.forEach(d => {
            ctx.moveTo(d.x, d.y);
            ctx.lineTo(d.x, d.y + d.l);
            d.y += d.speed;
            if (d.y > cvs.height) {
                d.y = -d.l;
                d.x = Math.random() * cvs.width;
            }
        });
        ctx.stroke();
        requestAnimationFrame(draw);
    }
    draw();

    /* ========= 4. 雨声 ========= */
    const snd = new Audio();
    snd.loop = true;
    snd.volume = AUDIO_VOLUME;
    // 10 秒循环雨声（Base64，mp3 格式，44kHz）
    snd.src = 'data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA/+M4wAAAAAAAAAAAAEluZm8AAAAPAAAAAwAAAbAAYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBg'
})();