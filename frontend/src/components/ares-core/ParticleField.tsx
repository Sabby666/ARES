import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Points, PointMaterial } from '@react-three/drei';
import * as THREE from 'three';

interface ParticleLayer {
  count: number;
  positions: Float32Array;
  sizes: Float32Array;
  alphas: Float32Array;
  speeds: Float32Array;
  phases: Float32Array;
  color: THREE.Color;
  baseRadius: number;
  radiusVariance: number;
  sizeRange: [number, number];
  opacityRange: [number, number];
  rotationSpeed: [number, number, number];
  driftSpeed: number;
}

export function ParticleField({
  color,
  accentColor,
  count = 2000,
  speedMultiplier = 1,
  stateIntensity = 1
}: {
  color: THREE.Color,
  accentColor?: THREE.Color,
  count?: number,
  speedMultiplier?: number,
  stateIntensity?: number
}) {
  const layersRef = useRef<(THREE.Points | null)[]>([]);

  // Create multiple particle layers for depth
  const layers = useMemo((): ParticleLayer[] => {
    const accent = accentColor || new THREE.Color('#8B5CF6');
    const cyan = new THREE.Color('#00ffff');
    const layers: ParticleLayer[] = [];

    // LAYER 1: Core proximity - dense, slow, blue-white
    {
      const layerCount = Math.floor(count * 0.25);
      const positions = new Float32Array(layerCount * 3);
      const sizes = new Float32Array(layerCount);
      const alphas = new Float32Array(layerCount);
      const speeds = new Float32Array(layerCount);
      const phases = new Float32Array(layerCount);

      for (let i = 0; i < layerCount; i++) {
        const radius = 0.8 + Math.pow(Math.random(), 1.2) * 1.5;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);

        positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
        positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
        positions[i * 3 + 2] = radius * Math.cos(phi);

        sizes[i] = 0.02 + Math.random() * 0.025;
        alphas[i] = 0.4 + Math.random() * 0.3;
        speeds[i] = 0.02 + Math.random() * 0.03;
        phases[i] = Math.random() * Math.PI * 2;
      }

      layers.push({
        count: layerCount,
        positions, sizes, alphas, speeds, phases,
        color: color.clone(),
        baseRadius: 1.5,
        radiusVariance: 1.5,
        sizeRange: [0.02, 0.045],
        opacityRange: [0.4, 0.7],
        rotationSpeed: [0.01, 0.005, 0.002],
        driftSpeed: 0.01
      });
    }

    // LAYER 2: Mid field - computational particles, varied sizes
    {
      const layerCount = Math.floor(count * 0.35);
      const positions = new Float32Array(layerCount * 3);
      const sizes = new Float32Array(layerCount);
      const alphas = new Float32Array(layerCount);
      const speeds = new Float32Array(layerCount);
      const phases = new Float32Array(layerCount);

      for (let i = 0; i < layerCount; i++) {
        const radius = 2.0 + Math.pow(Math.random(), 1.5) * 2.0;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);

        positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
        positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
        positions[i * 3 + 2] = radius * Math.cos(phi);

        sizes[i] = 0.015 + Math.random() * 0.02;
        alphas[i] = 0.25 + Math.random() * 0.25;
        speeds[i] = 0.03 + Math.random() * 0.05;
        phases[i] = Math.random() * Math.PI * 2;
      }

      layers.push({
        count: layerCount,
        positions, sizes, alphas, speeds, phases,
        color: accent,
        baseRadius: 3.0,
        radiusVariance: 2.0,
        sizeRange: [0.015, 0.035],
        opacityRange: [0.25, 0.5],
        rotationSpeed: [-0.015, -0.008, -0.003],
        driftSpeed: 0.015
      });
    }

    // LAYER 3: Outer field - sparse, cyan, fast
    {
      const layerCount = Math.floor(count * 0.2);
      const positions = new Float32Array(layerCount * 3);
      const sizes = new Float32Array(layerCount);
      const alphas = new Float32Array(layerCount);
      const speeds = new Float32Array(layerCount);
      const phases = new Float32Array(layerCount);

      for (let i = 0; i < layerCount; i++) {
        const radius = 3.5 + Math.pow(Math.random(), 1.8) * 2.5;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);

        positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
        positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
        positions[i * 3 + 2] = radius * Math.cos(phi);

        sizes[i] = 0.01 + Math.random() * 0.015;
        alphas[i] = 0.15 + Math.random() * 0.2;
        speeds[i] = 0.05 + Math.random() * 0.08;
        phases[i] = Math.random() * Math.PI * 2;
      }

      layers.push({
        count: layerCount,
        positions, sizes, alphas, speeds, phases,
        color: cyan,
        baseRadius: 5.0,
        radiusVariance: 2.5,
        sizeRange: [0.01, 0.025],
        opacityRange: [0.15, 0.35],
        rotationSpeed: [0.02, 0.01, 0.005],
        driftSpeed: 0.02
      });
    }

    // LAYER 4: Energy streams - directed flow particles
    {
      const layerCount = Math.floor(count * 0.1);
      const positions = new Float32Array(layerCount * 3);
      const sizes = new Float32Array(layerCount);
      const alphas = new Float32Array(layerCount);
      const speeds = new Float32Array(layerCount);
      const phases = new Float32Array(layerCount);
      const streamIds = new Float32Array(layerCount);

      // Create 8 stream paths
      const streamCount = 8;
      const streamDirs: THREE.Vector3[] = [];
      for (let s = 0; s < streamCount; s++) {
        const phi = Math.acos(-1 + (2 * s + 1) / streamCount);
        const theta = Math.sqrt(streamCount * Math.PI) * phi;
        streamDirs.push(new THREE.Vector3(
          Math.cos(theta) * Math.sin(phi),
          Math.sin(theta) * Math.sin(phi),
          Math.cos(phi)
        ));
      }

      for (let i = 0; i < layerCount; i++) {
        const streamId = i % streamCount;
        streamIds[i] = streamId;
        const dir = streamDirs[streamId];

        // Particles distributed along stream path
        const t = Math.random();
        const radius = 1.5 + t * 3.5;

        positions[i * 3] = dir.x * radius + (Math.random() - 0.5) * 0.3;
        positions[i * 3 + 1] = dir.y * radius + (Math.random() - 0.5) * 0.3;
        positions[i * 3 + 2] = dir.z * radius + (Math.random() - 0.5) * 0.3;

        sizes[i] = 0.025 + Math.random() * 0.02;
        alphas[i] = 0.5 + Math.random() * 0.3;
        speeds[i] = 0.08 + Math.random() * 0.12;
        phases[i] = Math.random() * Math.PI * 2;
      }

      layers.push({
        count: layerCount,
        positions, sizes, alphas, speeds, phases,
        color: new THREE.Color('#ffffff'),
        baseRadius: 3.0,
        radiusVariance: 2.0,
        sizeRange: [0.025, 0.045],
        opacityRange: [0.5, 0.8],
        rotationSpeed: [0, 0, 0],
        driftSpeed: 0.05
      });
    }

    // LAYER 5: Ambient sparkles - very sparse, bright, pulsing
    {
      const layerCount = Math.floor(count * 0.1);
      const positions = new Float32Array(layerCount * 3);
      const sizes = new Float32Array(layerCount);
      const alphas = new Float32Array(layerCount);
      const speeds = new Float32Array(layerCount);
      const phases = new Float32Array(layerCount);

      for (let i = 0; i < layerCount; i++) {
        const radius = 1.0 + Math.random() * 5.0;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);

        positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
        positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
        positions[i * 3 + 2] = radius * Math.cos(phi);

        sizes[i] = 0.03 + Math.random() * 0.04;
        alphas[i] = 0.6 + Math.random() * 0.3;
        speeds[i] = 0.01 + Math.random() * 0.02;
        phases[i] = Math.random() * Math.PI * 2;
      }

      layers.push({
        count: layerCount,
        positions, sizes, alphas, speeds, phases,
        color: new THREE.Color('#ffffff'),
        baseRadius: 3.0,
        radiusVariance: 3.0,
        sizeRange: [0.03, 0.07],
        opacityRange: [0.6, 0.9],
        rotationSpeed: [0.005, 0.003, 0.001],
        driftSpeed: 0.005
      });
    }

    return layers;
  }, [count, color, accentColor]);

  useFrame((state, delta) => {
    const intensity = stateIntensity;
    const baseSpeed = delta * speedMultiplier;

    // Only rotate the layer groups — no per-particle CPU mutation
    // This is dramatically cheaper: O(layers) vs O(particles) per frame
    layersRef.current.forEach((points, layerIdx) => {
      if (!points) return;
      const layer = layers[layerIdx];
      if (!layer) return;

      points.rotation.x += baseSpeed * layer.rotationSpeed[0] * intensity;
      points.rotation.y += baseSpeed * layer.rotationSpeed[1] * intensity;
      points.rotation.z += baseSpeed * layer.rotationSpeed[2] * intensity;
    });
  });

  return (
    <group>
      {layers.map((layer, idx) => (
        <Points
          key={`particles-${idx}`}
          ref={(el) => { layersRef.current[idx] = el; }}
          positions={layer.positions}
          stride={3}
          frustumCulled={false}
        >
          <PointMaterial
            transparent
            color={layer.color}
            size={layer.sizeRange[0]}
            sizeAttenuation={true}
            depthWrite={false}
            blending={idx === 3 ? THREE.AdditiveBlending : THREE.AdditiveBlending}
            opacity={layer.opacityRange[0]}
            vertexColors={false}
            // Custom attributes for per-particle animation
            onBeforeCompile={(shader) => {
              shader.uniforms.uTime = { value: 0 };
              shader.vertexShader = `
                attribute float size;
                attribute float alpha;
                varying float vAlpha;
                ${shader.vertexShader}
              `.replace(
                'gl_PointSize = size * ( scale / - mvPosition.z );',
                'gl_PointSize = size * ( scale / - mvPosition.z );\nvAlpha = alpha;'
              );
              shader.fragmentShader = `
                varying float vAlpha;
                ${shader.fragmentShader}
              `.replace(
                'gl_FragColor = vec4( outgoingLight, diffuseColor.a );',
                'gl_FragColor = vec4( outgoingLight, diffuseColor.a * vAlpha );'
              );
            }}
          />
        </Points>
      ))}
    </group>
  );
}