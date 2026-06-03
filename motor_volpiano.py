"""
motor_volpiano.py
=================
Motor de cálculo para dimensionamento de fonte linear DC.
Recebe uma lista de saídas e executa todas as etapas do Memorial de Cálculo
Volpiano, devolvendo um dict completo com todos os resultados intermediários
e finais — pronto para ser exibido na interface ou exportado para PDF.

Uso:
    from motor_volpiano import dimensionar
    resultado = dimensionar(saidas, Vp=110, Vond=3.0, Vd=0.7)
"""

import math
from dataclasses import dataclass, field
from typing import List, Optional

from schade_engine import fig3 as schade_fig3, fig4 as schade_fig4
import banco_dados as bd


# ─────────────────────────────────────────────────────────────────────────────
#  CONSTANTES
# ─────────────────────────────────────────────────────────────────────────────

FREQ_REDE = 60.0                        # Hz (Brasil)
OMEGA_S   = 2 * math.pi * FREQ_REDE * 2  # 120 Hz (onda completa)
N_RETIF   = 2                           # ponte de Graetz
KI        = 0.75    # fator segurança corrente diodo
KV        = 2.5     # fator segurança tensão reversa
KF        = 1.25    # fator segurança fusível
RS_PERC   = 0.01    # Rs = 1% de Refetiva


# ─────────────────────────────────────────────────────────────────────────────
#  ESTRUTURA DE SAÍDA
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Saida:
    """Define uma saída da fonte."""
    tipo: str        # "fixa" ou "variavel"
    Vout: float      # V — tensão desejada (ou máxima para variável)
    IL: float        # A — corrente de carga
    R2: float = 10000.0  # Ω — apenas para variável


@dataclass
class ResultadoSaida:
    """Resultado de dimensionamento de um regulador."""
    indice: int
    tipo: str
    Vout_desejado: float
    IL: float
    modelo: str
    exato: bool
    Vout_real: float
    Vreg: float
    Pd: float
    alerta_dissipador: bool
    alerta_corrente: bool
    # Variável
    R1_calc: Optional[float] = None
    R1_com: Optional[int]   = None
    R2: Optional[float]     = None
    # Fixo
    Vin_min: Optional[float] = None
    Vin_max: Optional[float] = None
    sugestao_alt: Optional[str] = None


@dataclass
class Resultado:
    """Resultado completo do dimensionamento."""
    # Entradas
    Vp: float
    Vond: float
    Vd: float
    saidas: List[Saida]

    # 1. Transformador (cálculo)
    Vout_max: float = 0
    IL_total: float = 0
    Vinmin_tr: float = 0
    Vinmedia_tr: float = 0
    Vsmax: float = 0
    Vsef: float = 0

    # 2. Verificação reguladores
    Vinmedia: float = 0
    Vinmax: float = 0
    Vinmin: float = 0
    reguladores_ok: bool = True

    # 3. Capacitor
    C_calc_uF: float = 0
    Vcap_min: float = 0
    C_com: int = 0
    V_cap_com: int = 0

    # 4. Diodos
    Ifav: float = 0
    Vrev_d: float = 0
    Refetiva: float = 0
    Rs: float = 0
    x_param: float = 0
    Rs_nRL_pct: float = 0
    curva_fig3: float = 0
    curva_fig4: float = 0
    IFrms: float = 0
    IFrm: float = 0
    Ifav_min: float = 0
    IFrms_min: float = 0
    VRRM: float = 0
    RD: float = 0
    IFsm: float = 0
    tau_ms: float = 0
    diodo: Optional[dict] = None

    # 5. Fusíveis
    Is: float = 0
    KT: float = 0
    Ip: float = 0
    Fus_s: float = 0
    Fus_p: float = 0

    # 6. Transformador comercial
    Ss: float = 0
    TR_cod: str = ""
    TR_Vs: float = 0
    TR_Is: float = 0
    TR_Ss: float = 0
    TR_encontrado: bool = False

    # 7. Reguladores por saída
    res_saidas: List[ResultadoSaida] = field(default_factory=list)

    # Alertas globais
    alertas: List[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
#  MOTOR PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def dimensionar(saidas: List[Saida], Vp: float = 110,
                Vond: float = 3.0, Vd: float = 0.7) -> Resultado:
    """
    Executa o dimensionamento completo da fonte.

    Parâmetros
    ----------
    saidas : lista de Saida
    Vp     : tensão de rede (110 ou 220 V)
    Vond   : ripple máximo (V)
    Vd     : queda de tensão por diodo (V)

    Retorno
    -------
    Resultado com todos os valores calculados e componentes comerciais.
    """
    r = Resultado(Vp=Vp, Vond=Vond, Vd=Vd, saidas=saidas)

    _etapa1_transformador(r)
    _etapa2_verificacao(r)
    _etapa3_capacitor(r)
    _etapa4_diodos(r)
    _etapa5_fusiveis(r)
    _etapa6_transformador_comercial(r)
    _etapa7_reguladores(r)
    _alertas_globais(r)

    return r


