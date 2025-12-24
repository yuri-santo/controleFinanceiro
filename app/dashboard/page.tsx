import { createClient } from "@/lib/supabase/server"
import { StatsCard } from "@/components/dashboard/stats-card"
import { RecentTransactions } from "@/components/dashboard/recent-transactions"
import { ExpenseChart } from "@/components/dashboard/expense-chart"
import { BudgetProgress } from "@/components/dashboard/budget-progress"
import { formatCurrency } from "@/lib/utils/currency"
import { getCurrentMonthRange } from "@/lib/utils/date"
import { ArrowDownCircle, ArrowUpCircle, Wallet, TrendingUp, Zap } from "lucide-react"
import type { Despesa, Receita, Categoria, Orcamento } from "@/lib/types"
import { PageAnimation } from "@/components/animations/page-animation"

export default async function DashboardPage() {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) return null

  const { start, end } = getCurrentMonthRange()

  // Fetch all data in parallel
  const [despesasRes, receitasRes, categoriasRes, orcamentosRes] = await Promise.all([
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
    supabase
      .from("orcamentos")
      .select("*, categoria:categorias(*)")
      .eq("user_id", user.id)
      .eq("mes", new Date().getMonth() + 1)
      .eq("ano", new Date().getFullYear()),
  ])

  const despesas = (despesasRes.data || []) as Despesa[]
  const receitas = (receitasRes.data || []) as Receita[]
  const categorias = (categoriasRes.data || []) as Categoria[]
  const orcamentos = (orcamentosRes.data || []) as Orcamento[]

  const totalDespesas = despesas.reduce((sum, d) => sum + d.valor, 0)
  const totalReceitas = receitas.reduce((sum, r) => sum + r.valor, 0)
  const saldo = totalReceitas - totalDespesas
  const economia = totalReceitas > 0 ? ((totalReceitas - totalDespesas) / totalReceitas) * 100 : 0

  return (
    <div className="space-y-6">
      <PageAnimation type="dashboard" />

      <div className="flex items-center gap-3">
        <div className="relative">
          <Zap className="h-8 w-8 text-primary" />
          <div className="absolute inset-0 blur-md bg-primary/50 rounded-full" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">Dashboard</span>
          </h1>
          <p className="text-muted-foreground">Visao geral das suas financas em tempo real</p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Receitas do Mes"
          value={formatCurrency(totalReceitas)}
          description="este mes"
          icon={ArrowUpCircle}
          variant="success"
        />
        <StatsCard
          title="Despesas do Mes"
          value={formatCurrency(totalDespesas)}
          description="este mes"
          icon={ArrowDownCircle}
          variant="destructive"
        />
        <StatsCard
          title="Saldo Atual"
          value={formatCurrency(saldo)}
          description="receitas - despesas"
          icon={Wallet}
          variant={saldo >= 0 ? "success" : "destructive"}
        />
        <StatsCard
          title="Taxa de Economia"
          value={`${economia.toFixed(1)}%`}
          description="do total recebido"
          icon={TrendingUp}
          variant={economia >= 20 ? "success" : economia >= 10 ? "warning" : "destructive"}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ExpenseChart despesas={despesas} categorias={categorias} />
        <BudgetProgress orcamentos={orcamentos} despesas={despesas} />
      </div>

      <RecentTransactions despesas={despesas} receitas={receitas} />
    </div>
  )
}
