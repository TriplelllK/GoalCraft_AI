import { useState } from 'react';
import { api } from '../api';
import { KpiCard } from '../components/KpiCard';
import { SourceBox } from '../components/SourceBox';
import type { CascadeGoalsResponse } from '../types';

export function CascadePage() {
  const [managerId, setManagerId] = useState('emp_mgr');
  const [quarter, setQuarter] = useState('Q2');
  const [year, setYear] = useState(2026);
  const [count, setCount] = useState(3);
  const [focus, setFocus] = useState('');
  const [result, setResult] = useState<CascadeGoalsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleCascade() {
    setLoading(true);
    setError('');
    try {
      const data = await api.cascadeGoals({
        manager_id: managerId,
        quarter,
        year,
        count_per_employee: count,
        focus: focus || undefined,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка каскадирования');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-grid">
      <section className="panel panel-primary">
        <div className="panel-header">
          <div>
            <h2>Каскад целей от руководителя</h2>
            <p>
              Берёт цели руководителя и генерирует связанные цели для каждого подчинённого,
              учитывая должность, подразделение и ВНД.
            </p>
          </div>
        </div>

        <div className="form-grid two-columns">
          <label>
            Manager ID
            <input value={managerId} onChange={(e) => setManagerId(e.target.value)} />
          </label>
          <label>
            Количество целей на сотрудника
            <select value={count} onChange={(e) => setCount(Number(e.target.value))}>
              <option value={2}>2</option>
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
          Фокус квартала (опционально)
          <textarea rows={3} value={focus} onChange={(e) => setFocus(e.target.value)} placeholder="Оставьте пустым для автоматического определения" />
        </label>

        <div className="button-row">
          <button onClick={handleCascade} disabled={loading}>
            {loading ? 'Каскадирование...' : 'Каскадировать цели'}
          </button>
        </div>

        {error ? <div className="error-box">{error}</div> : null}
      </section>

      {result ? (
        <>
          {/* Manager goals summary */}
          <section className="panel">
            <h3>Цели руководителя: {result.manager_name}</h3>
            <div className="kpi-grid">
              <KpiCard label="Целей руководителя" value={`${result.manager_goals.length}`} />
              <KpiCard label="Подчинённых" value={`${result.subordinates.length}`} />
              <KpiCard label="Сгенерировано" value={`${result.total_generated}`} />
            </div>
            <div className="subtle-card stack-gap">
              <div className="muted">Цели менеджера</div>
              <ul className="plain-list">
                {result.manager_goals.map((g) => (
                  <li key={g.id}>{g.title}</li>
                ))}
              </ul>
            </div>
          </section>

          {/* Subordinate goals */}
          <section className="panel panel-wide">
            <h3>Каскадированные цели для подчинённых</h3>
            {result.subordinates.map((sub) => (
              <div className="cascade-employee-block" key={sub.employee_id}>
                <div className="cascade-employee-header">
                  <strong>{sub.employee_name}</strong>
                  <span className="muted">{sub.position} · {sub.department}</span>
                </div>
                <div className="goal-list">
                  {sub.goals.map((goal, idx) => (
                    <article className="goal-card" key={`${sub.employee_id}-${idx}`}>
                      <div className="goal-topline">
                        <span className="badge">{goal.alignment_level}</span>
                        <span className="badge badge-soft">{goal.goal_type}</span>
                        <span className="score-pill">SMART {Math.round(goal.score * 100)}%</span>
                      </div>
                      <h4>{goal.title}</h4>
                      <p>{goal.rationale}</p>
                      <SourceBox source={goal.source} />
                    </article>
                  ))}
                </div>
              </div>
            ))}
          </section>
        </>
      ) : (
        <section className="panel">
          <div className="empty-state">
            Нажмите «Каскадировать цели», чтобы сгенерировать связанные цели для всех подчинённых руководителя.
          </div>
        </section>
      )}
    </div>
  );
}
