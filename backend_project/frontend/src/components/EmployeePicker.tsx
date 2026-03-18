import { useEffect, useState } from 'react';
import { api } from '../api';
import type { EmployeeRef } from '../types';

interface EmployeePickerProps {
  value: string;
  onChange: (id: string) => void;
  label?: string;
  /** Filter by manager_id — show only employees with this manager */
  managersOnly?: boolean;
}

export function EmployeePicker({ value, onChange, label = 'Сотрудник', managersOnly = false }: EmployeePickerProps) {
  const [employees, setEmployees] = useState<EmployeeRef[]>([]);

  useEffect(() => {
    api.listEmployees().then((list) => {
      const filtered = managersOnly
        ? list.filter((e) => list.some((sub) => sub.manager_id === e.id))
        : list;
      setEmployees(filtered);
      // Auto-select first employee if current value is not in the list
      if (filtered.length && !filtered.some((e) => e.id === value)) {
        onChange(filtered[0].id);
      }
    }).catch(() => {});
  }, [managersOnly]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <label>
      {label}
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {employees.map((emp) => (
          <option key={emp.id} value={emp.id}>
            {emp.full_name} — {emp.position_name} ({emp.department_name})
          </option>
        ))}
      </select>
    </label>
  );
}
