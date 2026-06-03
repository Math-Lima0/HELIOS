"""
=============================================================
  DIMENSIONADOR DE FONTE LINEAR — MÚLTIPLAS SAÍDAS
  Baseado no Memorial de Cálculo Volpiano
  Suporta 1, 2 ou 3 saídas | Fixas (LM78xx) e Variável (LM317)
=============================================================
"""

import math


# ══════════════════════════════════════════════════════════════
#  CURVAS TABELADAS — FIGURA 3 e FIGURA 4 (digitalizadas)
#  FIG3: IFrms/Ifav  vs  n·ωs·RL·C  →  Y LINEAR, X log
#  FIG4: IFrm/Ifav   vs  n·ωs·RL·C  →  Y log,    X log
# ══════════════════════════════════════════════════════════════

FIG3 = {
    0.02:  [(1,2.05),(2,2.35),(3,2.56),(5,2.82),(7,3.01),(10,3.23),(15,3.50),
            (20,3.68),(30,3.95),(50,4.28),(70,4.50),(100,4.72),(200,5.05),
            (300,5.20),(500,5.38),(1000,5.55)],
    0.05:  [(1,2.00),(2,2.27),(3,2.47),(5,2.71),(7,2.89),(10,3.10),(15,3.35),
            (20,3.52),(30,3.77),(50,4.08),(70,4.28),(100,4.48),(200,4.80),
            (300,4.94),(500,5.10),(1000,5.26)],
    0.1:   [(1,1.93),(2,2.19),(3,2.38),(5,2.60),(7,2.77),(10,2.97),(15,3.20),
            (20,3.36),(30,3.59),(50,3.88),(70,4.07),(100,4.25),(200,4.55),
            (300,4.68),(500,4.83),(1000,4.98)],
    0.2:   [(1,1.84),(2,2.08),(3,2.26),(5,2.46),(7,2.62),(10,2.80),(15,3.02),
            (20,3.16),(30,3.37),(50,3.63),(70,3.80),(100,3.97),(200,4.23),
            (300,4.35),(500,4.49),(1000,4.62)],
    0.5:   [(1,1.60),(2,1.82),(3,1.98),(5,2.17),(7,2.31),(10,2.48),(15,2.66),
            (20,2.80),(30,3.00),(50,3.25),(70,3.42),(100,3.58),(200,3.78),
            (300,3.88),(500,4.00),(1000,4.12)],
    1.0:   [(1,1.42),(2,1.60),(3,1.73),(5,1.89),(7,2.00),(10,2.14),(15,2.29),
            (20,2.40),(30,2.56),(50,2.75),(70,2.88),(100,3.01),(200,3.18),
            (300,3.26),(500,3.36),(1000,3.45)],
    2.0:   [(1,1.23),(2,1.38),(3,1.48),(5,1.60),(7,1.69),(10,1.80),(15,1.91),
            (20,1.99),(30,2.11),(50,2.26),(70,2.36),(100,2.45),(200,2.58),
            (300,2.64),(500,2.72),(1000,2.79)],
    5.0:   [(1,1.02),(2,1.12),(3,1.19),(5,1.28),(7,1.34),(10,1.41),(15,1.49),
            (20,1.54),(30,1.62),(50,1.72),(70,1.78),(100,1.84),(200,1.94),
            (300,1.98),(500,2.03),(1000,2.07)],
    10.0:  [(1,0.88),(2,0.96),(3,1.01),(5,1.07),(7,1.11),(10,1.17),(15,1.22),
            (20,1.26),(30,1.32),(50,1.39),(70,1.43),(100,1.48),(200,1.55),
            (300,1.58),(500,1.62),(1000,1.65)],
    30.0:  [(1,0.70),(2,0.76),(3,0.79),(5,0.83),(7,0.86),(10,0.90),(15,0.93),
            (20,0.95),(30,0.99),(50,1.03),(70,1.06),(100,1.09),(200,1.13),
            (300,1.15),(500,1.17),(1000,1.19)],
    100.0: [(1,0.55),(2,0.59),(3,0.61),(5,0.64),(7,0.66),(10,0.68),(15,0.71),
            (20,0.72),(30,0.74),(50,0.77),(70,0.79),(100,0.81),(200,0.84),
            (300,0.85),(500,0.86),(1000,0.87)],
}

