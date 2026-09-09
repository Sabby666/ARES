import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Icosahedron, Line, Points, PointMaterial } from '@react-three/drei';
import * as THREE from 'three';

export function TopologySphere({ color, scale = 1, stateIntensity = 1 }: { color: THREE.Color, scale?: number, stateIntensity?: number }) {
  const groupRef = useRef<THREE.Group>(null);
  const wireframeRef = useRef<THREE.Mesh>(null);
  const pointsRef = useRef<THREE.Points>(null);
  const innerShellRef = useRef<THREE.Mesh>(null);
  const outerShellRef = useRef<THREE.Mesh>(null);

  // Generate topology geometry - multiple layers of icosahedron
  const topologyData = useMemo(() => {
    const vertices: THREE.Vector3[] = [];
    const edges: [number, number][] = [];
    const positions: number[] = [];

    // Layer 1: Dense computational topology - radius 3.2
    const geo1 = new THREE.IcosahedronGeometry(3.2, 5);
    const pos1 = geo1.attributes.position.array as Float32Array;
    for (let i = 0; i < pos1.length; i += 3) {
      vertices.push(new THREE.Vector3(pos1[i], pos1[i+1], pos1[i+2]));
    }

    // Create edges from the geometry
    const index1 = geo1.index?.array;
    if (index1) {
      for (let i = 0; i < index1.length; i += 3) {
        const a = index1[i];
        const b = index1[i+1];
        const c = index1[i+2];
        edges.push([a, b], [b, c], [c, a]);
      }
    }

    // Layer 2: Intermediate topology - radius 3.8
    const geo2 = new THREE.IcosahedronGeometry(3.8, 4);
    const pos2 = geo2.attributes.position.array as Float32Array;
    for (let i = 0; i < pos2.length; i += 3) {
      vertices.push(new THREE.Vector3(pos2[i], pos2[i+1], pos2[i+2]));
    }

    // Layer 3: Outer topology - radius 4.4
    const geo3 = new THREE.IcosahedronGeometry(4.4, 3);
    const pos3 = geo3.attributes.position.array as Float32Array;
    for (let i = 0; i < pos3.length; i += 3) {
      vertices.push(new THREE.Vector3(pos3[i], pos3[i+1], pos3[i+2]));
    }

    // Generate glowing intersection points for all layers
    for (let i = 0; i < vertices.length; i++) {
      const v = vertices[i];
      // Add slight noise for organic feel
      positions.push(
        v.x + (Math.random() - 0.5) * 0.02,
        v.y + (Math.random() - 0.5) * 0.02,
        v.z + (Math.random() - 0.5) * 0.02
      );
    }

    return { vertices, edges, positions: new Float32Array(positions) };
  }, []);

  useFrame((state) => {
    const time = state.clock.elapsedTime;
    const intensity = stateIntensity;

    if (groupRef.current) {
      groupRef.current.rotation.y = time * 0.02;
      groupRef.current.rotation.z = time * 0.01;
      groupRef.current.rotation.x = time * 0.005;
    }
    if (wireframeRef.current) {
      wireframeRef.current.rotation.y = -time * 0.015;
      wireframeRef.current.rotation.x = time * 0.008;
    }
    if (innerShellRef.current) {
      innerShellRef.current.rotation.y = time * 0.01;
      innerShellRef.current.rotation.x = -time * 0.005;
    }
    if (outerShellRef.current) {
      outerShellRef.current.rotation.y = -time * 0.008;
      outerShellRef.current.rotation.z = time * 0.004;
    }
    if (pointsRef.current) {
      // Simple rotation only — no per-vertex mutation
      pointsRef.current.rotation.y = time * 0.015;
      pointsRef.current.rotation.x = -time * 0.008;
    }
  });

  return (
    <group ref={groupRef} scale={scale}>
      {/* Layer 1: Inner computational shell - dark blue, denser */}
      <Icosahedron ref={innerShellRef} args={[3.2, 5]}>
        <meshPhysicalMaterial
          color={new THREE.Color('#0a1a3a')}
          wireframe
          transparent
          opacity={0.12}
          metalness={0.6}
          roughness={0.3}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </Icosahedron>

      {/* Layer 2: Mid computational topology - primary color */}
      <Icosahedron ref={wireframeRef} args={[3.8, 4]}>
        <meshBasicMaterial
          color={color}
          wireframe
          transparent
          opacity={0.15}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </Icosahedron>

      {/* Layer 3: Outer computational topology - lighter, sparser */}
      <Icosahedron ref={outerShellRef} args={[4.4, 3]}>
        <meshBasicMaterial
          color={new THREE.Color('#1a3a6e')}
          wireframe
          transparent
          opacity={0.08}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </Icosahedron>

      {/* Layer 4: Glowing intersection points - all layers combined */}
      <Points ref={pointsRef} positions={topologyData.positions} stride={3} frustumCulled={false}>
        <PointMaterial
          transparent
          color={color}
          size={0.025}
          sizeAttenuation={true}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
          opacity={0.7}
        />
      </Points>

      {/* Layer 5: Secondary highlight points - brighter, sparser */}
      <Points positions={topologyData.positions} stride={3} frustumCulled={false} scale={1.001}>
        <PointMaterial
          transparent
          color="#ffffff"
          size={0.015}
          sizeAttenuation={true}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
          opacity={0.3}
        />
      </Points>

      {/* Layer 6: Energy field lines - connecting nearby vertices */}
      {topologyData.edges.slice(0, 200).map(([a, b], idx) => {
        const v1 = topologyData.vertices[a];
        const v2 = topologyData.vertices[b];
        if (!v1 || !v2) return null;
        const dist = v1.distanceTo(v2);
        if (dist > 1.8) return null;
        return (
          <Line
            key={`edge-${idx}`}
            points={[v1, v2]}
            color={color}
            transparent
            opacity={0.08}
            lineWidth={0.5}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        );
      })}
    </group>
  );
}