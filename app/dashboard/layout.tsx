import type React from "react"
import { redirect } from "next/navigation"
import { createClient } from "@/lib/supabase/server"
import { Sidebar } from "@/components/dashboard/sidebar"
import { Header } from "@/components/dashboard/header"
import type { Profile } from "@/lib/types"

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient()

  const {
    data: { user },
    error,
  } = await supabase.auth.getUser()

  if (error || !user) {
    redirect("/auth/login")
  }

  const { data: profile } = await supabase.from("profiles").select("*").eq("id", user.id).single()

  return (
    <div className="min-h-screen bg-background noise-overlay relative">
      {/* Grid pattern background */}
      <div className="fixed inset-0 grid-pattern opacity-30 pointer-events-none" />

      {/* Gradient orbs for ambient lighting */}
      <div className="fixed top-0 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl pointer-events-none" />
      <div className="fixed bottom-0 right-1/4 w-80 h-80 bg-accent/10 rounded-full blur-3xl pointer-events-none" />

      <Sidebar />
      <div className="lg:pl-64 relative">
        <Header profile={profile as Profile | null} />
        <main className="p-4 lg:p-6">{children}</main>
      </div>
    </div>
  )
}
