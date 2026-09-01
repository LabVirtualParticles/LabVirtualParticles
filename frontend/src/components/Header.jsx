export default function Header() {
  return (
    <header className="w-full bg-slate-950 text-slate-100 px-6 py-4 flex items-center justify-between border-b border-slate-800">
      <div className="font-bold text-lg tracking-tight" style={{ fontFamily: 'Space Grotesk' }}>
        LabVirtual
      </div>
      {/* <nav className="hidden md:flex gap-6 text-sm text-slate-300">
        <a href="#" className="hover:text-cyan-400 transition">Física Médica</a>
        <a href="#" className="hover:text-cyan-400 transition">Astrofísica</a>
        <a href="#" className="hover:text-cyan-400 transition">Nuclear</a>
        <a href="https://github.com/helen1789/LabVirtualParticles" className="hover:text-cyan-400 transition">GitHub</a>
      </nav> */}
    </header>
  )
}
