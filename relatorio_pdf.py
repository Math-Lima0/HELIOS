"""
relatorio_pdf.py — Memorial de Cálculo PDF para Fonte Linear DC
"""

import math, io, datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak, Image as RLImage
)
from reportlab.pdfgen import canvas as rl_canvas

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from schade_engine import fig3 as schade_fig3, fig4 as schade_fig4, _CURVES

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm

# ── Cores Pantheon Systems ────────────────────────────────────────────────────
C_AZUL_PANTHEON = colors.HexColor("#0B192C")  # Azul celestial profundo
C_CYAN          = colors.HexColor("#00B4FF")  # Ciano brilhante
C_AMBER         = colors.HexColor("#FF7A00")  # Laranja Solar
C_CINZA_TEXTO   = colors.HexColor("#1E293B")  # Texto principal escuro
C_CINZA_MED     = colors.HexColor("#64748B")  # Texto secundário
C_FUNDO_ALT     = colors.HexColor("#F0F4F8")  # Fundo zebrado suave
C_LINHA         = colors.HexColor("#CBD5E1")  # Linhas de tabela
C_BRANCO        = colors.white

# Aliases para compatibilidade com o resto do código
C_AZUL      = C_CYAN
C_AZUL_ESC  = C_AZUL_PANTHEON
C_CINZA_ESC = C_AZUL_PANTHEON
C_CINZA_CLR = C_LINHA
C_FUNDO     = C_FUNDO_ALT
C_LINHA_TB  = C_LINHA
C_WARN      = C_AMBER

def _E():
    return {
        "titulo": ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=22,
            textColor=C_AZUL_PANTHEON, spaceAfter=2*mm, leading=26),
        "sub": ParagraphStyle("s", fontName="Helvetica", fontSize=10,
            textColor=C_CINZA_MED, spaceAfter=6*mm),
        "corpo": ParagraphStyle("c", fontName="Helvetica", fontSize=9,
            textColor=C_CINZA_TEXTO, leading=14, spaceAfter=2*mm),
        "alerta": ParagraphStyle("a", fontName="Helvetica-Bold", fontSize=9,
            textColor=C_AMBER, leading=12),
        "nota": ParagraphStyle("n", fontName="Helvetica-Oblique", fontSize=8,
            textColor=C_CINZA_MED, leading=11),
    }

# ── Canvas com cabeçalho/rodapé ───────────────────────────────────────────────
class DocCanvas(rl_canvas.Canvas):
    def __init__(self, *a, titulo="Memorial de Cálculo", **kw):
        super().__init__(*a, **kw)
        self._titulo = titulo
        self._saved  = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        n = len(self._saved)
        for i, st in enumerate(self._saved):
            self.__dict__.update(st)
            self._frame(i+1, n)
            super().showPage()
        super().save()

    def _frame(self, pg, total):
        # Cabeçalho monumental — barra azul ponta a ponta
        self.setFillColor(C_AZUL_PANTHEON)
        self.rect(0, PAGE_H-20*mm, PAGE_W, 20*mm, fill=1, stroke=0)
        # Linha solar fina embaixo do cabeçalho
        self.setFillColor(C_AMBER)
        self.rect(0, PAGE_H-21*mm, PAGE_W, 1*mm, fill=1, stroke=0)

        self.setFont("Helvetica-Bold", 14); self.setFillColor(C_BRANCO)
        self.drawString(MARGIN, PAGE_H-12*mm, self._titulo)
        self.setFont("Helvetica-Bold", 9); self.setFillColor(C_CYAN)
        self.drawRightString(PAGE_W-MARGIN, PAGE_H-12*mm, "H.E.L.I.O.S.  •  Pantheon Systems")

        # Rodapé elegante
        self.setStrokeColor(C_LINHA); self.setLineWidth(0.5)
        self.line(MARGIN, 12*mm, PAGE_W-MARGIN, 12*mm)
        self.setFont("Helvetica", 7.5); self.setFillColor(C_CINZA_MED)
        data = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        self.drawString(MARGIN, 8*mm, f"Gerado em {data}")
        self.drawCentredString(PAGE_W/2, 8*mm, "Memorial de Cálculo Volpiano — Curvas de Schade (scipy)")
        self.setFillColor(C_AZUL_PANTHEON)
        self.drawRightString(PAGE_W-MARGIN, 8*mm, f"Pág. {pg} / {total}")

