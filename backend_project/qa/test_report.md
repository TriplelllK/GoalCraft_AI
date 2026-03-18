# API contract test report

Passed: **15** / 15
Failed: **0**

## ✅ health
ok

```json
{
  "status": "ok",
  "mode": "demo",
  "vector_backend": "memory",
  "indexed_documents": 10,
  "indexed_chunks": 12,
  "llm_enabled": false,
  "employees_count": 6,
  "goals_count": 18,
  "goal_events_count": 0,
  "goal_reviews_count": 0,
  "kpi_catalog_count": 0
}
```

## ✅ employee_context
ok

```json
{
  "employee": {
    "id": "emp_1",
    "employee_code": "E0002",
    "full_name": "Aigerim S.",
    "email": "aigerim@example.com",
    "department_id": "dep_hr",
    "position_id": "pos_hrbp",
    "manager_id": "emp_mgr",
    "hire_date": "2024-02-01",
    "is_active": true
  },
  "department": {
    "id": "dep_hr",
    "name": "HR / Production Block",
    "code": "HR-PB",
    "parent_id": null,
    "is_active": true
  },
  "position": {
    "id": "pos_hrbp",
    "name": "HR Business Partner",
    "grade": "G10"
  },
  "manager": {
    "id": "emp_mgr",
    "employee_code": "E0001",
    "full_name": "Aidos S.",
    "email": "aidos@example.com",
    "department_id": "dep_hr",
    "position_id": "pos_mgr",
    "manager_id": null,
    "hire_date": "2023-01-10",
    "is_active": true
  },
  "active_goals": [
    {
      "id": "goal_demo_1",
      "employee_id": "emp_1",
      "department_id": "dep_hr",
      "position": "HR Business Partner",
      "title": "До конца Q2 довести долю целей, привязанных к KPI подразделения, до 85%",
      "goal_text": "До конца Q2 довести долю целей, привязанных к KPI подразделения, до 85%",
      "description": "",
      "metric": "доля целей привязанных к KPI >= 85%",
      "deadline": "2026-06-30",
      "status": "draft",
      "quarter": "Q2",
      "year": 2026,
      "weight": 50.0,
      "reviewer_comment": "",
      "created_at": "",
      "updated_at": ""
    },
    {
      "id": "goal_demo_2",
      "employee_id": "emp_1",
      "department_id": "dep_hr",
      "position": "HR Business Partner",
      "title": "До 30.06 сократить средний срок согласования HR-заявок с 5 до 3 рабочих дней",
      "goal_text": "До 30.06 сократить средний срок согласования HR-заявок с 5 до 3 рабочих дней",
      "description": "",
      "metric": "средний срок согласования <= 3 рабочих дней",
      "deadline": "2026-06-30",
      "status": "draft",
      "quarter": "Q2",
      "year": 2026,
      "weight": 50.0,
      "reviewer_comment": "",
      "created_at": "",
      "updated_at": ""
    }
  ],
  "projects": [],
  "department_kpis": [],
  "goal_history_stats": {
    "draft": 2,
    "approved": 5
  }
}
```

## ✅ documents_ingest
ok

```json
{
  "indexed_documents": 2,
  "indexed_chunks": 14
}
```

## ✅ evaluate_cases
ok

```json
[
  {
    "name": "weak_generic_goal",
    "overall_score": 0.42,
    "alignment": "functional"
  },
  {
    "name": "strategic_impact_goal",
    "overall_score": 0.88,
    "alignment": "strategic"
  },
  {
    "name": "output_goal",
    "overall_score": 0.68,
    "alignment": "strategic"
  },
  {
    "name": "unrealistic_goal_achievability",
    "overall_score": 0.49,
    "alignment": "operational"
  },
  {
    "name": "metric_without_deadline",
    "overall_score": 0.77,
    "alignment": "strategic"
  },
  {
    "name": "process_not_result",
    "overall_score": 0.53,
    "alignment": "functional"
  },
  {
    "name": "recruiter_strong_goal",
    "overall_score": 0.88,
    "alignment": "operational"
  }
]
```

## ✅ generate_cases
ok

