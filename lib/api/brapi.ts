// API gratuita para cotações de ações brasileiras
// https://brapi.dev - sem necessidade de API key para uso básico

const BRAPI_BASE_URL = "https://brapi.dev/api"

export interface BrapiQuote {
  symbol: string
  shortName: string
  longName: string
  currency: string
  regularMarketPrice: number
  regularMarketDayHigh: number
  regularMarketDayLow: number
  regularMarketChange: number
  regularMarketChangePercent: number
  regularMarketTime: string
  regularMarketOpen: number
  regularMarketVolume: number
  regularMarketPreviousClose: number
  logourl?: string
}

export interface BrapiResponse {
  results: BrapiQuote[]
  requestedAt: string
  took: string
}

// Buscar cotação de um ou mais ativos
export async function getCotacoes(tickers: string[]): Promise<BrapiQuote[]> {
  if (tickers.length === 0) return []

  try {
    const tickerList = tickers.join(",")
    const response = await fetch(
      `${BRAPI_BASE_URL}/quote/${tickerList}?fundamental=false`,
      { next: { revalidate: 300 } }, // Cache por 5 minutos
    )

    if (!response.ok) {
      console.error("[v0] Brapi API error:", response.status)
      return []
    }

    const data: BrapiResponse = await response.json()
    return data.results || []
  } catch (error) {
    console.error("[v0] Error fetching quotes:", error)
    return []
  }
}

// Buscar cotação de um único ativo
export async function getCotacao(ticker: string): Promise<BrapiQuote | null> {
  const quotes = await getCotacoes([ticker])
  return quotes[0] || null
}

// Buscar lista de ativos disponíveis
export async function searchAtivos(query: string): Promise<{ symbol: string; name: string }[]> {
  try {
    const response = await fetch(
      `${BRAPI_BASE_URL}/available?search=${encodeURIComponent(query)}`,
      { next: { revalidate: 3600 } }, // Cache por 1 hora
    )

    if (!response.ok) return []

    const data = await response.json()
    return data.stocks?.slice(0, 20) || []
  } catch (error) {
    console.error("[v0] Error searching stocks:", error)
    return []
  }
}

// Tipos de ativos
export const TIPOS_RENDA_VARIAVEL = {
  acao: { label: "Ação", color: "#3b82f6" },
  fii: { label: "FII", color: "#10b981" },
  etf: { label: "ETF", color: "#8b5cf6" },
  bdr: { label: "BDR", color: "#f59e0b" },
} as const

export const TIPOS_RENDA_FIXA = {
  cdb: { label: "CDB", color: "#3b82f6" },
  lci: { label: "LCI", color: "#10b981" },
  lca: { label: "LCA", color: "#22c55e" },
  tesouro_selic: { label: "Tesouro Selic", color: "#f59e0b" },
  tesouro_ipca: { label: "Tesouro IPCA+", color: "#ef4444" },
  tesouro_prefixado: { label: "Tesouro Prefixado", color: "#8b5cf6" },
  debenture: { label: "Debênture", color: "#ec4899" },
  cri: { label: "CRI", color: "#06b6d4" },
  cra: { label: "CRA", color: "#14b8a6" },
  poupanca: { label: "Poupança", color: "#6b7280" },
} as const

export const INDEXADORES = {
  cdi: { label: "CDI", symbol: "%" },
  ipca: { label: "IPCA+", symbol: "% a.a." },
  selic: { label: "Selic", symbol: "%" },
  prefixado: { label: "Prefixado", symbol: "% a.a." },
  poupanca: { label: "Poupança", symbol: "" },
} as const

export const SETORES = [
  "Financeiro",
  "Energia Elétrica",
  "Saneamento",
  "Varejo",
  "Tecnologia",
  "Saúde",
  "Construção Civil",
  "Telecomunicações",
  "Petróleo e Gás",
  "Mineração",
  "Alimentos e Bebidas",
  "Papel e Celulose",
  "Siderurgia",
  "Transporte",
  "Imobiliário",
  "Agronegócio",
  "Outros",
] as const
