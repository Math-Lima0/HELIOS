"""
api.py — H.E.L.I.O.S. Web Engine (FastAPI)
============================================
Ponto de entrada na nuvem para o ecossistema Pantheon Systems.
Permite que agentes IA (A.R.E.S.) e outros serviços consumam o
motor de cálculo via HTTP.

Endpoints:
  GET  /                          → health check
  GET  /health                    → health detalhado + versão
  POST /api/v1/dimensionar        → cálculo completo
  POST /api/v1/dimensionar/resumo → apenas componentes selecionados
  GET  /api/v1/componentes/diodos → banco de diodos disponíveis
  GET  /api/v1/componentes/reguladores → banco de reguladores
"""

import time
import logging
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, model_validator

from motor_volpiano import dimensionar, Saida
import banco_dados as bd

# ─────────────────────────────────────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("helios.api")


# ─────────────────────────────────────────────────────────────────────────────
#  LIFESPAN (startup / shutdown)
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("⚡ H.E.L.I.O.S. API iniciando — Motor Volpiano carregado.")
    yield
    log.info("H.E.L.I.O.S. API encerrada.")


# ─────────────────────────────────────────────────────────────────────────────
#  APLICAÇÃO
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="H.E.L.I.O.S. API",
    description=(
        "**High-accuracy Electronics & Linear Input-Output Simulator**\n\n"
        "Motor Volpiano via HTTP para automação e IA — *Pantheon Systems*\n\n"
        "Calcula transformadores, capacitores, diodos (Curvas de Schade), "
        "fusíveis e reguladores de tensão para fontes lineares DC."
    ),
    version="1.1.0",
    contact={"name": "Pantheon Systems", "url": "https://pantheon.systems"},
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — permite chamadas do front-end local e de domínios Pantheon
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8080",
        "https://*.pantheon.systems",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
#  MIDDLEWARE — LOG DE LATÊNCIA
# ─────────────────────────────────────────────────────────────────────────────

@app.middleware("http")
async def log_requests(request: Request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - t0) * 1000
    log.info(f"{request.method} {request.url.path} → {response.status_code}  ({ms:.1f}ms)")
    response.headers["X-Process-Time-Ms"] = f"{ms:.1f}"
    return response


# ─────────────────────────────────────────────────────────────────────────────
#  MODELOS DE ENTRADA
# ─────────────────────────────────────────────────────────────────────────────

