# API contract test report

Passed: **10** / 10
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
  "llm_enabled": true
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
  ]
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
    "overall_score": 0.87,
    "alignment": "strategic"
  },
  {
    "name": "output_goal",
    "overall_score": 0.68,
    "alignment": "strategic"
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
      "Внедрить цифровую платформу для автоматизации HR-процессов, сократив их время на 20% до 30.06.2026 за счет использования новых технологий и программного обеспечения.",
      "Обеспечить 100% прозрачность исполнения обязательного обучения на дашборде сотрудников до конца Q2 2026 за счет регулярного мониторинга и обновления статусов обучения, что позволит снизить долю просроченных обучений до 0% к указанному сроку."
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
    "average_smart_index": 0.88,
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
    "strategic_goal_share": 0.11,
    "departments": [
      {
        "department_id": "dep_hr",
        "department_name": "HR / Production Block",
        "avg_smart_score": 0.8,
        "strategic_goal_share": 0.58,
        "weakest_criterion": "achievable",
        "alert_count": 1,
        "maturity_index": 0.71,
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
        "strategic_goal_share": 0.33,
        "weakest_criterion": "achievable",
        "alert_count": 0,
        "maturity_index": 0.57,
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
    "strategic_goal_share": 0.58,
    "weakest_criterion": "achievable",
    "alert_count": 1,
    "maturity_index": 0.71,
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
  "overall_score": 0.87
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
    "maturity_index": 0.72,
    "maturity_level": "зрелый",
    "total_goals": 5,
    "recommendations": [
      "Слабый критерий «достижимость» (средний: 0.65). Обратите внимание при постановке целей.",
      "У 1 из 3 сотрудников отсутствуют цели на квартал."
    ]
  }
]
```
