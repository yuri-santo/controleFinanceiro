import { createClient } from "@/lib/supabase/server"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { PiggyBank, Wallet } from "lucide-react"
import { formatCurrency } from "@/lib/utils/currency"
import type { Caixinha, Objetivo } from "@/lib/types"
import { SavingsBoxItem } from "@/components/savings/savings-box-item"
import { AddSavingsBoxDialog } from "@/components/savings/add-savings-box-dialog"
import { PageAnimation } from "@/components/animations/page-animation"

export default async function CaixinhasPage() {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) return null

  const [caixinhasRes, objetivosRes] = await Promise.all([
    supabase.from("caixinhas").select("*, objetivo:objetivos(*)").eq("user_id", user.id).order("nome"),
    supabase.from("objetivos").select("*").eq("user_id", user.id),
  ])

  const caixinhas = (caixinhasRes.data || []) as Caixinha[]
  const objetivos = (objetivosRes.data || []) as Objetivo[]

  const totalGuardado = caixinhas.reduce((sum, c) => sum + c.saldo, 0)

  return (
    <div className="space-y-6">
      <PageAnimation type="caixinhas" />

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold neon-text">Caixinhas</h1>
          <p className="text-muted-foreground">Organize seu dinheiro em envelopes virtuais</p>
        </div>
        <AddSavingsBoxDialog userId={user.id} objetivos={objetivos} />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card className="card-3d glass-card overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-orange-500/10 to-transparent" />
          <CardHeader className="relative flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Guardado</CardTitle>
            <Wallet className="h-5 w-5 text-orange-400" />
          </CardHeader>
          <CardContent className="relative">
            <div className="text-2xl font-bold text-orange-400">{formatCurrency(totalGuardado)}</div>
            <p className="text-sm text-muted-foreground">{caixinhas.length} caixinhas</p>
          </CardContent>
        </Card>
      </div>

      {caixinhas.length === 0 ? (
        <Card className="card-3d glass-card">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <PiggyBank className="h-12 w-12 text-muted-foreground" />
            <h3 className="mt-4 font-semibold">Nenhuma caixinha criada</h3>
            <p className="mt-2 text-sm text-muted-foreground">Crie caixinhas para organizar seu dinheiro</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {caixinhas.map((caixinha) => (
            <SavingsBoxItem
              key={caixinha.id}
              caixinha={caixinha}
              caixinhas={caixinhas}
              objetivos={objetivos}
              userId={user.id}
            />
          ))}
        </div>
      )}
    </div>
  )
}
