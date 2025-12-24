import { createClient } from "@/lib/supabase/server"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp, DollarSign, Landmark, Calendar } from "lucide-react"
import { formatCurrency, formatPercent } from "@/lib/utils/currency"
import type { RendaFixa } from "@/lib/types"
import { TIPOS_RENDA_FIXA } from "@/lib/api/brapi"
import { RendaFixaList } from "@/components/investments/renda-fixa-list"
import { AddRendaFixaDialog } from "@/components/investments/add-renda-fixa-dialog"
import { PortfolioChart } from "@/components/investments/portfolio-chart"
import { RendimentoChart } from "@/components/investments/rendimento-chart"

function calcularDiasRestantes(dataVencimento: string | null): number | null {
  if (!dataVencimento) return null
  const hoje = new Date()
  const vencimento = new Date(dataVencimento)
  const diff = vencimento.getTime() - hoje.getTime()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

export default async function RendaFixaPage() {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) return null

  const { data: investimentos } = await supabase
    .from("renda_fixa")
    .select("*")
    .eq("user_id", user.id)
    .order("data_vencimento", { ascending: true })

  const rendaFixa = (investimentos || []).map((inv) => ({
    ...inv,
    rendimento: inv.valor_atual - inv.valor_investido,
    rendimento_percent:
      inv.valor_investido > 0 ? ((inv.valor_atual - inv.valor_investido) / inv.valor_investido) * 100 : 0,
    dias_restantes: calcularDiasRestantes(inv.data_vencimento),
  })) as RendaFixa[]

  // Totais
  const totalInvestido = rendaFixa.reduce((sum, inv) => sum + inv.valor_investido, 0)
  const totalAtual = rendaFixa.reduce((sum, inv) => sum + inv.valor_atual, 0)
  const totalRendimento = totalAtual - totalInvestido
  const totalRendimentoPercent = totalInvestido > 0 ? (totalRendimento / totalInvestido) * 100 : 0

  // Próximos vencimentos
  const proximosVencimentos = rendaFixa
    .filter((inv) => inv.dias_restantes !== null && inv.dias_restantes > 0)
    .sort((a, b) => (a.dias_restantes || 0) - (b.dias_restantes || 0))
    .slice(0, 3)

  // Agrupar por tipo para gráfico
  const porTipo = rendaFixa.reduce(
    (acc, inv) => {
      const tipo = inv.tipo
      if (!acc[tipo]) acc[tipo] = 0
      acc[tipo] += inv.valor_atual
      return acc
    },
    {} as Record<string, number>,
  )

  const chartData = Object.entries(porTipo).map(([tipo, valor]) => ({
    name: TIPOS_RENDA_FIXA[tipo as keyof typeof TIPOS_RENDA_FIXA]?.label || tipo,
    value: valor,
    color: TIPOS_RENDA_FIXA[tipo as keyof typeof TIPOS_RENDA_FIXA]?.color || "#6b7280",
  }))

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold neon-text">Renda Fixa</h1>
          <p className="text-muted-foreground">CDBs, LCIs, LCAs, Tesouro Direto e mais</p>
        </div>
        <div className="flex gap-2">
          <AddRendaFixaDialog />
        </div>
      </div>

      {/* Cards de resumo */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="card-3d glass-card overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent" />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Investido</CardTitle>
            <DollarSign className="h-5 w-5 text-blue-400" />
          </CardHeader>
          <CardContent className="relative">
            <div className="text-2xl font-bold">{formatCurrency(totalInvestido)}</div>
            <p className="text-sm text-muted-foreground">{rendaFixa.length} aplicacoes</p>
          </CardContent>
        </Card>

        <Card className="card-3d glass-card overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/10 to-transparent" />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Valor Atual</CardTitle>
            <Landmark className="h-5 w-5 text-cyan-400" />
          </CardHeader>
          <CardContent className="relative">
            <div className="text-2xl font-bold">{formatCurrency(totalAtual)}</div>
            <p className="text-sm text-muted-foreground">Atualizado manualmente</p>
          </CardContent>
        </Card>

        <Card className="card-3d glass-card overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-transparent" />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Rendimento Total</CardTitle>
            <TrendingUp className="h-5 w-5 text-emerald-400" />
          </CardHeader>
          <CardContent className="relative">
            <div className="text-2xl font-bold text-emerald-400">+{formatCurrency(totalRendimento)}</div>
            <p className="text-sm text-emerald-400/70">+{formatPercent(totalRendimentoPercent)}</p>
          </CardContent>
        </Card>

        <Card className="card-3d glass-card overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-amber-500/10 to-transparent" />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Prox. Vencimento</CardTitle>
            <Calendar className="h-5 w-5 text-amber-400" />
          </CardHeader>
          <CardContent className="relative">
            {proximosVencimentos.length > 0 ? (
              <>
                <div className="text-2xl font-bold">{proximosVencimentos[0].dias_restantes} dias</div>
                <p className="text-sm text-muted-foreground truncate">{proximosVencimentos[0].nome}</p>
              </>
            ) : (
              <>
                <div className="text-2xl font-bold">-</div>
                <p className="text-sm text-muted-foreground">Nenhum vencimento</p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Gráficos */}
      <div className="grid gap-6 lg:grid-cols-2">
        <PortfolioChart data={chartData} title="Distribuicao por Tipo" />
        <RendimentoChart investimentos={rendaFixa} />
      </div>

      {/* Lista de investimentos */}
      <RendaFixaList investimentos={rendaFixa} />
    </div>
  )
}
