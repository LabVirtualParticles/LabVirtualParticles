# Geantino Labs

Plataforma web para simulação e visualização de experimentos de física de
partículas direto no navegador, sem precisar instalar nada localmente. O
objetivo é rodar simulações apoiadas no **Geant4** — o toolkit científico de
simulação de partículas usado no CERN — e exibir os resultados em uma cena
3D interativa.

Projeto acadêmico do **IFPR**.

> Este repositório contém, por enquanto, apenas o **front-end**
> (`frontend/`). A integração com o backend/Geant4 ainda não existe: os
> dados de simulação exibidos hoje são gerados localmente por uma função
> mock, só para a interface ter o que renderizar enquanto o motor de
> cálculo real não é conectado.

## Stack

- **React 19** + **Vite 8**
- **React Router 7** — roteamento entre páginas
- **Tailwind CSS 4** — utilitários de estilo (usados em parte das páginas)
- **Three.js** + **@react-three/fiber** + **@react-three/drei** — renderização 3D da cena de simulação
- **ESLint** — lint do código

## Estrutura do projeto

```
LabVirtualParticles/
└── frontend/
    ├── public/
    │   ├── fonts/            # Fontes auto-hospedadas (Ykar, Basteleur, Fraunces)
    │   └── videos/           # Vídeo de fundo do Hero
    └── src/
        ├── components/       # Componentes de UI reutilizáveis
        │   ├── layout/        (Navbar)
        │   └── home/          (Hero)
        ├── features/
        │   └── simulation-demo/   # Núcleo da página de simulação
        │       ├── ParametersPanel.jsx    # Formulário gerado a partir de um schema JSON
        │       ├── SimulationViewer.jsx   # Cena 3D (Three.js)
        │       ├── useSimulationRun.js    # Hook de estado + simulação mock
        │       └── data/                  # JSONs de exemplo (parâmetros e resultado)
        ├── pages/             # Páginas roteadas (Home, SimulationExample, Contact)
        ├── styles/            # tokens.css (design tokens), global.css, fonts.css
        └── App.jsx            # Definição das rotas
```

## Rodando o projeto localmente

Pré-requisitos: [Node.js](https://nodejs.org/) 18+ e npm.

```bash
cd frontend
npm install
npm run dev
```

O Vite vai subir um servidor local (por padrão em `http://localhost:5173`).

### Outros comandos

```bash
npm run build     # build de produção (gera frontend/dist)
npm run preview   # serve o build de produção localmente
npm run lint      # roda o ESLint
```

## Rotas disponíveis

| Rota                       | Página                                          |
| --------------------------- | ------------------------------------------------ |
| `/`                         | Home — landing page do projeto                   |
| `/simulacoes/rutherford`    | Exemplo de simulação: Espalhamento de Rutherford |
| `/contato`                  | Página de contato / equipe                       |

Outras categorias (Física Nuclear, Astrofísica, Física Médica) já aparecem
no menu, marcadas como "Em breve" — ainda não têm simulações implementadas.

## Design tokens

As cores, tipografia e espaçamentos do projeto ficam centralizados em
`src/styles/tokens.css`. A paleta foi extraída do próprio render de
espalhamento de Rutherford usado no vídeo do Hero (fundo preto, feixe azul,
traço dourado), para que a interface pareça uma extensão da simulação em
vez de um tema genérico por cima dela.

## Como plugar o backend real (Geant4)

A função `runMockSimulation`, em
`src/features/simulation-demo/useSimulationRun.js`, é o único ponto que
precisa ser trocado por uma chamada real à API/Geant4. Ela deve resolver
com um objeto no mesmo formato de
`src/features/simulation-demo/data/result.example.json`
(`{ world, volumes, trajectories }`) — nenhum outro componente
(`SimulationViewer.jsx`, `ParametersPanel.jsx`) precisa mudar.

Para adicionar uma nova simulação, edite
`src/features/simulation-demo/data/parameters.example.json` (o schema que
gera o formulário automaticamente) e crie a rota correspondente em
`src/App.jsx`.
