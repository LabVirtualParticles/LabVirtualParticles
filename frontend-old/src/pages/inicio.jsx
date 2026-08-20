import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import sim1 from '../assets/sim1.jpg'
import sim2 from '../assets/sim2.jpg'
import sim3 from '../assets/sim3.jpg'

const imagens = [sim1, sim2, sim3]

function Carrossel() {
  const [atual, setAtual] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setAtual(i => (i + 1) % imagens.length)
    }, 4000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div style={{ position: 'relative', height: '420px', background: '#000', overflow: 'hidden' }}>
      {imagens.map((img, i) => (
        <img
          key={i}
          src={img}
          style={{
            position: 'absolute', width: '100%', height: '100%',
            objectFit: 'cover', opacity: i === atual ? 1 : 0,
            transition: 'opacity 1s ease'
          }}
        />
      ))}
      <div style={{
        position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.5)',
        display: 'flex', flexDirection: 'column', justifyContent: 'center',
        padding: '2rem'
      }}>
        <h1 style={{ color: 'white', fontSize: '2.2rem', maxWidth: '500px', lineHeight: 1.3 }}>
          Simule experimentos de física de partículas direto no navegador
        </h1>
      </div>
      <div style={{ position: 'absolute', bottom: '1rem', left: '50%', transform: 'translateX(-50%)', display: 'flex', gap: '0.5rem' }}>
        {imagens.map((_, i) => (
          <div
            key={i}
            onClick={() => setAtual(i)}
            style={{
              width: '10px', height: '10px', borderRadius: '50%',
              background: i === atual ? 'white' : '#888', cursor: 'pointer'
            }}
          />
        ))}
      </div>
    </div>
  )
}

function Cards() {
  return (
    <div style={{ background: '#fff', padding: '3rem 2rem' }}>
      <h2 style={{ textAlign: 'center', marginBottom: '0.5rem', fontSize: '1.8rem' }}>
        Simulação de física de partículas direto no navegador!
      </h2>
      <p style={{ textAlign: 'center', color: '#666', marginBottom: '2rem' }}>
        Powered by Geant4 — CERN
      </p>
      <div style={{ display: 'flex', gap: '2rem', maxWidth: '900px', margin: '0 auto', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: '250px' }}>
          <p style={{ color: '#444', lineHeight: 1.7 }}>
            Uma plataforma web para simulação e visualização de interações entre partículas
            subatômicas, desenvolvida com base no toolkit Geant4 do CERN. Com ela, é possível
            configurar partículas, definir materiais e geometrias, e analisar os resultados
            — sem precisar instalar nada.
          </p>
        </div>
        <div style={{ flex: 1, minWidth: '250px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ background: '#f0f0f0', padding: '1rem', borderRadius: '8px' }}>
            <strong>Ensino e pesquisa:</strong>
            <p style={{ color: '#555', marginTop: '0.25rem' }}>Exploração de fenômenos físicos em contexto acadêmico.</p>
          </div>
          <div style={{ background: '#f0f0f0', padding: '1rem', borderRadius: '8px' }}>
            <strong>Prototipagem rápida:</strong>
            <p style={{ color: '#555', marginTop: '0.25rem' }}>Configuração e teste de simulações sem ambiente local instalado.</p>
          </div>
        </div>
      </div>
    </div>
  )
}

function ComoFunciona() {
  const passos = [
    { num: '01', titulo: 'Escolha um experimento', desc: 'Navegue pelas seções temáticas e selecione uma simulação predefinida.' },
    { num: '02', titulo: 'Configure os parâmetros', desc: 'Ajuste energia do feixe, material do alvo, espessura e outros parâmetros físicos.' },
    { num: '03', titulo: 'Execute a simulação', desc: 'O Geant4 processa os cálculos no servidor e retorna os resultados.' },
    { num: '04', titulo: 'Visualize em 3D', desc: 'Explore a cena interativa com trajetórias das partículas renderizadas em tempo real.' },
  ]
  return (
    <div style={{ background: '#111', padding: '3rem 2rem' }}>
      <h2 style={{ color: 'white', textAlign: 'center', marginBottom: '2rem', fontSize: '1.8rem' }}>
        Como funciona
      </h2>
      <div style={{ display: 'flex', gap: '1.5rem', maxWidth: '900px', margin: '0 auto', flexWrap: 'wrap' }}>
        {passos.map(p => (
          <div key={p.num} style={{ flex: 1, minWidth: '180px', textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', color: '#4f8ef7', fontWeight: 'bold' }}>{p.num}</div>
            <h3 style={{ color: 'white', margin: '0.5rem 0' }}>{p.titulo}</h3>
            <p style={{ color: '#888', lineHeight: 1.6 }}>{p.desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

function SobreGeant4() {
  return (
    <div style={{ background: '#fff', padding: '3rem 2rem' }}>
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>
        <h2 style={{ fontSize: '1.8rem', marginBottom: '1.5rem' }}>O que é o Geant4?</h2>
        <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '250px' }}>
            <p style={{ color: '#444', lineHeight: 1.7, marginBottom: '1rem' }}>
              O Geant4 é o principal toolkit mundial para simulação de interações de partículas
              com a matéria. Desenvolvido pelo CERN — Conselho Europeu para a Pesquisa Nuclear
              — é distribuído como software de código aberto desde 1998 e acumula mais de
              16.000 citações científicas.
            </p>
            <p style={{ color: '#444', lineHeight: 1.7 }}>
              Além da física de partículas, é utilizado em áreas como engenharia nuclear,
              astrofísica, física biomédica e arqueologia. Instituições como NASA, CERN e
              centros de radioterapia ao redor do mundo dependem dele para pesquisa e desenvolvimento.
            </p>
          </div>
          <div style={{ flex: 1, minWidth: '250px' }}>
            <div style={{ background: '#f0f0f0', padding: '1.5rem', borderRadius: '8px' }}>
              <h3 style={{ marginBottom: '1rem' }}>O que é o CERN?</h3>
              <p style={{ color: '#555', lineHeight: 1.7 }}>
                O CERN é a maior organização de pesquisa em física de partículas do mundo,
                localizado na fronteira entre a Suíça e a França. Responsável pelo Large Hadron
                Collider (LHC) e pela descoberta do bóson de Higgs em 2012, o CERN também
                criou a World Wide Web em 1989 como ferramenta para compartilhar dados científicos.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function BotaoSimular() {
  const navigate = useNavigate()
  return (
    <div style={{ background: '#111', padding: '3rem 2rem', textAlign: 'center' }}>
      <h2 style={{ color: 'white', marginBottom: '1rem' }}>Pronto para experimentar?</h2>
      <p style={{ color: '#888', marginBottom: '2rem' }}>
        Acesse as simulações gratuitamente, sem precisar criar uma conta.
      </p>
      <button
        onClick={() => navigate('/simulacoes')}
        style={{
          background: '#4f8ef7', color: 'white', border: 'none',
          padding: '1rem 2.5rem', borderRadius: '4px', fontSize: '1.1rem',
          cursor: 'pointer'
        }}
      >
        Acessar simulações
      </button>
    </div>
  )
}

export default function Inicio() {
  return (
    <div>
      <Carrossel />
      <Cards />
      <ComoFunciona />
      <SobreGeant4 />
      <BotaoSimular />
    </div>
  )
}