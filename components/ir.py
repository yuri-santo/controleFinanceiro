# components/ir.py
import dash
from dash import html, dcc, Input, Output, State, callback, ctx
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import pandas as pd
from services import ir, db  # usa o services/ir.py e db.py do seu projeto

# registre com tema bonito no app principal (app.py):
# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX])

dash.register_page(__name__, path="/ir", name="Imposto de Renda (Assistente)")

# ---------- Helpers de UI ----------
def SectionHeader(icon, title, subtitle=None):
    return html.Div(
        dbc.Row([
            dbc.Col(DashIconify(icon=icon, width=26), width="auto"),
            dbc.Col(html.H5(title, className="mb-0")),
            dbc.Col(html.Small(subtitle, className="text-muted"), width=True)
        ], align="center", className="g-2"),
        className="mb-2"
    )

def MoneyInput(id_, label, placeholder="0,00"):
    return dbc.InputGroup([
        dbc.InputGroupText("R$"),
        dbc.Input(id_, placeholder=placeholder, type="text", inputMode="decimal")
    ], className="mb-2"), dbc.FormText("Use vírgula como separador decimal. Ex: 1.234,56")

def DocHelp(id_, text):
    return html.Span([
        html.Span(" ?", id=id_, className="badge rounded-pill bg-info-subtle text-info-emphasis",
                  style={"cursor": "help", "marginLeft":"6px"}),
        dbc.Tooltip(text, target=id_, placement="right", autohide=True),
    ])

def Select(id_, label, options, value=None, helptext=None):
    return html.Div([
        dbc.Label([label, DocHelp(f"help-{id_}", helptext or "")]) if helptext else dbc.Label(label),
        dcc.Dropdown(id=id_, options=options, value=value, clearable=False),
    ], className="mb-3")

def TextInput(id_, label, placeholder="", helptext=None):
    return html.Div([
        dbc.Label([label, DocHelp(f"help-{id_}", helptext)]) if helptext else dbc.Label(label),
        dbc.Input(id=id_, placeholder=placeholder, type="text"),
    ], className="mb-2")

def CPFInput(id_):  # validação simples (formato)
    return TextInput(id_, "CPF", "000.000.000-00", "Informe apenas números ou no formato 000.000.000-00")

def CNPJInput(id_):
    return TextInput(id_, "CNPJ", "00.000.000/0001-00", "CNPJ da fonte pagadora / plano de saúde / escola, quando aplicável")

# ---------- Catálogos (PF) ----------
PAGAMENTOS = [
    {"label":"10 – Médicos (Brasil)", "value":10},
    {"label":"11 – Dentistas (Brasil)", "value":11},
    {"label":"21 – Hospitais/Laboratórios", "value":21},
    {"label":"26 – Plano de saúde (Brasil)", "value":26},
    {"label":"36 – Previdência complementar (PGBL)", "value":36},
    {"label":"37 – Previdência complementar empresarial", "value":37},
]
BENS_DIREITOS = [
    {"label":"03–01 Ações (inclusive listadas)", "value":"3-1"},
    {"label":"04–02 Títulos tributáveis (CDB/Tesouro/Debêntures)", "value":"4-2"},
    {"label":"04–03 Títulos isentos (LCI/LCA/CRI/CRA)", "value":"4-3"},
]

