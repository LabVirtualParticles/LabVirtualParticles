import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import SimulationsMap from './pages/SimulationsMap'
import SimulationCatalog from './pages/SimulationCatalog'
import SimulationExample from './pages/SimulationExample'
import Contact from './pages/Contact'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/simulacoes" element={<SimulationsMap />} />
      <Route path="/simulacoes/categoria/:slug" element={<SimulationCatalog />} />
      <Route path="/simulacoes/rutherford" element={<SimulationExample />} />
      <Route path="/contato" element={<Contact />} />
    </Routes>
  )
}
