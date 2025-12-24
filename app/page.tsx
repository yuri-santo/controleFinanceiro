import { Button } from "@/components/ui/button"
import {
  Wallet,
  TrendingUp,
  PiggyBank,
  CreditCard,
  Target,
  BarChart3,
  Shield,
  Smartphone,
  Sparkles,
  Zap,
  Globe,
} from "lucide-react"
import Link from "next/link"
import { HeroScene } from "@/components/3d/hero-scene"

export default function HomePage() {
  const features = [
    {
      icon: TrendingUp,
      title: "Controle de Despesas",
      description: "Registre e categorize todos os seus gastos com IA inteligente",
      color: "from-neon-cyan to-neon-cyan/50",
    },
    {
      icon: CreditCard,
      title: "Gestao de Cartoes",
      description: "Acompanhe faturas, limites e parcelas em tempo real",
      color: "from-neon-purple to-neon-purple/50",
    },
    {
      icon: Target,
      title: "Objetivos Financeiros",
      description: "Defina metas e visualize seu progresso com graficos 3D",
      color: "from-neon-pink to-neon-pink/50",
    },
    {
      icon: PiggyBank,
      title: "Caixinhas Virtuais",
      description: "Organize seu dinheiro em envelopes virtuais inteligentes",
      color: "from-neon-green to-neon-green/50",
    },
    {
      icon: BarChart3,
      title: "Relatorios Avancados",
      description: "Dashboards interativos e exportacao profissional",
      color: "from-neon-cyan to-neon-purple/50",
    },
    {
      icon: Shield,
      title: "Seguranca Total",
      description: "Criptografia de ponta e autenticacao multi-fator",
      color: "from-neon-purple to-neon-pink/50",
    },
  ]

  const stats = [
    { value: "100K+", label: "Usuarios ativos" },
    { value: "R$2B+", label: "Gerenciados" },
    { value: "99.9%", label: "Uptime" },
    { value: "4.9", label: "Avaliacao" },
  ]

  return (
    <div className="flex min-h-svh flex-col bg-background noise-overlay">
      {/* Grid pattern background */}
      <div className="fixed inset-0 grid-pattern opacity-50 pointer-events-none" />

      {/* Gradient orbs */}
      <div className="fixed top-20 -left-40 w-80 h-80 bg-neon-cyan/20 rounded-full blur-3xl pointer-events-none" />
      <div className="fixed top-40 -right-40 w-96 h-96 bg-neon-purple/20 rounded-full blur-3xl pointer-events-none" />
      <div className="fixed bottom-20 left-1/3 w-72 h-72 bg-neon-pink/10 rounded-full blur-3xl pointer-events-none" />

      <header className="sticky top-0 z-50 glass-strong">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="relative">
              <Wallet className="h-7 w-7 text-primary" />
              <div className="absolute inset-0 blur-sm bg-primary/50 rounded-full" />
            </div>
            <span className="text-xl font-bold neon-text text-primary">FinControl</span>
          </div>
          <div className="flex items-center gap-4">
            <Button asChild variant="ghost" className="text-foreground hover:text-primary hover:bg-primary/10">
              <Link href="/auth/login">Entrar</Link>
            </Button>
            <Button asChild className="neon-glow-subtle bg-primary hover:bg-primary/90 text-primary-foreground">
              <Link href="/auth/sign-up">
                <Sparkles className="mr-2 h-4 w-4" />
                Criar conta
              </Link>
            </Button>
          </div>
        </div>
      </header>

      <main className="flex-1 relative">
        {/* Hero Section */}
        <section className="container py-16 md:py-24 relative">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass border border-primary/30 text-sm">
                <Zap className="h-4 w-4 text-primary" />
                <span className="text-primary">Novo: IA Financeira Integrada</span>
              </div>

              <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl lg:text-7xl">
                <span className="block text-foreground">Controle suas</span>
                <span className="block text-transparent bg-clip-text bg-gradient-to-r from-primary via-accent to-neon-purple animate-gradient">
                  financas do futuro
                </span>
              </h1>

              <p className="text-lg text-muted-foreground max-w-xl text-pretty leading-relaxed">
                O FinControl e seu assistente financeiro com tecnologia de ponta. Interface futuristica, graficos 3D e
                inteligencia artificial para decisoes financeiras mais inteligentes.
              </p>

              <div className="flex flex-col sm:flex-row gap-4">
                <Button
                  asChild
                  size="lg"
                  className="neon-glow bg-primary hover:bg-primary/90 text-primary-foreground group"
                >
                  <Link href="/auth/sign-up">
                    <Smartphone className="mr-2 h-5 w-5 group-hover:rotate-12 transition-transform" />
                    Comecar agora
                  </Link>
                </Button>
                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="border-primary/50 hover:bg-primary/10 hover:border-primary group bg-transparent"
                >
                  <Link href="/auth/login">
                    <Globe className="mr-2 h-5 w-5 group-hover:rotate-180 transition-transform duration-500" />
                    Ja tenho conta
                  </Link>
                </Button>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-8">
                {stats.map((stat) => (
                  <div key={stat.label} className="text-center">
                    <div className="text-2xl font-bold text-primary neon-text">{stat.value}</div>
                    <div className="text-xs text-muted-foreground">{stat.label}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* 3D Hero Scene */}
            <div className="relative h-[400px] lg:h-[500px]">
              <HeroScene />
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="container py-24 relative">
          <div className="text-center space-y-4 mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">
              Tecnologia do futuro, hoje
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Funcionalidades avancadas com design futurista para sua saude financeira
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature, index) => (
              <div
                key={feature.title}
                className="group glass card-3d rounded-xl p-6 hover:neon-border transition-all duration-300"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div
                  className={`inline-flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br ${feature.color} mb-4 group-hover:scale-110 transition-transform`}
                >
                  <feature.icon className="h-7 w-7 text-background" />
                </div>
                <h3 className="text-lg font-semibold mb-2 group-hover:text-primary transition-colors">
                  {feature.title}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA Section */}
        <section className="container py-24 relative">
          <div className="glass rounded-3xl p-8 md:p-16 text-center relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-accent/5" />
            <div className="relative z-10 space-y-6">
              <h2 className="text-3xl md:text-4xl font-bold">
                Pronto para o{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">
                  futuro financeiro
                </span>
                ?
              </h2>
              <p className="text-muted-foreground max-w-xl mx-auto">
                Crie sua conta gratuita e experimente a revolucao no controle financeiro
              </p>
              <Button asChild size="lg" className="neon-glow bg-primary hover:bg-primary/90 text-primary-foreground">
                <Link href="/auth/sign-up">
                  <Sparkles className="mr-2 h-5 w-5" />
                  Criar conta gratuita
                </Link>
              </Button>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-border/50 py-8 relative glass-strong">
        <div className="container flex flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-2">
            <Wallet className="h-5 w-5 text-primary" />
            <span className="font-medium text-primary">FinControl</span>
          </div>
          <p className="text-sm text-muted-foreground">2024 FinControl. Controle financeiro do futuro.</p>
        </div>
      </footer>
    </div>
  )
}
