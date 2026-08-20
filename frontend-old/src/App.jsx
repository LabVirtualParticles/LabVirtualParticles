import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import Menu from './components/Menu'
import Inicio from './pages/Inicio'
import Simulacoes from './pages/Simulacoes'
import Rutherford from './pages/Rutherford'
import Sobre from './pages/Sobre'
import Login from './pages/Login'

function Layout() {
  const location = useLocation()
  const semMenu = location.pathname.startsWith('/simulacao')
  return (
    <>
      {!semMenu && <Menu />}
      <Routes>
        <Route path="/" element={<Inicio />} />
        <Route path="/simulacoes" element={<Simulacoes />} />
        <Route path="/simulacao/rutherford" element={<Rutherford />} />
        <Route path="/sobre" element={<Sobre />} />
        <Route path="/login" element={<Login />} />
      </Routes>
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  )
}

