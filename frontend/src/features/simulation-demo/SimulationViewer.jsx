import { Suspense, useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { Line, OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

// Clean edge-only wireframe (via EdgesGeometry) instead of the
// `wireframe: true` material prop, which draws a diagonal across every
// quad face and doesn't match the clean box outline in the reference
// video.
function WireframeBox({ size, position = [0, 0, 0] }) {
  const edges = useMemo(
    () => new THREE.EdgesGeometry(new THREE.BoxGeometry(...size)),
    [size]
  );
  return (
    <lineSegments geometry={edges} position={position}>
      <lineBasicMaterial color="#ffffff" transparent opacity={0.35} />
    </lineSegments>
  );
}

function TargetVolume({ size, position = [0, 0, 0] }) {
  return (
    <mesh position={position}>
      <boxGeometry args={size} />
      <meshBasicMaterial color="#e3b23c" wireframe />
    </mesh>
  );
}

function Trajectories({ trajectories }) {
  return trajectories.map((trajectory) => (
    <Line key={trajectory.id} points={trajectory.points} color={trajectory.color} lineWidth={1.4} />
  ));
}

/**
 * Placeholder 3D view. `data` is expected to follow the shape of
 * data/result.example.json:
 *   { world: { size }, volumes: [{ id, shape, size, position, wireframeOnly? }], trajectories: [{ id, color, points }] }
 *
 * Once the Geant4 pipeline is wired up, feed the converted
 * geometry/trajectory JSON from your backend into this same `data`
 * prop — nothing in this file needs to change as long as the shape
 * matches.
 */
export default function SimulationViewer({ data, status }) {
  return (
    <div className="simulation-viewer">
      <Canvas camera={{ position: [220, 160, 260], fov: 40 }}>
        <color attach="background" args={['#000000']} />
        <ambientLight intensity={0.6} />
        <Suspense fallback={null}>
          <WireframeBox size={data.world.size} />
          {data.volumes
            .filter((volume) => !volume.wireframeOnly)
            .map((volume) => (
              <TargetVolume key={volume.id} size={volume.size} position={volume.position} />
            ))}
          <Trajectories trajectories={data.trajectories} />
        </Suspense>
        <OrbitControls enablePan={false} minDistance={120} maxDistance={600} />
      </Canvas>

      {status === 'running' && (
        <div className="simulation-viewer__overlay" role="status">
          Processando simulação…
        </div>
      )}
    </div>
  );
}
