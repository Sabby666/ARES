import { useRef, useMemo, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Ring, Circle, Line } from '@react-three/drei';
import * as THREE from 'three';

interface RingData {
  inner: number;
  outer: number;
  segments: number;
  thetaStart: number;
  thetaLength: number;
  opacity: number;
  color: THREE.Color;
  rotationSpeed: number;
  isSegmented: boolean;
}

interface TickData {
  angle: number;
  innerR: number;
  outerR: number;
  opacity: number;
  color: THREE.Color;
  length: number;
}

interface GridLineData {
  angle?: number;
  innerR?: number;
  outerR?: number;
  opacity: number;
  color: THREE.Color;
  isMajor?: boolean;
  radius?: number;
  isCircular?: boolean;
}

export function RadialPlatform({ color, accentColor, stateIntensity = 1 }: { color: THREE.Color, accentColor?: THREE.Color, stateIntensity?: number }) {
  const groupRef = useRef<THREE.Group>(null);
  const innerRingsRef = useRef<THREE.Group>(null);
  const outerRingsRef = useRef<THREE.Group>(null);
  const tickMarksRef = useRef<THREE.Group>(null);
  const gridRef = useRef<THREE.Group>(null);
  const glowRef = useRef<THREE.Mesh>(null);
  const [intensity, setIntensity] = useState(stateIntensity);

  const accent = accentColor || new THREE.Color('#8B5CF6');
  const cyan = new THREE.Color('#00ffff');

  // Keep intensity in sync with prop
  useFrame(() => {
    setIntensity(stateIntensity);
  });

  // Precompute radial geometry data
  const radialData = useMemo(() => {
    const rings: RingData[] = [];
    const ticks: TickData[] = [];
    const gridLines: GridLineData[] = [];
    const segments = 64;
    const tickSegments = 72;

    // Concentric rings data
    const ringRadii = [0.4, 0.8, 1.3, 1.9, 2.6, 3.4, 4.3, 5.3];
    ringRadii.forEach((r, idx) => {
      rings.push({
        inner: r,
        outer: r + 0.03,
        segments: 64,
        thetaStart: 0,
        thetaLength: Math.PI * 2,
        opacity: 0.04 + idx * 0.02,
        color: idx % 2 === 0 ? color : accent,
        rotationSpeed: (idx % 2 === 0 ? 0.02 : -0.015) * (1 + idx * 0.1),
        isSegmented: false
      });
    });

    // Segmented arcs - outer rings
    const arcRadii = [5.8, 6.2, 6.7];
    arcRadii.forEach((r, idx) => {
      const arcCount = 3 + idx;
      for (let a = 0; a < arcCount; a++) {
        rings.push({
          inner: r,
          outer: r + 0.025,
          segments: 48,
          thetaStart: (a / arcCount) * Math.PI * 2 + idx * 0.5,
          thetaLength: Math.PI * (0.3 + idx * 0.15),
          opacity: 0.15 + idx * 0.05,
          color: idx === 0 ? accent : idx === 1 ? color : cyan,
          rotationSpeed: (idx % 2 === 0 ? 0.01 : -0.008) * (1 + idx * 0.05),
          isSegmented: true
        });
      }
    });

    // Radial tick marks
    for (let i = 0; i < tickSegments; i++) {
      const angle = (i / tickSegments) * Math.PI * 2;
      const radius = 4.0 + Math.random() * 2.5;
      const innerR = radius;
      const outerR = radius + 0.15 + Math.random() * 0.2;
      ticks.push({
        angle,
        innerR,
        outerR,
        opacity: 0.08 + Math.random() * 0.12,
        color: Math.random() > 0.5 ? color : accent,
        length: outerR - innerR
      });
    }

    // Radial grid lines (spokes)
    const spokeCount = 12;
    for (let i = 0; i < spokeCount; i++) {
      const angle = (i / spokeCount) * Math.PI * 2;
      gridLines.push({
        angle,
        innerR: 0.5,
        outerR: 6.5,
        opacity: 0.02,
        color: color,
        isMajor: i % 3 === 0,
        isCircular: false
      });
    }

    // Circular grid lines
    const circularRadii = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0];
    circularRadii.forEach(r => {
      gridLines.push({
        radius: r,
        opacity: 0.015,
        color: color,
        isCircular: true
      });
    });

    return { rings, ticks, gridLines };
  }, [color, accent]);

  useFrame((state, delta) => {
    const time = state.clock.elapsedTime;

    if (groupRef.current) {
      groupRef.current.rotation.z += delta * 0.008 * intensity;
    }
    if (innerRingsRef.current) {
      innerRingsRef.current.rotation.z += delta * 0.012 * intensity;
    }
    if (outerRingsRef.current) {
      outerRingsRef.current.rotation.z -= delta * 0.006 * intensity;
    }
    if (tickMarksRef.current) {
      tickMarksRef.current.rotation.z += delta * 0.003 * intensity;
    }
    if (gridRef.current) {
      gridRef.current.rotation.z -= delta * 0.002 * intensity;
    }
    if (glowRef.current) {
      const pulse = 1 + Math.sin(time * 0.6) * 0.05 * intensity;
      glowRef.current.scale.setScalar(pulse);
      (glowRef.current.material as THREE.MeshBasicMaterial).opacity = 0.015 + Math.sin(time * 0.6) * 0.008 * intensity;
    }
  });

  return (
    <group position={[0, -2.8, 0]} rotation={[-Math.PI / 2, 0, 0]} ref={groupRef}>
      {/* BASE GLOW - Large radial gradient beneath everything */}
      <mesh ref={glowRef} position={[0, 0, -0.2]}>
        <circleGeometry args={[8, 64]} />
        <meshBasicMaterial
          color={color}
          transparent
          opacity={0.02}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* SECONDARY GLOW - Tighter, brighter */}
      <mesh position={[0, 0, -0.15]}>
        <circleGeometry args={[5, 64]} />
        <meshBasicMaterial
          color={color}
          transparent
          opacity={0.03}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* INNER CONCENTRIC RINGS */}
      <group ref={innerRingsRef}>
        {radialData.rings
          .filter(r => !r.isSegmented && r.inner <= 3.5)
          .map((ring, idx) => (
            <Ring
              key={`ring-inner-${idx}`}
              args={[ring.inner, ring.outer, ring.segments, 1, ring.thetaStart, ring.thetaLength]}
              material-color={ring.color}
              material-transparent
              material-opacity={ring.opacity * intensity}
              material-blending={THREE.AdditiveBlending}
              material-side={THREE.DoubleSide}
              material-depthWrite={false}
            />
          ))}
      </group>

      {/* OUTER CONCENTRIC RINGS */}
      <group ref={outerRingsRef}>
        {radialData.rings
          .filter(r => !r.isSegmented && r.inner > 3.5)
          .map((ring, idx) => (
            <Ring
              key={`ring-outer-${idx}`}
              args={[ring.inner, ring.outer, ring.segments, 1, ring.thetaStart, ring.thetaLength]}
              material-color={ring.color}
              material-transparent
              material-opacity={ring.opacity * intensity}
              material-blending={THREE.AdditiveBlending}
              material-side={THREE.DoubleSide}
              material-depthWrite={false}
            />
          ))}
      </group>

      {/* SEGMENTED ARCS - Asymmetric arcs for computational feel */}
      <group rotation={[-0.05, 0.1, 0]}>
        {radialData.rings
          .filter(r => r.isSegmented)
          .map((ring, idx) => (
            <Ring
              key={`arc-${idx}`}
              args={[ring.inner, ring.outer, ring.segments, 1, ring.thetaStart, ring.thetaLength]}
              material-color={ring.color}
              material-transparent
              material-opacity={ring.opacity * intensity}
              material-blending={THREE.AdditiveBlending}
              material-side={THREE.DoubleSide}
              material-depthWrite={false}
            />
          ))}
      </group>

      {/* RADIAL TICK MARKS */}
      <group ref={tickMarksRef}>
        {radialData.ticks.map((tick, idx) => (
          <Line
            key={`tick-${idx}`}
            points={[
              new THREE.Vector3(Math.cos(tick.angle) * tick.innerR, Math.sin(tick.angle) * tick.innerR, 0),
              new THREE.Vector3(Math.cos(tick.angle) * tick.outerR, Math.sin(tick.angle) * tick.outerR, 0)
            ]}
            color={tick.color}
            transparent
            opacity={tick.opacity * intensity}
            lineWidth={0.5}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        ))}

        {/* Major cardinal ticks - longer and brighter */}
        {[0, Math.PI/2, Math.PI, 3*Math.PI/2].map((angle, idx) => (
          <Line
            key={`tick-major-${idx}`}
            points={[
              new THREE.Vector3(Math.cos(angle) * 3.8, Math.sin(angle) * 3.8, 0),
              new THREE.Vector3(Math.cos(angle) * 6.8, Math.sin(angle) * 6.8, 0)
            ]}
            color={accent}
            transparent
            opacity={0.15 * intensity}
            lineWidth={1}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        ))}
      </group>

      {/* POLAR GRID - Spokes and circular lines */}
      <group ref={gridRef}>
        {/* Radial spokes */}
        {radialData.gridLines.filter((l): l is GridLineData & { isCircular: false } => !l.isCircular).map((line, idx) => (
          <Line
            key={`spoke-${idx}`}
            points={[
              new THREE.Vector3(Math.cos(line.angle!) * line.innerR!, Math.sin(line.angle!) * line.innerR!, 0.001),
              new THREE.Vector3(Math.cos(line.angle!) * line.outerR!, Math.sin(line.angle!) * line.outerR!, 0.001)
            ]}
            color={line.color}
            transparent
            opacity={line.opacity * (line.isMajor ? 2 : 1) * intensity}
            lineWidth={line.isMajor ? 0.6 : 0.3}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        ))}

        {/* Circular grid lines */}
        {radialData.gridLines.filter((l): l is GridLineData & { isCircular: true; radius: number } => l.isCircular === true).map((line, idx) => (
          <Ring
            key={`grid-circle-${idx}`}
            args={[line.radius!, line.radius! + 0.01, 64, 1, 0, Math.PI * 2]}
            material-color={line.color}
            material-transparent
            material-opacity={line.opacity * intensity}
            material-blending={THREE.AdditiveBlending}
            material-side={THREE.DoubleSide}
            material-depthWrite={false}
          />
        ))}
      </group>

      {/* TECHNICAL MARKERS - Corner brackets and reference marks */}
      <group>
        {([0, Math.PI/2, Math.PI, 3*Math.PI/2] as const).map((angle, idx) => (
          <group
            key={`bracket-${idx}`}
            rotation={[0, 0, angle]}
            position={[5.5, 0, 0.01]}
          >
            {/* L-bracket markers */}
            <Line
              points={[
                new THREE.Vector3(0, 0, 0),
                new THREE.Vector3(0.5, 0, 0),
                new THREE.Vector3(0.5, 0.5, 0)
              ]}
              color={accent}
              transparent
              opacity={0.12 * intensity}
              lineWidth={1}
              blending={THREE.AdditiveBlending}
              depthWrite={false}
            />
            <Line
              points={[
                new THREE.Vector3(0, 0, 0),
                new THREE.Vector3(0, 0.5, 0),
                new THREE.Vector3(-0.5, 0.5, 0)
              ]}
              color={accent}
              transparent
              opacity={0.12 * intensity}
              lineWidth={1}
              blending={THREE.AdditiveBlending}
              depthWrite={false}
            />
          </group>
        ))}

        {/* Distance markers - small circles at cardinal radii */}
        {[2.0, 3.0, 4.0, 5.0, 6.0].map((r, idx) => (
          <Ring
            key={`dist-marker-${idx}`}
            args={[r, r + 0.02, 32, 1, 0, Math.PI * 2]}
            material-color={idx % 2 === 0 ? color : accent}
            material-transparent
            material-opacity={0.05 * intensity}
            material-blending={THREE.AdditiveBlending}
            material-side={THREE.DoubleSide}
            material-depthWrite={false}
          />
        ))}
      </group>

      {/* CENTRAL ANCHOR - Small detailed center piece */}
      <group position={[0, 0, 0.05]}>
        <Ring args={[0.15, 0.25, 32]} material-color={color} material-transparent material-opacity={0.2 * intensity} material-blending={THREE.AdditiveBlending} material-side={THREE.DoubleSide} material-depthWrite={false} />
        <Ring args={[0.25, 0.28, 32]} material-color={accent} material-transparent material-opacity={0.15 * intensity} material-blending={THREE.AdditiveBlending} material-side={THREE.DoubleSide} material-depthWrite={false} />
        <Circle args={[0.15, 32]} rotation={[0, 0, 0]} >
          <meshBasicMaterial color={color} transparent opacity={0.1 * intensity} blending={THREE.AdditiveBlending} depthWrite={false} side={THREE.DoubleSide} />
        </Circle>
      </group>
    </group>
  );
}