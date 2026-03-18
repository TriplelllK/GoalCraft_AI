import { useEffect, useState } from 'react';
import { api } from '../api';
import type { DepartmentRef } from '../types';

interface DepartmentPickerProps {
  value: string;
  onChange: (id: string) => void;
  label?: string;
}

export function DepartmentPicker({ value, onChange, label = 'Подразделение' }: DepartmentPickerProps) {
  const [departments, setDepartments] = useState<DepartmentRef[]>([]);

  useEffect(() => {
    api.listDepartments().then(setDepartments).catch(() => {});
  }, []);

  return (
    <label>
      {label}
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {departments.map((d) => (
          <option key={d.id} value={d.id}>
            {d.name} ({d.code})
          </option>
        ))}
      </select>
    </label>
  );
}