def _make_canvas(titulo):
    def factory(*a, **kw):
        return DocCanvas(*a, titulo=titulo, **kw)
    return factory

# ── Helpers de tabela ─────────────────────────────────────────────────────────
def _tb_calc(linhas):
    util = PAGE_W - 2*MARGIN
    cw   = [util*.40, util*.30, util*.18, util*.12]
    st   = TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  C_AZUL_PANTHEON),
        ("TEXTCOLOR",     (0,0),(-1,0),  C_CYAN),
        ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,0),  8.5),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_BRANCO, C_FUNDO_ALT]),
        ("GRID",          (0,0),(-1,-1), 0.3, C_LINHA),
        ("FONTNAME",      (0,1),(-1,-1), "Helvetica"),
        ("FONTSIZE",      (0,1),(-1,-1), 8.5),
        ("FONTNAME",      (2,1),(2,-1),  "Helvetica-Bold"),
        ("TEXTCOLOR",     (2,1),(2,-1),  C_AZUL_PANTHEON),
        ("ALIGN",         (2,0),(3,-1),  "RIGHT"),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        ("RIGHTPADDING",  (0,0),(-1,-1), 6),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ])
    return Table(linhas, colWidths=cw, style=st, repeatRows=1)

def _tb_comp(linhas):
    util = PAGE_W - 2*MARGIN
    cw   = [util*.20, util*.35, util*.27, util*.18]
    st   = TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  C_AZUL_PANTHEON),
        ("TEXTCOLOR",     (0,0),(-1,0),  C_CYAN),
        ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,0),  8.5),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_BRANCO, C_FUNDO_ALT]),
        ("GRID",          (0,0),(-1,-1), 0.3, C_LINHA),
        ("FONTNAME",      (0,1),(-1,-1), "Helvetica"),
        ("FONTSIZE",      (0,1),(-1,-1), 8.5),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        ("RIGHTPADDING",  (0,0),(-1,-1), 6),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ])
    return Table(linhas, colWidths=cw, style=st, repeatRows=1)

def _sec(numero, texto):
    util = PAGE_W - 2*MARGIN
    dados = [[f"  {numero}", f"  {texto}"]]
    st = TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_FUNDO_ALT),
        ("BACKGROUND",    (0,0),(0,0),   C_AMBER),
        ("TEXTCOLOR",     (0,0),(0,0),   C_BRANCO),
        ("TEXTCOLOR",     (1,0),(-1,-1), C_AZUL_PANTHEON),
        ("FONTNAME",      (0,0),(-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,-1), 10),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("LINEBELOW",     (0,0),(-1,-1), 1, C_AMBER),
    ])
    return Table(dados, colWidths=[12*mm, util-12*mm], style=st)

