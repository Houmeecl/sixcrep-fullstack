"""
SIXCREP Backend — Valorización Ecosistémica SEEA-EA
2ª Región de Antofagasta, Chile
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional
import math, json
from pathlib import Path

app = FastAPI(
    title="SIXCREP API",
    description="Sistema de Valorización Ecosistémica · 2ª Región de Antofagasta",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir frontend desde raíz del proyecto
FRONTEND = Path(__file__).parent.parent
app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")


# ── Datos de ecosistemas (espeja los del frontend) ────────────────

USD_CLP = 950

ECO_DATA = {
    "desierto": dict(name="Desierto Absoluto",
        svc=dict(prov=2, reg=12, cult=18, mant=8), trend=-0.005),
    "matorral": dict(name="Matorral Desértico",
        svc=dict(prov=8, reg=35, cult=42, mant=38), trend=-0.008),
    "loma":     dict(name="Loma Costera",
        svc=dict(prov=65, reg=220, cult=180, mant=110), trend=-0.015),
    "pajonal":  dict(name="Pajonal Altiplánico",
        svc=dict(prov=85, reg=140, cult=65, mant=95), trend=-0.010),
    "bofedal":  dict(name="Bofedal Altoandino",
        svc=dict(prov=280, reg=3200, cult=450, mant=1400), trend=-0.020),
    "salar":    dict(name="Salar / Laguna Andina",
        svc=dict(prov=25, reg=210, cult=280, mant=165), trend=-0.025),
    "oasis":    dict(name="Oasis / Quebrada",
        svc=dict(prov=420, reg=850, cult=380, mant=290), trend=+0.002),
    "costero":  dict(name="Zona Costera Marina",
        svc=dict(prov=1650, reg=3400, cult=820, mant=1900), trend=-0.008),
    "minera":   dict(name="Zona Minera Activa",
        svc=dict(prov=-180, reg=-850, cult=-60, mant=-320), trend=-0.030),
}

HIST_YEARS = list(range(2015, 2025))
HIST_IDX = {
    "desierto": [100,99.5,99.1,98.7,98.4,98.0,97.7,97.4,97.1,96.8],
    "matorral": [100,99.2,98.5,97.8,97.1,96.4,95.6,94.9,94.2,93.5],
    "loma":     [100,98.5,97.0,95.5,93.5,91.5,89.5,87.5,85.5,83.5],
    "pajonal":  [100,99.0,98.0,97.0,96.0,95.0,93.8,92.5,91.2,90.0],
    "bofedal":  [100,98.0,96.0,93.5,91.0,88.5,85.5,82.5,79.5,76.5],
    "salar":    [100,97.5,95.0,92.0,89.0,85.8,82.5,79.0,75.5,72.0],
    "oasis":    [100,100.2,100.4,100.6,100.8,101.0,101.0,100.8,100.6,100.4],
    "costero":  [100,99.2,98.4,97.5,96.6,95.7,94.8,93.8,92.8,91.8],
    "minera":   [100,97.0,94.0,91.0,87.5,84.0,80.5,77.0,73.5,70.0],
}


def eco_total_usd(t: str) -> float:
    s = ECO_DATA[t]["svc"]
    return s["prov"] + s["reg"] + s["cult"] + s["mant"]


# ── Cálculo de área (fórmula de Gauss esférica) ───────────────────

def polygon_area_ha(coords: List[List[float]]) -> float:
    """Área aproximada en hectáreas para polígono lon/lat usando esfera."""
    R = 6371000  # radio Tierra en metros
    n = len(coords)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        lat1 = math.radians(coords[i][1])
        lat2 = math.radians(coords[j][1])
        dlon = math.radians(coords[j][0] - coords[i][0])
        area += dlon * (2 + math.sin(lat1) + math.sin(lat2))
    return abs(area) * R * R / 2 / 10_000


# ── Modelos Pydantic ──────────────────────────────────────────────

class EcosystemShare(BaseModel):
    ecosystem_type: str
    area_ha: float          # hectáreas del ecosistema dentro del área


class ValuationRequest(BaseModel):
    area_ha: Optional[float] = None          # puede venir calculado del frontend
    polygon: Optional[List[List[float]]] = None  # coords [[lon,lat],...] para calcular
    ecosystem_shares: List[EcosystemShare]   # desglose por ecosistema
    base_year: int = 2015
    compare_year: int = 2024


class ServiceBreakdown(BaseModel):
    prov: float; reg: float; cult: float; mant: float


class YearValue(BaseModel):
    year: int; value_usd: float; value_clp: float


class ValuationResponse(BaseModel):
    area_ha: float
    ecosystems: int
    service_breakdown: ServiceBreakdown
    total_usd_base: float
    total_usd_compare: float
    total_clp_compare: float
    change_pct: float
    historical: List[YearValue]
    per_ha_usd: float


# ── Endpoints ────────────────────────────────────────────────────

@app.get("/", tags=["info"])
def root():
    return {
        "sistema": "SIXCREP",
        "descripcion": "Valorización Ecosistémica SEEA-EA · 2ª Región de Antofagasta",
        "version": "2.0.0",
        "frontend": "/static/panel_antofagasta.html"
    }


@app.get("/api/ecosistemas", tags=["datos"])
def get_ecosistemas():
    """Retorna la tabla completa de tipos de ecosistemas con sus valores SEEA-EA."""
    result = {}
    for t, eco in ECO_DATA.items():
        total = eco_total_usd(t)
        result[t] = {
            "nombre": eco["name"],
            "servicios_usd_ha_año": eco["svc"],
            "total_usd_ha_año": round(total),
            "tendencia_anual": eco["trend"],
        }
    return result


@app.get("/api/historico/{eco_type}", tags=["datos"])
def get_historico(eco_type: str, year_from: int = 2015, year_to: int = 2024):
    """Retorna índices históricos de valorización para un tipo de ecosistema."""
    if eco_type not in HIST_IDX:
        raise HTTPException(404, f"Tipo '{eco_type}' no encontrado")
    data = [
        {"año": y, "indice": HIST_IDX[eco_type][i]}
        for i, y in enumerate(HIST_YEARS)
        if year_from <= y <= year_to
    ]
    return {"ecosistema": eco_type, "nombre": ECO_DATA[eco_type]["name"], "datos": data}


@app.post("/api/valorizar", response_model=ValuationResponse, tags=["análisis"])
def valorizar(req: ValuationRequest):
    """
    Calcula la valorización ecosistémica SEEA-EA para un área definida.
    Acepta desglose de ecosistemas y rango de años para comparación histórica.
    """
    # Calcular área si se pasa polígono
    area_ha = req.area_ha
    if area_ha is None and req.polygon:
        area_ha = polygon_area_ha(req.polygon)
    if area_ha is None or area_ha <= 0:
        raise HTTPException(400, "Se requiere area_ha o polygon con coordenadas válidas")

    # Validar tipos de ecosistema
    for share in req.ecosystem_shares:
        if share.ecosystem_type not in ECO_DATA:
            raise HTTPException(400, f"Tipo desconocido: {share.ecosystem_type}")

    bi = HIST_YEARS.index(req.base_year)    if req.base_year    in HIST_YEARS else 0
    ci = HIST_YEARS.index(req.compare_year) if req.compare_year in HIST_YEARS else -1

    # Breakdown de servicios
    bd = dict(prov=0.0, reg=0.0, cult=0.0, mant=0.0)
    total_usd = 0.0
    for share in req.ecosystem_shares:
        svc = ECO_DATA[share.ecosystem_type]["svc"]
        for k in bd:
            v = svc[k] * share.area_ha
            bd[k] += v
            total_usd += v

    # Serie histórica
    historical: List[YearValue] = []
    for i, yr in enumerate(HIST_YEARS):
        v = 0.0
        for share in req.ecosystem_shares:
            t = share.ecosystem_type
            factor = HIST_IDX[t][i] / 100
            v += eco_total_usd(t) * factor * share.area_ha
        historical.append(YearValue(year=yr, value_usd=round(v), value_clp=round(v * USD_CLP)))

    total_usd_base    = historical[bi].value_usd
    total_usd_compare = historical[ci].value_usd
    change_pct = ((total_usd_compare - total_usd_base) / abs(total_usd_base or 1)) * 100

    return ValuationResponse(
        area_ha=round(area_ha, 2),
        ecosystems=len(req.ecosystem_shares),
        service_breakdown=ServiceBreakdown(**{k: round(v) for k, v in bd.items()}),
        total_usd_base=round(total_usd_base),
        total_usd_compare=round(total_usd_compare),
        total_clp_compare=round(total_usd_compare * USD_CLP),
        change_pct=round(change_pct, 2),
        historical=historical,
        per_ha_usd=round(total_usd_compare / area_ha, 2),
    )


@app.get("/api/comparar", tags=["análisis"])
def comparar_años(eco_type: str, ha: float, year_a: int = 2015, year_b: int = 2024):
    """Comparación directa de valorización entre dos años para un ecosistema."""
    if eco_type not in ECO_DATA:
        raise HTTPException(404, f"Tipo '{eco_type}' no encontrado")
    if eco_type not in HIST_IDX:
        raise HTTPException(404, "Sin datos históricos para ese tipo")

    ia = HIST_YEARS.index(year_a) if year_a in HIST_YEARS else 0
    ib = HIST_YEARS.index(year_b) if year_b in HIST_YEARS else -1

    vha = eco_total_usd(eco_type)
    va = vha * (HIST_IDX[eco_type][ia] / 100) * ha
    vb = vha * (HIST_IDX[eco_type][ib] / 100) * ha
    delta = vb - va

    return {
        "ecosistema": ECO_DATA[eco_type]["name"],
        "area_ha": ha,
        f"valor_{year_a}_usd": round(va),
        f"valor_{year_b}_usd": round(vb),
        "delta_usd": round(delta),
        "delta_pct": round(delta / abs(va or 1) * 100, 2),
        "tendencia": ECO_DATA[eco_type]["trend"],
    }
