import { Link } from 'react-router-dom';
import './Navbar.css';

export default function Navbar() {
  return (
    <header className="navbar">
      <div className="navbar__inner">
        <Link to="/" className="navbar__brand">
          Geantino Labs
        </Link>

        <nav className="navbar__nav" aria-label="Principal">
          <Link to="/sobre" className="navbar__link">
            Sobre
          </Link>

          <Link to="/simulacoes" className="navbar__link">
            Simulações
          </Link>

          <Link to="/contato" className="navbar__link">
            Contato
          </Link>
        </nav>
      </div>
    </header>
  );
}
