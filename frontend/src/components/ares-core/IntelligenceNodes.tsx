import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sphere, Icosahedron, Line, Points, PointMaterial } from '@react-three/drei';
import * as THREE from 'three';

interface Node {
  position: THREE.Vector3;
  baseRadius: number;
  baseDistance: number;
  type: 'primary' | 'secondary' | 'micro';
  phase: number;
  speed: number;
  connections: number[];
  pulsePhase: number;
  pulseSpeed: number;
  color: THREE.Color;
  glowColor: THREE.Color;
}

export function IntelligenceNodes({ color, accentColor, speedMultiplier = 1, stateIntensity = 1 }: { color: THREE.Color, accentColor?: THREE.Color, speedMultiplier?: number, stateIntensity?: number }) {
  const groupRef = useRef<THREE.Group>(null);
  const primaryNodesRef = useRef<THREE.Group>(null);
  const secondaryNodesRef = useRef<THREE.Group>(null);

  // Generate hierarchical node system
  const nodes = useMemo((): Node[] => {
    const arr: Node[] = [];
    const accent = accentColor || new THREE.Color('#8B5CF6');
    const cyanAccent = new THREE.Color('#00ffff');

    // PRIMARY NODES - 12 major intelligence nodes at varying distances
    const primaryCount = 12;
    for (let i = 0; i < primaryCount; i++) {
      const phi = Math.acos(-1 + (2 * i + 1) / primaryCount);
      const theta = Math.sqrt(primaryCount * Math.PI) * phi + Math.random() * 0.5;
      const baseDistance = 3.0 + Math.random() * 1.2; // 3.0 - 4.2

      const x = baseDistance * Math.cos(theta) * Math.sin(phi);
      const y = baseDistance * Math.sin(theta) * Math.sin(phi);
      const z = baseDistance * Math.cos(phi);

      arr.push({
        position: new THREE.Vector3(x, y, z),
        baseRadius: 0.08 + Math.random() * 0.04,
        baseDistance,
        type: 'primary',
        phase: Math.random() * Math.PI * 2,
        speed: 0.05 + Math.random() * 0.08,
        connections: [],
        pulsePhase: Math.random() * Math.PI * 2,
        pulseSpeed: 0.8 + Math.random() * 1.2,
        color: color.clone(),
        glowColor: color.clone()
      });
    }

    // SECONDARY NODES - 20 intermediate nodes
    const secondaryCount = 20;
    for (let i = 0; i < secondaryCount; i++) {
      const phi = Math.acos(-1 + (2 * i + 1) / secondaryCount);
      const theta = Math.sqrt(secondaryCount * Math.PI) * phi + Math.random() * 0.8;
      const baseDistance = 2.5 + Math.random() * 2.0; // 2.5 - 4.5

      const x = baseDistance * Math.cos(theta) * Math.sin(phi);
      const y = baseDistance * Math.sin(theta) * Math.sin(phi);
      const z = baseDistance * Math.cos(phi);

      arr.push({
        position: new THREE.Vector3(x, y, z),
        baseRadius: 0.04 + Math.random() * 0.02,
        baseDistance,
        type: 'secondary',
        phase: Math.random() * Math.PI * 2,
        speed: 0.08 + Math.random() * 0.12,
        connections: [],
        pulsePhase: Math.random() * Math.PI * 2,
        pulseSpeed: 1.2 + Math.random() * 1.5,
        color: accent,
        glowColor: accent.clone()
      });
    }

    // MICRO NODES - 50 tiny particles
    const microCount = 50;
    for (let i = 0; i < microCount; i++) {
      const phi = Math.acos(-1 + (2 * i + 1) / microCount);
      const theta = Math.sqrt(microCount * Math.PI) * phi + Math.random() * 1.5;
      const baseDistance = 2.0 + Math.random() * 3.0; // 2.0 - 5.0

      const x = baseDistance * Math.cos(theta) * Math.sin(phi);
      const y = baseDistance * Math.sin(theta) * Math.sin(phi);
      const z = baseDistance * Math.cos(phi);

      arr.push({
        position: new THREE.Vector3(x, y, z),
        baseRadius: 0.015 + Math.random() * 0.01,
        baseDistance,
        type: 'micro',
        phase: Math.random() * Math.PI * 2,
        speed: 0.15 + Math.random() * 0.25,
        connections: [],
        pulsePhase: Math.random() * Math.PI * 2,
        pulseSpeed: 2 + Math.random() * 2,
        color: cyanAccent,
        glowColor: cyanAccent.clone()
      });
    }

    // Build connection graph - connect nearby nodes
    for (let i = 0; i < arr.length; i++) {
      for (let j = i + 1; j < arr.length; j++) {
        const dist = arr[i].position.distanceTo(arr[j].position);
        // Connect primary to primary/secondary, secondary to secondary/micro
        const maxDist = arr[i].type === 'primary' ? 3.2 : arr[i].type === 'secondary' ? 2.5 : 1.8;
        if (dist < maxDist && arr[i].connections.length < 6 && arr[j].connections.length < 6) {
          arr[i].connections.push(j);
          arr[j].connections.push(i);
        }
      }
    }

    return arr;
  }, [color, accentColor]);

  useFrame((state, delta) => {
    const time = state.clock.elapsedTime;
    const intensity = stateIntensity;
    const baseSpeed = delta * speedMultiplier * intensity;

    if (groupRef.current) {
      groupRef.current.rotation.y += baseSpeed * 0.3;
      groupRef.current.rotation.x += baseSpeed * 0.1;
    }
    if (primaryNodesRef.current) {
      primaryNodesRef.current.rotation.y += baseSpeed * 0.15;
      primaryNodesRef.current.rotation.z += baseSpeed * 0.05;
    }
    if (secondaryNodesRef.current) {
      secondaryNodesRef.current.rotation.y -= baseSpeed * 0.2;
      secondaryNodesRef.current.rotation.x += baseSpeed * 0.08;
    }
  });

  // Split nodes by type for rendering groups
  const primaryNodes = nodes.filter(n => n.type === 'primary');
  const secondaryNodes = nodes.filter(n => n.type === 'secondary');
  const microNodes = nodes.filter(n => n.type === 'micro');

  return (
    <group ref={groupRef}>
      {/* CONNECTION TOPOLOGY - rendered first for depth */}
      <group>
        {nodes.map((node, i) =>
          node.connections.map((connIdx, ci) => {
            if (connIdx < i) return null; // Avoid duplicate lines
            const target = nodes[connIdx];
            if (!target) return null;

            // Connection strength based on node types
            let opacity = 0.06;
            let lineWidth = 0.4;
            if (node.type === 'primary' && target.type === 'primary') {
              opacity = 0.15;
              lineWidth = 0.8;
            } else if (node.type === 'primary' || target.type === 'primary') {
              opacity = 0.1;
              lineWidth = 0.6;
            } else if (node.type === 'secondary' && target.type === 'secondary') {
              opacity = 0.08;
              lineWidth = 0.5;
            }

            // Color based on node types
            let lineColor = color;
            if (node.type === 'primary' && target.type === 'primary') lineColor = color;
            else if (node.type === 'secondary' || target.type === 'secondary') lineColor = accentColor || color;
            else lineColor = new THREE.Color('#00ffff');

            return (
              <Line
                key={`conn-${i}-${connIdx}`}
                points={[node.position, target.position]}
                color={lineColor}
                transparent
                opacity={opacity}
                lineWidth={lineWidth}
                blending={THREE.AdditiveBlending}
                depthWrite={false}
              />
            );
          })
        )}

        {/* Energy trails - animated signal paths between primary nodes */}
        {primaryNodes.map((node, i) =>
          node.connections
            .filter(idx => idx > i && nodes[idx].type === 'primary')
            .map((connIdx, ci) => {
              const target = nodes[connIdx];
              if (!target) return null;

              return (
                <EnergyTrail
                  key={`trail-${i}-${connIdx}`}
                  start={node.position}
                  end={target.position}
                  color={color}
                  speed={0.8 + Math.random() * 0.6}
                  phase={Math.random() * Math.PI * 2}
                  intensity={stateIntensity}
                />
              );
            })
        )}
      </group>

      {/* PRIMARY NODES - Large luminous orbs with halos */}
      <group ref={primaryNodesRef}>
        {primaryNodes.map((node, idx) => (
          <PrimaryNode
            key={`primary-${idx}`}
            node={node}
            index={idx}
            time={0} // Will use internal clock
            intensity={stateIntensity}
          />
        ))}
      </group>

      {/* SECONDARY NODES - Medium points with subtle glow */}
      <group ref={secondaryNodesRef}>
        {secondaryNodes.map((node, idx) => (
          <SecondaryNode
            key={`secondary-${idx}`}
            node={node}
            index={idx}
            intensity={stateIntensity}
          />
        ))}
      </group>

      {/* MICRO NODES - Tiny points as particle field */}
      <Points positions={new Float32Array(microNodes.length * 3)} stride={3} frustumCulled={false}>
        <PointMaterial
          transparent
          color={new THREE.Color('#00ffff')}
          size={0.015}
          sizeAttenuation={true}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
          opacity={0.4}
        />
      </Points>

      {/* Render micro nodes as individual small spheres for better depth */}
      {microNodes.map((node, idx) => (
        <MicroNode key={`micro-${idx}`} node={node} intensity={stateIntensity} />
      ))}
    </group>
  );
}

