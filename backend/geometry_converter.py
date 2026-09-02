"""
geometry_converter.py

Converte a geometria exportada pelo Geant4 em GDML para o JSON consumido
pelo Three.js no frontend (vértices + índices por volume, prontos para
virar um THREE.BufferGeometry).

Baseado no parser que já existia no repositório GeometryGeant4
(https://github.com/helen1789/GeometryGeant4, main.py), com correções em
relação à versão original:

1. **Percurso da árvore de volumes corrigido.** A versão original iterava
   cada `<volume>` do GDML e, para cada `<physvol>` DENTRO dele, exportava
   o mesh do PRÓPRIO volume (não do volume referenciado no physvol) na
   posição do filho. Isso funciona por acaso só quando a hierarquia tem
   exatamente um nível E o volume-mãe é o único com sólido tesselável; no
   caso real do FolhaDeOuro (World > FolhaDeOuro + Detector, todos com
   sólido próprio) isso faz o World aparecer duplicado nas posições dos
   filhos, e a folha de ouro e o detector nunca aparecerem. Agora o
   percurso é recursivo de verdade: começa no volume de `<setup><world>`,
   desce por `physvol -> volumeref`, e cada volume é desenhado com o
   próprio sólido, na transformação (posição + rotação) acumulada desde a
   raiz.
2. **Rotação de physvol agora é aplicada.** O Detector.cpp do FolhaDeOuro
   rotaciona o detector 90° em X (`rotacao->rotateX(90*deg)`) - sem
   suporte a `<rotation>`/`<rotationref>` o detector sairia com o eixo do
   tubo na orientação errada. A convenção de sinal do GDML para rotação de
   physvol é "mãe-para-filha" (a inversa da rotação "física" do objeto);
   aplicamos a transposta para compensar - ver `_parse_rotation_matrix`
   para o comentário completo e como inverter caso o resultado saia
   espelhado quando testado contra uma exportação real.
3. **`tessellate_tube` respeita `startphi`/`deltaphi`.** A versão original
   sempre desenhava uma volta completa (360°); o detector é um G4Tubs de
   começando em 30° e varrendo 300° (termina em 330°, deixa um vão de 60°
   sem material) - não um anel fechado.
4. **Unidades.** Todas as coordenadas (vértices e posições) são
   convertidas para centímetros a partir de `lunit` (GDML default é mm,
   que é a unidade interna do Geant4) - a versão original tratava os
   números como se já estivessem todos numa unidade só. Centímetro foi
   escolhido para bater com o Detector.cpp e com o TrajectoryRecorder (que
   já escreve as trajetórias em cm).

Não depende de nenhuma biblioteca de geometria externa (pyg4ometry, etc.)
- só `xml.etree`, da stdlib. Suporta os sólidos usados hoje (box, tube);
sphere é tesselada mas sem suporte a corte parcial de phi/theta. Outros
sólidos GDML (cone, trapézio, booleanos) geram um aviso e são omitidos do
JSON em vez de desenhar algo errado silenciosamente - dá pra ver no log
do backend quando isso acontece.
"""

from __future__ import annotations

import io
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from xml.etree import ElementTree as ET

logger = logging.getLogger("geometry_converter")

_LENGTH_UNIT_TO_CM = {
    "mm": 0.1,
    "cm": 1.0,
    "m": 100.0,
}

Vec3 = Tuple[float, float, float]
Mat3 = Tuple[Vec3, Vec3, Vec3]

_IDENTITY: Mat3 = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


class GdmlConversionError(Exception):
    """Erro ao interpretar o GDML (estrutura inesperada, sólido não suportado, etc.)."""


# --------------------------------------------------------------------------- #
# Unidades
# --------------------------------------------------------------------------- #

def _length_factor(elem: ET.Element, default_unit: str = "mm") -> float:
    # <box>/<tube>/... usam o atributo "lunit"; <position> usa "unit".
    # Aceita os dois nomes para não depender de qual o G4GDMLParser real
    # escreve (não temos Geant4 instalado aqui para conferir na prática).
    unit = elem.get("lunit") or elem.get("unit") or default_unit
    factor = _LENGTH_UNIT_TO_CM.get(unit)
    if factor is None:
        logger.warning("Unidade de comprimento desconhecida '%s', assumindo mm", unit)
        factor = _LENGTH_UNIT_TO_CM["mm"]
    return factor


def _angle_to_radians(value: float, elem: ET.Element, default_unit: str = "deg") -> float:
    # <tube>/... usam "aunit"; <rotation> usa "unit". Aceita os dois pelo
    # mesmo motivo do comentário em _length_factor.
    unit = elem.get("aunit") or elem.get("unit") or default_unit
    if unit == "rad":
        return value
    return math.radians(value)


