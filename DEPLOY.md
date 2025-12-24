# Guia de Deploy - FinControl

## Pre-requisitos

1. Conta no Supabase (gratuito): https://supabase.com
2. Conta no servico de hospedagem (Render, Vercel, Railway, etc.)
3. Node.js 18+ instalado localmente

---

## IMPORTANTE: Seguranca

Este projeto foi atualizado para corrigir a vulnerabilidade CVE-2025-55182 (React Server Components RCE).

**Versoes seguras utilizadas:**
- Next.js: 16.0.7+
- React: 19.2.1+

**Recursos de seguranca implementados:**
- Headers de seguranca (CSP, X-Frame-Options, etc.)
- Sanitizacao de inputs com DOMPurify
- Rate limiting para prevenir ataques de forca bruta
- Validacao de UUID e tipos
- Row Level Security (RLS) no Supabase

---

## Passo 1: Configurar o Supabase

### 1.1 Criar Projeto

1. Acesse https://supabase.com/dashboard
2. Clique em "New Project"
3. Escolha um nome e senha para o banco de dados
4. Selecione a regiao mais proxima (South America para BR)
5. Aguarde a criacao do projeto (~2 minutos)

### 1.2 Executar Script do Banco de Dados

1. No dashboard do Supabase, va em **SQL Editor**
2. Clique em **New Query**
3. Copie TODO o conteudo do arquivo `scripts/000_FULL_DATABASE_SETUP.sql`
4. Cole no editor e clique em **Run**
5. Aguarde a execucao (deve mostrar "Success")

**IMPORTANTE:** Este script cria:
- Todas as tabelas (despesas, receitas, cartoes, investimentos, etc.)
- Politicas de seguranca RLS (Row Level Security)
- Triggers para criar perfil e categorias automaticamente
- Tabelas de renda variavel e renda fixa

### 1.3 Executar Script de Investimentos

1. No SQL Editor, crie uma nova query
2. Copie o conteudo de `scripts/005_investments_tables.sql`
3. Execute para criar as tabelas de investimentos

### 1.4 Obter Credenciais

1. Va em **Settings** > **API**
2. Copie os valores:
   - **Project URL** → `NEXT_PUBLIC_SUPABASE_URL`
   - **anon public** → `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - **service_role** → `SUPABASE_SERVICE_ROLE_KEY`

### 1.5 Configurar Autenticacao

1. Va em **Authentication** > **URL Configuration**
2. Em **Site URL**, coloque sua URL de producao
3. Em **Redirect URLs**, adicione:
   - `https://seu-dominio.com/*`
   - `http://localhost:3000/*` (para desenvolvimento)

---

## Passo 2: Deploy no Render (Gratuito)

### 2.1 Preparar Repositorio

1. Faca push do codigo para um repositorio GitHub
2. Certifique-se que o `.gitignore` inclui `.env.local`

### 2.2 Criar Web Service no Render

1. Acesse https://render.com e faca login
2. Clique em **New** > **Web Service**
3. Conecte seu repositorio GitHub
4. Configure:
   - **Name**: fincontrol (ou outro nome)
   - **Region**: Oregon (ou mais proxima)
   - **Branch**: main
   - **Runtime**: Node
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm start`

### 2.3 Configurar Variaveis de Ambiente

No painel do Render, va em **Environment** e adicione:

```
NEXT_PUBLIC_SUPABASE_URL=https://seu-projeto.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sua_anon_key
SUPABASE_SERVICE_ROLE_KEY=sua_service_role_key
NEXT_PUBLIC_DEV_SUPABASE_REDIRECT_URL=
```

### 2.4 Deploy

1. Clique em **Create Web Service**
2. Aguarde o build e deploy (~5-10 minutos)
3. Acesse a URL fornecida pelo Render

---

## Passo 3: Deploy na Vercel (Recomendado)

### 3.1 Via Dashboard (Mais Facil)

1. Acesse https://vercel.com
2. Clique em **Add New** > **Project**
3. Importe o repositorio GitHub
4. Em **Environment Variables**, adicione:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
5. Clique em **Deploy**

### 3.2 Via CLI

```bash
# Instalar Vercel CLI
npm i -g vercel

