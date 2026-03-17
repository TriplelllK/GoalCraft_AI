import { useState } from 'react';
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import { api } from '../api';
import { KpiCard } from '../components/KpiCard';
import { ProgressBar } from '../components/ProgressBar';
import type { MaturityReport } from '../types';

const palette = ['#3b82f6', '#14b8a6', '#8b5cf6', '#f59e0b', '#ef4444'];

const maturityColor: Record<string, string> = {
  'начальный': '#ef4444',
  'развивающийся': '#f59e0b',
  'зрелый': '#14b8a6',
  'продвинутый': '#3b82f6',
};

export function MaturityPage() {
  const [departmentId, setDepartmentId] = useState('dep_hr');
  const [quarter, setQuarter] = useState('Q2');
  const [year, setYear] = useState(2026);
  const [report, setReport] = useState<MaturityReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleFetch() {
    setLoading(true);
    setError('');
    try {
      const data = await api.departmentMaturity(departmentId, quarter, year);
      setReport(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка загрузки отчёта зрелости');
    } finally {
      setLoading(false);
    }
  }

  const typePie = report
    ? [
        { name: 'Impact-based', value: Math.round(report.goal_type_distribution.impact_based * 100) },
        { name: 'Output-based', value: Math.round(report.goal_type_distribution.output_based * 100) },
        { name: 'Activity-based', value: Math.round(report.goal_type_distribution.activity_based * 100) },
      ]
    : [];

  const alignPie = report
    ? [
        { name: 'Стратегические', value: Math.round(report.alignment_distribution.strategic * 100) },
        { name: 'Функциональные', value: Math.round(report.alignment_distribution.functional * 100) },
        { name: 'Операционные', value: Math.round(report.alignment_distribution.operational * 100) },
      ]
    : [];

  return (
    <div className="page-grid">
      <section className="panel panel-primary">
        <div className="panel-header">
          <div>
            <h2>Индекс зрелости целеполагания</h2>
            <p>
              Интегральная оценка качества целеполагания подразделения: SMART-распределение,
              типы целей, стратегическая связка, слабые критерии и рекомендации.
            </p>
          </div>
        </div>

        <div className="form-grid three-columns">
          <label>
            Department ID
            <input value={departmentId} onChange={(e) => setDepartmentId(e.target.value)} />
          </label>
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

        <div className="button-row">
          <button onClick={handleFetch} disabled={loading}>
            {loading ? 'Загрузка...' : 'Построить отчёт зрелости'}
          </button>
        </div>

        {error ? <div className="error-box">{error}</div> : null}
      </section>

      {report ? (
        <>
          {/* Top-level KPIs */}
          <section className="panel panel-wide">
            <div className="maturity-hero">
              <div className="maturity-index-circle" style={{ borderColor: maturityColor[report.maturity_level] || '#888' }}>
                <span className="maturity-index-value">{Math.round(report.maturity_index * 100)}%</span>
                <span className="maturity-index-label">{report.maturity_level}</span>
              </div>
              <div className="kpi-grid">
                <KpiCard label="Сотрудников" value={`${report.total_employees}`} />
                <KpiCard label="С целями" value={`${report.employees_with_goals}`} />
                <KpiCard label="Всего целей" value={`${report.total_goals}`} />
                <KpiCard label="Средний SMART" value={`${Math.round(report.avg_smart_score * 100)}%`} />
                <KpiCard label="Стратег. доля" value={`${Math.round(report.strategic_goal_share * 100)}%`} />
                <KpiCard label="Алерты" value={`${report.alert_count}`} />
              </div>
            </div>
          </section>

          {/* SMART distribution */}
          <section className="panel">
            <h3>SMART-распределение</h3>
            <div className="stack-gap">
              <ProgressBar label={`Отлично (≥80%): ${report.smart_distribution.excellent}`} value={report.total_goals ? report.smart_distribution.excellent / report.total_goals : 0} />
              <ProgressBar label={`Хорошо (60–79%): ${report.smart_distribution.good}`} value={report.total_goals ? report.smart_distribution.good / report.total_goals : 0} />
              <ProgressBar label={`Нужна доработка (<60%): ${report.smart_distribution.needs_improvement}`} value={report.total_goals ? report.smart_distribution.needs_improvement / report.total_goals : 0} />
            </div>

            <h4>Слабые критерии</h4>
            <div className="tag-row">
              {report.weakest_criteria.map((item) => (
                <span className="tag tag-warn" key={item}>{item}</span>
              ))}
            </div>
          </section>

          {/* Pie charts */}
          <section className="panel">
            <h3>Типы целей</h3>
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={typePie} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label>
                  {typePie.map((_, i) => <Cell key={i} fill={palette[i % palette.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </section>

          <section className="panel">
            <h3>Стратегическая связка</h3>
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={alignPie} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label>
                  {alignPie.map((_, i) => <Cell key={i} fill={palette[i % palette.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </section>

          {/* Recommendations */}
          <section className="panel panel-wide">
            <h3>Рекомендации для руководителя</h3>
            {report.top_recommendations.length ? (
              <ul className="plain-list reco-list">
                {report.top_recommendations.map((rec, i) => (
                  <li key={i}>{rec}</li>
                ))}
              </ul>
            ) : (
              <div className="muted">Рекомендаций нет — целеполагание в хорошем состоянии.</div>
            )}
          </section>
        </>
      ) : (
        <section className="panel">
          <div className="empty-state">
            Нажмите «Построить отчёт зрелости» для комплексной оценки подразделения.
          </div>
        </section>
      )}
    </div>
  );
}
