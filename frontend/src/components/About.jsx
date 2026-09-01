import Hero from '../components/home/Hero'
export default function About() {
  return (
    <Hero />
    <section className="bg-slate-900 text-slate-100 px-6 py-20">
      <div className="max-w-4xl mx-auto text-center">
        <h2
          className="text-3xl md:text-4xl font-bold mb-6"
          style={{ fontFamily: 'Space Grotesk' }}
        >
          Simulação de física de partículas direto no navegador
        </h2>
        <p className="text-slate-400 text-lg leading-relaxed">
          Uma plataforma web para simulação e visualização de interações entre
          partículas subatômicas, desenvolvida com base no toolkit Geant4 do
          CERN. Com ela, é possível configurar partículas, definir materiais e
          geometrias, e analisar os resultados — sem precisar instalar nada.
        </p>

        <div className="grid sm:grid-cols-2 gap-4 mt-10 text-left">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-5">
            <h3 className="font-semibold mb-2 text-cyan-400">Ensino e pesquisa</h3>
            <p className="text-slate-400 text-sm">
              Exploração de fenômenos físicos em contexto acadêmico.
            </p>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-5">
            <h3 className="font-semibold mb-2 text-cyan-400">Prototipagem rápida</h3>
            <p className="text-slate-400 text-sm">
              Configuração e teste de simulações sem ambiente local instalado.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
