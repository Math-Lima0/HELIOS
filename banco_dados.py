"""
banco_dados.py
==============
Banco de dados de componentes comerciais para o dimensionador de fonte linear.
Todos os valores seguem catálogos reais (série E24, capacitores comerciais,
transformadores padrão brasileiros, reguladores TO-220).
"""

# ─────────────────────────────────────────────────────────────────────────────
#  RESISTORES — Série E24 (10Ω a 100kΩ)
# ─────────────────────────────────────────────────────────────────────────────

_E24_BASE = [1.0,1.1,1.2,1.3,1.5,1.6,1.8,2.0,2.2,2.4,2.7,3.0,
             3.3,3.6,3.9,4.3,4.7,5.1,5.6,6.2,6.8,7.5,8.2,9.1]

RESISTORES_E24 = []
for _dec in [10, 100, 1000, 10000]:
    for _v in _E24_BASE:
        RESISTORES_E24.append(round(_v * _dec))


def resistor_comercial(valor_ohm: float) -> int:
    """Menor resistor E24 >= valor_ohm."""
    for r in RESISTORES_E24:
        if r >= valor_ohm:
            return r
    return RESISTORES_E24[-1]


# ─────────────────────────────────────────────────────────────────────────────
#  CAPACITORES ELETROLÍTICOS (µF, V_isolação)
# ─────────────────────────────────────────────────────────────────────────────

CAPACITORES = sorted([
    # 25V
    (220,25),(330,25),(470,25),(680,25),(1000,25),(1500,25),(2200,25),
    (3300,25),(4700,25),(6800,25),(10000,25),
    # 35V
    (100,35),(220,35),(470,35),(1000,35),(2200,35),(4700,35),(6800,35),(10000,35),
    # 50V
    (47,50),(100,50),(220,50),(470,50),(1000,50),(1500,50),(2200,50),
    (3300,50),(4700,50),(5600,50),(6800,50),(10000,50),(15000,50),(22000,50),
    # 63V
    (47,63),(100,63),(220,63),(470,63),(1000,63),(2200,63),(4700,63),
    (6800,63),(10000,63),(15000,63),
    # 100V
    (47,100),(100,100),(220,100),(470,100),(1000,100),(2200,100),
    (4700,100),(6800,100),(10000,100),
])


def capacitor_comercial(c_min_uf: float, v_min: float) -> tuple:
    """Menor capacitor comercial com C >= c_min_uf e V >= v_min."""
    for c, v in CAPACITORES:
        if c >= c_min_uf and v >= v_min:
            return c, v
    return CAPACITORES[-1]


# ─────────────────────────────────────────────────────────────────────────────
#  FUSÍVEIS (A)
# ─────────────────────────────────────────────────────────────────────────────

FUSIVEIS = [0.1, 0.15, 0.2, 0.25, 0.315, 0.4, 0.5, 0.63, 0.8,
            1.0, 1.25, 1.6, 2.0, 2.5, 3.15, 4.0, 5.0, 6.3,
            8.0, 10.0, 12.5, 16.0, 20.0, 25.0, 32.0]


def fusivel_comercial(i_min: float) -> float:
    """Menor fusível comercial >= i_min."""
    for f in FUSIVEIS:
        if f >= i_min:
            return f
    return FUSIVEIS[-1]


# ─────────────────────────────────────────────────────────────────────────────
#  TRANSFORMADORES (Vs V, Is A, Ss VA, código)
# ─────────────────────────────────────────────────────────────────────────────

