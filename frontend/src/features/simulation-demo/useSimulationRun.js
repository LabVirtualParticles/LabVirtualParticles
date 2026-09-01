import { useCallback, useState } from 'react';
import resultShape from './data/result.example.json';

function defaultsFromSchema(schema) {
  return schema.fields.reduce((acc, field) => {
    acc[field.id] = field.default;
    return acc;
  }, {});
}

function randomInRange(min, max) {
  return Math.random() * (max - min) + min;
}

/**
 * Placeholder trajectory generator — this is NOT a physics engine, just
 * visual filler so the viewer has something to render before Geant4 is
 * wired up.
 *
 * *** This is the function to replace when you integrate the backend. ***
 * Swap its body for a call to your API (e.g. POST the current
 * parameters, poll or await the response), and resolve with an object
 * in the same shape as data/result.example.json. SimulationViewer.jsx
 * and ParametersPanel.jsx do not need to change.
 */
function runMockSimulation(params) {
  const beamCount = Number(params.beamCount) || 200;
  const energy = Number(params.energy) || 5;
  const scatterCount = Math.min(24, Math.max(4, Math.round(beamCount / 40)));

  const trajectories = [{ id: 'beam', color: '#2F5DFF', points: [[0, 0, -180], [0, 0, -2]] }];

  for (let i = 0; i < scatterCount; i += 1) {
    const spread = energy < 3 ? 1.4 : 1;
    const angle = randomInRange(-70, 70) * spread;
    const azimuth = randomInRange(0, Math.PI * 2);
    const distance = randomInRange(90, 170);
    const rad = (angle * Math.PI) / 180;
    const x = Math.sin(rad) * Math.cos(azimuth) * distance;
    const y = Math.sin(rad) * Math.sin(azimuth) * distance;
    const z = Math.cos(rad) * distance;

    trajectories.push({
      id: `scatter-${i}`,
      color: Math.abs(angle) > 40 ? '#E3B23C' : '#2F5DFF',
      points: [
        [0, 0, -2],
        [x, y, z],
      ],
    });
  }

  return new Promise((resolve) => {
    setTimeout(() => resolve({ ...resultShape, trajectories }), 900);
  });
}

export function useSimulationRun(schema) {
  const [values, setValues] = useState(() => defaultsFromSchema(schema));
  const [status, setStatus] = useState('idle'); // idle | running | done
  const [data, setData] = useState(resultShape);

  const setField = useCallback((id, value) => {
    setValues((prev) => ({ ...prev, [id]: value }));
  }, []);

  const run = useCallback(async () => {
    setStatus('running');
    const next = await runMockSimulation(values);
    setData(next);
    setStatus('done');
  }, [values]);

  const exportData = useCallback(() => {
    const payload = { simulationId: schema.simulationId, parameters: values, result: data };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${schema.simulationId ?? 'simulacao'}-resultado.json`;
    link.click();
    URL.revokeObjectURL(url);
  }, [schema.simulationId, values, data]);

  return { values, setField, status, data, run, exportData };
}
