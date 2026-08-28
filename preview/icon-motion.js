const DURATION_MS = 2000;

function fieldName(field) {
  return field.split("@")[0];
}

function cubicBezierY(x, p1x, p1y, p2x, p2y) {
  if (x <= 0) return 0;
  if (x >= 1) return 1;

  let t = x;
  for (let i = 0; i < 8; i += 1) {
    const mt = 1 - t;
    const bx = 3 * mt * mt * t * p1x + 3 * mt * t * t * p2x + t * t * t;
    const dx = 3 * mt * mt * p1x + 6 * mt * t * (p2x - p1x) + 3 * t * t * (1 - p2x);
    if (Math.abs(dx) < 1e-6) break;
    t -= (bx - x) / dx;
    t = Math.min(1, Math.max(0, t));
  }

  const mt = 1 - t;
  return 3 * mt * mt * t * p1y + 3 * mt * t * t * p2y + t * t * t;
}

function springProgress(localT, durationMs, springValues, start, end) {
  const { mass = 1, stiffness = 600, damping = 15 } = springValues;
  const wn = Math.sqrt(stiffness / mass);
  const zeta = damping / (2 * Math.sqrt(stiffness * mass));
  const t = (localT * durationMs) / 1000;
  const delta = end - start;
  if (zeta < 1) {
    const wd = wn * Math.sqrt(1 - zeta * zeta);
    const envelope = Math.exp(-zeta * wn * t);
    const value =
      end - envelope * (delta * Math.cos(wd * t) + ((zeta * wn * delta) / wd) * Math.sin(wd * t));
    return value;
  }
  const envelope = Math.exp(-wn * t);
  return end - (delta + wn * delta * t) * envelope;
}

function sampleField(keyframes, timeMs) {
  if (!keyframes.length) return 0;
  if (timeMs <= keyframes[0].timeMs) return keyframes[0].value;
  const last = keyframes[keyframes.length - 1];
  if (timeMs >= last.timeMs) return last.value;

  for (let i = 0; i < keyframes.length - 1; i += 1) {
    const from = keyframes[i];
    const to = keyframes[i + 1];
    if (timeMs > to.timeMs) continue;
    const duration = to.timeMs - from.timeMs;
    if (duration <= 0) return to.value;
    const localT = (timeMs - from.timeMs) / duration;
    const easing = from.easingToNext || {};
    if (easing.hold) return from.value;
    if (easing.springValues) {
      return springProgress(localT, duration, easing.springValues, from.value, to.value);
    }
    if (easing.bezierValues) {
      const { p1x, p1y, p2x, p2y } = easing.bezierValues;
      return from.value + (to.value - from.value) * cubicBezierY(localT, p1x, p1y, p2x, p2y);
    }
    return from.value + (to.value - from.value) * localT;
  }
  return last.value;
}

function sampleNode(node, timeMs) {
  const values = {
    motionTranslationX: 0,
    motionTranslationY: 0,
    motionScaleX: 1,
    motionScaleY: 1,
    opacity: 100,
  };
  for (const field of node.fields) {
    values[fieldName(field.field)] = sampleField(field.keyframes, timeMs);
  }
  return values;
}

function applyNode(el, values) {
  const sx = values.motionScaleX ?? 1;
  const sy = values.motionScaleY ?? 1;
  el.style.opacity = String((values.opacity ?? 100) / 100);
  if (el.dataset.layout === "static") {
    el.style.transform = `scale(${sx}, ${sy})`;
    return;
  }
  const x = values.motionTranslationX || 0;
  const y = values.motionTranslationY || 0;
  el.style.transform = `translate(${x}px, ${y}px) scale(${sx}, ${sy})`;
}

export async function playIconMotion(options) {
  const { root, playhead, timeLabel, reducedMotion } = options;
  const motion = await fetch("./assets/figma-motion.json").then((res) => res.json());
  const layers = [...root.querySelectorAll("[data-node]")];
  const nodeMap = Object.fromEntries(motion.nodes.map((node) => [node.node, node]));

  const applyTime = (timeMs) => {
    for (const el of layers) {
      const spec = nodeMap[el.dataset.node];
      if (!spec) continue;
      applyNode(el, sampleNode(spec, timeMs));
    }
    if (playhead) playhead.style.width = `${(timeMs / DURATION_MS) * 100}%`;
    if (timeLabel) timeLabel.textContent = `${(timeMs / 1000).toFixed(2)}s`;
  };

  if (reducedMotion) {
    applyTime(DURATION_MS);
    return { stop() {} };
  }

  let start = performance.now();
  let playing = true;
  let raf = 0;
  let pausedAt = 0;

  const tick = (now) => {
    if (!playing) return;
    const timeMs = (now - start) % DURATION_MS;
    applyTime(timeMs);
    raf = requestAnimationFrame(tick);
  };

  applyTime(0);
  raf = requestAnimationFrame(tick);

  return {
    play() {
      if (playing) return;
      playing = true;
      start = performance.now() - pausedAt;
      raf = requestAnimationFrame(tick);
    },
    pause() {
      playing = false;
      pausedAt = (performance.now() - start) % DURATION_MS;
      cancelAnimationFrame(raf);
    },
    restart() {
      playing = true;
      pausedAt = 0;
      start = performance.now();
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(tick);
    },
    stop() {
      playing = false;
      cancelAnimationFrame(raf);
    },
  };
}

window.playIconMotion = playIconMotion;
