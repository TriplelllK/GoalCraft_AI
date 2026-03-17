import { useEffect, useState } from 'react';
import { api } from '../api';
import { KpiCard } from '../components/KpiCard';
import { SourceBox } from '../components/SourceBox';
import type { EmployeeContextResponse, GeneratedGoal } from '../types';

export function GeneratePage() {
  const [employeeId, setEmployeeId] = useState('emp_1');
  const [quarter, setQuarter] = useState('Q2');
  const [year, setYear] = useState(2026);
  const [count, setCount] = useState(3);
  const [focus, setFocus] = useState('цифровизация HR-процессов и стратегическая связка целей');
  const [context, setContext] = useState<EmployeeContextResponse | null>(null);
  const [goals, setGoals] = useState<GeneratedGoal[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.employeeContext(employeeId, quarter, year)
      .then(setContext)
      .catch((err) => setError(err.message));
  }, [employeeId, quarter, year]);

  async function handleGenerate() {
    setLoading(true);
    setError('');
    try {
      const result = await api.generateGoals({ employee_id: employeeId, quarter, year, count, focus });
      setGoals(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сгенерировать цели.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-grid">
      <section className="panel panel-primary">
        <h2>Генерация целей по роли и контексту</h2>
        <p>Формируем 3–5 целей по сотруднику, учитывая ВНД, подразделение, роль и фокус квартала.</p>

        <div className="form-grid two-columns">
          <label>
            Employee ID
            <input value={employeeId} onChange={(e) => setEmployeeId(e.target.value)} />
          </label>
          <label>
            Количество целей
            <select value={count} onChange={(e) => setCount(Number(e.target.value))}>
              <option value={3}>3</option>
              <option value={4}>4</option>
              <option value={5}>5</option>
            </select>
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

        <label>
          Фокус квартала
          <textarea rows={4} value={focus} onChange={(e) => setFocus(e.target.value)} />
        </label>

        <div className="subtle-card">
          <div className="muted">Контекст сотрудника</div>
          <strong>{context?.employee.full_name || '—'}</strong>
          <div>{context?.position?.name || '—'} · {context?.department?.name || '—'}</div>
          <div className="muted">Менеджер: {context?.manager?.full_name || 'не указан'}</div>
        </div>

        <div className="button-row">
          <button onClick={handleGenerate} disabled={loading}>{loading ? 'Генерация...' : 'Сгенерировать цели'}</button>
        </div>

        {error ? <div className="error-box">{error}</div> : null}
      </section>

      <section className="panel panel-wide">
        <h3>Сгенерированные цели</h3>
        {goals.length ? (
          <div className="goal-list">
            {goals.map((goal) => (
              <article className="goal-card" key={`${goal.title}-${goal.source.doc_id}`}>
                <div className="goal-topline">
                  <span className="badge">{goal.alignment_level}</span>
                  <span className="badge badge-soft">{goal.goal_type}</span>
                  <span className="score-pill">SMART {Math.round(goal.score * 100)}%</span>
                </div>
                <h4>{goal.title}</h4>
                <p>{goal.rationale}</p>
                <div className="kpi-grid compact-grid">
                  <KpiCard label="Источник" value={goal.source.doc_type} />
                  <KpiCard label="Документ" value={goal.source.title} hint={goal.source.doc_id} />
                </div>
                <SourceBox source={goal.source} />
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">Нажмите «Сгенерировать цели», чтобы получить набор из 3–5 целей с источниками.</div>
        )}
      </section>
    </div>
  );
}