TRANSFORMADORES = [
    # Vs   Is    Ss    código
    ( 6,  0.5,   5,  "T06-0.5A"),
    ( 6,  1.0,  10,  "T06-1A"),
    ( 6,  2.0,  20,  "T06-2A"),
    ( 6,  3.0,  30,  "T06-3A"),
    ( 6,  5.0,  50,  "T06-5A"),
    ( 9,  0.5,   7,  "T09-0.5A"),
    ( 9,  1.0,  15,  "T09-1A"),
    ( 9,  2.0,  30,  "T09-2A"),
    ( 9,  3.0,  40,  "T09-3A"),
    ( 9,  5.0,  60,  "T09-5A"),
    (12,  0.5,  10,  "T12-0.5A"),
    (12,  1.0,  20,  "T12-1A"),
    (12,  2.0,  30,  "T12-2A"),
    (12,  3.0,  50,  "T12-3A"),
    (12,  5.0,  50,  "I9"),
    (12,  8.0, 120,  "T12-8A"),
    (12, 10.0, 150,  "T12-10A"),
    (15,  0.5,  10,  "T15-0.5A"),
    (15,  1.0,  20,  "T15-1A"),
    (15,  2.0,  40,  "T15-2A"),
    (15,  3.0,  50,  "T15-3A"),
    (15,  5.0,  80,  "T15-5A"),
    (15, 10.0, 160,  "T15-10A"),
    (18,  1.0,  30,  "I7A"),
    (18,  2.0,  40,  "I59"),
    (18,  3.0,  54,  "I549"),
    (18,  5.0,  90,  "306574"),
    (18,  8.0, 150,  "T18-8A"),
    (18, 10.0, 200,  "T18-10A"),
    (24,  1.0,  30,  "T24-1A"),
    (24,  2.0,  50,  "T24-2A"),
    (24,  3.0,  80,  "T24-3A"),
    (24,  5.0, 130,  "T24-5A"),
    (24, 10.0, 300,  "T24-10A"),
    (28,  2.0,  60,  "T28-2A"),
    (28,  5.0, 150,  "T28-5A"),
    (30,  2.0,  70,  "T30-2A"),
    (30,  5.0, 160,  "T30-5A"),
]


def transformador_comercial(vs_min: float, is_min: float, ss_min: float):
    """
    Menor transformador comercial que atende Vs >= vs_min, Is >= is_min, Ss >= ss_min.
    Retorna (Vs, Is, Ss, código) ou None.
    """
    cands = [(vs, Is, ss, cod) for vs, Is, ss, cod in TRANSFORMADORES
             if vs >= vs_min and Is >= is_min and ss >= ss_min]
    return min(cands, key=lambda x: x[2]) if cands else None


# ─────────────────────────────────────────────────────────────────────────────
#  REGULADORES DE TENSÃO
# ─────────────────────────────────────────────────────────────────────────────

# LM78xx positivos fixos
# (Vout, modelo, Vin_min, Vin_max, Imax_A, Vdropout_min)
REGULADORES_78XX = [
    ( 5,  "LM7805",  7.5,  35, 1.5, 2.0),
    ( 6,  "LM7806",  8.5,  35, 1.5, 2.0),
    ( 8,  "LM7808", 10.5,  35, 1.5, 2.0),
    ( 9,  "LM7809", 11.5,  35, 1.5, 2.0),
    (10,  "LM7810", 12.5,  35, 1.5, 2.0),
    (12,  "LM7812", 14.5,  35, 1.5, 2.0),
    (15,  "LM7815", 17.5,  35, 1.5, 2.0),
    (18,  "LM7818", 21.0,  35, 1.5, 3.0),
    (24,  "LM7824", 27.0,  40, 1.5, 3.0),
]

# Reguladores variáveis positivos
# (modelo, Vout_min, Vout_max, Vin_max, Imax_A, Vref, Vdropout_min)
REGULADORES_VARIAVEIS = [
    ("LM317",  1.25, 37.0, 40, 1.5,  1.25, 3.0),
    ("LM350",  1.25, 33.0, 35, 3.0,  1.25, 3.0),
    ("LM338",  1.25, 32.0, 35, 5.0,  1.25, 3.0),
]

