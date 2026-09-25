import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  // Não trava o app — só avisa no console. Sem essas duas variáveis no
  // `.env` (ver `.env.example`), login/cadastro simplesmente não vão
  // funcionar até você criar o projeto no Supabase e preencher elas.
  console.warn(
    '[supabase] VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY não configuradas — ' +
      'veja frontend/.env.example. Login e cadastro não vão funcionar até isso ser preenchido.'
  );
}

export const supabase = createClient(supabaseUrl ?? '', supabaseAnonKey ?? '');
