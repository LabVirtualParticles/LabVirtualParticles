"""
app.py

API mínima (FastAPI) para a pré-banca: recebe os parâmetros de uma
simulação, roda o Geant4 em modo batch via geant4_runner, converte a
geometria (.gdml) e lê as trajetórias (.json, já escritas pelo C++ - ver
TrajectoryRecorder) e devolve tudo numa resposta só.

Escopo deliberadamente reduzido pra essa fase (ver decisões registradas no
projeto): sem fila de jobs, sem autenticação, sem catálogo em banco de
dados - roda a simulação de forma síncrona (a requisição HTTP espera o
Geant4 terminar) porque a plataforma ainda não está pública e é uso
local/demonstração. Isso é dívida técnica CONSCIENTE, não esquecimento -
ver PENDENTE.md / o doc do projeto para o que falta pra produção.

Como rodar localmente:

    pip install fastapi "uvicorn[standard]" --break-system-packages
    uvicorn app:app --reload --port 8000

Depois:

    curl -X POST http://localhost:8000/simulations/rutherford/run \
         -H "Content-Type: application/json" \
         -d '{"particle": "alpha", "energy_MeV": 5, "pos_x_cm": 10, "pos_y_cm": 0,
              "pos_z_cm": 0, "dir_x": -1, "dir_y": 0, "dir_z": 0, "n_events": 1000}'
"""

from __future__ import annotations

import json
import math
import logging
import os
import random
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from geant4_runner import Geant4Runner, SimulationRequest
from geometry_converter import GdmlConversionError, parse_gdml

logger = logging.getLogger("app")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(title="Laboratório Virtual de Física de Partículas - backend (pré-banca)")

# CORS liberado geral por ora (uso local/demo, sem dados sensíveis). Restringir
# para o domínio real do frontend quando a plataforma for exposta publicamente.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# "Catálogo" de simulações disponíveis - hardcoded por ora.
#
# Caminhos ajustados em 2026-08-30 para a máquina real de Lorenzo, depois
# de validar a Fase 1 (C++) rodando de verdade (ver doc do projeto:
# backend-execucao-batch-geant4.md).
# --------------------------------------------------------------------------- #

# Isótopos emissores de pósitron usados em PET (para o B3a): nome -> (Z, A).
ISOTOPES: Dict[str, tuple] = {
    "F18": (9, 18),
    "C11": (6, 11),
    "N13": (7, 13),
    "O15": (8, 15),
}

# O código do B3a fica neste mesmo repositório (simulations/B3a-geantino),
# então o caminho padrão vale em qualquer máquina que tenha o repo — só
# precisa compilar lá dentro (build/). GEANTINO_B3A_DIR ainda sobrescreve.
B3A_DIR = os.environ.get(
    "GEANTINO_B3A_DIR",
    str(Path(__file__).resolve().parent.parent / "simulations" / "B3a-geantino"),
)

