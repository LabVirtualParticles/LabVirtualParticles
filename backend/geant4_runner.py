"""
geant4_runner.py

Executor genérico de simulações Geant4 em modo batch, pensado para ser
chamado por um backend web (ex.: FastAPI/Flask). Não conhece nada sobre
uma simulação específica (Rutherford, etc.) — recebe o caminho do
executável já compilado e uma macro (.mac), roda em processo separado,
e devolve os arquivos de saída gerados.

Uso típico dentro de uma rota do backend:

    from geant4_runner import Geant4Runner, SimulationRequest

    runner = Geant4Runner(
        geant4_env_script="/opt/geant4/install/bin/geant4.sh",  # opcional
    )

    result = runner.run(SimulationRequest(
        executable="/srv/simulations/rutherford/build/programa",
        macro_template="/srv/simulations/rutherford/macros/run.mac.tmpl",
        params={"energy_MeV": 5.0, "n_events": 1000, "target_thickness_cm": 0.0001},
        output_patterns=["*.root", "*.gdml"],
    ))

    if result.success:
        for f in result.output_files:
            ...  # enviar para conversão / frontend
    else:
        ...  # result.stderr tem o motivo

Também funciona via linha de comando para testes manuais:

    python geant4_runner.py --executable ./build/programa --macro macros/run.mac
"""

from __future__ import annotations

import argparse
import dataclasses
import fnmatch
import json
import logging
import os
import shutil
import string
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger("geant4_runner")


# --------------------------------------------------------------------------- #
# Exceções
# --------------------------------------------------------------------------- #

class Geant4RunnerError(Exception):
    """Erro genérico de configuração/execução do runner."""


class MacroRenderError(Geant4RunnerError):
    """Erro ao gerar a macro a partir do template + parâmetros do usuário."""


class SimulationTimeoutError(Geant4RunnerError):
    """A simulação excedeu o tempo limite e foi encerrada."""


# --------------------------------------------------------------------------- #
# Estruturas de entrada/saída
# --------------------------------------------------------------------------- #

@dataclasses.dataclass
class SimulationRequest:
    # Caminho do binário compilado do Geant4 (ex.: build/programa)
    executable: str

    # UMA das duas opções abaixo deve ser fornecida:
    # - macro_path: um arquivo .mac já pronto, usado como está
    # - macro_template: um arquivo .mac com placeholders $nome, preenchido
    #   com `params` antes de rodar (ver render_macro)
    macro_path: Optional[str] = None
    macro_template: Optional[str] = None
    params: Dict[str, Any] = dataclasses.field(default_factory=dict)

    # Padrões (estilo glob) dos arquivos que a simulação deve produzir e que
    # devem ser coletados ao final (ex.: ["*.root", "*.gdml"]). Se vazio,
    # nenhum arquivo é coletado automaticamente (útil se você já sabe o nome
    # exato do arquivo de saída e quer conferir você mesmo).
    output_patterns: List[str] = dataclasses.field(default_factory=list)

    # Argumentos extra de linha de comando após a macro, se o executável
    # aceitar (a maioria dos exemplos Geant4 não precisa disso).
    extra_args: List[str] = dataclasses.field(default_factory=list)

    # Diretório onde a simulação vai rodar (cwd). Se None, um diretório
    # temporário isolado é criado automaticamente — recomendado quando
    # várias simulações podem rodar concorrentemente no servidor.
    work_dir: Optional[str] = None

    # Tempo máximo em segundos antes de matar o processo.
    timeout_seconds: float = 300.0

    # Variáveis de ambiente extra (além do os.environ e do que vier do
    # geant4_env_script do Runner), ex.: {"OMP_NUM_THREADS": "1"}
    env: Dict[str, str] = dataclasses.field(default_factory=dict)

    # Se True, mantém o work_dir após a execução (default). Se False, apaga
    # o diretório temporário ao final (só faz sentido quando work_dir=None).
    keep_work_dir: bool = True

    # Identificador opcional da simulação, útil para logs/rastreamento.
    run_id: Optional[str] = None


@dataclasses.dataclass
class SimulationResult:
    success: bool
    run_id: str
    return_code: Optional[int]
    duration_seconds: float
    work_dir: str
    macro_path: str
    stdout: str
    stderr: str
    output_files: List[str] = dataclasses.field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