FIG4 = {
    0.02:  [(1,2.2),(2,3.5),(3,4.7),(5,6.8),(7,8.8),(10,12),(15,17),(20,21),
            (30,29),(50,42),(70,55),(100,72),(200,110),(300,140),(500,190),(1000,270)],
    0.05:  [(1,2.0),(2,3.1),(3,4.1),(5,5.9),(7,7.6),(10,10.2),(15,14.4),(20,17.8),
            (30,24),(50,34),(70,44),(100,58),(200,88),(300,112),(500,150),(1000,212)],
    0.1:   [(1,1.80),(2,2.75),(3,3.65),(5,5.2),(7,6.7),(10,8.9),(15,12.5),(20,15.4),
            (30,20.5),(50,29),(70,37),(100,48),(200,72),(300,91),(500,120),(1000,170)],
    0.2:   [(1,1.58),(2,2.38),(3,3.12),(5,4.42),(7,5.65),(10,7.5),(15,10.4),(20,12.8),
            (30,16.8),(50,23.5),(70,30),(100,39),(200,57),(300,72),(500,95),(1000,133)],
    0.5:   [(1,0.80),(2,1.15),(3,1.48),(5,2.08),(7,2.62),(10,3.45),(15,4.70),(20,5.80),
            (30,7.55),(50,10.50),(70,13.5),(100,17.0),(200,24.5),(300,30.0),
            (500,39.0),(1000,55.0)],
    1.0:   [(1,0.62),(2,0.88),(3,1.12),(5,1.55),(7,1.95),(10,2.55),(15,3.45),(20,4.20),
            (30,5.45),(50,7.50),(70,9.5),(100,12),(200,17),(300,21),(500,27),(1000,38)],
    2.0:   [(1,0.45),(2,0.63),(3,0.80),(5,1.10),(7,1.38),(10,1.78),(15,2.38),(20,2.90),
            (30,3.72),(50,5.10),(70,6.4),(100,8.0),(200,11.5),(300,14),(500,18),(1000,25)],
    5.0:   [(1,0.27),(2,0.37),(3,0.46),(5,0.63),(7,0.79),(10,1.01),(15,1.33),(20,1.60),
            (30,2.04),(50,2.75),(70,3.45),(100,4.30),(200,6.1),(300,7.5),(500,9.5),(1000,13.2)],
    10.0:  [(1,0.17),(2,0.23),(3,0.29),(5,0.39),(7,0.48),(10,0.61),(15,0.81),(20,0.97),
            (30,1.22),(50,1.63),(70,2.04),(100,2.52),(200,3.55),(300,4.35),(500,5.5),(1000,7.6)],
    30.0:  [(1,0.075),(2,0.10),(3,0.12),(5,0.16),(7,0.20),(10,0.25),(15,0.33),(20,0.39),
            (30,0.49),(50,0.65),(70,0.81),(100,1.00),(200,1.40),(300,1.70),(500,2.15),(1000,2.95)],
    100.0: [(1,0.030),(2,0.040),(3,0.048),(5,0.063),(7,0.078),(10,0.097),(15,0.128),
            (20,0.152),(30,0.190),(50,0.252),(70,0.313),(100,0.385),(200,0.535),
            (300,0.650),(500,0.820),(1000,1.12)],
}


def _semilog_1d(x, pts):
    xs, ys = zip(*pts)
    if x <= xs[0]:  return ys[0]
    if x >= xs[-1]: return ys[-1]
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i+1]:
            t = (math.log10(x) - math.log10(xs[i])) / (math.log10(xs[i+1]) - math.log10(xs[i]))
            return ys[i] + t * (ys[i+1] - ys[i])


def _loglog_1d(x, pts):
    xs, ys = zip(*pts)
    if x <= xs[0]:  return ys[0]
    if x >= xs[-1]: return ys[-1]
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i+1]:
            t = (math.log10(x) - math.log10(xs[i])) / (math.log10(xs[i+1]) - math.log10(xs[i]))
            return 10 ** (math.log10(ys[i]) + t * (math.log10(ys[i+1]) - math.log10(ys[i])))


