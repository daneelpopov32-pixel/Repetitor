"""
KIM classifier for EGE History tasks — STRICT STRUCTURAL RULES.

Classification priority:
  1. Structural markers (headers, image presence, answer format)
  2. Content patterns as fallback
  3. Honest None when uncertain — NO default to any position

Source: Task 23 specifications based on real FIPI task analysis.
"""

import re

# ─── Official levels and points ──────────────────────────────────────
POSITION_LEVELS = {
    1: "Б", 2: "Б", 3: "Б", 4: "П", 5: "Б", 6: "П", 7: "Б",
    8: "Б", 9: "Б", 10: "Б", 11: "П", 12: "Б",
    13: "П", 14: "Б", 15: "П", 16: "П", 17: "П", 18: "В",
    19: "П", 20: "В", 21: "В",
}

POSITION_POINTS = {
    1: 2, 2: 1, 3: 2, 4: 3, 5: 2, 6: 2, 7: 2, 8: 1, 9: 1, 10: 1, 11: 1, 12: 2,
    13: 2, 14: 2, 15: 2, 16: 2, 17: 3, 18: 3, 19: 2, 20: 3, 21: 3,
}


def _has_image(text_content: dict) -> bool:
    if not isinstance(text_content, dict):
        return False
    return bool(text_content.get("images", []))


def _get_task_description(text: str) -> str:
    """Extract task description only (before answer options)."""
    for marker in [
        "\nА)", "\nа)", "\n1)", "\nСОБЫТИЯ", "\nПРОЦЕССЫ", "\nГОДЫ",
        "\nУЧАСТНИКИ", "\nФАКТЫ", "\nПАМЯТНИКИ", "\nДЕЯТЕЛИ",
        "\nГОСУДАРСТВЕННЫЕ ДЕЯТЕЛИ", "\nПропущенные элементы",
        "\nХАРАКТЕРИСТИКИ",
    ]:
        idx = text.find(marker)
        if idx > 0:
            return text[:idx]
    return text


# ═══════════════════════════════════════════════════════════════════════
# TYPE-SPECIFIC STRUCTURAL PATTERNS
# ═══════════════════════════════════════════════════════════════════════

# Type 1: matching, right column = years (4-digit numbers)
# No explicit header, detected by content pattern
_TYPE1_YEARS = re.compile(
    r'(?:событиями\s+и\s+годами|годам\w*\s+и\s+событ|'
    r'ГОДЫ\s*$|хронологическ)',
    re.MULTILINE | re.IGNORECASE
)

# Type 3: matching, headers "ПРОЦЕСС(Ы) (ЯВЛЕНИЕ, СОБЫТИЕ)" and "ФАКТЫ"
_TYPE3_HEADERS = re.compile(
    r'(?:ПРОЦЕСС\w*\s*\([\w,\s]+\)|ФАКТЫ|'
    r'событиями\s+и\s+участник\w*|'
    r'участниками\s+этих\s+событий|'
    r'процессами\s+и\s+фактами|'
    r'явлениями.*событиями.*и\s+фактами)',
    re.IGNORECASE
)

# Type 4: HTML table with blanks + "Пропущенные элементы"
_TYPE4_TABLE = re.compile(
    r'(?:заполните\s+пустые\s+ячейки\s+таблиц|'
    r'пустые\s+ячейки\s+таблиц|'
    r'заполните\s+таблиц)',
    re.IGNORECASE
)

# Type 5: matching, header "ГОСУДАРСТВЕННЫЕ ДЕЯТЕЛИ", "ДЕЯТЕЛИ", or "УЧАСТНИКИ"
_TYPE5_FIGURES = re.compile(
    r'(?:ГОСУДАРСТВЕННЫЕ\s+ДЕЯТЕЛИ|ДЕЯТЕЛИ\b|УЧАСТНИКИ)',
    re.IGNORECASE
)

# Type 6: long quote + "выберите верные суждения" / "запишите цифры"
# NOT short_answer — separate format "множественный выбор по цитате"
_TYPE6_SOURCE = re.compile(
    r'(?:выберите\s+\w+\s+верн\w*\s+суждени|'
    r'запишите\s+цифры\s*,?\s*под\s+которыми|'
    r'прочтите\s+отрывок\s+и\s+(?:выберите|запишите)|'
    r'какие\s+из\s+перечисленн\w+\s+суждени)',
    re.IGNORECASE
)

# Type 7: matching, header "ПАМЯТНИК(И) КУЛЬТУРЫ"
_TYPE7_CULTURE = re.compile(
    r'(?:ПАМЯТНИК\w*\s+КУЛЬТУРЫ|'
    r'памятник\w*\s+культур\w*|'
    r'произведен\w*\s+культур\w*)',
    re.IGNORECASE
)

