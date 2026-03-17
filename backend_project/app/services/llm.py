"""LLM integration layer for goal generation, rewriting and OKR mapping.

This module provides a graceful-degradation architecture:
- When OPENAI_API_KEY is set → uses LLM for generation, rewriting and OKR analysis
- When no key → falls back to deterministic rule-based templates (existing behavior)

The hybrid approach: SMART rules (deterministic, 100% accuracy) + LLM (semantic richness).
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── System prompts ───────────────────────────────────────────────────

_SYSTEM_GOAL_GENERATOR = """\
Ты — эксперт по управлению эффективностью персонала (Performance Management) в крупной компании.
Твоя задача — генерировать цели для сотрудников, которые соответствуют комбинированной методологии SMART + OKR:

SMART-критерии:
- Specific (конкретная): чёткий объект действия, конкретный глагол
- Measurable (измеримая): числовой KPI, %, срок, количество
- Achievable (достижимая): "за счет" механизм достижения
- Relevant (релевантная): привязка к KPI подразделения или стратегии компании
- Time-bound (ограниченная по времени): конкретная дата или квартал

OKR-элементы:
- Objective: амбициозная, но достижимая цель уровня подразделения/компании
- Key Result: 1-2 измеримых результата, доказывающих достижение цели

Правила формулировки:
1. Каждая цель — одно предложение на русском языке
2. Начинается с глагола действия (обеспечить, внедрить, снизить, повысить и т.д.)
3. Содержит числовую метрику (%, дни, количество)
4. Содержит дедлайн (дата или "до конца Qx")
5. Содержит "за счет" с описанием механизма
6. Связана с ролью сотрудника и стратегией компании
7. НЕ перегружена — одна цель = один результат
"""

_SYSTEM_REWRITER = """\
Ты — эксперт по формулировке целей в HR. Перепиши цель сотрудника так, чтобы она:
1. Соответствовала SMART-критериям (Specific, Measurable, Achievable, Relevant, Time-bound)
2. Содержала элементы OKR (привязка к стратегическому Objective + измеримый Key Result)
3. Начиналась с глагола действия (обеспечить, снизить, повысить, внедрить, сократить)
4. Содержала конкретную числовую метрику (%, дни, количество)
5. Содержала точный дедлайн — используй ТОЛЬКО тот год и квартал, который указан в контексте
6. Содержала механизм достижения ("за счет...")
7. Была на русском языке, профессиональной и лаконичной (1-2 предложения)
8. НЕ использовала выдуманные даты или годы — только указанный период

КРИТИЧЕСКИ ВАЖНО: если в контексте указан год 2026, используй 2026 в дедлайне.
Верни ТОЛЬКО переписанную цель, без пояснений.
"""

_SYSTEM_OKR_MAPPER = """\
Ты — эксперт по OKR (Objectives & Key Results) в области HR и управления персоналом.
Проанализируй цель сотрудника и определи:
1. К какому стратегическому Objective компании она относится (кратко, на русском)
2. Какие Key Results (2-3 шт.) можно вывести из этой цели (измеримые, конкретные)
3. Уровень амбициозности (1-10): насколько цель выходит за рамки текущей нормы
4. Уровень прозрачности/каскадируемости (1-10): можно ли объективно оценить прогресс

