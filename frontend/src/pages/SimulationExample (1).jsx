import Navbar from '../components/layout/Navbar';
import ParametersPanel from '../features/simulation-demo/ParametersPanel';
import SimulationViewer from '../features/simulation-demo/SimulationViewer';
import { useSimulationRun } from '../features/simulation-demo/useSimulationRun';
import schema from '../features/simulation-demo/data/parameters.example.json';
import '../features/simulation-demo/simulation-demo.css';

// Reference page for running a simulation end to end: parameter fields
// on the left, 3D viewer + actions on the right. Everything here is
// wired to placeholder data — the two places to touch when Geant4 is
// ready are data/parameters.example.json (the form fields) and
// useSimulationRun.js (the runMockSimulation function).
export default function SimulationExample() {
  const { values, setField, status, data, run, exportData } = useSimulationRun(schema);

  return (
    <>
      <Navbar />
      <main className="sim-page">
        <header className="sim-page__header">
          <h1>{schema.title}</h1>
          <p>
            Página de referência para executar uma simulação: os campos de parâmetros e a
            renderização já estão prontos, falta apenas ligar <code>useSimulationRun</code> ao
            backend real do Geant4.
          </p>
        </header>

        <div className="sim-page__grid">
          <ParametersPanel schema={schema} values={values} onChange={setField} />

          <div className="sim-page__stage">
            <SimulationViewer data={data} status={status} />
            <div className="sim-page__actions">
              <button
                type="button"
                className="sim-page__button sim-page__button--primary"
                onClick={run}
                disabled={status === 'running'}
              >
                {status === 'running' ? 'Simulando…' : 'Simular'}
              </button>
              <button
                type="button"
                className="sim-page__button"
                onClick={exportData}
                disabled={status !== 'done'}
              >
                Exportar dados
              </button>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
