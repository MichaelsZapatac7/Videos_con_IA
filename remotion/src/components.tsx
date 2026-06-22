import React from 'react';
import {
  AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig,
  interpolate, spring, Easing,
} from 'remotion';
import {RGB, rgb, FONT, SQL_KEYWORDS, Segment} from './theme';

// ───────────────────────── Fondo animado (sin blur, barato) ─────────────────────────
export const AnimatedBackground: React.FC<{accents: RGB[]}> = ({accents}) => {
  const frame = useCurrentFrame();
  const {width, height, durationInFrames} = useVideoConfig();
  const t = (frame / Math.max(1, durationInFrames)) * (accents.length - 1);
  const i = Math.min(accents.length - 2, Math.floor(t));
  const f = t - i;
  const a = accents[Math.max(0, i)] || [255, 107, 53];
  const b = accents[Math.max(0, i) + 1] || a;
  const accent: RGB = [
    Math.round(a[0] + (b[0] - a[0]) * f),
    Math.round(a[1] + (b[1] - a[1]) * f),
    Math.round(a[2] + (b[2] - a[2]) * f),
  ];
  // "Blobs" como radial-gradients (baratos), animados con translate
  const glow = (cx: number, cy: number, r: number, speed: number, ph: number, c: RGB, op: number) => {
    const x = Math.sin(frame * speed + ph) * width * 0.05;
    const y = Math.cos(frame * speed * 0.8 + ph) * height * 0.05;
    return (
      <div style={{
        position: 'absolute', left: cx - r, top: cy - r, width: r * 2, height: r * 2,
        transform: `translate(${x}px,${y}px)`,
        background: `radial-gradient(circle at center, ${rgb(c, op)} 0%, ${rgb(c, 0)} 70%)`,
      }} />
    );
  };
  return (
    <AbsoluteFill style={{background: 'linear-gradient(135deg,#0c0d16 0%,#13142a 55%,#0a0a14 100%)'}}>
      {glow(width * 0.24, height * 0.30, width * 0.34, 0.012, 0, accent, 0.28)}
      {glow(width * 0.82, height * 0.70, width * 0.40, 0.009, 2, [80, 120, 255], 0.20)}
      {glow(width * 0.62, height * 0.18, width * 0.24, 0.015, 4, accent, 0.16)}
      <AbsoluteFill style={{
        backgroundImage:
          'linear-gradient(rgba(255,255,255,0.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.035) 1px,transparent 1px)',
        backgroundSize: '90px 90px',
        transform: `translateY(${(frame * 0.4) % 90}px)`,
      }} />
      {/* viñeta como gradiente radial (barato) */}
      <AbsoluteFill style={{
        background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 45%, rgba(0,0,0,0.8) 100%)',
      }} />
    </AbsoluteFill>
  );
};

// ───────────────────────── Partículas (ligeras) ─────────────────────────
export const Particles: React.FC<{accent: RGB; count?: number}> = ({accent, count = 14}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const dots = new Array(count).fill(0).map((_, k) => {
    const seed = (k * 9301 + 49297) % 233280;
    const rx = seed / 233280;
    const ry = ((seed * 7) % 233280) / 233280;
    const size = 3 + (k % 3);
    const speed = 0.3 + (k % 5) * 0.1;
    const y = (height * ry - frame * speed * 3) % height;
    const x = width * rx + Math.sin(frame * 0.02 + k) * 12;
    return (
      <div key={k} style={{
        position: 'absolute', left: x, top: (y + height) % height,
        width: size, height: size, borderRadius: '50%', background: rgb(accent, 0.55),
      }} />
    );
  });
  return <AbsoluteFill>{dots}</AbsoluteFill>;
};

// ───────────────────────── Imagen con Ken Burns ─────────────────────────
export const KenBurns: React.FC<{src: string; dur: number; idx: number; radius?: number}> = ({
  src, dur, idx, radius = 0,
}) => {
  const frame = useCurrentFrame();
  const zoomIn = idx % 2 === 0;
  const z = interpolate(frame, [0, dur], zoomIn ? [1.06, 1.22] : [1.22, 1.06], {
    extrapolateRight: 'clamp',
  });
  const px = interpolate(frame, [0, dur], [-1.5, 1.5]);
  const py = interpolate(frame, [0, dur], [1.2, -1.2]);
  return (
    <AbsoluteFill style={{overflow: 'hidden', borderRadius: radius}}>
      <Img src={staticFile(src)} style={{
        width: '100%', height: '100%', objectFit: 'cover',
        transform: `scale(${z}) translate(${px}%,${py}%)`,
      }} />
    </AbsoluteFill>
  );
};