# ── Gráfico Schade ────────────────────────────────────────────────────────────
def _graf_schade(r, figura="fig3") -> bytes:
    fn     = schade_fig3 if figura == "fig3" else schade_fig4
    log_y  = (figura == "fig4")
    ylabel = "IFrms / Ifav" if figura == "fig3" else "IFrm / Ifav"
    titulo = "Figura 3 — IFrms/Ifav  vs  n·ωs·RL·C" if figura == "fig3" else "Figura 4 — IFrm/Ifav  vs  n·ωs·RL·C"

    fig, ax = plt.subplots(figsize=(11, 5))
    fig.patch.set_facecolor("#0F172A")
    ax.set_facecolor("#1E293B")
    cmap = plt.cm.get_cmap("cool", len(_CURVES))
    xs   = np.logspace(0, 3, 300)

    for idx, rs in enumerate(_CURVES):
        ys = [fn(x, rs) for x in xs]
        ax.plot(xs, ys, color=cmap(idx), lw=1.1, alpha=0.85)
        ax.annotate(f"{rs}%", xy=(1000, ys[-1]), fontsize=6,
                    color=cmap(idx), va="center", ha="left",
                    xytext=(3,0), textcoords="offset points")

    xp = r.x_param; rsp = r.Rs_nRL_pct; yp = fn(xp, rsp)
    ax.scatter([xp], [yp], color="#F59E0B", s=80, zorder=10,
               edgecolors="white", lw=0.8)
    ax.axvline(xp, color="#F59E0B", lw=0.6, ls="--", alpha=0.55)
    ax.axhline(yp, color="#F59E0B", lw=0.6, ls="--", alpha=0.55)
    ax.annotate(f" ({xp:.1f} ; {yp:.3f})", xy=(xp, yp),
                fontsize=7.5, color="#F59E0B",
                xytext=(10, 8), textcoords="offset points",
                arrowprops=dict(arrowstyle="->", color="#F59E0B", lw=0.7))

    ax.set_xscale("log")
    if log_y: ax.set_yscale("log")
    ax.set_xlabel("n · ωs · RL · C", color="#94A3B8", fontsize=8.5)
    ax.set_ylabel(ylabel,             color="#94A3B8", fontsize=8.5)
    ax.set_title(titulo,              color="#E2E8F0", fontsize=10, pad=7)
    ax.tick_params(colors="#64748B", labelsize=7)
    for sp in ax.spines.values(): sp.set_edgecolor("#334155")
    ax.grid(True, which="both", color="#334155", lw=0.35, alpha=0.55)
    ax.text(0.01, 0.97, "Parâmetro: Rs/(n·RL) em %",
            transform=ax.transAxes, fontsize=6.5, color="#64748B", va="top")

    fig.tight_layout(pad=1.0)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.read()

