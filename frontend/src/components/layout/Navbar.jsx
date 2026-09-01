import { useEffect, useRef, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Navbar.css';

// Edit this list to match your real simulation catalog — the dropdown
// below is generated entirely from this array, so adding, renaming or
// removing a category never requires touching the markup.
const SIMULATION_SECTIONS = [
  {
    label: 'Física de Partículas',
    items: [{ label: 'Espalhamento de Rutherford', path: '/simulacoes/rutherford' }],
  },
  {
    label: 'Física Nuclear',
    items: [],
  },
  {
    label: 'Astrofísica',
    items: [],
  },
  {
    label: 'Física Médica',
    items: [],
  },
];

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const closeTimer = useRef(null);
  const wrapperRef = useRef(null);
  const location = useLocation();

  // Close the dropdown whenever the route changes. Adjusting state
  // directly during render (React's recommended pattern for this case)
  // instead of in a useEffect avoids an extra render pass.
  const [lastPathname, setLastPathname] = useState(location.pathname);
  if (location.pathname !== lastPathname) {
    setLastPathname(location.pathname);
    setOpen(false);
  }

  // Close on outside click and on Escape.
  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setOpen(false);
      }
    }
    function handleKeyDown(event) {
      if (event.key === 'Escape') setOpen(false);
    }
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  function openNow() {
    clearTimeout(closeTimer.current);
    setOpen(true);
  }

  function closeSoon() {
    // Small delay so the pointer can travel from the button down into
    // the panel without the dropdown closing in between.
    closeTimer.current = setTimeout(() => setOpen(false), 150);
  }

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

          <div
            className="navbar__dropdown-wrapper"
            ref={wrapperRef}
            onMouseEnter={openNow}
            onMouseLeave={closeSoon}
          >
            <button
              type="button"
              className="navbar__link navbar__dropdown-trigger"
              aria-haspopup="true"
              aria-expanded={open}
              onClick={() => setOpen((prev) => !prev)}
            >
              Simulações
              <span className="navbar__caret" aria-hidden="true" />
            </button>

            {open && (
              <div className="navbar__dropdown" role="menu">
                {SIMULATION_SECTIONS.map((section) => (
                  <div key={section.label} className="navbar__dropdown-group">
                    <span className="navbar__dropdown-heading">{section.label}</span>
                    {section.items.length > 0 ? (
                      <ul>
                        {section.items.map((item) => (
                          <li key={item.path}>
                            <Link to={item.path} role="menuitem">
                              {item.label}
                            </Link>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <span className="navbar__dropdown-soon">Em breve</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          <Link to="/contato" className="navbar__link">
            Contato
          </Link>
        </nav>
      </div>
    </header>
  );
}