# Diodos retificadores comuns
# (modelo, Ifav_A, IFrms_A, VRRM_V, IFsm_A, Vf_V, descricao)
DIODOS = [
    ("1N4001",  1.0,  1.0,   50,  30,  1.1, "GP 1A/50V"),
    ("1N4002",  1.0,  1.0,  100,  30,  1.1, "GP 1A/100V"),
    ("1N4003",  1.0,  1.0,  200,  30,  1.1, "GP 1A/200V"),
    ("1N4004",  1.0,  1.0,  400,  30,  1.1, "GP 1A/400V"),
    ("1N4005",  1.0,  1.0,  600,  30,  1.1, "GP 1A/600V"),
    ("1N4006",  1.0,  1.0,  800,  30,  1.1, "GP 1A/800V"),
    ("1N4007",  1.0,  1.0, 1000,  30,  1.1, "GP 1A/1000V"),
    ("BY127",   1.0,  1.0, 1250,  35,  1.1, "GP 1A/1250V"),
    ("BY255",   3.0,  3.0, 1300,  80,  1.1, "GP 3A/1300V"),
    ("SK3",     3.0,  4.0, 1000,  80,  1.0, "Schottky-like 3A/1000V"),
    ("SK5",     5.0,  6.0, 1000, 150,  1.0, "5A/1000V"),
    ("MR750",   6.0,  6.0,  600, 300,  1.1, "6A/600V"),
    ("MR756",   6.0,  6.0,  600, 300,  1.1, "6A/600V"),
    ("10A10",  10.0, 12.0, 1000, 400,  1.1, "10A/1000V"),
    ("KBPC1010",10.0,12.0, 1000, 400,  1.1, "Ponte 10A/1000V"),
    ("KBPC2510",25.0,30.0, 1000, 300,  1.1, "Ponte 25A/1000V"),
]


def diodo_comercial(ifav_min: float, ifrms_min: float, vrrm_min: float):
    """
    Seleciona o menor diodo que atende:
      Ifav  >= ifav_min
      IFrms >= ifrms_min
      VRRM  >= vrrm_min
    Retorna dict com os parâmetros ou None.
    """
    cands = [d for d in DIODOS
             if d[1] >= ifav_min and d[2] >= ifrms_min and d[3] >= vrrm_min]
    if not cands:
        return None
    # Menor Ifav que atende (mais econômico)
    melhor = min(cands, key=lambda d: (d[1], d[3]))
    return {
        "modelo": melhor[0], "Ifav": melhor[1], "IFrms": melhor[2],
        "VRRM": melhor[3],   "IFsm": melhor[4], "Vf":   melhor[5],
        "descricao": melhor[6],
    }


def regulador_fixo(vout_v: int, vinmax: float):
    """
    Busca LM78xx exato para vout_v com vinmax compatível.
    Se não existir exato, retorna o mais próximo + sugere LM317/LM350/LM338.
    Retorna dict: modelo, Vout_real, Vin_min, Vin_max, Imax, exato, sugestao_variavel
    """
    # 1. Exato e dentro da faixa
    for vr, mod, vmn, vmx, imax, vdrop in REGULADORES_78XX:
        if vr == vout_v and vmn <= vinmax <= vmx:
            return dict(modelo=mod, Vout_real=vr, Vin_min=vmn, Vin_max=vmx,
                        Imax=imax, Vdrop=vdrop, exato=True, sugestao_variavel=None)
    # 2. Mais próximo compatível
    compat = [(vr,mod,vmn,vmx,imax,vdrop) for vr,mod,vmn,vmx,imax,vdrop in REGULADORES_78XX
              if vmn <= vinmax <= vmx]
    if compat:
        vr,mod,vmn,vmx,imax,vdrop = min(compat, key=lambda x: abs(x[0]-vout_v))
        return dict(modelo=mod, Vout_real=vr, Vin_min=vmn, Vin_max=vmx,
                    Imax=imax, Vdrop=vdrop, exato=False, sugestao_variavel="LM317")
    return dict(modelo=None, Vout_real=vout_v, Vin_min=None, Vin_max=None,
                Imax=None, Vdrop=None, exato=False, sugestao_variavel="LM317")