def _interp2d(x, rs, tabela, fn1d):
    chaves = sorted(tabela.keys())
    rs = max(chaves[0], min(chaves[-1], rs))
    if rs <= chaves[0]:  return fn1d(x, tabela[chaves[0]])
    if rs >= chaves[-1]: return fn1d(x, tabela[chaves[-1]])
    for i in range(len(chaves) - 1):
        k0, k1 = chaves[i], chaves[i+1]
        if k0 <= rs <= k1:
            y0 = fn1d(x, tabela[k0])
            y1 = fn1d(x, tabela[k1])
            t  = (math.log10(rs) - math.log10(k0)) / (math.log10(k1) - math.log10(k0))
            if fn1d is _semilog_1d:
                return y0 + t * (y1 - y0)
            else:
                return 10 ** (math.log10(y0) + t * (math.log10(y1) - math.log10(y0)))


def ler_fig3(x, rs): return _interp2d(x, rs, FIG3, _semilog_1d)
def ler_fig4(x, rs): return _interp2d(x, rs, FIG4, _loglog_1d)


# ══════════════════════════════════════════════════════════════
#  CONSTANTES E BANCOS DE DADOS
# ══════════════════════════════════════════════════════════════

FREQ_REDE = 60
OMEGA_S   = 2 * math.pi * FREQ_REDE * 2   # 120 Hz
N_RETIF   = 2
KI        = 0.75
KV        = 2.5
KF        = 1.25
RS_PERC   = 0.01

# Reguladores LM78xx: (Vout, modelo, Vin_min, Vin_max, Imax_A)
REGULADORES_78XX = [
    (5,  "LM7805",  8,  35, 1.5),
    (6,  "LM7806",  9,  35, 1.5),
    (8,  "LM7808", 11,  35, 1.5),
    (9,  "LM7809", 12,  35, 1.5),
    (10, "LM7810", 13,  35, 1.5),
    (12, "LM7812", 15,  35, 1.5),
    (15, "LM7815", 18,  35, 1.5),
    (18, "LM7818", 21,  35, 1.5),
    (24, "LM7824", 27,  35, 1.5),
]

# Capacitores (uF, Viso)
CAPS = sorted([
    (470,25),(1000,25),(2200,25),(3300,25),(4700,25),
    (470,50),(1000,50),(1500,50),(2200,50),(3300,50),(4700,50),
    (5600,50),(6800,50),(10000,50),(15000,50),(22000,50),
    (1000,63),(2200,63),(4700,63),(6800,63),(10000,63),
    (1000,100),(2200,100),(4700,100),(6800,100),(10000,100),
])

FUSIVEIS = [0.25,0.5,0.8,1.0,1.25,1.5,2.0,2.5,3.0,4.0,5.0,
            6.0,6.3,8.0,10.0,12.0,15.0,20.0,25.0,30.0]

# Transformadores (Vs, Is, Ss, código)
TRANSFORMADORES = [
    (6,  1.0, 10, "T06-1A"),(9,  1.0, 15, "T09-1A"),(12, 1.0, 20, "T12-1A"),
    (15, 1.0, 20, "T15-1A"),(18, 1.0, 30, "I7A"),   (24, 1.0, 30, "T24-1A"),
    (6,  2.0, 20, "T06-2A"),(9,  2.0, 30, "T09-2A"),(12, 2.0, 30, "T12-2A"),
    (15, 2.0, 40, "T15-2A"),(18, 2.0, 40, "I59"),   (24, 2.0, 50, "T24-2A"),
    (6,  3.0, 30, "T06-3A"),(9,  3.0, 40, "T09-3A"),(12, 3.0, 50, "T12-3A"),
    (15, 3.0, 50, "T15-3A"),(18, 3.0, 54, "I549"),  (24, 3.0, 80, "T24-3A"),
    (12, 5.0, 50, "I9"),    (15, 5.0, 80, "T15-5A"),(18, 5.0, 90, "306574"),
    (24, 5.0,130, "T24-5A"),(12,10.0,150,"T12-10A"),(18,10.0,200,"T18-10A"),
    (24,10.0,300,"T24-10A"),
]

# Resistores E24 (10Ω a 100kΩ)
E24 = []
for dec in [10, 100, 1000, 10000]:
    for v in [1.0,1.1,1.2,1.3,1.5,1.6,1.8,2.0,2.2,2.4,2.7,3.0,
              3.3,3.6,3.9,4.3,4.7,5.1,5.6,6.2,6.8,7.5,8.2,9.1]:
        E24.append(round(v * dec))


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

