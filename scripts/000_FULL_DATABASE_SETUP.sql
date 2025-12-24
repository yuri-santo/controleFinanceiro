-- =====================================================
-- FINCONTROL - SCRIPT COMPLETO DE SETUP DO BANCO DE DADOS
-- =====================================================
-- Execute este script no SQL Editor do Supabase
-- URL: https://supabase.com/dashboard/project/SEU_PROJETO/sql
-- =====================================================

-- =====================================================
-- 1. CRIAR TABELAS PRINCIPAIS
-- =====================================================

-- Create profiles table
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT,
  nome TEXT,
  tipo_usuario TEXT DEFAULT 'PF' CHECK (tipo_usuario IN ('PF', 'PJ')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create categorias table
CREATE TABLE IF NOT EXISTS categorias (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  nome TEXT NOT NULL,
  tipo TEXT NOT NULL CHECK (tipo IN ('despesa', 'receita')),
  cor TEXT DEFAULT '#6366f1',
  icone TEXT DEFAULT 'circle',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create despesas table
CREATE TABLE IF NOT EXISTS despesas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  valor DECIMAL(12,2) NOT NULL,
  categoria_id UUID REFERENCES categorias(id) ON DELETE SET NULL,
  subcategoria TEXT,
  data DATE NOT NULL,
  descricao TEXT,
  forma_pagamento TEXT CHECK (forma_pagamento IN ('cartao', 'debito', 'pix', 'dinheiro')),
  cartao_id UUID,
  recorrente BOOLEAN DEFAULT FALSE,
  parcelado BOOLEAN DEFAULT FALSE,
  total_parcelas INTEGER DEFAULT 1,
  parcela_atual INTEGER DEFAULT 1,
  observacoes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create receitas table
CREATE TABLE IF NOT EXISTS receitas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  valor DECIMAL(12,2) NOT NULL,
  fonte TEXT NOT NULL,
  data DATE NOT NULL,
  descricao TEXT,
  recorrente BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create cartoes table
CREATE TABLE IF NOT EXISTS cartoes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  nome TEXT NOT NULL,
  bandeira TEXT,
  limite_total DECIMAL(12,2) NOT NULL,
  fechamento_fatura INTEGER NOT NULL CHECK (fechamento_fatura BETWEEN 1 AND 31),
  vencimento INTEGER NOT NULL CHECK (vencimento BETWEEN 1 AND 31),
  cor TEXT DEFAULT '#6366f1',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add foreign key for cartao_id in despesas
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints 
    WHERE constraint_name = 'fk_cartao' AND table_name = 'despesas'
  ) THEN
    ALTER TABLE despesas ADD CONSTRAINT fk_cartao FOREIGN KEY (cartao_id) REFERENCES cartoes(id) ON DELETE SET NULL;
  END IF;
END $$;

-- Create objetivos table
CREATE TABLE IF NOT EXISTS objetivos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  nome TEXT NOT NULL,
  valor_total DECIMAL(12,2) NOT NULL,
  valor_atual DECIMAL(12,2) DEFAULT 0,
  prazo DATE,
  tipo TEXT CHECK (tipo IN ('sonho', 'reserva', 'projeto', 'emergencia')),
  cor TEXT DEFAULT '#10b981',
  icone TEXT DEFAULT 'target',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create caixinhas table
CREATE TABLE IF NOT EXISTS caixinhas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  nome TEXT NOT NULL,
  saldo DECIMAL(12,2) DEFAULT 0,
  objetivo_id UUID REFERENCES objetivos(id) ON DELETE SET NULL,
  cor TEXT DEFAULT '#f59e0b',
  icone TEXT DEFAULT 'piggy-bank',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create orcamentos table
CREATE TABLE IF NOT EXISTS orcamentos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  categoria_id UUID REFERENCES categorias(id) ON DELETE CASCADE,
  valor_limite DECIMAL(12,2) NOT NULL,
  mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
  ano INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, categoria_id, mes, ano)
);