# ─────────────────────────────────────────────────────────────────────────────
#  ETAPAS INTERNAS
# ─────────────────────────────────────────────────────────────────────────────

def _etapa1_transformador(r: Resultado):
    """
    Regra de ouro: usar MAIOR Vout como pior caso e SOMA de correntes.
    """
    r.Vout_max  = max(s.Vout for s in r.saidas)
    r.IL_total  = sum(s.IL   for s in r.saidas)

    r.Vinmin_tr   = r.Vout_max + 3.0
    r.Vinmedia_tr = r.Vinmin_tr + r.Vond / 2
    r.Vsmax       = r.Vinmedia_tr + 2 * r.Vd + r.Vond / 2
    r.Vsef        = r.Vsmax / math.sqrt(2)


def _etapa2_verificacao(r: Resultado):
    """
    Calcula Vinmedia, Vinmax, Vinmin a partir de Vsmax e
    verifica cada regulador na sua faixa operacional.
    """
    r.Vinmedia = (r.Vsmax - 2 * r.Vd) - r.Vond / 2
    r.Vinmax   = r.Vinmedia + r.Vond / 2
    r.Vinmin   = r.Vinmedia - r.Vond / 2

    ok_geral = True
    for s in r.saidas:
        if s.tipo == "variavel":
            ok1 = 3.0 <= (r.Vinmin - s.Vout) <= 35.0
            ok2 = 3.0 <= (r.Vinmax - s.Vout) <= 35.0
            if not (ok1 and ok2):
                ok_geral = False
                r.alertas.append(
                    f"Saída variável {s.Vout}V: dropout LM317 fora de faixa — "
                    f"Vin-Vout = {r.Vinmin-s.Vout:.1f}V (mín) / {r.Vinmax-s.Vout:.1f}V (máx)"
                )
        else:
            reg = bd.regulador_fixo(int(s.Vout), r.Vinmax)
            vmn = reg["Vin_min"] or 0
            vmx = reg["Vin_max"] or 99
            ok1 = vmn <= r.Vinmin <= vmx
            ok2 = vmn <= r.Vinmax <= vmx
            if not (ok1 and ok2):
                ok_geral = False
                r.alertas.append(
                    f"Saída fixa {s.Vout}V ({reg['modelo']}): Vin fora da faixa "
                    f"[{vmn}–{vmx}V] — calculado [{r.Vinmin:.1f}–{r.Vinmax:.1f}V]"
                )
    r.reguladores_ok = ok_geral


def _etapa3_capacitor(r: Resultado):
    Freq = OMEGA_S / (2 * math.pi)   # 120 Hz
    r.C_calc_uF = (r.IL_total / (Freq * r.Vond)) * 1e6
    r.Vcap_min  = r.Vsmax * 1.4
    r.C_com, r.V_cap_com = bd.capacitor_comercial(r.C_calc_uF, r.Vcap_min)