# --------------------------------------------------------------------------- #
# Álgebra linear mínima (sem numpy - só o suficiente para compor transforms)
# --------------------------------------------------------------------------- #

def _mat_mul(a: Mat3, b: Mat3) -> Mat3:
    return tuple(
        tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3))
        for i in range(3)
    )  # type: ignore[return-value]


def _mat_vec(m: Mat3, v: Vec3) -> Vec3:
    return (
        m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
        m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
        m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2],
    )


def _mat_transpose(m: Mat3) -> Mat3:
    return (
        (m[0][0], m[1][0], m[2][0]),
        (m[0][1], m[1][1], m[2][1]),
        (m[0][2], m[1][2], m[2][2]),
    )


def _vec_add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _rotate_flat_vertices(vertices: List[float], m: Mat3) -> List[float]:
    if m == _IDENTITY:
        return vertices
    out: List[float] = []
    for i in range(0, len(vertices), 3):
        x, y, z = _mat_vec(m, (vertices[i], vertices[i + 1], vertices[i + 2]))
        out += [x, y, z]
    return out


def _parse_rotation_matrix(elem: ET.Element) -> Mat3:
    rx = _angle_to_radians(float(elem.get("x", 0)), elem)
    ry = _angle_to_radians(float(elem.get("y", 0)), elem)
    rz = _angle_to_radians(float(elem.get("z", 0)), elem)

    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)

    r_x: Mat3 = ((1, 0, 0), (0, cx, -sx), (0, sx, cx))
    r_y: Mat3 = ((cy, 0, sy), (0, 1, 0), (-sy, 0, cy))
    r_z: Mat3 = ((cz, -sz, 0), (sz, cz, 0), (0, 0, 1))

    # Ordem extrínseca X, depois Y, depois Z (convenção mais comum em GDML).
    r = _mat_mul(_mat_mul(r_z, r_y), r_x)

    # ATENÇÃO - ponto que precisa ser validado contra uma exportação GDML
    # real do Geant4 (não temos Geant4 instalado neste ambiente para
    # testar): a rotação de um <physvol> no GDML segue a convenção do
    # G4PVPlacement, onde a matriz é "mãe-para-filha" (rotaciona os eixos
    # da mãe para alinhar com os da filha) - o inverso da rotação "física"
    # que precisamos aplicar ao mesh local para desenhá-lo no referencial
    # do mundo. Como é uma matriz de rotação (ortogonal), o inverso é a
    # transposta. Se, ao rodar de verdade, o detector aparecer espelhado
    # ou no eixo errado, troque a linha abaixo para `return r` (sem
    # transpor) - é a primeira coisa a tentar.
    return _mat_transpose(r)


# --------------------------------------------------------------------------- #
# Parsing GDML -> JSON
# --------------------------------------------------------------------------- #

def parse_gdml(source: Union[str, Path, io.IOBase]) -> Dict[str, Any]:
    """
    Lê um arquivo/stream GDML e devolve {"volumes": [...]}, onde cada volume
    tem "name", "vertices" (lista plana [x0,y0,z0,x1,y1,z1,...] em cm, já
    na orientação/posição final no referencial do mundo), "indices"
    (triângulos) e "position" ([x,y,z] em cm, do centro do volume).
    """
    if isinstance(source, (str, Path)):
        tree = ET.parse(source)
    else:
        tree = ET.ElementTree(ET.fromstring(source.read()))
    root = tree.getroot()

    solids_elem = root.find("solids")
    if solids_elem is None:
        raise GdmlConversionError("GDML sem seção <solids>")
    solids = {solid.get("name"): solid for solid in solids_elem}

    positions: Dict[str, Vec3] = {}
    rotations: Dict[str, Mat3] = {}
    defines = root.find("define")
    if defines is not None:
        for pos in defines.findall("position"):
            factor = _length_factor(pos)
            positions[pos.get("name")] = (
                float(pos.get("x", 0)) * factor,
                float(pos.get("y", 0)) * factor,
                float(pos.get("z", 0)) * factor,
            )
        for rot in defines.findall("rotation"):
            rotations[rot.get("name")] = _parse_rotation_matrix(rot)

    structure = root.find("structure")
    if structure is None:
        raise GdmlConversionError("GDML sem seção <structure>")
    volumes_by_name = {vol.get("name"): vol for vol in structure.findall("volume")}
    if not volumes_by_name:
        raise GdmlConversionError("GDML sem nenhum <volume> em <structure>")

    world_ref = None
    setup = root.find("setup")
    if setup is not None:
        world_elem = setup.find("world")
        if world_elem is not None:
            world_ref = world_elem.get("ref")
    if world_ref is None or world_ref not in volumes_by_name:
        # Fallback: GDML normalmente lista o volume-mundo por último em
        # <structure>. Não deveria ser necessário (G4GDMLParser sempre
        # escreve <setup>), mas evita quebrar em GDML editado à mão.
        world_ref = list(volumes_by_name.keys())[-1]
        logger.warning(
            "GDML sem <setup><world ref=...> válido - assumindo '%s' como volume-mundo",
            world_ref,
        )

    output: List[Dict[str, Any]] = []
    _walk_volume(
        world_ref, volumes_by_name, solids, positions, rotations,
        parent_pos=(0.0, 0.0, 0.0), parent_rot=_IDENTITY,
        output=output, visited=set(),
    )
    return {"volumes": output}