# Fazer login
vercel login

# Deploy
vercel

# Adicionar variaveis de ambiente
vercel env add NEXT_PUBLIC_SUPABASE_URL
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY
vercel env add SUPABASE_SERVICE_ROLE_KEY

# Redeploy com as variaveis
vercel --prod
```

---

## Passo 4: Deploy na Hostinger

### 4.1 Build Local

```bash
npm install
npm run build
```

### 4.2 Upload via FTP/File Manager

1. Acesse o painel da Hostinger
2. Va em **File Manager** ou use FTP
3. Faca upload de:
   - Pasta `.next`
   - Pasta `public`
   - Pasta `node_modules` (ou rode `npm install` no servidor)
   - Arquivo `package.json`
   - Arquivo `next.config.mjs`

### 4.3 Configurar Node.js

1. No painel, va em **Website** > **Advanced** > **Node.js**
2. Habilite Node.js
3. Configure o comando de inicio: `npm start`
4. Adicione as variaveis de ambiente no painel

---

## Configuracao para GitHub Actions (CI/CD)

Crie o arquivo `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run build
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

---

## Exemplo de .env.local

```env
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://abcdefghijk.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Redirecionamento (deixe vazio em producao)
NEXT_PUBLIC_DEV_SUPABASE_REDIRECT_URL=
```

---

## Verificacao Final

Apos o deploy, verifique:

- [ ] Landing page carrega corretamente
- [ ] Pagina de login funciona
- [ ] Cadastro de usuario funciona
- [ ] Email de confirmacao e enviado
- [ ] Dashboard carrega apos login
- [ ] Animacoes funcionam corretamente
- [ ] Dados sao salvos no banco
- [ ] Graficos aparecem corretamente
- [ ] Investimentos exibem cotacoes (API Brapi)
- [ ] Exportacao Excel/CSV funciona
- [ ] Headers de seguranca estao ativos (verificar no DevTools > Network)

---

## Troubleshooting

### Erro de CORS
- Verifique se a URL do site esta nas Redirect URLs do Supabase

### Erro de Autenticacao
- Confirme que as variaveis de ambiente estao corretas
- Verifique se o script SQL foi executado

### Pagina em branco
- Verifique os logs do servidor
- Confirme que o build foi bem sucedido

### Cotacoes nao carregam
- A API Brapi e gratuita mas tem limite de requests
- Verifique se nao ha erro de rede

### Graficos nao aparecem
- Verifique se ha dados no banco
- Abra o console do navegador para ver erros

### Animacoes nao funcionam
- Verifique se o JavaScript esta habilitado
- Usuarios com `prefers-reduced-motion` terao animacoes desabilitadas

---

## Custos Estimados

| Servico | Plano | Custo |
|---------|-------|-------|
| Supabase | Free | R$ 0 |
| Render | Free | R$ 0 |
| Vercel | Hobby | R$ 0 |
| Brapi (Cotacoes) | Free | R$ 0 |
| Hostinger | Premium | ~R$ 15/mes |

**Total minimo: R$ 0/mes** (usando Supabase + Render/Vercel + Brapi)

---

## Links Uteis

- [Documentacao Supabase](https://supabase.com/docs)
- [Documentacao Vercel](https://vercel.com/docs)
- [Documentacao Render](https://render.com/docs)
- [API Brapi (Cotacoes)](https://brapi.dev)
- [Next.js Docs](https://nextjs.org/docs)
- [CVE-2025-55182 Info](https://www.oligo.security/blog/critical-react-next-js-rce-vulnerability-cve-2025-55182-cve-2025-66478-what-you-need-to-know)