def _etapa4_diodos(r: Resultado):
    r.Ifav   = r.IL_total / 2
    r.Vrev_d = math.sqrt(2) * r.Vsef

    r.Refetiva  = r.Vinmedia / r.IL_total
    r.Rs        = RS_PERC * r.Refetiva
    C1          = r.C_com * 1e-6
    r.x_param   = N_RETIF * OMEGA_S * r.Refetiva * C1
    r.Rs_nRL_pct = (1 / N_RETIF) * (r.Rs / r.Refetiva) * 100

    r.curva_fig3 = schade_fig3(r.x_param, r.Rs_nRL_pct)
    r.curva_fig4 = schade_fig4(r.x_param, r.Rs_nRL_pct)
    r.IFrms      = r.curva_fig3 * r.Ifav
    r.IFrm       = r.curva_fig4 * r.Ifav

    r.Ifav_min  = r.IL_total / KI
    r.IFrms_min = r.IFrms    / KI
    r.VRRM      = KV * r.Vsmax

    # Corrente de surto
    Vdmax = 1.2; Id_ref = 3.0
    r.RD   = (Vdmax - r.Vd) / Id_ref
    r.IFsm = r.Vsmax / (r.Rs + 2 * r.RD)
    r.tau_ms = 18.0 * C1 * 1e3   # Rth_ref × C1

    # Seleção automática do diodo
    r.diodo = bd.diodo_comercial(r.Ifav_min, r.IFrms_min, r.VRRM)
    if r.diodo is None:
        r.alertas.append(
            f"Nenhum diodo no banco atende Ifav≥{r.Ifav_min:.1f}A, "
            f"IFrms≥{r.IFrms_min:.1f}A, VRRM≥{r.VRRM:.0f}V — dimensionar ponte sob medida."
        )


def _etapa5_fusiveis(r: Resultado):
    r.Is  = math.sqrt(2) * r.IFrms
    r.KT  = r.Vp / r.Vsef
    r.Ip  = r.Is / r.KT
    r.Fus_s = bd.fusivel_comercial(KF * r.Is)
    r.Fus_p = bd.fusivel_comercial(KF * r.Ip)


def _etapa6_transformador_comercial(r: Resultado):
    r.Ss = r.Vsef * r.Is
    tr   = bd.transformador_comercial(r.Vsef, r.Is, r.Ss)
    if tr:
        r.TR_Vs, r.TR_Is, r.TR_Ss, r.TR_cod = tr
        r.TR_encontrado = True
    else:
        r.TR_Vs  = round(r.Vsef, 1)
        r.TR_Is  = round(r.Is,   1)
        r.TR_Ss  = round(r.Ss)
        r.TR_cod = "Sob encomenda"
        r.TR_encontrado = False
        r.alertas.append(
            f"Transformador {r.TR_Vs}V / {r.TR_Is}A / {r.TR_Ss}VA não encontrado "
            f"no banco — dimensionar sob encomenda."
        )


def _etapa7_reguladores(r: Resultado):
    r.res_saidas = []

    for i, s in enumerate(r.saidas):
        Vreg = r.Vinmax - s.Vout
        Pd   = Vreg * s.IL

        if s.tipo == "variavel":
            lm = bd.lm317_resistores(s.Vout, s.IL, s.R2)
            rs = ResultadoSaida(
                indice=i+1, tipo="variavel",
                Vout_desejado=s.Vout, IL=s.IL,
                modelo=lm["regulador"], exato=True,
                Vout_real=lm["Vout_real"],
                Vreg=Vreg, Pd=Pd,
                alerta_dissipador=(Pd > 1.0),
                alerta_corrente=(s.IL > 5.0),
                R1_calc=lm["R1_calc"], R1_com=lm["R1_com"],
                R2=lm["R2"],
            )
            # Alerta se LM317 insuficiente
            if "LM338" in lm["regulador"] or "LM350" in lm["regulador"]:
                r.alertas.append(
                    f"Saída {i+1} ({s.Vout}V/{s.IL}A): corrente acima do LM317 (1,5A) "
                    f"→ usando {lm['regulador']}."
                )

        else:
            reg = bd.regulador_fixo(int(s.Vout), r.Vinmax)
            alt = None
            if not reg["exato"] or reg["modelo"] is None:
                lm_alt = bd.lm317_resistores(s.Vout, s.IL)
                alt = (f"LM317 R1={lm_alt['R1_com']}Ω / R2={lm_alt['R2']:.0f}Ω "
                       f"→ Vout={lm_alt['Vout_real']:.2f}V")
            rs = ResultadoSaida(
                indice=i+1, tipo="fixa",
                Vout_desejado=s.Vout, IL=s.IL,
                modelo=reg["modelo"] or "LM317",
                exato=reg["exato"],
                Vout_real=reg["Vout_real"],
                Vreg=Vreg, Pd=Pd,
                alerta_dissipador=(Pd > 1.0),
                alerta_corrente=(s.IL > (reg["Imax"] or 1.5)),
                Vin_min=reg["Vin_min"],
                Vin_max=reg["Vin_max"],
                sugestao_alt=alt,
            )
            if rs.alerta_corrente:
                r.alertas.append(
                    f"Saída {i+1} ({s.Vout}V): IL={s.IL}A excede Imax do {reg['modelo']} "
                    f"(1,5A) — usar LM338 ou transistor pass externo."
                )

        r.res_saidas.append(rs)


