import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Por padrão o Vite só expõe pro código do navegador env vars
  // prefixadas com VITE_. `SUPABASE_ANON_KEY` foi pedida sem esse
  // prefixo de propósito, então precisa ser lida aqui via `loadEnv`
  // (que enxerga o .env e as env vars do ambiente de build, ex. Vercel,
  // com ou sem prefixo) e injetada manualmente com `define`.
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react(), tailwindcss()],
    define: {
      'import.meta.env.SUPABASE_ANON_KEY': JSON.stringify(env.SUPABASE_ANON_KEY ?? ''),
    },
  }
})


