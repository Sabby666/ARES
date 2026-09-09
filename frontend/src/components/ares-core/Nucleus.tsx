import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sphere, Icosahedron, Billboard, Plane } from '@react-three/drei';
import * as THREE from 'three';

// Canvas-based "A" texture — no font file loading, no Suspense issues
function createATexture(): THREE.CanvasTexture {
  const size = 256;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d')!;

  ctx.clearRect(0, 0, size, size);

  // Soft radial glow behind the letter
  const gradient = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  gradient.addColorStop(0, 'rgba(120, 190, 255, 0.22)');
  gradient.addColorStop(0.5, 'rgba(80, 140, 255, 0.10)');
  gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, size, size);

  // Draw "A" glyph — white, semi-transparent
  ctx.fillStyle = 'rgba(230, 245, 255, 0.96)';
  ctx.font = `bold ${Math.floor(size * 0.60)}px "Outfit", "Inter", Arial, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('A', size / 2, size / 2 + size * 0.03);

  return new THREE.CanvasTexture(canvas);
}

export function Nucleus({
  color,
  scale = 1,
  stateIntensity = 1,
}: {
  color: THREE.Color;
  scale?: number;
  stateIntensity?: number;
}) {
  const innerRef = useRef<THREE.Mesh>(null);
  const outerRef = useRef<THREE.Mesh>(null);
  const coreGlowRef = useRef<THREE.Mesh>(null);
  const energyPulseRef = useRef<THREE.Mesh>(null);
  const coronaRef = useRef<THREE.Mesh>(null);

  // Canvas texture for "A" mark — no network fetch, no Suspense
  const aTexture = useMemo(() => createATexture(), []);

  useFrame((state) => {
    const time = state.clock.elapsedTime;
    const intensity = stateIntensity;

    if (innerRef.current) {
      innerRef.current.rotation.y = time * 0.12;
      innerRef.current.rotation.x = time * 0.07;
      const breath = 1 + Math.sin(time * 1.1) * 0.025 * intensity;
      innerRef.current.scale.setScalar(breath);
    }
    if (outerRef.current) {
      outerRef.current.rotation.y = -time * 0.09;
      outerRef.current.rotation.x = time * 0.05;
      outerRef.current.rotation.z = time * 0.03;
    }
    if (coreGlowRef.current) {
      coreGlowRef.current.rotation.y = -time * 0.04;
      const pulse = 1 + Math.sin(time * 1.8) * 0.06 * intensity;
      coreGlowRef.current.scale.setScalar(pulse);
      (coreGlowRef.current.material as THREE.MeshBasicMaterial).opacity =
        0.18 + Math.sin(time * 1.8) * 0.07 * intensity;
    }
    if (energyPulseRef.current) {
      energyPulseRef.current.rotation.y = time * 0.07;
      energyPulseRef.current.rotation.x = time * 0.03;
      const pulseScale = 1 + Math.sin(time * 1.4 + 1.2) * 0.1 * intensity;
      energyPulseRef.current.scale.setScalar(pulseScale);
      (energyPulseRef.current.material as THREE.MeshBasicMaterial).opacity =
        0.07 + Math.sin(time * 1.4 + 1.2) * 0.03 * intensity;
    }
    if (coronaRef.current) {
      coronaRef.current.rotation.y = -time * 0.025;
      const coronaPulse = 1 + Math.sin(time * 0.6) * 0.04;
      coronaRef.current.scale.setScalar(coronaPulse);
    }
  });

  return (
    <group scale={scale}>
      {/* Layer 1: Dense solid core sphere */}
      <Sphere ref={innerRef} args={[0.48, 48, 48]}>
        <meshBasicMaterial color={color} />
      </Sphere>

      {/* Layer 2: Bright white highlight — tiny inner core point */}
      <Sphere args={[0.18, 16, 16]}>
        <meshBasicMaterial
          color={new THREE.Color('#ffffff')}
          transparent
          opacity={0.92}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </Sphere>

      {/* Layer 3: "A" identity mark — Billboard keeps it facing camera */}
      <Billboard follow lockX={false} lockY={false} lockZ={false}>
        <Plane args={[0.72, 0.72]}>
          <meshBasicMaterial
            map={aTexture}
            transparent
            opacity={0.96}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
            side={THREE.DoubleSide}
          />
        </Plane>
      </Billboard>

      {/* Layer 4: Inner energy shell — wireframe */}
      <Sphere ref={outerRef} args={[0.68, 48, 48]}>
        <meshBasicMaterial
          color={color}
          transparent
          opacity={0.30}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
          wireframe
        />
      </Sphere>

      {/* Layer 5: Core glow — smooth additive bloom */}
      <Sphere ref={coreGlowRef} args={[0.82, 32, 32]}>
        <meshBasicMaterial
          color={color}
          transparent
          opacity={0.15}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </Sphere>

      {/* Layer 6: Energy pulse — icosahedron wireframe */}
      <Icosahedron ref={energyPulseRef} args={[0.96, 1]}>
        <meshBasicMaterial
          color={color}
          transparent
          opacity={0.06}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
          wireframe
        />
      </Icosahedron>

      {/* Layer 7: Outer corona — wide glow */}
      <Sphere ref={coronaRef} args={[1.18, 24, 24]}>
        <meshBasicMaterial
          color={color}
          transparent
          opacity={0.04}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </Sphere>
    </group>
  );
}