def resistor_comercial(v):
    for r in E24:
        if r >= v: return r
    return E24[-1]

def capacitor_comercial(c_uf, v_min):
    for c, v in CAPS:
        if c >= c_uf and v >= v_min: return c, v
    return CAPS[-1]

def fusivel_comercial(i):
    for f in FUSIVEIS:
        if f >= i: return f
    return FUSIVEIS[-1]

def transformador_comercial(vs_min, is_min, ss_min):
    cands = [(vs,Is,ss,cod) for vs,Is,ss,cod in TRANSFORMADORES
             if vs >= vs_min and Is >= is_min and ss >= ss_min]
    return min(cands, key=lambda x: x[2]) if cands else None

def regulador_fixo(vout_v, vinmax):
    """
    Busca o LM78xx ideal para vout_v (inteiro) com Vinmax compatível.
    Retorna dict: modelo, Vout_real, Vin_min, Vin_max, exato, alt_317
    """
    # 1. Exato e compatível
    for vr, mod, vmn, vmx, imax in REGULADORES_78XX:
        if vr == vout_v and vmn <= vinmax <= vmx:
            return dict(modelo=mod, Vout_real=vr, Vin_min=vmn, Vin_max=vmx,
                        Imax=imax, exato=True, alt_317=False)
    # 2. Mais próximo compatível
    compat = [(vr,mod,vmn,vmx,imax) for vr,mod,vmn,vmx,imax in REGULADORES_78XX
              if vmn <= vinmax <= vmx]
    if compat:
        vr,mod,vmn,vmx,imax = min(compat, key=lambda x: abs(x[0]-vout_v))
        return dict(modelo=mod, Vout_real=vr, Vin_min=vmn, Vin_max=vmx,
                    Imax=imax, exato=False, alt_317=True)
    # 3. Nenhum compatível
    return dict(modelo=None, Vout_real=vout_v, Vin_min=None,
                Vin_max=None, Imax=None, exato=False, alt_317=True)

def lm317_resistores(vout, R2=10000):
    """Calcula R1 E24 e Vout real para o LM317."""
    R1_calc = (R2 * 1.25) / (vout - 1.25)
    R1_com  = resistor_comercial(R1_calc)
    Vout_r  = 1.25 * (1 + R2 / R1_com)
    return R1_com, R2, Vout_r

def sep(t=""):
    print("\n" + "="*64)
    if t: print(f"  {t}"); print("="*64)

def ln(desc, val, unit=""):
    print(f"  {desc:<47} {val:>9.4g} {unit}")

def ok(c): return "✓ OK" if c else "✗ FALHOU"


# ══════════════════════════════════════════════════════════════
#  ENTRADA DE DADOS
# ══════════════════════════════════════════════════════════════

def entrada_dados():
    sep("ENTRADA DE DADOS")

    print("\n  Tensão de rede:  [1] 110V   [2] 220V")
    Vp   = 220 if input("  Escolha: ").strip() == "2" else 110
    Vond = float(input("\n  Ripple máximo [V] (ex: 3): ") or 3)
    Vd   = float(input("  Queda por diodo [V] (ex: 0.7): ") or 0.7)

    print("\n  Quantas saídas?  [1]  [2]  [3]")
    n = max(1, min(3, int(input("  Número: ").strip() or 1)))

    saidas = []
    for i in range(n):
        print(f"\n  ── Saída {i+1} {'─'*40}")
        print("  Tipo:  [1] Fixa (LM78xx)   [2] Variável (LM317)")
        tipo = input("  Escolha: ").strip()

        if tipo == "2":
            Vout = float(input("  Tensão máx. de saída [V] (mín 1.25, ex: 18): "))
            IL   = float(input("  Corrente de carga [A]: "))
            R2   = float(input("  R2 do LM317 [Ω] (ex: 10000): ") or 10000)
            saidas.append({"tipo": "variavel", "Vout": Vout, "IL": IL, "R2": R2})
        else:
            Vout = float(input("  Tensão de saída [V] (ex: 5, 9, 12, 15, 18...): "))
            IL   = float(input("  Corrente de carga [A]: "))
            saidas.append({"tipo": "fixa", "Vout": Vout, "IL": IL})

    return {"Vp": Vp, "Vond": Vond, "Vd": Vd, "saidas": saidas}


