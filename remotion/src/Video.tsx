import React from 'react';
import {AbsoluteFill, Series, Audio, staticFile, useVideoConfig} from 'remotion';
import {VideoProps} from './theme';
import {AnimatedBackground, BrandMark, ProgressBar} from './components';
import {Scene} from './scenes';

export const MZVideo: React.FC<VideoProps> = ({segments, channel, music}) => {
  const {width, height} = useVideoConfig();
  const vertical = height > width;
  const accents = segments.map((s) => s.accent);
  const accent = accents[0] || [255, 107, 53];

  return (
    <AbsoluteFill>
      <AnimatedBackground accents={accents} />
      <Series>
        {segments.map((seg, i) => (
          <Series.Sequence key={i} durationInFrames={Math.max(1, seg.durationInFrames)}>
            <Scene seg={seg} vertical={vertical} />
          </Series.Sequence>
        ))}
      </Series>
      <ProgressBar accent={accent} />
      <BrandMark channel={channel} accent={accent} vertical={vertical} />
      {music ? <Audio loop src={staticFile(music)} volume={0.1} /> : null}
    </AbsoluteFill>
  );
};
