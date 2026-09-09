import React, { useEffect, useRef } from 'react';
import { useThree, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface JarvisCameraControllerProps {
  isFocused: boolean;
  onFocusChange?: (focused: boolean) => void;
  isHovered: boolean;
  pointerRef: React.RefObject<{ x: number; y: number }>;
}

export default function JarvisCameraController({
  isFocused,
  onFocusChange,
  isHovered,
  pointerRef,
}: JarvisCameraControllerProps) {
  const { camera, gl } = useThree();

  // Target camera coordinates
  const targetZRef = useRef<number>(10.0);
  const currentZRef = useRef<number>(10.0);
  const targetYRef = useRef<number>(1.0);

  // Smooth pointer coordinates for damped motion
  const smoothPointer = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  // Reduced motion preference
  const reducedMotionRef = useRef<boolean>(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    reducedMotionRef.current = mediaQuery.matches;
    const handler = (e: MediaQueryListEvent) => {
      reducedMotionRef.current = e.matches;
    };
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  // Sync focus state to camera distance
  useEffect(() => {
    if (isFocused) {
      targetZRef.current = 5.5; // DEEP_INSPECT
    } else {
      targetZRef.current = 10.0; // DEFAULT_VIEW
    }
  }, [isFocused]);

  // Wheel listener for smooth dolly zoom & keys / dblclick listeners
  useEffect(() => {
    const canvas = gl.domElement;

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      const delta = e.deltaY * 0.005;
      // Clamp between safe min (5.2) and max (12.0)
      targetZRef.current = THREE.MathUtils.clamp(targetZRef.current + delta, 5.2, 12.0);

      if (onFocusChange) {
        if (targetZRef.current <= 6.5 && !isFocused) {
          onFocusChange(true);
        } else if (targetZRef.current > 7.5 && isFocused) {
          onFocusChange(false);
        }
      }
    };

    const handleDblClick = () => {
      const nextFocus = targetZRef.current > 6.5;
      targetZRef.current = nextFocus ? 5.5 : 10.0;
      if (onFocusChange) {
        onFocusChange(nextFocus);
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        targetZRef.current = 10.0;
        if (onFocusChange) {
          onFocusChange(false);
        }
      }
    };

    canvas.addEventListener('wheel', handleWheel, { passive: false });
    canvas.addEventListener('dblclick', handleDblClick);
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      canvas.removeEventListener('wheel', handleWheel);
      canvas.removeEventListener('dblclick', handleDblClick);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [gl, isFocused, onFocusChange]);

  // Frame animation loop: smooth damping for camera position & parallax
  useFrame((_, delta) => {
    const reduced = reducedMotionRef.current;
    const targetPx = (reduced || !pointerRef.current) ? 0 : pointerRef.current.x;
    const targetPy = (reduced || !pointerRef.current) ? 0 : pointerRef.current.y;

    // Frame-rate independent lerp factor for pointer damping
    const lerpFactor = reduced ? 1.0 : Math.min(delta * 5.0, 0.15);
    smoothPointer.current.x = THREE.MathUtils.lerp(
      smoothPointer.current.x,
      targetPx,
      lerpFactor
    );
    smoothPointer.current.y = THREE.MathUtils.lerp(
      smoothPointer.current.y,
      targetPy,
      lerpFactor
    );

    // Damped Z transition for smooth dolly zoom
    currentZRef.current = THREE.MathUtils.lerp(
      currentZRef.current,
      targetZRef.current,
      Math.min(delta * 5.0, 0.12)
    );

    // Base Y offset scales proportionally with Z distance to preserve perspective angle
    targetYRef.current = 1.0 * (currentZRef.current / 10.0);

    // Controlled camera position translation (subtle, bounded spatial shift)
    const camX = smoothPointer.current.x * 0.70;
    const camY = targetYRef.current + (smoothPointer.current.y * 0.50);

    camera.position.x = camX;
    camera.position.y = camY;
    camera.position.z = currentZRef.current;

    // Continuous camera focus on central nucleus [0, 0, 0]
    camera.lookAt(0, 0, 0);
  });

  return null;
}
