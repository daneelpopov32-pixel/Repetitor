"""
EGE History variant template — matches official typification exactly.

Source: docs/типизация.md (based on ИС-11 ЕГЭ 2025 СПЕЦ.pdf)
Structure: 21 tasks, 210 minutes, 42 max primary points.
"""

EGE_HISTORY_TEMPLATE = [
    # Part 1: Short answer (12 tasks, 20 pts)
    {"position": 1,  "task_type": "matching",     "description": "Систематизация исторической информации: соответствие. VIII – начало XXI века", "max_points": 2, "level": "basic",   "allowed_types": ["TEST"], "allowed_subtypes": ["matching"]},
    {"position": 2,  "task_type": "sequence",      "description": "Определение последовательности исторических событий. VIII – начало XXI века", "max_points": 1, "level": "basic",   "allowed_types": ["TEST"], "allowed_subtypes": ["sequence"]},
    {"position": 3,  "task_type": "matching",      "description": "Систематизация исторической информации: соответствие. VIII – начало XXI века", "max_points": 2, "level": "basic",   "allowed_types": ["TEST"], "allowed_subtypes": ["matching"]},
    {"position": 4,  "task_type": "short_answer",  "description": "Работа с информацией, представленной в форме таблицы",                     "max_points": 3, "level": "advanced","allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 5,  "task_type": "matching",      "description": "Знание исторических деятелей VIII – начала XXI в.",                          "max_points": 2, "level": "basic",   "allowed_types": ["TEST"], "allowed_subtypes": ["matching"]},
    {"position": 6,  "task_type": "short_answer",  "description": "Анализ текстовых исторических источников. Часть 1",                          "max_points": 2, "level": "advanced","allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 7,  "task_type": "matching",      "description": "Систематизация исторической информации: соответствие. VIII – начало XXI века", "max_points": 2, "level": "basic",   "allowed_types": ["TEST"], "allowed_subtypes": ["matching"]},
    {"position": 8,  "task_type": "short_answer",  "description": "Работа с изображениями ВОВ",                                             "max_points": 1, "level": "basic",   "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 9,  "task_type": "short_answer",  "description": "Анализ исторических карт, схем. Часть 1",                                  "max_points": 1, "level": "basic",   "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 10, "task_type": "short_answer",  "description": "Анализ исторических карт, схем. Часть 1",                                  "max_points": 1, "level": "basic",   "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 11, "task_type": "short_answer",  "description": "Соответствие информации из исторической карты и текста",                    "max_points": 1, "level": "advanced","allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 12, "task_type": "short_answer",  "description": "Соответствие информации из исторической карты и текста",                    "max_points": 2, "level": "basic",   "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},

    # Part 2: Extended answer (9 tasks, 22 pts)
    {"position": 13, "task_type": "essay",         "description": "Определение характеристик исторического источника. XVIII – начало XX века",  "max_points": 2, "level": "advanced","allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    {"position": 14, "task_type": "essay",         "description": "Поиск исторической информации. XVIII - начало XX века",                     "max_points": 2, "level": "basic",   "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    {"position": 15, "task_type": "essay",         "description": "Анализ иллюстративного материала. XVIII − XIX века",                       "max_points": 2, "level": "advanced","allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    {"position": 16, "task_type": "essay",         "description": "Работа с историческим источником. XX век",                                 "max_points": 2, "level": "advanced","allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    {"position": 17, "task_type": "essay",         "description": "Работа с историческим источником. XX век",                                 "max_points": 3, "level": "advanced","allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    {"position": 18, "task_type": "essay",         "description": "Установление причинно-следственных связей. XVIII − XIX века",             "max_points": 3, "level": "high",   "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    {"position": 19, "task_type": "essay",         "description": "Проверка знаний исторических понятий. XVIII − XIX века",                   "max_points": 2, "level": "advanced","allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    {"position": 20, "task_type": "essay",         "description": "Сравнение исторических событий",                                          "max_points": 3, "level": "high",   "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    {"position": 21, "task_type": "essay",         "description": "Аргументация с использованием исторических фактов. VIII − XVII века",     "max_points": 3, "level": "high",   "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
]

# Points verification: 2+1+2+3+2+2+2+1+1+1+1+2=20 | 2+2+2+2+3+3+2+3+3=22 | Total=42

MAX_PRIMARY_POINTS = 42
EXAM_TIME_MINUTES = 210
TOTAL_TASKS = 21