class SaidaRequest(BaseModel):
    tipo: str = Field(
        ...,
        description="Tipo do regulador: `'fixa'` (LM78xx) ou `'variavel'` (LM317/350/338)",
        examples=["fixa", "variavel"],
    )
    Vout: float = Field(
        ..., gt=0, le=50,
        description="Tensão de saída desejada (V). Faixa válida: 0 < Vout ≤ 50 V",
        examples=[12.0, 5.0, 18.0],
    )
    IL: float = Field(
        ..., gt=0, le=25,
        description="Corrente de carga máxima (A). Faixa válida: 0 < IL ≤ 25 A",
        examples=[0.5, 1.5, 0.75],
    )
    R2: float = Field(
        10000.0, gt=0,
        description="Resistor R2 do divisor do LM317 (Ω). Ignorado para saídas fixas.",
        examples=[10000.0],
    )

    @field_validator("tipo")
    @classmethod
    def validar_tipo(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in ("fixa", "variavel"):
            raise ValueError("tipo deve ser 'fixa' ou 'variavel'")
        return v


class DimensionarRequest(BaseModel):
    vp: float = Field(
        110.0,
        description="Tensão da rede elétrica de entrada (V). Use 110 ou 220.",
        examples=[110.0, 220.0],
    )
    vond: float = Field(
        3.0, gt=0, le=20,
        description="Tensão de ripple máxima permitida na saída do filtro (V).",
        examples=[3.0],
    )
    vd: float = Field(
        0.7, gt=0, le=2,
        description="Queda de tensão direta por diodo (V). Típico: 0.7 V para Si.",
        examples=[0.7],
    )
    saidas: List[SaidaRequest] = Field(
        ...,
        min_length=1,
        max_length=6,
        description="Lista de saídas da fonte. Mínimo 1, máximo 6.",
    )

    @field_validator("vp")
    @classmethod
    def validar_vp(cls, v: float) -> float:
        if v not in (110.0, 220.0):
            raise ValueError("vp deve ser 110 ou 220 V (padrão brasileiro)")
        return v

    @model_validator(mode="after")
    def validar_tensoes_saida(self) -> "DimensionarRequest":
        """Garante que nenhuma saída excede um limite razoável dado Vp."""
        vp_max_vout = {110.0: 40.0, 220.0: 80.0}
        limite = vp_max_vout[self.vp]
        for i, s in enumerate(self.saidas):
            if s.Vout > limite:
                raise ValueError(
                    f"Saída {i+1}: Vout={s.Vout}V excede o limite de {limite}V "
                    f"para rede de {self.vp}V"
                )
        return self


# ─────────────────────────────────────────────────────────────────────────────
#  MODELOS DE SAÍDA
# ─────────────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    system: str
    version: str
    motor: str
    message: str


class ResumoComponentes(BaseModel):
    transformador: dict
    capacitor: dict
    diodo: Optional[dict]
    fusiveis: dict
    reguladores: List[dict]
    alertas: List[str]


# ─────────────────────────────────────────────────────────────────────────────
#  HANDLER DE ERROS GLOBAL
# ─────────────────────────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    log.error(f"Erro não tratado em {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "code": 500,
            "detail": "Erro interno no Motor Volpiano. Verifique os parâmetros.",
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
#  ROTAS
# ─────────────────────────────────────────────────────────────────────────────

@app.get(
    "/",
    summary="Ping rápido",
    tags=["Sistema"],
)
def home():
    """Endpoint de verificação de status simples (health check rápido)."""
    return {
        "status": "online",
        "system": "H.E.L.I.O.S.",
        "message": "Santuário Digital ativo. Motor aguardando cálculos.",
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check detalhado",
    tags=["Sistema"],
)
def health():
    """Retorna status detalhado da API, versão e estado do motor."""
    return HealthResponse(
        status="healthy",
        system="H.E.L.I.O.S.",
        version="1.1.0",
        motor="Motor Volpiano + Curvas de Schade (scipy)",
        message="Todos os subsistemas operacionais.",
    )


@app.post(
    "/api/v1/dimensionar",
    summary="Cálculo completo da fonte",
    tags=["Motor"],
    status_code=status.HTTP_200_OK,
)
def api_dimensionar(req: DimensionarRequest):
    """
    Recebe os parâmetros do projeto e executa o **dimensionamento completo**
    da fonte linear, retornando todos os valores intermediários e componentes
    comerciais selecionados.

    O resultado inclui:
    - Transformador (Vsmax, Vsef, código comercial)
    - Capacitor eletrolítico
    - Diodos da ponte Graetz (via Curvas de Schade)
    - Fusíveis primário e secundário
    - Reguladores por saída (LM78xx / LM317 / LM350 / LM338)
    - Alertas de projeto (dissipador, faixa de tensão, etc.)
    """
    lista_saidas = [
        Saida(tipo=s.tipo, Vout=s.Vout, IL=s.IL, R2=s.R2)
        for s in req.saidas
    ]

    try:
        resultado = dimensionar(
            saidas=lista_saidas,
            Vp=req.vp,
            Vond=req.vond,
            Vd=req.vd,
        )
    except Exception as e:
        log.error(f"Falha no motor: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Falha de processamento no Motor Volpiano: {e}",
        )

    return {
        "status": "success",
        "parametros": {
            "vp": req.vp,
            "vond": req.vond,
            "vd": req.vd,
            "n_saidas": len(req.saidas),
        },
        "data": asdict(resultado),
    }


@app.post(
    "/api/v1/dimensionar/resumo",
    summary="Resumo de componentes (lista de compras)",
    tags=["Motor"],
    status_code=status.HTTP_200_OK,
)
def api_dimensionar_resumo(req: DimensionarRequest):
    """
    Versão enxuta do cálculo completo — retorna apenas os **componentes
    comerciais selecionados**, ideal para integração com agentes de compra
    ou geração de BOM (Bill of Materials).
    """
    lista_saidas = [
        Saida(tipo=s.tipo, Vout=s.Vout, IL=s.IL, R2=s.R2)
        for s in req.saidas
    ]

    try:
        r = dimensionar(
            saidas=lista_saidas,
            Vp=req.vp,
            Vond=req.vond,
            Vd=req.vd,
        )
    except Exception as e:
        log.error(f"Falha no motor (resumo): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Falha de processamento no Motor Volpiano: {e}",
        )

    reguladores = []
    for rs in r.res_saidas:
        reg = {
            "saida": rs.indice,
            "tipo": rs.tipo,
            "Vout_desejado": rs.Vout_desejado,
            "IL": rs.IL,
            "modelo": rs.modelo,
            "Vout_real": round(rs.Vout_real, 4),
            "Pd_W": round(rs.Pd, 4),
            "alerta_dissipador": rs.alerta_dissipador,
        }
        if rs.R1_com:
            reg["R1_ohm"] = rs.R1_com
            reg["R2_ohm"] = rs.R2
        reguladores.append(reg)

    return {
        "status": "success",
        "bom": {
            "transformador": {
                "codigo": r.TR_cod,
                "Vs_V": r.TR_Vs,
                "Is_A": r.TR_Is,
                "Ss_VA": r.TR_Ss,
                "encontrado_no_banco": r.TR_encontrado,
            },
            "capacitor": {
                "C_uF": r.C_com,
                "V_isolacao": r.V_cap_com,
            },
            "diodo": r.diodo,
            "fusiveis": {
                "secundario_A": r.Fus_s,
                "primario_A": r.Fus_p,
            },
            "reguladores": reguladores,
        },
        "alertas": r.alertas,
    }


@app.get(
    "/api/v1/componentes/diodos",
    summary="Banco de diodos disponíveis",
    tags=["Banco de Dados"],
)
def listar_diodos():
    """Retorna todos os diodos retificadores disponíveis no banco de dados."""
    return {
        "status": "success",
        "total": len(bd.DIODOS),
        "diodos": [
            {
                "modelo":    d[0],
                "Ifav_A":    d[1],
                "IFrms_A":   d[2],
                "VRRM_V":    d[3],
                "IFsm_A":    d[4],
                "Vf_V":      d[5],
                "descricao": d[6],
            }
            for d in bd.DIODOS
        ],
    }


@app.get(
    "/api/v1/componentes/reguladores",
    summary="Banco de reguladores disponíveis",
    tags=["Banco de Dados"],
)
def listar_reguladores():
    """Retorna reguladores fixos (LM78xx) e variáveis (LM317/350/338)."""
    fixos = [
        {
            "modelo": r[1], "Vout_V": r[0],
            "Vin_min_V": r[2], "Vin_max_V": r[3],
            "Imax_A": r[4], "Vdropout_V": r[5],
        }
        for r in bd.REGULADORES_78XX
    ]
    variaveis = [
        {
            "modelo": r[0], "Vout_min_V": r[1], "Vout_max_V": r[2],
            "Vin_max_V": r[3], "Imax_A": r[4],
            "Vref_V": r[5], "Vdropout_V": r[6],
        }
        for r in bd.REGULADORES_VARIAVEIS
    ]
    return {
        "status": "success",
        "fixos": {"total": len(fixos), "reguladores": fixos},
        "variaveis": {"total": len(variaveis), "reguladores": variaveis},
    }


@app.get(
    "/api/v1/componentes/transformadores",
    summary="Banco de transformadores disponíveis",
    tags=["Banco de Dados"],
)
def listar_transformadores():
    """Retorna todos os transformadores do banco de dados."""
    return {
        "status": "success",
        "total": len(bd.TRANSFORMADORES),
        "transformadores": [
            {"Vs_V": t[0], "Is_A": t[1], "Ss_VA": t[2], "codigo": t[3]}
            for t in bd.TRANSFORMADORES
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
#  EXECUÇÃO
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("⚡ Iniciando H.E.L.I.O.S. API na porta 8000...")
    print("   Docs: http://127.0.0.1:8000/docs")
    print("   ReDoc: http://127.0.0.1:8000/redoc")
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True, log_level="info")