def regulador_variavel_adequado(il: float) -> dict:
    """
    Retorna o menor regulador variável que suporta a corrente IL.
    LM317 (1.5A) → LM350 (3A) → LM338 (5A).
    """
    for mod, vmin, vmax, vinmax, imax, vref, vdrop in REGULADORES_VARIAVEIS:
        if imax >= il:
            return dict(modelo=mod, Imax=imax, Vout_min=vmin,
                        Vout_max=vmax, Vin_max=vinmax, Vref=vref, Vdrop=vdrop)
    # Acima de 5A: paralelo de LM338
    n = int(il / 5.0) + 1
    return dict(modelo=f"{n}× LM338 paralelo", Imax=n*5.0,
                Vout_min=1.25, Vout_max=32.0, Vin_max=35, Vref=1.25, Vdrop=3.0)


def lm317_resistores(vout: float, il: float, R2: float = 10000.0) -> dict:
    """
    Calcula R1, R2 e Vout real para o LM317/LM350/LM338.
    Ajusta automaticamente R2 se necessário para manter R1 na faixa útil (100Ω–10kΩ).
    """
    reg = regulador_variavel_adequado(il)
    Vref = reg["Vref"]

    # Tenta com R2 fornecido
    R1_calc = (R2 * Vref) / (vout - Vref)
    R1_com  = resistor_comercial(R1_calc)
    Vout_r  = Vref * (1 + R2 / R1_com)

    # Se R1 calculado < 100Ω, reduzir R2
    if R1_calc < 100:
        R2 = round(R1_calc * (vout - Vref) / Vref * 10) * 10
        R2 = max(1000, R2)
        R1_calc = (R2 * Vref) / (vout - Vref)
        R1_com  = resistor_comercial(R1_calc)
        Vout_r  = Vref * (1 + R2 / R1_com)

    return dict(
        regulador=reg["modelo"],
        R1_calc=R1_calc, R1_com=R1_com,
        R2=R2, Vout_real=Vout_r,
        Vref=Vref, Vdrop=reg["Vdrop"],
    )


# ─────────────────────────────────────────────────────────────────────────────
#  SELF-TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Testes banco_dados.py ===\n")

    print("Resistores:")
    for v in [100, 746, 909, 3333]:
        print(f"  {v}Ω → E24: {resistor_comercial(v)}Ω")

    print("\nCapacitores:")
    for c, v in [(5138, 35.6), (4167, 31.4), (200, 20)]:
        cc, vc = capacitor_comercial(c, v)
        print(f"  ≥{c}µF / ≥{v}V → {cc}µF / {vc}V")

    print("\nDiodos:")
    for ifav, ifrms, vrrm in [(2.5, 4.0, 64), (0.8, 1.0, 100), (10, 12, 1000)]:
        d = diodo_comercial(ifav, ifrms, vrrm)
        print(f"  Ifav≥{ifav}A, IFrms≥{ifrms}A, VRRM≥{vrrm}V → {d['modelo']} ({d['descricao']})")

    print("\nReguladores fixos:")
    for vout, vinmax in [(5, 24), (9, 21), (7, 18), (13, 20)]:
        r = regulador_fixo(vout, vinmax)
        print(f"  Vout={vout}V, Vinmax={vinmax}V → {r['modelo']} (exato={r['exato']})")

    print("\nReguladores variáveis (LM317/350/338):")
    for vout, il in [(18, 0.75), (12, 2.5), (5, 5.5)]:
        r = lm317_resistores(vout, il)
        print(f"  Vout={vout}V, IL={il}A → {r['regulador']}: R1={r['R1_com']}Ω R2={r['R2']}Ω Vout_real={r['Vout_real']:.2f}V")

    print("\nTransformadores:")
    for vs, Is, ss in [(13.7, 4.7, 65), (17.9, 6.6, 120), (8, 2, 25)]:
        t = transformador_comercial(vs, Is, ss)
        print(f"  Vs≥{vs}V, Is≥{Is}A, Ss≥{ss}VA → {t}")