// Primary Node Component - Luminous orb with halo and pulse
function PrimaryNode({ node, index, time, intensity }: { node: Node, index: number, time: number, intensity: number }) {
  const ref = useRef<THREE.Group>(null);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    if (ref.current) {
      // Orbital motion around base position
      const orbitRadius = 0.15;
      ref.current.position.x = node.position.x + Math.cos(t * node.speed + node.phase) * orbitRadius;
      ref.current.position.y = node.position.y + Math.sin(t * node.speed * 1.3 + node.phase) * orbitRadius;
      ref.current.position.z = node.position.z + Math.cos(t * node.speed * 0.7 + node.phase) * orbitRadius * 0.5;

      // Pulse animation
      const pulse = 1 + Math.sin(t * node.pulseSpeed + node.pulsePhase) * 0.15 * intensity;
      ref.current.scale.setScalar(pulse);
    }
  });

  return (
    <group ref={ref} position={node.position}>
      {/* Core orb */}
      <Icosahedron args={[node.baseRadius, 1]}>
        <meshPhysicalMaterial
          color={node.color}
          emissive={node.color}
          emissiveIntensity={0.8 * intensity}
          metalness={0.9}
          roughness={0.1}
          clearcoat={1}
          clearcoatRoughness={0.05}
          transparent
          opacity={1}
        />
      </Icosahedron>

      {/* Inner glow sphere */}
      <Sphere args={[node.baseRadius * 1.4, 16, 16]}>
        <meshBasicMaterial
          color={node.glowColor}
          transparent
          opacity={0.5 * intensity}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </Sphere>

      {/* Outer halo */}
      <Sphere args={[node.baseRadius * 2.5, 16, 16]}>
        <meshBasicMaterial
          color={node.glowColor}
          transparent
          opacity={0.2 * intensity}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </Sphere>

      {/* Corona ring */}
      <Icosahedron args={[node.baseRadius * 3.2, 0]}>
        <meshBasicMaterial
          color={node.glowColor}
          transparent
          opacity={0.08 * intensity}
          wireframe
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </Icosahedron>
    </group>
  );
}

