import { Canvas } from '@react-three/fiber'
import { OrbitControls, Line } from '@react-three/drei'
import { useNavigate } from 'react-router-dom'

const trajetorias = [
  [[-5, 0, 0], [-1, 0, 0], [0, 0, 0], [3, 1, 0]],
  [[-5, 0.3, 0], [-1, 0.3, 0], [0, 0.1, 0], [3, -0.5, 0.2]],
  [[-5, -0.3, 0], [-1, -0.3, 0], [0, -0.1, 0], [3, 0.8, -0.3]],
  [[-5, 0.1, 0.2], [-1, 0.1, 0.2], [-0.5, 0.1, 0.2], [-3, 2, 0.5]],
]

export default function Rutherford() {
  const navigate = useNavigate()
  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      <button
        onClick={() => navigate('/simulacoes')}
        style={{
          position: 'absolute', top: '1rem', left: '1rem',
          zIndex: 10, background: '#333', color: 'white',
          border: 'none', padding: '0.5rem 1rem', cursor: 'pointer',
          borderRadius: '4px'
        }}
      >
        ← Voltar
      </button>
      <div style={{
        position: 'absolute', top: '1rem', left: '50%',
        transform: 'translateX(-50%)', zIndex: 10,
        color: 'white', fontSize: '1.2rem', fontWeight: 'bold'
      }}>
        Espalhamento de Rutherford
      </div>
      <Canvas camera={{ position: [5, 3, 5], fov: 60 }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[5, 5, 5]} intensity={1} />
        <mesh>
          <boxGeometry args={[0.1, 2, 2]} />
          <meshStandardMaterial color="#FFD700" transparent opacity={0.6} />
        </mesh>
        {trajetorias.map((pontos, i) => (
          <Line key={i} points={pontos} color="#FF4444" lineWidth={2} />
        ))}
        <OrbitControls />
        <axesHelper args={[3]} />
        <gridHelper args={[10, 10]} />
      </Canvas>
    </div>
  )
}