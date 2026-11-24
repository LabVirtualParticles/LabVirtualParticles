# B3a para o Geantino Labs — PET (tomografia por emissão de pósitrons)

Versão do exemplo oficial **B3a** do Geant4 (`examples/basic/B3/B3a`)
adaptada para rodar no backend do site Geantino Labs: só modo batch, sem
interface gráfica, gravando os arquivos que o site lê.

## Créditos

O exemplo B3 — geometria do scanner, materiais, física, scorers e a
contagem de eventos — é da **Colaboração Geant4** e faz parte da
distribuição oficial do Geant4 (https://geant4.web.cern.ch). Ele é
distribuído sob a Licença de Software do Geant4
(https://cern.ch/geant4/license). O aviso de licença foi mantido em todos
os arquivos derivados do original.

Referência para citar o Geant4:

- S. Agostinelli et al., "Geant4 — a simulation toolkit", *Nucl. Instrum.
  Meth. A* 506 (2003) 250–303.
- J. Allison et al., "Geant4 developments and applications", *IEEE Trans.
  Nucl. Sci.* 53 (2006) 270–278.
- J. Allison et al., "Recent developments in Geant4", *Nucl. Instrum. Meth.
  A* 835 (2016) 186–225.

As adaptações para o site (lista abaixo) foram feitas pelo Geantino Labs
(IFPR — Centro de Referência Biopark, Toledo) em novembro de 2026.

## O que o exemplo simula

Um scanner PET simplificado: 9 anéis de 32 cristais de LSO (Lu₂SiO₅) em
volta de um "paciente" (cilindro de tecido cerebral, `G4_BRAIN_ICRP`).
Dentro do paciente fica uma fonte de **flúor-18** em repouso. O F18 decai
em O18 emitindo um pósitron; o pósitron se aniquila com um elétron e gera
dois fótons de 511 keV em sentidos opostos. Um evento é "bom" quando
exatamente dois cristais recebem mais de 500 keV — a coincidência que um
PET de verdade usa para formar a imagem. O exemplo também soma a dose
depositada no paciente.

## O que mudou em relação ao B3a original

| Arquivo | Mudança |
|---|---|
| `geantinoB3a.cc` (era `exampleB3a.cc`) | Só modo batch; sem `G4UIExecutive`, `G4VisExecutive` e `G4TScoreNtupleWriter`; run manager sequencial |
| `PrimaryGeneratorAction` | Centro e tamanho da região da fonte viram comandos (`/geantino/source/centre`, `/geantino/source/size`). Padrão igual ao original: (4, 4, 4) cm, cubo de 1 cm |
| `DetectorConstruction.cc` | Só acrescenta o scorer `edepRC` (energia por cristal com o anel separado) |
| `EventAction` | Nos eventos bons, registra a linha de resposta (LOR) entre os dois cristais; em todos os eventos, manda a energia de cada cristal atingido para o espectro. Contagem e dose idênticas ao original |
| `RunAction` | Grava `geometria.gdml`, `trajetorias.json` e `resultados.json` |
| `CrystalScorer`, `TrajectoryRecorder`, `SteppingAction` | Novos (Geantino Labs) |
| `macros/` | `run_batch.mac.tmpl` (preenchida pelo backend) e `run_batch_exemplo.mac` (teste manual) |

Física (`PhysicsList`), geometria, materiais e o `StackingAction` não foram
alterados.

## Compilar e testar

Precisa de um Geant4 compilado com GDML (`GEANT4_USE_GDML=ON`).

```bash
source /caminho/do/geant4/install/bin/geant4.sh
cmake -S . -B build
cmake --build build -j4
cd build && ./geantinoB3a run_batch_exemplo.mac
```

Ao final aparecem, na pasta `build/`, os três arquivos e a linha
`[Geantino] 100 eventos; ... linhas de resposta.`

## Arquivos de saída

- `geometria.gdml` — geometria completa (o backend esconde os volumes de ar
  `Ring` e `Detector`, que no original já eram invisíveis).
- `trajetorias.json` — mesmo formato do FolhaDeOuro. Limite de 300 mil
  pontos (`"truncated": true` quando passa).
- `resultados.json` — `n_events`, `source_particle`, `good_events`,
  `good_fraction`, `dose_Gy`, `energy_threshold_keV`,
  `trajectories_truncated`, `lines_of_response` (evento, centros dos dois
  cristais em cm e energia em cada um, em keV) e `crystal_spectrum`
  (quantos cristais receberam cada faixa de 10 keV, de 0 a 1100 keV, em
  todos os eventos; `overflow` = acima disso).