SIMULATIONS: Dict[str, Dict[str, Any]] = {
    "rutherford": {
        "label": "Espalhamento de Rutherford",
        "executable": "/home/lorenzo/Scientific/geant4/ProjetoIntegrador/FolhaDeOuro/build/programa",
        "macro_template": "/home/lorenzo/Scientific/geant4/ProjetoIntegrador/FolhaDeOuro/macros/run_batch.mac.tmpl",
        "geometry_filename": "geometria.gdml",
        "trajectories_filename": "trajetorias.json",
        "default_params": {
            "particle": "alpha",
            "energy_MeV": 5,
            "pos_x_cm": 10,
            "pos_y_cm": 0,
            "pos_z_cm": 0,
            "dir_x": -1,
            "dir_y": 0,
            "dir_z": 0,
            "n_events": 1000,
        },
        # Faixas de validação - ver nota de segurança mais abaixo: qualquer
        # parâmetro fora daqui é rejeitado ANTES de virar texto na macro.
        # `None` no lugar do máximo = sem limite superior (pedido do
        # Lorenzo, nov/2026). Os mínimos ficam porque abaixo deles o Geant4
        # não roda (energia precisa ser > 0 e pelo menos 1 evento).
        "param_ranges": {
            "energy_MeV": (0.001, None),
            "n_events": (1, None),
        },
        "allowed_particles": {"alpha", "e-", "e+", "gamma", "proton"},
    },
    # Exemplo oficial B3a do Geant4 (scanner PET), adaptado para batch pelo
    # Geantino Labs — código em simulations/B3a-geantino/ (ver o README de
    # lá). Compilar com: cmake -S . -B build && cmake --build build.
    "b3a": {
        "label": "PET — exemplo B3a do Geant4",
        "executable": f"{B3A_DIR}/build/geantinoB3a",
        "macro_template": f"{B3A_DIR}/macros/run_batch.mac.tmpl",
        "geometry_filename": "geometria.gdml",
        "trajectories_filename": "trajetorias.json",
        "results_filename": "resultados.json",
        # Volumes de ar que só agrupam os cristais (no original já eram
        # invisíveis no visualizador do Geant4). Sem eles a cena fica mais
        # leve e os cristais aparecem.
        "hidden_volumes": ["Ring", "Detector"],
        "default_params": {
            "isotope": "F18",
            "pos_x_cm": 4,
            "pos_y_cm": 4,
            "pos_z_cm": 4,
            "source_size_cm": 1,
            "n_events": 200,
        },
        # Fonte tem que ficar dentro do mundo (±40 cm em x/y, ±32 cm em z);
        # o paciente é um cilindro de raio 8 cm e meia-altura 5 cm.
        "param_ranges": {
            "pos_x_cm": (-30, 30),
            "pos_y_cm": (-30, 30),
            "pos_z_cm": (-30, 30),
            "source_size_cm": (0, 10),
            "n_events": (1, None),
        },
        "choices": {"isotope": set(ISOTOPES)},
    },
}

# Sem isso, o Geant4Runner sobe o processo do "programa" sem G4LEDATA/
# G4NEUTRONHPDATA/etc. definidos no ambiente -- funciona "por acaso" se o
# uvicorn for iniciado num shell que já deu source no geant4.sh (ex.: via
# .bashrc), mas falha silenciosamente ou dá erro de dados ausentes se for
# iniciado de outro jeito (systemd, IDE, outro terminal). Setando aqui, o
# Geant4Runner sourcia e cacheia sozinho, independente de como o uvicorn
# foi chamado.
GEANT4_ENV_SCRIPT: Optional[str] = "/home/lorenzo/Scientific/geant4/install/bin/geant4.sh"

runner = Geant4Runner(geant4_env_script=GEANT4_ENV_SCRIPT)


# --------------------------------------------------------------------------- #
# Schemas da API
# --------------------------------------------------------------------------- #

class RunSimulationRequest(BaseModel):
    particle: Optional[str] = None
    energy_MeV: Optional[float] = None
    pos_x_cm: Optional[float] = None
    pos_y_cm: Optional[float] = None
    pos_z_cm: Optional[float] = None
    dir_x: Optional[float] = None
    dir_y: Optional[float] = None
    dir_z: Optional[float] = None
    n_events: Optional[int] = Field(default=None, ge=1)
    # Seed do gerador de números aleatórios do Geant4 (/random/setSeeds no
    # macro). Opcional: se o usuário não mandar, o backend sorteia uma e
    # devolve em `seed_used` na resposta — é isso que permite o relatório
    # do dashboard registrar qual seed gerou cada simulação, e também
    # permite reproduzir a mesma simulação de novo passando a mesma seed.
    seed1: Optional[int] = Field(default=None, ge=0, le=900000000)
    seed2: Optional[int] = Field(default=None, ge=0, le=900000000)
    # B3a (PET)
    isotope: Optional[str] = None
    source_size_cm: Optional[float] = None


class SimulationSummary(BaseModel):
    id: str
    label: str
    default_params: Dict[str, Any]