# ══════════════════════════════════════════════════════════════
#  1. TRANSFORMADOR
#     Regra: maior Vout + soma de correntes
# ══════════════════════════════════════════════════════════════

def calc_transformador(d):
    sep("1. DIMENSIONAMENTO DO TRANSFORMADOR")
    Vond     = d["Vond"]; Vd = d["Vd"]
    Vout_max = max(s["Vout"] for s in d["saidas"])
    IL_total = sum(s["IL"]   for s in d["saidas"])

    Vinmin   = Vout_max + 3
    Vinmedia = Vinmin + Vond / 2
    Vsmax    = Vinmedia + 2 * Vd + Vond / 2
    Vsef     = Vsmax / math.sqrt(2)

    print(f"\n  Maior Vout (pior caso): {Vout_max} V")
    print(f"  Soma de correntes:      {IL_total} A\n")
    ln("Vinmin  = Vout_max + 3V",            Vinmin,   "V")
    ln("Vinmédia = Vinmin + Vond/2",         Vinmedia, "V")
    ln("Vsmáx  = Vinmédia + 2·Vd + Vond/2", Vsmax,    "V")
    ln("Vsef   = Vsmáx / √2",               Vsef,     "V")

    d.update({"Vout_max": Vout_max, "IL_total": IL_total,
              "Vsmax": Vsmax, "Vsef": Vsef,
              "Vinmin_tr": Vinmin, "Vinmedia_tr": Vinmedia})
    return d


# ══════════════════════════════════════════════════════════════
#  2. VERIFICAÇÃO NOS REGULADORES
# ══════════════════════════════════════════════════════════════

def calc_verificacao_reguladores(d):
    sep("2. VERIFICAÇÃO NOS REGULADORES")
    Vsmax = d["Vsmax"]; Vond = d["Vond"]; Vd = d["Vd"]

    Vinmedia = (Vsmax - 2 * Vd) - Vond / 2
    Vinmax   = Vinmedia + Vond / 2
    Vinmin   = Vinmedia - Vond / 2

    print()
    ln("Vinmédia = (Vsmáx - 2·Vd) - Vond/2", Vinmedia, "V")
    ln("Vinmáx   = Vinmédia + Vond/2",        Vinmax,   "V")
    ln("Vinmin   = Vinmédia - Vond/2",         Vinmin,   "V")

    tudo_ok = True
    for i, s in enumerate(d["saidas"]):
        Vout = s["Vout"]; tipo = s["tipo"]
        print(f"\n  [Saída {i+1} — {Vout}V — {'LM317' if tipo=='variavel' else 'LM78xx'}]")

        if tipo == "variavel":
            ok1 = 3 <= (Vinmin - Vout) <= 35
            ok2 = 3 <= (Vinmax - Vout) <= 35
            print(f"    3V ≤ Vinmin-Vout = {Vinmin-Vout:.2f}V ≤ 35V  [{ok(ok1)}]")
            print(f"    3V ≤ Vinmax-Vout = {Vinmax-Vout:.2f}V ≤ 35V  [{ok(ok2)}]")
        else:
            reg  = regulador_fixo(int(Vout), Vinmax)
            vmn  = reg["Vin_min"] or 0
            vmx  = reg["Vin_max"] or 99
            ok1  = vmn <= Vinmin <= vmx
            ok2  = vmn <= Vinmax <= vmx
            mod  = reg["modelo"] or "(sem modelo exato — usar LM317)"
            print(f"    Regulador: {mod}  (faixa Vin: {vmn}V – {vmx}V)")
            print(f"    {vmn}V ≤ Vinmin={Vinmin:.2f}V ≤ {vmx}V  [{ok(ok1)}]")
            print(f"    {vmn}V ≤ Vinmax={Vinmax:.2f}V ≤ {vmx}V  [{ok(ok2)}]")

        tudo_ok = tudo_ok and ok1 and ok2

    if not tudo_ok:
        print("\n  ⚠ Revisão necessária: algum regulador fora da faixa.")

    d.update({"Vinmedia": Vinmedia, "Vinmax": Vinmax, "Vinmin": Vinmin})
    return d


