# services/ir.py
import pandas as pd
from . import db

# --------- Catálogos úteis (PF) ----------
PAGAMENTOS_CODIGOS = {
    10: "Médicos no Brasil (CPF/CNPJ)",
    11: "Dentistas no Brasil (CPF/CNPJ)",
    21: "Hospitais/Laboratórios",
    26: "Planos de Saúde no Brasil (CNPJ)",
    36: "Previdência complementar (PGBL) - dedutível",
    37: "Previdência complementar empresarial"
}

BENS_DIREITOS_CATALOGO = {
    (3,1): "Ações (inclusive as listadas)",
    (4,2): "Títulos públicos/privados sujeitos à tributação (CDB, Tesouro, debêntures)",
    (4,3): "Títulos isentos (LCI, LCA, CRI, CRA, etc.)"
    # Ex.: VGBL pode variar de código a cada exercício; exibimos dinamicamente no front.
}

DARF_CODIGOS = {
    "bolsa_pf": "6015",
    "carne_leao": "0190",
    "irpf_quota": "0211",
    "irpj_presumido": "2089",
    "irpj_bolsa_presumido": "0231",
    "irpj_bolsa_real": "3317"
}

# --------- LOADS GENÉRICOS ----------
def load_table(name):
    return db.load_table(name)

def upsert_row(table, payload, key_fields=None):
    """
    key_fields: lista de campos que definem unicidade (ano+mes+cnpj etc.)
    Se existir, faz UPDATE; senão, INSERT.
    """
    df = db.load_table(table)
    if key_fields:
        mask = pd.Series([True] * len(df))
        for k in key_fields:
            mask = mask & (df[k] == payload.get(k))
        if df[mask].shape[0] > 0:
            row_id = int(df[mask].iloc[0]["id"])
            db.update_row(table, row_id, payload)
            return row_id
    return db.insert_row(table, payload)

# --------- TEXTOS “PRONTOS PARA DECLARAÇÃO” ----------
def texto_bem_direito(row):
    """Monta o campo 'Discriminação' para Bens e Direitos (modo leigo)."""
    base = BENS_DIREITOS_CATALOGO.get((int(row["grupo"]), int(row["codigo"])), "Bem/Aplicação financeira")
    doc = row.get("doc_relacionado") or ""
    perc = row.get("perc_part") or 100
    aquis = row.get("data_aquisicao") or ""
    return (f"{base}. Documento relacionado: {doc}. "
            f"Titularidade: {perc:.0f}%. Data de aquisição: {aquis}. "
            f"Informar situação em 31/12 do ano anterior e do ano-base. "
            f"Manter informes/corretoras como documentação de suporte.")

def resumo_darf_bolsa_pf(row):
    mes = int(row["mes"])
    devido = float(row.get("imposto_devido") or 0)
    irrf = float(row.get("irrf_daytrade") or 0) + float(row.get("irrf_outros") or 0)
    codigo = DARF_CODIGOS["bolsa_pf"]
    txt = (f"Mês {mes:02d}: Imposto devido R$ {devido:,.2f}. "
           f"IRRF a compensar R$ {irrf:,.2f}. Emitir DARF código {codigo} "
           f"no Sicalc até o último dia útil do mês seguinte.")
    return txt.replace(",", "X").replace(".", ",").replace("X", ".")

# --------- CONSOLIDAÇÕES (ganchos nos seus dados) ----------
def consolidar_pf_bolsa_auto(ano):
    """
    Opcional: pré-preenche pf_rv_mensal usando suas tabelas 'trades' e 'proventos'.
    Se não quiser ainda, pode ignorar. Depois a gente refina com XIRR/PM/Venda.
    """
    try:
        trades = db.load_trades()
    except Exception:
        return pd.DataFrame()
    if trades.empty:
        return pd.DataFrame()
    trades = trades[trades["Data"].dt.year == ano].copy()
    trades["mes"] = trades["Data"].dt.month

    # Simplificação: separa day trade vs comum por flag 'Tipo' (ex.: 'DT'/'C')
    def _signed_val(r):
        return r["Valor"] * (1 if r["Tipo"] in ("V", "VD") else -1)

    agg = trades.groupby("mes").agg(vendas=("Valor", "sum")).reset_index()
    # placeholders: lucros e IRRF devem vir do motor de apuração; aqui deixamos zeros
    agg["vendas_acoes_comum"] = agg["vendas"]
    agg["lucro_acoes_comum"] = 0.0
    agg["vendas_daytrade"] = 0.0
    agg["lucro_daytrade"] = 0.0
    agg["vendas_outros"] = 0.0
    agg["lucro_outros"] = 0.0
    agg["irrf_daytrade"] = 0.0
    agg["irrf_outros"] = 0.0
    agg["prejuizo_acum_anter"] = 0.0
    agg["imposto_devido"] = 0.0
    agg["darfs_6015_pagos"] = 0.0
    agg["ano"] = ano
    return agg[[
        "ano","mes","vendas_acoes_comum","lucro_acoes_comum","vendas_daytrade","lucro_daytrade",
        "vendas_outros","lucro_outros","irrf_daytrade","irrf_outros",
        "prejuizo_acum_anter","imposto_devido","darfs_6015_pagos"
    ]]
