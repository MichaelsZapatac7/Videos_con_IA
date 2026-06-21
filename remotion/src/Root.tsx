import React from 'react';
import {Composition} from 'remotion';

const Hello: React.FC = () => (
  <div style={{flex: 1, background: '#1A1A2E', display: 'flex',
    alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: 80}}>
    MZSHARD · Remotion OK
  </div>
);

export const RemotionRoot: React.FC = () => (
  <Composition id="Hello" component={Hello} durationInFrames={30}
    fps={30} width={1280} height={720} />
);