# ══════════════════════════════════════════════════════════════
#  3. CAPACITOR
# ══════════════════════════════════════════════════════════════

def calc_capacitor(d):
    sep("3. DIMENSIONAMENTO DO CAPACITOR")
    IL = d["IL_total"]; Vond = d["Vond"]; Vsmax = d["Vsmax"]
    Freq = OMEGA_S / (2 * math.pi)

    C_uF = (IL / (Freq * Vond)) * 1e6
    Vcap = Vsmax * 1.4
    C_com, V_com = capacitor_comercial(C_uF, Vcap)

    print()
    ln("IL total",                  IL,    "A")
    ln("Frequência retificador",    Freq,  "Hz")
    ln("C = IL / (Freq × Vond)",   C_uF,  "µF")
    ln("Vcap = Vsmáx × 1,4",      Vcap,  "V")
    print(f"\n  ► Capacitor: {C_com} µF / {V_com} V")

    d.update({"C_calc_uF": C_uF, "C_com": C_com, "V_cap_com": V_com,
              "Vcap": Vcap, "C1": C_com * 1e-6})
    return d


# ══════════════════════════════════════════════════════════════
#  4. DIODOS
# ══════════════════════════════════════════════════════════════

def calc_diodos(d):
    sep("4. DIMENSIONAMENTO DOS DIODOS")
    IL   = d["IL_total"]; Vsmax = d["Vsmax"]
    Vsef = d["Vsef"]; Vinmedia = d["Vinmedia"]; Vd = d["Vd"]

    Ifav     = IL / 2
    Vrev_d   = math.sqrt(2) * Vsef
    Refetiva = Vinmedia / IL
    Rs       = RS_PERC * Refetiva
    x_param  = N_RETIF * OMEGA_S * Refetiva * d["C1"]
    Rs_nRL   = (1 / N_RETIF) * (Rs / Refetiva) * 100

    curva3 = ler_fig3(x_param, Rs_nRL)
    curva4 = ler_fig4(x_param, Rs_nRL)
    IFrms  = curva3 * Ifav
    IFrm   = curva4 * Ifav

    Ifav_min  = IL / KI
    IFrms_min = IFrms / KI
    VRRM      = KV * Vsmax

    print()
    ln("Imed_ret = IL_total",           IL,       "A")
    ln("Ifav = Imed_ret / 2",          Ifav,     "A")
    ln("Vrev_d = √2 × Vsef",          Vrev_d,   "V")
    print()
    ln("Refetiva = Vinmédia / IL",     Refetiva, "Ω")
    ln("Rs = 1% × Refetiva",          Rs,       "Ω")
    ln("n·ωs·RL·C  (eixo X curvas)",  x_param,  "")
    ln("Rs/(n·RL) %",                 Rs_nRL,   "%")
    print(f"  {'Fig3 → IFrms/Ifav':<47} {curva3:>9.3f}")
    ln("IFrms = curva3 × Ifav",       IFrms,    "A")
    print(f"  {'Fig4 → IFrm/Ifav (pico)':<47} {curva4:>9.3f}")
    ln("IFrm  = curva4 × Ifav",       IFrm,     "A")
    print()
    print("  [Mínimos para seleção — com fatores de segurança]")
    ln("Ifav  ≥ IL / Ki",             Ifav_min,  "A")
    ln("IFrms ≥ IFrms / Ki",          IFrms_min, "A")
    ln("VRRM  = Kv × Vsmáx",         VRRM,      "V")

    # Corrente de surto
    Vdmax = 1.2; Id_ref = 3.0
    RD   = (Vdmax - Vd) / Id_ref
    IFsm = Vsmax / (Rs + 2 * RD)
    tau  = 18 * d["C1"] * 1e3   # Rth_SK3 × C1

    print()
    sep("4b. CORRENTE DE SURTO")
    ln("RD = (Vdmáx - Vd) / Id",     RD,   "Ω")
    ln("IFsm = Vsmáx / (Rs + 2·Rd)", IFsm, "A")
    ln("Γ = Rth × C1",               tau,  "ms")

    d.update({"Ifav": Ifav, "IFrms": IFrms, "IFrm": IFrm,
              "Ifav_min": Ifav_min, "IFrms_min": IFrms_min,
              "VRRM": VRRM, "Refetiva": Refetiva, "Rs": Rs,
              "x_param": x_param, "IFsm": IFsm})
    return d


