export interface Profile {
  id: string
  email: string
  nome: string
  tipo_usuario: "PF" | "PJ"
  created_at: string
}

export interface Categoria {
  id: string
  user_id: string
  nome: string
  tipo: "despesa" | "receita"
  cor: string
  icone: string
  created_at: string
}

export interface Despesa {
  id: string
  user_id: string
  valor: number
  categoria_id: string | null
  subcategoria: string | null
  data: string
  descricao: string | null
  forma_pagamento: "cartao" | "debito" | "pix" | "dinheiro" | null
  cartao_id: string | null
  recorrente: boolean
  parcelado: boolean
  total_parcelas: number
  parcela_atual: number
  observacoes: string | null
  created_at: string
  categoria?: Categoria
  cartao?: Cartao
}

export interface Receita {
  id: string
  user_id: string
  valor: number
  fonte: string
  data: string
  descricao: string | null
  recorrente: boolean
  created_at: string
}

export interface Cartao {
  id: string
  user_id: string
  nome: string
  bandeira: string | null
  limite_total: number
  fechamento_fatura: number
  vencimento: number
  cor: string
  created_at: string
}

export interface Objetivo {
  id: string
  user_id: string
  nome: string
  valor_total: number
  valor_atual: number
  prazo: string | null
  tipo: "sonho" | "reserva" | "projeto" | "emergencia"
  cor: string
  icone: string
  created_at: string
}

export interface Caixinha {
  id: string
  user_id: string
  nome: string
  saldo: number
  objetivo_id: string | null
  cor: string
  icone: string
  created_at: string
  objetivo?: Objetivo
}

export interface Orcamento {
  id: string
  user_id: string
  categoria_id: string
  valor_limite: number
  mes: number
  ano: number
  created_at: string
  categoria?: Categoria
}

export interface TransferenciaCaixinha {
  id: string
  user_id: string
  caixinha_origem_id: string | null
  caixinha_destino_id: string | null
  valor: number
  data: string
  observacao: string | null
  created_at: string
}

export interface RendaVariavel {
  id: string
  user_id: string
  ticker: string
  tipo: "acao" | "fii" | "etf" | "bdr"
  quantidade: number
  preco_medio: number
  data_compra: string
  corretora: string | null
  setor: string | null
  observacoes: string | null
  created_at: string
  // Dados em tempo real (não persistidos)
  cotacao_atual?: number
  variacao?: number
  valor_atual?: number
  lucro_prejuizo?: number
  lucro_prejuizo_percent?: number
}

export interface RendaFixa {
  id: string
  user_id: string
  nome: string
  tipo:
    | "cdb"
    | "lci"
    | "lca"
    | "tesouro_selic"
    | "tesouro_ipca"
    | "tesouro_prefixado"
    | "debenture"
    | "cri"
    | "cra"
    | "poupanca"
  instituicao: string
  valor_investido: number
  valor_atual: number
  taxa: number
  indexador: "cdi" | "ipca" | "selic" | "prefixado" | "poupanca" | null
  data_aplicacao: string
  data_vencimento: string | null
  liquidez: "diaria" | "vencimento" | "carencia" | null
  dias_carencia: number | null
  observacoes: string | null
  created_at: string
  // Calculados
  rendimento?: number
  rendimento_percent?: number
  dias_restantes?: number
}

export interface CotacaoHistorico {
  id: string
  ticker: string
  preco: number
  variacao: number | null
  data: string
  created_at: string
}

export interface TransacaoInvestimento {
  id: string
  user_id: string
  investimento_id: string
  tipo_investimento: "renda_variavel" | "renda_fixa"
  tipo_operacao: "compra" | "venda" | "dividendo" | "jcp" | "rendimento" | "amortizacao"
  quantidade: number | null
  valor: number
  data: string
  observacoes: string | null
  created_at: string
}

export interface Provento {
  id: string
  user_id: string
  ticker: string
  tipo: "dividendo" | "jcp" | "rendimento" | "amortizacao"
  valor: number
  data_com: string | null
  data_pagamento: string
  quantidade_base: number | null
  observacoes: string | null
  created_at: string
}

export interface CotacaoAPI {
  symbol: string
  shortName: string
  longName: string
  currency: string
  regularMarketPrice: number
  regularMarketDayHigh: number
  regularMarketDayLow: number
  regularMarketDayRange: string
  regularMarketChange: number
  regularMarketChangePercent: number
  regularMarketTime: string
  regularMarketOpen: number
  regularMarketVolume: number
  regularMarketPreviousClose: number
  logourl?: string
}
