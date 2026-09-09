import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sphere, Points, PointMaterial } from '@react-three/drei';
import * as THREE from 'three';

export function InnerField({ color, scale = 1, stateIntensity = 1 }: { color: THREE.Color, scale?: number, stateIntensity?: number }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const pointsRef = useRef<THREE.Points>(null);
  const innerGlowRef = useRef<THREE.Mesh>(null);

  // Volumetric noise positions for the inner field
  const particlePositions = useMemo(() => {
    const count = 800;
    const positions = new Float32Array(count * 3);
    const sizes = new Float32Array(count);
    const alphas = new Float32Array(count);

    for (let i = 0; i < count; i++) {
      // Spherical distribution with density bias toward center
      const radius = 1.2 + Math.pow(Math.random(), 1.5) * 1.8;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);

      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = radius * Math.cos(phi);

      // Size varies - smaller near center, larger at edges for depth perception
      sizes[i] = 0.015 + Math.random() * 0.025;
      // Alpha varies - more opaque near center
      alphas[i] = 0.3 + (1 - radius / 3) * 0.4;
    }
    return { positions, sizes, alphas };
  }, []);

  useFrame((state) => {
    const time = state.clock.elapsedTime;
    const intensity = stateIntensity;

    if (meshRef.current) {
      meshRef.current.rotation.x = time * 0.015;
      meshRef.current.rotation.y = time * 0.02;
      meshRef.current.rotation.z = time * 0.008;
    }
    if (innerGlowRef.current) {
      innerGlowRef.current.rotation.y = -time * 0.01;
      innerGlowRef.current.rotation.x = time * 0.005;
      const pulse = 1 + Math.sin(time * 0.8) * 0.03 * intensity;
      innerGlowRef.current.scale.setScalar(pulse);
      (innerGlowRef.current.material as THREE.MeshBasicMaterial).opacity =
        0.05 + Math.sin(time * 0.8) * 0.02 * intensity;
    }
    if (pointsRef.current) {
      // Simple rotation only — no per-vertex mutation
      pointsRef.current.rotation.y += 0.0003 * intensity;
      pointsRef.current.rotation.x += 0.00015 * intensity;
    }
  });

  return (
    <group scale={scale}>
      {/* Layer 1: Volumetric outer shell - physical material with transmission */}
      <Sphere ref={meshRef} args={[2.8, 64, 64]}>
        <meshPhysicalMaterial
          color={color}
          transparent
          opacity={0.04}
          metalness={0.1}
          roughness={0.9}
          transmission={0.95}
          thickness={0.5}
          ior={1.15}
          side={THREE.BackSide}
          depthWrite={false}
        />
      </Sphere>

      {/* Layer 2: Inner volumetric glow - additive blending */}
      <Sphere ref={innerGlowRef} args={[2.9, 48, 48]}>
        <meshBasicMaterial
          color={color}
          transparent
          opacity={0.04}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
          side={THREE.BackSide}
        />
      </Sphere>

      {/* Layer 3: Edge highlight - thin wireframe at boundary */}
      <Sphere args={[3.05, 32, 32]}>
        <meshBasicMaterial
          color={color}
          transparent
          opacity={0.06}
          wireframe
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </Sphere>

      {/* Layer 4: Volumetric particle field within the inner field */}
      <Points
        ref={pointsRef}
        positions={particlePositions.positions}
        stride={3}
        frustumCulled={false}
      >
        <PointMaterial
          transparent
          color={color}
          size={0.018}
          sizeAttenuation={true}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
          opacity={0.35}
          vertexColors={false}
        />
      </Points>

      {/* Layer 5: Secondary particle layer - smaller, sparser, different depth */}
      <Points
        positions={particlePositions.positions}
        stride={3}
        frustumCulled={false}
        rotation={[0.3, 0.7, 0.2]}
        scale={1.15}
      >
        <PointMaterial
          transparent
          color={color}
          size={0.012}
          sizeAttenuation={true}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
          opacity={0.15}
        />
      </Points>
    </group>
  );
}