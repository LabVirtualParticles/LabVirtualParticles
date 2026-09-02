import { Link } from 'react-router-dom';
import Navbar from '../components/layout/Navbar';
import { SIMULATION_CATEGORIES } from '../data/simulationCategories';
import './SimulationsMap.css';

// Landing page for "Simulações" in the navbar — replaces the old
// hover dropdown. Shows one card per category fanning out from the
// center title; click a card to go to its catalog (or, for a
// category whose `directPath` is set, straight to that simulation).
function categoryHref(category) {
  return category.directPath ?? `/simulacoes/categoria/${category.slug}`;
}

export default function SimulationsMap() {
  return (
    <>
      <Navbar />
      <main className="sim-map">
        <div className="sim-map__diagram">
          <svg
            className="sim-map__lines"
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <path d="M 30 25 C 38 35, 42 42, 47 47" />
            <path d="M 70 25 C 62 35, 58 42, 53 47" />
            <path d="M 30 75 C 38 65, 42 58, 47 53" />
            <path d="M 70 75 C 62 65, 58 58, 53 53" />
          </svg>

          <div className="sim-map__center">
            <h1 className="sim-map__center-title">Simulações</h1>
            <p className="sim-map__center-hint">
              Escolha uma área para ver as simulações disponíveis.
            </p>
          </div>

          {SIMULATION_CATEGORIES.map((category, index) => (
            <Link
              key={category.slug}
              to={categoryHref(category)}
              className={`sim-map__card sim-map__card--${index}`}
            >
              <span className="sim-map__card-title">{category.label}</span>
              <span className="sim-map__card-rule" aria-hidden="true" />
              {category.items.length === 0 && !category.directPath && (
                <span className="sim-map__card-soon">Em breve</span>
              )}
            </Link>
          ))}
        </div>
      </main>
    </>
  );
}
