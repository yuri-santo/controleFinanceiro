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
    (NEW.id, 'Outros', 'despesa', '#6b7280', 'more-horizontal');
  
  -- Default income categories
  INSERT INTO public.categorias (user_id, nome, tipo, cor, icone) VALUES
    (NEW.id, 'Salario', 'receita', '#10b981', 'wallet'),
    (NEW.id, 'Freelance', 'receita', '#06b6d4', 'laptop'),
    (NEW.id, 'Investimentos', 'receita', '#8b5cf6', 'trending-up'),
    (NEW.id, 'Outros', 'receita', '#6b7280', 'plus-circle');

  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_profile_created ON public.profiles;

CREATE TRIGGER on_profile_created
  AFTER INSERT ON public.profiles
  FOR EACH ROW
  EXECUTE FUNCTION public.create_default_categories();
