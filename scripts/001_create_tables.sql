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
ALTER TABLE despesas ADD CONSTRAINT fk_cartao FOREIGN KEY (cartao_id) REFERENCES cartoes(id) ON DELETE SET NULL;

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

-- Enable Row Level Security on all tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE categorias ENABLE ROW LEVEL SECURITY;
ALTER TABLE despesas ENABLE ROW LEVEL SECURITY;
ALTER TABLE receitas ENABLE ROW LEVEL SECURITY;
ALTER TABLE cartoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE objetivos ENABLE ROW LEVEL SECURITY;
ALTER TABLE caixinhas ENABLE ROW LEVEL SECURITY;
ALTER TABLE orcamentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE transferencias_caixinha ENABLE ROW LEVEL SECURITY;