# Type 8: "Рассмотрите изображение" + image + WWII markers
_TYPE8_INTRO = re.compile(
    r'рассмотрите\s+изображени\w*\s+и\s+выполните',
    re.IGNORECASE
)

_WWII_MARKERS = re.compile(
    r'(?:194[1-5]|великая\s+отечественная|'
    r'блокада\s+ленинграда|сталинград|Курская\s+битва|'
    r'Берлин|Победа|День\s+Победы|9\s+мая|'
    r'ВОВ|вторая\s+мировая\s+война)',
    re.IGNORECASE
)

# Types 9-12: ALL require image + map intro
_TYPE9_12_MAP_INTRO = re.compile(
    r'(?:рассмотрите\s+(?:схему|карту)\s+и\s+выполните|'
    r'обозначен\w*\s+на\s+(?:схеме|карте)|'
    r'в\s+легенде\s+схемы|'
    r'на\s+схеме|'
    r'на\s+карт\w*|'
    r'отражён\w*\s+на\s+схеме)',
    re.IGNORECASE
)

# Type 9: question about general context of the map (ruler, period, event participants)
# NOT about a specific numbered object — that's Type 10
_TYPE9_WHOLE_EVENT = re.compile(
    r'(?:напишите\s+название\s+(?:войны|события)|'
    r'назовите\s+название\s+(?:войны|события)|'
    r'какому\s+событию\s+посвящена\s+схема|'
    r'укажите\s+правителя|'
    r'назовите\s+правителя|'
    r'кто\s+был\s+(?:правителем|царём|императором)|'
    r'в\s+период\s+какого\s+события|'
    r'участники\s+события)',
    re.IGNORECASE
)

# Type 10: question about numbered object on map
_TYPE10_NUMBERED = re.compile(
    r'(?:обозначен\w*\s+цифр\w*\s*[«"\d]|'
    r'город\s*,?\s*обозначен|'
    r'рек\w*\s*,?\s*обозначен|'
    r'укажите\s+название\s+(?:города|реки)|'
    r'назовите\s+город)',
    re.IGNORECASE
)

# Type 11: map + text with blank (комбинация карта+текст)
_TYPE11_MAP_TEXT = re.compile(
    r'(?:используя\s+(?:схему|карт\w*)\s*,?\s*укажите\s+пропущенное|'
    r'заполните\s+пропуск\s+в\s+предложении.*(?:на\s+схеме|на\s+карт\w*)|'
    r'напишите\s+название\s+города.*пропущено\s+в\s+тексте|'
    r'прочтите\s+текст\s+о\s+событиях.*на\s+схеме|'
    r'пропущенное\s+в\s+тексте.*(?:используя|на\s+схеме)|'
    r'дважды\s+пропущенное\s+в\s+тексте)',
    re.IGNORECASE
)

# Type 12: map + list of judgments (like Type 6 but about map)
# ONLY "суждений/суждения" — not buildings/posters (those are Type 16)
_TYPE12_MAP_JUDGMENTS = re.compile(
    r'(?:какие\s+из\s+представленн\w+\s+суждени|'
    r'какие\s+суждени|'
    r'какие\s+из\s+перечисленн\w+\s+суждени|'
    r'суждени\w*\s+относящ\w*\s+к\s+(?:схеме|карт\w*)|'
    r'являются\s+верными\s*\?|'
    r'являются\s+верными)',
    re.IGNORECASE
)

# Type 16: multiple images to choose from (buildings, posters, etc.)
_TYPE16_MULTI_IMAGE = re.compile(
    r'(?:какие\s+из\s+представленн\w+\s+(?:зданий|сооружений|плакатов|афиш|памятников)|'
    r'какой\s+из\s+представленн\w+\s+памятников|'
    r'укажите\s+афиши|'
    r'какие\s+здания|'
    r'какие\s+из\s+нижеперечисленн\w+)',
    re.IGNORECASE
)

# Type 13: source quote + FACTUAL question about the source itself (attribution)
# "Укажите год", "Укажите фамилию", "кем был написан", "обстоятельства создания",
# "к какому периоду относится", "назовите название", "определите автора"
_TYPE13_ATTRIBUTION = re.compile(
    r'(?:автор\w*\s+этого|'
    r'кем\s+был\s+написан|'
    r'обстоятельства\s+создания|'
    r'к\s+какому\s+периоду\s+относится|'
    r'назовите\s+название\s+(?:сочинения|произведения|документа)|'
    r'определите\s+автор|'
    r'установите\s+дату\s+создания|'
    r'укажите\s+год\b|'
    r'укажите\s+фамилию|'
    r'укажите\s+(?:историческ\w*\s+деятел|княз|император|цар|председател))',
    re.IGNORECASE
)