```json
[
  {
    "name": "default_generation_hrbp",
    "count": 3,
    "sample_titles": [
      "До 30.06 обеспечить доля целей, привязанных к KPI подразделения, не ниже 85% за счет систематического согласования целей с руководителями подразделений.",
      "До 30.06 внедрить дашборд по статусу целей и обязательному обучению с еженедельным обновлением показателей."
    ]
  },
  {
    "name": "generate_for_recruiter",
    "count": 3,
    "sample_titles": [
      "До 30.06 обеспечить средний срок закрытия вакансий не более 30 рабочих дней за счет оптимизации воронки подбора и автоматизации скрининга кандидатов.",
      "До 30.06 сократить средний срок согласования HR-заявок с 5 до 3 рабочих дней за счет цифровизации маршрута согласования."
    ]
  },
  {
    "name": "generate_for_lnd_specialist",
    "count": 3,
    "sample_titles": [
      "До 30.06 обеспечить доля сотрудников, прошедших обязательное обучение, не ниже 97% за счет автоматизации напоминаний и еженедельного контроля статусов.",
      "До 30.06 сократить средний срок согласования HR-заявок с 5 до 3 рабочих дней за счет цифровизации маршрута согласования."
    ]
  },
  {
    "name": "generate_5_goals_max",
    "count": 5,
    "sample_titles": [
      "До 30.06 обеспечить доля автоматизированных HR-отчётов не менее 80% за счет внедрения дашбордов и автоматизации сбора данных из HR-систем.",
      "До 30.06 сократить средний срок согласования HR-заявок с 5 до 3 рабочих дней за счет цифровизации маршрута согласования."
    ]
  }
]
```

## ✅ batch_cases
ok

```json
[
  {
    "name": "balanced_two_goals",
    "average_smart_index": 0.89,
    "alerts": [
      "У сотрудника менее 3 целей на квартал."
    ]
  },
  {
    "name": "duplicates_and_wrong_weight",
    "average_smart_index": 0.42,
    "alerts": [
      "У сотрудника менее 3 целей на квартал.",
      "Суммарный вес целей не равен 100%.",
      "Обнаружено дублирующихся целей: 1."
    ]
  },
  {
    "name": "ideal_balanced_batch",
    "average_smart_index": 0.81,
    "alerts": []
  },
  {
    "name": "overloaded_six_goals",
    "average_smart_index": 0.76,
    "alerts": [
      "У сотрудника более 5 целей на квартал."
    ]
  }
]
```

## ✅ dashboard
ok

```json
{
  "overview": {
    "quarter": "Q2",
    "year": 2026,
    "total_departments": 8,
    "total_goals_evaluated": 11,
    "avg_smart_score": 0.3,
    "strategic_goal_share": 0.04,
    "departments": [
      {
        "department_id": "dep_hr",
        "department_name": "HR / Production Block",
        "avg_smart_score": 0.8,
        "strategic_goal_share": 0.34,
        "weakest_criterion": "achievable",
        "alert_count": 1,
        "maturity_index": 0.63,
        "maturity_level": "зрелый"
      },
      {
        "department_id": "dep_lnd",
        "department_name": "Learning & Development",
        "avg_smart_score": 0.0,
        "strategic_goal_share": 0.0,
        "weakest_criterion": "n/a",
        "alert_count": 0,
        "maturity_index": 0.0,
        "maturity_level": "начальный"
      },
      {
        "department_id": "dep_ops",
        "department_name": "Production Operations",
        "avg_smart_score": 0.0,
        "strategic_goal_share": 0.0,
        "weakest_criterion": "n/a",
        "alert_count": 0,
        "maturity_index": 0.0,
        "maturity_level": "начальный"
      },
      {
        "department_id": "dep_comp",
        "department_name": "Compensation & Benefits",
        "avg_smart_score": 0.77,
        "strategic_goal_share": 0.0,
        "weakest_criterion": "achievable",
        "alert_count": 0,
        "maturity_index": 0.45,
        "maturity_level": "развивающийся"
      },
      {
        "department_id": "dep_rec",
        "department_name": "Recruitment & Staffing",
        "avg_smart_score": 0.79,
        "strategic_goal_share": 0.0,
        "weakest_criterion": "achievable",
        "alert_count": 0,
        "maturity_index": 0.46,
        "maturity_level": "развивающийся"
      },
      {
        "department_id": "dep_fin",
        "department_name": "Finance & Budgeting",
        "avg_smart_score": 0.0,
        "strategic_goal_share": 0.0,
        "weakest_criterion": "n/a",
        "alert_count": 0,
        "maturity_index": 0.0,
        "maturity_level": "начальный"
      },
      {
        "department_id": "dep_it",
        "department_name": "IT & Digital",
        "avg_smart_score": 0.0,
        "strategic_goal_share": 0.0,
        "weakest_criterion": "n/a",
        "alert_count": 0,
        "maturity_index": 0.0,
        "maturity_level": "начальный"
      },
      {
        "department_id": "dep_legal",
        "department_name": "Legal & Compliance",
        "avg_smart_score": 0.0,
        "strategic_goal_share": 0.0,
        "weakest_criterion": "n/a",
        "alert_count": 0,
        "maturity_index": 0.0,
        "maturity_level": "начальный"
      }
    ]
  },
  "department": {
    "department_id": "dep_hr",
    "department_name": "HR / Production Block",
    "avg_smart_score": 0.8,
    "strategic_goal_share": 0.34,
    "weakest_criterion": "achievable",
    "alert_count": 1,
    "maturity_index": 0.63,
    "maturity_level": "зрелый"
  }
}
```

