-- Profiles policies
CREATE POLICY "profiles_select_own" ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "profiles_insert_own" ON profiles FOR INSERT WITH CHECK (auth.uid() = id);
CREATE POLICY "profiles_update_own" ON profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "profiles_delete_own" ON profiles FOR DELETE USING (auth.uid() = id);

-- Categorias policies
CREATE POLICY "categorias_select_own" ON categorias FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "categorias_insert_own" ON categorias FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "categorias_update_own" ON categorias FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "categorias_delete_own" ON categorias FOR DELETE USING (auth.uid() = user_id);

-- Despesas policies
CREATE POLICY "despesas_select_own" ON despesas FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "despesas_insert_own" ON despesas FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "despesas_update_own" ON despesas FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "despesas_delete_own" ON despesas FOR DELETE USING (auth.uid() = user_id);

-- Receitas policies
CREATE POLICY "receitas_select_own" ON receitas FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "receitas_insert_own" ON receitas FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "receitas_update_own" ON receitas FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "receitas_delete_own" ON receitas FOR DELETE USING (auth.uid() = user_id);

-- Cartoes policies
CREATE POLICY "cartoes_select_own" ON cartoes FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "cartoes_insert_own" ON cartoes FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "cartoes_update_own" ON cartoes FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "cartoes_delete_own" ON cartoes FOR DELETE USING (auth.uid() = user_id);

-- Objetivos policies
CREATE POLICY "objetivos_select_own" ON objetivos FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "objetivos_insert_own" ON objetivos FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "objetivos_update_own" ON objetivos FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "objetivos_delete_own" ON objetivos FOR DELETE USING (auth.uid() = user_id);

-- Caixinhas policies
CREATE POLICY "caixinhas_select_own" ON caixinhas FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "caixinhas_insert_own" ON caixinhas FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "caixinhas_update_own" ON caixinhas FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "caixinhas_delete_own" ON caixinhas FOR DELETE USING (auth.uid() = user_id);

-- Orcamentos policies
CREATE POLICY "orcamentos_select_own" ON orcamentos FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "orcamentos_insert_own" ON orcamentos FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "orcamentos_update_own" ON orcamentos FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "orcamentos_delete_own" ON orcamentos FOR DELETE USING (auth.uid() = user_id);

-- Transferencias caixinha policies
CREATE POLICY "transferencias_caixinha_select_own" ON transferencias_caixinha FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "transferencias_caixinha_insert_own" ON transferencias_caixinha FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "transferencias_caixinha_update_own" ON transferencias_caixinha FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "transferencias_caixinha_delete_own" ON transferencias_caixinha FOR DELETE USING (auth.uid() = user_id);
