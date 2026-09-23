import { Link } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

export function Header({ onAuthClick, theme, onToggleTheme }) {
  const { user, logout, isAuthenticated } = useAuth();

  return (
    <header className="header">
      <Link to="/" className="logo">
        Nebula
      </Link>
      <div className="header-actions">
        <button type="button" className="btn ghost" onClick={onToggleTheme}>
          {theme === 'dark' ? '☀️ Light' : '🌙 Dark'}
        </button>
        {isAuthenticated ? (
          <>
            <span className="user-email">{user.email}</span>
            <button type="button" className="btn ghost" onClick={logout}>
              Log out
            </button>
          </>
        ) : (
          <button type="button" className="btn primary" onClick={onAuthClick}>
            Sign in
          </button>
        )}
        <a className="btn ghost" href="/legacy/index.html">
          Legacy UI
        </a>
      </div>
    </header>
  );
}
