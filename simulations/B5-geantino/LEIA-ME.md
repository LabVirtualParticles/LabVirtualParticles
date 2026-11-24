# B5 para o Geantino Labs — espectrômetro de dois braços

Versão do exemplo oficial **B5** do Geant4 (`examples/basic/B5`) adaptada
para o backend do site Geantino Labs: só modo batch, sem interface gráfica,
gravando os arquivos que o site lê. O `README` em inglês, ao lado, é o do
exemplo original.

## Créditos

O exemplo B5 — geometria do espectrômetro, materiais, detectores sensíveis,
hits, lista de física (FTFP_BERT) e gerador de partículas — é da
**Colaboração Geant4** e faz parte da distribuição oficial do Geant4
(https://geant4.web.cern.ch), sob a Licença de Software do Geant4
(https://cern.ch/geant4/license). O aviso de licença foi mantido em todos os
arquivos derivados do original.

Referências para citar o Geant4:

- S. Agostinelli et al., "Geant4 — a simulation toolkit", *Nucl. Instrum.
  Meth. A* 506 (2003) 250–303.
- J. Allison et al., "Geant4 developments and applications", *IEEE Trans.
  Nucl. Sci.* 53 (2006) 270–278.
- J. Allison et al., "Recent developments in Geant4", *Nucl. Instrum. Meth.
  A* 835 (2016) 186–225.

Adaptações: Geantino Labs (IFPR — Centro de Referência Biopark, Toledo),
novembro de 2026.

## O que mudou em relação ao B5 original

| Arquivo | Mudança |
|---|---|
| `geantinoB5.cc` (era `exampleB5.cc`) | Só modo batch; sem `G4UIExecutive`/`G4VisExecutive`; run manager sequencial |
| `RunAction` | Sem histogramas/ntuple ROOT; grava `geometria.gdml`, `trajetorias.json` e `resultados.json` |
| `EventAction` | As mesmas grandezas da ntuple (hits nas câmaras, energia nos calorímetros, tempos nos hodoscópios), por evento, + partícula e momento; tempo = acerto mais cedo de cada hodoscópio |
| `ActionInitialization.cc` | RunAction antes do EventAction; SteppingAction das trajetórias |
| `DetectorConstruction.cc` | Passo máximo no ímã: 1 m → 2 cm (só para a curva ter pontos no desenho) |
| `SteppingAction`, `TrajectoryRecorder` | Novos. Grava a primária e secundárias ≥ 20 MeV (sem nêutrons e neutrinos); `/geantino/trajectories/minEnergy` muda o corte |
| `macros/` | `run_batch.mac.tmpl` (backend) e `run_batch_exemplo.mac` (teste) |

Física, geometria, materiais, detectores sensíveis, hits e o gerador de
partículas (`/B5/generator/...`, `/B5/field/value`, `/B5/detector/armAngle`)
não foram alterados.

## Compilar e testar

```bash
source /caminho/do/geant4/install/bin/geant4.sh
cmake -S . -B build
cmake --build build -j4
cd build && ./geantinoB5 run_batch_exemplo.mac
```

No fim aparece `[Geantino] 20 eventos; ... pontos de trajetoria`.

## resultados.json

`n_events`, `trajectories_truncated` e `events`: para cada evento,
`particle`, `momentum_MeV`, `dc1_hits`, `dc2_hits`, `em_edep_MeV`,
`had_edep_MeV`, `em_cells`, `had_cells`, `t1_ns` e `t2_ns` (`null` quando o
hodoscópio não foi atingido).
