/* Hero · 琉璃流体球（Three.js r160, 自定义 shader）
   透明清透色系：雾蓝 / 薄荷 / 淡紫，fresnel 流光 + 单工噪声呼吸形变
   CDN 失败或 WebGL 不可用时静默退出，页面保留纯 CSS 极光背景。 */

const canvas = document.getElementById("hero3d");
if (canvas) {
  init().catch(() => { canvas.style.display = "none"; });
}

async function init() {
  const THREE = await import(
    "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js"
  );

  const renderer = new THREE.WebGLRenderer({
    canvas,
    alpha: true,
    antialias: true,
    powerPreference: "high-performance",
  });
  renderer.setClearColor(0x000000, 0);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 60);
  camera.position.set(0, 0, 7.2);

  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- 琉璃流体球 ---------- */
  const noiseGLSL = /* glsl */ `
    vec3 mod289(vec3 x){return x-floor(x*(1.0/289.0))*289.0;}
    vec4 mod289(vec4 x){return x-floor(x*(1.0/289.0))*289.0;}
    vec4 permute(vec4 x){return mod289(((x*34.0)+1.0)*x);}
    vec4 taylorInvSqrt(vec4 r){return 1.79284291400159-0.85373472095314*r;}
    float snoise(vec3 v){
      const vec2 C=vec2(1.0/6.0,1.0/3.0);
      const vec4 D=vec4(0.0,0.5,1.0,2.0);
      vec3 i=floor(v+dot(v,C.yyy));
      vec3 x0=v-i+dot(i,C.xxx);
      vec3 g=step(x0.yzx,x0.xyz);
      vec3 l=1.0-g;
      vec3 i1=min(g.xyz,l.zxy);
      vec3 i2=max(g.xyz,l.zxy);
      vec3 x1=x0-i1+C.xxx;
      vec3 x2=x0-i2+C.yyy;
      vec3 x3=x0-D.yyy;
      i=mod289(i);
      vec4 p=permute(permute(permute(i.z+vec4(0.0,i1.z,i2.z,1.0))+i.y+vec4(0.0,i1.y,i2.y,1.0))+i.x+vec4(0.0,i1.x,i2.x,1.0));
      float n_=0.142857142857;
      vec3 ns=n_*D.wyz-D.xzx;
      vec4 j=p-49.0*floor(p*ns.z*ns.z);
      vec4 x_=floor(j*ns.z);
      vec4 y_=floor(j-7.0*x_);
      vec4 x=x_*ns.x+ns.yyyy;
      vec4 y=y_*ns.x+ns.yyyy;
      vec4 h=1.0-abs(x)-abs(y);
      vec4 b0=vec4(x.xy,y.xy);
      vec4 b1=vec4(x.zw,y.zw);
      vec4 s0=floor(b0)*2.0+1.0;
      vec4 s1=floor(b1)*2.0+1.0;
      vec4 sh=-step(h,vec4(0.0));
      vec4 a0=b0.xzyw+s0.xzyw*sh.xxyy;
      vec4 a1=b1.xzyw+s1.xzyw*sh.zzww;
      vec3 p0=vec3(a0.xy,h.x);
      vec3 p1=vec3(a0.zw,h.y);
      vec3 p2=vec3(a1.xy,h.z);
      vec3 p3=vec3(a1.zw,h.w);
      vec4 norm=taylorInvSqrt(vec4(dot(p0,p0),dot(p1,p1),dot(p2,p2),dot(p3,p3)));
      p0*=norm.x;p1*=norm.y;p2*=norm.z;p3*=norm.w;
      vec4 m=max(0.6-vec4(dot(x0,x0),dot(x1,x1),dot(x2,x2),dot(x3,x3)),0.0);
      m=m*m;
      return 42.0*dot(m*m,vec4(dot(p0,x0),dot(p1,x1),dot(p2,x2),dot(p3,x3)));
    }
  `;

  const blobUniforms = {
    uTime: { value: 0 },
    uAmp: { value: 0.32 },
    uFreq: { value: 1.15 },
  };

  const blobMat = new THREE.ShaderMaterial({
    uniforms: blobUniforms,
    transparent: true,
    vertexShader: noiseGLSL + /* glsl */ `
      uniform float uTime;
      uniform float uAmp;
      uniform float uFreq;
      varying vec3 vN;
      varying vec3 vPos;
      varying float vNoise;
      void main() {
        float t = uTime * 0.35;
        float n = snoise(normal * uFreq + vec3(t, t * 0.7, -t * 0.5));
        float n2 = snoise(normal * uFreq * 2.3 - vec3(t * 0.6)) * 0.35;
        vNoise = n + n2;
        vec3 displaced = position + normal * (n * uAmp + n2 * uAmp * 0.6);
        vN = normalize(normalMatrix * normal);
        vec4 mv = modelViewMatrix * vec4(displaced, 1.0);
        vPos = mv.xyz;
        gl_Position = projectionMatrix * mv;
      }
    `,
    fragmentShader: /* glsl */ `
      varying vec3 vN;
      varying vec3 vPos;
      varying float vNoise;
      void main() {
        vec3 V = normalize(-vPos);
        vec3 N = normalize(vN);
        float fres = pow(1.0 - max(dot(N, V), 0.0), 2.2);

        // 清透四色：雾蓝 → 天青 → 薄荷 → 淡紫
        vec3 cA = vec3(0.42, 0.60, 1.00);  // #6B9AFF
        vec3 cB = vec3(0.40, 0.82, 0.96);  // #66D1F5
        vec3 cC = vec3(0.36, 0.90, 0.78);  // #5CE6C7
        vec3 cD = vec3(0.68, 0.62, 1.00);  // #AD9EFF

        float m1 = smoothstep(-0.7, 0.7, vNoise);
        float m2 = smoothstep(-0.9, 0.9, N.y + vNoise * 0.4);
        vec3 col = mix(cA, cB, m1);
        col = mix(col, cC, m2 * 0.55);
        col = mix(col, cD, smoothstep(0.2, 1.0, fres) * 0.6);

        // 流光边缘 + 顶部高光
        col += fres * vec3(0.55, 0.65, 0.9) * 0.55;
        col += pow(max(dot(N, normalize(vec3(-0.4, 0.8, 0.5))), 0.0), 14.0) * 0.35;

        float alpha = 0.62 + fres * 0.38;
        gl_FragColor = vec4(col, alpha);
      }
    `,
  });

  const group = new THREE.Group();
  scene.add(group);

  const blob = new THREE.Mesh(new THREE.IcosahedronGeometry(1.5, 96), blobMat);
  group.add(blob);

  /* ---------- 轨道环 ×2 ---------- */
  function ring(radius, tube, color, opacity, tilt) {
    const m = new THREE.Mesh(
      new THREE.TorusGeometry(radius, tube, 12, 220),
      new THREE.MeshBasicMaterial({ color, transparent: true, opacity })
    );
    m.rotation.x = tilt;
    m.rotation.y = tilt * 0.45;
    return m;
  }
  const ring1 = ring(2.35, 0.006, 0x8fb2ff, 0.55, Math.PI * 0.42);
  const ring2 = ring(2.9, 0.004, 0x5ce6c7, 0.4, Math.PI * 0.5);
  group.add(ring1, ring2);

  /* ---------- 粒子星尘 ---------- */
  const COUNT = 900;
  const pos = new Float32Array(COUNT * 3);
  const col = new Float32Array(COUNT * 3);
  const scale = new Float32Array(COUNT);
  const palette = [
    new THREE.Color(0x6b9aff),
    new THREE.Color(0x66d1f5),
    new THREE.Color(0x5ce6c7),
    new THREE.Color(0xad9eff),
    new THREE.Color(0xf2a5c8),
  ];
  for (let i = 0; i < COUNT; i++) {
    const r = 2.4 + Math.random() * 5.2;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
    pos[i * 3 + 1] = r * Math.cos(phi) * 0.72;
    pos[i * 3 + 2] = r * Math.sin(phi) * Math.sin(theta);
    const c = palette[(Math.random() * palette.length) | 0];
    col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b;
    scale[i] = 0.5 + Math.random() * 1.6;
  }
  const pGeo = new THREE.BufferGeometry();
  pGeo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  pGeo.setAttribute("aColor", new THREE.BufferAttribute(col, 3));
  pGeo.setAttribute("aScale", new THREE.BufferAttribute(scale, 1));

  const pUniforms = { uTime: { value: 0 }, uPx: { value: renderer.getPixelRatio() } };
  const pMat = new THREE.ShaderMaterial({
    uniforms: pUniforms,
    transparent: true,
    depthWrite: false,
    blending: THREE.NormalBlending,
    vertexShader: /* glsl */ `
      attribute vec3 aColor;
      attribute float aScale;
      uniform float uTime;
      uniform float uPx;
      varying vec3 vColor;
      varying float vTw;
      void main() {
        vColor = aColor;
        vec3 p = position;
        p.y += sin(uTime * 0.35 + position.x * 1.7) * 0.16;
        p.x += cos(uTime * 0.22 + position.y * 1.3) * 0.1;
        vTw = 0.55 + 0.45 * sin(uTime * (0.6 + aScale * 0.5) + position.z * 3.0);
        vec4 mv = modelViewMatrix * vec4(p, 1.0);
        gl_PointSize = aScale * uPx * 5.2 * (1.0 / -mv.z) * 6.0;
        gl_Position = projectionMatrix * mv;
      }
    `,
    fragmentShader: /* glsl */ `
      varying vec3 vColor;
      varying float vTw;
      void main() {
        float d = length(gl_PointCoord - 0.5);
        float a = smoothstep(0.5, 0.05, d) * 0.55 * vTw;
        gl_FragColor = vec4(vColor, a);
      }
    `,
  });
  scene.add(new THREE.Points(pGeo, pMat));

  /* ---------- 交互与循环 ---------- */
  let mx = 0, my = 0, tx = 0, ty = 0;
  window.addEventListener("pointermove", (e) => {
    tx = (e.clientX / window.innerWidth - 0.5) * 2;
    ty = (e.clientY / window.innerHeight - 0.5) * 2;
  }, { passive: true });

  function resize() {
    const w = canvas.clientWidth || canvas.parentElement.clientWidth;
    const h = canvas.clientHeight || canvas.parentElement.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  resize();
  window.addEventListener("resize", resize);

  const clock = new THREE.Clock();
  let visible = true;
  document.addEventListener("visibilitychange", () => { visible = !document.hidden; });

  function frame() {
    requestAnimationFrame(frame);
    if (!visible) return;
    const t = clock.getElapsedTime();
    blobUniforms.uTime.value = t;
    pUniforms.uTime.value = t;

    mx += (tx - mx) * 0.04;
    my += (ty - my) * 0.04;

    group.rotation.y = t * 0.12 + mx * 0.25;
    group.rotation.x = Math.sin(t * 0.18) * 0.08 + my * 0.16;
    group.position.y = Math.sin(t * 0.5) * 0.1;
    ring1.rotation.z = t * 0.1;
    ring2.rotation.z = -t * 0.07;

    camera.position.x = mx * 0.35;
    camera.position.y = -my * 0.25;
    camera.lookAt(0, 0, 0);

    renderer.render(scene, camera);
    if (reduced) visible = false; // 减少动态偏好：渲染一帧后停
  }
  frame();
}
