from __future__ import annotations

from collections import Counter
from typing import Optional

from app.models.schemas import (
    AchievabilityCheck,
    AlignmentDistribution,
    BatchEvaluationResponse,
    BatchItemResult,
    CascadeEmployeeGoals,
    CascadeGoalsResponse,
    DashboardOverview,
    DepartmentSnapshot,
    EmployeeContextResponse,
    GeneratedGoal,
    GoalEvaluationResponse,
    GoalTypeDistribution,
    HealthResponse,
    IngestDocumentsResponse,
    MaturityReport,
    NotificationItem,
    NotificationsResponse,
    OkrMapping,
    SmartBreakdown,
    SmartDistribution,
    SourceEvidence,
)
from app.services.rules import (
    QUARTER_END_HINT,
    ROLE_METRIC_HINTS,
    find_action_verb,
    goal_word_count,
    has_measurement,
    has_specific_object,
    has_time_bound,
    has_unrealistic_metric,
    has_vague_language,
    hr_business_relevance_score,
    is_overloaded_goal,
    overlap_ratio,
    safe_mean,
    specificity_quality_score,
)
from app.vector.memory_vector import ChunkRecord, ScoredChunk
from app.services.llm import get_llm_service


class GoalEngine:
    def __init__(self, store, vector_store) -> None:
        self.store = store
        self.vector_store = vector_store
        self.llm = get_llm_service()
        self._eval_cache: dict[str, GoalEvaluationResponse] = {}
        self.index_documents()

    def index_documents(self) -> int:
        return self.vector_store.index_documents(self.store.list_documents())

    def health(self) -> HealthResponse:
        # Count extended tables if available
        goal_events_count = 0
        goal_reviews_count = 0
        kpi_count = 0
        goals_count = 0
        employees_count = 0
        try:
            goal_events_count = self.store.count_table_rows("goal_events")
            goal_reviews_count = self.store.count_table_rows("goal_reviews")
            kpi_count = self.store.count_table_rows("kpi_catalog")
            goals_count = self.store.count_table_rows("goals")
            employees_count = self.store.count_table_rows("employees")
        except Exception:
            pass

        has_dump = False
        try:
            has_dump = self.store.has_dump_data()
        except Exception:
            pass

        return HealthResponse(
            status="ok",
            mode="hackathon-dump" if has_dump else ("demo" if self.vector_store.backend_name == "memory" else "configured"),
            vector_backend=self.vector_store.backend_name,
            indexed_documents=len(self.store.list_documents()),
            indexed_chunks=len(getattr(self.vector_store, "chunks", [])),
            llm_enabled=self.llm.is_enabled,
            employees_count=employees_count,
            goals_count=goals_count,
            goal_events_count=goal_events_count,
            goal_reviews_count=goal_reviews_count,
            kpi_catalog_count=kpi_count,
        )

    def _build_source(self, chunk: Optional[ChunkRecord], query: str, search_score: Optional[float] = None) -> Optional[SourceEvidence]:
        if not chunk:
            return None
        score = search_score if search_score is not None else round(overlap_ratio(query, chunk.text), 4)
        return SourceEvidence(
            doc_id=chunk.doc_id,
            title=chunk.title,
            doc_type=chunk.doc_type,
            fragment=chunk.text,
            score=round(score, 4),
        )

    def _build_okr_mapping(self, goal_text: str, department_name: str) -> Optional[OkrMapping]:
        """Map goal to OKR framework. Uses LLM if available, else rule-based heuristic."""
        # Try LLM first
        llm_result = self.llm.map_to_okr(goal_text, department_name)
        if llm_result:
            return OkrMapping(
                objective=llm_result.get("objective", ""),
                key_results=llm_result.get("key_results", []),
                ambition_score=float(llm_result.get("ambition_score", 5)),
                transparency_score=float(llm_result.get("transparency_score", 5)),
                okr_recommendation=llm_result.get("okr_recommendation", ""),
            )

        # Rule-based fallback: extract OKR-like elements from goal text
        lower = goal_text.lower()

        # Infer Objective from alignment keywords
        if any(t in lower for t in ["стратег", "цифров", "трансформац"]):
            objective = "Цифровая трансформация HR-процессов"
        elif any(t in lower for t in ["обуч", "развит", "компетенц"]):
            objective = "Развитие человеческого капитала и компетенций"
        elif any(t in lower for t in ["текучест", "удержан", "вовлечён", "вовлечен"]):
            objective = "Повышение вовлечённости и удержание талантов"
        elif any(t in lower for t in ["затрат", "бюджет", "оптимиз", "эффектив"]):
            objective = "Повышение операционной эффективности"
        elif any(t in lower for t in ["рекрут", "подбор", "вакан"]):
            objective = "Обеспечение бизнеса квалифицированными кадрами"
        else:
            objective = "Операционное совершенствование HR-функции"

        # Extract Key Results from measurable parts
        key_results = []
        if has_measurement(goal_text):
            key_results.append(f"KR: {goal_text[:120]}")
        if "за счет" in lower:
            idx = lower.index("за счет")
            mechanism = goal_text[idx:idx + 80].strip().rstrip(".")
            key_results.append(f"KR: Реализовать {mechanism}")
        if not key_results:
            key_results.append("KR: Определить измеримый результат для данной цели")

        # Ambition = specificity * measurability heuristic
        spec = specificity_quality_score(goal_text)
        ambition = round(min(10, max(1, spec * 10 + (2 if has_measurement(goal_text) else 0))), 1)
        # Transparency = how well it cascades
        transparency = round(min(10, max(1, 5 + (2 if has_time_bound(goal_text) else 0) + (2 if has_measurement(goal_text) else 0))), 1)

        return OkrMapping(
            objective=objective,
            key_results=key_results,
            ambition_score=ambition,
            transparency_score=transparency,
            okr_recommendation="Для полноценного OKR-подхода рекомендуется выделить 2-3 измеримых Key Results и привязать цель к стратегическому Objective подразделения.",
        )

    def _smart_breakdown(self, goal_text: str, role_name: str, department_name: str, top_chunk: Optional[ChunkRecord], achievability_score: Optional[float] = None) -> SmartBreakdown:
        # ── Specific: use refined quality score ──
        specific = specificity_quality_score(goal_text)

        # ── Measurable: check for real metrics, penalise unrealistic ones ──
        if has_measurement(goal_text):
            measurable = 0.92
            if has_unrealistic_metric(goal_text):
                measurable = 0.55  # metric exists but is unrealistic
        else:
            measurable = 0.30

        # ── Achievable ──
        if achievability_score is not None:
            achievable = achievability_score
        elif has_unrealistic_metric(goal_text):
            achievable = 0.35  # unrealistic targets are not achievable
        elif is_overloaded_goal(goal_text):
            achievable = 0.45  # too many objectives
        elif "за счет" in goal_text.lower() or "на основе" in goal_text.lower():
            achievable = 0.82
        else:
            achievable = 0.58

        # ── Relevant: use HR/business relevance + role/dept overlap ──
        relevant = hr_business_relevance_score(goal_text)
        if role_name and overlap_ratio(goal_text, role_name) > 0:
            relevant = min(0.95, relevant + 0.05)
        if department_name and overlap_ratio(goal_text, department_name) > 0:
            relevant = min(0.95, relevant + 0.05)
        if top_chunk:
            chunk_overlap = overlap_ratio(goal_text, top_chunk.text + " " + " ".join(top_chunk.keywords))
            relevant = min(0.95, relevant + min(0.10, chunk_overlap))
        # Dampen relevance for poorly formed goals
        if has_unrealistic_metric(goal_text):
            relevant = min(relevant, 0.55)
        if is_overloaded_goal(goal_text):
            relevant = min(relevant, 0.55)

        # ── Time-bound ──
        timebound = 0.91 if has_time_bound(goal_text) else 0.28

        return SmartBreakdown(
            specific=round(specific, 2),
            measurable=round(measurable, 2),
            achievable=round(achievable, 2),
            relevant=round(relevant, 2),
            timebound=round(timebound, 2),
        )

    def _alignment_level(self, goal_text: str, chunk: Optional[ChunkRecord]) -> str:
        text = goal_text.lower()
        wc = goal_word_count(goal_text)
        has_obj = has_specific_object(goal_text)

        # Strategic keywords — classic + IT domain (§4.2: all employees are IT engineers)
        strategic_terms = [
            "стратег", "цифров", "трансформац", "прозрач",
            # IT strategic: reliability, security, platform stability
            "uptime", "sla", "доступност", "отказоустойч",
            "безопасност", "информационн", "импортозамещен",
            # Business impact
            "затрат", "эффектив", "рентабельн", "оптимизац",
            # Architecture / platform
            "архитектур", "платформ", "инфраструктур",
            # Data & analytics
            "data quality", "качеств данн", "аналитик",
        ]
        if any(term in text for term in strategic_terms) and wc >= 5 and has_obj:
            return "strategic"

        # Impact keywords with measurement — always strategic
        if any(term in text for term in ["снизить", "сократить", "увеличить", "повысить", "улучшить"]) \
                and has_measurement(goal_text) and has_obj:
            return "strategic"

        # Document-based alignment from vector search
        if chunk and chunk.doc_type in {"strategy", "manager_goal", "kpi_framework"} and wc >= 5 and has_obj:
            return "strategic"

        # Functional — KPI/training/coordination/IT operational with substance
        functional_terms = [
            "kpi", "okr", "обуч", "согласован", "компетенц", "performance", "оценк",
            "мониторинг", "инцидент", "тикет", "сервис", "деплой", "релиз",
            "тестирован", "разработ", "интеграц", "автоматизац",
        ]
        if any(term in text for term in functional_terms):
            return "functional"

        return "operational"

    def _goal_type(self, goal_text: str) -> str:
        lower = goal_text.lower()
        # Impact-based: measurable business outcome change
        if any(term in lower for term in ["снизить", "увеличить", "рост", "сократить", "повысить", "довести", "достичь"]) and has_measurement(goal_text):
            return "impact-based"
        # Output-based: deliver a concrete deliverable
        if any(term in lower for term in ["внедрить", "подготовить", "разработать", "запустить", "создать"]):
            return "output-based"
        return "activity-based"

    def _recommendations(self, breakdown: SmartBreakdown, goal_text: str = "") -> list[str]:
        recs: list[str] = []
        if breakdown.specific < 0.7:
            recs.append("Уточнить объект действия и ожидаемый результат без общих слов вроде 'улучшить'.")
        if breakdown.measurable < 0.7:
            recs.append("Добавить метрику: %, срок, количество, SLA или иной проверяемый показатель.")
        if breakdown.achievable < 0.7:
            recs.append("Добавить формулировку 'за счет' или указать управляемый механизм достижения результата.")
        if breakdown.relevant < 0.7:
            recs.append("Привязать цель к KPI подразделения, ВНД или цели руководителя.")
        if breakdown.timebound < 0.7:
            recs.append("Указать срок исполнения: дата, конец квартала или частоту выполнения.")
        # Extra checks
        if goal_text and is_overloaded_goal(goal_text):
            recs.append("Цель перегружена: разбейте на 2–3 отдельных цели с чёткими результатами.")
        if goal_text and has_unrealistic_metric(goal_text):
            recs.append("Метрика выглядит нереалистичной. Укажите достижимые показатели на основе исторических данных.")
        if goal_text and has_vague_language(goal_text):
            recs.append("Избегайте размытых формулировок ('попробовать', 'улучшить'). Используйте конкретный глагол действия с измеримым результатом.")
        return recs or ["Цель выглядит качественной. Добавить метрику базового и целевого значения для точного отслеживания прогресса."]

    def rewrite_goal(self, employee_id: str, goal_text: str, quarter: str, year: int = 2026) -> str:
        employee = self.store.get_employee(employee_id)
        if employee is None:
            raise ValueError("employee not found")
        position = self.store.get_position(employee.position_id)
        department = self.store.get_department(employee.department_id)
        role_name = (position.name if position else "").lower()

        # Try LLM rewrite first (richer, more natural language)
        scored_chunks = self.vector_store.search_scored(goal_text, employee.department_id, top_k=2)
        rag_context = None
        if scored_chunks:
            # Include title + doc_type for richer LLM context
            parts = []
            for sc in scored_chunks[:2]:
                parts.append(f"[{sc.chunk.doc_type}: {sc.chunk.title}] {sc.chunk.text}")
            rag_context = "\n".join(parts)

        llm_rewrite = self.llm.rewrite_goal(
            goal_text,
            role_name=position.name if position else "",
            department_name=department.name if department else "",
            quarter=quarter,
            year=year,
            rag_context=rag_context,
        )
        if llm_rewrite:
            return llm_rewrite

        # Rule-based fallback (deterministic template) — improved to avoid doubling
        hints = ROLE_METRIC_HINTS.get(role_name, {
            "metric": "согласованный KPI подразделения не ниже 90%",
            "business": "стандартизации процесса и контроля исполнения",
        })
        deadline = QUARTER_END_HINT.get(quarter, "до конца квартала")
        text = goal_text.strip().rstrip(".")
        if not find_action_verb(text):
            text = f"обеспечить {text[:1].lower() + text[1:]}" if text else "обеспечить достижение целевого показателя"
        if not has_time_bound(text):
            text = f"{deadline} {text}"
        if not has_measurement(text):
            text = f"{text} с достижением показателя: {hints['metric']}"
        # Fix: only add "за счет" if not already present (prevents doubling)
        if "за счет" not in text.lower() and "на основе" not in text.lower():
            business = hints["business"]
            # Remove leading "за счет" from the hint itself if present
            if business.lower().startswith("за счет "):
                business = business[8:]
            text = f"{text} за счет {business}"
        return text[:1].upper() + text[1:]

    def _check_achievability(self, goal_text: str, employee_id: str, quarter: str, year: int) -> AchievabilityCheck:
        """F-20: Check achievability by comparing with historical goals of same role / department."""
        employee = self.store.get_employee(employee_id)
        if employee is None:
            return AchievabilityCheck(is_achievable=True, confidence=0.0)

        # Gather historical goals for same position
        hist_pos = self.store.list_all_goals_for_position(
            employee.position_id, exclude_quarter=quarter, exclude_year=year
        )
        # Also gather from same department
        hist_dept = self.store.list_all_goals_for_department(
            employee.department_id, exclude_quarter=quarter, exclude_year=year
        )
        # Merge unique
        seen_ids: set[str] = set()
        all_historical: list = []
        for g in hist_pos + hist_dept:
            if g.id not in seen_ids:
                seen_ids.add(g.id)
                all_historical.append(g)

        if not all_historical:
            return AchievabilityCheck(is_achievable=True, confidence=0.3, similar_goals_found=0)

        # Find semantically similar historical goals
        similarities = [(g, overlap_ratio(goal_text, g.title)) for g in all_historical]
        similar = [(g, s) for g, s in similarities if s >= 0.15]
        similar.sort(key=lambda x: x[1], reverse=True)

        if not similar:
            return AchievabilityCheck(
                is_achievable=True,
                confidence=0.4,
                similar_goals_found=0,
                warning="Нет аналогичных целей в истории — невозможно оценить достижимость по данным прошлых периодов.",
            )

        # Evaluate historical similar goals
        hist_scores = []
        for g, sim in similar[:5]:
            breakdown = self._smart_breakdown(g.title, "", "", None)
            hist_scores.append(safe_mean([breakdown.specific, breakdown.measurable, breakdown.achievable, breakdown.relevant, breakdown.timebound]))

        avg_hist = safe_mean(hist_scores)
        # Current goal preliminary score
        curr_breakdown = self._smart_breakdown(goal_text, "", "", None)
        curr_score = safe_mean([curr_breakdown.specific, curr_breakdown.measurable, curr_breakdown.achievable, curr_breakdown.relevant, curr_breakdown.timebound])

        deviation = abs(curr_score - avg_hist)
        is_achievable = deviation < 0.3
        warning = None
        if not is_achievable:
            warning = (
                f"Цель значительно отклоняется от исторических аналогов "
                f"(средний SMART исторических целей: {round(avg_hist, 2)}, текущая: {round(curr_score, 2)}). "
                f"Возможно, цель нереалистична или требует корректировки."
            )

        # Compute achievability score for SMART breakdown
        base = 0.78 if ("за счет" in goal_text.lower() or "на основе" in goal_text.lower()) else 0.61
        if len(similar) >= 2:
            base = max(base, 0.70)  # Has precedent → boost confidence
        if not is_achievable:
            base = min(base, 0.50)  # Deviates too much → penalize

        return AchievabilityCheck(
            is_achievable=is_achievable,
            confidence=round(min(0.95, 0.5 + len(similar) * 0.1), 2),
            historical_avg_score=round(avg_hist, 2),
            similar_goals_found=len(similar),
            warning=warning,
        )

    def _build_kpi_context(self, department_id: str) -> Optional[str]:
        """Build a compact KPI context string for LLM prompts from the KPI catalog + timeseries."""
        try:
            kpis = self.store.get_kpi_for_department(department_id)
            if not kpis:
                return None
            lines = []
            for kpi in kpis[:8]:  # max 8 KPIs to keep context concise
                try:
                    ts_data = self.store.get_kpi_timeseries(kpi.id, department_id)
                    if ts_data:
                        # Latest value
                        latest = ts_data[-1]
                        unit = kpi.unit or ""
                        lines.append(f"- {kpi.name} ({kpi.id}): {round(latest.value, 2)} {unit} (последнее значение {latest.period})")
                    else:
                        lines.append(f"- {kpi.name} ({kpi.id}): {kpi.description}")
                except Exception:
                    lines.append(f"- {kpi.name}: {kpi.description}")
            return "KPI подразделения:\n" + "\n".join(lines) if lines else None
        except Exception:
            return None

    def evaluate_goal(self, employee_id: str, goal_text: str, quarter: str, year: int) -> GoalEvaluationResponse:
        # Check cache
        cache_key = f"{employee_id}|{goal_text}|{quarter}|{year}"
        if cache_key in self._eval_cache:
            return self._eval_cache[cache_key]

        employee = self.store.get_employee(employee_id)
        if employee is None:
            raise ValueError("employee not found")
        department = self.store.get_department(employee.department_id)
        position = self.store.get_position(employee.position_id)
        scored_chunks = self.vector_store.search_scored(goal_text, employee.department_id, top_k=2)
        top_chunk = scored_chunks[0].chunk if scored_chunks else None
        top_score = scored_chunks[0].score if scored_chunks else None

        # F-20: achievability check from historical data
        achievability = self._check_achievability(goal_text, employee_id, quarter, year)

        # Compute achievability score for SMART
        achievability_score: Optional[float] = None
        if achievability.similar_goals_found >= 2:
            base = 0.78 if ("за счет" in goal_text.lower() or "на основе" in goal_text.lower()) else 0.61
            base = max(base, 0.70)
            if not achievability.is_achievable:
                base = min(base, 0.50)
            achievability_score = base

        # ── LLM-based SMART evaluation (richer, semantic) ────────────
        score_explanations: Optional[dict] = None
        rag_context_eval: Optional[str] = None
        if scored_chunks:
            rag_context_eval = "\n".join(
                f"[{sc.chunk.doc_type}: {sc.chunk.title}] {sc.chunk.text}"
                for sc in scored_chunks[:2]
            )
        kpi_context = self._build_kpi_context(employee.department_id)

        llm_eval = self.llm.evaluate_smart(
            goal_text,
            role_name=position.name if position else "",
            department_name=department.name if department else "",
            rag_context=rag_context_eval,
            kpi_context=kpi_context,
        )

        if llm_eval:
            # Use LLM scores, but guard Achievable with historical data if available
            achievable_llm = llm_eval.get("achievable", 0.6)
            if achievability_score is not None:
                # Blend LLM achievability with historical signal
                achievable_llm = round((achievable_llm + achievability_score) / 2, 2)
            breakdown = SmartBreakdown(
                specific=round(llm_eval.get("specific", 0.5), 2),
                measurable=round(llm_eval.get("measurable", 0.5), 2),
                achievable=round(achievable_llm, 2),
                relevant=round(llm_eval.get("relevant", 0.5), 2),
                timebound=round(llm_eval.get("timebound", 0.5), 2),
            )
            score_explanations = {
                "specific": llm_eval.get("specific_why", ""),
                "measurable": llm_eval.get("measurable_why", ""),
                "achievable": llm_eval.get("achievable_why", ""),
                "relevant": llm_eval.get("relevant_why", ""),
                "timebound": llm_eval.get("timebound_why", ""),
            }
        else:
            # Rule-based fallback
            breakdown = self._smart_breakdown(
                goal_text,
                role_name=position.name if position else "",
                department_name=department.name if department else "",
                top_chunk=top_chunk,
                achievability_score=achievability_score,
            )

        overall = round(safe_mean([breakdown.specific, breakdown.measurable, breakdown.achievable, breakdown.relevant, breakdown.timebound]), 2)
        alignment = self._alignment_level(goal_text, top_chunk)
        goal_type = self._goal_type(goal_text)
        recs = self._recommendations(breakdown, goal_text)

        # Enrich recommendations with LLM criterion explanations for weak scores
        if score_explanations:
            threshold = 0.65
            criteria_map = {
                "specific": ("S (конкретность)", breakdown.specific),
                "measurable": ("M (измеримость)", breakdown.measurable),
                "achievable": ("A (достижимость)", breakdown.achievable),
                "relevant": ("R (релевантность)", breakdown.relevant),
                "timebound": ("T (срок)", breakdown.timebound),
            }
            for key, (label, score) in criteria_map.items():
                why = score_explanations.get(key, "")
                if score < threshold and why:
                    recs = [r for r in recs if label[:10] not in r]  # dedup
                    recs.insert(0, f"{label}: {why}")

        rewrite = self.rewrite_goal(employee_id, goal_text, quarter, year)
        source = self._build_source(top_chunk, goal_text, search_score=top_score)

        # OKR mapping via LLM (graceful degradation → rule-based fallback)
        okr_mapping = self._build_okr_mapping(goal_text, department.name if department else "")

        result = GoalEvaluationResponse(
            scores=breakdown,
            overall_score=overall,
            alignment_level=alignment,
            goal_type=goal_type,
            methodology="SMART+OKR" if okr_mapping else "SMART",
            recommendations=recs,
            rewrite=rewrite,
            source=source,
            achievability=achievability,
            okr_mapping=okr_mapping,
            score_explanations=score_explanations,
        )
        self._eval_cache[cache_key] = result
        return result

    def generate_goals(self, employee_id: str, quarter: str, year: int, count: int, focus: Optional[str] = None) -> list[GeneratedGoal]:
        employee = self.store.get_employee(employee_id)
        if employee is None:
            raise ValueError("employee not found")
        position = self.store.get_position(employee.position_id)
        dept = self.store.get_department(employee.department_id)
        manager = self.store.get_employee(employee.manager_id) if employee.manager_id else None
        retrieval_query = " ".join(filter(None, [position.name if position else "", dept.name if dept else "", focus or "", manager.full_name if manager else ""]))

        # §4.2: Enrich retrieval query with KPI context if available
        kpi_context_str: Optional[str] = None
        try:
            kpis = self.store.get_kpi_for_department(employee.department_id)
            if kpis:
                retrieval_query += " " + " ".join(k.name for k in kpis[:5])
                # Build rich KPI context for LLM: include actual recent values
                kpi_lines = []
                for kpi in kpis[:8]:
                    try:
                        ts = self.store.get_kpi_timeseries(kpi.id, employee.department_id)
                        if ts:
                            latest = ts[-1]
                            kpi_lines.append(
                                f"- {kpi.name} ({kpi.id}): {round(latest.value, 2)} {kpi.unit}"
                                f" — {kpi.description} (данные за {latest.period})"
                            )
                        else:
                            kpi_lines.append(f"- {kpi.name} ({kpi.id}): {kpi.description}")
                    except Exception:
                        kpi_lines.append(f"- {kpi.name}: {kpi.description}")
                if kpi_lines:
                    kpi_context_str = "Текущие KPI подразделения (используй эти значения как целевые ориентиры):\n" + "\n".join(kpi_lines)
        except Exception:
            pass

        # §4.2: Add employee project context
        try:
            projects = self.store.get_employee_projects(employee_id)
            if projects:
                retrieval_query += " " + " ".join(p.get("project_name", "") for p in projects[:3])
        except Exception:
            pass

        scored_results = self.vector_store.search_scored(retrieval_query, employee.department_id, top_k=max(count, 5))
        top_chunks = [sc.chunk for sc in scored_results]
        top_scores = {sc.chunk.chunk_id: sc.score for sc in scored_results}

        # Build enriched RAG context from retrieved chunks (include doc metadata)
        rag_parts: list[str] = []
        for sc in scored_results[:4]:
            c = sc.chunk
            kw_str = ", ".join(c.keywords) if c.keywords else ""
            rag_parts.append(
                f"[{c.doc_type}: {c.title}] {c.text}"
                + (f" (ключевые слова: {kw_str})" if kw_str else "")
            )
        # Append KPI context into RAG context for LLM generation
        if kpi_context_str:
            rag_parts.append(kpi_context_str)
        rag_context = "\n".join(rag_parts) if rag_parts else None

        # Gather manager goals for context
        manager_goals_text: list[str] = []
        if manager:
            mgr_goals = self.store.list_employee_goals(manager.id, quarter, year)
            for g in mgr_goals:
                manager_goals_text.append(g.title)

        # §3.2.2 step 4: Gather existing goals for duplicate detection
        existing_goals = self.store.list_employee_goals(employee_id, quarter, year)
        existing_titles = [g.title for g in existing_goals]

        # ── Try LLM generation first ──
        llm_goals = self.llm.generate_goals(
            role_name=position.name if position else "",
            department_name=dept.name if dept else "",
            quarter=quarter,
            year=year,
            count=count,
            focus=focus,
            rag_context=rag_context,
            manager_goals=manager_goals_text or None,
        )

        if llm_goals:
            # LLM succeeded — evaluate each generated goal
            results: list[GeneratedGoal] = []
            for idx, title in enumerate(llm_goals):
                # §3.2.2 step 4: Check for duplicates with existing goals
                is_duplicate = any(overlap_ratio(title, et) >= 0.65 for et in existing_titles)
                if is_duplicate:
                    continue  # Skip duplicate goals

                source_chunk = top_chunks[idx % len(top_chunks)] if top_chunks else None
                source_score = top_scores.get(source_chunk.chunk_id, 0.0) if source_chunk else None
                eval_result = self.evaluate_goal(employee_id, title, quarter, year)
                # Auto-rewrite if SMART score is too low
                final_title = title
                if eval_result.overall_score < 0.7:
                    final_title = self.rewrite_goal(employee_id, title, quarter, year)
                    eval_result = self.evaluate_goal(employee_id, final_title, quarter, year)

                # Build detailed rationale citing source documents
                rationale_parts = [f"Цель сгенерирована ИИ на основе роли ({position.name if position else 'N/A'})"]
                if source_chunk:
                    rationale_parts.append(f"документа «{source_chunk.title}» ({source_chunk.doc_type})")
                if manager_goals_text:
                    rationale_parts.append("целей руководителя")
                rationale = ", ".join(rationale_parts) + "."

                results.append(
                    GeneratedGoal(
                        title=final_title,
                        score=eval_result.overall_score,
                        alignment_level=eval_result.alignment_level,
                        goal_type=eval_result.goal_type,
                        methodology="SMART+OKR (LLM)",
                        rationale=rationale,
                        source=self._build_source(source_chunk, final_title, search_score=source_score) or SourceEvidence(
                            doc_id="N/A",
                            title="LLM-generated",
                            doc_type="llm",
                            fragment="Цель сгенерирована языковой моделью с учётом контекста ВНД",
                            score=0.0,
                        ),
                    )
                )
            return results[:count]

        # ── Fallback: expanded role-aware + RAG-aware templates ──
        hints = ROLE_METRIC_HINTS.get((position.name if position else "").lower(), {
            "metric": "согласованный KPI подразделения не ниже 90%",
            "business": "стандартизации процесса и контроля исполнения",
        })
        deadline = QUARTER_END_HINT.get(quarter, "до конца квартала")

        # Extract keywords from top RAG chunks for template enrichment
        rag_keywords: list[str] = []
        rag_doc_titles: list[str] = []
        for c in top_chunks[:3]:
            rag_keywords.extend(c.keywords)
            rag_doc_titles.append(c.title)

        # Core templates (always available)
        templates = [
            f"{deadline} обеспечить {hints['metric']} за счет {hints.get('business', 'системной работы с показателями')}.",
            f"{deadline} сократить средний срок согласования HR-заявок с 5 до 3 рабочих дней за счет цифровизации маршрута согласования.",
            f"{deadline} внедрить дашборд по статусу целей и обязательному обучению с еженедельным обновлением показателей.",
            f"{deadline} снизить долю просроченных обучений ниже 3% за счет автоматизации напоминаний и контроля статусов.",
            f"{deadline} повысить долю стратегически связанных целей сотрудников не ниже 80% на основе ВНД, KPI и целей руководителя.",
        ]

        # RAG-enriched templates: incorporate document context
        if rag_keywords:
            kw_sample = rag_keywords[:2]
            if "обучение" in rag_keywords or "компетенции" in rag_keywords:
                templates.append(f"{deadline} обеспечить прохождение обязательного обучения не менее 97% сотрудников за счет автоматизации контроля и напоминаний.")
            if "цифровизация" in rag_keywords or "HR" in rag_keywords:
                templates.append(f"{deadline} перевести не менее 3 ручных HR-процессов в цифровой формат за счет внедрения автоматизации и стандартизации workflow.")
            if "KPI" in rag_keywords or "цели" in rag_keywords:
                templates.append(f"{deadline} довести долю целей с привязкой к KPI подразделения до 90% за счет регулярных калибровочных сессий с руководителями.")
            if any(kw in rag_keywords for kw in ["подбор", "вакансии", "адаптация"]):
                templates.append(f"{deadline} сократить средний срок закрытия вакансий до 25 рабочих дней за счет оптимизации воронки подбора и автоматизации скрининга.")
            if any(kw in rag_keywords for kw in ["текучесть", "eNPS", "таланты"]):
                templates.append(f"{deadline} снизить текучесть ключевых сотрудников ниже 8% за счет программы удержания и развития карьерных треков.")
            if any(kw in rag_keywords for kw in ["компенсации", "бонусы", "ФОТ"]):
                templates.append(f"{deadline} обеспечить отклонение ФОТ от бюджета не более 3% за счет ежемесячного контроля и автоматизации расчётов.")
            if any(kw in rag_keywords for kw in ["оценка", "performance review", "калибровка"]):
                templates.append(f"{deadline} провести калибровочные сессии для 100% подразделений с формированием индивидуальных планов развития по итогам оценки.")
            if any(kw in rag_keywords for kw in ["безопасность", "персональные данные", "аудит"]):
                templates.append(f"{deadline} обеспечить прохождение обучения по информационной безопасности 100% сотрудников HR за счет интеграции с LMS и автоматических напоминаний.")

        # Role-specific bonus templates
        role_lower = (position.name if position else "").lower()
        if "recruiter" in role_lower:
            templates.append(f"{deadline} увеличить долю кандидатов из реферальной программы до 20% за счет запуска программы мотивации рекомендателей.")
        elif "analyst" in role_lower:
            templates.append(f"{deadline} автоматизировать не менее 80% регулярных HR-отчётов за счет настройки дашбордов и интеграции с HRIS.")
        elif "director" in role_lower:
            templates.append(f"{deadline} обеспечить каскадирование стратегических целей на 100% ключевых руководителей за счет проведения стратегических сессий и мониторинга привязки целей.")
        elif "project manager" in role_lower or "it" in role_lower:
            templates.append(f"{deadline} обеспечить выполнение SLA по HR-проектам не ниже 95% за счет внедрения Agile-спринтов и еженедельных ретроспектив.")

        results = []
        for idx in range(len(templates)):
            if len(results) >= count:
                break
            title = templates[idx % len(templates)]
            # §3.2.2 step 4: Skip if duplicate with existing goals
            if any(overlap_ratio(title, et) >= 0.65 for et in existing_titles):
                continue
            # Also skip if duplicate with already generated results
            if any(overlap_ratio(title, r.title) >= 0.65 for r in results):
                continue
            source_chunk = top_chunks[idx % len(top_chunks)] if top_chunks else None
            source_score = top_scores.get(source_chunk.chunk_id, 0.0) if source_chunk else None
            eval_result = self.evaluate_goal(employee_id, title, quarter, year)

            # Build rationale citing specific documents
            rationale = f"Цель сформирована на основе роли «{position.name if position else 'N/A'}»"
            if source_chunk:
                rationale += f", документа «{source_chunk.title}» ({source_chunk.doc_type})"
            rationale += " и приоритетов квартала."

            results.append(
                GeneratedGoal(
                    title=title,
                    score=eval_result.overall_score,
                    alignment_level=eval_result.alignment_level,
                    goal_type=eval_result.goal_type,
                    methodology="SMART (rule-based)",
                    rationale=rationale,
                    source=self._build_source(source_chunk, title, search_score=source_score) or SourceEvidence(
                        doc_id="N/A",
                        title="Synthetic source",
                        doc_type="synthetic",
                        fragment="Синтетический источник для demo-режима",
                        score=0.0,
                    ),
                )
            )
        return results

    def evaluate_batch(self, employee_id: str, quarter: str, year: int, goals: list[dict]) -> BatchEvaluationResponse:
        items: list[BatchItemResult] = []
        weakest_counter: Counter[str] = Counter()
        duplicates = 0
        duplicate_map: list[Optional[int]] = [None] * len(goals)
        for i in range(len(goals)):
            for j in range(i):
                if overlap_ratio(goals[i]["title"], goals[j]["title"]) >= 0.65:
                    duplicates += 1
                    duplicate_map[i] = j
                    break

        evaluations = []
        for idx, item in enumerate(goals):
            eval_result = self.evaluate_goal(employee_id, item["title"], quarter, year)
            evaluations.append(eval_result)
            criteria = {
                "specific": eval_result.scores.specific,
                "measurable": eval_result.scores.measurable,
                "achievable": eval_result.scores.achievable,
                "relevant": eval_result.scores.relevant,
                "timebound": eval_result.scores.timebound,
            }
            weakest_counter.update([min(criteria.items(), key=lambda x: x[1])[0]])
            items.append(
                BatchItemResult(
                    title=item["title"],
                    weight=item.get("weight"),
                    overall_score=eval_result.overall_score,
                    alignment_level=eval_result.alignment_level,
                    goal_type=eval_result.goal_type,
                    duplicate_of=duplicate_map[idx],
                )
            )

        total_weight = None
        if any(item.get("weight") is not None for item in goals):
            total_weight = round(sum(float(item.get("weight") or 0) for item in goals), 2)

        alerts: list[str] = []
        if len(goals) < 3:
            alerts.append("У сотрудника менее 3 целей на квартал.")
        if len(goals) > 5:
            alerts.append("У сотрудника более 5 целей на квартал.")
        if total_weight is not None and abs(total_weight - 100.0) > 0.01:
            alerts.append("Суммарный вес целей не равен 100%.")
        if duplicates > 0:
            alerts.append(f"Обнаружено дублирующихся целей: {duplicates}.")

        strategic_share = safe_mean([1.0 if e.alignment_level == "strategic" else 0.0 for e in evaluations])
        return BatchEvaluationResponse(
            goal_count=len(goals),
            average_smart_index=round(safe_mean([e.overall_score for e in evaluations]), 2),
            strategic_goal_share=round(strategic_share, 2),
            total_weight=total_weight,
            weakest_criteria=[name for name, _ in weakest_counter.most_common(3)],
            duplicates_found=duplicates,
            alerts=alerts,
            items=items,
        )

    def _fast_evaluate_goal_text(self, goal_text: str, role_name: str = "", dept_name: str = "") -> tuple[float, str, str]:
        """Fast SMART evaluation for dashboard aggregation (no RAG/LLM/history lookups).

        Returns: (overall_score, alignment_level, goal_type)
        """
        breakdown = self._smart_breakdown(goal_text, role_name, dept_name, top_chunk=None)
        overall = round(safe_mean([
            breakdown.specific, breakdown.measurable, breakdown.achievable,
            breakdown.relevant, breakdown.timebound,
        ]), 2)
        alignment = self._alignment_level(goal_text, None)
        goal_type = self._goal_type(goal_text)
        return overall, alignment, goal_type

    def dashboard_department(self, department_id: str, quarter: str, year: int) -> DepartmentSnapshot:
        dept = self.store.get_department(department_id)
        if dept is None:
            raise ValueError("department not found")

        # Get all goals for the department in one query (efficient for large datasets)
        dept_goals = self.store.list_department_goals(department_id, quarter, year)

        if not dept_goals:
            return DepartmentSnapshot(
                department_id=department_id,
                department_name=dept.name,
                avg_smart_score=0.0,
                strategic_goal_share=0.0,
                weakest_criterion="n/a",
                alert_count=0,
            )

        # Use fast scoring path for large datasets (> 20 goals), full scoring for small
        use_fast = len(dept_goals) > 20
        scores = []
        strategic_count = 0
        weakest_counter: Counter[str] = Counter()

        if use_fast:
            # Fast path: rule-based scoring without RAG/LLM
            for goal in dept_goals:
                overall, alignment, _ = self._fast_evaluate_goal_text(
                    goal.title, goal.position, dept.name,
                )
                scores.append(overall)
                if alignment == "strategic":
                    strategic_count += 1
                # Track weakest criteria via fast breakdown
                bd = self._smart_breakdown(goal.title, goal.position, dept.name, None)
                criteria = {"specific": bd.specific, "measurable": bd.measurable,
                            "achievable": bd.achievable, "relevant": bd.relevant, "timebound": bd.timebound}
                weakest_counter.update([min(criteria.items(), key=lambda x: x[1])[0]])
        else:
            # Full path for small datasets (demo mode)
            employee_ids = set(g.employee_id for g in dept_goals)
            batch_results = []
            for employee_id in employee_ids:
                emp_goals = [g for g in dept_goals if g.employee_id == employee_id]
                if not emp_goals:
                    continue
                batch = self.evaluate_batch(
                    employee_id, quarter, year,
                    [{"title": goal.title, "weight": goal.weight} for goal in emp_goals],
                )
                batch_results.append(batch)
            if batch_results:
                for result in batch_results:
                    weakest_counter.update(result.weakest_criteria[:1])
                scores = [item.average_smart_index for item in batch_results]
                strategic_count = sum(1 for item in batch_results if item.strategic_goal_share > 0.5)

        avg_smart = round(safe_mean(scores), 2)
        strategic_share = round(strategic_count / len(dept_goals), 2) if dept_goals else 0.0
        if not use_fast and scores:
            strategic_share = round(safe_mean([item.strategic_goal_share for item in batch_results]), 2)
        maturity_index = round(self._compute_maturity_index(avg_smart, strategic_share, len(set(g.employee_id for g in dept_goals))), 2)

        return DepartmentSnapshot(
            department_id=department_id,
            department_name=dept.name,
            avg_smart_score=avg_smart,
            strategic_goal_share=strategic_share,
            weakest_criterion=weakest_counter.most_common(1)[0][0] if weakest_counter else "n/a",
            alert_count=sum(1 for _ in dept_goals if _.weight and _.weight < 10),
            maturity_index=maturity_index,
            maturity_level=self._maturity_level(maturity_index),
        )

    def dashboard_overview(self, quarter: str, year: int) -> DashboardOverview:
        all_departments = list(self.store.departments.values())
        departments = []
        total_goals = 0
        for dep in all_departments:
            snapshot = self.dashboard_department(dep.id, quarter, year)
            departments.append(snapshot)
            # Count goals via the department goals query
            dept_goals = self.store.list_department_goals(dep.id, quarter, year)
            total_goals += len(dept_goals)
        return DashboardOverview(
            quarter=quarter,
            year=year,
            total_departments=len(departments),
            total_goals_evaluated=total_goals,
            avg_smart_score=round(safe_mean([d.avg_smart_score for d in departments if d.avg_smart_score > 0]), 2),
            strategic_goal_share=round(safe_mean([d.strategic_goal_share for d in departments if d.avg_smart_score > 0]), 2),
            departments=departments,
        )

    def employee_context(self, employee_id: str, quarter: str, year: int) -> EmployeeContextResponse:
        employee = self.store.get_employee(employee_id)
        if employee is None:
            raise ValueError("employee not found")
        department = self.store.get_department(employee.department_id)
        position = self.store.get_position(employee.position_id)
        manager = self.store.get_employee(employee.manager_id) if employee.manager_id else None

        # §4.2 extended context
        projects: list[dict] = []
        department_kpis: list[dict] = []
        goal_history_stats: dict = {}
        try:
            projects = self.store.get_employee_projects(employee_id)
        except Exception:
            pass
        try:
            kpis = self.store.get_kpi_for_department(employee.department_id)
            department_kpis = [{"id": k.id, "name": k.name, "unit": k.unit, "description": k.description} for k in kpis]
        except Exception:
            pass
        try:
            goal_history_stats = self.store.get_goal_history_stats(employee_id)
        except Exception:
            pass

        return EmployeeContextResponse(
            employee=employee,
            department=department,
            position=position,
            manager=manager,
            active_goals=self.store.list_employee_goals(employee_id, quarter, year),
            projects=projects,
            department_kpis=department_kpis,
            goal_history_stats=goal_history_stats,
        )

    def ingest_documents(self, documents) -> IngestDocumentsResponse:
        count = self.store.add_documents(documents)
        indexed_chunks = self.index_documents()
        return IngestDocumentsResponse(indexed_documents=count, indexed_chunks=indexed_chunks)

    # ── F-22: Maturity helpers ───────────────────────────────────────

    @staticmethod
    def _compute_maturity_index(avg_smart: float, strategic_share: float, employees_with_goals: int) -> float:
        """Integrated maturity index: weighted combination of quality dimensions."""
        coverage_bonus = min(0.15, employees_with_goals * 0.05)
        return min(1.0, avg_smart * 0.45 + strategic_share * 0.35 + coverage_bonus + 0.05)

    @staticmethod
    def _maturity_level(index: float) -> str:
        if index >= 0.8:
            return "продвинутый"
        if index >= 0.6:
            return "зрелый"
        if index >= 0.4:
            return "развивающийся"
        return "начальный"

    def maturity_report(self, department_id: str, quarter: str, year: int) -> MaturityReport:
        """F-22: Comprehensive maturity index for a department."""
        dept = self.store.get_department(department_id)
        if dept is None:
            raise ValueError("department not found")

        all_employees = self.store.list_employees(department_id)
        total_employees = len(all_employees)

        # Get all department goals in one query
        dept_goals = self.store.list_department_goals(department_id, quarter, year)
        employees_with_goals_ids: set[str] = set()
        
        # Use fast scoring for large datasets
        use_fast = len(dept_goals) > 20

        total_goals = len(dept_goals)
        smart_scores = []
        goal_types: list[str] = []
        alignments: list[str] = []
        criteria_sums: dict[str, float] = {"specific": 0, "measurable": 0, "achievable": 0, "relevant": 0, "timebound": 0}

        for goal in dept_goals:
            employees_with_goals_ids.add(goal.employee_id)
            if use_fast:
                bd = self._smart_breakdown(goal.title, goal.position, dept.name, None)
                overall = round(safe_mean([bd.specific, bd.measurable, bd.achievable, bd.relevant, bd.timebound]), 2)
                alignment = self._alignment_level(goal.title, None)
                goal_type = self._goal_type(goal.title)
                smart_scores.append(overall)
                goal_types.append(goal_type)
                alignments.append(alignment)
                criteria_sums["specific"] += bd.specific
                criteria_sums["measurable"] += bd.measurable
                criteria_sums["achievable"] += bd.achievable
                criteria_sums["relevant"] += bd.relevant
                criteria_sums["timebound"] += bd.timebound
            else:
                eval_result = self.evaluate_goal(goal.employee_id, goal.title, quarter, year)
                smart_scores.append(eval_result.overall_score)
                goal_types.append(eval_result.goal_type)
                alignments.append(eval_result.alignment_level)
                criteria_sums["specific"] += eval_result.scores.specific
                criteria_sums["measurable"] += eval_result.scores.measurable
                criteria_sums["achievable"] += eval_result.scores.achievable
                criteria_sums["relevant"] += eval_result.scores.relevant
                criteria_sums["timebound"] += eval_result.scores.timebound

        employees_with_goals = len(employees_with_goals_ids)

        if not smart_scores:
            return MaturityReport(
                department_id=department_id,
                department_name=dept.name,
                quarter=quarter,
                year=year,
                total_employees=total_employees,
                employees_with_goals=0,
                total_goals=0,
                maturity_level="начальный",
                top_recommendations=["Нет целей для анализа. Необходимо начать процесс целеполагания."],
            )

        n = len(smart_scores)

        # SMART distribution
        smart_dist = SmartDistribution()
        for sc in smart_scores:
            if sc >= 0.8:
                smart_dist.excellent += 1
            elif sc >= 0.6:
                smart_dist.good += 1
            else:
                smart_dist.needs_improvement += 1

        # Goal type distribution
        type_counter = Counter(goal_types)
        goal_type_dist = GoalTypeDistribution(
            impact_based=round(type_counter.get("impact-based", 0) / n, 2),
            output_based=round(type_counter.get("output-based", 0) / n, 2),
            activity_based=round(type_counter.get("activity-based", 0) / n, 2),
        )

        # Alignment distribution
        align_counter = Counter(alignments)
        alignment_dist = AlignmentDistribution(
            strategic=round(align_counter.get("strategic", 0) / n, 2),
            functional=round(align_counter.get("functional", 0) / n, 2),
            operational=round(align_counter.get("operational", 0) / n, 2),
        )

        # Weakest SMART criteria
        criteria_avgs = {k: v / n for k, v in criteria_sums.items()}
        weakest = sorted(criteria_avgs.items(), key=lambda x: x[1])[:3]

        # Aggregate scores
        avg_smart = round(safe_mean(smart_scores), 2)
        strategic_share = round(align_counter.get("strategic", 0) / n, 2)

        maturity_index = round(self._compute_maturity_index(avg_smart, strategic_share, employees_with_goals), 2)

        # Count alerts
        alert_count = 0
        for emp_id in employees_with_goals_ids:
            emp_goals = [g for g in dept_goals if g.employee_id == emp_id]
            if len(emp_goals) < 3:
                alert_count += 1
            if len(emp_goals) > 5:
                alert_count += 1
            weights = [g.weight for g in emp_goals if g.weight is not None]
            if weights and abs(sum(weights) - 100.0) > 0.01:
                alert_count += 1

        # Recommendations for the manager
        recs: list[str] = []
        if goal_type_dist.activity_based > 0.5:
            recs.append(f"Более {int(goal_type_dist.activity_based * 100)}% целей — activity-based. Рекомендуется переформулировать в результат-ориентированные (output/impact).")
        if alignment_dist.operational > 0.4:
            recs.append(f"Высокая доля операционных целей ({int(alignment_dist.operational * 100)}%). Усильте стратегическую привязку целей к ВНД и KPI.")
        if avg_smart < 0.6:
            recs.append("Средний SMART-индекс ниже 60%. Проведите обучение сотрудников по формулированию целей.")
        if strategic_share < 0.5:
            recs.append("Менее половины целей имеют стратегическую связку. Пересмотрите цели с привязкой к стратегии компании.")
        for crit_name, crit_val in weakest[:2]:
            if crit_val < 0.7:
                label_map = {"specific": "конкретность", "measurable": "измеримость", "achievable": "достижимость", "relevant": "релевантность", "timebound": "ограниченность во времени"}
                recs.append(f"Слабый критерий «{label_map.get(crit_name, crit_name)}» (средний: {round(crit_val, 2)}). Обратите внимание при постановке целей.")
        if employees_with_goals < total_employees:
            recs.append(f"У {total_employees - employees_with_goals} из {total_employees} сотрудников отсутствуют цели на квартал.")
        if not recs:
            recs.append("Подразделение демонстрирует зрелый уровень целеполагания. Поддерживайте текущий подход.")

        return MaturityReport(
            department_id=department_id,
            department_name=dept.name,
            quarter=quarter,
            year=year,
            maturity_index=maturity_index,
            maturity_level=self._maturity_level(maturity_index),
            total_employees=total_employees,
            employees_with_goals=employees_with_goals,
            total_goals=total_goals,
            avg_smart_score=avg_smart,
            strategic_goal_share=strategic_share,
            smart_distribution=smart_dist,
            goal_type_distribution=goal_type_dist,
            alignment_distribution=alignment_dist,
            weakest_criteria=[name for name, _ in weakest],
            top_recommendations=recs,
            alert_count=alert_count,
        )

    # ── Alert Manager: Notifications ──────────────────────────────────

    def notifications(self, quarter: str, year: int) -> NotificationsResponse:
        """Generate notifications for managers / employees / HR based on goal quality analysis.
        
        Optimized: uses fast scoring for large datasets and limits per-department processing.
        """
        items: list[NotificationItem] = []
        idx = 0

        all_departments = list(self.store.departments.values())

        for dept in all_departments:
            dept_employees = self.store.list_employees(dept.id)
            # Get all goals for the department in one query
            dept_goals = self.store.list_department_goals(dept.id, quarter, year)
            # Build employee → goals mapping
            emp_goals_map: dict[str, list] = {}
            for g in dept_goals:
                emp_goals_map.setdefault(g.employee_id, []).append(g)

            # Limit: for large departments, only process first 50 employees for notifications
            employees_to_process = dept_employees[:50] if len(dept_employees) > 50 else dept_employees

            for emp in employees_to_process:
                goals = emp_goals_map.get(emp.id, [])

                if not goals:
                    idx += 1
                    items.append(NotificationItem(
                        id=f"notif_{idx}", severity="warning", target_role="manager",
                        employee_id=emp.id, employee_name=emp.full_name,
                        department_id=dept.id, department_name=dept.name,
                        title="Нет целей на квартал",
                        message=f"У сотрудника {emp.full_name} ({dept.name}) отсутствуют цели на {quarter} {year}. Необходимо инициировать целеполагание.",
                        quarter=quarter, year=year,
                    ))
                    continue

                # Use fast scoring for large datasets
                use_fast = len(dept_goals) > 20
                if use_fast:
                    scores_list = []
                    strat_count = 0
                    for g in goals:
                        sc, al, _ = self._fast_evaluate_goal_text(g.title, g.position, dept.name)
                        scores_list.append(sc)
                        if al == "strategic":
                            strat_count += 1
                    avg_smart = safe_mean(scores_list)
                    strat_share = strat_count / len(goals) if goals else 0.0
                    alerts_list: list[str] = []
                    if len(goals) < 3:
                        alerts_list.append("У сотрудника менее 3 целей на квартал.")
                    if len(goals) > 5:
                        alerts_list.append("У сотрудника более 5 целей на квартал.")
                    weights = [g.weight for g in goals if g.weight is not None]
                    if weights and abs(sum(weights) - 100.0) > 0.01:
                        alerts_list.append("Суммарный вес целей не равен 100%.")
                else:
                    batch = self.evaluate_batch(
                        emp.id, quarter, year,
                        [{"title": g.title, "weight": g.weight} for g in goals],
                    )
                    avg_smart = batch.average_smart_index
                    strat_share = batch.strategic_goal_share
                    alerts_list = batch.alerts

                if avg_smart < 0.6:
                    idx += 1
                    items.append(NotificationItem(
                        id=f"notif_{idx}", severity="critical", target_role="manager",
                        employee_id=emp.id, employee_name=emp.full_name,
                        department_id=dept.id, department_name=dept.name,
                        title="Низкий индекс качества целей",
                        message=f"Средний SMART-индекс целей сотрудника {emp.full_name}: {round(avg_smart * 100)}%. Требуется доработка формулировок.",
                        quarter=quarter, year=year,
                    ))

                if strat_share < 0.3:
                    idx += 1
                    items.append(NotificationItem(
                        id=f"notif_{idx}", severity="warning", target_role="employee",
                        employee_id=emp.id, employee_name=emp.full_name,
                        department_id=dept.id, department_name=dept.name,
                        title="Слабая стратегическая связка",
                        message=f"Менее 30% целей {emp.full_name} имеют стратегическую привязку. Рекомендуется пересмотреть цели с учётом ВНД и стратегии.",
                        quarter=quarter, year=year,
                    ))

                for alert_text in alerts_list:
                    idx += 1
                    sev = "critical" if "менее 3" in alert_text.lower() or "не равен 100" in alert_text.lower() else "warning"
                    items.append(NotificationItem(
                        id=f"notif_{idx}", severity=sev, target_role="manager",
                        employee_id=emp.id, employee_name=emp.full_name,
                        department_id=dept.id, department_name=dept.name,
                        title="Алерт по набору целей",
                        message=f"{emp.full_name}: {alert_text}",
                        quarter=quarter, year=year,
                    ))

            # Department-level maturity check
            dept_emp_with_goals = [e for e in employees_to_process if e.id in emp_goals_map]
            if not dept_emp_with_goals:
                idx += 1
                items.append(NotificationItem(
                    id=f"notif_{idx}", severity="critical", target_role="hr",
                    department_id=dept.id, department_name=dept.name,
                    title="Низкая зрелость подразделения",
                    message=f"Подразделение «{dept.name}» не имеет целей на {quarter} {year}. Требуется внимание HR.",
                    quarter=quarter, year=year,
                ))

        # Sort: critical → warning → info
        priority = {"critical": 0, "warning": 1, "info": 2}
        items.sort(key=lambda x: priority.get(x.severity, 99))

        crit = sum(1 for i in items if i.severity == "critical")
        warn = sum(1 for i in items if i.severity == "warning")
        info = sum(1 for i in items if i.severity == "info")

        return NotificationsResponse(total=len(items), critical=crit, warnings=warn, info=info, items=items)

    # ── F-14: Cascade goals from manager ─────────────────────────────

    def cascade_goals(self, manager_id: str, quarter: str, year: int, count_per_employee: int = 3, focus: Optional[str] = None) -> CascadeGoalsResponse:
        """Generate cascaded goals for subordinates based on manager's own goals."""
        manager = self.store.get_employee(manager_id)
        if manager is None:
            raise ValueError("manager not found")

        manager_goals = self.store.list_employee_goals(manager_id, quarter, year)
        subordinates = self.store.list_subordinates(manager_id)

        if not subordinates:
            raise ValueError("no subordinates found for this manager")

        # Build focus from manager goals if not explicitly provided
        cascade_focus = focus or ""
        if manager_goals:
            cascade_focus += " " + " ".join(g.title for g in manager_goals)
        cascade_focus = cascade_focus.strip()

        result_subs: list[CascadeEmployeeGoals] = []
        total_generated = 0

        for sub in subordinates:
            position = self.store.get_position(sub.position_id)
            dept = self.store.get_department(sub.department_id)
            generated = self.generate_goals(sub.id, quarter, year, count_per_employee, cascade_focus)

            # Enhance rationale to explicitly reference manager goals
            enhanced: list[GeneratedGoal] = []
            for g in generated:
                rationale = g.rationale
                if manager_goals:
                    mgr_titles = "; ".join(mg.title[:60] for mg in manager_goals[:2])
                    rationale = f"Каскадирована от целей руководителя ({mgr_titles}). {rationale}"
                enhanced.append(g.model_copy(update={"rationale": rationale}))

            result_subs.append(CascadeEmployeeGoals(
                employee_id=sub.id,
                employee_name=sub.full_name,
                position=position.name if position else "",
                department=dept.name if dept else "",
                goals=enhanced,
            ))
            total_generated += len(enhanced)

        return CascadeGoalsResponse(
            manager_id=manager_id,
            manager_name=manager.full_name,
            manager_goals=manager_goals,
            subordinates=result_subs,
            total_generated=total_generated,
        )
