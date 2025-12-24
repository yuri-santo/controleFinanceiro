import { createClient } from "@/lib/supabase/server"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { BarChart3, TrendingUp, TrendingDown } from "lucide-react"
import { formatCurrency } from "@/lib/utils/currency"
import { getCurrentMonthRange, formatMonthYear } from "@/lib/utils/date"
import type { Orcamento, Categoria, Despesa } from "@/lib/types"
import { BudgetItem } from "@/components/budget/budget-item"
import { AddBudgetDialog } from "@/components/budget/add-budget-dialog"

export default async function OrcamentoPage() {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) return null

  const now = new Date()
  const mes = now.getMonth() + 1
  const ano = now.getFullYear()
  const { start, end } = getCurrentMonthRange()

  const [orcamentosRes, categoriasRes, despesasRes] = await Promise.all([
    supabase
      .from("orcamentos")
      .select("*, categoria:categorias(*)")
      .eq("user_id", user.id)
      .eq("mes", mes)
      .eq("ano", ano),
    supabase.from("categorias").select("*").eq("user_id", user.id).eq("tipo", "despesa"),
    supabase.from("despesas").select("*").eq("user_id", user.id).gte("data", start).lte("data", end),
  ])

  const orcamentos = (orcamentosRes.data || []) as Orcamento[]
  const categorias = (categoriasRes.data || []) as Categoria[]
  const despesas = (despesasRes.data || []) as Despesa[]

  const totalOrcado = orcamentos.reduce((sum, o) => sum + o.valor_limite, 0)
  const totalGasto = despesas.reduce((sum, d) => sum + d.valor, 0)
  const saldo = totalOrcado - totalGasto

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold">Orcamento</h1>
          <p className="text-muted-foreground">{formatMonthYear(now)}</p>
        </div>
        <AddBudgetDialog userId={user.id} categorias={categorias} mes={mes} ano={ano} />
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Orcado</CardTitle>
            <BarChart3 className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totalOrcado)}</div>
            <p className="text-sm text-muted-foreground">{orcamentos.length} categorias</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Gasto</CardTitle>
            <TrendingDown className="h-5 w-5 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{formatCurrency(totalGasto)}</div>
            <p className="text-sm text-muted-foreground">
              {totalOrcado > 0 ? `${((totalGasto / totalOrcado) * 100).toFixed(0)}% do orcamento` : "sem orcamento"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Saldo Disponivel</CardTitle>
            <TrendingUp className={`h-5 w-5 ${saldo >= 0 ? "text-emerald-500" : "text-red-500"}`} />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${saldo >= 0 ? "text-emerald-600" : "text-red-600"}`}>
              {formatCurrency(saldo)}
            </div>
            <p className="text-sm text-muted-foreground">{saldo >= 0 ? "dentro do orcamento" : "acima do orcamento"}</p>
          </CardContent>
        </Card>
      </div>

      {orcamentos.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <BarChart3 className="h-12 w-12 text-muted-foreground" />
            <h3 className="mt-4 font-semibold">Nenhum orcamento definido</h3>
            <p className="mt-2 text-sm text-muted-foreground">Defina limites de gastos por categoria</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {orcamentos.map((orcamento) => (
            <BudgetItem
              key={orcamento.id}
              orcamento={orcamento}
              categorias={categorias}
              despesas={despesas}
              userId={user.id}
            />
          ))}
        </div>
      )}
    </div>
  )
}