# Type 14: source quote + INTERPRETIVE question about content inside source
# "В чём состоит правда", "как автор характеризует", "что имел в виду автор",
# "с чем согласен/не согласен", "какие суждения верны"
_TYPE14_CONTENT = re.compile(
    r'(?:в\s+чём.*состоит\s+(?:правда|смысл|суть)|'
    r'как\s+автор\w*.*(?:характеризует|оценивает|описывает)|'
    r'что\s+имел\w*\s+в\s+виду\s+автор|'
    r'с\s+чем\s+согласен|'
    r'какие\s+из\s+перечисленн\w+\s+событ\w*\s+относятся|'
    r'какие\s+из\s+представленн\w+\s+суждени|'
    r'какие\s+отрицательн\w*\s+последстви|'
    r'как\w*\s+автор\w*\s+(?:считает|полагает|утверждает))',
    re.IGNORECASE
)

# Type 15: single image + "назовите местность/событие"
_TYPE15_SINGLE_IMAGE = re.compile(
    r'(?:назовите\s+(?:местность|событие|город|год|месяц)|'
    r'укажите\s+(?:месяц|год|название)|'
    r'заполните\s+пропуск\s+в\s+предложении)',
    re.IGNORECASE
)

# Type 17: WWII sources (two fragments A/B)
_TYPE17_WWII_SOURCES = re.compile(
    r'(?:фрагмент\w*\s+источник|'
    r'прочтите\s+отрывки?\s+из\s+воспоминаний|'
    r'источник\w*\s+[АБ]\))',
    re.IGNORECASE
)

# Type 18: three-part answer structure (а/б/в)
_TYPE18_CAUSE_EFFECT = re.compile(
    r'(?:а\)\s*причин|б\)\s*последстви|в\)\s*последстви|'
    r'причин\w*\s+и\s+следстви|'
    r'установите\s+соответствие\s+между\s+причинами)',
    re.IGNORECASE
)

# Type 19: "раскройте смысл понятия"
_TYPE19_CONCEPTS = re.compile(
    r'(?:раскройте\s+смысл\s+понятия|'
    r'определени\w*\s+термина|'
    r'что\s+означает\s+термин)',
    re.IGNORECASE
)

# Type 20: comparison with 2+2 structure
_TYPE20_COMPARISON = re.compile(
    r'(?:тезис\s*\(обобщённое|'
    r'два\s+обоснования|'
    r'сравните\s+два\s+события|'
    r'сопоставьте\s+два)',
    re.IGNORECASE
)

# Type 21: argumentation with named categories for two objects
_TYPE21_ARGUMENT = re.compile(
    r'(?:аргумент\s+для\s+\w+|'
    r'приведите\s+аргумент\w*\s+для\s+каждого|'
    r'напишите\s+последовательный\s+связный\s+текст|'
    r'историческое\s+сочинение\s+об\s+одном|'
    r'вам\s+необходимо\s+написать)',
    re.IGNORECASE
)

# Content patterns for fallback
_DATE_PATTERN = re.compile(r'\b(?:1[0-9]{3}|20[0-2][0-9])\b')
_FIGURE_NAMES = re.compile(
    r'(?:[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.)|'
    r'(?:\bимператор\b|\bцарь\b|\bкнязь\b|\bхан\b|\bпрезидент\b|\bгенерал\b)',
    re.IGNORECASE
)