-- Create transferencias_caixinha table
CREATE TABLE IF NOT EXISTS transferencias_caixinha (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  caixinha_origem_id UUID REFERENCES caixinhas(id) ON DELETE SET NULL,
  caixinha_destino_id UUID REFERENCES caixinhas(id) ON DELETE SET NULL,
  valor DECIMAL(12,2) NOT NULL,
  data DATE NOT NULL,
  observacao TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 2. TABELAS DE INVESTIMENTOS
-- =====================================================

-- Tabela de ativos de renda variável (ações, FIIs, ETFs, BDRs)
CREATE TABLE IF NOT EXISTS renda_variavel (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  ticker TEXT NOT NULL,
  tipo TEXT NOT NULL CHECK (tipo IN ('acao', 'fii', 'etf', 'bdr')),
  quantidade DECIMAL(12,4) NOT NULL,
  preco_medio DECIMAL(12,2) NOT NULL,
  data_compra DATE NOT NULL,
  corretora TEXT,
  setor TEXT,
  observacoes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de renda fixa
CREATE TABLE IF NOT EXISTS renda_fixa (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  nome TEXT NOT NULL,
  tipo TEXT NOT NULL CHECK (tipo IN ('cdb', 'lci', 'lca', 'tesouro_selic', 'tesouro_ipca', 'tesouro_prefixado', 'debenture', 'cri', 'cra', 'poupanca')),
  instituicao TEXT NOT NULL,
  valor_investido DECIMAL(12,2) NOT NULL,
  valor_atual DECIMAL(12,2) NOT NULL,
  taxa DECIMAL(8,4) NOT NULL,
  indexador TEXT CHECK (indexador IN ('cdi', 'ipca', 'selic', 'prefixado', 'poupanca')),
  data_aplicacao DATE NOT NULL,
  data_vencimento DATE,
  liquidez TEXT CHECK (liquidez IN ('diaria', 'vencimento', 'carencia')),
  dias_carencia INTEGER,
  observacoes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de histórico de cotações (cache local)
CREATE TABLE IF NOT EXISTS cotacoes_historico (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticker TEXT NOT NULL,
  preco DECIMAL(12,2) NOT NULL,
  variacao DECIMAL(8,4),
  data DATE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(ticker, data)
);

-- Tabela de transações de investimentos
CREATE TABLE IF NOT EXISTS transacoes_investimentos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  investimento_id UUID NOT NULL,
  tipo_investimento TEXT NOT NULL CHECK (tipo_investimento IN ('renda_variavel', 'renda_fixa')),
  tipo_operacao TEXT NOT NULL CHECK (tipo_operacao IN ('compra', 'venda', 'dividendo', 'jcp', 'rendimento', 'amortizacao')),
  quantidade DECIMAL(12,4),
  valor DECIMAL(12,2) NOT NULL,
  data DATE NOT NULL,
  observacoes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de dividendos e proventos
CREATE TABLE IF NOT EXISTS proventos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  ticker TEXT NOT NULL,
  tipo TEXT NOT NULL CHECK (tipo IN ('dividendo', 'jcp', 'rendimento', 'amortizacao')),
  valor DECIMAL(12,2) NOT NULL,
  data_com DATE,
  data_pagamento DATE NOT NULL,
  quantidade_base DECIMAL(12,4),
  observacoes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 3. HABILITAR ROW LEVEL SECURITY
-- =====================================================

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE categorias ENABLE ROW LEVEL SECURITY;
ALTER TABLE despesas ENABLE ROW LEVEL SECURITY;
ALTER TABLE receitas ENABLE ROW LEVEL SECURITY;
ALTER TABLE cartoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE objetivos ENABLE ROW LEVEL SECURITY;
ALTER TABLE caixinhas ENABLE ROW LEVEL SECURITY;
ALTER TABLE orcamentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE transferencias_caixinha ENABLE ROW LEVEL SECURITY;
ALTER TABLE renda_variavel ENABLE ROW LEVEL SECURITY;
ALTER TABLE renda_fixa ENABLE ROW LEVEL SECURITY;
ALTER TABLE cotacoes_historico ENABLE ROW LEVEL SECURITY;
ALTER TABLE transacoes_investimentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE proventos ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- 4. CRIAR POLITICAS RLS
-- =====================================================

-- Profiles policies
DROP POLICY IF EXISTS "profiles_select_own" ON profiles;
DROP POLICY IF EXISTS "profiles_insert_own" ON profiles;
DROP POLICY IF EXISTS "profiles_update_own" ON profiles;
DROP POLICY IF EXISTS "profiles_delete_own" ON profiles;

CREATE POLICY "profiles_select_own" ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "profiles_insert_own" ON profiles FOR INSERT WITH CHECK (auth.uid() = id);
CREATE POLICY "profiles_update_own" ON profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "profiles_delete_own" ON profiles FOR DELETE USING (auth.uid() = id);

-- Categorias policies
DROP POLICY IF EXISTS "categorias_select_own" ON categorias;
DROP POLICY IF EXISTS "categorias_insert_own" ON categorias;
DROP POLICY IF EXISTS "categorias_update_own" ON categorias;
DROP POLICY IF EXISTS "categorias_delete_own" ON categorias;

CREATE POLICY "categorias_select_own" ON categorias FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "categorias_insert_own" ON categorias FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "categorias_update_own" ON categorias FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "categorias_delete_own" ON categorias FOR DELETE USING (auth.uid() = user_id);

-- Despesas policies
DROP POLICY IF EXISTS "despesas_select_own" ON despesas;
DROP POLICY IF EXISTS "despesas_insert_own" ON despesas;
DROP POLICY IF EXISTS "despesas_update_own" ON despesas;
DROP POLICY IF EXISTS "despesas_delete_own" ON despesas;

CREATE POLICY "despesas_select_own" ON despesas FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "despesas_insert_own" ON despesas FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "despesas_update_own" ON despesas FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "despesas_delete_own" ON despesas FOR DELETE USING (auth.uid() = user_id);

-- Receitas policies
DROP POLICY IF EXISTS "receitas_select_own" ON receitas;
DROP POLICY IF EXISTS "receitas_insert_own" ON receitas;
DROP POLICY IF EXISTS "receitas_update_own" ON receitas;
DROP POLICY IF EXISTS "receitas_delete_own" ON receitas;

CREATE POLICY "receitas_select_own" ON receitas FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "receitas_insert_own" ON receitas FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "receitas_update_own" ON receitas FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "receitas_delete_own" ON receitas FOR DELETE USING (auth.uid() = user_id);

-- Cartoes policies
DROP POLICY IF EXISTS "cartoes_select_own" ON cartoes;
DROP POLICY IF EXISTS "cartoes_insert_own" ON cartoes;
DROP POLICY IF EXISTS "cartoes_update_own" ON cartoes;
DROP POLICY IF EXISTS "cartoes_delete_own" ON cartoes;

CREATE POLICY "cartoes_select_own" ON cartoes FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "cartoes_insert_own" ON cartoes FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "cartoes_update_own" ON cartoes FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "cartoes_delete_own" ON cartoes FOR DELETE USING (auth.uid() = user_id);

-- Objetivos policies
DROP POLICY IF EXISTS "objetivos_select_own" ON objetivos;
DROP POLICY IF EXISTS "objetivos_insert_own" ON objetivos;
DROP POLICY IF EXISTS "objetivos_update_own" ON objetivos;
DROP POLICY IF EXISTS "objetivos_delete_own" ON objetivos;

CREATE POLICY "objetivos_select_own" ON objetivos FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "objetivos_insert_own" ON objetivos FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "objetivos_update_own" ON objetivos FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "objetivos_delete_own" ON objetivos FOR DELETE USING (auth.uid() = user_id);

-- Caixinhas policies
DROP POLICY IF EXISTS "caixinhas_select_own" ON caixinhas;
DROP POLICY IF EXISTS "caixinhas_insert_own" ON caixinhas;
DROP POLICY IF EXISTS "caixinhas_update_own" ON caixinhas;
DROP POLICY IF EXISTS "caixinhas_delete_own" ON caixinhas;

CREATE POLICY "caixinhas_select_own" ON caixinhas FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "caixinhas_insert_own" ON caixinhas FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "caixinhas_update_own" ON caixinhas FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "caixinhas_delete_own" ON caixinhas FOR DELETE USING (auth.uid() = user_id);

-- Orcamentos policies
DROP POLICY IF EXISTS "orcamentos_select_own" ON orcamentos;
DROP POLICY IF EXISTS "orcamentos_insert_own" ON orcamentos;
DROP POLICY IF EXISTS "orcamentos_update_own" ON orcamentos;
DROP POLICY IF EXISTS "orcamentos_delete_own" ON orcamentos;

CREATE POLICY "orcamentos_select_own" ON orcamentos FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "orcamentos_insert_own" ON orcamentos FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "orcamentos_update_own" ON orcamentos FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "orcamentos_delete_own" ON orcamentos FOR DELETE USING (auth.uid() = user_id);

-- Transferencias caixinha policies
DROP POLICY IF EXISTS "transferencias_caixinha_select_own" ON transferencias_caixinha;
DROP POLICY IF EXISTS "transferencias_caixinha_insert_own" ON transferencias_caixinha;
DROP POLICY IF EXISTS "transferencias_caixinha_update_own" ON transferencias_caixinha;
DROP POLICY IF EXISTS "transferencias_caixinha_delete_own" ON transferencias_caixinha;

CREATE POLICY "transferencias_caixinha_select_own" ON transferencias_caixinha FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "transferencias_caixinha_insert_own" ON transferencias_caixinha FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "transferencias_caixinha_update_own" ON transferencias_caixinha FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "transferencias_caixinha_delete_own" ON transferencias_caixinha FOR DELETE USING (auth.uid() = user_id);

-- Renda variável policies
DROP POLICY IF EXISTS "renda_variavel_select_own" ON renda_variavel;
DROP POLICY IF EXISTS "renda_variavel_insert_own" ON renda_variavel;
DROP POLICY IF EXISTS "renda_variavel_update_own" ON renda_variavel;
DROP POLICY IF EXISTS "renda_variavel_delete_own" ON renda_variavel;

CREATE POLICY "renda_variavel_select_own" ON renda_variavel FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "renda_variavel_insert_own" ON renda_variavel FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "renda_variavel_update_own" ON renda_variavel FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "renda_variavel_delete_own" ON renda_variavel FOR DELETE USING (auth.uid() = user_id);

-- Renda fixa policies
DROP POLICY IF EXISTS "renda_fixa_select_own" ON renda_fixa;
DROP POLICY IF EXISTS "renda_fixa_insert_own" ON renda_fixa;
DROP POLICY IF EXISTS "renda_fixa_update_own" ON renda_fixa;
DROP POLICY IF EXISTS "renda_fixa_delete_own" ON renda_fixa;

CREATE POLICY "renda_fixa_select_own" ON renda_fixa FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "renda_fixa_insert_own" ON renda_fixa FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "renda_fixa_update_own" ON renda_fixa FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "renda_fixa_delete_own" ON renda_fixa FOR DELETE USING (auth.uid() = user_id);

-- Cotações histórico policies (leitura pública para cache)
DROP POLICY IF EXISTS "cotacoes_historico_select_all" ON cotacoes_historico;
DROP POLICY IF EXISTS "cotacoes_historico_insert_all" ON cotacoes_historico;

CREATE POLICY "cotacoes_historico_select_all" ON cotacoes_historico FOR SELECT USING (true);
CREATE POLICY "cotacoes_historico_insert_all" ON cotacoes_historico FOR INSERT WITH CHECK (true);

-- Transações investimentos policies
DROP POLICY IF EXISTS "transacoes_investimentos_select_own" ON transacoes_investimentos;
DROP POLICY IF EXISTS "transacoes_investimentos_insert_own" ON transacoes_investimentos;
DROP POLICY IF EXISTS "transacoes_investimentos_update_own" ON transacoes_investimentos;
DROP POLICY IF EXISTS "transacoes_investimentos_delete_own" ON transacoes_investimentos;

CREATE POLICY "transacoes_investimentos_select_own" ON transacoes_investimentos FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "transacoes_investimentos_insert_own" ON transacoes_investimentos FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "transacoes_investimentos_update_own" ON transacoes_investimentos FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "transacoes_investimentos_delete_own" ON transacoes_investimentos FOR DELETE USING (auth.uid() = user_id);

-- Proventos policies
DROP POLICY IF EXISTS "proventos_select_own" ON proventos;
DROP POLICY IF EXISTS "proventos_insert_own" ON proventos;
DROP POLICY IF EXISTS "proventos_update_own" ON proventos;
DROP POLICY IF EXISTS "proventos_delete_own" ON proventos;

CREATE POLICY "proventos_select_own" ON proventos FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "proventos_insert_own" ON proventos FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "proventos_update_own" ON proventos FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "proventos_delete_own" ON proventos FOR DELETE USING (auth.uid() = user_id);

-- =====================================================
-- 5. CRIAR TRIGGERS E FUNCOES
-- =====================================================

-- Trigger to auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (id, email, nome)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data ->> 'nome', split_part(NEW.email, '@', 1))
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();

-- Function to create default categories for new users
CREATE OR REPLACE FUNCTION public.create_default_categories()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  -- Default expense categories
  INSERT INTO public.categorias (user_id, nome, tipo, cor, icone) VALUES
    (NEW.id, 'Alimentacao', 'despesa', '#ef4444', 'utensils'),
    (NEW.id, 'Transporte', 'despesa', '#f97316', 'car'),
    (NEW.id, 'Moradia', 'despesa', '#eab308', 'home'),
    (NEW.id, 'Saude', 'despesa', '#22c55e', 'heart-pulse'),
    (NEW.id, 'Educacao', 'despesa', '#3b82f6', 'graduation-cap'),
    (NEW.id, 'Lazer', 'despesa', '#8b5cf6', 'gamepad-2'),
    (NEW.id, 'Vestuario', 'despesa', '#ec4899', 'shirt'),
    (NEW.id, 'Investimentos', 'despesa', '#06b6d4', 'trending-up'),
    (NEW.id, 'Outros', 'despesa', '#6b7280', 'more-horizontal');
  
  -- Default income categories
  INSERT INTO public.categorias (user_id, nome, tipo, cor, icone) VALUES
    (NEW.id, 'Salario', 'receita', '#10b981', 'wallet'),
    (NEW.id, 'Freelance', 'receita', '#06b6d4', 'laptop'),
    (NEW.id, 'Investimentos', 'receita', '#8b5cf6', 'trending-up'),
    (NEW.id, 'Dividendos', 'receita', '#f59e0b', 'coins'),
    (NEW.id, 'Outros', 'receita', '#6b7280', 'plus-circle');

  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_profile_created ON public.profiles;

CREATE TRIGGER on_profile_created
  AFTER INSERT ON public.profiles
  FOR EACH ROW
  EXECUTE FUNCTION public.create_default_categories();

-- =====================================================
-- SETUP COMPLETO! Seu banco de dados esta pronto.
-- =====================================================
