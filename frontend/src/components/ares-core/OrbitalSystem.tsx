import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Ring, Torus, Line } from '@react-three/drei';
import * as THREE from 'three';

interface OrbitalRing {
  radius: number;
  tube: number;
  radialSegments: number;
  tubularSegments: number;
  arc: number;
  rotation: [number, number, number];
  color: THREE.Color;
  opacity: number;
  speed: number;
  direction: number;
  isArc: boolean;
  glow?: boolean;
}

export function OrbitalSystem({ primaryColor, accentColor, speedMultiplier = 1, stateIntensity = 1 }: { primaryColor: THREE.Color, accentColor: THREE.Color, speedMultiplier?: number, stateIntensity?: number }) {
  const ringsRef = useRef<THREE.Group>(null);
  const arcRefs = useRef<(THREE.Group | null)[]>([]);

  // Define orbital rings with varied parameters
  const orbitalData = useMemo((): OrbitalRing[] => [
    // Primary equatorial ring - full torus
    {
      radius: 3.5,
      tube: 0.015,
      radialSegments: 8,
      tubularSegments: 64,
      arc: Math.PI * 2,
      rotation: [Math.PI / 2, 0, 0],
      color: primaryColor,
      opacity: 0.25,
      speed: 0.15,
      direction: 1,
      isArc: false,
      glow: true
    },
    // Secondary equatorial ring - thinner, inner
    {
      radius: 2.9,
      tube: 0.01,
      radialSegments: 6,
      tubularSegments: 64,
      arc: Math.PI * 2,
      rotation: [Math.PI / 2, 0, 0],
      color: accentColor,
      opacity: 0.18,
      speed: -0.22,
      direction: -1,
      isArc: false,
      glow: false
    },
    // Tertiary ring - outer, very thin
    {
      radius: 4.2,
      tube: 0.008,
      radialSegments: 4,
      tubularSegments: 64,
      arc: Math.PI * 2,
      rotation: [Math.PI / 2, 0, 0],
      color: primaryColor,
      opacity: 0.12,
      speed: 0.1,
      direction: 1,
      isArc: false,
      glow: false
    },
    // Tilted orbital arc 1 - asymmetric
    {
      radius: 3.8,
      tube: 0.02,
      radialSegments: 8,
      tubularSegments: 48,
      arc: Math.PI * 1.6,
      rotation: [Math.PI / 3.5, Math.PI / 5, Math.PI / 8],
      color: accentColor,
      opacity: 0.35,
      speed: 0.18,
      direction: 1,
      isArc: true,
      glow: true
    },
    // Tilted orbital arc 2 - opposite direction
    {
      radius: 4.5,
      tube: 0.015,
      radialSegments: 6,
      tubularSegments: 48,
      arc: Math.PI * 1.3,
      rotation: [-Math.PI / 4, -Math.PI / 6, -Math.PI / 10],
      color: primaryColor,
      opacity: 0.28,
      speed: -0.16,
      direction: -1,
      isArc: true,
      glow: true
    },
    // Tilted orbital arc 3 - steep angle
    {
      radius: 3.2,
      tube: 0.012,
      radialSegments: 6,
      tubularSegments: 48,
      arc: Math.PI * 1.8,
      rotation: [Math.PI / 2.2, Math.PI / 3, Math.PI / 12],
      color: accentColor,
      opacity: 0.22,
      speed: 0.2,
      direction: 1,
      isArc: true,
      glow: false
    },
    // Tilted orbital arc 4 - shallow angle
    {
      radius: 4.8,
      tube: 0.01,
      radialSegments: 4,
      tubularSegments: 48,
      arc: Math.PI * 1.1,
      rotation: [Math.PI / 6, -Math.PI / 4, Math.PI / 6],
      color: primaryColor,
      opacity: 0.18,
      speed: -0.12,
      direction: -1,
      isArc: true,
      glow: false
    },
    // Polar orbit - vertical
    {
      radius: 4.0,
      tube: 0.01,
      radialSegments: 6,
      tubularSegments: 64,
      arc: Math.PI * 1.9,
      rotation: [0, Math.PI / 2, 0],
      color: primaryColor,
      opacity: 0.15,
      speed: 0.08,
      direction: 1,
      isArc: true,
      glow: false
    },
    // High-energy highlighted arc - variable
    {
      radius: 3.6,
      tube: 0.025,
      radialSegments: 10,
      tubularSegments: 32,
      arc: Math.PI * 0.9,
      rotation: [Math.PI / 2.5, Math.PI / 8, Math.PI / 4],
      color: new THREE.Color('#00ffff'),
      opacity: 0.5,
      speed: 0.35,
      direction: 1,
      isArc: true,
      glow: true
    }
  ], [primaryColor, accentColor]);

  useFrame((state, delta) => {
    const time = state.clock.elapsedTime;
    const intensity = stateIntensity;
    const baseSpeed = delta * speedMultiplier;

    if (ringsRef.current) {
      ringsRef.current.children.forEach((child, idx) => {
        const data = orbitalData[idx];
        if (!data) return;

        const speed = data.speed * baseSpeed * intensity * data.direction;
        if (data.rotation[0] === Math.PI / 2 && data.rotation[1] === 0 && data.rotation[2] === 0) {
          // Equatorial rings rotate on Z
          child.rotation.z += speed;
        } else if (data.rotation[1] === Math.PI / 2 && data.rotation[0] === 0) {
          // Polar ring rotates on Y
          child.rotation.y += speed;
        } else {
          // Tilted rings - rotate on their local Z axis
          child.rotation.z += speed;
        }

        // Add subtle wobble for organic feel
        child.rotation.x += Math.sin(time * 0.5 + idx) * 0.0001 * intensity;
        child.rotation.y += Math.cos(time * 0.7 + idx) * 0.0001 * intensity;
      });
    }

    // Animate arc highlights
    arcRefs.current.forEach((arcGroup, idx) => {
      if (!arcGroup) return;
      const data = orbitalData[idx + 3]; // Skip first 3 full rings
      if (!data) return;

      const speed = data.speed * baseSpeed * intensity * data.direction;
      arcGroup.rotation.z += speed;

      // Pulse the highlighted arc
      if (data.glow && data.color.getHex() === 0x00ffff) {
        const pulse = 1 + Math.sin(time * 2.5) * 0.1;
        arcGroup.scale.setScalar(pulse);
        arcGroup.children.forEach((child: any) => {
          if (child.material) {
            child.material.opacity = data.opacity * (0.8 + Math.sin(time * 2.5) * 0.2);
          }
        });
      }
    });
  });

  return (
    <group ref={ringsRef}>
      {orbitalData.map((data, idx) => (
        <group
          key={`orbit-${idx}`}
          rotation={data.rotation}
          ref={(el) => { if (el && data.isArc && idx >= 3) arcRefs.current[idx - 3] = el; }}
        >
          {data.isArc ? (
            // Asymmetric arc using Ring with thetaLength
            <>
              <Ring
                args={[data.radius - data.tube * 2, data.radius + data.tube * 2, 32, 1, 0, data.arc]}
                material-color={data.color}
                material-transparent
                material-opacity={data.opacity}
                material-blending={data.glow ? THREE.AdditiveBlending : THREE.NormalBlending}
                material-side={THREE.DoubleSide}
                material-depthWrite={false}
              />
              {data.glow && (
                <Ring
                  args={[data.radius - data.tube * 4, data.radius + data.tube * 4, 32, 1, 0, data.arc]}
                  material-color={data.color}
                  material-transparent
                  material-opacity={data.opacity * 0.3}
                  material-blending={THREE.AdditiveBlending}
                  material-side={THREE.DoubleSide}
                  material-depthWrite={false}
                />
              )}
              // Arc endpoint markers
              <group position={[data.radius, 0, 0]}>
                <Torus args={[0.03, 0.008, 8, 16]} rotation={[0, 0, Math.PI / 2]}>
                  <meshBasicMaterial color={data.color} transparent opacity={data.opacity * 1.5} blending={THREE.AdditiveBlending} depthWrite={false} />
                </Torus>
              </group>
              <group position={[-data.radius * Math.cos(data.arc), -data.radius * Math.sin(data.arc), 0]}>
                <Torus args={[0.03, 0.008, 8, 16]} rotation={[0, 0, Math.PI / 2]}>
                  <meshBasicMaterial color={data.color} transparent opacity={data.opacity * 1.5} blending={THREE.AdditiveBlending} depthWrite={false} />
                </Torus>
              </group>
            </>
          ) : (
            // Full torus ring
            <>
              <Torus
                args={[data.radius, data.tube, data.radialSegments, data.tubularSegments, data.arc]}
                material-color={data.color}
                material-transparent
                material-opacity={data.opacity}
                material-metalness={0.3}
                material-roughness={0.5}
                material-blending={data.glow ? THREE.AdditiveBlending : THREE.NormalBlending}
              />
              {data.glow && (
                <Torus
                  args={[data.radius, data.tube * 2.5, data.radialSegments, 32, data.arc]}
                  material-color={data.color}
                  material-transparent
                  material-opacity={data.opacity * 0.2}
                  material-blending={THREE.AdditiveBlending}
                  material-depthWrite={false}
                />
              )}
            </>
          )}
        </group>
      ))}

      {/* Orbital path indicators - subtle dashed lines showing trajectories */}
      {orbitalData.slice(0, 3).map((data, idx) => {
        if (!data.isArc) {
          const points = [];
          const segments = 64;
          for (let i = 0; i <= segments; i++) {
            const angle = (i / segments) * Math.PI * 2;
            points.push(new THREE.Vector3(
              Math.cos(angle) * data.radius,
              Math.sin(angle) * data.radius,
              0
            ));
          }
          return (
            <Line
              key={`path-${idx}`}
              points={points}
              color={data.color}
              transparent
              opacity={0.03}
              lineWidth={0.5}
              blending={THREE.AdditiveBlending}
              depthWrite={false}
            />
          );
        }
        return null;
      })}
    </group>
  );
}