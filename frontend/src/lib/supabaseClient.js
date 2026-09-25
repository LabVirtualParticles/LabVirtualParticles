import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
// Sem prefixo VITE_ de propósito — por isso não é exposta pelo
// mecanismo automático do Vite, e sim manualmente via `define` no
// vite.config.js (procure por SUPABASE_ANON_KEY lá).
const supabaseAnonKey = import.meta.env.SUPABASE_ANON_KEY;

export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);

if (!isSupabaseConfigured) {
  // Não trava o app — só avisa no console. Sem essas duas variáveis
  // (VITE_SUPABASE_URL no `.env`/env vars normais, SUPABASE_ANON_KEY
  // também no `.env`/env vars mas exposta via vite.config.js), login e
  // cadastro ficam desativados, mas o resto do site continua funcionando
  // normalmente. IMPORTANTE: `createClient` joga um erro síncrono se
  // receber url/key vazios, então só chamamos ele quando as duas
  // variáveis existem de verdade.
  console.warn(
    '[supabase] VITE_SUPABASE_URL / SUPABASE_ANON_KEY não configuradas — ' +
      'veja claude/supabase-auth-setup.md. Login e cadastro não vão funcionar até isso ser preenchido.'
  );
}

export const supabase = isSupabaseConfigured
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null;
