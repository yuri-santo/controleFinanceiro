import { createClient } from "@/lib/supabase/server"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { BarChart3, TrendingUp, TrendingDown, Wallet, PiggyBank, CreditCard, Target } from "lucide-react"
import { formatCurrency } from "@/lib/utils/currency"
import { formatMonthYear } from "@/lib/utils/date"
import type { Despesa, Receita, Categoria, RendaVariavel, RendaFixa } from "@/lib/types"
import { MonthlyChart } from "@/components/reports/monthly-chart"
import { CategoryBreakdown } from "@/components/reports/category-breakdown"
import { ExportButton } from "@/components/reports/export-button"
import { PeriodSelector } from "@/components/reports/period-selector"
import { FinancialHealthChart } from "@/components/reports/financial-health-chart"
import { InvestmentsOverview } from "@/components/reports/investments-overview"
import { GoalsProgress } from "@/components/reports/goals-progress"
import { CashFlowChart } from "@/components/reports/cashflow-chart"
import { getCotacoes } from "@/lib/api/brapi"

export default async function RelatoriosPage({
  searchParams,
}: {
  searchParams: Promise<{ mes?: string; ano?: string }>
}) {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) return null

  const params = await searchParams
  const now = new Date()
  const mes = params.mes ? Number.parseInt(params.mes) : now.getMonth() + 1
  const ano = params.ano ? Number.parseInt(params.ano) : now.getFullYear()

  // Get date range for selected month
  const startDate = new Date(ano, mes - 1, 1)
  const endDate = new Date(ano, mes, 0)
  const start = startDate.toISOString().split("T")[0]
  const end = endDate.toISOString().split("T")[0]

  // Get data for the last 6 months for the chart
  const sixMonthsAgo = new Date(ano, mes - 6, 1)
  const chartStart = sixMonthsAgo.toISOString().split("T")[0]

  const [
    despesasRes,
    receitasRes,
    categoriasRes,
    despesas6mRes,
    receitas6mRes,
    cartoesRes,
    rendaVariavelRes,
    rendaFixaRes,
    objetivosRes,
    caixinhasRes,
  ] = await Promise.all([
    supabase
      .from("despesas")
      .select("*, categoria:categorias(*)")
      .eq("user_id", user.id)
      .gte("data", start)
      .lte("data", end)
      .order("data", { ascending: false }),
    supabase
      .from("receitas")
      .select("*")
      .eq("user_id", user.id)
      .gte("data", start)
      .lte("data", end)
      .order("data", { ascending: false }),
    supabase.from("categorias").select("*").eq("user_id", user.id),
    supabase.from("despesas").select("*").eq("user_id", user.id).gte("data", chartStart).lte("data", end),
    supabase.from("receitas").select("*").eq("user_id", user.id).gte("data", chartStart).lte("data", end),
    supabase.from("cartoes").select("*").eq("user_id", user.id),
    supabase.from("renda_variavel").select("*").eq("user_id", user.id),
    supabase.from("renda_fixa").select("*").eq("user_id", user.id),
    supabase.from("objetivos").select("*").eq("user_id", user.id),
    supabase.from("caixinhas").select("*").eq("user_id", user.id),
  ])

  const despesas = (despesasRes.data || []) as Despesa[]
  const receitas = (receitasRes.data || []) as Receita[]
  const categorias = (categoriasRes.data || []) as Categoria[]
  const despesas6m = (despesas6mRes.data || []) as Despesa[]
  const receitas6m = (receitas6mRes.data || []) as Receita[]
  const cartoes = cartoesRes.data || []
  const rendaVariavel = (rendaVariavelRes.data || []) as RendaVariavel[]
  const rendaFixa = (rendaFixaRes.data || []) as RendaFixa[]
  const objetivos = objetivosRes.data || []
  const caixinhas = caixinhasRes.data || []

  // Buscar cotações
  const tickers = rendaVariavel.map((a) => a.ticker)
  const cotacoes = await getCotacoes(tickers)
  const cotacoesMap = new Map(cotacoes.map((c) => [c.symbol, c]))

  // Calcular valores de investimentos
  const totalRendaVariavel = rendaVariavel.reduce((sum, a) => {
    const cotacao = cotacoesMap.get(a.ticker)
    return sum + a.quantidade * (cotacao?.regularMarketPrice || a.preco_medio)
  }, 0)
  const totalRendaFixa = rendaFixa.reduce((sum, inv) => sum + inv.valor_atual, 0)
  const totalCaixinhas = caixinhas.reduce((sum, c) => sum + (c.saldo || 0), 0)
  const totalObjetivos = objetivos.reduce((sum, o) => sum + (o.valor_atual || 0), 0)

  const totalDespesas = despesas.reduce((sum, d) => sum + d.valor, 0)
  const totalReceitas = receitas.reduce((sum, r) => sum + r.valor, 0)
  const saldo = totalReceitas - totalDespesas
  const economia = totalReceitas > 0 ? ((totalReceitas - totalDespesas) / totalReceitas) * 100 : 0

  // Patrimônio total
  const patrimonioTotal = totalRendaVariavel + totalRendaFixa + totalCaixinhas + totalObjetivos

  // Total de limites de cartões
  const totalLimiteCartoes = cartoes.reduce((sum, c) => sum + (c.limite_total || 0), 0)

  // Process monthly data for chart
  const monthlyData = []
  for (let i = 5; i >= 0; i--) {
    const monthDate = new Date(ano, mes - 1 - i, 1)
    const monthStart = monthDate.toISOString().split("T")[0]
    const monthEnd = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0).toISOString().split("T")[0]

    const monthDespesas = despesas6m
      .filter((d) => d.data >= monthStart && d.data <= monthEnd)
      .reduce((sum, d) => sum + d.valor, 0)

    const monthReceitas = receitas6m
      .filter((r) => r.data >= monthStart && r.data <= monthEnd)
      .reduce((sum, r) => sum + r.valor, 0)

    monthlyData.push({
      month: monthDate.toLocaleDateString("pt-BR", { month: "short" }),
      despesas: monthDespesas,
      receitas: monthReceitas,
    })
  }

  // Dados de saúde financeira
  const healthData = {
    economia,
    despesasFixas: despesas.filter((d) => d.recorrente).reduce((sum, d) => sum + d.valor, 0),
    despesasVariaveis: despesas.filter((d) => !d.recorrente).reduce((sum, d) => sum + d.valor, 0),
    investimentos: totalRendaVariavel + totalRendaFixa,
    reserva: totalCaixinhas + totalObjetivos,
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold neon-text">Relatorios</h1>
          <p className="text-muted-foreground">{formatMonthYear(startDate)}</p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <PeriodSelector mes={mes} ano={ano} />
          <ExportButton despesas={despesas} receitas={receitas} categorias={categorias} mes={mes} ano={ano} />
        </div>
      </div>

      {/* Cards principais com animação */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="card-3d glass-card overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-transparent group-hover:from-emerald-500/20 transition-all" />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Receitas</CardTitle>
            <TrendingUp className="h-5 w-5 text-emerald-400" />
          </CardHeader>
          <CardContent className="relative">
            <div className="text-2xl font-bold text-emerald-400">{formatCurrency(totalReceitas)}</div>
            <p className="text-sm text-muted-foreground">{receitas.length} transacoes</p>
          </CardContent>
        </Card>

        <Card className="card-3d glass-card overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-red-500/10 to-transparent group-hover:from-red-500/20 transition-all" />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Despesas</CardTitle>
            <TrendingDown className="h-5 w-5 text-red-400" />
          </CardHeader>
          <CardContent className="relative">
            <div className="text-2xl font-bold text-red-400">{formatCurrency(totalDespesas)}</div>
            <p className="text-sm text-muted-foreground">{despesas.length} transacoes</p>
          </CardContent>
        </Card>

        <Card className="card-3d glass-card overflow-hidden group">
          <div
            className={`absolute inset-0 bg-gradient-to-br ${saldo >= 0 ? "from-cyan-500/10 group-hover:from-cyan-500/20" : "from-amber-500/10 group-hover:from-amber-500/20"} to-transparent transition-all`}
          />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Saldo do Mes</CardTitle>
            <BarChart3 className={`h-5 w-5 ${saldo >= 0 ? "text-cyan-400" : "text-amber-400"}`} />
          </CardHeader>
          <CardContent className="relative">
            <div className={`text-2xl font-bold ${saldo >= 0 ? "text-cyan-400" : "text-amber-400"}`}>
              {saldo >= 0 ? "+" : ""}
              {formatCurrency(saldo)}
            </div>
            <p className="text-sm text-muted-foreground">{saldo >= 0 ? "Saldo positivo" : "Saldo negativo"}</p>
          </CardContent>
        </Card>

        <Card className="card-3d glass-card overflow-hidden group">
          <div
            className={`absolute inset-0 bg-gradient-to-br ${economia >= 20 ? "from-emerald-500/10 group-hover:from-emerald-500/20" : "from-amber-500/10 group-hover:from-amber-500/20"} to-transparent transition-all`}
          />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Taxa de Economia</CardTitle>
            <PiggyBank className={`h-5 w-5 ${economia >= 20 ? "text-emerald-400" : "text-amber-400"}`} />
          </CardHeader>
          <CardContent className="relative">
            <div className={`text-2xl font-bold ${economia >= 20 ? "text-emerald-400" : "text-amber-400"}`}>
              {economia.toFixed(1)}%
            </div>
            <p className="text-sm text-muted-foreground">{economia >= 20 ? "Otimo!" : "Meta: 20%"}</p>
          </CardContent>
        </Card>
      </div>

      {/* Patrimônio */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="card-3d glass-card overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent" />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Patrimonio Total</CardTitle>
            <Wallet className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent className="relative">
            <div className="text-2xl font-bold neon-text">{formatCurrency(patrimonioTotal)}</div>
            <p className="text-sm text-muted-foreground">Investimentos + Reservas</p>
          </CardContent>
        </Card>

        <Card className="card-3d glass-card overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent" />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Investimentos</CardTitle>
            <TrendingUp className="h-5 w-5 text-blue-400" />
          </CardHeader>
          <CardContent className="relative">
            <div className="text-2xl font-bold">{formatCurrency(totalRendaVariavel + totalRendaFixa)}</div>
            <p className="text-sm text-muted-foreground">RV + RF</p>
          </CardContent>
        </Card>

        <Card className="card-3d glass-card overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-transparent" />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Limite Cartoes</CardTitle>
            <CreditCard className="h-5 w-5 text-purple-400" />
          </CardHeader>
          <CardContent className="relative">
            <div className="text-2xl font-bold">{formatCurrency(totalLimiteCartoes)}</div>
            <p className="text-sm text-muted-foreground">{cartoes.length} cartoes</p>
          </CardContent>
        </Card>

        <Card className="card-3d glass-card overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-amber-500/10 to-transparent" />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Objetivos</CardTitle>
            <Target className="h-5 w-5 text-amber-400" />
          </CardHeader>
          <CardContent className="relative">
            <div className="text-2xl font-bold">{formatCurrency(totalObjetivos)}</div>
            <p className="text-sm text-muted-foreground">{objetivos.length} objetivos</p>
          </CardContent>
        </Card>
      </div>

      {/* Gráficos principais */}
      <div className="grid gap-6 lg:grid-cols-2">
        <MonthlyChart data={monthlyData} />
        <CategoryBreakdown despesas={despesas} categorias={categorias} />
      </div>

      {/* Gráficos adicionais */}
      <div className="grid gap-6 lg:grid-cols-2">
        <FinancialHealthChart data={healthData} totalReceitas={totalReceitas} />
        <CashFlowChart monthlyData={monthlyData} />
      </div>

      {/* Resumo de investimentos e objetivos */}
      <div className="grid gap-6 lg:grid-cols-2">
        <InvestmentsOverview
          rendaVariavel={totalRendaVariavel}
          rendaFixa={totalRendaFixa}
          total={totalRendaVariavel + totalRendaFixa}
        />
        <GoalsProgress objetivos={objetivos} />
      </div>
    </div>
  )
}