# ══════════════════════════════════════════════════════════════
#  5. FUSÍVEIS
# ══════════════════════════════════════════════════════════════

def calc_fusiveis(d):
    sep("5. DIMENSIONAMENTO DOS FUSÍVEIS")
    Is    = math.sqrt(2) * d["IFrms"]
    KT    = d["Vp"] / d["Vsef"]
    Ip    = Is / KT
    Fus_s = fusivel_comercial(KF * Is)
    Fus_p = fusivel_comercial(KF * Ip)

    print()
    ln("Is = √2 × IFrms",       Is,     "A")
    ln("KT = Vp / Vsef",        KT,     "")
    ln("Ip = Is / KT",          Ip,     "A")
    ln("Fusível sec ≥ Kf×Is",   KF*Is,  "A")
    ln("Fusível pri ≥ Kf×Ip",   KF*Ip,  "A")
    print(f"\n  ► Fusível secundário: {Fus_s} A")
    print(f"  ► Fusível primário:   {Fus_p} A")

    d.update({"Is": Is, "KT": KT, "Ip": Ip, "Fus_s": Fus_s, "Fus_p": Fus_p})
    return d


# ══════════════════════════════════════════════════════════════
#  6. TRANSFORMADOR COMERCIAL
# ══════════════════════════════════════════════════════════════

def calc_transformador_comercial(d):
    sep("6. TRANSFORMADOR COMERCIAL")
    Ss = d["Vsef"] * d["Is"]

    print()
    ln("Ss = Vsef × Is", Ss, "VA")

    tr = transformador_comercial(d["Vsef"], d["Is"], Ss)
    if tr:
        vs, is_tr, ss_tr, cod = tr
        print(f"\n  ► {cod}  —  {d['Vp']}V / {vs}V  /  {is_tr}A  /  {ss_tr}VA")
    else:
        print("\n  ✗ Sem modelo no banco — dimensionar sob encomenda.")
        vs, is_tr, ss_tr, cod = round(d["Vsef"],1), round(d["Is"],1), round(Ss), "Sob encomenda"

    d.update({"Ss": Ss, "TR_cod": cod, "TR_Vs": vs, "TR_Is": is_tr, "TR_Ss": ss_tr})
    return d


# ══════════════════════════════════════════════════════════════
#  7. REGULADORES (por saída)
# ══════════════════════════════════════════════════════════════

def calc_reguladores(d):
    sep("7. DIMENSIONAMENTO DOS REGULADORES")
    Vinmax = d["Vinmax"]
    res_saidas = []

    for i, s in enumerate(d["saidas"]):
        Vout = s["Vout"]; IL = s["IL"]; tipo = s["tipo"]
        print()

        if tipo == "variavel":
            R1, R2, Vout_r = lm317_resistores(Vout, s["R2"])
            Pd   = (Vinmax - Vout) * IL
            Vreg = Vinmax - Vout

            print(f"  [Saída {i+1} — LM317 variável — até {Vout}V / {IL}A]")
            ln("R2 (potenciômetro)",               s["R2"], "Ω")
            ln("R1 calculado",  (s["R2"]*1.25)/(Vout-1.25),"Ω")
            ln("R1 comercial E24",                 R1,      "Ω")
            ln("Vout real com R1 comercial",        Vout_r,  "V")
            ln("Vreg = Vinmax - Vout",             Vreg,    "V")
            ln("Pd = Vreg × IL",                  Pd,      "W")
            if Pd > 1.0: print("    ⚠ Necessário dissipador!")

            res_saidas.append({"tipo":"variavel","modelo":"LM317",
                               "R1":R1,"R2":R2,"Pd":Pd,"Vout_real":Vout_r})

        else:
            reg  = regulador_fixo(int(Vout), Vinmax)
            Vreg = Vinmax - Vout
            Pd   = Vreg * IL

            print(f"  [Saída {i+1} — Fixa {Vout}V / {IL}A]")

            if reg["exato"]:
                print(f"    ✓ Regulador: {reg['modelo']}  (tensão exata)")
            elif reg["modelo"]:
                print(f"    ⚠ Sem LM78xx exato para {Vout}V.")
                print(f"    Mais próximo: {reg['modelo']} ({reg['Vout_real']}V)")
                R1_alt, R2_alt, Vo_alt = lm317_resistores(Vout)
                print(f"    Alternativa LM317: R1={R1_alt}Ω / R2={R2_alt}Ω → Vout≈{Vo_alt:.2f}V")
            else:
                print(f"    ✗ Nenhum LM78xx compatível com Vinmax={Vinmax:.1f}V.")
                R1_alt, R2_alt, Vo_alt = lm317_resistores(Vout)
                print(f"    Use LM317: R1={R1_alt}Ω / R2={R2_alt}Ω → Vout≈{Vo_alt:.2f}V")

            ln("Vreg = Vinmax - Vout", Vreg, "V")
            ln("Pd = Vreg × IL",      Pd,   "W")
            if Pd > 1.0: print("    ⚠ Necessário dissipador!")

            res_saidas.append({"tipo":"fixa","modelo":reg["modelo"] or "LM317",
                               "Pd":Pd,"Vout_real":reg["Vout_real"],
                               "exato":reg["exato"],"alt_317":reg["alt_317"]})

    d["res_saidas"] = res_saidas
    return d


