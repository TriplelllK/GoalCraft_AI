import { NavLink } from 'react-router-dom';
import type { HealthResponse } from '../types';
import { AlertsPanel } from './AlertsPanel';

interface LayoutProps {
  health: HealthResponse | null;
  children: React.ReactNode;
}

export function Layout({ health, children }: LayoutProps) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <span className="brand-icon">🎯</span>
          <span className="brand-text">GoalCraft AI</span>
        </div>
        <nav className="nav-links">
          <NavLink to="/evaluate" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Оценка</NavLink>
          <NavLink to="/generate" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Генерация</NavLink>
          <NavLink to="/cascade" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Каскад</NavLink>
          <NavLink to="/dashboard" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Дашборд</NavLink>
          <NavLink to="/maturity" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>Зрелость</NavLink>
        </nav>
        <div className="header-actions">
          <AlertsPanel />
          <div className="status-pill">
            {health ? (
              <span className="status-dot online" title={`${health.mode} · ${health.vector_backend} · LLM: ${health.llm_enabled ? 'ON' : 'OFF'}`} />
            ) : (
              <span className="status-dot offline" />
            )}
            {health ? `${health.mode} · ${health.indexed_documents} док · ${health.employees_count || '?'} сотр` : 'offline'}
          </div>
        </div>
      </header>
      <main className="app-main">{children}</main>
    </div>
  );
}
