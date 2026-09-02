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

import logging
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
        "param_ranges": {
            "energy_MeV": (0.001, 20.0),
            "n_events": (1, 20000),
        },
        "allowed_particles": {"alpha", "e-", "e+", "gamma", "proton"},
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


class SimulationSummary(BaseModel):
    id: str
    label: str
    default_params: Dict[str, Any]


class RunSimulationResponse(BaseModel):
    run_id: str
    duration_seconds: float
    params_used: Dict[str, Any]
    geometry: Dict[str, Any]
    trajectories: List[Dict[str, Any]]
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
    params = dict(sim_config["default_params"])
    provided = req.model_dump(exclude_none=True)
    params.update(provided)

    allowed_particles = sim_config.get("allowed_particles")
    if allowed_particles and params["particle"] not in allowed_particles:
        raise HTTPException(
            status_code=422,
            detail=f"Partícula '{params['particle']}' não permitida para '{sim_id}'. Opções: {sorted(allowed_particles)}",
        )

    ranges = sim_config.get("param_ranges", {})
    for key, (low, high) in ranges.items():
        value = params.get(key)
        if value is None or not (low <= value <= high):
            raise HTTPException(
                status_code=422,
                detail=f"Parâmetro '{key}'={value!r} fora da faixa permitida [{low}, {high}]",
            )

    for key in ("pos_x_cm", "pos_y_cm", "pos_z_cm", "dir_x", "dir_y", "dir_z"):
        value = params.get(key)
        if not isinstance(value, (int, float)):
            raise HTTPException(status_code=422, detail=f"Parâmetro '{key}' deve ser numérico, recebi {value!r}")

    if not isinstance(params.get("particle"), str) or "\n" in params["particle"] or " " in params["particle"]:
        raise HTTPException(status_code=422, detail="Parâmetro 'particle' inválido")

    return params


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

    sim_request = SimulationRequest(
        executable=sim_config["executable"],
        macro_template=sim_config["macro_template"],
        params=params,
        output_patterns=[sim_config["geometry_filename"], sim_config["trajectories_filename"]],
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

    import json
    try:
        trajectories_data = json.loads(trajectories_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao ler trajetórias geradas: {exc}") from exc

    return RunSimulationResponse(
        run_id=result.run_id,
        duration_seconds=result.duration_seconds,
        params_used=params,
        geometry=geometry,
        trajectories=trajectories_data.get("trajectories", []),
        stdout_tail=result.stdout[-2000:],
    )


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}
