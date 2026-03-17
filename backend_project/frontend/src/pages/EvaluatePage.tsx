import { useEffect, useMemo, useState } from 'react';
import { api } from '../api';
import { KpiCard } from '../components/KpiCard';
import { ProgressBar } from '../components/ProgressBar';
import { SourceBox } from '../components/SourceBox';
import type { BatchEvaluationResponse, EmployeeContextResponse, GoalEvaluationResponse } from '../types';

const defaultQuarter = 'Q2';
const defaultYear = 2026;
const defaultEmployeeId = 'emp_1';
const defaultGoal = 'Улучшить процесс обучения сотрудников';

export function EvaluatePage() {
  const [employeeId, setEmployeeId] = useState(defaultEmployeeId);
  const [quarter, setQuarter] = useState(defaultQuarter);
  const [year, setYear] = useState(defaultYear);
  const [goalText, setGoalText] = useState(defaultGoal);
  const [evaluation, setEvaluation] = useState<GoalEvaluationResponse | null>(null);
  const [context, setContext] = useState<EmployeeContextResponse | null>(null);
  const [batch, setBatch] = useState<BatchEvaluationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.employeeContext(employeeId, quarter, year)
      .then(setContext)
      .catch((err) => setError(err.message));
  }, [employeeId, quarter, year]);

  const activeGoalsForBatch = useMemo(
    () => (context?.active_goals || []).map((goal) => ({ title: goal.title, weight: goal.weight ?? undefined })),
    [context]
  );

  async function handleEvaluate() {
    setLoading(true);
    setError('');
    try {
      const result = await api.evaluateGoal({ employee_id: employeeId, goal_text: goalText, quarter, year });
      setEvaluation(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось выполнить оценку цели.');
    } finally {
      setLoading(false);
    }
  }

  async function handleBatch() {
    if (!activeGoalsForBatch.length) {
      setError('У сотрудника нет активных целей для пакетной оценки.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const result = await api.evaluateBatch({ employee_id: employeeId, quarter, year, goals: activeGoalsForBatch });
      setBatch(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось оценить набор целей.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-grid">
      <section className="panel panel-primary">
        <div className="panel-header">
          <div>
            <h2>Оценка цели сотрудника</h2>
            <p>Проверка SMART, стратегической связки, типа цели и предложение улучшенной формулировки.</p>
          </div>
        </div>

        <div className="form-grid two-columns">
          <label>
            Employee ID
            <input value={employeeId} onChange={(e) => setEmployeeId(e.target.value)} />
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
          <div className="context-box subtle-card">
            <div className="muted">Контекст из backend</div>
            <strong>{context?.employee.full_name || '—'}</strong>
            <div>{context?.position?.name || '—'}</div>
            <div>{context?.department?.name || '—'}</div>
          </div>
        </div>

        <label>
          Текст цели
          <textarea rows={7} value={goalText} onChange={(e) => setGoalText(e.target.value)} />
        </label>

        <div className="button-row">
          <button onClick={handleEvaluate} disabled={loading}>{loading ? 'Оценка...' : 'Оценить цель'}</button>
          <button className="secondary" onClick={handleBatch} disabled={loading}>Оценить текущий набор целей</button>
        </div>

        {error ? <div className="error-box">{error}</div> : null}
      </section>

      <section className="panel">
        <h3>Результат оценки</h3>
        {evaluation ? (
          <>
            <div className="kpi-grid">
              <KpiCard label="Итоговый индекс" value={`${Math.round(evaluation.overall_score * 100)}%`} />
              <KpiCard label="Уровень связки" value={evaluation.alignment_level} />
              <KpiCard label="Тип цели" value={evaluation.goal_type} />
            </div>

            <div className="subtle-card stack-gap">
              <ProgressBar label="Specific" value={evaluation.scores.specific} />
              <ProgressBar label="Measurable" value={evaluation.scores.measurable} />
              <ProgressBar label="Achievable" value={evaluation.scores.achievable} />
              <ProgressBar label="Relevant" value={evaluation.scores.relevant} />
              <ProgressBar label="Time-bound" value={evaluation.scores.timebound} />
            </div>

            <div className="subtle-card">
              <h4>Рекомендации</h4>
              <ul className="plain-list">
                {evaluation.recommendations.map((rec) => <li key={rec}>{rec}</li>)}
              </ul>
            </div>

            <div className="subtle-card">
              <h4>AI rewrite</h4>
              <p>{evaluation.rewrite}</p>
            </div>

            {evaluation.achievability ? (
              <div className="subtle-card stack-gap">
                <h4>Проверка достижимости (F-20)</h4>
                <div className="kpi-grid compact-grid">
                  <KpiCard label="Достижима?" value={evaluation.achievability.is_achievable ? 'Да' : 'Нет'} />
                  <KpiCard label="Уверенность" value={`${Math.round(evaluation.achievability.confidence * 100)}%`} />
                  <KpiCard label="Похожих целей" value={`${evaluation.achievability.similar_goals_found}`} />
                  {evaluation.achievability.historical_avg_score != null ? (
                    <KpiCard label="Ист. средний" value={`${Math.round(evaluation.achievability.historical_avg_score * 100)}%`} />
                  ) : null}
                </div>
                {evaluation.achievability.warning ? (
                  <div className="error-box">{evaluation.achievability.warning}</div>
                ) : null}
              </div>
            ) : null}

            {evaluation.okr_mapping ? (
              <div className="subtle-card stack-gap">
                <h4>OKR-маппинг · <span className="tag">{evaluation.methodology}</span></h4>
                <div className="kpi-grid compact-grid">
                  <KpiCard label="Амбициозность" value={`${evaluation.okr_mapping.ambition_score}/10`} />
                  <KpiCard label="Прозрачность" value={`${evaluation.okr_mapping.transparency_score}/10`} />
                </div>
                <div><strong>Objective:</strong> {evaluation.okr_mapping.objective}</div>
                <ul className="plain-list">
                  {evaluation.okr_mapping.key_results.map((kr) => <li key={kr}>{kr}</li>)}
                </ul>
                {evaluation.okr_mapping.okr_recommendation ? (
                  <div className="muted">{evaluation.okr_mapping.okr_recommendation}</div>
                ) : null}
              </div>
            ) : null}

            <SourceBox source={evaluation.source} />
          </>
        ) : (
          <div className="empty-state">Введите цель и нажмите «Оценить цель».</div>
        )}
      </section>

      <section className="panel panel-wide">
        <h3>Пакетная оценка текущих целей сотрудника</h3>
        {context?.active_goals?.length ? (
          <div className="subtle-card">
            <div className="muted">Текущие цели из backend</div>
            <ul className="plain-list">
              {context.active_goals.map((goal) => (
                <li key={goal.id}>{goal.title} {goal.weight ? `· вес ${goal.weight}%` : ''}</li>
              ))}
            </ul>
          </div>
        ) : null}

        {batch ? (
          <div className="batch-layout">
            <div className="kpi-grid">
              <KpiCard label="Количество целей" value={`${batch.goal_count}`} />
              <KpiCard label="Средний SMART" value={`${Math.round(batch.average_smart_index * 100)}%`} />
              <KpiCard label="Strategic share" value={`${Math.round(batch.strategic_goal_share * 100)}%`} />
              <KpiCard label="Total weight" value={batch.total_weight != null ? `${batch.total_weight}%` : '—'} />
            </div>
            <div className="subtle-card">
              <h4>Алерты</h4>
              {batch.alerts.length ? (
                <ul className="plain-list">{batch.alerts.map((alert) => <li key={alert}>{alert}</li>)}</ul>
              ) : (
                <div className="muted">Критичных алертов нет.</div>
              )}
            </div>
            <div className="subtle-card">
              <h4>Слабые критерии</h4>
              <div className="tag-row">
                {batch.weakest_criteria.map((item) => <span className="tag" key={item}>{item}</span>)}
              </div>
            </div>
          </div>
        ) : (
          <div className="empty-state">Нажмите «Оценить текущий набор целей», чтобы проверить комплектность, суммарный вес и дубли.</div>
        )}
      </section>
    </div>
  );
}
