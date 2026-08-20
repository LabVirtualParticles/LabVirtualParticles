import { useNavigate } from 'react-router-dom'

export default function Simulacoes() {
  const navigate = useNavigate()
  return (
    <div style={{ color: 'white', padding: '2rem' }}>
      <h1>Simulações</h1>
      <h2 style={{ marginTop: '1rem' }}>Física Nuclear</h2>
      <button onClick={() => navigate('/simulacao/rutherford')}>
        Espalhamento de Rutherford
      </button>
      <h2 style={{ marginTop: '1rem' }}>Física Médica</h2>
      <p>Em breve</p>
      <h2 style={{ marginTop: '1rem' }}>Astrofísica</h2>
      <p>Em breve</p>
    </div>
  )
}