class RunSimulationResponse(BaseModel):
    run_id: str
    duration_seconds: float
    params_used: Dict[str, Any]
    seed_used: Dict[str, int]
    geometry: Dict[str, Any]
    trajectories: List[Dict[str, Any]]
    # Resultados numéricos próprios de cada simulação (ex.: no B3a, eventos
    # em coincidência, dose e linhas de resposta). None quando a simulação
    # não grava um arquivo de resultados (Rutherford).
    results: Optional[Dict[str, Any]] = None
    stdout_tail: str


# --------------------------------------------------------------------------- #
# Validação dos parâmetros do usuário ANTES de virarem texto na macro.
#
# IMPORTANTE (segurança): a macro é montada por substituição de texto
# (string.Template) em cima do valor que o usuário mandou. Sem validar
# aqui, um valor malicioso poderia injetar comandos extras na macro (por
# exemplo, um "energy_MeV" contendo uma quebra de linha seguida de outro
# comando UI). Isso NÃO substitui rodar o binário sandboxed/isolado antes
# de expor isso publicamente (ver pendências de produção já discutidas) -
# é só a primeira barreira, e é obrigatória mesmo pra demo local.
# --------------------------------------------------------------------------- #

def _validate_and_merge_params(sim_id: str, sim_config: Dict[str, Any], req: RunSimulationRequest) -> Dict[str, Any]:
    defaults = sim_config["default_params"]
    params = dict(defaults)
    provided = req.model_dump(exclude_none=True)
    # Só aceita parâmetros que a simulação conhece (+ seeds) — um campo de
    # outra simulação (ex. "particle" mandado pro B3a) é ignorado em vez de
    # virar texto na macro.
    params.update({k: v for k, v in provided.items() if k in defaults or k in ("seed1", "seed2")})

    if "particle" in defaults:
        allowed_particles = sim_config.get("allowed_particles")
        if allowed_particles and params["particle"] not in allowed_particles:
            raise HTTPException(
                status_code=422,
                detail=f"Partícula '{params['particle']}' não permitida para '{sim_id}'. Opções: {sorted(allowed_particles)}",
            )
        if not isinstance(params.get("particle"), str) or "\n" in params["particle"] or " " in params["particle"]:
            raise HTTPException(status_code=422, detail="Parâmetro 'particle' inválido")

    for key, allowed in sim_config.get("choices", {}).items():
        if params.get(key) not in allowed:
            raise HTTPException(
                status_code=422,
                detail=f"Parâmetro '{key}'={params.get(key)!r} inválido para '{sim_id}'. Opções: {sorted(allowed)}",
            )

    ranges = sim_config.get("param_ranges", {})
    for key, (low, high) in ranges.items():
        value = params.get(key)
        # isfinite: sem limite superior, "Infinity"/NaN (que o JSON do
        # Python aceita) passariam e virariam "inf"/"nan" na macro.
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or (low is not None and value < low)
            or (high is not None and value > high)
        ):
            faixa = f"[{low}, {high if high is not None else '∞'}]"
            raise HTTPException(
                status_code=422,
                detail=f"Parâmetro '{key}'={value!r} fora da faixa permitida {faixa}",
            )

    # Todo parâmetro que não é texto escolhido de uma lista tem que ser
    # número finito (vale para pos/dir do Rutherford e qualquer outro).
    text_keys = {"particle"} | set(sim_config.get("choices", {}))
    for key, value in params.items():
        if key in text_keys or key in ("seed1", "seed2"):
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise HTTPException(status_code=422, detail=f"Parâmetro '{key}' deve ser numérico, recebi {value!r}")

    return params


