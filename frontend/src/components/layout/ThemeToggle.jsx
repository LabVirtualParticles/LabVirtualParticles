import { useTheme } from '../../context/ThemeContext';
import './ThemeToggle.css';

// Ícones provisórios (sol/lua desenhados à mão em SVG inline) — troque o
// conteúdo dos dois <svg> abaixo pelo SVG do Lorenzo assim que ele estiver
// disponível. Importante: cole o MARKUP do SVG diretamente aqui (como
// está feito agora), em vez de dar `import` de um arquivo .svg — isso
// evita o problema de importação, e permite usar `stroke="currentColor"`
// / `fill="currentColor"` no SVG pra ele herdar a cor do tema automaticamente.
export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isLight = theme === 'light';

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={toggleTheme}
      aria-label={isLight ? 'Ativar tema escuro' : 'Ativar tema claro'}
      aria-pressed={isLight}
      title={isLight ? 'Tema escuro' : 'Tema claro'}
    >
      {isLight ? (
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79Z" />
        </svg>
      ) : (
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
        </svg>
      )}
    </button>
  );
}
