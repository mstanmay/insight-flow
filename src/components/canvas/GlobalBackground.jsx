import React from 'react';
import FloatingLines from './FloatingLines';
import { useWorkspace } from '../../context/WorkspaceContext';

/**
 * Global reactive background canvas with theme adaptation
 */
export default function GlobalBackground() {
  const { theme } = useWorkspace();
  const isDark = theme === 'dark';

  return (
    <div
      className="fixed inset-0 pointer-events-none overflow-hidden transition-opacity duration-700"
      style={{
        zIndex: -1,
        opacity: isDark ? 0.75 : 0.65,
      }}
    >
      <FloatingLines
        enabledWaves={['top', 'middle', 'bottom']}
        lineCount={8}
        lineDistance={8}
        bendRadius={8}
        bendStrength={-2}
        interactive={true}
        parallax={true}
        animationSpeed={0.8}
        linesGradient={['#e945f5', '#6366f1', '#06b6d4', '#38bdf8']}
        backgroundColor={isDark ? '#070B14' : '#ffffff'}
        lightMode={!isDark}
        mixBlendMode={isDark ? 'screen' : 'multiply'}
      />
    </div>
  );
}