# ---------- Layout ----------
layout = dbc.Container([
    html.Br(),
    dbc.Row([
        dbc.Col([
            html.H3("Imposto de Renda — Assistente Visual"),
            dbc.Alert([
                html.B("Como usar: "),
                "preencha cada bloco. Eu mostro códigos da Receita, textos prontos e o que copiar/colar."
            ], color="primary", className="mt-2")
        ])
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    SectionHeader("mdi:account-cash", "Configurações"),
                    dbc.Row([
                        dbc.Col(Select("ano", "Ano-calendário", [{"label":str(y),"value":y} for y in range(2019,2031)], value=2025,
                                       helptext="Ano dos rendimentos (ex.: 2025). A declaração é entregue no ano seguinte."), md=4),
                        dbc.Col(Select("perfil", "Perfil", [{"label":"Pessoa Física (PF)","value":"pf"},{"label":"Pessoa Jurídica (PJ)","value":"pj"}],
                                       value="pf"), md=4),
                        dbc.Col(Select("regime_pj", "Regime (PJ)", [{"label":"Simples","value":"Simples"},{"label":"Presumido","value":"Presumido"},{"label":"Real","value":"Real"}],
                                       value="Simples", helptext="Se PF, ignore."), md=4),
                    ])
                ])
            ], className="mb-4"),

            # ----- PF: Seções em acordeões -----
            dbc.Accordion([
                dbc.AccordionItem([
                    SectionHeader("mdi:card-account-details-star", "Identificação"),
                    dbc.Row([
                        dbc.Col(TextInput("pf-nome","Nome completo","Seu nome exatamente como no CPF"), md=6),
                        dbc.Col(CPFInput("pf-cpf"), md=6),
                    ]),
                    dbc.Row([
                        dbc.Col(TextInput("pf-email","E-mail","seu@email.com"), md=6),
                        dbc.Col(TextInput("pf-tel","Telefone","(xx) xxxxx-xxxx"), md=6),
                    ]),
                    html.Hr(),
                    SectionHeader("mdi:bank-transfer", "Conta para Restituição"),
                    dbc.Row([
                        dbc.Col(TextInput("pf-banco","Banco (código)","001 – Banco do Brasil"), md=4),
                        dbc.Col(TextInput("pf-ag","Agência","0001"), md=4),
                        dbc.Col(TextInput("pf-conta","Conta","12345-6"), md=4),
                    ]),
                    dbc.Button("Salvar Identificação", id="save-pf-id", color="success", className="mt-2",
                               n_clicks=0),
                ], title="PF • Identificação e Restituição"),

                dbc.AccordionItem([
                    SectionHeader("mdi:file-document-edit", "Fontes Pagadoras (Tributáveis)"),
                    dbc.Row([
                        dbc.Col(CNPJInput("fp-cnpj"), md=4),
                        dbc.Col(TextInput("fp-razao","Razão Social","EMPRESA S/A"), md=8),
                    ]),
                    dbc.Row([
                        dbc.Col(Select("fp-tipo","Tipo de rendimento",[
                            {"label":"Salário","value":"salario"},
                            {"label":"Aposentadoria","value":"aposentadoria"},
                            {"label":"Estágio/Bolsa","value":"estagio"}], "salario",
                            helptext="Informe conforme Informe de Rendimentos"), md=4),
                        dbc.Col(MoneyInput("fp-rbruto","Rendimento Bruto")[0], md=4),
                        dbc.Col(MoneyInput("fp-irrf","IRRF")[0], md=4),
                    ]),
                    dbc.Row([
                        dbc.Col(MoneyInput("fp-prev","Contribuição Previdenciária (INSS)")[0], md=4),
                        dbc.Col(MoneyInput("fp-pensao","Pensão alimentícia (se houver)")[0], md=4),
                        dbc.Col(MoneyInput("fp-13","13º salário bruto")[0], md=4),
                    ]),
                    dbc.Button("Adicionar Fonte Pagadora", id="add-fp", color="primary", className="mt-2", n_clicks=0),
                    dbc.Toast(id="toast-fp", header="Fonte salva", icon="success", is_open=False, duration=2500,
                              style={"position":"fixed","bottom":"20px","right":"20px","zIndex":2000}),
                ], title="PF • Fontes Pagadoras"),

                dbc.AccordionItem([
                    SectionHeader("mdi:heart-pulse", "Pagamentos / Deduções"),
                    dbc.Row([
                        dbc.Col(Select("pg-codigo","Código (Ficha Pagamentos)", PAGAMENTOS, 10,
                                       helptext="Ex.: 10 médicos, 26 plano de saúde, 36 PGBL (dedutível até 12% da renda bruta)"), md=6),
                        dbc.Col(CNPJInput("pg-doc"), md=6),
                    ]),
                    dbc.Row([
                        dbc.Col(TextInput("pg-nome","Nome do prestador","Dr(a). Fulano / CNPJ Plano"), md=6),
                        dbc.Col(MoneyInput("pg-valor","Valor pago")[0], md=6),
                    ]),
                    dbc.Row([
                        dbc.Col(TextInput("pg-data","Data (AAAA-MM-DD)","2025-03-15"), md=6),
                        dbc.Col(Select("pg-reembolso","Teve reembolso?", [{"label":"Não","value":0},{"label":"Sim","value":1}], 0), md=6),
                    ]),
                    dbc.Button("Adicionar Pagamento", id="add-pg", color="primary", className="mt-2", n_clicks=0),
                    dbc.Toast(id="toast-pg", header="Pagamento salvo", icon="success", is_open=False, duration=2500,
                              style={"position":"fixed","bottom":"20px","right":"20px","zIndex":2000}),
                ], title="PF • Deduções (Saúde, Educação, Previdência etc.)"),

                dbc.AccordionItem([
                    SectionHeader("mdi:chart-timeline-variant", "Renda Variável (Bolsa)"),
                    dbc.Row([
                        dbc.Col(Select("rv-mes","Mês", [{"label":f"{m:02d}","value":m} for m in range(1,13)], 1), md=3),
                        dbc.Col(MoneyInput("rv-lucro-comum","Lucro/Prejuízo – operações comuns")[0], md=3),
                        dbc.Col(MoneyInput("rv-lucro-dt","Lucro/Prejuízo – day trade")[0], md=3),
                        dbc.Col(MoneyInput("rv-irrf","IRRF no mês (somatório)")[0], md=3),
                    ]),
                    dbc.Button("Salvar mês", id="add-rv", color="primary", className="mt-2", n_clicks=0),
                    dbc.Toast(id="toast-rv", header="Mês salvo", icon="success", is_open=False, duration=2500,
                              style={"position":"fixed","bottom":"20px","right":"20px","zIndex":2000}),
                    html.Hr(),
                    dbc.Button("Importar automaticamente de trades (rascunho)", id="rv-auto", color="secondary", outline=True, n_clicks=0),
                    html.Div(id="rv-auto-msg", className="text-muted mt-2"),
                ], title="PF • Bolsa (DARF 6015)"),

                dbc.AccordionItem([
                    SectionHeader("mdi:shield-home", "Bens e Direitos"),
                    dbc.Row([
                        dbc.Col(Select("bd-codigo","Grupo/Código", BENS_DIREITOS, "3-1",
                                       helptext="Ações 03–01, CDB/Tesouro 04–02, LCI/LCA 04–03"), md=6),
                        dbc.Col(TextInput("bd-doc","CPF/CNPJ relacionado","CNPJ da corretora/emitente (se houver)"), md=6),
                    ]),
                    dbc.Row([
                        dbc.Col(TextInput("bd-discr","Discriminação (texto)","Eu gero isso pra você ao salvar"), md=12),
                    ]),
                    dbc.Row([
                        dbc.Col(TextInput("bd-aquis","Data de aquisição","AAAA-MM-DD"), md=4),
                        dbc.Col(TextInput("bd-sit-ant","Situação 31/12 ano anterior","0,00"), md=4),
                        dbc.Col(TextInput("bd-sit-ano","Situação 31/12 ano-base","0,00"), md=4),
                    ]),
                    dbc.Button("Adicionar Bem/Direito", id="add-bd", color="primary", className="mt-2", n_clicks=0),
                    dbc.Toast(id="toast-bd", header="Bem/Direito salvo", icon="success", is_open=False, duration=2500,
                              style={"position":"fixed","bottom":"20px","right":"20px","zIndex":2000}),
                ], title="PF • Bens & Direitos"),
            ], start_collapsed=True, id="acc-pf"),

            # ----- PJ: Acordeões -----
            dbc.Accordion([
                dbc.AccordionItem([
                    SectionHeader("mdi:office-building", "Dados da Empresa"),
                    dbc.Row([
                        dbc.Col(CNPJInput("pj-cnpj"), md=6),
                        dbc.Col(TextInput("pj-razao","Razão Social","SUA EMPRESA LTDA"), md=6),
                    ]),
                    dbc.Row([
                        dbc.Col(TextInput("pj-cnae","CNAE principal","6201-5/01"), md=4),
                        dbc.Col(Select("pj-regime","Regime", [{"label":"Simples","value":"Simples"},{"label":"Presumido","value":"Presumido"},{"label":"Real","value":"Real"}], "Simples"), md=4),
                        dbc.Col(TextInput("pj-anexo","Anexo (se Simples)","Ex.: Anexo III"), md=4),
                    ]),
                    dbc.Button("Salvar Empresa", id="save-pj", color="success", className="mt-2", n_clicks=0),
                    dbc.Toast(id="toast-pj", header="Empresa salva", icon="success", is_open=False, duration=2500,
                              style={"position":"fixed","bottom":"20px","right":"20px","zIndex":2000}),
                ], title="PJ • Empresa"),
                dbc.AccordionItem([
                    SectionHeader("mdi:calculator-variant", "Apuração / Tributos"),
                    dbc.Row([
                        dbc.Col(Select("pj-periodo","Período", [{"label":f"T{t}","value":f"T{t}"} for t in range(1,5)] + [{"label":f"{m:02d}","value":f"M{m}"} for m in range(1,13)], "T1",
                                       helptext="Trimestre (Presumido/Real) ou Mês (Simples)"), md=3),
                        dbc.Col(MoneyInput("pj-fatur","Faturamento")[0], md=3),
                        dbc.Col(MoneyInput("pj-desp","Custos/Despesas")[0], md=3),
                        dbc.Col(MoneyInput("pj-folha","Folha (base INSS)")[0], md=3),
                    ]),
                    dbc.Button("Adicionar Período", id="add-pj-apur", color="primary", className="mt-2", n_clicks=0),
                    dbc.Toast(id="toast-pj-apur", header="Período salvo", icon="success", is_open=False, duration=2500,
                              style={"position":"fixed","bottom":"20px","right":"20px","zIndex":2000}),
                ], title="PJ • Apuração"),
            ], start_collapsed=True, id="acc-pj"),
            html.Br(),
            # CERTO (uma única definição de children como lista)
            dbc.Button(
                [DashIconify(icon="mdi:content-save-outline", width=20), html.Span(" Salvar tudo")],
                id="save-all", color="success", className="me-2"
            ),

            dbc.Button(
                [DashIconify(icon="mdi:file-export-outline", width=20), html.Span(" Exportar Excel/PDF")],
                id="export", color="secondary", outline=True
            ),

            html.Div(id="export-msg", className="text-muted mt-2"),
            html.Br(), html.Br(),
        ], md=8),

        # ----- Coluna de Resumo -----
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([DashIconify(icon="mdi:lightbulb-on-outline", width=22), html.Span("  Resumo Inteligente")]),
                dbc.CardBody([
                    html.Div(id="resumo-alertas"),
                    html.H6("Opção recomendada"),
                    html.Div(id="resumo-opcao", className="mb-2"),
                    html.H6("DARFs (se houver)"),
                    html.Ul(id="resumo-darfs", className="mb-2"),
                    html.H6("Atalhos úteis"),
                    html.Ul([
                        html.Li("Sicalc (emitir DARF 6015/0190)"),
                        html.Li("Manual da DIRPF (códigos por ficha)"),
                        html.Li("Agenda Tributária (códigos PJ)")
                    ], className="text-muted"),
                ])
            ], className="sticky-top", style={"top":"88px"})
        ], md=4),
    ]),
    html.Div(id="debug", style={"display":"none"})
], fluid=True)

