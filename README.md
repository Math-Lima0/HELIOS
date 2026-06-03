# ☀️ H.E.L.I.O.S.

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.13](https://img.shields.io/badge/Python-3.13-F6D049?logo=python&logoColor=3776AB)](https://www.python.org/)

> **High Efficiency Linear Integrated Optimization System**

Plataforma de engenharia para dimensionamento, validação e documentação automatizada de fontes lineares reguladas.

---

## 📖 Visão Geral
O H.E.L.I.O.S. é uma plataforma desenvolvida para automatizar o processo de projeto de fontes lineares reguladas, transformando requisitos elétricos em soluções completas e tecnicamente validadas. 

O sistema combina modelos matemáticos clássicos da engenharia eletrônica com uma arquitetura moderna de software, permitindo que cálculos normalmente realizados manualmente sejam executados de forma rápida, rastreável e reproduzível. Além do dimensionamento elétrico, o H.E.L.I.O.S. realiza a seleção automática de componentes comerciais, valida parâmetros físicos e gera documentação técnica.

## 🔬 Diferenciais Técnicos
* **Precisão Matemática:** Implementação baseada em metodologias clássicas de projeto, utilizando a interpolação das curvas de Schade.
* **Validação Física:** Bloqueio rigoroso de parâmetros de entrada fisicamente inconsistentes (tensões impossíveis, correntes inválidas).
* **Seleção Comercial:** Escolha automática de componentes reais de mercado (Transformadores, Diodos, Reguladores, Série E24).
* **Arquitetura Desacoplada:** Separação clara entre a Interface Gráfica (Desktop), a API REST e o Motor Matemático.
* **Reprodutibilidade:** Geração de memoriais de cálculo e memória técnica para auditoria de engenharia.
* **AI-Ready:** Estrutura de dados já preparada para integração com Agentes de Inteligência Artificial.

## 🧰 Tecnologias Utilizadas

| Camada | Tecnologia |
| :--- | :--- |
| **Backend & Motor** | Python 3.13 |
| **API REST** | FastAPI |
| **Validação de Dados** | Pydantic |
| **Interface Gráfica** | CustomTkinter |
| **Persistência & Docs** | JSON / Markdown / PDF |
| **Controle de Versão** | Git / GitHub |
| **Arquitetura** | Modular / Desacoplada |

## 📂 Estrutura do Projeto

```text
HELIOS/
│
├── src/
│   ├── calculos/        # Motor Volpiano e Curvas de Schade
│   ├── database/        # Catálogo de componentes comerciais
│   ├── models/          # Schemas Pydantic e validações físicas
│   ├── services/        # Lógica de relatórios e persistência
│   ├── ui/              # Interface gráfica CustomTkinter
│   └── api/             # Endpoints FastAPI
│
├── docs/                # Imagens, diagramas e memoriais
├── tests/               # Scripts de validação e estresse
├── requirements.txt     # Dependências do ecossistema
├── LICENSE              # Licença GNU AGPL v3
└── main.py              # Ponto de entrada unificado
⚙️ Como Executar
1. Instalação das dependências:

Bash
pip install -r requirements.txt
2. Executar a Interface Gráfica (Desktop):

Bash
python main.py
3. Executar o Servidor da API REST:

Bash
uvicorn src.api.api:app --reload
🛣️ Roadmap de Evolução
V1 — Engenharia Profissional (Foco Atual)
[x] Motor de Cálculo e Interface Desktop

[x] API REST Base

[ ] Geração Avançada de Relatórios PDF

[ ] Exportação/Importação JSON de Projetos

[ ] Conteinerização (Docker) e Autenticação de API

V2 — Inteligência Técnica
[ ] Integração RAG (Retrieval-Augmented Generation) para leitura de datasheets.

[ ] Base de conhecimento eletrônica expansível.

[ ] Memória técnica de projetos anteriores.

V3 — Integração EDA (Electronic Design Automation)
[ ] Geração automatizada de Netlists.

[ ] Integração de metadados com KiCad.

[ ] Exportação de modelos de simulação (LTspice).

V4+ — Simulação e Ecossistema
[ ] Simulação paramétrica via Monte Carlo.

[ ] Digital Twin (Integração IoT para leitura de dados reais).

[ ] Orquestração completa com o ecossistema A.R.E.S.

🌌 Visão de Longo Prazo
O H.E.L.I.O.S. é o núcleo computacional da iniciativa Pantheon Systems.

Sua evolução prevê a integração direta com o A.R.E.S. (Autonomous Reasoning Engineering System), formando um ecossistema de engenharia assistida por Inteligência Artificial capaz de realizar não apenas o dimensionamento e validação, mas também oferecer suporte técnico especializado, orquestração de dados e tomada de decisão autônoma.

📜 Licença e Direitos Autorais
Este projeto (código-fonte) é distribuído sob a licença GNU AGPL v3. O código pode ser estudado, modificado e redistribuído de forma aberta, desde que as condições da licença sejam rigorosamente respeitadas (incluindo a obrigatoriedade de abertura de código para aplicações servidas em rede/SaaS).

⚠️ Marca e Identidade Visual:
A marca H.E.L.I.O.S., o logotipo, a identidade visual associada, a documentação oficial e os ativos relacionados à marca Pantheon Systems permanecem estritamente protegidos por direitos autorais. O uso da licença de software aberto não concede permissão para uso comercial ou redistribuição sob o nome Pantheon Systems sem autorização prévia.

Copyright © 2026 Matheus. Todos os direitos reservados. Engenharia de Controle e Automação.