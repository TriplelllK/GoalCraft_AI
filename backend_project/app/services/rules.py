"""Deterministic helper functions for SMART evaluation, text processing and tokenization."""

from __future__ import annotations

import re
from typing import Sequence

# ── Constants ────────────────────────────────────────────────────────

QUARTER_END_HINT: dict[str, str] = {
    "Q1": "До 31.03",
    "Q2": "До 30.06",
    "Q3": "До 30.09",
    "Q4": "До 31.12",
}

ROLE_METRIC_HINTS: dict[str, dict[str, str]] = {
    "hr business partner": {
        "metric": "доля целей, привязанных к KPI подразделения, не ниже 85%",
        "business": "за счет систематического согласования целей с руководителями подразделений",
    },
    "learning and development specialist": {
        "metric": "доля сотрудников, прошедших обязательное обучение, не ниже 97%",
        "business": "за счет автоматизации напоминаний и еженедельного контроля статусов",
    },
    "production manager": {
        "metric": "снижение удельных операционных затрат на 5%",
        "business": "за счет оптимизации производственного планирования и цифровизации процессов",
    },
    "compensation and benefits specialist": {
        "metric": "доля ошибок в расчёте бонусов ниже 2%",
        "business": "за счет автоматизации проверки данных и стандартизации процедур расчёта",
    },
    "recruiter": {
        "metric": "средний срок закрытия вакансий не более 30 рабочих дней",
        "business": "за счет оптимизации воронки подбора и автоматизации скрининга кандидатов",
    },
    "hr analyst": {
        "metric": "доля автоматизированных HR-отчётов не менее 80%",
        "business": "за счет внедрения дашбордов и автоматизации сбора данных из HR-систем",
    },
    "hr director": {
        "metric": "рост доли стратегически связанных целей сотрудников не ниже 80%",
        "business": "за счет каскадирования целей и систематической калибровки с руководителями",
    },
    "it project manager": {
        "metric": "выполнение SLA по HR-проектам не ниже 95%",
        "business": "за счет внедрения методологии Agile и регулярного контроля спринтов",
    },
}

# ── Action verbs ─────────────────────────────────────────────────────

_ACTION_VERBS = [
    "обеспечить", "обеспечивать", "внедрить", "внедрять",
    "разработать", "разрабатывать", "сократить", "сокращать",
    "снизить", "снижать", "повысить", "повышать",
    "увеличить", "увеличивать", "подготовить", "подготавливать",
    "запустить", "запускать", "автоматизировать",
    "организовать", "организовывать", "провести", "проводить",
    "создать", "создавать", "оптимизировать",
    "реализовать", "реализовывать",
    "довести", "доводить", "перевести", "переводить",
    "достичь", "достигать", "достигнуть",
    "выполнить", "выполнять", "контролировать",
    "завершить", "завершать", "предоставить", "предоставлять",
]


def find_action_verb(text: str) -> str | None:
    """Return first action verb found in text or None."""
    lower = text.lower()
    for verb in _ACTION_VERBS:
        if verb in lower:
            return verb
    return None


# ── Measurement ──────────────────────────────────────────────────────

_MEASURE_PATTERN = re.compile(
    r"\d+\s*%|"
    r"\d+\s*(рабоч|дн|штук|раз|един|мин|час|сотрудн|процент|балл|шт|ед|"
    r"сесси|мероприят|документ|договор|должност|ваканс|заявк|модул|проект|тикет|позиц)|"
    r"\d+\s+\S+\s+(подраздел|должност|сотрудн|ваканс|документ|проект|модул|процесс)|"
    r"не\s+(ниже|менее|выше|более)\s+\d|"
    r"с\s+\d+\s+(до|на)\s+\d|"
    r"до\s+\d+\s+%|"
    r"\d+\s*\S*\s*(SLA|KPI|OKR)",
    re.IGNORECASE,
)


def has_measurement(text: str) -> bool:
    return bool(_MEASURE_PATTERN.search(text))


# ── Time bound ───────────────────────────────────────────────────────

