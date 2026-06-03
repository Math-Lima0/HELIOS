"""
interface.py — H.E.L.I.O.S.
High-accuracy Electronics & Linear Input-Output Simulator
Pantheon Systems

Interface do Santuário Digital:
  · Fundo espacial cósmico #0A0E17
  · Azul técnico #2F9EEF + Âmbar #FFB846
  · Glassmorphism nos cards de saída
  · Alertas por aura âmbar (sem vermelho agressivo)
  · Astrolábio de Engenharia (Curvas de Schade)
  · Tema dark/light alternável
  · Salvamento automático + explícito (.helios)
  · Dashboard de projetos recentes
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import threading, os, sys, math, json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from motor_volpiano import dimensionar, Saida, Resultado
from relatorio_pdf  import gerar_pdf
from sistemas_arquivos import salvar_projeto_helios, carregar_projeto_helios

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
try:
    import matplotlib.patheffects as pe
    _PE = True
except Exception:
    _PE = False
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from schade_engine import fig3 as schade_fig3, fig4 as schade_fig4, _CURVES


# ─────────────────────────────────────────────────────────────────────────────
#  IDENTIDADE VISUAL H.E.L.I.O.S. (Tema Único: Slate Dark)
# ─────────────────────────────────────────────────────────────────────────────

CORES = {
    "dark": {
        "cosmos":     "#180F2D",  # Fundo: roxo noturno profundo
        "void":       "#251543",  # Topbar/sidebar: roxo denso
        "card":       "#3A215D",  # Cards: roxo médio
        "card2":      "#52307D",  # Destaques internos
        "glass":      "#2E1B4D",  # Fundo das saídas
        "glass_bord": "#FF8CC8",  # Bordas: rosa claro vibrante
        "text":       "#FFF7FA",  # Texto: branco rosado
        "text2":      "#E7C5DD",  # Texto secundário: lilás claro
        "text3":      "#B78EB4",  # Legendas/desativados: lilás médio
        "azul":       "#FF6EB4",  # Acento principal: magenta
        "azul2":      "#FF4E9C",  # Hover do acento
        "ciano":      "#FFC4E1",  # Títulos de seção: rosa pálido
        "amber":      "#FF8A80",  # Alertas/energia: coral
        "amber2":     "#FF6F61",  # Hover do coral
        "amber_dim":  "#5B2433",  # Glow de alerta escuro
        "ok":         "#7FFFC5",  # Sucesso: menta
        "ok_dim":     "#14543D",
        "graf_bg":    "#180F2D",  # Fundo externo do gráfico
        "graf_ax":    "#3A215D",  # Área interna do gráfico
        "graf_grid":  "#5C4278",  # Grade: roxo suave
    }
}

RECENTES_PATH = Path.home() / ".helios_recentes.json"
MAX_RECENTES  = 6


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS DE RECENTES
# ─────────────────────────────────────────────────────────────────────────────

def _carregar_recentes():
    try:
        if RECENTES_PATH.exists():
            return json.loads(RECENTES_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []

def _salvar_recentes(lista):
    try:
        RECENTES_PATH.write_text(
            json.dumps(lista, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass

def _registrar_recente(caminho, nome):
    rec = _carregar_recentes()
    rec = [r for r in rec if r.get("caminho") != caminho]
    rec.insert(0, {
        "caminho": caminho,
        "nome": nome,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
    })
    _salvar_recentes(rec[:MAX_RECENTES])


# ─────────────────────────────────────────────────────────────────────────────
#  CARD DE SAÍDA — Glassmorphism com aura de alerta
# ─────────────────────────────────────────────────────────────────────────────

class PainelSaida(ctk.CTkFrame):
    def __init__(self, master, numero, on_remove, tema, **kw):
        super().__init__(master, **kw)
        self._n      = numero
        self._remove = on_remove
        self._tema   = tema
        self._build()

    def _build(self):
        p = CORES[self._tema]
        self.configure(
            fg_color=p["glass"],
            corner_radius=10,
            border_width=1,
            border_color=p["glass_bord"],
        )

        # Header
        hdr = ctk.CTkFrame(self, fg_color=p["card2"], corner_radius=8)
        hdr.pack(fill="x", padx=8, pady=(8, 0))

        ctk.CTkLabel(
            hdr, text=f" S{self._n} ",
            font=("Segoe UI", 9, "bold"),
            fg_color=p["azul"], text_color="#FFF",
            corner_radius=4, width=28, height=20,
        ).pack(side="left", padx=(8, 6), pady=6)

        self._tipo = ctk.StringVar(value="Fixa (LM78xx)")
        ctk.CTkSegmentedButton(
            hdr,
            values=["Fixa (LM78xx)", "Variável (LM317)"],
            variable=self._tipo,
            command=self._on_tipo,
            selected_color=p["azul"],
            selected_hover_color=p["azul2"],
            unselected_color=p["glass"],
            text_color=p["text"],
            font=("Segoe UI", 9),
            height=26,
        ).pack(side="left", pady=6)

        if self._n > 1:
            ctk.CTkButton(
                hdr, text="✕", width=26, height=26,
                fg_color="transparent",
                hover_color=p["amber_dim"],
                text_color=p["text3"],
                font=("Segoe UI", 11),
                command=lambda: self._remove(self),
            ).pack(side="right", padx=6)

        # Campos
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="x", padx=12, pady=(8, 10))
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=1)
        f.columnconfigure(2, weight=1)

        for col, lbl in enumerate(["Tensão (V)", "Corrente (A)", "R2 Ω  [variável]"]):
            ctk.CTkLabel(
                f, text=lbl, font=("Segoe UI", 8),
                text_color=p["text2"],
            ).grid(row=0, column=col, sticky="w", padx=(0, 6), pady=(0, 2))

        def _e(col, ph, val=""):
            e = ctk.CTkEntry(
                f, placeholder_text=ph,
                fg_color=p["card"], border_color=p["text3"],
                text_color=p["text"],
                placeholder_text_color=p["text3"],
                font=("Consolas", 10), height=32, corner_radius=6,
            )
            e.grid(row=1, column=col, sticky="ew", padx=(0, 6 if col < 2 else 0))
            if val:
                e.insert(0, val)
            return e

        self._vout = _e(0, "ex: 12")
        self._il   = _e(1, "ex: 0.5")
        self._r2   = _e(2, "10000", "10000")
        self._on_tipo("Fixa (LM78xx)")

    def _on_tipo(self, val):
        p = CORES[self._tema]
        if "Variável" in val:
            self._r2.configure(
                state="normal", text_color=p["text"], border_color=p["amber"]
            )
        else:
            self._r2.configure(
                state="disabled", text_color=p["text3"], border_color=p["text3"]
            )

    def set_alerta(self, ativo: bool):
        """Aura âmbar quando há alerta de dissipador ou corrente."""
        p = CORES[self._tema]
        self.configure(
            border_color=p["amber"] if ativo else p["glass_bord"],
            border_width=2 if ativo else 1,
        )

    def get_saida(self) -> Saida:
        tipo = "variavel" if "Variável" in self._tipo.get() else "fixa"
        return Saida(
            tipo=tipo,
            Vout=float(self._vout.get() or 0),
            IL=float(self._il.get() or 0),
            R2=float(self._r2.get() or 10000),
        )

    def validar(self):
        erros = []
        try:
            v = float(self._vout.get())
            if v <= 0:
                raise ValueError
        except Exception:
            erros.append(f"Saída {self._n}: tensão inválida")
        try:
            i = float(self._il.get())
            if i <= 0:
                raise ValueError
        except Exception:
            erros.append(f"Saída {self._n}: corrente inválida")
        return erros


# ─────────────────────────────────────────────────────────────────────────────
#  DASHBOARD — Tela inicial de projetos
# ─────────────────────────────────────────────────────────────────────────────

class TelaDashboard(ctk.CTkToplevel):
    def __init__(self, master, on_novo, on_abrir, tema):
        super().__init__(master)
        self._on_novo  = on_novo
        self._on_abrir = on_abrir
        self._tema     = tema
        self.title("H.E.L.I.O.S. — Pantheon Systems")
        self.state("zoomed")
        self._build()
        self.lift()
        self.focus_force()

    def _build(self):
        p = CORES[self._tema]
        self.configure(fg_color=p["cosmos"])

        # Cabeçalho monumental
        hdr = ctk.CTkFrame(self, fg_color=p["void"], corner_radius=0, height=120)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkLabel(
            hdr,
            text="H . E . L . I . O . S .",
            font=("Segoe UI", 30, "bold"),
            text_color=p["azul"],
        ).pack(pady=(22, 4))

        ctk.CTkLabel(
            hdr,
            text="High-accuracy Electronics & Linear Input-Output Simulator",
            font=("Segoe UI", 9),
            text_color=p["text2"],
        ).pack()

        ctk.CTkLabel(
            hdr,
            text="Pantheon Systems",
            font=("Segoe UI", 9, "bold"), # Deixei a fonte um pouquinho mais forte para dar destaque
            text_color=p["text3"],
        ).pack(pady=(4, 0)) # Um pequeno padding no topo para desgrudar do texto acima

        # Botões
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=32, pady=20)
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        ctk.CTkButton(
            row, text="＋  Novo Projeto",
            height=46, fg_color=p["azul"], hover_color=p["azul2"],
            text_color="#FFF", font=("Segoe UI", 12, "bold"),
            corner_radius=8, command=self._novo,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            row, text="📂  Abrir .helios",
            height=46, fg_color=p["card2"], hover_color=p["glass"],
            text_color=p["azul"], border_color=p["azul"], border_width=1,
            font=("Segoe UI", 12, "bold"),
            corner_radius=8, command=self._abrir,
        ).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        # Recentes
        ctk.CTkLabel(
            self, text="PROJETOS RECENTES",
            font=("Segoe UI", 8, "bold"),
            text_color=p["text3"],
        ).pack(anchor="w", padx=32, pady=(0, 6))

        scroll = ctk.CTkScrollableFrame(
            self, fg_color=p["void"], corner_radius=12,
        )
        scroll.pack(fill="both", expand=True, padx=32, pady=(0, 24))

        recentes = _carregar_recentes()
        if not recentes:
            ctk.CTkLabel(
                scroll,
                text="Nenhum projeto recente.\nCrie ou abra um projeto para começar.",
                font=("Segoe UI", 11), text_color=p["text3"], justify="center",
            ).pack(expand=True, pady=40)
        else:
            for r in recentes:
                self._card_recente(scroll, r, p)

    def _card_recente(self, parent, dados, p):
        card = ctk.CTkFrame(
            parent, fg_color=p["card"], corner_radius=8,
            border_width=1, border_color=p["text3"],
        )
        card.pack(fill="x", pady=4)

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=14, pady=10)

        ctk.CTkLabel(
            info, text=dados.get("nome", "Projeto"),
            font=("Segoe UI", 11, "bold"), text_color=p["text"], anchor="w",
        ).pack(anchor="w")

        caminho = dados.get("caminho", "")
        data    = dados.get("data", "")
        ctk.CTkLabel(
            info, text=f"{caminho}  ·  {data}",
            font=("Segoe UI", 8), text_color=p["text3"], anchor="w",
        ).pack(anchor="w")

        ctk.CTkButton(
            card, text="Abrir", width=72, height=30,
            fg_color=p["azul"], hover_color=p["azul2"],
            text_color="#FFF", font=("Segoe UI", 9, "bold"),
            corner_radius=6, command=lambda c=caminho: self._abrir_caminho(c),
        ).pack(side="right", padx=12)

    def _novo(self):
        self.destroy()
        self._on_novo()

    def _abrir(self):
        cam = filedialog.askopenfilename(
            filetypes=[("Projeto H.E.L.I.O.S.", "*.helios")],
            title="Abrir Projeto H.E.L.I.O.S.",
        )
        if cam:
            self.destroy()
            self._on_abrir(cam)

    def _abrir_caminho(self, caminho):
        if not os.path.exists(caminho):
            messagebox.showerror(
                "Arquivo não encontrado",
                f"O arquivo não existe mais:\n{caminho}",
            )
            return
        self.destroy()
        self._on_abrir(caminho)


# ─────────────────────────────────────────────────────────────────────────────
#  APLICAÇÃO PRINCIPAL — O SANTUÁRIO DIGITAL
# ─────────────────────────────────────────────────────────────────────────────

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self._tema       = "dark"
        self._resultado  = None
        self._paineis    = []
        self._nome_proj  = "Novo Projeto"
        self._caminho    = None
        self._modificado = False

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("H.E.L.I.O.S. — Pantheon Systems")
        self.geometry("1400x900")
        self.minsize(1100, 720)
        self.state("zoomed")
        self.protocol("WM_DELETE_WINDOW", self._on_fechar)

        self.withdraw()
        self._build()
        self._modificado = False 
        self.after(250, self._mostrar_dashboard)

    # ─── Tema ─────────────────────────────────────────────────────────────────
    def _rebuild(self):
        for w in self.winfo_children():
            w.destroy()
        self._paineis = []
        self._build()
        if self._resultado:
            self._mostrar(self._resultado)
            self._draw_schade(self._resultado)

    # ─── Layout raiz ──────────────────────────────────────────────────────────

    def _build(self):
        p = CORES[self._tema]
        self.configure(fg_color=p["cosmos"])
        self.columnconfigure(0, weight=1, minsize=390)
        self.columnconfigure(1, weight=5)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self._build_topbar()
        self._build_esq()
        self._build_dir()

    # ─── Topbar ───────────────────────────────────────────────────────────────

    def _build_topbar(self):
        p = CORES[self._tema]
        bar = ctk.CTkFrame(self, fg_color=p["void"], corner_radius=0, height=52)
        bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        bar.grid_propagate(False)

        ctk.CTkLabel(
            bar,
            text="H.E.L.I.O.S.",
            font=("Segoe UI", 17, "bold"),
            text_color=p["azul"],
        ).pack(side="left", padx=20)

        ctk.CTkLabel(
            bar,
            text="Pantheon Systems",
            font=("Segoe UI", 8),
            text_color=p["text3"],
        ).pack(side="left")

        # Botões da direita
        for txt, cmd, destaque in [
            ("📄 PDF",   self._exportar_pdf, False),
            ("💾 Salvar", self._salvar_projeto, False),
            ("📂 Abrir", self._abrir_projeto, False),
            ("＋ Novo",  self._novo_projeto,  True),
        ]:
            ctk.CTkButton(
                bar, text=txt,
                width=94, height=32,
                fg_color=p["azul"] if destaque else p["card2"],
                hover_color=p["azul2"] if destaque else p["glass"],
                text_color="#FFF",
                border_color=p["azul"],
                border_width=0 if destaque else 1,
                font=("Segoe UI", 9, "bold"),
                corner_radius=6,
                command=cmd,
            ).pack(side="right", padx=(0, 8), pady=10)

    # ─── Coluna esquerda ──────────────────────────────────────────────────────

    def _build_esq(self):
        p = CORES[self._tema]
        outer = ctk.CTkFrame(self, fg_color=p["void"], corner_radius=0)
        outer.grid(row=1, column=0, sticky="nsew")
        self._scroll_esq = ctk.CTkScrollableFrame(
            outer, fg_color="transparent",
            scrollbar_button_color=p["text3"],
        )
        self._scroll_esq.pack(fill="both", expand=True)
        self._build_esq_conteudo()

    def _build_esq_conteudo(self):
        p = CORES[self._tema]
        s = self._scroll_esq

        # Nome do projeto
        self._mk_sep(s, "PROJETO")
        self._entry_nome = ctk.CTkEntry(
            s, placeholder_text="Nome do projeto",
            fg_color=p["card"], border_color=p["text3"],
            text_color=p["text"], font=("Segoe UI", 11, "bold"),
            height=36, corner_radius=6,
        )
        self._entry_nome.insert(0, self._nome_proj)
        self._entry_nome.pack(fill="x", padx=20, pady=(0, 4))

        # Parâmetros globais
        self._mk_sep(s, "PARÂMETROS GLOBAIS")
        gbox = ctk.CTkFrame(
            s, fg_color=p["card"], corner_radius=10,
            border_width=1, border_color=p["graf_grid"], # Borda mais sutil com o novo tema
        )
        gbox.pack(fill="x", padx=20, pady=(4, 0))
        
        g = ctk.CTkFrame(gbox, fg_color="transparent")
        g.pack(fill="x", padx=16, pady=16) # Maior respiro interno (padding)
        
        # Ajuste cirúrgico: Coluna 0 (Rede) fica com tamanho fixo, as outras expandem
        g.columnconfigure(0, weight=0) 
        g.columnconfigure(1, weight=1)
        g.columnconfigure(2, weight=1)

        for col, lbl in enumerate(["Rede", "Ripple (V)", "Queda diodo (V)"]):
            ctk.CTkLabel(
                g, text=lbl, font=("Segoe UI", 10), # Fonte um pouco mais legível
                text_color=p["text2"],
            ).grid(row=0, column=col, sticky="w", padx=(0, 16), pady=(0, 6))

        self._vp = ctk.CTkSegmentedButton(
            g, values=["110V", "220V"],
            selected_color=p["azul"], selected_hover_color=p["azul2"],
            unselected_color=p["glass"], text_color=p["text"],
            font=("Segoe UI", 11, "bold"), height=32, width=120 # Largura confortável forçada
        )
        self._vp.set("110V")
        self._vp.grid(row=1, column=0, sticky="w", padx=(0, 16))

        self._vond = ctk.CTkEntry(
            g, placeholder_text="3.0",
            fg_color=p["glass"], border_color=p["graf_grid"],
            text_color=p["text"], font=("Consolas", 11), height=32, corner_radius=6,
        )
        self._vond.insert(0, "3.0")
        self._vond.grid(row=1, column=1, sticky="ew", padx=(0, 16))

        self._vd = ctk.CTkEntry(
            g, placeholder_text="0.7",
            fg_color=p["glass"], border_color=p["graf_grid"],
            text_color=p["text"], font=("Consolas", 11), height=32, corner_radius=6,
        )
        self._vd.insert(0, "0.7")
        self._vd.grid(row=1, column=2, sticky="ew")

        # Saídas
        self._mk_sep(s, "SAÍDAS DA FONTE")

        ctk.CTkButton(
            s, text="＋  Adicionar Saída",
            height=32, fg_color="transparent",
            border_color=p["azul"], border_width=1,
            hover_color=p["card2"], text_color=p["azul"],
            font=("Segoe UI", 9, "bold"), corner_radius=6,
            command=self._add_saida,
        ).pack(fill="x", padx=20, pady=(4, 6))

        self._cont_saidas = ctk.CTkFrame(s, fg_color="transparent")
        self._cont_saidas.pack(fill="x", padx=20)
        self._add_saida()

        # Calcular
        self._mk_sep(s, "")
        self._btn_calc = ctk.CTkButton(
            s, text="⚡   CALCULAR FONTE",
            height=50, fg_color=p["azul"], hover_color=p["azul2"],
            text_color="#FFF", font=("Segoe UI", 13, "bold"),
            corner_radius=8, command=self._calcular,
        )
        self._btn_calc.pack(fill="x", padx=20, pady=(8, 6))

        # Salvar / Abrir rápido
        row = ctk.CTkFrame(s, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 24))
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        ctk.CTkButton(
            row, text="💾  Salvar", height=34,
            fg_color=p["card2"], hover_color=p["glass"],
            text_color=p["amber"], border_color=p["amber"], border_width=1,
            font=("Segoe UI", 9, "bold"), corner_radius=6,
            command=self._salvar_projeto,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4))

        ctk.CTkButton(
            row, text="📂  Abrir", height=34,
            fg_color=p["card2"], hover_color=p["glass"],
            text_color=p["text2"], border_color=p["text3"], border_width=1,
            font=("Segoe UI", 9, "bold"), corner_radius=6,
            command=self._abrir_projeto,
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0))

    def _mk_sep(self, parent, titulo):
        p = CORES[self._tema]
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=(16, 4))
        if titulo:
            ctk.CTkLabel(
                f, text=titulo, font=("Segoe UI", 7, "bold"),
                text_color=p["text3"],
            ).pack(side="left")
        ctk.CTkFrame(f, height=1, fg_color=p["text3"]).pack(
            side="right", fill="x", expand=True, padx=(6, 0), pady=6,
        )

    # ─── Coluna direita ───────────────────────────────────────────────────────

    def _build_dir(self):
        p = CORES[self._tema]
        self._frame_dir = ctk.CTkFrame(self, fg_color=p["cosmos"], corner_radius=0)
        self._frame_dir.grid(row=1, column=1, sticky="nsew", padx=(1, 0))
        self._frame_dir.columnconfigure(0, weight=3)
        self._frame_dir.columnconfigure(1, weight=2)
        self._frame_dir.rowconfigure(0, weight=1)

        self._frame_res = ctk.CTkFrame(
            self._frame_dir, fg_color=p["card"], corner_radius=12,
            border_width=1, border_color=p["text3"],
        )
        self._frame_res.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)

        self._frame_graf = ctk.CTkFrame(
            self._frame_dir, fg_color=p["card"], corner_radius=12,
            border_width=1, border_color=p["text3"],
        )
        self._frame_graf.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)

        self._placeholder()
        self._build_grafico_vazio()

    def _placeholder(self):
        p = CORES[self._tema]
        for w in self._frame_res.winfo_children():
            w.destroy()
        ctk.CTkLabel(self._frame_res, text="⚡",
                     font=("Segoe UI", 56), text_color=p["text3"]).pack(expand=True)
        ctk.CTkLabel(self._frame_res,
                     text="Configure os parâmetros\ne pressione CALCULAR FONTE",
                     font=("Segoe UI", 12), text_color=p["text3"],
                     justify="center").pack(pady=(0, 70))

    def _build_grafico_vazio(self):
        p = CORES[self._tema]
        for w in self._frame_graf.winfo_children():
            w.destroy()
        ctk.CTkLabel(self._frame_graf, text="Astrolábio de Engenharia",
                     font=("Segoe UI", 11, "bold"),
                     text_color=p["text2"]).pack(anchor="w", padx=14, pady=(14, 4))
        ctk.CTkLabel(self._frame_graf,
                     text="Execute um cálculo para ver\nas Curvas de Schade com\no ponto do projeto marcado.",
                     font=("Segoe UI", 9), text_color=p["text3"],
                     justify="center").pack(expand=True)

    # ─── Saídas ───────────────────────────────────────────────────────────────

    def _add_saida(self):
        if len(self._paineis) >= 6:
            return
        n  = len(self._paineis) + 1
        ps = PainelSaida(
            self._cont_saidas, numero=n,
            on_remove=self._rem_saida, tema=self._tema,
            fg_color="transparent",
        )
        ps.pack(fill="x", pady=(0, 6))
        self._paineis.append(ps)
        self._modificado = True

    def _rem_saida(self, painel):
        if len(self._paineis) <= 1:
            return
        self._paineis.remove(painel)
        painel.pack_forget()
        painel.destroy()
        for i, ps in enumerate(self._paineis):
            ps._n = i + 1
        self._modificado = True

    # ─── Calcular ─────────────────────────────────────────────────────────────

    def _calcular(self):
        erros = []
        for ps in self._paineis:
            erros += ps.validar()
        if erros:
            messagebox.showerror("Parâmetros inválidos", "\n".join(erros))
            return

        try:
            Vp   = float(self._vp.get().replace("V", ""))
            Vond = float(self._vond.get() or 3.0)
            Vd   = float(self._vd.get() or 0.7)
            saidas = [ps.get_saida() for ps in self._paineis]
        except ValueError as e:
            messagebox.showerror("Erro", f"Valores inválidos: {e}")
            return

        self._btn_calc.configure(state="disabled", text="Calculando…")
        self.update()

        def _run():
            try:
                r = dimensionar(saidas, Vp=Vp, Vond=Vond, Vd=Vd)
                self._resultado  = r
                self._modificado = True
                self.after(0, lambda: self._on_calculado(r))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erro no motor", str(e)))
            finally:
                self.after(0, lambda: self._btn_calc.configure(
                    state="normal", text="⚡   CALCULAR FONTE"
                ))

        threading.Thread(target=_run, daemon=True).start()

    def _on_calculado(self, r: Resultado):
        self._mostrar(r)
        self._draw_schade(r)
        
        # Auto-salva se já tem caminho
        if self._caminho:
            nome = self._entry_nome.get() or self._nome_proj
            salvar_projeto_helios(r, self._caminho, nome)
            
            # Zera a flag pois o auto-save garantiu que não há alterações pendentes
            self._modificado = False

        # Aura nos cards com alerta
        alertas_idx = {rs.indice - 1 for rs in r.res_saidas
                       if rs.alerta_dissipador or rs.alerta_corrente}
        for i, ps in enumerate(self._paineis):
            ps.set_alerta(i in alertas_idx)

    # ─── Painel de resultados ─────────────────────────────────────────────────

    def _mostrar(self, r: Resultado):
        p = CORES[self._tema]
        for w in self._frame_res.winfo_children():
            w.destroy()

        scroll = ctk.CTkScrollableFrame(
            self._frame_res, fg_color="transparent",
            scrollbar_button_color=p["text3"],
        )
        scroll.pack(fill="both", expand=True)

        # Helpers locais
        def _titulo(txt):
            ctk.CTkLabel(scroll, text=txt,
                         font=("Segoe UI", 10, "bold"),
                         text_color=p["ciano"]).pack(anchor="w", padx=16, pady=(12, 2))
            ctk.CTkFrame(scroll, height=1, fg_color=p["text3"]).pack(
                fill="x", padx=16, pady=(0, 4))

        def _kv(k, v, dest=False):
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=1)
            row.columnconfigure(0, weight=1)
            row.columnconfigure(1, weight=0)
            ctk.CTkLabel(row, text=k, font=("Segoe UI", 9),
                         text_color=p["text2"], anchor="w").grid(
                row=0, column=0, sticky="w")
            ctk.CTkLabel(row, text=str(v),
                         font=("Consolas", 9) if dest else ("Segoe UI", 9),
                         text_color=p["azul"] if dest else p["text"],
                         anchor="e").grid(row=0, column=1, sticky="e", padx=(8, 0))

        def _badge(txt, cor=None):
            cor = cor or p["azul"]
            fg  = "#000" if cor == p["amber"] else "#FFF"
            ctk.CTkLabel(scroll, text=txt,
                         font=("Segoe UI", 9, "bold"),
                         fg_color=cor, text_color=fg,
                         corner_radius=4, height=22,
                         wraplength=400, justify="left").pack(
                fill="x", padx=16, pady=(2, 4))

        # ── Cabeçalho
        ctk.CTkLabel(scroll, text="Memorial de Cálculo",
                     font=("Segoe UI", 14, "bold"),
                     text_color=p["text"]).pack(anchor="w", padx=16, pady=(14, 0))
        ctk.CTkLabel(scroll,
                     text=f"{len(r.saidas)} saída(s)  ·  {r.Vp}V  ·  Ripple {r.Vond}V  ·  Vd {r.Vd}V",
                     font=("Segoe UI", 8), text_color=p["text3"]).pack(anchor="w", padx=16)

        # ── 1. Transformador
        _titulo("1 · Transformador")
        _kv("Vout máx (pior caso)",   f"{r.Vout_max} V")
        _kv("Corrente total ΣIL",     f"{r.IL_total:.3f} A")
        _kv("Vsmáx",                  f"{r.Vsmax:.2f} V")
        _kv("Vsef",                   f"{r.Vsef:.2f} V")
        _kv("Vin méd / máx / mín",    f"{r.Vinmedia:.1f} / {r.Vinmax:.1f} / {r.Vinmin:.1f} V")
        _badge(f"▶  {r.TR_cod}  —  {r.TR_Vs}V / {r.TR_Is}A / {r.TR_Ss}VA")

        # ── 2. Capacitor
        _titulo("2 · Capacitor Eletrolítico")
        _kv("C calculado",    f"{r.C_calc_uF:.1f} µF")
        _kv("V isolação mín.", f"{r.Vcap_min:.1f} V")
        _badge(f"▶  {r.C_com} µF / {r.V_cap_com} V")

        # ── 3. Diodos
        _titulo("3 · Diodos  (ponte Graetz)")
        _kv("Ifav",              f"{r.Ifav:.4f} A")
        _kv("IFrms",             f"{r.IFrms:.4f} A", True)
        _kv("IFrm (pico)",       f"{r.IFrm:.4f} A")
        _kv("VRRM mín.",         f"{r.VRRM:.2f} V")
        _kv("Corrente surto",    f"{r.IFsm:.2f} A")
        _kv("n·ωs·RL·C",        f"{r.x_param:.3f}", True)
        _kv("Rs/(n·RL) %",      f"{r.Rs_nRL_pct:.4f} %")
        _kv("Fig.3  IFrms/Ifav", f"{r.curva_fig3:.4f}", True)
        _kv("Fig.4  IFrm/Ifav",  f"{r.curva_fig4:.4f}", True)
        if r.diodo:
            _badge(f"▶  {r.diodo['modelo']}  —  {r.diodo['descricao']}")

        # ── 4. Fusíveis
        _titulo("4 · Fusíveis")
        _kv("Is = √2 × IFrms",  f"{r.Is:.4f} A")
        _kv("KT = Vp / Vsef",   f"{r.KT:.4f}")
        _kv("Ip = Is / KT",     f"{r.Ip:.4f} A")
        _badge(f"▶  Secundário: {r.Fus_s} A   |   Primário: {r.Fus_p} A")

        # ── 5. Reguladores
        _titulo("5 · Reguladores")
        for rs in r.res_saidas:
            tag  = "VAR" if rs.tipo == "variavel" else "FIX"
            alrt = rs.alerta_dissipador or rs.alerta_corrente
            card = ctk.CTkFrame(
                scroll, fg_color=p["glass"], corner_radius=8,
                border_width=2 if alrt else 1,
                border_color=p["amber"] if alrt else p["text3"],
            )
            card.pack(fill="x", padx=16, pady=3)

            hdr = ctk.CTkFrame(card, fg_color="transparent")
            hdr.pack(fill="x", padx=10, pady=(6, 2))

            ctk.CTkLabel(
                hdr, text=f" {tag} ",
                font=("Segoe UI", 8, "bold"),
                fg_color=p["amber"] if alrt else p["azul2"],
                text_color="#000" if alrt else "#FFF",
                corner_radius=3, height=18,
            ).pack(side="left")

            ctk.CTkLabel(
                hdr,
                text=f"  Saída {rs.indice}  —  {rs.Vout_desejado}V / {rs.IL}A",
                font=("Segoe UI", 10, "bold"), text_color=p["text"],
            ).pack(side="left")

            if rs.alerta_dissipador:
                ctk.CTkLabel(hdr, text=" ⚠ DISSIPADOR ",
                             font=("Segoe UI", 7, "bold"),
                             fg_color=p["amber"], text_color="#000",
                             corner_radius=3).pack(side="right")

            b = ctk.CTkFrame(card, fg_color="transparent")
            b.pack(fill="x", padx=10, pady=(0, 8))

            def _rkv(k, v, _b=b):
                rw = ctk.CTkFrame(_b, fg_color="transparent")
                rw.pack(fill="x", pady=1)
                ctk.CTkLabel(rw, text=k, font=("Segoe UI", 8),
                             text_color=p["text2"], width=160, anchor="w").pack(side="left")
                ctk.CTkLabel(rw, text=str(v), font=("Consolas", 9),
                             text_color=p["azul"], anchor="e").pack(side="right")

            _rkv("Modelo",    f"{rs.modelo}  {'✓' if rs.exato else '≈'}")
            _rkv("Vout real", f"{rs.Vout_real:.3f} V")
            _rkv("Vreg / Pd", f"{rs.Vreg:.2f}V  /  {rs.Pd:.3f}W")
            if rs.R1_com:
                _rkv("R1 / R2", f"{rs.R1_com} Ω  /  {rs.R2:.0f} Ω")
            if rs.sugestao_alt:
                ctk.CTkLabel(b, text=f"↳ {rs.sugestao_alt}",
                             font=("Segoe UI", 8), text_color=p["text3"],
                             wraplength=320, justify="left").pack(anchor="w")

        # ── Alertas globais
        if r.alertas:
            _titulo("⚠  Alertas do Projeto")
            
            for a in r.alertas:
                # Frame contêiner para o alerta
                alert_frame = ctk.CTkFrame(scroll, fg_color="transparent")
                alert_frame.pack(fill="x", padx=(16, 28), pady=2)

                # Label do alerta
                lbl = ctk.CTkLabel(
                    alert_frame,
                    text=f"• {a}",
                    font=("Segoe UI", 9),
                    text_color=p["amber"],
                    justify="left",
                    anchor="w"
                )
                lbl.pack(fill="x")

                # Atualização reativa: ajusta o wraplength quando o frame muda de tamanho
                def atualizar_wrap(event, label=lbl):
                    label.configure(wraplength=event.width - 10)

                alert_frame.bind("<Configure>", atualizar_wrap)

        # ── Botão PDF
        ctk.CTkFrame(scroll, height=1, fg_color=p["text3"]).pack(
            fill="x", padx=16, pady=(14, 6))
        self._btn_pdf = ctk.CTkButton(
            scroll,
            text="📄  Exportar Memorial de Cálculo (PDF)",
            height=42, fg_color=p["azul"], hover_color=p["azul2"],
            text_color="#FFF", font=("Segoe UI", 10, "bold"),
            corner_radius=8, command=self._exportar_pdf,
        )
        self._btn_pdf.pack(fill="x", padx=16, pady=(0, 16))

    # ─── Astrolábio de Engenharia ─────────────────────────────────────────────

    def _draw_schade(self, r: Resultado):
        p = CORES[self._tema]
        for w in self._frame_graf.winfo_children():
            w.destroy()

        hdr = ctk.CTkFrame(self._frame_graf, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(12, 2))

        ctk.CTkLabel(hdr, text="Astrolábio de Engenharia",
                     font=("Segoe UI", 11, "bold"),
                     text_color=p["text2"]).pack(side="left")

        self._fig_sel = ctk.StringVar(value="Fig. 3")
        ctk.CTkSegmentedButton(
            hdr, values=["Fig. 3", "Fig. 4"],
            variable=self._fig_sel,
            selected_color=p["azul"], selected_hover_color=p["azul2"],
            unselected_color=p["glass"], text_color=p["text"],
            font=("Segoe UI", 8), height=24,
            command=lambda v: self._render_schade(r),
        ).pack(side="right")

        ctk.CTkLabel(self._frame_graf,
                     text="Parâmetro: Rs / (n·RL) em %  ·  Ciano → Dourado",
                     font=("Segoe UI", 7), text_color=p["text3"]).pack(anchor="w", padx=14)

        self._host_schade = ctk.CTkFrame(self._frame_graf, fg_color="transparent")
        self._host_schade.pack(fill="both", expand=True, padx=6, pady=(4, 8))
        self._render_schade(r)

    def _render_schade(self, r: Resultado):
        p     = CORES[self._tema]
        dark  = self._tema == "dark"
        for w in self._host_schade.winfo_children():
            w.destroy()

        fig3_mode = self._fig_sel.get() == "Fig. 3"
        fn        = schade_fig3 if fig3_mode else schade_fig4
        logy      = not fig3_mode

        fig, ax = plt.subplots(figsize=(5.6, 4.5))
        fig.patch.set_facecolor(p["graf_bg"])
        ax.set_facecolor(p["graf_ax"])

        # Curvas gradiente ciano (#00D4FF) → dourado (#FFB846)
        n = len(_CURVES)
        xs = np.logspace(0, 3, 300)
        for idx, rs in enumerate(_CURVES):
            t    = idx / max(n - 1, 1)
            r_ch = int(0x00 + t * (0xFF - 0x00))
            g_ch = int(0xD4 + t * (0xB8 - 0xD4))
            b_ch = int(0xFF + t * (0x46 - 0xFF))
            cor  = f"#{r_ch:02X}{g_ch:02X}{b_ch:02X}"
            lw   = 1.4 if rs in [0.5, 1.0, 2.0] else 0.7
            ys   = [fn(x, rs) for x in xs]
            ax.plot(xs, ys, color=cor, linewidth=lw, alpha=0.88)
            ax.annotate(f"{rs}%", xy=(1000, ys[-1]),
                        fontsize=5, color=cor, va="center",
                        ha="left", xytext=(3, 0), textcoords="offset points")

        # Ponto do projeto — cruzeta de astrolábio
        xp = r.x_param
        rp = r.Rs_nRL_pct
        yp = fn(xp, rp)
        amber = p["amber"]

        ax.axvline(xp, color=amber, lw=0.8, ls="--", alpha=0.55)
        ax.axhline(yp, color=amber, lw=0.8, ls="--", alpha=0.55)

        # Círculo externo
        ax.plot(xp, yp, "o",
                markersize=13, color=amber, zorder=12,
                markeredgecolor="#FFF" if dark else "#333",
                markeredgewidth=1.5, alpha=0.9)
        # Cruz central (estilo mapa estelar)
        ax.plot(xp, yp, "+",
                markersize=10, zorder=13,
                color="#FFF" if dark else "#333",
                markeredgewidth=1.2)
        # Anotação
        ax.annotate(
            f"  ({xp:.1f} ; {yp:.3f})",
            xy=(xp, yp), fontsize=7.5, color=amber, fontweight="bold",
            xytext=(14, 8), textcoords="offset points",
            arrowprops=dict(arrowstyle="->", color=amber, lw=0.8),
        )

        ax.set_xscale("log")
        if logy:
            ax.set_yscale("log")
        ax.set_xlabel("n · ωs · RL · C", color=p["text2"], fontsize=8)
        ax.set_ylabel("IFrms / Ifav" if fig3_mode else "IFrm / Ifav",
                      color=p["text2"], fontsize=8)
        ax.tick_params(colors=p["text2"], labelsize=6.5)
        for sp in ax.spines.values():
            sp.set_edgecolor(p["graf_grid"])
        ax.grid(True, which="both", color=p["graf_grid"], lw=0.35, alpha=0.65)
        fig.tight_layout(pad=0.8)

        cv = FigureCanvasTkAgg(fig, master=self._host_schade)
        cv.draw()
        cv.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)

    # ─── Exportar PDF ─────────────────────────────────────────────────────────

    def _exportar_pdf(self):
        if not self._resultado:
            messagebox.showwarning("Sem resultado",
                                   "Execute um cálculo antes de exportar.")
            return
        nome = self._entry_nome.get() or "helios"
        cam  = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"memorial_{nome}.pdf",
            title="Exportar Memorial de Cálculo",
        )
        if not cam:
            return
        self._btn_pdf.configure(state="disabled", text="Gerando PDF…")
        self.update()

        def _run():
            try:
                gerar_pdf(self._resultado, cam, nome)
                self.after(0, lambda: messagebox.showinfo(
                    "PDF Exportado", f"Memorial salvo:\n{cam}"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erro ao gerar PDF", str(e)))
            finally:
                self.after(0, lambda: self._btn_pdf.configure(
                    state="normal", text="📄  Exportar Memorial de Cálculo (PDF)"))

        threading.Thread(target=_run, daemon=True).start()

    # ─── Sistema .helios ──────────────────────────────────────────────────────

    def _salvar_projeto(self):
        if not self._resultado:
            messagebox.showwarning("Sem resultado",
                                   "Execute um cálculo antes de salvar.")
            return
        nome = self._entry_nome.get() or "Novo Projeto"
        cam  = self._caminho
        if not cam:
            cam = filedialog.asksaveasfilename(
                defaultextension=".helios",
                filetypes=[("Projeto H.E.L.I.O.S.", "*.helios")],
                initialfile=f"{nome}.helios",
                title="Salvar Projeto H.E.L.I.O.S.",
            )
        if not cam:
            return
        ok, msg = salvar_projeto_helios(self._resultado, cam, nome)
        if ok:
            self._caminho    = cam
            self._modificado = False
            _registrar_recente(cam, nome)
            self.title(f"H.E.L.I.O.S.  ·  {nome}")
        else:
            messagebox.showerror("Erro ao salvar", msg)

    def _abrir_projeto(self, caminho=None):
        if not caminho:
            caminho = filedialog.askopenfilename(
                filetypes=[("Projeto H.E.L.I.O.S.", "*.helios")],
                title="Abrir Projeto H.E.L.I.O.S.",
            )
        if not caminho:
            return
        ok, res, nome = carregar_projeto_helios(caminho)
        if ok:
            self._resultado  = res
            self._caminho    = caminho
            self._nome_proj  = nome
            _registrar_recente(caminho, nome)
            self._restaurar_ui(res)
            self._mostrar(res)
            self._draw_schade(res)
            self.title(f"H.E.L.I.O.S.  ·  {nome}")
            
            # Zera a flag de modificação APÓS a interface terminar de ser montada
            self._modificado = False 
        else:
            messagebox.showerror("Erro ao abrir", str(res))

    def _restaurar_ui(self, r: Resultado):
        self._vp.set(f"{r.Vp}V")
        self._vond.delete(0, "end"); self._vond.insert(0, str(r.Vond))
        self._vd.delete(0, "end");   self._vd.insert(0, str(r.Vd))
        self._entry_nome.delete(0, "end")
        self._entry_nome.insert(0, self._nome_proj)

        while len(self._paineis) > len(r.saidas):
            ps = self._paineis.pop()
            ps.pack_forget(); ps.destroy()
        while len(self._paineis) < len(r.saidas):
            self._add_saida()

        for i, s in enumerate(r.saidas):
            ps = self._paineis[i]
            ps._tipo.set("Variável (LM317)" if s.tipo == "variavel"
                         else "Fixa (LM78xx)")
            ps._on_tipo(ps._tipo.get())
            ps._vout.delete(0, "end"); ps._vout.insert(0, str(s.Vout))
            ps._il.delete(0, "end");   ps._il.insert(0, str(s.IL))
            if s.tipo == "variavel":
                ps._r2.delete(0, "end"); ps._r2.insert(0, str(s.R2))

    def _novo_projeto(self):
        if self._modificado:
            if not messagebox.askyesno(
                "Projeto não salvo",
                "Há alterações não salvas. Descartar e criar novo?",
            ):
                return
        self._resultado  = None
        self._caminho    = None
        self._nome_proj  = "Novo Projeto"
        self.title("H.E.L.I.O.S. — Pantheon Systems")
        
        self._rebuild() # Aqui ele constrói o card S1 e seta como True sem querer
        
        self._modificado = False # <--- MOVA PARA CÁ (Última linha) para limpar a flag

    def _mostrar_dashboard(self):
        self.withdraw() # Garante que a tela de trás fique invisível
        dash = TelaDashboard(
            self,
            on_novo=self._novo_do_dash,
            on_abrir=self._abrir_do_dash,
            tema=self._tema,
        )
        # Se fechar o Dashboard no "X", mata o processo do Python para não ficar rodando fantasma
        dash.protocol("WM_DELETE_WINDOW", self.destroy)

    # --- Funções ponte para fazer a tela principal reaparecer ---
    def _novo_do_dash(self):
        self.deiconify() # Revela o Santuário
        self.state("zoomed")
        self._novo_projeto()

    def _abrir_do_dash(self, caminho):
        self.deiconify() # Revela o Santuário
        self.state("zoomed")
        self._abrir_projeto(caminho)

    def _on_fechar(self):
        if self._modificado and self._resultado:
            resp = messagebox.askyesnocancel(
                "Sair",
                "Há alterações não salvas.\nDeseja salvar antes de sair?",
            )
            if resp is None:
                return
            if resp:
                self._salvar_projeto()
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    App().mainloop()

if __name__ == "__main__":
    main()