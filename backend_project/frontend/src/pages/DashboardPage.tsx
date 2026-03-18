import { useEffect, useMemo, useState } from 'react';
import { Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from '../api';
import { KpiCard } from '../components/KpiCard';
import { ProgressBar } from '../components/ProgressBar';
import type { DashboardOverview, DataStats, DepartmentSnapshot } from '../types';

const palette = ['#3b82f6', '#14b8a6', '#8b5cf6', '#f59e0b', '#ef4444', '#ec4899', '#06b6d4', '#84cc16'];

function scoreColor(v: number): string {
  if (v >= 0.8) return '#22c55e';
  if (v >= 0.6) return '#f59e0b';
  return '#ef4444';
}

function levelBadge(level: string): string {
  if (level === 'продвинутый') return 'badge-green';
  if (level === 'зрелый') return 'badge-teal';
  if (level === 'развивающийся') return 'badge-yellow';
  return 'badge-red';
}

export function DashboardPage() {
  const [quarter, setQuarter] = useState('Q2');
  const [year, setYear] = useState(2026);
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [selectedDepartmentId, setSelectedDepartmentId] = useState('');
  const [department, setDepartment] = useState<DepartmentSnapshot | null>(null);
  const [dataStats, setDataStats] = useState<DataStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    setError('');
    Promise.all([
      api.dashboardOverview(quarter, year),
      api.dataStats(),
    ])
      .then(([data, stats]) => {
        setOverview(data);
        setDataStats(stats);
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

  // Chart: grouped bar (SMART + Strategic)
  const barChartData = useMemo(
    () => (overview?.departments || []).map((item) => ({
      name: item.department_name.replace(/^Отдел\s+/i, ''),
      smart: Math.round(item.avg_smart_score * 100),
      strategic: Math.round(item.strategic_goal_share * 100),
      alerts: item.alert_count,
    })),
    [overview]
  );

  // Chart: maturity pie
  const maturityPieData = useMemo(() => {
    const levels: Record<string, number> = {};
    (overview?.departments || []).forEach((d) => {
      levels[d.maturity_level] = (levels[d.maturity_level] || 0) + 1;
    });
    return Object.entries(levels).map(([name, value]) => ({ name, value }));
  }, [overview]);

  const maturityColors: Record<string, string> = {
    'продвинутый': '#3b82f6',
    'зрелый': '#14b8a6',
    'развивающийся': '#f59e0b',
    'начальный': '#ef4444',
  };

  // Sort departments by SMART desc for ranking table
  const sortedDepts = useMemo(
    () => [...(overview?.departments || [])].sort((a, b) => b.avg_smart_score - a.avg_smart_score),
    [overview]
  );

  return (
    <div className="page-grid">
      {/* ── Top KPI ribbon ──────────────────────────────────────── */}
      <section className="panel panel-primary panel-wide">
        <div className="panel-header">
          <div>
            <h2>📊 Дашборд руководителя</h2>
            <p>Агрегированная аналитика целеполагания по всем подразделениям за период.</p>
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

        {loading && <div className="loading-bar" />}

        {overview ? (
          <div className="kpi-grid kpi-grid-5">
            <KpiCard label="Подразделения" value={`${overview.total_departments}`} />
            <KpiCard label="Оценено целей" value={`${overview.total_goals_evaluated}`} />
            <KpiCard
              label="Средний SMART"
              value={`${Math.round(overview.avg_smart_score * 100)}%`}
              color={scoreColor(overview.avg_smart_score)}
            />
            <KpiCard
              label="Стратег. доля"
              value={`${Math.round(overview.strategic_goal_share * 100)}%`}
              color={scoreColor(overview.strategic_goal_share)}
            />
            <KpiCard
              label="Режим данных"
              value={dataStats?.has_dump_data ? 'Дамп ТЗ' : 'Демо'}
              hint={dataStats ? `${dataStats.employees} сотр · ${dataStats.goals} целей` : ''}
            />
          </div>
        ) : (
          <div className="empty-state">{loading ? 'Загрузка...' : 'Нет данных.'}</div>
        )}

        {error ? <div className="error-box">{error}</div> : null}
      </section>

      {/* ── Grouped bar chart: SMART + Strategic ────────────────── */}
      {overview && barChartData.length > 0 && (
        <section className="panel panel-wide">
          <h3>Сравнение подразделений: SMART-индекс и стратегическая доля</h3>
          <div className="chart-card">
            <ResponsiveContainer width="100%" height={340}>
              <BarChart data={barChartData} barGap={2} barCategoryGap="20%">
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2e3d" />
                <XAxis dataKey="name" tick={{ fill: '#8b8fa5', fontSize: 12 }} />
                <YAxis tick={{ fill: '#8b8fa5', fontSize: 12 }} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ background: '#1a1d28', border: '1px solid #2a2e3d', borderRadius: 8 }}
                  labelStyle={{ color: '#e4e6f0' }}
                />
                <Legend wrapperStyle={{ fontSize: 13 }} />
                <Bar dataKey="smart" name="SMART %" fill="#3b82f6" radius={[6, 6, 0, 0]} />
                <Bar dataKey="strategic" name="Стратег. %" fill="#14b8a6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}

      {/* ── Maturity pie + Ranking table ────────────────────────── */}
      {overview && (
        <>
          <section className="panel">
            <h3>Распределение зрелости</h3>
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={maturityPieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={95} label>
                  {maturityPieData.map((item, i) => (
                    <Cell key={i} fill={maturityColors[item.name] || palette[i]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </section>

          <section className="panel">
            <h3>Рейтинг подразделений</h3>
            <div className="dept-table-wrap">
              <table className="dept-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Подразделение</th>
                    <th>SMART</th>
                    <th>Стратег.</th>
                    <th>Алерты</th>
                    <th>Уровень</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedDepts.map((d, i) => (
                    <tr
                      key={d.department_id}
                      className={selectedDepartmentId === d.department_id ? 'row-selected' : ''}
                      onClick={() => setSelectedDepartmentId(d.department_id)}
                    >
                      <td className="rank-cell">{i + 1}</td>
                      <td>{d.department_name}</td>
                      <td>
                        <span className="score-inline" style={{ color: scoreColor(d.avg_smart_score) }}>
                          {Math.round(d.avg_smart_score * 100)}%
                        </span>
                      </td>
                      <td>
                        <span className="score-inline" style={{ color: scoreColor(d.strategic_goal_share) }}>
                          {Math.round(d.strategic_goal_share * 100)}%
                        </span>
                      </td>
                      <td>
                        {d.alert_count > 0 ? (
                          <span className="alert-badge">{d.alert_count}</span>
                        ) : (
                          <span className="ok-badge">0</span>
                        )}
                      </td>
                      <td><span className={`badge ${levelBadge(d.maturity_level)}`}>{d.maturity_level}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}

      {/* ── Department detail panel ─────────────────────────────── */}
      <section className="panel panel-wide">
        <div className="panel-header">
          <h3>📋 Детали подразделения</h3>
          <label style={{ minWidth: 220 }}>
            <select value={selectedDepartmentId} onChange={(e) => setSelectedDepartmentId(e.target.value)}>
              {(overview?.departments || []).map((item) => (
                <option key={item.department_id} value={item.department_id}>{item.department_name}</option>
              ))}
            </select>
          </label>
        </div>

        {department ? (
          <div className="dept-detail-grid">
            <div className="dept-detail-kpis">
              <div className="kpi-grid compact-grid">
                <KpiCard label="Средний SMART" value={`${Math.round(department.avg_smart_score * 100)}%`} color={scoreColor(department.avg_smart_score)} />
                <KpiCard label="Стратег. доля" value={`${Math.round(department.strategic_goal_share * 100)}%`} color={scoreColor(department.strategic_goal_share)} />
                <KpiCard label="Слабый критерий" value={department.weakest_criterion} />
                <KpiCard label="Алерты" value={`${department.alert_count}`} color={department.alert_count > 0 ? '#ef4444' : '#22c55e'} />
              </div>
            </div>
            <div className="dept-detail-maturity">
              <div className="maturity-mini-circle" style={{ borderColor: scoreColor(department.maturity_index) }}>
                <span className="maturity-mini-value">{Math.round(department.maturity_index * 100)}%</span>
                <span className="maturity-mini-label">{department.maturity_level}</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="empty-state">Выберите подразделение для детального анализа.</div>
        )}
      </section>

      {/* ── Data stats panel (§4.2) ─────────────────────────────── */}
      {dataStats && (
        <section className="panel panel-wide">
          <h3>📦 Статистика данных (§4.2 ТЗ)</h3>
          <div className="kpi-grid">
            <KpiCard label="Подразделения" value={`${dataStats.departments}`} />
            <KpiCard label="Должности" value={`${dataStats.positions}`} />
            <KpiCard label="Сотрудники" value={`${dataStats.employees}`} />
            <KpiCard label="Документы" value={`${dataStats.documents}`} />
            <KpiCard label="Цели" value={`${dataStats.goals}`} />
            <KpiCard label="События целей" value={`${dataStats.goal_events}`} />
            <KpiCard label="Ревью целей" value={`${dataStats.goal_reviews}`} />
            <KpiCard label="KPI каталог" value={`${dataStats.kpi_catalog}`} />
            <KpiCard label="KPI временные ряды" value={`${dataStats.kpi_timeseries}`} />
          </div>
          <div className="subtle-card" style={{ marginTop: '0.75rem' }}>
            <span className={dataStats.has_dump_data ? 'status-ok' : 'status-demo'}>
              {dataStats.has_dump_data ? '✅ Загружен полный дамп организаторов' : '🔧 Режим демо-данных (seed)'}
            </span>
          </div>
        </section>
      )}
    </div>
  );
}