_TIME_PATTERN = re.compile(
    r"до\s+\d{2}\.\d{2}|"
    r"до\s+конца\s+(Q[1-4]|квартал|года|месяц)|"
    r"до\s+\d{2}\.\d{2}\.\d{4}|"
    r"ежемесячн|еженедельн|ежеквартальн|"
    r"Q[1-4]|"
    r"\d{2}\.\d{2}\.\d{4}|"
    r"до\s+\d{1,2}\s+(январ|феврал|март|апрел|ма[яй]|июн|июл|август|сентябр|октябр|ноябр|декабр)",
    re.IGNORECASE,
)


def has_time_bound(text: str) -> bool:
    return bool(_TIME_PATTERN.search(text))


# ── Specificity quality ──────────────────────────────────────────────

_VAGUE_WORDS = [
    "улучшить", "лучше", "повысить эффективность", "работать лучше",
    "стараться", "попробовать", "попытаться", "было бы неплохо",
    "вроде бы", "наверное", "что-нибудь", "что-то", "как-нибудь",
    "какой-нибудь", "по мере необходимости", "по возможности",
]

_OBJECT_INDICATORS = re.compile(
    r"(заявк|заяво|ваканс|ваканц|сотрудн|обуч|процесс|систем|отчёт|отчет|дашборд|"
    r"документ|бюджет|план|проект|реглам|базу|данн|програм|платформ|"
    r"модул|интеграц|инструмент|показател|метрик|"
    r"аудит|сесси|мероприят|договор|рынок|рынк|матриц|анализ|реестр|"
    r"бизнес|кейс|портал|приложен|опрос|тестирован|терминал|зарплат|"
    r"миграц|воронк|компенсац|тикет|стажиров|лна|вебинар|бот|должност|"
    r"KPI|SLA|NPS|OKR|ERP|CRM|HRIS|LMS|RPA|SAP|ЛНА)",
    re.IGNORECASE,
)


def goal_word_count(text: str) -> int:
    """Count meaningful words in goal text."""
    return len(tokenize(text))


def is_overloaded_goal(text: str) -> bool:
    """Detect goals that pack too many separate objectives."""
    # Count action verbs — if 3+ different verbs present, likely overloaded
    lower = text.lower()
    found_verbs = [v for v in _ACTION_VERBS if v in lower]
    if len(found_verbs) >= 3:
        return True
    # Count comma-separated clauses
    clauses = [c.strip() for c in text.split(",") if len(c.strip()) > 10]
    if len(clauses) >= 4:
        return True
    return False


_UNREALISTIC_PATTERN = re.compile(
    r"в\s+(\d+)\s+раз|"       # "в 10 раз" — very aggressive multiplier
    r"полностью\s+исключ|"    # "полностью исключить ошибки"
    r"100\s*%\s*(удовлетвор|довольн|счастлив|исключ|отсутств)",  # 100% satisfaction etc
    re.IGNORECASE,
)

_LARGE_PERCENT = re.compile(r"(\d{3,})\s*%", re.IGNORECASE)
_COVERAGE_AFTER_100 = re.compile(
    r"100\s*%\s*(сотрудн|руковод|вакан|обуч|критич|подраздел|менедж|позиц|должн|укомплект|процедур|прохожден|кадров)",
    re.IGNORECASE,
)


def has_unrealistic_metric(text: str) -> bool:
    """Detect obviously unrealistic targets."""
    m = _UNREALISTIC_PATTERN.search(text)
    if m:
        # Check "в N раз" — unrealistic if N >= 5
        if m.group(1):
            try:
                multiplier = int(m.group(1))
                return multiplier >= 5
            except ValueError:
                pass
        return True
    # Check 3-digit percentages (100-999): unrealistic UNLESS it's coverage
    lp = _LARGE_PERCENT.search(text)
    if lp:
        pct = int(lp.group(1))
        if pct > 100:
            return True  # 150%, 200% etc. — always unrealistic
        if pct == 100 and _COVERAGE_AFTER_100.search(text):
            return False  # "100% сотрудников" — valid coverage
        if pct == 100:
            return True   # "100%" without coverage context — likely unrealistic
    return False


def has_vague_language(text: str) -> bool:
    """Detect vague, uncertain or informal phrasing."""
    lower = text.lower()
    return any(phrase in lower for phrase in _VAGUE_WORDS)