# ---------- Callbacks (exemplos) ----------
@callback(Output("toast-fp","is_open"), Input("add-fp","n_clicks"),
          State("ano","value"), State("fp-cnpj","value"), State("fp-razao","value"),
          State("fp-tipo","value"), State("fp-rbruto","value"), State("fp-irrf","value"),
          State("fp-prev","value"), State("fp-pensao","value"), State("fp-13","value"), prevent_initial_call=True)
def salvar_fonte(n, ano, cnpj, razao, tipo, rbruto, irrf, prev, pensao, dec13):
    if not n: return False
    payload = {
        "ano": ano, "cnpj": cnpj, "razao_social": razao, "tipo": tipo,
        "rend_bruto": parse_money(rbruto), "irrf": parse_money(irrf),
        "contrib_prev_oficial": parse_money(prev), "pensao_alimenticia": parse_money(pensao),
        "decimo_terceiro_bruto": parse_money(dec13), "meses_trabalhados": None
    }
    ir.upsert_row("pf_fontes_pagadoras", payload, key_fields=["ano","cnpj"])
    return True

@callback(Output("toast-pg","is_open"), Input("add-pg","n_clicks"),
          State("ano","value"), State("pg-codigo","value"), State("pg-doc","value"),
          State("pg-nome","value"), State("pg-valor","value"), State("pg-data","value"),
          State("pg-reembolso","value"), prevent_initial_call=True)
