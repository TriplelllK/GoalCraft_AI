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
    api.listDepartments().then((list) => {
      setDepartments(list);
      // Auto-select first department if current value is not in the list
      if (list.length && !list.some((d) => d.id === value)) {
        onChange(list[0].id);
      }
    }).catch(() => {});
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

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
