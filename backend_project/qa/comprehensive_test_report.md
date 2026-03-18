# GoalCraft AI — Comprehensive QA Test Report

**Date**: 2026-03-18T12:32:51.042509
**Total Tests**: 61
**Passed**: 61 ✅
**Failed**: 0 ❌
**Pass Rate**: 100.0%
**Duration**: 21.93s

## §4.2 Data Volumes

| Table | Count |
|-------|------:|
| departments | 8 |
| positions | 25 |
| employees | 450 |
| documents | 160 |
| goals | 9,000 |
| projects | 34 |
| systems | 10 |
| project_systems | 65 |
| employee_projects | 886 |
| goal_events | 30,789 |
| goal_reviews | 4,305 |
| kpi_catalog | 13 |
| kpi_timeseries | 2,112 |
| **TOTAL** | **47,857** |

## Results by Category

### ✅ Schema Validation: 15/15

- ✅ **schema_departments_count** (0.0ms)
- ✅ **schema_positions_count** (0.0ms)
- ✅ **schema_employees_count** (0.0ms)
- ✅ **schema_documents_count** (0.0ms)
- ✅ **schema_goals_count** (0.0ms)
- ✅ **schema_goal_events_count** (0.0ms)
- ✅ **schema_goal_reviews_count** (0.0ms)
- ✅ **schema_kpi_catalog_count** (0.0ms)
- ✅ **schema_kpi_timeseries_count** (0.0ms)
- ✅ **schema_projects_count** (0.0ms)
- ✅ **schema_employee_projects_count** (0.0ms)
- ✅ **schema_employee_referential_integrity** (0.1ms)
- ✅ **schema_goal_employee_integrity** (0.1ms)
- ✅ **schema_manager_hierarchy** (0.1ms)
- ✅ **schema_has_dump_data** (0.0ms)

### ✅ API Contracts: 21/21

- ✅ **api_health** (26.5ms)
- ✅ **api_departments** (3.0ms)
- ✅ **api_employees_list** (6.6ms)
- ✅ **api_employees_filter_by_dept** (3.4ms)
- ✅ **api_employee_context** (15.5ms)
- ✅ **api_employee_context_404** (2.6ms)
- ✅ **api_data_stats** (2.3ms)
- ✅ **api_evaluate_good_goal** (22.8ms)
- ✅ **api_evaluate_bad_goal** (13.7ms)
- ✅ **api_generate_goals** (57.6ms)
- ✅ **api_evaluate_batch** (37.3ms)
- ✅ **api_batch_weight_alert** (26.8ms)
- ✅ **api_dashboard_overview** (17407.8ms)
- ✅ **api_department_snapshot** (31.1ms)
- ✅ **api_department_404** (2.5ms)
- ✅ **api_maturity_report** (4.8ms)
- ✅ **api_goal_history** (5.7ms)
- ✅ **api_cascade_goals** (3325.1ms)
- ✅ **api_notifications** (32.2ms)
- ✅ **api_ingest_documents** (50.6ms)
- ✅ **api_rewrite_goal** (4.7ms)

### ✅ Performance: 6/6

- ✅ **perf_health_under_100ms** (1.9ms)
- ✅ **perf_evaluate_under_2s** (21.1ms)
- ✅ **perf_generate_under_5s** (6.5ms)
- ✅ **perf_departments_list_under_200ms** (2.3ms)
- ✅ **perf_employees_list_under_500ms** (6.4ms)
- ✅ **perf_data_stats_under_200ms** (2.7ms)

### ✅ Edge Cases: 8/8

- ✅ **edge_empty_goal_text** (13.8ms)
- ✅ **edge_very_long_goal** (191.7ms)
- ✅ **edge_special_characters** (17.6ms)
- ✅ **edge_nonexistent_employee_evaluate** (2.5ms)
- ✅ **edge_invalid_quarter** (2.8ms)
- ✅ **edge_batch_empty_goals** (2.2ms)
- ✅ **edge_batch_duplicate_goals** (2.1ms)
- ✅ **edge_cascade_no_subordinates** (3.0ms)

### ✅ Data Integrity: 6/6

- ✅ **integrity_all_depts_have_employees** (0.1ms)
- ✅ **integrity_all_depts_have_goals** (4.1ms)
- ✅ **integrity_goal_status_distribution** (0.9ms)
- ✅ **integrity_goal_weight_sum** (11.7ms)
- ✅ **integrity_kpi_timeseries_coverage** (0.1ms)
- ✅ **integrity_employee_projects_valid** (0.0ms)

### ✅ Cross-Module: 3/3

- ✅ **cross_dashboard_matches_goals** (379.8ms)
- ✅ **cross_maturity_all_departments** (51.4ms)
- ✅ **cross_employee_context_all_fields** (18.6ms)

### ✅ SMART Accuracy: 2/2

- ✅ **accuracy_good_goals_score_high** (44.2ms)
- ✅ **accuracy_bad_goals_score_low** (51.8ms)