def _macro_params(sim_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Valores extras que só a macro precisa (não vão em params_used)."""
    extra: Dict[str, Any] = {}
    if "isotope" in params:
        extra["ion_Z"], extra["ion_A"] = ISOTOPES[params["isotope"]]
    return extra


def _hide_volumes(geometry: Dict[str, Any], hidden: List[str]) -> Dict[str, Any]:
    # O G4GDMLParser acrescenta o endereço ao nome (ex. "Ring0x55d1..."),
    # por isso compara o nome lógico sem esse sufixo.
    if not hidden:
        return geometry
    hidden_set = set(hidden)
    volumes = [
        v for v in geometry.get("volumes", [])
        if re.sub(r"0x[0-9a-fA-F]+$", "", v.get("name", "")) not in hidden_set
    ]
    return {**geometry, "volumes": volumes}


# --------------------------------------------------------------------------- #
# Rotas
# --------------------------------------------------------------------------- #

@app.get("/simulations", response_model=List[SimulationSummary])
def list_simulations() -> List[SimulationSummary]:
    return [
        SimulationSummary(id=sim_id, label=cfg["label"], default_params=cfg["default_params"])
        for sim_id, cfg in SIMULATIONS.items()
    ]


@app.post("/simulations/{sim_id}/run", response_model=RunSimulationResponse)
def run_simulation(sim_id: str, req: RunSimulationRequest) -> RunSimulationResponse:
    sim_config = SIMULATIONS.get(sim_id)
    if sim_config is None:
        raise HTTPException(status_code=404, detail=f"Simulação '{sim_id}' não encontrada")

    params = _validate_and_merge_params(sim_id, sim_config, req)

    # Sorteia a seed quando o usuário não mandou uma própria. Faixa
    # 0..900000000 (abaixo do limite de 32 bits que o Geant4/CLHEP espera
    # para /random/setSeeds) — guardamos os dois valores sorteados/usados
    # em `seed_used` na resposta, não só o que foi passado, porque só aí
    # dá pra saber a seed real mesmo quando o usuário não informou uma.
    seed1 = params.pop("seed1", None)
    seed2 = params.pop("seed2", None)
    if seed1 is None:
        seed1 = random.randint(0, 900_000_000)
    if seed2 is None:
        seed2 = random.randint(0, 900_000_000)
    params["seed1"] = seed1
    params["seed2"] = seed2
    seed_used = {"seed1": seed1, "seed2": seed2}

    output_patterns = [sim_config["geometry_filename"], sim_config["trajectories_filename"]]
    if sim_config.get("results_filename"):
        output_patterns.append(sim_config["results_filename"])

    sim_request = SimulationRequest(
        executable=sim_config["executable"],
        macro_template=sim_config["macro_template"],
        params={**params, **_macro_params(sim_id, params)},
        output_patterns=output_patterns,
        timeout_seconds=120.0,
    )

    result = runner.run(sim_request)

    if not result.success:
        logger.error("Simulação '%s' falhou (run_id=%s): %s", sim_id, result.run_id, result.error)
        raise HTTPException(
            status_code=502,
            detail={
                "message": "A simulação não terminou com sucesso.",
                "error": result.error,
                "stderr_tail": result.stderr[-2000:],
            },
        )

    work_dir = Path(result.work_dir)
    geometry_path = work_dir / sim_config["geometry_filename"]
    trajectories_path = work_dir / sim_config["trajectories_filename"]

    if not geometry_path.is_file():
        raise HTTPException(status_code=502, detail=f"Simulação terminou mas não gerou '{geometry_path.name}'")
    if not trajectories_path.is_file():
        raise HTTPException(status_code=502, detail=f"Simulação terminou mas não gerou '{trajectories_path.name}'")

    try:
        geometry = parse_gdml(geometry_path)
    except GdmlConversionError as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao interpretar a geometria gerada: {exc}") from exc

    geometry = _hide_volumes(geometry, sim_config.get("hidden_volumes", []))

    try:
        trajectories_data = json.loads(trajectories_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao ler trajetórias geradas: {exc}") from exc

    results = None
    if sim_config.get("results_filename"):
        results_path = work_dir / sim_config["results_filename"]
        if not results_path.is_file():
            raise HTTPException(status_code=502, detail=f"Simulação terminou mas não gerou '{results_path.name}'")
        try:
            results = json.loads(results_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=502, detail=f"Falha ao ler resultados gerados: {exc}") from exc

    return RunSimulationResponse(
        run_id=result.run_id,
        duration_seconds=result.duration_seconds,
        params_used=params,
        seed_used=seed_used,
        geometry=geometry,
        trajectories=trajectories_data.get("trajectories", []),
        results=results,
        stdout_tail=result.stdout[-2000:],
    )


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}
