"""
OGE variant templates — History and Social Studies.

Structure mirrors official FIPI typification.
Both subjects: 24 tasks total.
"""

# ═══════════════════════════════════════════════════════════════════════
# OGE HISTORY — 24 tasks (20 short + 4 extended)
# ═══════════════════════════════════════════════════════════════════════

OGE_HISTORY_TEMPLATE = [
    # Part 1: Short answer (20 tasks)
    {"position": 1,  "task_type": "matching",     "description": "Соответствие элементов культурно-исторического наследия",     "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["matching"]},
    {"position": 2,  "task_type": "sequence",      "description": "Определение последовательности исторических событий",       "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["sequence"]},
    {"position": 3,  "task_type": "matching",      "description": "Установление соответствия между элементами",               "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["matching"]},
    {"position": 4,  "task_type": "short_answer",  "description": "Работа с информацией, представленной в форме таблицы",     "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 5,  "task_type": "matching",      "description": "Знание исторических деятелей",                            "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["matching"]},
    {"position": 6,  "task_type": "short_answer",  "description": "Анализ текстового исторического источника",                "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 7,  "task_type": "matching",      "description": "Систематизация исторической информации: соответствие",   "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["matching"]},
    {"position": 8,  "task_type": "short_answer",  "description": "Работа с изображениями",                                 "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 9,  "task_type": "short_answer",  "description": "Анализ исторических карт, схем",                          "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 10, "task_type": "short_answer",  "description": "Соответствие информации из исторической карты и текста",  "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 11, "task_type": "short_answer",  "description": "Соотнесение понятий и событий",                          "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 12, "task_type": "short_answer",  "description": "Определение сущности исторических понятий",               "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 13, "task_type": "short_answer",  "description": "Работа с изображениями (продвинутый уровень)",            "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 14, "task_type": "short_answer",  "description": "Анализ исторических карт (продвинутый уровень)",          "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 15, "task_type": "short_answer",  "description": "Сравнение исторических событий и процессов",             "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 16, "task_type": "short_answer",  "description": "Работа с источниками информации",                         "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 17, "task_type": "short_answer",  "description": "Определение характерных особенностей исторических событий", "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 18, "task_type": "short_answer",  "description": "Установление причинно-следственных связей",              "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 19, "task_type": "short_answer",  "description": "Работа с исторической картой (комплексная задача)",      "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 20, "task_type": "short_answer",  "description": "Анализ исторических источников и аргументация",         "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},

    # Part 2: Extended answer (4 tasks)
    {"position": 21, "task_type": "essay",         "description": "Определение характеристик исторического источника",     "max_points": 4, "level": "advanced", "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    {"position": 22, "task_type": "essay",         "description": "Поиск исторической информации",                          "max_points": 3, "level": "basic",   "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    {"position": 23, "task_type": "essay",         "description": "Установление причинно-следственных связей",             "max_points": 5, "level": "advanced", "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    {"position": 24, "task_type": "essay",         "description": "Работа с историческим источником и аргументация",       "max_points": 8, "level": "high",    "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
]

OGE_HISTORY_MAX_PRIMARY_POINTS = 39
OGE_HISTORY_EXAM_TIME_MINUTES = 155
OGE_HISTORY_TOTAL_TASKS = 24


# ═══════════════════════════════════════════════════════════════════════
# OGE SOCIAL STUDIES — 24 tasks (18 short + 6 extended)
# ═══════════════════════════════════════════════════════════════════════

OGE_SOCIAL_TEMPLATE = [
    # Part 1: Short answer (18 tasks)
    {"position": 1,  "task_type": "matching",     "description": "Соответствие понятий и примеров",                        "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["matching"]},
    {"position": 2,  "task_type": "sequence",      "description": "Определение последовательности событий",                 "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["sequence"]},
    {"position": 3,  "task_type": "matching",      "description": "Соответствие элементов политической и правовой сферы",  "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["matching"]},
    {"position": 4,  "task_type": "short_answer",  "description": "Работа с информацией в форме таблицы",                  "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 5,  "task_type": "matching",      "description": "Соответствие элементов экономической сферы",            "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["matching"]},
    {"position": 6,  "task_type": "short_answer",  "description": "Анализ социальной информации",                           "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 7,  "task_type": "matching",      "description": "Систематизация информации: соответствие",                "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["matching"]},
    {"position": 8,  "task_type": "short_answer",  "description": "Работа с изображениями",                                "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 9,  "task_type": "short_answer",  "description": "Анализ графической информации",                          "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 10, "task_type": "short_answer",  "description": "Соответствие информации из таблицы и текста",            "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 11, "task_type": "short_answer",  "description": "Соотнесение понятий сфер общественной жизни",           "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 12, "task_type": "short_answer",  "description": "Определение сущности социальных понятий",               "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 13, "task_type": "short_answer",  "description": "Работа с нормативно-правовыми документами",             "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 14, "task_type": "short_answer",  "description": "Анализ экономической информации",                        "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 15, "task_type": "short_answer",  "description": "Сравнение социальных объектов и процессов",             "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 16, "task_type": "short_answer",  "description": "Работа с источниками информации",                        "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 17, "task_type": "short_answer",  "description": "Определение характерных особенностей общественных процессов", "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},
    {"position": 18, "task_type": "short_answer",  "description": "Установление причинно-следственных связей",             "max_points": 1, "level": "basic",  "allowed_types": ["TEST"], "allowed_subtypes": ["short_answer"]},

    # Part 2: Extended answer (6 tasks)
    {"position": 19, "task_type": "essay",         "description": "Использование знаний для решения познавательных задач", "max_points": 2, "level": "basic",   "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    {"position": 20, "task_type": "essay",         "description": "Работа с источниками социальной информации",            "max_points": 2, "level": "basic",   "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    {"position": 21, "task_type": "essay",         "description": "Анализ деятельности социальных субъектов",              "max_points": 2, "level": "basic",   "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    {"position": 22, "task_type": "essay",         "description": "Сравнение социальных объектов",                        "max_points": 2, "level": "advanced", "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    {"position": 23, "task_type": "essay",         "description": "Установление причинно-следственных связей",             "max_points": 3, "level": "advanced", "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
    {"position": 24, "task_type": "essay",         "description": "Решение комплексной задачи с использованием знаний из разных тем", "max_points": 3, "level": "high", "allowed_types": ["ESSAY"], "allowed_subtypes": ["essay"]},
]

OGE_SOCIAL_MAX_PRIMARY_POINTS = 39
OGE_SOCIAL_EXAM_TIME_MINUTES = 155
OGE_SOCIAL_TOTAL_TASKS = 24