# --------------------------------------------------------------------------- #
# Renderização de macro a partir de um template
# --------------------------------------------------------------------------- #

def render_macro(template_path: str, params: Dict[str, Any], destination_path: str) -> str:
    """
    Substitui placeholders $nome (string.Template) no template da macro
    pelos valores em `params` e escreve o resultado em destination_path.

    Exemplo de macro-template (macros/run.mac.tmpl):

        /run/verbose 1
        /gps/particle alpha
        /gps/energy $energy_MeV MeV
        /run/beamOn $n_events

    Chamada:

        render_macro("macros/run.mac.tmpl",
                      {"energy_MeV": 5, "n_events": 1000},
                      "/tmp/run_abc123/run.mac")

    Qualquer placeholder presente no template que não tenha valor
    correspondente em `params` gera MacroRenderError (evita rodar o Geant4
    com um comando incompleto silenciosamente).

    Nota: como o formato usa $, qualquer cifrão literal que porventura
    apareça no template (ex.: em um comentário) precisa ser escrito em
    dobro ($$), senão string.Template tenta interpretá-lo como placeholder
    e o render falha.
    """
    template_file = Path(template_path)
    if not template_file.is_file():
        raise MacroRenderError(f"Template de macro não encontrado: {template_path}")

    raw = template_file.read_text(encoding="utf-8")
    template = string.Template(raw)
    try:
        rendered = template.substitute(**params)
    except KeyError as exc:
        raise MacroRenderError(
            f"Parâmetro ausente para o placeholder {exc} exigido pelo template {template_path}"
        ) from exc
    except ValueError as exc:
        raise MacroRenderError(f"Template de macro inválido em {template_path}: {exc}") from exc

    dest = Path(destination_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(rendered, encoding="utf-8")
    return str(dest)


# --------------------------------------------------------------------------- #
# Runner principal
# --------------------------------------------------------------------------- #

class Geant4Runner:
    def __init__(
        self,
        geant4_env_script: Optional[str] = None,
        base_work_dir: Optional[str] = None,
    ) -> None:
        """
        geant4_env_script: caminho para o geant4.sh / geant4make.sh gerado
            pela instalação do Geant4 (define G4LEDATA, G4NEUTRONHPDATA,
            etc.). Se fornecido, é "sourceado" uma vez e o ambiente
            resultante é reutilizado em todas as execuções — sem isso,
            simulações que dependem de dados físicos (nêutrons, radioativos,
            etc.) podem falhar silenciosamente ou dar resultados errados.
        base_work_dir: diretório base onde os diretórios temporários de
            cada execução são criados (default: diretório temporário do SO).
        """
        self._base_work_dir = base_work_dir
        self._cached_geant4_env: Optional[Dict[str, str]] = None
        self._geant4_env_script = geant4_env_script

    # -- ambiente ----------------------------------------------------------

    def _resolve_env(self, extra_env: Dict[str, str]) -> Dict[str, str]:
        env = dict(os.environ)
        if self._geant4_env_script:
            env.update(self._load_shell_env(self._geant4_env_script))
        env.update(extra_env)
        return env

    def _load_shell_env(self, script_path: str) -> Dict[str, str]:
        """
        "Source-ia" um script shell (que só define variáveis de ambiente,
        como o geant4.sh) e captura o ambiente resultante, já que o Python
        não consegue importar variáveis de um script sh diretamente.
        Resultado é cacheado em memória (o processo do backend web fica de
        pé por muito tempo, não faz sentido re-sourcear a cada request).
        """
        if self._cached_geant4_env is not None:
            return self._cached_geant4_env

        if not Path(script_path).is_file():
            raise Geant4RunnerError(f"Script de ambiente do Geant4 não encontrado: {script_path}")

        marker = f"__GEANT4_ENV_MARKER_{uuid.uuid4().hex}__"
        cmd = f'source "{script_path}" >/dev/null 2>&1; echo "{marker}"; env'
        try:
            proc = subprocess.run(
                ["bash", "-c", cmd],
                capture_output=True,
                text=True,
                timeout=60,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            raise Geant4RunnerError(
                f"Falha ao carregar ambiente do Geant4 a partir de {script_path}: {exc.stderr}"
            ) from exc

        # Tudo depois do marcador é o `env` já com as variáveis do Geant4.
        _, _, after_marker = proc.stdout.partition(marker)
        parsed: Dict[str, str] = {}
        for line in after_marker.strip().splitlines():
            if "=" in line:
                key, _, value = line.partition("=")
                parsed[key] = value

        self._cached_geant4_env = parsed
        logger.info("Ambiente do Geant4 carregado de %s (%d variáveis)", script_path, len(parsed))
        return parsed

    # -- execução ------------------------------------------------------------

    def run(self, request: SimulationRequest) -> SimulationResult:
        run_id = request.run_id or uuid.uuid4().hex[:12]

        executable = Path(request.executable).expanduser().resolve()
        if not executable.is_file():
            return self._failure(run_id, "", f"Executável não encontrado: {executable}")
        if not os.access(executable, os.X_OK):
            return self._failure(run_id, "", f"Executável sem permissão de execução: {executable}")

        # -- diretório de trabalho isolado por execução --
        cleanup_dir = False
        if request.work_dir:
            work_dir = Path(request.work_dir).expanduser().resolve()
            work_dir.mkdir(parents=True, exist_ok=True)
        else:
            work_dir = Path(tempfile.mkdtemp(prefix=f"g4run_{run_id}_", dir=self._base_work_dir))
            cleanup_dir = not request.keep_work_dir

        # -- resolve a macro (arquivo pronto ou template + params) --
        try:
            macro_path = self._resolve_macro(request, work_dir)
        except MacroRenderError as exc:
            return self._failure(run_id, str(work_dir), str(exc))

        # -- monta o comando: <executavel> <macro> [extra_args...] --
        # Geant4 batch convencional: passar a macro como argv[1] faz o
        # executável rodar "/control/execute macro.mac" e sair — desde que
        # o main.cpp NÃO force uma sessão de UI interativa depois (ver nota
        # sobre o patch sugerido no main.cpp).
        cmd = [str(executable), str(macro_path), *request.extra_args]

        env = self._resolve_env(request.env)

        logger.info("[%s] executando: %s (cwd=%s)", run_id, " ".join(cmd), work_dir)
        start = time.monotonic()
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(work_dir),
                env=env,
                capture_output=True,
                text=True,
                timeout=request.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            duration = time.monotonic() - start

            def _as_text(value: Any) -> str:
                if value is None:
                    return ""
                if isinstance(value, bytes):
                    return value.decode("utf-8", errors="replace")
                return value

            return SimulationResult(
                success=False,
                run_id=run_id,
                return_code=None,
                duration_seconds=duration,
                work_dir=str(work_dir),
                macro_path=str(macro_path),
                stdout=_as_text(exc.stdout),
                stderr=_as_text(exc.stderr) + "\n[runner] processo excedeu o timeout e foi encerrado.",
                error=f"Timeout após {request.timeout_seconds}s",
            )
        except OSError as exc:
            duration = time.monotonic() - start
            return SimulationResult(
                success=False,
                run_id=run_id,
                return_code=None,
                duration_seconds=duration,
                work_dir=str(work_dir),
                macro_path=str(macro_path),
                stdout="",
                stderr="",
                error=f"Falha ao iniciar o processo: {exc}",
            )

        duration = time.monotonic() - start
        success = proc.returncode == 0

        output_files: List[str] = []
        if request.output_patterns:
            output_files = self._collect_output_files(work_dir, request.output_patterns)
            if success and not output_files:
                # O processo terminou com código 0 mas não gerou nenhum dos
                # arquivos esperados — normalmente sinal de macro incompleta
                # (ex.: faltou /run/beamOn) ou de que a simulação não grava
                # nada ainda (sem RunAction/AnalysisManager no código C++).
                success = False
                proc_stderr = (
                    proc.stderr
                    + "\n[runner] processo terminou com sucesso mas nenhum arquivo de saída "
                    f"correspondente a {request.output_patterns} foi encontrado em {work_dir}."
                )
            else:
                proc_stderr = proc.stderr
        else:
            proc_stderr = proc.stderr

        result = SimulationResult(
            success=success,
            run_id=run_id,
            return_code=proc.returncode,
            duration_seconds=duration,
            work_dir=str(work_dir),
            macro_path=str(macro_path),
            stdout=proc.stdout,
            stderr=proc_stderr,
            output_files=output_files,
            error=None if success else f"Geant4 retornou código {proc.returncode}",
        )

        if cleanup_dir:
            shutil.rmtree(work_dir, ignore_errors=True)
            result.work_dir = "" # já removido

        logger.info(
            "[%s] finalizado: success=%s duration=%.2fs arquivos=%d",
            run_id, result.success, result.duration_seconds, len(result.output_files),
        )
        return result

    # -- helpers -------------------------------------------------------------

    @staticmethod
    def _resolve_macro(request: SimulationRequest, work_dir: Path) -> Path:
        if request.macro_path and request.macro_template:
            raise MacroRenderError("Forneça apenas um de macro_path ou macro_template, não os dois.")

        if request.macro_path:
            macro_file = Path(request.macro_path).expanduser().resolve()
            if not macro_file.is_file():
                raise MacroRenderError(f"Macro não encontrada: {macro_file}")
            return macro_file

        if request.macro_template:
            rendered_path = work_dir / "run.mac"
            render_macro(request.macro_template, request.params, str(rendered_path))
            return rendered_path

        raise MacroRenderError("É preciso fornecer macro_path ou macro_template.")

    @staticmethod
    def _collect_output_files(work_dir: Path, patterns: Iterable[str]) -> List[str]:
        found: List[str] = []
        for entry in sorted(work_dir.rglob("*")):
            if entry.is_file() and any(fnmatch.fnmatch(entry.name, pat) for pat in patterns):
                found.append(str(entry))
        return found

    @staticmethod
    def _failure(run_id: str, work_dir: str, message: str) -> SimulationResult:
        logger.error("[%s] %s", run_id, message)
        return SimulationResult(
            success=False,
            run_id=run_id,
            return_code=None,
            duration_seconds=0.0,
            work_dir=work_dir,
            macro_path="",
            stdout="",
            stderr="",
            error=message,
        )


# --------------------------------------------------------------------------- #
# CLI para testes manuais
# --------------------------------------------------------------------------- #

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Executa uma simulação Geant4 em modo batch.")
    parser.add_argument("--executable", required=True, help="Caminho do binário compilado (ex.: build/programa)")

    macro_group = parser.add_mutually_exclusive_group(required=True)
    macro_group.add_argument("--macro", help="Caminho de uma macro .mac pronta")
    macro_group.add_argument("--macro-template", help="Caminho de um template .mac com placeholders $nome")

    parser.add_argument(
        "--param", action="append", default=[],
        help="Parâmetro para o template no formato nome=valor (repita para vários). Ex.: --param energy_MeV=5",
    )
    parser.add_argument("--output-pattern", action="append", default=[],
                         help="Padrão glob de arquivo de saída a coletar (repita para vários). Ex.: --output-pattern '*.root'")
    parser.add_argument("--work-dir", help="Diretório de trabalho (default: temporário)")
    parser.add_argument("--geant4-env-script", help="geant4.sh / geant4make.sh a sourcear antes de rodar")
    parser.add_argument("--timeout", type=float, default=300.0, help="Timeout em segundos (default: 300)")
    parser.add_argument("--json", action="store_true", help="Imprime o resultado como JSON")
    return parser


def _parse_params(pairs: List[str]) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"--param inválido (esperado nome=valor): {pair}")
        key, _, value = pair.partition("=")
        # tenta converter para número quando possível, senão mantém string
        try:
            value_converted: Any = int(value)
        except ValueError:
            try:
                value_converted = float(value)
            except ValueError:
                value_converted = value
        params[key] = value_converted
    return params


def main(argv: Optional[List[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = _build_arg_parser().parse_args(argv)

    runner = Geant4Runner(geant4_env_script=args.geant4_env_script)

    request = SimulationRequest(
        executable=args.executable,
        macro_path=args.macro,
        macro_template=args.macro_template,
        params=_parse_params(args.param),
        output_patterns=args.output_pattern,
        work_dir=args.work_dir,
        timeout_seconds=args.timeout,
    )

    result = runner.run(request)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(f"success        : {result.success}")
        print(f"run_id         : {result.run_id}")
        print(f"return_code    : {result.return_code}")
        print(f"duration_s     : {result.duration_seconds:.2f}")
        print(f"work_dir       : {result.work_dir}")
        print(f"macro_path     : {result.macro_path}")
        print(f"output_files   : {result.output_files}")
        if result.error:
            print(f"error          : {result.error}")
        print("---- stdout ----")
        print(result.stdout)
        print("---- stderr ----")
        print(result.stderr)

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