Ответ строго в JSON (без markdown, без ```):
{
  "objective": "Стратегический Objective компании",
  "key_results": ["KR1: ...", "KR2: ...", "KR3: ..."],
  "ambition_score": 7,
  "transparency_score": 8,
  "okr_recommendation": "Краткая рекомендация по улучшению с точки зрения OKR"
}
"""


class LLMService:
    """Wrapper around OpenAI API with graceful fallback."""

    def __init__(self) -> None:
        self._client = None
        self._model = settings.openai_model
        self._enabled = settings.llm_enabled

        if self._enabled:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=settings.openai_api_key)
                logger.info("LLM enabled: model=%s", self._model)
            except Exception as exc:
                logger.warning("Failed to initialize OpenAI client: %s — falling back to rules", exc)
                self._enabled = False
        else:
            logger.info("LLM disabled (no OPENAI_API_KEY). Using rule-based fallback.")

    @property
    def is_enabled(self) -> bool:
        return self._enabled and self._client is not None

    def _chat(self, system: str, user: str, temperature: float = 0.7, max_tokens: int = 1024) -> Optional[str]:
        """Make a chat completion call. Returns None on failure."""
        if not self.is_enabled or self._client is None:
            return None
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            return content.strip() if content else None
        except Exception as exc:
            logger.error("LLM call failed: %s", exc)
            return None

    def generate_goals(
        self,
        role_name: str,
        department_name: str,
        quarter: str,
        year: int,
        count: int,
        focus: Optional[str] = None,
        rag_context: Optional[str] = None,
        manager_goals: Optional[list[str]] = None,
    ) -> Optional[list[str]]:
        """Generate goals using LLM. Returns None if LLM is unavailable."""
        if not self.is_enabled:
            return None

        context_parts = [
            f"Должность сотрудника: {role_name}",
            f"Подразделение: {department_name}",
            f"Период: {quarter} {year}",
        ]
        if focus:
            context_parts.append(f"Фокус-приоритет: {focus}")
        if manager_goals:
            context_parts.append(f"Цели руководителя: {'; '.join(manager_goals)}")
        if rag_context:
            context_parts.append(f"Релевантные фрагменты ВНД/стратегии:\n{rag_context}")

        user_prompt = (
            f"{chr(10).join(context_parts)}\n\n"
            f"Сгенерируй {count} целей для этого сотрудника. "
            f"Каждая цель — отдельная строка, пронумерованная (1. 2. 3. и т.д.). "
            f"Не добавляй ничего кроме самих целей."
        )

        result = self._chat(_SYSTEM_GOAL_GENERATOR, user_prompt, temperature=0.8)
        if not result:
            return None

        # Parse numbered list
        goals: list[str] = []
        for line in result.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Remove numbering: "1. ", "1) ", "- "
            for prefix in [".", ")", "-", "•"]:
                if len(line) > 2 and line[0].isdigit() and prefix in line[:4]:
                    line = line[line.index(prefix) + 1:].strip()
                    break
            if line.startswith("- "):
                line = line[2:].strip()
            if len(line) > 20:  # Skip very short garbage
                goals.append(line)

        return goals[:count] if goals else None

    def rewrite_goal(
        self,
        goal_text: str,
        role_name: str,
        department_name: str,
        quarter: str,
        year: int = 2026,
        rag_context: Optional[str] = None,
    ) -> Optional[str]:
        """Rewrite a goal using LLM. Returns None if LLM is unavailable."""
        if not self.is_enabled:
            return None

        context_parts = [
            f"Исходная цель: {goal_text}",
            f"Должность: {role_name}",
            f"Подразделение: {department_name}",
            f"Период: {quarter} {year}",
            f"ВАЖНО: используй год {year} в дедлайне, не изобретай другой год.",
        ]
        if rag_context:
            context_parts.append(f"Контекст из ВНД/стратегии:\n{rag_context}")

        user_prompt = "\n".join(context_parts)
        result = self._chat(_SYSTEM_REWRITER, user_prompt, temperature=0.5)
        return result if result and len(result) > 20 else None

    def map_to_okr(self, goal_text: str, department_context: str = "") -> Optional[dict]:
        """Map a goal to OKR framework using LLM. Returns None if unavailable."""
        if not self.is_enabled:
            return None

        user_prompt = f"Цель: {goal_text}"
        if department_context:
            user_prompt += f"\nКонтекст подразделения: {department_context}"

        result = self._chat(_SYSTEM_OKR_MAPPER, user_prompt, temperature=0.3, max_tokens=512)
        if not result:
            return None

        # Parse JSON from LLM output
        try:
            # Handle markdown code blocks
            if "```" in result:
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
                result = result.strip()
            return json.loads(result)
        except (json.JSONDecodeError, IndexError):
            logger.warning("Failed to parse OKR JSON from LLM: %s", result[:200])
            return None


# Module-level singleton (lazy initialization)
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
