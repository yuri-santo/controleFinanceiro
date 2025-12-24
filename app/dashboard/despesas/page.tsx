import { createClient } from "@/lib/supabase/server"
import type { Despesa, Categoria, Cartao } from "@/lib/types"
import { PageAnimation } from "@/components/animations/page-animation"
import { DespesasClient } from "@/components/expenses/despesas-client"

export default async function DespesasPage() {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) return null

  const [despesasRes, categoriasRes, cartoesRes] = await Promise.all([
    supabase
      .from("despesas")
      .select("*, categoria:categorias(*), cartao:cartoes(*)")
      .eq("user_id", user.id)
      .order("data", { ascending: false }),
    supabase.from("categorias").select("*").eq("user_id", user.id).eq("tipo", "despesa"),
    supabase.from("cartoes").select("*").eq("user_id", user.id),
  ])

  const despesas = (despesasRes.data || []) as Despesa[]
  const categorias = (categoriasRes.data || []) as Categoria[]
  const cartoes = (cartoesRes.data || []) as Cartao[]

  return (
    <div className="space-y-6">
      <PageAnimation type="despesas" />

      <DespesasClient despesas={despesas} categorias={categorias} cartoes={cartoes} userId={user.id} />
    </div>
  )
}
