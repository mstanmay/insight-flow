'use client';

import React, { useRef, useCallback, useEffect } from 'react';
import './BorderGlow.css';

function parseHSL(hslStr) {
  const match = hslStr.match(/([\d.]+)\s*([\d.]+)%?\s*([\d.]+)%?/);
  if (!match) return { h: 40, s: 80, l: 80 };
  return { h: parseFloat(match[1]), s: parseFloat(match[2]), l: parseFloat(match[3]) };
}

function buildGlowVars(glowColor, intensity) {
  const { h, s, l } = parseHSL(glowColor);
  const base = `${h}deg ${s}% ${l}%`;
  const opacities = [100, 60, 50, 40, 30, 20, 10];
  const keys = ['', '-60', '-50', '-40', '-30', '-20', '-10'];
  const vars = {};
  for (let i = 0; i < opacities.length; i++) {
    vars[`--glow-color${keys[i]}`] = `hsl(${base} / ${Math.min(opacities[i] * intensity, 100)}%)`;
  }
  return vars;
}

const GRADIENT_POSITIONS = ['80% 55%', '69% 34%', '8% 6%', '41% 38%', '86% 85%', '82% 18%', '51% 4%'];
const GRADIENT_KEYS = ['--gradient-one', '--gradient-two', '--gradient-three', '--gradient-four', '--gradient-five', '--gradient-six', '--gradient-seven'];
const COLOR_MAP = [0, 1, 2, 0, 1, 2, 1];

function buildGradientVars(colors) {
  const vars = {};
  for (let i = 0; i < 7; i++) {
    const c = colors[Math.min(COLOR_MAP[i], colors.length - 1)];
    vars[GRADIENT_KEYS[i]] = `radial-gradient(at ${GRADIENT_POSITIONS[i]}, ${c} 0px, transparent 50%)`;
  }
  vars['--gradient-base'] = `linear-gradient(${colors[0]} 0 100%)`;
  return vars;
}

function isLightColor(color) {
  const value = color.trim().replace('#', '');
  if (!/^[\da-f]{3}([\da-f]{3})?$/i.test(value)) return false;
  const hex = value.length === 3 ? value.split('').map(char => char + char).join('') : value;
  const red = parseInt(hex.slice(0, 2), 16);
  const green = parseInt(hex.slice(2, 4), 16);
  const blue = parseInt(hex.slice(4, 6), 16);
  return red * 0.2126 + green * 0.7152 + blue * 0.0722 > 180;
}

function easeOutCubic(x) { return 1 - Math.pow(1 - x, 3); }
function easeInCubic(x) { return x * x * x; }

function animateValue({ start = 0, end = 100, duration = 1000, delay = 0, ease = easeOutCubic, onUpdate, onEnd }) {
  const t0 = performance.now() + delay;
  function tick() {
    const elapsed = performance.now() - t0;
    const t = Math.min(elapsed / duration, 1);
    onUpdate(start + (end - start) * ease(t));
    if (t < 1) requestAnimationFrame(tick);
    else if (onEnd) onEnd();
  }
  setTimeout(() => requestAnimationFrame(tick), delay);
}

export default function BorderGlow({
  children,
  className = '',
  edgeSensitivity = 30,
  glowColor = '40 80 80',
  backgroundColor = '#120F17',
  borderRadius = 28,
  glowRadius = 40,
  glowIntensity = 1,
  coneSpread = 25,
  animated = false,
  colors = ['#c299ff', '#ff99dd', '#99ffbb'],
}) {
  const cardRef = useRef(null);

  const setProximity = useCallback((val) => {
    cardRef.current?.style.setProperty('--edge-proximity', val.toFixed(2));
  }, []);

  const setAngle = useCallback((deg) => {
    cardRef.current?.style.setProperty('--cursor-angle', `${deg.toFixed(2)}deg`);
  }, []);

  const handlePointerMove = useCallback((e) => {
    const card = cardRef.current;
    if (!card) return;

    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const cx = rect.width / 2;
    const cy = rect.height / 2;
    const dx = x - cx;
    const dy = y - cy;

    let kx = Infinity, ky = Infinity;
    if (dx !== 0) kx = cx / Math.abs(dx);
    if (dy !== 0) ky = cy / Math.abs(dy);
    const proximity = Math.min(Math.max(1 / Math.min(kx, ky), 0), 1) * 100;

    const radians = Math.atan2(dy, dx);
    let degrees = radians * (180 / Math.PI) + 90;
    if (degrees < 0) degrees += 360;

    setProximity(proximity);
    setAngle(degrees);
  }, [setProximity, setAngle]);

  const handlePointerOut = useCallback((e) => {
    if (!cardRef.current?.contains(e.relatedTarget)) {
      setProximity(0);
    }
  }, [setProximity]);

  useEffect(() => {
    if (!animated) return;
    const card = cardRef.current;
    if (!card) return;

    card.classList.add('sweep-active');
    setProximity(100);

    animateValue({
      start: 0,
      end: 360,
      duration: 2500,
      ease: easeOutCubic,
      onUpdate: (deg) => setAngle(deg),
      onEnd: () => {
        animateValue({
          start: 100,
          end: 0,
          duration: 800,
          ease: easeInCubic,
          onUpdate: (p) => setProximity(p),
          onEnd: () => card.classList.remove('sweep-active'),
        });
      },
    });
  }, [animated, setProximity, setAngle]);

  const glowVars = buildGlowVars(glowColor, glowIntensity);
  const gradientVars = buildGradientVars(colors);
  const isLight = isLightColor(backgroundColor);

  return (
    <div
      ref={cardRef}
      onPointerMove={handlePointerMove}
      onPointerOut={handlePointerOut}
      className={`border-glow-card ${isLight ? 'border-glow-card--light' : ''} ${className}`}
      style={{
        '--card-bg': backgroundColor,
        '--edge-sensitivity': edgeSensitivity,
        '--border-radius': `${borderRadius}px`,
        '--glow-padding': `${glowRadius}px`,
        '--cone-spread': coneSpread,
        ...glowVars,
        ...gradientVars,
      }}
    >
      <div className="edge-light" />
      <div className="border-glow-inner" style={{ borderRadius: `${borderRadius}px` }}>
        {children}
      </div>
    </div>
  );
}
