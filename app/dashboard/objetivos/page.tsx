import { createClient } from "@/lib/supabase/server"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Target, TrendingUp, Star } from "lucide-react"
import { formatCurrency } from "@/lib/utils/currency"
import type { Objetivo } from "@/lib/types"
import { GoalItem } from "@/components/goals/goal-item"
import { AddGoalDialog } from "@/components/goals/add-goal-dialog"

export default async function ObjetivosPage() {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) return null

  const { data: objetivos } = await supabase
    .from("objetivos")
    .select("*")
    .eq("user_id", user.id)
    .neq("tipo", "emergencia")
    .order("created_at", { ascending: false })

  const objetivosList = (objetivos || []) as Objetivo[]

  const totalMeta = objetivosList.reduce((sum, o) => sum + o.valor_total, 0)
  const totalGuardado = objetivosList.reduce((sum, o) => sum + o.valor_atual, 0)
  const concluidos = objetivosList.filter((o) => o.valor_atual >= o.valor_total).length

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold">Objetivos Financeiros</h1>
          <p className="text-muted-foreground">Acompanhe seus sonhos e metas</p>
        </div>
        <AddGoalDialog userId={user.id} />
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total das Metas</CardTitle>
            <Target className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totalMeta)}</div>
            <p className="text-sm text-muted-foreground">{objetivosList.length} objetivos</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Guardado</CardTitle>
            <TrendingUp className="h-5 w-5 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600">{formatCurrency(totalGuardado)}</div>
            <p className="text-sm text-muted-foreground">
              {totalMeta > 0 ? `${((totalGuardado / totalMeta) * 100).toFixed(0)}% do total` : "0%"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Concluidos</CardTitle>
            <Star className="h-5 w-5 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600">{concluidos}</div>
            <p className="text-sm text-muted-foreground">objetivos alcancados</p>
          </CardContent>
        </Card>
      </div>

      {objetivosList.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Target className="h-12 w-12 text-muted-foreground" />
            <h3 className="mt-4 font-semibold">Nenhum objetivo criado</h3>
            <p className="mt-2 text-sm text-muted-foreground">Crie seu primeiro objetivo financeiro</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {objetivosList.map((objetivo) => (
            <GoalItem key={objetivo.id} objetivo={objetivo} userId={user.id} />
          ))}
        </div>
      )}
    </div>
  )
}