## ✅ achievability_check
ok

```json
{
  "achievability": {
    "is_achievable": true,
    "confidence": 0.7,
    "historical_avg_score": 0.79,
    "similar_goals_found": 2,
    "warning": null
  },
  "overall_score": 0.88
}
```

## ✅ cascade_goals
ok

```json
[
  {
    "name": "cascade_from_manager",
    "manager_goals": 3,
    "subordinates": [
      {
        "name": "Aigerim S.",
        "goals": 3
      },
      {
        "name": "Dana M.",
        "goals": 3
      },
      {
        "name": "Marat K.",
        "goals": 3
      },
      {
        "name": "Saltanat B.",
        "goals": 3
      },
      {
        "name": "Nurzhan T.",
        "goals": 3
      }
    ],
    "total_generated": 15
  }
]
```

## ✅ maturity_report
ok

```json
[
  {
    "name": "hr_department_maturity",
    "maturity_index": 0.65,
    "maturity_level": "зрелый",
    "total_goals": 5,
    "recommendations": [
      "Менее половины целей имеют стратегическую связку. Пересмотрите цели с привязкой к стратегии компании.",
      "Слабый критерий «достижимость» (средний: 0.65). Обратите внимание при постановке целей."
    ]
  },
  {
    "name": "lnd_department_maturity",
    "maturity_index": 0.45,
    "maturity_level": "развивающийся",
    "total_goals": 2,
    "recommendations": [
      "Высокая доля операционных целей (50%). Усильте стратегическую привязку целей к ВНД и KPI.",
      "Менее половины целей имеют стратегическую связку. Пересмотрите цели с привязкой к стратегии компании."
    ]
  }
]
```

## ✅ goal_history
ok

```json
{
  "goal_id": "goal_hr_001",
  "events": [],
  "reviews": [],
  "total_events": 0,
  "total_reviews": 0
}
```

## ✅ data_stats
ok

```json
{
  "departments": 8,
  "positions": 8,
  "employees": 6,
  "documents": 12,
  "goals": 18,
  "projects": 0,
  "systems": 0,
  "project_systems": 0,
  "employee_projects": 0,
  "goal_events": 0,
  "goal_reviews": 0,
  "kpi_catalog": 0,
  "kpi_timeseries": 0,
  "has_dump_data": false
}
```

## ✅ list_departments
ok

```json
[
  {
    "id": "dep_hr",
    "name": "HR / Production Block",
    "code": "HR-PB"
  },
  {
    "id": "dep_lnd",
    "name": "Learning & Development",
    "code": "LND"
  },
  {
    "id": "dep_ops",
    "name": "Production Operations",
    "code": "OPS"
  }
]
```

## ✅ list_employees
ok

```json
[
  {
    "id": "emp_mgr",
    "full_name": "Aidos S.",
    "department_id": "dep_hr",
    "department_name": "HR / Production Block",
    "position_id": "pos_mgr",
    "position_name": "Production Manager",
    "manager_id": null
  },
  {
    "id": "emp_1",
    "full_name": "Aigerim S.",
    "department_id": "dep_hr",
    "department_name": "HR / Production Block",
    "position_id": "pos_hrbp",
    "position_name": "HR Business Partner",
    "manager_id": "emp_mgr"
  },
  {
    "id": "emp_2",
    "full_name": "Dana M.",
    "department_id": "dep_lnd",
    "department_name": "Learning & Development",
    "position_id": "pos_lnd",
    "position_name": "Learning and Development Specialist",
    "manager_id": "emp_mgr"
  }
]
```

## ✅ notifications
ok

```json
{
  "total": 11,
  "critical": 6,
  "warnings": 5
}
```