def salvar_pagamento(n, ano, codigo, doc, nome, valor, data, reembolso):
    if not n: return False
    payload = {
        "ano": ano, "codigo_pagamento": codigo, "doc_prestador": doc, "nome_prestador": nome,
        "valor": parse_money(valor), "data": data, "reembolso": int(reembolso or 0), "valor_reembolsado": 0.0
    }
    ir.upsert_row("pf_pagamentos", payload, key_fields=["ano","codigo_pagamento","doc_prestador","data"])
    return True

@callback(Output("toast-rv","is_open"), Input("add-rv","n_clicks"),
          State("ano","value"), State("rv-mes","value"),
          State("rv-lucro-comum","value"), State("rv-lucro-dt","value"), State("rv-irrf","value"),
          prevent_initial_call=True)
def salvar_rv(n, ano, mes, lc, ldt, irrf):
    if not n: return False
    payload = {
        "ano": ano, "mes": mes,
        "vendas_acoes_comum": 0.0,  # pode preencher depois
        "lucro_acoes_comum": parse_money(lc),
        "vendas_daytrade": 0.0, "lucro_daytrade": parse_money(ldt),
        "vendas_outros": 0.0, "lucro_outros": 0.0,
        "irrf_daytrade": parse_money(irrf), "irrf_outros": 0.0,
        "prejuizo_acum_anter": 0.0, "imposto_devido": 0.0, "darfs_6015_pagos": 0.0
    }
    ir.upsert_row("pf_rv_mensal", payload, key_fields=["ano","mes"])
    return True

