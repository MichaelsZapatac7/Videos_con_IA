import React from 'react';
import {
  AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig,
  interpolate, spring,
} from 'remotion';
import {Segment, RGB, rgb, FONT} from './theme';
import {
  BrollGallery, Particles, NumberBadge, CodeCard, Captions, titleEnter,
} from './components';

const DarkOverlay: React.FC<{from?: string}> = ({from = 'left'}) => (
  <AbsoluteFill style={{
    background:
      from === 'left'
        ? 'linear-gradient(90deg, rgba(6,7,14,0.92) 0%, rgba(6,7,14,0.72) 42%, rgba(6,7,14,0.35) 100%)'
        : 'linear-gradient(0deg, rgba(6,7,14,0.95) 0%, rgba(6,7,14,0.55) 45%, rgba(6,7,14,0.2) 100%)',
  }} />
);

// ───────────────────────── Bienvenida ─────────────────────────
export const WelcomeScene: React.FC<{seg: Segment; vertical: boolean}> = ({seg, vertical}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s1 = titleEnter(frame, fps, 4);
  const s2 = titleEnter(frame, fps, 14);
  const line = interpolate(frame, [20, 40], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
      <Particles accent={seg.accent} />
      <div style={{opacity: s1, transform: `translateY(${(1 - s1) * 30}px)`,
        color: '#c9c9d6', fontFamily: FONT, fontWeight: 700, letterSpacing: 6,
        fontSize: vertical ? 44 : 40}}>
        BIENVENIDO A
      </div>
      <div style={{opacity: s2, transform: `scale(${0.8 + s2 * 0.2})`,
        color: 'white', fontFamily: FONT, fontWeight: 900,
        fontSize: vertical ? 150 : 180, letterSpacing: 4, marginTop: 10,
        textShadow: `0 0 60px ${rgb(seg.accent, 0.6)}`}}>
        {seg.title}
      </div>
      <div style={{width: `${line * (vertical ? 60 : 28)}%`, height: 8, background: rgb(seg.accent),
        borderRadius: 4, marginTop: 24, boxShadow: `0 0 20px ${rgb(seg.accent)}`}} />
      <div style={{opacity: line, color: rgb(seg.accent), fontFamily: FONT, fontWeight: 700,
        fontSize: vertical ? 40 : 38, marginTop: 28}}>
        {seg.tagline}
      </div>
    </AbsoluteFill>
  );
};

// ───────────────────────── Tema / Intro ─────────────────────────
export const TopicScene: React.FC<{seg: Segment; vertical: boolean}> = ({seg, vertical}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = titleEnter(frame, fps, 6);
  return (
    <AbsoluteFill>
      {seg.images.length > 0 && <BrollGallery images={seg.images} dur={seg.durationInFrames} />}
      <DarkOverlay from="bottom" />
      <Particles accent={seg.accent} count={18} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', padding: '0 8%'}}>
        <div style={{opacity: s, transform: `translateY(${(1 - s) * 40}px)`, textAlign: 'center'}}>
          <div style={{display: 'inline-block', padding: '8px 22px', borderRadius: 999,
            border: `2px solid ${rgb(seg.accent)}`, color: rgb(seg.accent),
            fontFamily: FONT, fontWeight: 800, fontSize: vertical ? 34 : 30, letterSpacing: 3,
            marginBottom: 26}}>
            MZSHARD
          </div>
          <div style={{color: 'white', fontFamily: FONT, fontWeight: 900,
            fontSize: vertical ? 110 : 130, lineHeight: 1.02,
            textShadow: `0 0 50px ${rgb(seg.accent, 0.5)}`}}>
            {seg.title}
          </div>
        </div>
      </AbsoluteFill>
      <Captions text={seg.text} dur={seg.durationInFrames} accent={seg.accent}
        fontSize={vertical ? 46 : 40} vertical={vertical} />
    </AbsoluteFill>
  );
};

