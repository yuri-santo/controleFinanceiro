-- =====================================================
-- FINCONTROL - TABELAS DE INVESTIMENTOS
-- =====================================================
-- Execute este script no SQL Editor do Supabase
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

-- Habilitar RLS
ALTER TABLE renda_variavel ENABLE ROW LEVEL SECURITY;
ALTER TABLE renda_fixa ENABLE ROW LEVEL SECURITY;
ALTER TABLE cotacoes_historico ENABLE ROW LEVEL SECURITY;
ALTER TABLE transacoes_investimentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE proventos ENABLE ROW LEVEL SECURITY;

-- Políticas RLS para renda_variavel
DROP POLICY IF EXISTS "renda_variavel_select_own" ON renda_variavel;
DROP POLICY IF EXISTS "renda_variavel_insert_own" ON renda_variavel;
DROP POLICY IF EXISTS "renda_variavel_update_own" ON renda_variavel;
DROP POLICY IF EXISTS "renda_variavel_delete_own" ON renda_variavel;

CREATE POLICY "renda_variavel_select_own" ON renda_variavel FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "renda_variavel_insert_own" ON renda_variavel FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "renda_variavel_update_own" ON renda_variavel FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "renda_variavel_delete_own" ON renda_variavel FOR DELETE USING (auth.uid() = user_id);

-- Políticas RLS para renda_fixa
DROP POLICY IF EXISTS "renda_fixa_select_own" ON renda_fixa;
DROP POLICY IF EXISTS "renda_fixa_insert_own" ON renda_fixa;
DROP POLICY IF EXISTS "renda_fixa_update_own" ON renda_fixa;
DROP POLICY IF EXISTS "renda_fixa_delete_own" ON renda_fixa;

CREATE POLICY "renda_fixa_select_own" ON renda_fixa FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "renda_fixa_insert_own" ON renda_fixa FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "renda_fixa_update_own" ON renda_fixa FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "renda_fixa_delete_own" ON renda_fixa FOR DELETE USING (auth.uid() = user_id);

-- Políticas RLS para cotacoes_historico (leitura pública para cache)
DROP POLICY IF EXISTS "cotacoes_historico_select_all" ON cotacoes_historico;
DROP POLICY IF EXISTS "cotacoes_historico_insert_all" ON cotacoes_historico;

CREATE POLICY "cotacoes_historico_select_all" ON cotacoes_historico FOR SELECT USING (true);
CREATE POLICY "cotacoes_historico_insert_all" ON cotacoes_historico FOR INSERT WITH CHECK (true);

-- Políticas RLS para transacoes_investimentos
DROP POLICY IF EXISTS "transacoes_investimentos_select_own" ON transacoes_investimentos;
DROP POLICY IF EXISTS "transacoes_investimentos_insert_own" ON transacoes_investimentos;
DROP POLICY IF EXISTS "transacoes_investimentos_update_own" ON transacoes_investimentos;
DROP POLICY IF EXISTS "transacoes_investimentos_delete_own" ON transacoes_investimentos;

CREATE POLICY "transacoes_investimentos_select_own" ON transacoes_investimentos FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "transacoes_investimentos_insert_own" ON transacoes_investimentos FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "transacoes_investimentos_update_own" ON transacoes_investimentos FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "transacoes_investimentos_delete_own" ON transacoes_investimentos FOR DELETE USING (auth.uid() = user_id);

-- Políticas RLS para proventos
DROP POLICY IF EXISTS "proventos_select_own" ON proventos;
DROP POLICY IF EXISTS "proventos_insert_own" ON proventos;
DROP POLICY IF EXISTS "proventos_update_own" ON proventos;
DROP POLICY IF EXISTS "proventos_delete_own" ON proventos;

CREATE POLICY "proventos_select_own" ON proventos FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "proventos_insert_own" ON proventos FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "proventos_update_own" ON proventos FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "proventos_delete_own" ON proventos FOR DELETE USING (auth.uid() = user_id);

-- =====================================================
-- SETUP DE INVESTIMENTOS COMPLETO!
-- =====================================================