// Secondary Node Component - Smaller point with glow
function SecondaryNode({ node, index, intensity }: { node: Node, index: number, intensity: number }) {
  const ref = useRef<THREE.Group>(null);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    if (ref.current) {
      const orbitRadius = 0.1;
      ref.current.position.x = node.position.x + Math.cos(t * node.speed + node.phase) * orbitRadius;
      ref.current.position.y = node.position.y + Math.sin(t * node.speed * 1.2 + node.phase) * orbitRadius;
      ref.current.position.z = node.position.z + Math.cos(t * node.speed * 0.8 + node.phase) * orbitRadius * 0.5;

      const pulse = 1 + Math.sin(t * node.pulseSpeed + node.pulsePhase) * 0.1 * intensity;
      ref.current.scale.setScalar(pulse);
    }
  });

  return (
    <group ref={ref} position={node.position}>
      {/* Core */}
      <Sphere args={[node.baseRadius, 12, 12]}>
        <meshPhysicalMaterial
          color={node.color}
          emissive={node.color}
          emissiveIntensity={0.5 * intensity}
          metalness={0.7}
          roughness={0.2}
          transparent
          opacity={0.9}
        />
      </Sphere>

      {/* Glow */}
      <Sphere args={[node.baseRadius * 2.2, 12, 12]}>
        <meshBasicMaterial
          color={node.glowColor}
          transparent
          opacity={0.3 * intensity}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </Sphere>

      {/* Outer pulse */}
      <Sphere args={[node.baseRadius * 3.5, 8, 8]}>
        <meshBasicMaterial
          color={node.glowColor}
          transparent
          opacity={0.1 * intensity}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
          wireframe
        />
      </Sphere>
    </group>
  );
}

