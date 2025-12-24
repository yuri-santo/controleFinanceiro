import { createClient } from "@/lib/supabase/server"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp, TrendingDown, DollarSign, BarChart3, RefreshCw } from "lucide-react"
import { formatCurrency, formatPercent } from "@/lib/utils/currency"
import type { RendaVariavel } from "@/lib/types"
import { getCotacoes, TIPOS_RENDA_VARIAVEL } from "@/lib/api/brapi"
import { RendaVariavelList } from "@/components/investments/renda-variavel-list"
import { AddRendaVariavelDialog } from "@/components/investments/add-renda-variavel-dialog"
import { PortfolioChart } from "@/components/investments/portfolio-chart"
import { VariacaoChart } from "@/components/investments/variacao-chart"

export default async function RendaVariavelPage() {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) return null

  const { data: ativos } = await supabase
    .from("renda_variavel")
    .select("*")
    .eq("user_id", user.id)
    .order("ticker", { ascending: true })

  const rendaVariavel = (ativos || []) as RendaVariavel[]

  // Buscar cotações em tempo real
  const tickers = rendaVariavel.map((a) => a.ticker)
  const cotacoes = await getCotacoes(tickers)
  const cotacoesMap = new Map(cotacoes.map((c) => [c.symbol, c]))

  // Calcular valores atuais
  const ativosComCotacao = rendaVariavel.map((ativo) => {
    const cotacao = cotacoesMap.get(ativo.ticker)
    const cotacaoAtual = cotacao?.regularMarketPrice || ativo.preco_medio
    const valorInvestido = ativo.quantidade * ativo.preco_medio
    const valorAtual = ativo.quantidade * cotacaoAtual
    const lucroPrejuizo = valorAtual - valorInvestido
    const lucroPrejuizoPercent = valorInvestido > 0 ? (lucroPrejuizo / valorInvestido) * 100 : 0

    return {
      ...ativo,
      cotacao_atual: cotacaoAtual,
      variacao: cotacao?.regularMarketChangePercent || 0,
      valor_atual: valorAtual,
      lucro_prejuizo: lucroPrejuizo,
      lucro_prejuizo_percent: lucroPrejuizoPercent,
    }
  })

  // Totais
  const totalInvestido = ativosComCotacao.reduce((sum, a) => sum + a.quantidade * a.preco_medio, 0)
  const totalAtual = ativosComCotacao.reduce((sum, a) => sum + (a.valor_atual || 0), 0)
  const totalLucroPrejuizo = totalAtual - totalInvestido
  const totalLucroPrejuizoPercent = totalInvestido > 0 ? (totalLucroPrejuizo / totalInvestido) * 100 : 0

  // Agrupar por tipo para gráfico
  const porTipo = ativosComCotacao.reduce(
    (acc, a) => {
      const tipo = a.tipo
      if (!acc[tipo]) acc[tipo] = 0
      acc[tipo] += a.valor_atual || 0
      return acc
    },
    {} as Record<string, number>,
  )

  const chartData = Object.entries(porTipo).map(([tipo, valor]) => ({
    name: TIPOS_RENDA_VARIAVEL[tipo as keyof typeof TIPOS_RENDA_VARIAVEL]?.label || tipo,
    value: valor,
    color: TIPOS_RENDA_VARIAVEL[tipo as keyof typeof TIPOS_RENDA_VARIAVEL]?.color || "#6b7280",
  }))

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold neon-text">Renda Variavel</h1>
          <p className="text-muted-foreground">Acoes, FIIs, ETFs e BDRs</p>
        </div>
        <div className="flex gap-2">
          <AddRendaVariavelDialog />
        </div>
      </div>

      {/* Cards de resumo com efeito glass */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="card-3d glass-card overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent" />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Investido</CardTitle>
            <DollarSign className="h-5 w-5 text-blue-400" />
          </CardHeader>
          <CardContent className="relative">
            <div className="text-2xl font-bold">{formatCurrency(totalInvestido)}</div>
            <p className="text-sm text-muted-foreground">{rendaVariavel.length} ativos</p>
          </CardContent>
        </Card>

        <Card className="card-3d glass-card overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/10 to-transparent" />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Valor Atual</CardTitle>
            <BarChart3 className="h-5 w-5 text-cyan-400" />
          </CardHeader>
          <CardContent className="relative">
            <div className="text-2xl font-bold">{formatCurrency(totalAtual)}</div>
            <p className="text-sm text-muted-foreground">Cotacao em tempo real</p>
          </CardContent>
        </Card>

        <Card className="card-3d glass-card overflow-hidden">
          <div
            className={`absolute inset-0 bg-gradient-to-br ${totalLucroPrejuizo >= 0 ? "from-emerald-500/10" : "from-red-500/10"} to-transparent`}
          />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Lucro/Prejuizo</CardTitle>
            {totalLucroPrejuizo >= 0 ? (
              <TrendingUp className="h-5 w-5 text-emerald-400" />
            ) : (
              <TrendingDown className="h-5 w-5 text-red-400" />
            )}
          </CardHeader>
          <CardContent className="relative">
            <div className={`text-2xl font-bold ${totalLucroPrejuizo >= 0 ? "text-emerald-400" : "text-red-400"}`}>
              {totalLucroPrejuizo >= 0 ? "+" : ""}
              {formatCurrency(totalLucroPrejuizo)}
            </div>
            <p className={`text-sm ${totalLucroPrejuizo >= 0 ? "text-emerald-400/70" : "text-red-400/70"}`}>
              {totalLucroPrejuizo >= 0 ? "+" : ""}
              {formatPercent(totalLucroPrejuizoPercent)}
            </p>
          </CardContent>
        </Card>

        <Card className="card-3d glass-card overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-transparent" />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Ultima Atualizacao</CardTitle>
            <RefreshCw className="h-5 w-5 text-purple-400" />
          </CardHeader>
          <CardContent className="relative">
            <div className="text-2xl font-bold">Agora</div>
            <p className="text-sm text-muted-foreground">Atualiza a cada 5min</p>
          </CardContent>
        </Card>
      </div>

      {/* Gráficos */}
      <div className="grid gap-6 lg:grid-cols-2">
        <PortfolioChart data={chartData} title="Distribuicao por Tipo" />
        <VariacaoChart ativos={ativosComCotacao} />
      </div>

      {/* Lista de ativos */}
      <RendaVariavelList ativos={ativosComCotacao} />
    </div>
  )
}
