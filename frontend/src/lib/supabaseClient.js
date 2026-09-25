import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);

if (!isSupabaseConfigured) {
  // Não trava o app — só avisa no console. Sem essas duas variáveis no
  // `.env` (local) ou nas env vars do deploy (Vercel etc.), login e
  // cadastro ficam desativados, mas o resto do site continua funcionando
  // normalmente. IMPORTANTE: `createClient` joga um erro síncrono se
  // receber url/key vazios, então só chamamos ele quando as duas
  // variáveis existem de verdade.
  console.warn(
    '[supabase] VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY não configuradas — ' +
      'veja frontend/.env.example. Login e cadastro não vão funcionar até isso ser preenchido.'
  );
}

export const supabase = isSupabaseConfigured
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null;
