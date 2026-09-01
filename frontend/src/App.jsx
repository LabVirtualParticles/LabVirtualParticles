import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import SimulationExample from './pages/SimulationExample'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/simulacoes/rutherford" element={<SimulationExample />} />
    </Routes>
  )
}
