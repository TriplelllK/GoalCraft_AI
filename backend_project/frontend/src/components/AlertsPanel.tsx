import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../api';
import type { NotificationsResponse } from '../types';

const severityIcon: Record<string, string> = {
  critical: '🔴',
  warning: '🟡',
  info: '🔵',
};

const roleLabel: Record<string, string> = {
  manager: 'Руководитель',
  employee: 'Сотрудник',
  hr: 'HR',
};

export function AlertsPanel() {
  const [data, setData] = useState<NotificationsResponse | null>(null);
  const [open, setOpen] = useState(false);
  const [quarter] = useState('Q2');
  const [year] = useState(2026);
  const [loading, setLoading] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  const fetchNotifications = useCallback(() => {
    setLoading(true);
    api.notifications(quarter, year)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [quarter, year]);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 60_000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [open]);

  const badgeCount = data ? data.critical + data.warnings : 0;

  return (
    <div className="alerts-panel-wrap" ref={panelRef}>
      <button
        className="alerts-bell"
        onClick={() => setOpen((prev) => !prev)}
        title="Уведомления"
        aria-label="Открыть уведомления"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        {badgeCount > 0 && (
          <span className="alerts-badge-count">{badgeCount}</span>
        )}
      </button>

      {open && (
        <div className="alerts-dropdown">
          <div className="alerts-dropdown-header">
            <strong>Уведомления</strong>
            {data && (
              <span className="alerts-summary">
                {data.critical > 0 && <span className="alerts-crit-count">🔴 {data.critical}</span>}
                {data.warnings > 0 && <span className="alerts-warn-count">🟡 {data.warnings}</span>}
                {data.info > 0 && <span className="alerts-info-count">🔵 {data.info}</span>}
              </span>
            )}
          </div>

          {loading && <div className="loading-bar" />}

          <div className="alerts-dropdown-body">
            {!data || data.items.length === 0 ? (
              <div className="alerts-empty">Нет активных уведомлений</div>
            ) : (
              data.items.map((item) => (
                <div className={`alerts-item alerts-item-${item.severity}`} key={item.id}>
                  <div className="alerts-item-header">
                    <span className="alerts-item-icon">{severityIcon[item.severity] || '⚪'}</span>
                    <span className="alerts-item-title">{item.title}</span>
                    <span className="alerts-item-role">{roleLabel[item.target_role] || item.target_role}</span>
                  </div>
                  <div className="alerts-item-message">{item.message}</div>
                  {item.department_name && (
                    <div className="alerts-item-meta">
                      {item.department_name}
                      {item.employee_name ? ` · ${item.employee_name}` : ''}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          <div className="alerts-dropdown-footer">
            Всего: {data?.total ?? 0} · {quarter} {year}
          </div>
        </div>
      )}
    </div>
  );
}
