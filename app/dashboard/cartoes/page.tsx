import { createClient } from "@/lib/supabase/server"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { CreditCard, AlertTriangle } from "lucide-react"
import { formatCurrency } from "@/lib/utils/currency"
import { getCurrentMonthRange } from "@/lib/utils/date"
import type { Cartao, Despesa } from "@/lib/types"
import { CardItem } from "@/components/cards/card-item"
import { AddCardDialog } from "@/components/cards/add-card-dialog"
import { PageAnimation } from "@/components/animations/page-animation"

export default async function CartoesPage() {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) return null

  const { start, end } = getCurrentMonthRange()

  const [cartoesRes, despesasRes] = await Promise.all([
    supabase.from("cartoes").select("*").eq("user_id", user.id).order("nome"),
    supabase
      .from("despesas")
      .select("*")
      .eq("user_id", user.id)
      .eq("forma_pagamento", "cartao")
      .gte("data", start)
      .lte("data", end),
  ])

  const cartoes = (cartoesRes.data || []) as Cartao[]
  const despesas = (despesasRes.data || []) as Despesa[]

  const totalFaturas = despesas.reduce((sum, d) => sum + d.valor, 0)
  const totalLimite = cartoes.reduce((sum, c) => sum + c.limite_total, 0)
  const limiteUsado = totalLimite > 0 ? (totalFaturas / totalLimite) * 100 : 0

  return (
    <div className="space-y-6">
      <PageAnimation type="cartoes" />

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold neon-text">Cartoes de Credito</h1>
          <p className="text-muted-foreground">Gerencie seus cartoes e acompanhe as faturas</p>
        </div>
        <AddCardDialog userId={user.id} />
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="card-3d glass-card overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-transparent" />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total em Faturas</CardTitle>
            <CreditCard className="h-5 w-5 text-purple-400" />
          </CardHeader>
          <CardContent className="relative">
            <div className="text-2xl font-bold">{formatCurrency(totalFaturas)}</div>
            <p className="text-sm text-muted-foreground">{cartoes.length} cartoes</p>
          </CardContent>
        </Card>

        <Card className="card-3d glass-card overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-transparent" />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Limite Disponivel</CardTitle>
            <CreditCard className="h-5 w-5 text-emerald-400" />
          </CardHeader>
          <CardContent className="relative">
            <div className="text-2xl font-bold text-emerald-400">{formatCurrency(totalLimite - totalFaturas)}</div>
            <p className="text-sm text-muted-foreground">de {formatCurrency(totalLimite)}</p>
          </CardContent>
        </Card>

        <Card className="card-3d glass-card overflow-hidden">
          <div
            className={`absolute inset-0 bg-gradient-to-br ${limiteUsado > 80 ? "from-red-500/10" : limiteUsado > 50 ? "from-amber-500/10" : "from-emerald-500/10"} to-transparent`}
          />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Limite Usado</CardTitle>
            <AlertTriangle
              className={`h-5 w-5 ${limiteUsado > 80 ? "text-red-400" : limiteUsado > 50 ? "text-amber-400" : "text-emerald-400"}`}
            />
          </CardHeader>
          <CardContent className="relative">
            <div
              className={`text-2xl font-bold ${limiteUsado > 80 ? "text-red-400" : limiteUsado > 50 ? "text-amber-400" : "text-emerald-400"}`}
            >
              {limiteUsado.toFixed(1)}%
            </div>
            <p className="text-sm text-muted-foreground">
              {limiteUsado > 80 ? "Cuidado!" : limiteUsado > 50 ? "Atencao" : "Saudavel"}
            </p>
          </CardContent>
        </Card>
      </div>

      {cartoes.length === 0 ? (
        <Card className="card-3d glass-card">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <CreditCard className="h-12 w-12 text-muted-foreground" />
            <h3 className="mt-4 font-semibold">Nenhum cartao cadastrado</h3>
            <p className="mt-2 text-sm text-muted-foreground">Adicione seu primeiro cartao de credito</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cartoes.map((cartao) => (
            <CardItem key={cartao.id} cartao={cartao} despesas={despesas} userId={user.id} />
          ))}
        </div>
      )}
    </div>
  )
}