def classify_task(subtype: str, text: str = "", text_content: dict = None) -> tuple[int | None, str | None]:
    """Classify a task into KIM position and difficulty level.

    Structural markers first, content patterns as fallback.
    Returns (exam_position, difficulty_level) or (None, None) if uncertain.
    """
    if text_content is None:
        text_content = {}
    has_img = _has_image(text_content)
    desc = _get_task_description(text)

    # ══════════════════════════════════════════════════════════════════
    # SEQUENCE → Type 2
    # ══════════════════════════════════════════════════════════════════
    if subtype == "sequence":
        return 2, "Б"

    # ══════════════════════════════════════════════════════════════════
    # MATCHING → Types 1, 3, 4, 5, 7
    # ══════════════════════════════════════════════════════════════════
    if subtype == "matching":
        # Type 4: table with blanks
        if _TYPE4_TABLE.search(text):
            return 4, "П"

        # Type 5: header "ДЕЯТЕЛИ" / "УЧАСТНИКИ" — check full text (desc may be truncated)
        if _TYPE5_FIGURES.search(text):
            return 5, "Б"

        # Type 7: header "ПАМЯТНИКИ КУЛЬТУРЫ"
        if _TYPE7_CULTURE.search(desc):
            return 7, "Б"

        # Type 3: headers "ПРОЦЕССЫ/ФАКТЫ" or "событиями и участниками"
        if _TYPE3_HEADERS.search(desc):
            return 3, "Б"

        # Type 1: right column = years
        if _TYPE1_YEARS.search(desc):
            return 1, "Б"

        # Fallback: count years in description
        year_count = len(_DATE_PATTERN.findall(desc))
        if year_count >= 3:
            return 1, "Б"

        # Fallback: figure names → Type 5
        if _FIGURE_NAMES.search(desc):
            return 5, "Б"

        # Default matching → Type 3 (facts/participants)
        return 3, "Б"

    # ══════════════════════════════════════════════════════════════════
    # SHORT ANSWER → Types 4, 8, 9, 10, 11, 12
    # Type 6 is NOT short_answer — it's separate format
    # ══════════════════════════════════════════════════════════════════
    if subtype == "short_answer":
        # Type 8: image + intro "Рассмотрите изображение и выполните задание"
        # If also has WWII markers → definitely 8. Without WWII → still 8 if image present
        if has_img and _TYPE8_INTRO.search(text):
            return 8, "Б"

        # Types 9-12: require image + map intro, OR strong text marker
        has_map_text = _TYPE9_12_MAP_INTRO.search(text)

        if has_img and has_map_text:
            # Type 11: map + text with blank
            if _TYPE11_MAP_TEXT.search(text):
                return 11, "П"
            # Type 12: map + judgments to choose
            if _TYPE12_MAP_JUDGMENTS.search(text):
                return 12, "Б"
            # Type 10: numbered object on map
            if _TYPE10_NUMBERED.search(text):
                return 10, "Б"
            # Type 9: whole event/war question
            return 9, "Б"

        # Fallback: strong text marker without image (FIPI blocks downloads)
        if has_map_text:
            if _TYPE11_MAP_TEXT.search(text):
                return 11, "П"
            if _TYPE12_MAP_JUDGMENTS.search(text):
                return 12, "Б"
            if _TYPE10_NUMBERED.search(text):
                return 10, "Б"
            return 9, "Б"

        # Type 4: table (without image)
        if _TYPE4_TABLE.search(text):
            return 4, "П"

        # Type 16: multiple images to choose (without stored image)
        if _TYPE16_MULTI_IMAGE.search(text):
            return 16, "П"

        # No structural marker → honest None
        return None, None

    # ══════════════════════════════════════════════════════════════════
    # ESSAY → Types 13-21
    # ══════════════════════════════════════════════════════════════════
    if subtype == "essay":
        # Type 21: "написать историческое сочинение"
        if _TYPE21_ARGUMENT.search(text):
            return 21, "В"

        # Type 17: WWII sources (STRICT: two fragments + WWII)
        if _WWII_MARKERS.search(text) and _TYPE17_WWII_SOURCES.search(text):
            return 17, "П"

        # Type 18: three-part answer structure (а/б/в)
        if _TYPE18_CAUSE_EFFECT.search(text):
            return 18, "В"

        # Type 19: "раскройте смысл понятия"
        if _TYPE19_CONCEPTS.search(text):
            return 19, "П"

        # Type 20: comparison with 2+2
        if _TYPE20_COMPARISON.search(text):
            return 20, "В"

        # Type 15/16: image analysis (BEFORE attribution — image tasks take priority)
        if has_img:
            if _TYPE16_MULTI_IMAGE.search(text):
                return 16, "П"
            return 15, "П"

        # Type 13: source attribution
        if _TYPE13_ATTRIBUTION.search(text):
            return 13, "П"

        # Type 12: judgments about a map (essay subtype)
        if _TYPE12_MAP_JUDGMENTS.search(text):
            return 12, "Б"

        # Type 6: multiple choice based on source (essay subtype)
        if _TYPE6_SOURCE.search(text):
            return 6, "П"

        # Type 14: source content extraction (interpretive questions)
        if _TYPE14_CONTENT.search(text):
            return 14, "Б"

        # No structural marker → honest None
        return None, None

    # ══════════════════════════════════════════════════════════════════
    # EMPTY SUBTYPE → None
    # ══════════════════════════════════════════════════════════════════
    return None, None
