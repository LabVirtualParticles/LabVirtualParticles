import { useNavigate } from 'react-router-dom'

export default function Menu() {
  const navigate = useNavigate()
  const btn = {
    background: 'none', color: 'white', border: 'none',
    cursor: 'pointer', marginRight: '1.5rem', fontSize: '1rem'
  }
  return (
    <nav style={{
      background: '#111', padding: '1rem 2rem',
      borderBottom: '1px solid #333', display: 'flex', alignItems: 'center'
    }}>
      <span style={{ color: 'white', fontWeight: 'bold', marginRight: '2rem' }}>
        LabVirtualParticles
      </span>
      <button style={btn} onClick={() => navigate('/')}>Início</button>
      <button style={btn} onClick={() => navigate('/simulacoes')}>Simulações</button>
      <button style={btn} onClick={() => navigate('/sobre')}>Sobre</button>
      <button
  style={{ ...btn, marginLeft: 'auto', background: '#4f8ef7', padding: '0.4rem 1rem', borderRadius: '4px' }}
  onClick={() => navigate('/login')}
>
  Entrar
</button>
    </nav>
  )
}