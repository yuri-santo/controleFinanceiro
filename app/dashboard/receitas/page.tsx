import { createClient } from "@/lib/supabase/server"
import type { Receita } from "@/lib/types"
import { PageAnimation } from "@/components/animations/page-animation"
import { ReceitasClient } from "@/components/income/receitas-client"

export default async function ReceitasPage() {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) return null

  const { data: receitas } = await supabase
    .from("receitas")
    .select("*")
    .eq("user_id", user.id)
    .order("data", { ascending: false })

  const receitasList = (receitas || []) as Receita[]

  return (
    <div className="space-y-6">
      <PageAnimation type="receitas" />
      <ReceitasClient receitas={receitasList} userId={user.id} />
    </div>
  )
}