// Galería B-roll: cicla imágenes con crossfade dentro de la escena
export const BrollGallery: React.FC<{images: string[]; dur: number; radius?: number}> = ({
  images, dur, radius = 0,
}) => {
  const frame = useCurrentFrame();
  if (!images.length) return null;
  const per = dur / images.length;
  return (
    <AbsoluteFill>
      {images.map((src, k) => {
        const start = k * per;
        const op = interpolate(
          frame,
          [start - 10, start + 6, start + per - 6, start + per + 10],
          [0, 1, 1, 0],
          {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
        );
        return (
          <AbsoluteFill key={k} style={{opacity: op}}>
            <KenBurns src={src} dur={per + 20} idx={k} radius={radius} />
          </AbsoluteFill>
        );
      })}
    </AbsoluteFill>
  );
};

// ───────────────────────── Marca del canal ─────────────────────────
export const BrandMark: React.FC<{channel: string; accent: RGB; vertical?: boolean}> = ({
  channel, accent, vertical,
}) => {
  const frame = useCurrentFrame();
  const pulse = 1 + Math.sin(frame * 0.1) * 0.15;
  return (
    <div style={{
      position: 'absolute', top: vertical ? 70 : 48, left: vertical ? 50 : 60,
      display: 'flex', alignItems: 'center', gap: 16, zIndex: 20,
    }}>
      <div style={{
        width: 22, height: 22, borderRadius: '50%', background: rgb(accent),
        transform: `scale(${pulse})`, boxShadow: `0 0 18px ${rgb(accent, 0.9)}`,
      }} />
      <span style={{
        color: 'white', fontFamily: FONT, fontWeight: 800,
        fontSize: vertical ? 40 : 34, letterSpacing: 2,
      }}>{channel}</span>
    </div>
  );
};

// ───────────────────────── Logo (marca de agua) ─────────────────────────
export const LogoWatermark: React.FC<{src: string; vertical?: boolean}> = ({src, vertical}) => {
  const frame = useCurrentFrame();
  const {height} = useVideoConfig();
  // Escala por ALTURA (el logo es alto y angosto) para que no domine la esquina
  const h = height * (vertical ? 0.10 : 0.14);
  const fade = interpolate(frame, [0, 15], [0, 0.9], {extrapolateRight: 'clamp'});
  return (
    <div style={{
      position: 'absolute', top: vertical ? 56 : 34, right: vertical ? 40 : 50,
      zIndex: 25, opacity: fade,
    }}>
      <Img src={staticFile(src)} style={{
        height: h, width: 'auto',
        filter: 'drop-shadow(0 4px 14px rgba(0,0,0,0.55))',
      }} />
    </div>
  );
};

// ───────────────────────── Barra de progreso ─────────────────────────
export const ProgressBar: React.FC<{accent: RGB}> = ({accent}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const w = interpolate(frame, [0, durationInFrames], [0, 100], {extrapolateRight: 'clamp'});
  return (
    <div style={{position: 'absolute', top: 0, left: 0, right: 0, height: 6, zIndex: 30, background: 'rgba(255,255,255,0.08)'}}>
      <div style={{height: '100%', width: `${w}%`, background: rgb(accent), boxShadow: `0 0 12px ${rgb(accent)}`}} />
    </div>
  );
};

// ───────────────────────── Badge numérico ─────────────────────────
export const NumberBadge: React.FC<{number: string; accent: RGB; size: number}> = ({
  number, accent, size,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame, fps, config: {damping: 12, mass: 0.8}});
  const ringRot = frame * 2;
  return (
    <div style={{position: 'relative', width: size, height: size, transform: `scale(${s})`}}>
      <div style={{
        position: 'absolute', inset: 0, borderRadius: '50%',
        border: `4px solid ${rgb(accent, 0.5)}`, borderTopColor: rgb(accent),
        transform: `rotate(${ringRot}deg)`,
      }} />
      <div style={{
        position: 'absolute', inset: size * 0.1, borderRadius: '50%',
        background: rgb(accent, 0.16), border: `3px solid ${rgb(accent)}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{color: 'white', fontFamily: FONT, fontWeight: 900, fontSize: size * 0.5}}>
          {number}
        </span>
      </div>
    </div>
  );
};

// ───────────────────────── Tarjeta de código (terminal) ─────────────────────────
export const CodeCard: React.FC<{code: string; accent: RGB; fontSize: number}> = ({
  code, accent, fontSize,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 14}});
  // efecto de tipeo
  const chars = Math.floor(interpolate(frame, [6, 6 + code.length * 1.2], [0, code.length], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  }));
  const shown = code.slice(0, chars);
  const cursorOn = Math.floor(frame / 8) % 2 === 0;
  const tokens = shown.split(/(\s+)/);
  return (
    <div style={{
      transform: `translateY(${(1 - enter) * 40}px)`, opacity: enter,
      background: 'rgba(10,12,20,0.92)', border: `1px solid ${rgb(accent, 0.5)}`,
      borderRadius: 16, padding: '22px 26px', maxWidth: '92%',
      boxShadow: `0 20px 60px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.04)`,
    }}>
      <div style={{display: 'flex', gap: 9, marginBottom: 16}}>
        {['#ff5f56', '#ffbd2e', '#27c93f'].map((c) => (
          <div key={c} style={{width: 14, height: 14, borderRadius: '50%', background: c}} />
        ))}
      </div>
      <div style={{
        fontFamily: "'DejaVu Sans Mono','Courier New',monospace", fontSize,
        color: '#e6e6e6', whiteSpace: 'pre-wrap', lineHeight: 1.4,
      }}>
        {tokens.map((tk, k) => {
          const isKw = SQL_KEYWORDS.has(tk.toUpperCase());
          return (
            <span key={k} style={{color: isKw ? rgb(accent) : '#e6e6e6', fontWeight: isKw ? 800 : 500}}>
              {tk}
            </span>
          );
        })}
        <span style={{opacity: cursorOn ? 1 : 0, color: rgb(accent), fontWeight: 800}}>▋</span>
      </div>
    </div>
  );
};

// ───────────────────────── Subtítulos animados ─────────────────────────
export const Captions: React.FC<{text: string; dur: number; accent: RGB; fontSize: number; vertical?: boolean}> = ({
  text, dur, accent, fontSize, vertical,
}) => {
  const frame = useCurrentFrame();
  const words = text.split(/\s+/).filter(Boolean);
  const perChunk = vertical ? 4 : 7;
  const chunks: string[] = [];
  for (let i = 0; i < words.length; i += perChunk) {
    chunks.push(words.slice(i, i + perChunk).join(' '));
  }
  if (!chunks.length) return null;
  const per = dur / chunks.length;
  const idx = Math.min(chunks.length - 1, Math.floor(frame / per));
  const local = frame - idx * per;
  const op = interpolate(local, [0, 5, per - 5, per], [0, 1, 1, 0.6], {extrapolateRight: 'clamp'});
  const pop = interpolate(local, [0, 8], [0.86, 1], {extrapolateRight: 'clamp'});
  return (
    <div style={{
      position: 'absolute', left: 0, right: 0, bottom: vertical ? '16%' : 70,
      display: 'flex', justifyContent: 'center', padding: '0 8%', zIndex: 15,
    }}>
      <div style={{
        opacity: op, transform: `scale(${pop})`,
        background: 'rgba(0,0,0,0.55)', borderRadius: 14, padding: vertical ? '18px 30px' : '14px 28px',
        borderBottom: `4px solid ${rgb(accent)}`,
        fontFamily: FONT, fontWeight: 800, color: 'white', textAlign: 'center',
        fontSize, lineHeight: 1.25, maxWidth: '90%',
        textShadow: '0 2px 10px rgba(0,0,0,0.6)',
      }}>
        {chunks[idx]}
      </div>
    </div>
  );
};

export const titleEnter = (frame: number, fps: number, delay = 0) =>
  spring({frame: frame - delay, fps, config: {damping: 13, mass: 0.9}});