@callback(Output("rv-auto-msg","children"), Input("rv-auto","n_clicks"), State("ano","value"), prevent_initial_call=True)
def rascunho_rv(n, ano):
    df = ir.consolidar_pf_bolsa_auto(int(ano))
    if df.empty:
        return "Sem trades para importar ou motor desativado."
    # aqui você pode gravar no banco se quiser
    for _, row in df.iterrows():
        ir.upsert_row("pf_rv_mensal", row.to_dict(), key_fields=["ano","mes"])
    return f"Importado rascunho de {len(df)} mês(es) a partir de trades."

@callback(Output("toast-bd","is_open"), Input("add-bd","n_clicks"),
          State("ano","value"), State("bd-codigo","value"), State("bd-doc","value"),
          State("bd-discr","value"), State("bd-aquis","value"), State("bd-sit-ant","value"), State("bd-sit-ano","value"),
          prevent_initial_call=True)
def salvar_bd(n, ano, cod, doc, discr, aquis, s_ant, s_ano):
    if not n: return False
    grupo, codigo = cod.split("-")
    texto = discr or ir.texto_bem_direito({"grupo":int(grupo),"codigo":int(codigo),"doc_relacionado":doc,"perc_part":100,"data_aquisicao":aquis})
    payload = {
        "ano": ano, "grupo": int(grupo), "codigo": int(codigo), "discriminacao": texto,
        "doc_relacionado": doc, "localizacao": "BR", "perc_part": 100.0,
        "data_aquisicao": aquis, "situacao_ano_ant": parse_money(s_ant), "situacao_ano": parse_money(s_ano)
    }
    ir.upsert_row("pf_bens_direitos", payload, key_fields=["ano","grupo","codigo","discriminacao"])
    return True

# ----- Resumo inteligente (demonstração simples; dá pra ligar no seu motor de IR) -----
@callback(Output("resumo-opcao","children"), Output("resumo-darfs","children"), Output("resumo-alertas","children"),
          Input("ano","value"))
def resumo(ano):
    # cálculo simplificado: pega fontes pagadoras e pagamentos dedutíveis desse ano
    f = db.load_table("pf_fontes_pagadoras")
    p = db.load_table("pf_pagamentos")
    f = f[f["ano"] == ano] if "ano" in f.columns else f.iloc[0:0]
    p = p[p["ano"] == ano] if "ano" in p.columns else p.iloc[0:0]
    rend = float(f["rend_bruto"].sum()) if "rend_bruto" in f else 0.0
    irrf = float(f["irrf"].sum()) if "irrf" in f else 0.0
    dedu = float(p["valor"].sum()) if "valor" in p else 0.0

    # Modelo simplista: completo vs 20% simplificado (limite 16.754,34)
    desconto_simpl = min(rend*0.20, 16754.34)
    base_completo = max(0.0, rend - dedu)
    base_simplif = max(0.0, rend - desconto_simpl)
    # alíquota marginal simples (apenas indicativa)
    def faixa(base):
        if base <= 22859.20: return 0.0
        elif base <= 33919.80: return 0.075
        elif base <= 45012.60: return 0.15
        elif base <= 55976.16: return 0.225
        return 0.275
    imp_comp = base_completo * faixa(base_completo) - irrf
    imp_simp = base_simplif * faixa(base_simplif) - irrf
    recomendado = "Modelo Completo" if imp_comp < imp_simp else "Modelo Simplificado"

    item_darf = html.Li("Se houver lucro tributável em Bolsa no mês: emitir DARF 6015 até o último dia útil do mês seguinte.")
    alertas = dbc.Alert([
        html.Div(f"Rendimentos brutos: R$ {fmt(rend)} | Deduções informadas: R$ {fmt(dedu)}"),
        html.Div(f"IRRF já retido: R$ {fmt(irrf)}"),
        html.Div(f"Sugestão: {recomendado} (estimativa).")
    ], color="warning", className="mb-2")

    return recomendado, [item_darf], alertas

# ---------- Utils ----------
def parse_money(txt):
    if not txt: return 0.0
    s = str(txt).replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0

def fmt(v):
    return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X",".")