def _resolve_physvol_position(pv: ET.Element, positions: Dict[str, Vec3]) -> Vec3:
    pos_elem = pv.find("position")
    if pos_elem is not None:
        factor = _length_factor(pos_elem)
        return (
            float(pos_elem.get("x", 0)) * factor,
            float(pos_elem.get("y", 0)) * factor,
            float(pos_elem.get("z", 0)) * factor,
        )
    posref_elem = pv.find("positionref")
    if posref_elem is not None:
        ref = posref_elem.get("ref")
        if ref in positions:
            return positions[ref]
        logger.warning("positionref '%s' não encontrado em <define> - usando origem", ref)
    return (0.0, 0.0, 0.0)


def _resolve_physvol_rotation(pv: ET.Element, rotations: Dict[str, Mat3]) -> Mat3:
    rot_elem = pv.find("rotation")
    if rot_elem is not None:
        return _parse_rotation_matrix(rot_elem)
    rotref_elem = pv.find("rotationref")
    if rotref_elem is not None:
        ref = rotref_elem.get("ref")
        if ref in rotations:
            return rotations[ref]
        logger.warning("rotationref '%s' não encontrado em <define> - usando identidade", ref)
    return _IDENTITY


def _walk_volume(
    vol_name: str,
    volumes_by_name: Dict[str, ET.Element],
    solids: Dict[str, ET.Element],
    positions: Dict[str, Vec3],
    rotations: Dict[str, Mat3],
    parent_pos: Vec3,
    parent_rot: Mat3,
    output: List[Dict[str, Any]],
    visited: set,
) -> None:
    if vol_name in visited:
        logger.warning("Referência circular detectada em '%s' - interrompendo esse ramo", vol_name)
        return
    visited = visited | {vol_name}

    vol = volumes_by_name.get(vol_name)
    if vol is None:
        logger.warning("Volume '%s' referenciado mas não definido em <structure>", vol_name)
        return

    solid_ref_elem = vol.find("solidref")
    if solid_ref_elem is not None:
        solid = solids.get(solid_ref_elem.get("ref"))
        if solid is None:
            logger.warning(
                "Volume '%s' referencia sólido inexistente '%s'", vol_name, solid_ref_elem.get("ref")
            )
        else:
            mesh = tessellate(solid)
            if mesh is None:
                logger.warning(
                    "Sólido '%s' (tipo <%s>, volume '%s') ainda não é suportado - omitido do JSON.",
                    solid_ref_elem.get("ref"), solid.tag, vol_name,
                )
            else:
                rotated_verts = _rotate_flat_vertices(mesh["vertices"], parent_rot)
                output.append({
                    "name": vol_name,
                    "vertices": rotated_verts,
                    "indices": mesh["indices"],
                    "position": list(parent_pos),
                })

    for pv in vol.findall("physvol"):
        child_ref_elem = pv.find("volumeref")
        if child_ref_elem is None:
            continue
        child_name = child_ref_elem.get("ref")

        local_pos = _resolve_physvol_position(pv, positions)
        local_rot = _resolve_physvol_rotation(pv, rotations)

        world_pos = _vec_add(parent_pos, _mat_vec(parent_rot, local_pos))
        world_rot = _mat_mul(parent_rot, local_rot)

        _walk_volume(
            child_name, volumes_by_name, solids, positions, rotations,
            world_pos, world_rot, output, visited,
        )


# --------------------------------------------------------------------------- #
# Tesselação de sólidos
# --------------------------------------------------------------------------- #

def tessellate(solid: ET.Element) -> Optional[Dict[str, List[float]]]:
    tag = solid.tag
    if tag == "box":
        return tessellate_box(solid)
    elif tag == "tube":
        return tessellate_tube(solid)
    elif tag == "sphere":
        return tessellate_sphere(solid)
    return None