# ══════════════════════════════════════════════════════════════
#  RESUMO
# ══════════════════════════════════════════════════════════════

def resumo_final(d):
    sep("RESUMO — LISTA DE COMPONENTES")

    linhas_saidas = []
    for i, (s, r) in enumerate(zip(d["saidas"], d["res_saidas"])):
        if s["tipo"] == "variavel":
            desc = f"LM317  R1={r['R1']}Ω / R2={r['R2']:.0f}Ω → {r['Vout_real']:.2f}V"
        else:
            if r["exato"]:
                desc = r["modelo"]
            else:
                desc = f"{r['modelo']} (≈{r['Vout_real']}V) ou LM317"
        diss = "  ⚠ dissipador" if r["Pd"] > 1 else ""
        linhas_saidas.append(
            f"  │  Saída {i+1}: {s['Vout']}V / {s['IL']}A  →  {desc}  |  Pd={r['Pd']:.2f}W{diss}"
        )

    print(f"""
  ┌─ TRANSFORMADOR ────────────────────────────────────────────
  │  {d['TR_cod']}  —  {d['Vp']}V / {d['TR_Vs']}V  /  {d['TR_Is']}A  /  {d['TR_Ss']}VA
  │
  ├─ DIODOS (ponte de Graetz) ─────────────────────────────────
  │  Ifav  ≥ {d['Ifav_min']:.3f} A   |  IFrms ≥ {d['IFrms_min']:.3f} A
  │  VRRM  ≥ {d['VRRM']:.1f} V     |  IFrm(pico) = {d['IFrm']:.2f} A
  │  Corrente de surto IFsm = {d['IFsm']:.1f} A
  │
  ├─ CAPACITOR ────────────────────────────────────────────────
  │  {d['C_com']} µF / {d['V_cap_com']} V   (calculado: {d['C_calc_uF']:.1f} µF / mín. {d['Vcap']:.1f} V)
  │
  ├─ FUSÍVEIS ─────────────────────────────────────────────────
  │  Secundário: {d['Fus_s']} A   |   Primário: {d['Fus_p']} A
  │
  ├─ REGULADORES ──────────────────────────────────────────────""")

    for l in linhas_saidas:
        print(l)
    print("  └" + "─"*60)
    print()


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════

def main():
    print("\n" + "="*64)
    print("  DIMENSIONADOR DE FONTE LINEAR — MÚLTIPLAS SAÍDAS")
    print("  Fórmulas: Memorial de Cálculo Volpiano")
    print("="*64)

    d = entrada_dados()
    d = calc_transformador(d)
    d = calc_verificacao_reguladores(d)
    d = calc_capacitor(d)
    d = calc_diodos(d)
    d = calc_fusiveis(d)
    d = calc_transformador_comercial(d)
    d = calc_reguladores(d)
    resumo_final(d)

    print("  Dimensionamento concluído!\n" + "="*64 + "\n")


if __name__ == "__main__":
    main()