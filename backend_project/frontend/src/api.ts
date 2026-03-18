import type {
  BatchEvaluationResponse,
  CascadeGoalsResponse,
  DashboardOverview,
  DataStats,
  DepartmentRef,
  DepartmentSnapshot,
  EmployeeContextResponse,
  EmployeeRef,
  GeneratedGoal,
  GoalEvaluationResponse,
  GoalHistoryResponse,
  HealthResponse,
  MaturityReport,
} from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {})
    },
    ...options
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const data = await response.json();
      detail = data?.detail || JSON.stringify(data);
    } catch {
      detail = await response.text();
    }
    throw new Error(detail || 'Request failed');
  }

  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<HealthResponse>('/health'),
  employeeContext: (employeeId: string, quarter: string, year: number) =>
    request<EmployeeContextResponse>(`/api/v1/employees/${employeeId}/context?quarter=${quarter}&year=${year}`),
  evaluateGoal: (payload: { employee_id: string; goal_text: string; quarter: string; year: number }) =>
    request<GoalEvaluationResponse>('/api/v1/goals/evaluate', { method: 'POST', body: JSON.stringify(payload) }),
  rewriteGoal: (payload: { employee_id: string; goal_text: string; quarter: string; year: number }) =>
    request<{ rewrite: string }>('/api/v1/goals/rewrite', { method: 'POST', body: JSON.stringify(payload) }),
  generateGoals: (payload: { employee_id: string; quarter: string; year: number; count: number; focus?: string }) =>
    request<GeneratedGoal[]>('/api/v1/goals/generate', { method: 'POST', body: JSON.stringify(payload) }),
  evaluateBatch: (payload: { employee_id: string; quarter: string; year: number; goals: { title: string; weight?: number | null }[] }) =>
    request<BatchEvaluationResponse>('/api/v1/goals/evaluate-batch', { method: 'POST', body: JSON.stringify(payload) }),
  dashboardOverview: (quarter: string, year: number) =>
    request<DashboardOverview>(`/api/v1/dashboard/overview?quarter=${quarter}&year=${year}`),
  departmentDashboard: (departmentId: string, quarter: string, year: number) =>
    request<DepartmentSnapshot>(`/api/v1/dashboard/departments/${departmentId}?quarter=${quarter}&year=${year}`),
  cascadeGoals: (payload: { manager_id: string; quarter: string; year: number; count_per_employee?: number; focus?: string }) =>
    request<CascadeGoalsResponse>('/api/v1/goals/cascade', { method: 'POST', body: JSON.stringify(payload) }),
  departmentMaturity: (departmentId: string, quarter: string, year: number) =>
    request<MaturityReport>(`/api/v1/dashboard/departments/${departmentId}/maturity?quarter=${quarter}&year=${year}`),
  listDepartments: () => request<DepartmentRef[]>('/api/v1/departments'),
  listEmployees: (departmentId?: string) =>
    request<EmployeeRef[]>(`/api/v1/employees${departmentId ? `?department_id=${departmentId}` : ''}`),
  dataStats: () => request<DataStats>('/api/v1/data/stats'),
  goalHistory: (goalId: string) => request<GoalHistoryResponse>(`/api/v1/goals/${goalId}/history`),
};
