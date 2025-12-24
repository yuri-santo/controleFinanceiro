import { createClient } from "@/lib/supabase/server"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp, TrendingDown, Wallet, BarChart3, Activity } from "lucide-react"
import { formatCurrency, formatPercent } from "@/lib/utils/currency"
import type { RendaVariavel, RendaFixa } from "@/lib/types"
import { getCotacoes, TIPOS_RENDA_VARIAVEL, TIPOS_RENDA_FIXA } from "@/lib/api/brapi"
import { PortfolioChart } from "@/components/investments/portfolio-chart"
import { PatrimonioChart } from "@/components/investments/patrimonio-chart"
import { AlocacaoRadar } from "@/components/investments/alocacao-radar"
import { PageAnimation } from "@/components/animations/page-animation"

export default async function CarteiraPage() {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) return null

  // Buscar todos os dados
  const [rendaVariavelRes, rendaFixaRes, caixinhasRes, objetivosRes] = await Promise.all([
    supabase.from("renda_variavel").select("*").eq("user_id", user.id),
    supabase.from("renda_fixa").select("*").eq("user_id", user.id),
    supabase.from("caixinhas").select("*").eq("user_id", user.id),
    supabase.from("objetivos").select("*").eq("user_id", user.id),
  ])

  const rendaVariavel = (rendaVariavelRes.data || []) as RendaVariavel[]
  const rendaFixa = (rendaFixaRes.data || []) as RendaFixa[]
  const caixinhas = caixinhasRes.data || []
  const objetivos = objetivosRes.data || []

  // Buscar cotações em tempo real
  const tickers = rendaVariavel.map((a) => a.ticker)
  const cotacoes = await getCotacoes(tickers)
  const cotacoesMap = new Map(cotacoes.map((c) => [c.symbol, c]))

  // Calcular valores de renda variável
  const rvComCotacao = rendaVariavel.map((ativo) => {
    const cotacao = cotacoesMap.get(ativo.ticker)
    const cotacaoAtual = cotacao?.regularMarketPrice || ativo.preco_medio
    return {
      ...ativo,
      cotacao_atual: cotacaoAtual,
      valor_atual: ativo.quantidade * cotacaoAtual,
    }
  })

  // Totais por classe
  const totalRendaVariavel = rvComCotacao.reduce((sum, a) => sum + (a.valor_atual || 0), 0)
  const totalRendaFixa = rendaFixa.reduce((sum, inv) => sum + inv.valor_atual, 0)
  const totalCaixinhas = caixinhas.reduce((sum, c) => sum + (c.saldo || 0), 0)
  const totalObjetivos = objetivos.reduce((sum, o) => sum + (o.valor_atual || 0), 0)

  const patrimonioTotal = totalRendaVariavel + totalRendaFixa + totalCaixinhas + totalObjetivos

  // Rentabilidade
  const investidoRV = rendaVariavel.reduce((sum, a) => sum + a.quantidade * a.preco_medio, 0)
  const investidoRF = rendaFixa.reduce((sum, inv) => sum + inv.valor_investido, 0)
  const totalInvestido = investidoRV + investidoRF
  const lucroTotal = totalRendaVariavel + totalRendaFixa - totalInvestido
  const rentabilidadeTotal = totalInvestido > 0 ? (lucroTotal / totalInvestido) * 100 : 0

  // Dados para gráficos
  const alocacaoData = [
    { name: "Renda Variável", value: totalRendaVariavel, color: "#3b82f6" },
    { name: "Renda Fixa", value: totalRendaFixa, color: "#10b981" },
    { name: "Caixinhas", value: totalCaixinhas, color: "#f59e0b" },
    { name: "Objetivos", value: totalObjetivos, color: "#8b5cf6" },
  ].filter((d) => d.value > 0)

  // Agrupar renda variável por tipo
  const rvPorTipo = rvComCotacao.reduce(
    (acc, a) => {
      if (!acc[a.tipo]) acc[a.tipo] = 0
      acc[a.tipo] += a.valor_atual || 0
      return acc
    },
    {} as Record<string, number>,
  )

  const rvChartData = Object.entries(rvPorTipo).map(([tipo, valor]) => ({
    name: TIPOS_RENDA_VARIAVEL[tipo as keyof typeof TIPOS_RENDA_VARIAVEL]?.label || tipo,
    value: valor,
    color: TIPOS_RENDA_VARIAVEL[tipo as keyof typeof TIPOS_RENDA_VARIAVEL]?.color || "#6b7280",
  }))

  // Agrupar renda fixa por tipo
  const rfPorTipo = rendaFixa.reduce(
    (acc, inv) => {
      if (!acc[inv.tipo]) acc[inv.tipo] = 0
      acc[inv.tipo] += inv.valor_atual
      return acc
    },
    {} as Record<string, number>,
  )

  const rfChartData = Object.entries(rfPorTipo).map(([tipo, valor]) => ({
    name: TIPOS_RENDA_FIXA[tipo as keyof typeof TIPOS_RENDA_FIXA]?.label || tipo,
    value: valor,
    color: TIPOS_RENDA_FIXA[tipo as keyof typeof TIPOS_RENDA_FIXA]?.color || "#6b7280",
  }))

  return (
    <div className="space-y-6">
      <PageAnimation type="investimentos" />

      <div>
        <h1 className="text-2xl font-bold neon-text">Minha Carteira</h1>
        <p className="text-muted-foreground">Visao consolidada de todos os investimentos</p>
      </div>

      {/* Cards principais */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="card-3d glass-card overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-transparent" />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Patrimonio Total</CardTitle>
            <Wallet className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent className="relative">
            <div className="text-3xl font-bold neon-text">{formatCurrency(patrimonioTotal)}</div>
            <p className="text-sm text-muted-foreground">
              {rendaVariavel.length + rendaFixa.length} investimentos ativos
            </p>
          </CardContent>
        </Card>

        <Card className="card-3d glass-card overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent" />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Renda Variavel</CardTitle>
            <Activity className="h-5 w-5 text-blue-400" />
          </CardHeader>
          <CardContent className="relative">
            <div className="text-2xl font-bold">{formatCurrency(totalRendaVariavel)}</div>
            <p className="text-sm text-muted-foreground">
              {patrimonioTotal > 0 ? ((totalRendaVariavel / patrimonioTotal) * 100).toFixed(1) : 0}% do patrimonio
            </p>
          </CardContent>
        </Card>

        <Card className="card-3d glass-card overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-transparent" />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Renda Fixa</CardTitle>
            <BarChart3 className="h-5 w-5 text-emerald-400" />
          </CardHeader>
          <CardContent className="relative">
            <div className="text-2xl font-bold">{formatCurrency(totalRendaFixa)}</div>
            <p className="text-sm text-muted-foreground">
              {patrimonioTotal > 0 ? ((totalRendaFixa / patrimonioTotal) * 100).toFixed(1) : 0}% do patrimonio
            </p>
          </CardContent>
        </Card>

        <Card className="card-3d glass-card overflow-hidden">
          <div
            className={`absolute inset-0 bg-gradient-to-br ${lucroTotal >= 0 ? "from-emerald-500/10" : "from-red-500/10"} to-transparent`}
          />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Rentabilidade</CardTitle>
            {lucroTotal >= 0 ? (
              <TrendingUp className="h-5 w-5 text-emerald-400" />
            ) : (
              <TrendingDown className="h-5 w-5 text-red-400" />
            )}
          </CardHeader>
          <CardContent className="relative">
            <div className={`text-2xl font-bold ${lucroTotal >= 0 ? "text-emerald-400" : "text-red-400"}`}>
              {lucroTotal >= 0 ? "+" : ""}
              {formatCurrency(lucroTotal)}
            </div>
            <p className={`text-sm ${lucroTotal >= 0 ? "text-emerald-400/70" : "text-red-400/70"}`}>
              {lucroTotal >= 0 ? "+" : ""}
              {formatPercent(rentabilidadeTotal)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Gráficos de alocação */}
      <div className="grid gap-6 lg:grid-cols-2">
        <PatrimonioChart data={alocacaoData} />
        <AlocacaoRadar
          rendaVariavel={totalRendaVariavel}
          rendaFixa={totalRendaFixa}
          caixinhas={totalCaixinhas}
          objetivos={totalObjetivos}
        />
      </div>

      {/* Detalhamento por classe */}
      <div className="grid gap-6 lg:grid-cols-2">
        <PortfolioChart data={rvChartData} title="Renda Variavel por Tipo" />
        <PortfolioChart data={rfChartData} title="Renda Fixa por Tipo" />
      </div>

      {/* Top ativos */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="card-3d glass-card overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent" />
          <CardHeader className="relative">
            <CardTitle className="text-lg neon-text-subtle">Top 5 Acoes</CardTitle>
          </CardHeader>
          <CardContent className="relative space-y-3">
            {rvComCotacao
              .sort((a, b) => (b.valor_atual || 0) - (a.valor_atual || 0))
              .slice(0, 5)
              .map((ativo, index) => (
                <div
                  key={ativo.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-background/30 border border-primary/10"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-xs font-bold text-primary">
                      {index + 1}
                    </span>
                    <div>
                      <p className="font-bold">{ativo.ticker}</p>
                      <p className="text-xs text-muted-foreground">{ativo.quantidade} cotas</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">{formatCurrency(ativo.valor_atual || 0)}</p>
                    <p className="text-xs text-muted-foreground">
                      {patrimonioTotal > 0 ? (((ativo.valor_atual || 0) / patrimonioTotal) * 100).toFixed(1) : 0}%
                    </p>
                  </div>
                </div>
              ))}
            {rvComCotacao.length === 0 && (
              <p className="text-center text-muted-foreground py-4">Nenhum ativo de renda variavel</p>
            )}
          </CardContent>
        </Card>

        <Card className="card-3d glass-card overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent" />
          <CardHeader className="relative">
            <CardTitle className="text-lg neon-text-subtle">Top 5 Renda Fixa</CardTitle>
          </CardHeader>
          <CardContent className="relative space-y-3">
            {rendaFixa
              .sort((a, b) => b.valor_atual - a.valor_atual)
              .slice(0, 5)
              .map((inv, index) => (
                <div
                  key={inv.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-background/30 border border-primary/10"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center text-xs font-bold text-emerald-400">
                      {index + 1}
                    </span>
                    <div>
                      <p className="font-bold">{inv.nome}</p>
                      <p className="text-xs text-muted-foreground">{inv.instituicao}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">{formatCurrency(inv.valor_atual)}</p>
                    <p className="text-xs text-emerald-400">
                      +{formatPercent(((inv.valor_atual - inv.valor_investido) / inv.valor_investido) * 100)}
                    </p>
                  </div>
                </div>
              ))}
            {rendaFixa.length === 0 && (
              <p className="text-center text-muted-foreground py-4">Nenhuma aplicacao de renda fixa</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
