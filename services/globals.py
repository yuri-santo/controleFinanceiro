import pandas as pd
import os
from datetime import datetime

# Estrutura para Receitas
if "dfReceitas.csv" in os.listdir():
    dfReceitas = pd.read_csv("dfReceitas.csv", index_col=0, parse_dates=True)
    dfReceitas["Data"] = pd.to_datetime(dfReceitas["Data"]).dt.date
else:
    receitas_structure = {
        'Valor': [],
        'Recebido': [],  # 1 para recebido, 0 para não recebido
        'Recorrente': [],  # 1 para recorrente, 0 para ocasional
        'Data': [],
        'Categoria': [],
        'Descrição': [],
    }
    dfReceitas = pd.DataFrame(receitas_structure)
    dfReceitas.to_csv("dfReceitas.csv")

# Estrutura para Despesas
if "dfDespesas.csv" in os.listdir():
    dfDespesas = pd.read_csv("dfDespesas.csv", index_col=0, parse_dates=True)
    dfDespesas["Data"] = pd.to_datetime(dfDespesas["Data"]).dt.date
else:
    despesas_structure = {
        'Valor': [],
        'Pago': [],  # 1 para pago, 0 para pendente
        'Fixo': [],  # 1 para fixo, 0 para variável
        'Data': [],
        'Categoria': [],
        'Descrição': [],
        'Parcelado': [],  # 1 para parcelado, 0 para à vista
        'QtdParcelas': [],
        'ParcelaAtual': []  # Número da parcela atual
    }
    dfDespesas = pd.DataFrame(despesas_structure)
    dfDespesas.to_csv("dfDespesas.csv")

# Estrutura para Investimentos
if "dfInvestimentos.csv" in os.listdir():
    dfInvestimentos = pd.read_csv("dfInvestimentos.csv", index_col=0, parse_dates=True)
    dfInvestimentos["Data"] = pd.to_datetime(dfInvestimentos["Data"]).dt.date
else:
    investimentos_structure = {
        'Valor': [],
        'Tipo': [],  # Aplicação, Resgate, Dividendos
        'Data': [],
        'Categoria': [],
        'Descrição': [],
        'Rentabilidade': [],  # % esperada de rentabilidade
        'Vencimento': [],  # Para investimentos com prazo
        'Liquidez': []  # Diária, D+30, etc.
    }
    dfInvestimentos = pd.DataFrame(investimentos_structure)
    dfInvestimentos.to_csv("dfInvestimentos.csv")

# Categorias
if "dfCatReceitas.csv" in os.listdir():
    dfCatReceitas = pd.read_csv("dfCatReceitas.csv")
    catReceitas = dfCatReceitas["Categoria"].tolist()
else:
    catReceitas = ["Salário", "Investimentos", "Comissão", "Freelance", "Outros"]
    pd.DataFrame({'Categoria': catReceitas}).to_csv("dfCatReceitas.csv")

if "dfCatDespesas.csv" in os.listdir():
    dfCatDespesas = pd.read_csv("dfCatDespesas.csv")
    catDespesas = dfCatDespesas["Categoria"].tolist()
else:
    catDespesas = ["Moradia", "Alimentação", "Transporte", "Lazer", "Saúde", "Educação", "Outros"]
    pd.DataFrame({'Categoria': catDespesas}).to_csv("dfCatDespesas.csv")

if "dfCatInvestimentos.csv" in os.listdir():
    dfCatInvestimentos = pd.read_csv("dfCatInvestimentos.csv")
    catInvestimentos = dfCatInvestimentos["Categoria"].tolist()
else:
    catInvestimentos = ["Ações", "FIIs", "Renda Fixa", "Tesouro Direto", "Criptomoedas", "Fundos"]
    pd.DataFrame({'Categoria': catInvestimentos}).to_csv("dfCatInvestimentos.csv")