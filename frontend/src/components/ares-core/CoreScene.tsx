import { useRef, useEffect, useState, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sphere } from '@react-three/drei';
import * as THREE from 'three';
import gsap from 'gsap';

import { Nucleus } from './Nucleus';
import { InnerField } from './InnerField';
import { TopologySphere } from './TopologySphere';
import { OrbitalSystem } from './OrbitalSystem';
import { IntelligenceNodes } from './IntelligenceNodes';
import { ParticleField } from './ParticleField';

export type CoreState = 'IDLE' | 'STARTING' | 'POLICY_CHECK' | 'RECON' | 'ANALYSIS' | 'TOOL_EXECUTION' | 'EVIDENCE' | 'COMPLETED' | 'BLOCKED' | 'ERROR';

interface CoreSceneProps {
  status: CoreState;
  isHovered?: boolean;
  pointerRef?: React.RefObject<{ x: number; y: number }>;
}

const COLORS = {
  primary: new THREE.Color('#2563EB'),    // Electric Blue
  secondary: new THREE.Color('#3B82F6'),  // Cyan/Lighter Blue
  accent: new THREE.Color('#8B5CF6'),     // Violet
  cyan: new THREE.Color('#00ffff'),       // Cyan accent
  warning: new THREE.Color('#F59E0B'),    // Amber
  error: new THREE.Color('#EF4444'),      // Crimson
  success: new THREE.Color('#10B981'),    // Green
  idle: new THREE.Color('#2563EB'),       // Idle remains blue but calmer
};