// ───────────────────────── Item (con código + B-roll) ─────────────────────────
export const ItemScene: React.FC<{seg: Segment; vertical: boolean}> = ({seg, vertical}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const tEnter = titleEnter(frame, fps, 10);

  const content = (
    <>
      <div style={{display: 'flex', alignItems: 'center', gap: 24, marginBottom: 22}}>
        <NumberBadge number={seg.number || ''} accent={seg.accent} size={vertical ? 150 : 130} />
        <div style={{opacity: tEnter, transform: `translateX(${(1 - tEnter) * -30}px)`,
          color: 'white', fontFamily: FONT, fontWeight: 900,
          fontSize: vertical ? 80 : 88, lineHeight: 1.0,
          textShadow: `0 4px 24px rgba(0,0,0,0.5)`}}>
          {seg.title}
        </div>
      </div>
      {seg.tagline ? (
        seg.code ? (
          <CodeCard code={seg.tagline} accent={seg.accent} fontSize={vertical ? 40 : 42} />
        ) : (
          <div style={{opacity: tEnter, color: rgb(seg.accent), fontFamily: FONT,
            fontWeight: 700, fontSize: vertical ? 44 : 46}}>{seg.tagline}</div>
        )
      ) : null}
    </>
  );

  if (vertical) {
    return (
      <AbsoluteFill>
        <AbsoluteFill style={{bottom: '40%'}}>
          {seg.images.length > 0 && <BrollGallery images={seg.images} dur={seg.durationInFrames} />}
        </AbsoluteFill>
        <DarkOverlay from="bottom" />
        <div style={{position: 'absolute', top: '42%', left: 0, right: 0, padding: '0 7%'}}>
          {content}
        </div>
        <Captions text={seg.text} dur={seg.durationInFrames} accent={seg.accent}
          fontSize={46} vertical />
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill>
      {seg.images.length > 0 && <BrollGallery images={seg.images} dur={seg.durationInFrames} />}
      <DarkOverlay from="left" />
      <div style={{position: 'absolute', top: 0, bottom: 0, left: '6%', width: '58%',
        display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
        {content}
      </div>
      <Captions text={seg.text} dur={seg.durationInFrames} accent={seg.accent} fontSize={40} />
    </AbsoluteFill>
  );
};

// ───────────────────────── Outro / Suscríbete ─────────────────────────
export const OutroScene: React.FC<{seg: Segment; vertical: boolean}> = ({seg, vertical}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = titleEnter(frame, fps, 6);
  const pulse = 1 + Math.sin(frame * 0.18) * 0.05;
  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
      <Particles accent={seg.accent} />
      <div style={{opacity: s, transform: `scale(${0.85 + s * 0.15})`, color: 'white',
        fontFamily: FONT, fontWeight: 900, fontSize: vertical ? 120 : 150,
        textShadow: `0 0 60px ${rgb(seg.accent, 0.6)}`}}>
        SUSCRÍBETE
      </div>
      <div style={{transform: `scale(${pulse})`, marginTop: 40, background: '#e6212d',
        borderRadius: 18, padding: vertical ? '26px 60px' : '24px 56px',
        color: 'white', fontFamily: FONT, fontWeight: 900, fontSize: vertical ? 50 : 48,
        boxShadow: '0 16px 50px rgba(230,33,45,0.5)'}}>
        ▶  SUSCRIBIRSE
      </div>
      <div style={{marginTop: 36, color: rgb(seg.accent), fontFamily: FONT, fontWeight: 700,
        fontSize: vertical ? 38 : 34}}>
        @mzcshard · nuevos videos cada semana
      </div>
      <Captions text={seg.text} dur={seg.durationInFrames} accent={seg.accent}
        fontSize={vertical ? 44 : 38} vertical={vertical} />
    </AbsoluteFill>
  );
};

// ───────────────────────── Dispatcher ─────────────────────────
export const Scene: React.FC<{seg: Segment; vertical: boolean}> = ({seg, vertical}) => {
  const inner =
    seg.kind === 'welcome' ? <WelcomeScene seg={seg} vertical={vertical} /> :
    seg.kind === 'topic' ? <TopicScene seg={seg} vertical={vertical} /> :
    seg.kind === 'outro' ? <OutroScene seg={seg} vertical={vertical} /> :
    <ItemScene seg={seg} vertical={vertical} />;
  return (
    <AbsoluteFill>
      {inner}
      {seg.audio ? <Audio src={staticFile(seg.audio)} /> : null}
    </AbsoluteFill>
  );
};