def _alertas_globais(r: Resultado):
    """Alertas adicionais sobre o projeto como um todo."""
    Pd_total = sum(rs.Pd for rs in r.res_saidas)
    if Pd_total > 10:
        r.alertas.append(
            f"Potência dissipada total nos reguladores: {Pd_total:.1f}W — "
            f"considerar dissipadores adequados e ventilação do gabinete."
        )
    if not r.TR_encontrado:
        pass  # já adicionado em etapa6
    if r.Vinmax > 35:
        r.alertas.append(
            f"Vinmax = {r.Vinmax:.1f}V — verificar compatibilidade com reguladores "
            f"(maioria limita em 35–40V)."
        )


# ─────────────────────────────────────────────────────────────────────────────
#  SELF-TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Teste motor_volpiano.py ===\n")

    # Projeto do PDF Volpiano: 12V/0.5A, 5V/0.6A, 18V/0.75A
    saidas = [
        Saida("variavel", 18.0, 0.75, R2=10000),
        Saida("fixa",     12.0, 0.50),
        Saida("fixa",      5.0, 0.60),
    ]
    r = dimensionar(saidas, Vp=110, Vond=3.0, Vd=0.7)

    print(f"Vout_max={r.Vout_max}V  IL_total={r.IL_total}A")
    print(f"Vsmax={r.Vsmax:.2f}V  Vsef={r.Vsef:.2f}V")
    print(f"Vinmedia={r.Vinmedia:.1f}V  Vinmax={r.Vinmax:.1f}V  Vinmin={r.Vinmin:.1f}V")
    print(f"C={r.C_calc_uF:.0f}µF → {r.C_com}µF/{r.V_cap_com}V")
    print(f"Ifav={r.Ifav:.3f}A  IFrms={r.IFrms:.3f}A  VRRM={r.VRRM:.1f}V")
    print(f"x_param={r.x_param:.2f}  Rs/nRL={r.Rs_nRL_pct:.3f}%")
    print(f"Fig3={r.curva_fig3:.3f}  Fig4={r.curva_fig4:.3f}")
    print(f"Diodo: {r.diodo}")
    print(f"IFsm={r.IFsm:.1f}A")
    print(f"Fus_s={r.Fus_s}A  Fus_p={r.Fus_p}A")
    print(f"Transformador: {r.TR_cod} ({r.TR_Vs}V/{r.TR_Is}A/{r.TR_Ss}VA)")
    print()
    for rs in r.res_saidas:
        print(f"Saída {rs.indice} [{rs.tipo}] {rs.Vout_desejado}V/{rs.IL}A → "
              f"{rs.modelo}  Pd={rs.Pd:.2f}W  {'⚠ diss' if rs.alerta_dissipador else ''}")
        if rs.R1_com:
            print(f"  R1={rs.R1_com}Ω  R2={rs.R2:.0f}Ω  Vout_real={rs.Vout_real:.2f}V")
        if rs.sugestao_alt:
            print(f"  Alt: {rs.sugestao_alt}")
    print()
    if r.alertas:
        print("Alertas:")
        for a in r.alertas:
            print(f"  ⚠ {a}")
    else:
        print("Sem alertas — projeto dentro dos parâmetros.")

    print("\n--- Teste 2: 1 saída fixa 9V/2A (excede LM78xx) ---")
    r2 = dimensionar([Saida("fixa", 9.0, 2.0)], Vp=110, Vond=3.0, Vd=0.7)
    for a in r2.alertas:
        print(f"  ⚠ {a}")
    print(f"  Regulador: {r2.res_saidas[0].modelo}")
