
import heroImage from '../assets/hero-simulation.jpg'

export default function Hero() {
  return (
  
    <section className="bg-slate-950 text-slate-100 px-6 py-20 md:py-28">
      <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-12 items-center">
        <div>
          <h1 className="text-4xl md:text-5xl font-bold leading-tight mb-6" style={{ fontFamily: 'Space Grotesk' }}>
            Simule experimentos de física de partículas de forma simples e rápida
          </h1>
          <p className="text-slate-400 text-lg mb-8">
            Uma plataforma web para simulação e visualização de interações entre partículas subatômicas, com base no toolkit Geant4 do CERN.
          </p>
          <a href="#simulador" className="inline-block bg-cyan-400 text-slate-950 font-semibold px-6 py-3 rounded-lg hover:bg-cyan-300 transition">
            Acesse a simulação
          </a>
        </div>
        <div className="aspect-square bg-slate-900 border border-slate-800 rounded-xl overflow-hidden flex items-center justify-center">
  <img src={heroImage} alt="Simulação de física de partículas" className="w-full h-full object-contain" />
</div>
      </div>
    </section>
  )
}
