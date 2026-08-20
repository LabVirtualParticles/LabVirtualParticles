import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Login() {
  const [modo, setModo] = useState('login')
  const navigate = useNavigate()

  return (
    <div style={{
      display: 'flex', justifyContent: 'center', alignItems: 'center',
      minHeight: 'calc(100vh - 56px)', background: '#111'
    }}>
      <div style={{
        background: '#1a1a1a', padding: '2rem', borderRadius: '8px',
        width: '100%', maxWidth: '400px', border: '1px solid #333'
      }}>
        <h1 style={{ color: 'white', textAlign: 'center', marginBottom: '0.5rem' }}>
          LabVirtualParticles
        </h1>
        <p style={{ color: '#888', textAlign: 'center', marginBottom: '2rem', fontSize: '0.9rem' }}>
          Laboratório Virtual de Física de Partículas
        </p>

        <div style={{ display: 'flex', marginBottom: '2rem', borderBottom: '1px solid #333' }}>
          <button
            onClick={() => setModo('login')}
            style={{
              flex: 1, padding: '0.75rem', background: 'none', border: 'none',
              cursor: 'pointer', fontSize: '1rem',
              color: modo === 'login' ? 'white' : '#888',
              borderBottom: modo === 'login' ? '2px solid #4f8ef7' : 'none'
            }}
          >
            Entrar
          </button>
          <button
            onClick={() => setModo('cadastro')}
            style={{
              flex: 1, padding: '0.75rem', background: 'none', border: 'none',
              cursor: 'pointer', fontSize: '1rem',
              color: modo === 'cadastro' ? 'white' : '#888',
              borderBottom: modo === 'cadastro' ? '2px solid #4f8ef7' : 'none'
            }}
          >
            Criar conta
          </button>
        </div>

        {modo === 'cadastro' && (
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ color: '#aaa', fontSize: '0.85rem' }}>Nome</label>
            <input
              type="text"
              placeholder="Seu nome"
              style={{
                width: '100%', padding: '0.75rem', marginTop: '0.25rem',
                background: '#222', border: '1px solid #444', borderRadius: '4px',
                color: 'white', fontSize: '1rem', boxSizing: 'border-box'
              }}
            />
          </div>
        )}

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ color: '#aaa', fontSize: '0.85rem' }}>E-mail</label>
          <input
            type="email"
            placeholder="seu@email.com"
            style={{
              width: '100%', padding: '0.75rem', marginTop: '0.25rem',
              background: '#222', border: '1px solid #444', borderRadius: '4px',
              color: 'white', fontSize: '1rem', boxSizing: 'border-box'
            }}
          />
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ color: '#aaa', fontSize: '0.85rem' }}>Senha</label>
          <input
            type="password"
            placeholder="••••••••"
            style={{
              width: '100%', padding: '0.75rem', marginTop: '0.25rem',
              background: '#222', border: '1px solid #444', borderRadius: '4px',
              color: 'white', fontSize: '1rem', boxSizing: 'border-box'
            }}
          />
        </div>

        <button
          style={{
            width: '100%', padding: '0.75rem', background: '#4f8ef7',
            color: 'white', border: 'none', borderRadius: '4px',
            fontSize: '1rem', cursor: 'pointer', marginBottom: '1rem'
          }}
        >
          {modo === 'login' ? 'Entrar' : 'Criar conta'}
        </button>

        <div style={{ textAlign: 'center', margin: '1rem 0', color: '#555' }}>ou</div>

        <button
          style={{
            width: '100%', padding: '0.75rem', background: '#222',
            color: 'white', border: '1px solid #444', borderRadius: '4px',
            fontSize: '1rem', cursor: 'pointer', display: 'flex',
            alignItems: 'center', justifyContent: 'center', gap: '0.5rem'
          }}
        >
          Continuar com Google
        </button>

        <p
          onClick={() => navigate('/')}
          style={{
            color: '#888', textAlign: 'center', marginTop: '1.5rem',
            fontSize: '0.85rem', cursor: 'pointer'
          }}
        >
          Continuar sem conta →
        </p>
      </div>
    </div>
  )
}