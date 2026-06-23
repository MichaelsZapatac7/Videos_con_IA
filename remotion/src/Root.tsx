import React from 'react';
import {Composition} from 'remotion';
import {MZVideo} from './Video';
import {VideoProps} from './theme';

const empty: VideoProps = {fps: 30, channel: 'MZSHARD', music: null, segments: []};

const calcDur = ({props}: {props: VideoProps}) => {
  const total = (props.segments || []).reduce(
    (a, s) => a + Math.max(1, s.durationInFrames || 0), 0);
  return {durationInFrames: Math.max(1, total), fps: props.fps || 30};
};

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Video"
      component={MZVideo}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={empty}
      calculateMetadata={calcDur}
    />
    <Composition
      id="Short"
      component={MZVideo}
      durationInFrames={300}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={empty}
      calculateMetadata={calcDur}
    />
  </>
);