# ── GERADOR PRINCIPAL ─────────────────────────────────────────────────────────
def gerar_pdf(resultado, caminho: str, titulo_projeto: str = "Memorial de Cálculo") -> str:
    r  = resultado
    E  = _E()
    util = PAGE_W - 2*MARGIN

    doc = SimpleDocTemplate(
        caminho, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=18*mm, bottomMargin=18*mm,
        title=titulo_projeto,
    )
    story = []

    # ── CAPA ──────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 14*mm))
    capa = Table([[Paragraph(titulo_projeto, E["titulo"])]],
                 colWidths=[util])
    capa.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_CINZA_ESC),
        ("LEFTPADDING",   (0,0),(-1,-1), 8*mm),
        ("TOPPADDING",    (0,0),(-1,-1), 7*mm),
        ("BOTTOMPADDING", (0,0),(-1,-1), 7*mm),
        ("LINEAFTER",     (0,0),(0,0),   3*mm, C_AZUL),
    ]))
    story.append(capa)
    story.append(Spacer(1, 4*mm))
    data = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    story.append(Paragraph(
        f"Fonte Linear DC — {len(r.saidas)} saída(s) — "
        f"Rede {r.Vp}V / 60Hz — {data}", E["sub"]))
    story.append(HRFlowable(width=util, thickness=0.5, color=C_CINZA_CLR, spaceAfter=5*mm))

    # Tabela de saídas
    rows = [["Saída", "Tipo", "Tensão", "Corrente"]]
    for i, s in enumerate(r.saidas):
        rows.append([f"Saída {i+1}",
                     "Variável (LM317)" if s.tipo=="variavel" else "Fixa (LM78xx)",
                     f"{s.Vout} V", f"{s.IL} A"])
    story.append(_tb_comp(rows))
    story.append(Spacer(1, 4*mm))

    if r.alertas:
        story.append(Paragraph("Alertas do projeto:", E["alerta"]))
        for a in r.alertas:
            story.append(Paragraph(f"  ⚠  {a}", E["alerta"]))
    story.append(PageBreak())

    # ── 1. TRANSFORMADOR ──────────────────────────────────────────────────────
    story.append(_sec("1", "DIMENSIONAMENTO DO TRANSFORMADOR"))
    story.append(Spacer(1,3*mm))
    story.append(Paragraph(
        "Critério: <b>maior tensão de saída</b> como pior caso + <b>soma das correntes</b>.", E["corpo"]))
    story.append(Spacer(1,2*mm))
    story.append(_tb_calc([
        ["Grandeza","Fórmula","Resultado","Unid."],
        ["Maior tensão de saída",   "max(Vout_i)",                f"{r.Vout_max:.2f}",    "V"],
        ["Corrente total de carga", "Σ IL_i",                      f"{r.IL_total:.3f}",   "A"],
        ["Vinmin = Vout_max + 3V",  "Vout_max + 3",               f"{r.Vinmin_tr:.2f}",  "V"],
        ["Vinmédia = Vinmin+Vond/2","Vinmin + Vond/2",             f"{r.Vinmedia_tr:.2f}","V"],
        ["Vsmáx",                   "Vinméd + 2·Vd + Vond/2",     f"{r.Vsmax:.2f}",      "V"],
        ["Vsef = Vsmáx/√2",         "Vsmáx / √2",                 f"{r.Vsef:.2f}",       "V"],
    ]))
    story.append(Spacer(1,5*mm))

    # ── 2. VERIFICAÇÃO ────────────────────────────────────────────────────────
    story.append(_sec("2","VERIFICAÇÃO NOS REGULADORES"))
    story.append(Spacer(1,3*mm))
    story.append(_tb_calc([
        ["Grandeza","Fórmula","Resultado","Unid."],
        ["Vinmédia","(Vsmáx-2·Vd)-Vond/2",f"{r.Vinmedia:.2f}","V"],
        ["Vinmáx",  "Vinméd + Vond/2",     f"{r.Vinmax:.2f}", "V"],
        ["Vinmin",  "Vinméd - Vond/2",      f"{r.Vinmin:.2f}", "V"],
    ]))
    story.append(Spacer(1,2*mm))
    for i, s in enumerate(r.saidas):
        rs_i = r.res_saidas[i]
        ck = "✓ OK" if not rs_i.alerta_corrente else "⚠ Verificar"
        story.append(Paragraph(
            f"  Saída {i+1}: <b>{s.Vout}V/{s.IL}A</b> → "
            f"<font color='#0369A1'>{rs_i.modelo}</font>  {ck}", E["corpo"]))
    story.append(Spacer(1,5*mm))

    # ── 3. CAPACITOR ─────────────────────────────────────────────────────────
    story.append(_sec("3","DIMENSIONAMENTO DO CAPACITOR"))
    story.append(Spacer(1,3*mm))
    story.append(_tb_calc([
        ["Grandeza","Fórmula","Resultado","Unid."],
        ["Frequência retificador",   "2 × frede",             "120",                "Hz"],
        ["Capacitância calculada",   "IL / (freq × Vond)",    f"{r.C_calc_uF:.1f}", "µF"],
        ["Tensão mín. isolação",     "Vsmáx × 1,4",           f"{r.Vcap_min:.2f}",  "V"],
        ["Capacitor comercial",      "—",                     f"{r.C_com}",          "µF"],
        ["Tensão do capacitor",      "—",                     f"{r.V_cap_com}",      "V"],
    ]))
    story.append(Spacer(1,5*mm))

    # ── 4. DIODOS ─────────────────────────────────────────────────────────────
    story.append(_sec("4","DIMENSIONAMENTO DOS DIODOS — CURVAS DE SCHADE"))
    story.append(Spacer(1,3*mm))
    story.append(Paragraph(
        "IFrms e IFrm obtidos por interpolação 2D (CubicSpline + RegularGridInterpolator, scipy). "
        "Precisão: Fig. 3 ±1% / Fig. 4 ±5–10%.", E["corpo"]))
    story.append(Spacer(1,2*mm))
    story.append(_tb_calc([
        ["Grandeza","Fórmula","Resultado","Unid."],
        ["Ifav = IL/2",              "IL_total / 2",             f"{r.Ifav:.4f}",      "A"],
        ["Vrev = √2 × Vsef",         "√2 × Vsef",               f"{r.Vrev_d:.3f}",    "V"],
        ["Refetiva = Vinméd/IL",     "Vinmédia / IL_total",      f"{r.Refetiva:.4f}",  "Ω"],
        ["Rs = 1% × Refetiva",       "0,01 × Refetiva",          f"{r.Rs:.5f}",        "Ω"],
        ["x = n·ωs·RL·C",           "2·ωs·Refetiva·C",          f"{r.x_param:.3f}",   "—"],
        ["Rs/(n·RL) %",              "(Rs/Refetiva)/2 × 100",    f"{r.Rs_nRL_pct:.4f}","%"],
        ["Fig. 3 → IFrms/Ifav",      "Schade_Fig3(x, Rs/nRL)",  f"{r.curva_fig3:.5f}","—"],
        ["IFrms = curva3 × Ifav",    "—",                        f"{r.IFrms:.4f}",     "A"],
        ["Fig. 4 → IFrm/Ifav",       "Schade_Fig4(x, Rs/nRL)",  f"{r.curva_fig4:.5f}","—"],
        ["IFrm = curva4 × Ifav",     "—",                        f"{r.IFrm:.4f}",      "A"],
        ["Ifav mín. (Ki=0,75)",      "IL / Ki",                  f"{r.Ifav_min:.4f}",  "A"],
        ["IFrms mín. (Ki=0,75)",     "IFrms / Ki",               f"{r.IFrms_min:.4f}", "A"],
        ["VRRM (Kv=2,5)",            "Kv × Vsmáx",              f"{r.VRRM:.3f}",      "V"],
        ["IFsm",                     "Vsmáx/(Rs+2·RD)",          f"{r.IFsm:.3f}",      "A"],
        ["Γ = Rth × C1",             "18 × C1",                  f"{r.tau_ms:.3f}",    "ms"],
    ]))
    story.append(Spacer(1,3*mm))
    if r.diodo:
        d = r.diodo
        story.append(Paragraph(
            f"<b>Diodo selecionado:</b>  <font color='#0EA5E9'>{d['modelo']}</font>  —  "
            f"Ifav={d['Ifav']}A  |  IFrms={d['IFrms']}A  |  VRRM={d['VRRM']}V  |  "
            f"IFsm={d['IFsm']}A  —  {d['descricao']}", E["corpo"]))
    else:
        story.append(Paragraph("⚠  Diodo fora do banco — dimensionar ponte sob medida.", E["alerta"]))
    story.append(Spacer(1,4*mm))

    # Gráficos
    for fig_id, leg in [("fig3","Figura 3 — IFrms/Ifav"), ("fig4","Figura 4 — IFrm/Ifav")]:
        story.append(Paragraph(f"<b>{leg}</b>", E["corpo"]))
        story.append(Spacer(1,2*mm))
        png = _graf_schade(r, fig_id)
        story.append(RLImage(io.BytesIO(png), width=util, height=util*0.455))
        story.append(Paragraph(
            "● Ponto amarelo = projeto. Linhas tracejadas = valores lidos nas curvas.", E["nota"]))
        story.append(Spacer(1,4*mm))

    # ── 5. FUSÍVEIS ───────────────────────────────────────────────────────────
    story.append(_sec("5","DIMENSIONAMENTO DOS FUSÍVEIS"))
    story.append(Spacer(1,3*mm))
    story.append(_tb_calc([
        ["Grandeza","Fórmula","Resultado","Unid."],
        ["Is = √2 × IFrms",      "√2 × IFrms",    f"{r.Is:.4f}",  "A"],
        ["KT = Vp / Vsef",       "Vp / Vsef",      f"{r.KT:.4f}",  "—"],
        ["Ip = Is / KT",         "Is / KT",         f"{r.Ip:.4f}",  "A"],
        ["Fus. sec. mín.",        "1,25 × Is",       f"{1.25*r.Is:.3f}","A"],
        ["Fus. sec. comercial",   "—",               f"{r.Fus_s}",   "A"],
        ["Fus. pri. mín.",        "1,25 × Ip",       f"{1.25*r.Ip:.3f}","A"],
        ["Fus. pri. comercial",   "—",               f"{r.Fus_p}",   "A"],
    ]))
    story.append(Spacer(1,5*mm))

    # ── 6. TRANSFORMADOR COMERCIAL ────────────────────────────────────────────
    story.append(_sec("6","TRANSFORMADOR COMERCIAL"))
    story.append(Spacer(1,3*mm))
    story.append(_tb_calc([
        ["Grandeza","Fórmula","Resultado","Unid."],
        ["Ss = Vsef × Is",    "Vsef × Is",  f"{r.Ss:.2f}",  "VA"],
        ["Tensão sec. mín.",  "—",           f"{r.Vsef:.2f}","V"],
        ["Corrente sec. mín.","—",           f"{r.Is:.3f}",  "A"],
        ["Código comercial",  "—",           r.TR_cod,       "—"],
        ["Tensão sec.",       "—",           f"{r.TR_Vs}",   "V"],
        ["Corrente sec.",     "—",           f"{r.TR_Is}",   "A"],
        ["Potência aparente", "—",           f"{r.TR_Ss}",   "VA"],
    ]))
    if not r.TR_encontrado:
        story.append(Paragraph(
            f"⚠  Transformador não encontrado no banco — "
            f"solicitar {r.TR_Vs}V/{r.TR_Is}A/{r.TR_Ss}VA sob encomenda.", E["alerta"]))
    story.append(Spacer(1,5*mm))

    # ── 7. REGULADORES ────────────────────────────────────────────────────────
    story.append(_sec("7","DIMENSIONAMENTO DOS REGULADORES"))
    story.append(Spacer(1,3*mm))

    for rs_i in r.res_saidas:
        s = r.saidas[rs_i.indice-1]
        bloco = []
        bloco.append(Paragraph(
            f"<b>Saída {rs_i.indice} — "
            f"{'Variável' if rs_i.tipo=='variavel' else 'Fixa'} — "
            f"{rs_i.Vout_desejado}V / {rs_i.IL}A</b>", E["corpo"]))
        if rs_i.tipo == "variavel":
            linhas = [
                ["Grandeza","Fórmula","Resultado","Unid."],
                ["Regulador",           "—",                    rs_i.modelo,             "—"],
                ["R2 (potenciômetro)",  "—",                    f"{rs_i.R2:.0f}",         "Ω"],
                ["R1 calculado",        "R2·1,25/(Vout-1,25)",  f"{rs_i.R1_calc:.2f}",   "Ω"],
                ["R1 comercial E24",    "—",                    f"{rs_i.R1_com}",         "Ω"],
                ["Vout real",           "1,25·(1+R2/R1)",       f"{rs_i.Vout_real:.4f}", "V"],
                ["Vreg = Vinmax-Vout",  "Vinmax - Vout",        f"{rs_i.Vreg:.3f}",      "V"],
                ["Pd = Vreg × IL",      "Vreg × IL",            f"{rs_i.Pd:.4f}",        "W"],
            ]
        else:
            linhas = [
                ["Grandeza","Fórmula","Resultado","Unid."],
                ["Regulador",        "—",             rs_i.modelo,           "—"],
                ["Tensão exata",     "—",             "Sim" if rs_i.exato else "Não","—"],
                ["Vreg=Vinmax-Vout", "Vinmax-Vout",   f"{rs_i.Vreg:.3f}",   "V"],
                ["Pd = Vreg × IL",   "Vreg × IL",     f"{rs_i.Pd:.4f}",     "W"],
            ]
            if rs_i.Vin_min:
                linhas.append(["Faixa Vin",
                    f"{rs_i.Vin_min}V – {rs_i.Vin_max}V",
                    f"{r.Vinmin:.1f} – {r.Vinmax:.1f}", "V"])
        bloco.append(_tb_calc(linhas))
        if rs_i.alerta_dissipador:
            bloco.append(Paragraph(f"⚠  Pd={rs_i.Pd:.2f}W — necessário dissipador.", E["alerta"]))
        if rs_i.sugestao_alt:
            bloco.append(Paragraph(f"  Alternativa: {rs_i.sugestao_alt}", E["nota"]))
        bloco.append(Spacer(1,4*mm))
        story.append(KeepTogether(bloco))

    # ── RESUMO ────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(_sec("✓","LISTA DE COMPONENTES — RESUMO"))
    story.append(Spacer(1,4*mm))

    comp = [["Componente","Especificação","Valor Comercial","Obs."]]
    comp.append(["Transformador",
        f"Vp={r.Vp}V / Vs≥{r.Vsef:.1f}V / Is≥{r.Is:.2f}A",
        f"{r.TR_cod}  {r.TR_Vs}V/{r.TR_Is}A/{r.TR_Ss}VA",
        "" if r.TR_encontrado else "Sob encomenda"])
    d_str = "—"
    if r.diodo:
        d = r.diodo
        d_str = f"{d['modelo']}  {d['Ifav']}A/{d['VRRM']}V"
    comp.append(["Diodos ×4",
        f"Ifav≥{r.Ifav_min:.2f}A  VRRM≥{r.VRRM:.0f}V",
        d_str, f"IFsm={r.IFsm:.1f}A"])
    comp.append(["Capacitor",
        f"≥{r.C_calc_uF:.0f}µF / ≥{r.Vcap_min:.1f}V",
        f"{r.C_com}µF/{r.V_cap_com}V","Eletrolítico"])
    comp.append(["Fusível Sec.", f"≥{1.25*r.Is:.2f}A", f"{r.Fus_s}A","Rápido"])
    comp.append(["Fusível Pri.", f"≥{1.25*r.Ip:.2f}A", f"{r.Fus_p}A","Rápido"])
    for rs_i in r.res_saidas:
        s = r.saidas[rs_i.indice-1]
        if rs_i.tipo == "variavel":
            spec  = f"{s.Vout}V / {s.IL}A"
            valor = f"{rs_i.modelo}  R1={rs_i.R1_com}Ω R2={rs_i.R2:.0f}Ω"
            obs   = f"Vout={rs_i.Vout_real:.2f}V"
        else:
            spec  = f"{s.Vout}V / {s.IL}A"
            valor = rs_i.modelo
            obs   = ("" if rs_i.exato else "Aprox.")
        if rs_i.alerta_dissipador: obs += " ⚠Diss."
        comp.append([f"Reg. Saída {rs_i.indice}", spec, valor, obs])

    story.append(_tb_comp(comp))
    story.append(Spacer(1,5*mm))
    story.append(HRFlowable(width=util, thickness=0.4, color=C_CINZA_CLR))
    story.append(Spacer(1,3*mm))
    story.append(Paragraph(
        "Memorial de Cálculo gerado automaticamente pelo Dimensionador de Fonte Linear. "
        "Fórmulas: Memorial de Cálculo Volpiano. "
        "Interpolação das Curvas de Schade: CubicSpline + RegularGridInterpolator (scipy).",
        E["nota"]))

    doc.multiBuild(story, canvasmaker=_make_canvas(titulo_projeto))
    return caminho


if __name__ == "__main__":
    import sys; sys.path.insert(0,"/home/claude/fonte_linear")
    from motor_volpiano import dimensionar, Saida
    saidas = [Saida("variavel",18.0,0.75,R2=10000), Saida("fixa",12.0,0.50), Saida("fixa",5.0,0.60)]
    r = dimensionar(saidas, Vp=110, Vond=3.0, Vd=0.7)
    out = "/mnt/user-data/outputs/memorial_calculo.pdf"
    gerar_pdf(r, out, "Memorial de Cálculo — Fonte Linear 18V/12V/5V")
    print(f"PDF gerado: {out}")