export default function CoreScene({ status, isHovered = false, pointerRef }: CoreSceneProps) {
  const groupRef = useRef<THREE.Group>(null);

  // Group refs for multi-depth differential spatial parallax
  const nucleusGroupRef = useRef<THREE.Group>(null);
  const innerGroupRef = useRef<THREE.Group>(null);
  const topologyGroupRef = useRef<THREE.Group>(null);
  const orbitalGroupRef = useRef<THREE.Group>(null);
  const nodesGroupRef = useRef<THREE.Group>(null);
  const bgParticlesGroupRef = useRef<THREE.Group>(null);
  const atmosphereGroupRef = useRef<THREE.Group>(null);

  const smoothPointerRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  const [colors, setColors] = useState({
    primary: COLORS.idle.clone(),
    secondary: COLORS.secondary.clone(),
    accent: COLORS.accent.clone(),
    glow: COLORS.idle.clone(),
  });

  const [animParams, setAnimParams] = useState({
    speed: 1,
    scale: 1,
    intensity: 1,
    particleCount: 1,
  });

  // Effective intensity incorporating hover boost (+18% energy)
  const effectiveIntensity = animParams.intensity * (isHovered ? 1.18 : 1.0);

  // Reduced motion detection
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReducedMotion(mediaQuery.matches);
    const handler = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  useEffect(() => {
    let targetPrimary = COLORS.primary;
    let targetSecondary = COLORS.secondary;
    let targetAccent = COLORS.accent;
    let targetGlow = COLORS.primary;
    let targetSpeed = reducedMotion ? 0.1 : 1;
    let targetScale = 1;
    let targetIntensity = 1;
    let targetParticleCount = 1;

    switch (status) {
      case 'IDLE':
        targetPrimary = COLORS.idle;
        targetSecondary = COLORS.secondary;
        targetAccent = COLORS.accent;
        targetGlow = COLORS.idle;
        targetSpeed = reducedMotion ? 0.1 : 1;
        targetScale = 1;
        targetIntensity = 0.6;
        targetParticleCount = 1;
        break;
      case 'STARTING':
      case 'POLICY_CHECK':
        targetPrimary = COLORS.primary;
        targetSecondary = COLORS.secondary;
        targetAccent = COLORS.accent;
        targetGlow = COLORS.primary;
        targetSpeed = reducedMotion ? 0.15 : 1.3;
        targetScale = 1.05;
        targetIntensity = 0.8;
        targetParticleCount = 1.2;
        break;
      case 'RECON':
        targetPrimary = COLORS.primary;
        targetSecondary = COLORS.cyan;
        targetAccent = COLORS.cyan;
        targetGlow = COLORS.primary;
        targetSpeed = reducedMotion ? 0.2 : 1.8;
        targetScale = 1.12;
        targetIntensity = 1.2;
        targetParticleCount = 1.5;
        break;
      case 'ANALYSIS':
        targetPrimary = COLORS.primary;
        targetSecondary = COLORS.secondary;
        targetAccent = COLORS.accent;
        targetGlow = COLORS.primary;
        targetSpeed = reducedMotion ? 0.15 : 1.5;
        targetScale = 1.08;
        targetIntensity = 1.0;
        targetParticleCount = 1.3;
        break;
      case 'TOOL_EXECUTION':
        targetPrimary = COLORS.warning;
        targetSecondary = COLORS.warning;
        targetAccent = COLORS.warning;
        targetGlow = COLORS.warning;
        targetSpeed = reducedMotion ? 0.25 : 2.2;
        targetScale = 1.18;
        targetIntensity = 1.5;
        targetParticleCount = 1.8;
        break;
      case 'EVIDENCE':
        targetPrimary = COLORS.primary;
        targetSecondary = COLORS.cyan;
        targetAccent = COLORS.accent;
        targetGlow = COLORS.primary;
        targetSpeed = reducedMotion ? 0.1 : 1.2;
        targetScale = 1.0;
        targetIntensity = 0.9;
        targetParticleCount = 1.2;
        break;
      case 'COMPLETED':
        targetPrimary = COLORS.success;
        targetSecondary = COLORS.success;
        targetAccent = COLORS.success;
        targetGlow = COLORS.success;
        targetSpeed = reducedMotion ? 0.05 : 0.6;
        targetScale = 1;
        targetIntensity = 0.7;
        targetParticleCount = 0.8;
        break;
      case 'BLOCKED':
        targetPrimary = COLORS.accent; // Violet
        targetSecondary = COLORS.accent;
        targetAccent = COLORS.accent;
        targetGlow = COLORS.accent;
        targetSpeed = reducedMotion ? 0.02 : 0.25;
        targetScale = 0.92;
        targetIntensity = 0.4;
        targetParticleCount = 0.5;
        break;
      case 'ERROR':
        targetPrimary = COLORS.error;
        targetSecondary = COLORS.error;
        targetAccent = COLORS.error;
        targetGlow = COLORS.error;
        targetSpeed = reducedMotion ? 0.02 : 0.15;
        targetScale = 0.88;
        targetIntensity = 0.3;
        targetParticleCount = 0.3;
        break;
    }

    const duration = reducedMotion ? 0.3 : 1.5;

    if (groupRef.current) {
      gsap.to(groupRef.current.scale, {
        x: targetScale, y: targetScale, z: targetScale,
        duration, ease: 'power2.out'
      });
    }

    gsap.to(colors.primary, {
      r: targetPrimary.r, g: targetPrimary.g, b: targetPrimary.b,
      duration
    });
    gsap.to(colors.secondary, {
      r: targetSecondary.r, g: targetSecondary.g, b: targetSecondary.b,
      duration
    });
    gsap.to(colors.accent, {
      r: targetAccent.r, g: targetAccent.g, b: targetAccent.b,
      duration
    });
    gsap.to(colors.glow, {
      r: targetGlow.r, g: targetGlow.g, b: targetGlow.b,
      duration
    });

    gsap.to(animParams, {
      speed: targetSpeed,
      intensity: targetIntensity,
      particleCount: targetParticleCount,
      duration
    });
  }, [status, reducedMotion]);

  // Gentle breathing and floating for the entire core + differential layer parallax
  useFrame((state, delta) => {
    if (groupRef.current && !reducedMotion) {
      const time = state.clock.elapsedTime;
      groupRef.current.position.y = Math.sin(time * 0.4) * 0.04;
      groupRef.current.position.x = Math.sin(time * 0.25) * 0.02;
    }

    if (!reducedMotion) {
      const targetPx = pointerRef?.current?.x || 0;
      const targetPy = pointerRef?.current?.y || 0;
      const lerpFactor = Math.min(delta * 5.0, 0.15);

      smoothPointerRef.current.x = THREE.MathUtils.lerp(
        smoothPointerRef.current.x,
        targetPx,
        lerpFactor
      );
      smoothPointerRef.current.y = THREE.MathUtils.lerp(
        smoothPointerRef.current.y,
        targetPy,
        lerpFactor
      );

      const px = smoothPointerRef.current.x;
      const py = smoothPointerRef.current.y;

      // Differential depth layer parallax shifts (Background = strongest, Nucleus = minimal)
      if (bgParticlesGroupRef.current) {
        bgParticlesGroupRef.current.position.x = px * 0.65;
        bgParticlesGroupRef.current.position.y = py * 0.45;
      }
      if (atmosphereGroupRef.current) {
        atmosphereGroupRef.current.position.x = px * 0.45;
        atmosphereGroupRef.current.position.y = py * 0.30;
      }
      if (topologyGroupRef.current) {
        topologyGroupRef.current.position.x = px * 0.28;
        topologyGroupRef.current.position.y = py * 0.20;
      }
      if (orbitalGroupRef.current) {
        orbitalGroupRef.current.position.x = px * 0.16;
        orbitalGroupRef.current.position.y = py * 0.10;
      }
      if (nodesGroupRef.current) {
        nodesGroupRef.current.position.x = px * 0.14;
        nodesGroupRef.current.position.y = py * 0.08;
      }
      if (innerGroupRef.current) {
        innerGroupRef.current.position.x = px * 0.08;
        innerGroupRef.current.position.y = py * 0.05;
      }
      if (nucleusGroupRef.current) {
        nucleusGroupRef.current.position.x = px * 0.02;
        nucleusGroupRef.current.position.y = py * 0.01;
      }
    }
  });

  // SCENE_SCALE: balanced medium framing (~60% height fill of available container).
  // At 0.80: outer atmosphere r=6.5 → 5.2, orbital ring r=4.8 → 3.84,
  // radial platform outer arc r=6.7 → 5.36, topology outer shell r=4.4 → 3.52.
  // Perfectly balanced with camera at z=10.0, fov=48 — zero clipping, ideal breathing room.
  const SCENE_SCALE = 0.80;

  return (
    <group scale={SCENE_SCALE}>
    <group ref={groupRef}>
      {/* Lighting setup */}

      {/* Ambient light — dark blue tint for space feel */}
      <ambientLight intensity={0.4} color="#1a2a4a" />

      {/* Key light — main illumination from upper-right */}
      <directionalLight
        position={[6, 8, 5]}
        intensity={2.2}
        color={colors.primary}
      />

      {/* Fill light — left side, accent color */}
      <directionalLight
        position={[-5, 2, 4]}
        intensity={0.8}
        color={colors.accent}
      />

      {/* Rim light — from below-back for edge definition */}
      <directionalLight
        position={[0, -6, -4]}
        intensity={0.5}
        color={colors.glow}
      />

      {/* Top-down fill — reveals the radial platform */}
      <directionalLight
        position={[0, 12, 0]}
        intensity={0.4}
        color="#0a1a3a"
      />

      {/* Nucleus point light — core glow origin */}
      <pointLight
        position={[0, 0, 0]}
        intensity={3.0}
        color={colors.glow}
        distance={8}
        decay={2}
      />

      {/* Secondary fill point — slightly offset */}
      <pointLight
        position={[1.5, 1.0, 2.0]}
        intensity={0.6}
        color={colors.primary}
        distance={6}
        decay={2}
      />

      {/* 2. Core Sphere Group (Floating) */}
      <group>
        {/* Nucleus - central luminous core */}
        <group ref={nucleusGroupRef}>
          <Nucleus
            color={colors.primary}
            stateIntensity={effectiveIntensity}
          />
        </group>

        {/* Inner volumetric energy field */}
        <group ref={innerGroupRef}>
          <InnerField
            color={colors.primary}
            stateIntensity={effectiveIntensity}
          />
        </group>

        {/* Dense computational topology shell */}
        <group ref={topologyGroupRef}>
          <TopologySphere
            color={colors.primary}
            stateIntensity={effectiveIntensity}
          />
        </group>

        {/* Orbital System - Multiple orbital planes */}
        <group ref={orbitalGroupRef}>
          <OrbitalSystem
            primaryColor={colors.primary}
            accentColor={colors.accent}
            speedMultiplier={animParams.speed}
            stateIntensity={effectiveIntensity}
          />
        </group>

        {/* Intelligence Nodes - Hierarchical node system */}
        <group ref={nodesGroupRef}>
          <IntelligenceNodes
            color={colors.primary}
            accentColor={colors.accent}
            speedMultiplier={animParams.speed}
            stateIntensity={effectiveIntensity}
          />
        </group>

        {/* Particle Field - Multi-layer ambient particles */}
        <group ref={bgParticlesGroupRef}>
          <ParticleField
            color={colors.primary}
            accentColor={colors.accent}
            count={Math.floor(1800 * animParams.particleCount)}
            speedMultiplier={animParams.speed}
            stateIntensity={effectiveIntensity}
          />
        </group>

        {/* Atmosphere - Subtle depth fog/glow layer */}
        <group ref={atmosphereGroupRef}>
          <Atmosphere
            color={colors.glow}
            intensity={effectiveIntensity}
          />
        </group>
      </group>
    </group>
    </group>
  );
}

