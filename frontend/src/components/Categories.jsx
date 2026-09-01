import Hero from '../components/home/Hero'
const categories = [
  { name: 'Física Médica', desc: 'Simulações de radioterapia e imagem médica' },
  { name: 'Astrofísica', desc: 'Interações de partículas em ambientes cósmicos' },
  { name: 'Física Nuclear', desc: 'Decaimento, fissão e reações nucleares' },
]

export default function Categories() {
  return (
    <Hero />
    <section className="bg-slate-950 text-slate-100 px-6 py-20">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-2xl md:text-3xl font-bold mb-10 text-center" style={{ fontFamily: 'Space Grotesk' }}>
          Explore por área
        </h2>
        <div className="grid sm:grid-cols-3 gap-6">
          {categories.map((cat) => (
            <a key={cat.name} href="#" className="block bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-cyan-400 transition">
              <h3 className="font-semibold text-lg mb-2">{cat.name}</h3>
              <p className="text-slate-400 text-sm">{cat.desc}</p>
              <span className="inline-block mt-4 text-xs text-slate-600">Em breve</span>
            </a>
          ))}
        </div>
      </div>
    </section>
  )
}
