import pandas as pd
import os

if ("dfDespesas.csv" in os.listdir()) and ("dfReceitas.csv" in os.listdir() and ("dfInvestimentos.csv" in os.listdir())):
    dfReceitas = pd.read_csv("dfReceitas.csv", index_col=0, parse_dates=True)
    dfReceitas["Data"] = pd.to_datetime(dfReceitas["Data"])
    dfReceitas["Data"] = dfReceitas["Data"].apply(lambda x: x.date())

    dfDespesas = pd.read_csv("dfDespesas.csv", index_col=0, parse_dates=True)
    dfDespesas["Data"] = pd.to_datetime(dfDespesas["Data"])
    dfDespesas["Data"] = dfDespesas["Data"].apply(lambda x: x.date())
    
    dfInvestimentos = pd.read_csv("dfInvestimentos.csv", index_col=0, parse_dates=True)
    dfInvestimentos["Data"] = pd.to_datetime(dfInvestimentos["Data"])
    dfInvestimentos["Data"] = dfInvestimentos["Data"].apply(lambda x: x.date())

else:
    dataStructure = {'Valor':[],
        'Efetuado':[],
        'Fixo':[],
        'Data':[],
        'Categoria':[],
        'Descrição':[],}
    
    dfReceitas = pd.DataFrame(dataStructure)
    dfDespesas = pd.DataFrame(dataStructure)
    dfInvestimentos = pd.DataFrame(dataStructure)

    dfDespesas.to_csv("dfDespesas.csv")
    dfReceitas.to_csv("dfReceitas.csv")
    dfInvestimentos.to_csv("dfInvestimentos.csv")

if ("dfCatDespesas.csv" in os.listdir()) and ("dfCatReceitas.csv" in os.listdir() and ("dfCatInvestimentos.csv" in os.listdir())):
    dfCatDespesas = pd.read_csv("dfCatDespesas.csv", parse_dates=True)
    dfCatReceitas = pd.read_csv("dfCatReceitas.csv", parse_dates=True)
    dfCatInvestimentos = pd.read_csv("dfCatInvestimentos.csv", parse_dates=True)
    catReceitas = dfCatReceitas["Categoria"].tolist()
    catDespesas = dfCatDespesas["Categoria"].tolist()
    catInvestimentos = dfCatInvestimentos["Categoria"].tolist()

else:
    catReceitas = {'Categoria':["Salário", "Investimentos", "Comissão"]}
    catDespesas = {'Categoria':["Alimentação", "Estudo", "Lazer", "Saude", "Conbustivel", "Manutenção"]}
    catInvestimentos = {'Categoria':["Ações", "Renda Fixa", "Fundo Imobiliario"]}

    dfCatReceitas = pd.DataFrame(catReceitas, columns=['Categoria'])
    dfCatDespesas = pd.DataFrame(catDespesas)
    dfCatInvestimentos = pd.DataFrame(catInvestimentos)

    dfCatDespesas.to_csv("dfCatDespesas.csv")
    dfCatReceitas.to_csv("dfCatReceitas.csv")
    dfCatInvestimentos.to_csv("dfCatInvestimentos.csv")