// Micro Node Component - Tiny point
function MicroNode({ node, intensity }: { node: Node, intensity: number }) {
  const ref = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    if (ref.current) {
      const orbitRadius = 0.05;
      ref.current.position.x = node.position.x + Math.cos(t * node.speed + node.phase) * orbitRadius;
      ref.current.position.y = node.position.y + Math.sin(t * node.speed * 1.5 + node.phase) * orbitRadius;
      ref.current.position.z = node.position.z + Math.cos(t * node.speed * 0.6 + node.phase) * orbitRadius * 0.5;

      const pulse = 1 + Math.sin(t * node.pulseSpeed + node.pulsePhase) * 0.2 * intensity;
      ref.current.scale.setScalar(pulse);
      (ref.current.material as THREE.MeshBasicMaterial).opacity = 0.4 + Math.sin(t * node.pulseSpeed + node.pulsePhase) * 0.2 * intensity;
    }
  });

  return (
    <Sphere ref={ref} args={[node.baseRadius, 6, 6]} position={node.position}>
      <meshBasicMaterial
        color={node.color}
        transparent
        opacity={0.5}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </Sphere>
  );
}

// Energy Trail Component - Animated signal path
// NOTE: Uses ref-based mutation instead of useState to avoid per-frame re-renders
function EnergyTrail({ start, end, color, speed, phase, intensity }: { start: THREE.Vector3, end: THREE.Vector3, color: THREE.Color, speed: number, phase: number, intensity: number }) {
  const lineRef = useRef<any>(null);

  const points = useMemo(() => {
    const pts = [];
    const segments = 16;
    for (let i = 0; i <= segments; i++) {
      const t = i / segments;
      const x = THREE.MathUtils.lerp(start.x, end.x, t);
      const y = THREE.MathUtils.lerp(start.y, end.y, t);
      const z = THREE.MathUtils.lerp(start.z, end.z, t);
      const mid = Math.sin(t * Math.PI) * 0.12;
      const dir = new THREE.Vector3().subVectors(end, start).normalize();
      const perp = new THREE.Vector3(-dir.y, dir.x, 0).normalize();
      pts.push(new THREE.Vector3(x + perp.x * mid, y + perp.y * mid, z));
    }
    return pts;
  }, [start, end]);

  useFrame((state) => {
    if (!lineRef.current) return;
    const t = state.clock.elapsedTime;
    const offset = (t * speed + phase) % 1;
    // Directly mutate material — no React re-render
    if (lineRef.current.material) {
      lineRef.current.material.dashOffset = -offset * 2;
      lineRef.current.material.opacity = 0.28 * intensity * (0.5 + Math.sin(t * 3 + phase) * 0.5);
    }
  });

  return (
    <Line
      ref={lineRef}
      points={points}
      color={color}
      transparent
      lineWidth={1.2}
      blending={THREE.AdditiveBlending}
      depthWrite={false}
      dashed={true}
      dashSize={0.15}
      gapSize={0.3}
      dashOffset={0}
      opacity={0.28}
    />
  );
}