def has_specific_object(text: str) -> bool:
    """Check if goal mentions a concrete business object."""
    return bool(_OBJECT_INDICATORS.search(text))


def specificity_quality_score(text: str) -> float:
    """Return a refined specificity score (0.0–1.0) considering multiple factors."""
    score = 0.0
    # Action verb present
    if find_action_verb(text):
        score += 0.35
    # Has specific object
    if has_specific_object(text):
        score += 0.25
    # Sufficient length (at least 6 meaningful words)
    wc = goal_word_count(text)
    if wc >= 8:
        score += 0.20
    elif wc >= 5:
        score += 0.10
    elif wc <= 3:
        score -= 0.15  # very short goals lack specificity
    # Penalty for vague language
    if has_vague_language(text):
        score -= 0.20
    # Penalty for overloaded goal
    if is_overloaded_goal(text):
        score -= 0.15
    # Bonus for "за счет" (mechanism)
    if "за счет" in text.lower() or "на основе" in text.lower():
        score += 0.15
    return max(0.10, min(0.95, round(score, 2)))


# ── HR/business relevance keywords ──────────────────────────────────

_HR_KEYWORDS = [
    "рекрут", "адапт", "онбординг", "обуч", "развит", "компетенц",
    "грейд", "компенсац", "бонус", "вознагражд", "штатн", "кадров",
    "текучест", "вовлечённ", "вовлечен", "enps", "nps", "hris",
    "lms", "hr", "kpi", "okr", "sla", "performance", "assessment",
    "наставнич", "менторств", "карьер", "резерв", "преемств",
    "увольн", "exit", "трудов", "делопроизводств", "табельн",
    "зарплат", "расчёт", "расчет", "бюджет", "затрат", "стоимост",
    "вакан", "заявк", "стажир", "buddy", "документооборот",
    "руководител", "менеджер", "лидерск", "аудит", "сесси",
    "мероприят", "каскадирован", "целепол", "аттестац", "персонал",
    "укомплект", "отбор", "подбор", "ротаци", "мотивац",
    "лна", "рынк", "рынок", "корпоратив", "бренд работодат",
]


def hr_business_relevance_score(text: str) -> float:
    """Score 0.0–1.0 for HR/business relevance based on keyword density."""
    lower = text.lower()
    hits = sum(1 for kw in _HR_KEYWORDS if kw in lower)
    if hits >= 4:
        return 0.95
    if hits >= 3:
        return 0.88
    if hits >= 2:
        return 0.80
    if hits >= 1:
        return 0.72
    return 0.45


# ── Tokenizer ────────────────────────────────────────────────────────

_STOP_WORDS = frozenset({
    "и", "в", "на", "с", "по", "за", "к", "от", "из", "для", "не", "а",
    "но", "или", "до", "то", "что", "как", "это", "все", "при", "так",
    "же", "о", "об", "ко", "во", "со", "у", "ни", "бы", "ли", "без",
    "уже", "ещё", "еще", "его", "ее", "её", "их", "они", "мы", "вы",
})

_WORD_RE = re.compile(r"[а-яёa-z0-9]+", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase words, excluding stop words."""
    return [w for w in _WORD_RE.findall(text.lower()) if w not in _STOP_WORDS and len(w) > 2]


# ── Overlap ratio ────────────────────────────────────────────────────


def overlap_ratio(text_a: str, text_b: str) -> float:
    """Jaccard-like overlap ratio between two tokenized texts."""
    tokens_a = set(tokenize(text_a))
    tokens_b = set(tokenize(text_b))
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union) if union else 0.0


# ── Safe mean ────────────────────────────────────────────────────────


def safe_mean(values: Sequence[float]) -> float:
    """Mean that returns 0.0 for empty sequences."""
    if not values:
        return 0.0
    return sum(values) / len(values)


# ── Chunking ─────────────────────────────────────────────────────────


def chunk_text(content: str, max_chunk: int = 300, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks of approximately max_chunk characters."""
    content = content.strip()
    if not content:
        return []
    if len(content) <= max_chunk:
        return [content]
    chunks: list[str] = []
    start = 0
    while start < len(content):
        end = start + max_chunk
        chunk = content[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += max_chunk - overlap
    return chunks
