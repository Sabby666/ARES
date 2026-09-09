import React, { useState, useRef, useMemo, useCallback } from 'react';
import { Canvas } from '@react-three/fiber';
import { PerspectiveCamera } from '@react-three/drei';
import CoreScene, { CoreState } from './CoreScene';
import JarvisCameraController from './JarvisCameraController';

interface AresCoreProps {
  status?: string;
  className?: string;
}

export default function AresCore({ status = 'IDLE', className = '' }: AresCoreProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [isFocused, setIsFocused] = useState(false);

  // Mutable container-relative pointer reference: x in [-1, 1], y in [-1, 1]
  const pointerRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  // Normalize status to CoreState
  const normalizedStatus = useMemo((): CoreState => {
    if (!status) return 'IDLE';
    const s = status.toUpperCase();
    if (['IDLE', 'STARTING', 'POLICY_CHECK', 'RECON', 'ANALYSIS', 'TOOL_EXECUTION', 'EVIDENCE', 'COMPLETED', 'BLOCKED', 'ERROR'].includes(s)) {
      return s as CoreState;
    }
    if (s === 'RUNNING') return 'ANALYSIS';
    if (s === 'CREATED') return 'STARTING';
    if (s === 'FAILED') return 'ERROR';
    return 'IDLE';
  }, [status]);

  const handleMouseEnter = useCallback(() => {
    setIsHovered(true);
  }, []);

  const handlePointerMove = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0) {
      const nx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const ny = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      pointerRef.current.x = Math.max(-1, Math.min(1, nx));
      pointerRef.current.y = Math.max(-1, Math.min(1, ny));
    }
  }, []);

  const handlePointerLeave = useCallback(() => {
    setIsHovered(false);
    // Smoothly reset target pointer back to neutral origin (0, 0)
    pointerRef.current.x = 0;
    pointerRef.current.y = 0;
  }, []);

  const toggleFocus = useCallback(() => setIsFocused((prev) => !prev), []);

  return (
    <div
      className={`core-container ${className}`}
      onMouseEnter={handleMouseEnter}
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
    >
      <div className="core-overlay" style={{ pointerEvents: 'none' }}>
        <div
          style={{
            position: 'absolute',
            top: 16,
            left: 16,
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            color: 'var(--text-muted)',
            letterSpacing: '0.05em',
          }}
        >
          [CORE STATUS: {normalizedStatus}]
        </div>

        {/* Minimal Focus Control in Overlay */}
        <button
          onClick={toggleFocus}
          type="button"
          style={{
            position: 'absolute',
            top: 14,
            right: 16,
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            color: isFocused ? '#00ffff' : 'var(--text-muted)',
            background: 'rgba(10, 20, 40, 0.4)',
            border: isFocused ? '1px solid rgba(0, 255, 255, 0.4)' : '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 4,
            padding: '3px 8px',
            cursor: 'pointer',
            letterSpacing: '0.05em',
            pointerEvents: 'auto',
            transition: 'all 0.2s ease',
          }}
          title="Toggle Deep Inspect (Double-click scene or press Esc)"
        >
          [{isFocused ? 'RESET VIEW' : 'DEEP INSPECT'}]
        </button>

        <div
          style={{
            position: 'absolute',
            bottom: 16,
            right: 16,
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            color: 'var(--text-muted)',
          }}
        >
          ARES V0.1.0 // LOCAL NODE
        </div>
      </div>

      <div className="core-canvas-wrapper">
        <Canvas
          dpr={[1, 2]}
          gl={{
            antialias: true,
            alpha: true,
            powerPreference: 'high-performance',
          }}
        >
          {/* Default PerspectiveCamera baseline */}
          <PerspectiveCamera
            makeDefault
            position={[0, 1.0, 10.0]}
            fov={48}
            near={0.1}
            far={200}
          />

          {/* Cinematic Jarvis Camera Controller */}
          <JarvisCameraController
            isFocused={isFocused}
            onFocusChange={setIsFocused}
            isHovered={isHovered}
            pointerRef={pointerRef}
          />

          <React.Suspense fallback={null}>
            <CoreScene
              status={normalizedStatus}
              isHovered={isHovered}
              pointerRef={pointerRef}
            />
          </React.Suspense>
        </Canvas>
      </div>
    </div>
  );
}
