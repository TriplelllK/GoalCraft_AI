import { useEffect, useMemo, useState } from 'react';
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from '../api';
import { KpiCard } from '../components/KpiCard';
import type { DashboardOverview, DepartmentSnapshot } from '../types';

const palette = ['#3b82f6', '#14b8a6', '#8b5cf6', '#f59e0b', '#ef4444'];

export function DashboardPage() {
  const [quarter, setQuarter] = useState('Q2');
  const [year, setYear] = useState(2026);
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [selectedDepartmentId, setSelectedDepartmentId] = useState('');
  const [department, setDepartment] = useState<DepartmentSnapshot | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    setError('');
    api.dashboardOverview(quarter, year)
      .then((data) => {
        setOverview(data);
        const firstId = data.departments[0]?.department_id || '';
        setSelectedDepartmentId((prev) => prev || firstId);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [quarter, year]);

  useEffect(() => {
    if (!selectedDepartmentId) {
      setDepartment(null);
      return;
    }
    api.departmentDashboard(selectedDepartmentId, quarter, year)
      .then(setDepartment)
      .catch((err) => setError(err.message));
  }, [selectedDepartmentId, quarter, year]);

  const chartData = useMemo(
    () => (overview?.departments || []).map((item) => ({
      name: item.department_name,
      avgSmart: Math.round(item.avg_smart_score * 100),
      strategicShare: Math.round(item.strategic_goal_share * 100),
      alerts: item.alert_count
    })),
    [overview]
  );

  return (
    <div className="page-grid">
      <section className="panel panel-primary panel-wide">
        <div className="panel-header">
          <div>
            <h2>Дашборд руководителя</h2>
            <p>Агрегированная оценка зрелости целеполагания по подразделениям и детальный срез по выбранному отделу.</p>
          </div>
          <div className="form-grid inline-grid">
            <label>
              Квартал
              <select value={quarter} onChange={(e) => setQuarter(e.target.value)}>
                <option>Q1</option>
                <option>Q2</option>
                <option>Q3</option>
                <option>Q4</option>
              </select>
            </label>
            <label>
              Год
              <input type="number" value={year} onChange={(e) => setYear(Number(e.target.value))} />
            </label>
          </div>
        </div>

        {overview ? (
          <>
            <div className="kpi-grid">
              <KpiCard label="Подразделения" value={`${overview.total_departments}`} />
              <KpiCard label="Оценено целей" value={`${overview.total_goals_evaluated}`} />
              <KpiCard label="Средний SMART" value={`${Math.round(overview.avg_smart_score * 100)}%`} />
              <KpiCard label="Strategic share" value={`${Math.round(overview.strategic_goal_share * 100)}%`} />
            </div>

            <div className="chart-card">
              <h3>Средний SMART по подразделениям</h3>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="avgSmart" radius={[8, 8, 0, 0]}>
                    {chartData.map((entry, index) => <Cell key={`${entry.name}-${index}`} fill={palette[index % palette.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </>
        ) : (
          <div className="empty-state">{loading ? 'Загрузка dashboard...' : 'Нет данных для отображения.'}</div>
        )}

        {error ? <div className="error-box">{error}</div> : null}
      </section>

      <section className="panel">
        <h3>Выбранное подразделение</h3>
        <label>
          Подразделение
          <select value={selectedDepartmentId} onChange={(e) => setSelectedDepartmentId(e.target.value)}>
            {(overview?.departments || []).map((item) => (
              <option key={item.department_id} value={item.department_id}>{item.department_name}</option>
            ))}
          </select>
        </label>

        {department ? (
          <div className="stack-gap">
            <div className="subtle-card">
              <div className="muted">Название</div>
              <strong>{department.department_name}</strong>
            </div>
            <div className="kpi-grid compact-grid">
              <KpiCard label="Средний SMART" value={`${Math.round(department.avg_smart_score * 100)}%`} />
              <KpiCard label="Strategic share" value={`${Math.round(department.strategic_goal_share * 100)}%`} />
              <KpiCard label="Слабый критерий" value={department.weakest_criterion} />
              <KpiCard label="Алерты" value={`${department.alert_count}`} />
              <KpiCard label="Индекс зрелости" value={`${Math.round(department.maturity_index * 100)}%`} />
              <KpiCard label="Уровень" value={department.maturity_level} />
            </div>
          </div>
        ) : (
          <div className="empty-state">Выбери подразделение для детального среза.</div>
        )}
      </section>
    </div>
  );
}
