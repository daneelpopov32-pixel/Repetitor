"""
EGE History variant template — official FIPI specification 2025.

Source: ИС-11 ЕГЭ 2025 СПЕЦ.pdf, Приложение (обобщённый план варианта).
Structure: 21 tasks, 210 minutes, 42 max primary points.

Part 1 (tasks 1-12): Short answer, 20 points max
Part 2 (tasks 13-21): Extended answer, 22 points max
"""

EGE_HISTORY_TEMPLATE = [
    # === PART 1: Short answer (12 tasks, max 20 points) ===
    # Task 1: Matching (dates) — 2pts, Basic
    {"position": 1, "task_type": "matching", "description": "Знание дат (соответствие)", "max_points": 2, "level": "basic", "allowed_types": ["TEST"], "allowed_subtypes": ["matching"]},
    # Task 2: Sequence — 1pt, Basic
    {"position": 2, "task_type": "sequence", "description": "Систематизация (последовательность событий)", "max_points": 1, "level": "basic", "allowed_types": ["TEST"], "allowed_subtypes": ["sequence"]},
    # Task 3: Matching (facts) — 2pts, Basic
    {"position": 3, "task_type": "matching", "description": "Знание фактов (соответствие)", "max_points": 2, "level": "basic", "allowed_types": ["TEST"], "allowed_subtypes": ["matching"]},
    # Task 4: Table systematization — 3pts, Advanced
    {"position": 4, "task_type": "short_answer", "description": "Систематизация в таблице", "max_points": 3, "level": "advanced", "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    # Task 5: Matching (historical figures) — 2pts, Basic
    {"position": 5, "task_type": "matching", "description": "Знание исторических деятелей (соответствие)", "max_points": 2, "level": "basic", "allowed_types": ["TEST"], "allowed_subtypes": ["matching"]},
    # Task 6: Written source work — 2pts, Advanced
    {"position": 6, "task_type": "short_answer", "description": "Работа с письменным историческим источником", "max_points": 2, "level": "advanced", "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    # Task 7: Matching (culture facts) — 2pts, Basic
    {"position": 7, "task_type": "matching", "description": "Знание истории культуры (соответствие)", "max_points": 2, "level": "basic", "allowed_types": ["TEST"], "allowed_subtypes": ["matching"]},
    # Task 8: Image work (WWII) — 1pt, Basic
    {"position": 8, "task_type": "short_answer", "description": "Работа с изображениями (Великая Отечественная война)", "max_points": 1, "level": "basic", "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    # Task 9: Map work — 1pt, Basic
    {"position": 9, "task_type": "short_answer", "description": "Работа с исторической картой/схемой", "max_points": 1, "level": "basic", "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    # Task 10: Map work — 1pt, Basic
    {"position": 10, "task_type": "short_answer", "description": "Работа с исторической картой/схемой", "max_points": 1, "level": "basic", "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    # Task 11: Map + text correlation — 1pt, Advanced
    {"position": 11, "task_type": "short_answer", "description": "Работа с картой (соотнесение с текстом)", "max_points": 1, "level": "advanced", "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    # Task 12: Map multiple choice — 2pts, Basic
    {"position": 12, "task_type": "short_answer", "description": "Работа с картой (множественный выбор)", "max_points": 2, "level": "basic", "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},

    # === PART 2: Extended answer (9 tasks, max 22 points) ===
    # Task 13: Written source attribution — 2pts, Advanced
    {"position": 13, "task_type": "essay", "description": "Работа с письменным источником (атрибуция)", "max_points": 2, "level": "advanced", "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    # Task 14: Written source info extraction — 2pts, Basic
    {"position": 14, "task_type": "essay", "description": "Поиск информации в письменном источнике", "max_points": 2, "level": "basic", "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    # Task 15: Image analysis — 2pts, Advanced
    {"position": 15, "task_type": "essay", "description": "Работа с изображениями", "max_points": 2, "level": "advanced", "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    # Task 16: Image analysis — 2pts, Advanced
    {"position": 16, "task_type": "essay", "description": "Работа с изображениями", "max_points": 2, "level": "advanced", "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    # Task 17: Two sources on WWII — 3pts, Advanced
    {"position": 17, "task_type": "essay", "description": "Анализ двух источников по теме ВОВ", "max_points": 3, "level": "advanced", "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    # Task 18: Cause-effect — 3pts, High
    {"position": 18, "task_type": "essay", "description": "Причинно-следственные связи", "max_points": 3, "level": "high", "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    # Task 19: Historical term — 2pts, Advanced
    {"position": 19, "task_type": "essay", "description": "Знание исторических понятий", "max_points": 2, "level": "advanced", "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    # Task 20: Comparison — 3pts, High
    {"position": 20, "task_type": "essay", "description": "Сравнение исторических событий/явлений/процессов", "max_points": 3, "level": "high", "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    # Task 21: Argumentation — 3pts, High
    {"position": 21, "task_type": "essay", "description": "Аргументация точки зрения", "max_points": 3, "level": "high", "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
]

# Verification against official spec:
# Part 1: 2+1+2+3+2+2+2+1+1+1+1+2 = 20 pts ✓
# Part 2: 2+2+2+2+3+3+2+3+3 = 22 pts ✓
# Total: 20+22 = 42 pts ✓

MAX_PRIMARY_POINTS = 42
EXAM_TIME_MINUTES = 210
TOTAL_TASKS = 21