def tessellate_box(solid: ET.Element) -> Dict[str, List[float]]:
    factor = _length_factor(solid)
    dx = float(solid.get("x", 100)) * factor / 2
    dy = float(solid.get("y", 100)) * factor / 2
    dz = float(solid.get("z", 100)) * factor / 2

    v = [
        [-dx, -dy, -dz], [dx, -dy, -dz], [dx, dy, -dz], [-dx, dy, -dz],
        [-dx, -dy, dz], [dx, -dy, dz], [dx, dy, dz], [-dx, dy, dz],
    ]
    faces = [
        [0, 1, 2, 3], [4, 7, 6, 5],
        [0, 4, 5, 1], [2, 6, 7, 3],
        [0, 3, 7, 4], [1, 5, 6, 2],
    ]
    verts: List[float] = []
    idxs: List[int] = []
    for face in faces:
        base = len(verts) // 3
        for i in face:
            verts += v[i]
        idxs += [base, base + 1, base + 2, base, base + 2, base + 3]
    return {"vertices": verts, "indices": idxs}


def tessellate_tube(solid: ET.Element) -> Dict[str, List[float]]:
    lfactor = _length_factor(solid)
    rmax = float(solid.get("rmax", 50)) * lfactor
    rmin = float(solid.get("rmin", 0)) * lfactor
    hz = float(solid.get("z", 100)) * lfactor / 2

    startphi = _angle_to_radians(float(solid.get("startphi", 0)), solid)
    deltaphi = _angle_to_radians(float(solid.get("deltaphi", 360)), solid)
    is_full_revolution = deltaphi >= (2 * math.pi - 1e-9)

    segs = 64

    verts: List[float] = []
    idxs: List[int] = []

    for s in range(segs):
        a0 = startphi + deltaphi * s / segs
        a1 = startphi + deltaphi * (s + 1) / segs
        base = len(verts) // 3
        verts += [
            math.cos(a0) * rmax, math.sin(a0) * rmax, -hz,
            math.cos(a1) * rmax, math.sin(a1) * rmax, -hz,
            math.cos(a1) * rmax, math.sin(a1) * rmax, hz,
            math.cos(a0) * rmax, math.sin(a0) * rmax, hz,
        ]
        idxs += [base, base + 1, base + 2, base, base + 2, base + 3]

        if rmin > 0:
            base = len(verts) // 3
            verts += [
                math.cos(a0) * rmin, math.sin(a0) * rmin, -hz,
                math.cos(a1) * rmin, math.sin(a1) * rmin, -hz,
                math.cos(a1) * rmin, math.sin(a1) * rmin, hz,
                math.cos(a0) * rmin, math.sin(a0) * rmin, hz,
            ]
            idxs += [base, base + 2, base + 1, base, base + 3, base + 2]

        for z, sign in [(-hz, -1), (hz, 1)]:
            base = len(verts) // 3
            verts += [
                math.cos(a0) * rmin, math.sin(a0) * rmin, z,
                math.cos(a0) * rmax, math.sin(a0) * rmax, z,
                math.cos(a1) * rmax, math.sin(a1) * rmax, z,
                math.cos(a1) * rmin, math.sin(a1) * rmin, z,
            ]
            if sign > 0:
                idxs += [base, base + 1, base + 2, base, base + 2, base + 3]
            else:
                idxs += [base, base + 2, base + 1, base, base + 3, base + 2]

    if not is_full_revolution:
        # Tubo parcial (o detector do FolhaDeOuro começa em 30° e varre
        # 300°, terminando em 330°): sem isso o sólido fica "aberto" nas
        # duas pontas do arco - adiciona as paredes radiais que fecham
        # essas pontas.
        for angle in (startphi, startphi + deltaphi):
            base = len(verts) // 3
            verts += [
                math.cos(angle) * rmin, math.sin(angle) * rmin, -hz,
                math.cos(angle) * rmax, math.sin(angle) * rmax, -hz,
                math.cos(angle) * rmax, math.sin(angle) * rmax, hz,
                math.cos(angle) * rmin, math.sin(angle) * rmin, hz,
            ]
            idxs += [base, base + 1, base + 2, base, base + 2, base + 3]

    return {"vertices": verts, "indices": idxs}


def tessellate_sphere(solid: ET.Element) -> Dict[str, List[float]]:
    # Nota: ainda não trata phi/theta parciais (deltaphi/deltatheta), só
    # esferas completas - nenhum experimento atual usa G4Sphere, então não
    # foi prioridade agora. Sinalizar se algum experimento futuro precisar.
    lfactor = _length_factor(solid)
    rmax = float(solid.get("rmax", 50)) * lfactor
    segs = 32
    rings = 16

    verts: List[float] = []
    idxs: List[int] = []
    for i in range(rings + 1):
        phi = math.pi * i / rings
        for j in range(segs + 1):
            theta = 2 * math.pi * j / segs
            verts += [
                rmax * math.sin(phi) * math.cos(theta),
                rmax * math.cos(phi),
                rmax * math.sin(phi) * math.sin(theta),
            ]

    for i in range(rings):
        for j in range(segs):
            a = i * (segs + 1) + j
            b = a + segs + 1
            idxs += [a, b, a + 1, b, b + 1, a + 1]

    return {"vertices": verts, "indices": idxs}
