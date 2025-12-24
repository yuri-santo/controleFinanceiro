import { createClient } from "@/lib/supabase/server"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import type { Profile, Categoria } from "@/lib/types"
import { ProfileForm } from "@/components/settings/profile-form"
import { CategoriesManager } from "@/components/settings/categories-manager"

export default async function ConfiguracoesPage() {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) return null

  const [profileRes, categoriasRes] = await Promise.all([
    supabase.from("profiles").select("*").eq("id", user.id).single(),
    supabase.from("categorias").select("*").eq("user_id", user.id).order("nome"),
  ])

  const profile = profileRes.data as Profile | null
  const categorias = (categoriasRes.data || []) as Categoria[]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Configuracoes</h1>
        <p className="text-muted-foreground">Gerencie sua conta e preferencias</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Perfil</CardTitle>
            <CardDescription>Atualize suas informacoes pessoais</CardDescription>
          </CardHeader>
          <CardContent>
            <ProfileForm profile={profile} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Categorias</CardTitle>
            <CardDescription>Gerencie suas categorias de despesas e receitas</CardDescription>
          </CardHeader>
          <CardContent>
            <CategoriesManager categorias={categorias} userId={user.id} />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