// Atmosphere component - subtle volumetric depth layer
function Atmosphere({ color, intensity }: { color: THREE.Color, intensity: number }) {
  const ref = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    const time = state.clock.elapsedTime;
    if (ref.current) {
      ref.current.rotation.y = time * 0.003;
      ref.current.rotation.x = time * 0.0015;
      const pulse = 1 + Math.sin(time * 0.5) * 0.02 * intensity;
      ref.current.scale.setScalar(pulse);
      (ref.current.material as THREE.MeshBasicMaterial).opacity = 0.015 * intensity * (0.7 + Math.sin(time * 0.7) * 0.3);
    }
  });

  return (
    <>
      {/* Outer atmosphere sphere - very subtle */}
      <Sphere
        ref={ref}
        args={[6.5, 32, 32]}
      >
        <meshBasicMaterial
          color={color}
          transparent
          opacity={0.012}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
          side={THREE.BackSide}
        />
      </Sphere>

      {/* Mid atmosphere layer */}
      <Sphere args={[5.2, 24, 24]}>
        <meshBasicMaterial
          color={color}
          transparent
          opacity={0.008}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
          side={THREE.BackSide}
        />
      </Sphere>

      {/* Inner atmosphere - near topology */}
      <Sphere args={[4.0, 16, 16]}>
        <meshBasicMaterial
          color={color}
          transparent
          opacity={0.005}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
          side={THREE.BackSide}
        />
      </Sphere>
    </>
  );
}