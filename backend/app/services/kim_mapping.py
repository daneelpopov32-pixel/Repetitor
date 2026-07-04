"""
KIM classifier for EGE History tasks.

Classifies tasks into exam positions (1-21) and difficulty levels (Б/П/В)
based on content analysis, NOT just format.

Source: ИС-11 ЕГЭ 2025 СПЕЦ.pdf, "Обобщённый план варианта" (pages 11-14).
Official level distribution: 10 Б / 8 П / 3 В = 42 points.

Classification rules per position (content-based, not format-based):
  №1: matching + dates/years → Б
  №2: sequence/chronology → Б
  №3: matching + facts/processes (NOT dates, NOT figures, NOT culture) → Б
  №4: table-based data in task → П
  №5: matching + historical figures (names with initials/titles) → Б
  №6: short_answer + written source analysis → П
  №7: matching + culture (art, monuments, architecture) → Б
  №8: image + WWII markers (1941-1945) → Б (STRICT: must have image AND WWII)
  №9: map/image → Б
  №10: map/image → Б
  №11: map + text correlation → П
  №12: map, multiple choice → Б
  №13: essay + source attribution → П
  №14: essay + source info extraction → Б
  №15: essay + image (not map, not WWII necessarily) → П
  №16: essay + image → П
  №17: essay + sources + WWII markers (STRICT) → П
  №18: essay + cause-effect → В
  №19: essay + historical terms/concepts → П
  №20: essay + comparison → В
  №21: essay + argumentation → В
"""

import re

# ─── Official levels from PDF (verified) ─────────────────────────────
POSITION_LEVELS = {
    1: "Б", 2: "Б", 3: "Б", 4: "П", 5: "Б", 6: "П", 7: "Б",
    8: "Б", 9: "Б", 10: "Б", 11: "П", 12: "Б",
    13: "П", 14: "Б", 15: "П", 16: "П", 17: "П", 18: "В",
    19: "П", 20: "В", 21: "В",
}
# Verify: Б=10 (1,2,3,5,7,8,9,10,12,14), П=8 (4,6,11,13,15,16,17,19), В=3 (18,20,21)

POSITION_POINTS = {
    1: 2, 2: 1, 3: 2, 4: 3, 5: 2, 6: 2, 7: 2, 8: 1, 9: 1, 10: 1, 11: 1, 12: 2,
    13: 2, 14: 2, 15: 2, 16: 2, 17: 3, 18: 3, 19: 2, 20: 3, 21: 3,
}

# ─── Keyword patterns for content-based classification ────────────────

# №5: Historical figures — names, titles, roles (strict patterns)
_FIGURE_PATTERNS = re.compile(
    r'(?:\bимператор\b|\bцарь\b|\bцарица\b|\bкнязь\b|\bхан\b|\bпрезидент\b'
    r'|\bпредседатель\b|\bгенерал\b|\bмаршал\b|\bдиктатор\b|\bполководец\b'
    r'|\bреформатор\b'  # Specific roles
    r'|[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.)',  # Фамилия И.О.
    re.IGNORECASE
)

# №7: Culture — monuments, art, architecture
_CULTURE_PATTERNS = re.compile(
    r'(?:памятник|картина|собор|храм|музей|галерея|литературн|'
    r'произведени|архитектур|живопис|скульптур|иконопис|'
    r'фреск|мозаик|ансамбл| дворц| kreml|Третьяковк|'
    r'Эрмитаж|Большой театр|Мариинск)',
    re.IGNORECASE
)

# №8, №17: WWII markers (STRICT)
_WWII_PATTERNS = re.compile(
    r'(?:194[1-5]|великая отечественная|блокада ленинграда|'
    r'сталинград|Курская битва|Курск|Сталинград|'
    r'Берлин|Победа|День Победы|9 мая|'
    r'ВОВ|Великая война|вторая мировая война|'
    r'Воронеж|Курск|Орёл|Смоленск|Севастополь|'
    r'СССР.*Герман|Герман.*СССР|'
    r'Т-34|Катюша|Ил-2|ППШ|Т-34)',
    re.IGNORECASE
)

# №4: Table-based data
_TABLE_PATTERNS = re.compile(
    r'(?:таблиц|столбец|строка|графа|ячейка|'
    r'заполните таблиц|систематиз|расположите.*столб|'
    r'подберите.*столб|впишите.*таблиц|'
    r'заполните пропуск|впишите пропуск|'
    r'заполните пустые ячейки)',
    re.IGNORECASE
)

# №8-12: Map/image work (expanded)
_MAP_PATTERNS = re.compile(
    r'(?:карта|схем|территор|область|государств|'
    r'границ|район|область|округ|город|место|'
    r'расположен|находился|находится|отметьте.*на карт|'
    r'укажите.*название.*города|укажите.*название.*реки|'
    r'назовите.*город|назовите.*реку|'
    r'обозначен.*на.*карт|обозначен.*на.*схем)',
    re.IGNORECASE
)

# №14: Source info extraction (expanded)
_INFO_EXTRACT_PATTERNS = re.compile(
    r'(?:источник|документ|послание|памятник|закон|'
    r'указ|манифест|конституция|декрет|приказ|'
    r'отрывок|фрагмент|цитат|'
    r'прочтите.*текст|прочтите.*отрывок|'
    r'ниже приведён.*текст|ниже приведён.*отрывок)',
    re.IGNORECASE
)

# №15-16: Image analysis (expanded)
_IMAGE_PATTERNS = re.compile(
    r'(?:изображен|иллюстрац|фотограф|рисунк|гравюр|'
    r'портрет|памятник|предмет|вещь|оружие|монета|'
    r'обратите внимание.*изображен|на рисунке|на фото|'
    r'рассмотрите изображение|рассмотрите.*рисунок|'
    r'на данн.*марке|на данн.*монете|на данн.*медали)',
    re.IGNORECASE
)

# №13: Source attribution
_ATTRIBUTION_PATTERNS = re.compile(
    r'(?:автор|когда был|кем был написан|дата создания|'
    r'обстоятельства создания|источник был создан|'
    r'определите автор|установите дату|к какому периоду)',
    re.IGNORECASE
)

# №6: Source analysis (short answer) — expanded
_SOURCE_PATTERNS = re.compile(
    r'(?:источник|документ|послание|памятник|закон|'
    r'указ|манифест|конституция|декрет|приказ|'
    r'отрывок|фрагмент|цитат)',
    re.IGNORECASE
)

# №15-16: Image analysis (not map, not necessarily WWII)
_IMAGE_PATTERNS = re.compile(
    r'(?:изображен|иллюстрац|фотограф|рисунк|гравюр|'
    r'портрет|памятник|предмет|вещь|оружие|монета|'
    r'обратите внимание.*изображен|на рисунке|на фото)',
    re.IGNORECASE
)

# №9-12: Map work
_MAP_PATTERNS = re.compile(
    r'(?:карта|схем|территор|область|государств|'
    r'границ|район|область|округ|город|место|'
    r'расположен|находился|находится|отметьте.*на карт)',
    re.IGNORECASE
)

# №18: Cause-effect
_CAUSE_EFFECT_PATTERNS = re.compile(
    r'(?:причин|следстви|результат|влияние|привело к|'
    r'являлось следствием|обусловлен|обусловило|'
    r'привело к|способствовал|вызвало|породило)',
    re.IGNORECASE
)

# №19: Historical terms
_TERMS_PATTERNS = re.compile(
    r'(?:понятие|термин|определени|означает|обознача|'
    r'означение|смысл|содержание понятия|раскройте понятие|'
    r'историческ.*понятие|историческ.*термин)',
    re.IGNORECASE
)

# №20: Comparison
_COMPARISON_PATTERNS = re.compile(
    r'(?:сравни|сопостав|общее.*различн|сходств|отличи|'
    r'сравнительн|аналогичн|в отличие|по аналогии)',
    re.IGNORECASE
)

# №21: Argumentation
_ARGUMENT_PATTERNS = re.compile(
    r'(?:аргумент|докаж|обоснуй|аргументируй|'
    r'согласны ли вы|оцените|свой взгляд|своя позиция|'
    r'подтвердите|опровергните|как вы считаете)',
    re.IGNORECASE
)


def _has_image(text_content: dict) -> bool:
    """Check if the task has an image in text_content."""
    if not isinstance(text_content, dict):
        return False
    images = text_content.get("images", [])
    return bool(images)


def classify_task(subtype: str, text: str = "", text_content: dict = None) -> tuple[int | None, str | None]:
    """Classify a task into KIM position and difficulty level.

    Uses content-based rules, not just format.
    Returns (exam_position, difficulty_level) or (None, None) if uncertain.

    Args:
        subtype: FIPI parser subtype (matching/sequence/short_answer/essay)
        text: Cleaned task text
        text_content: Full text_content dict (for image checks)
    """
    if text_content is None:
        text_content = {}
    has_image = _has_image(text_content)

    # ── SEQUENCE → always position 2 ──
    if subtype == "sequence":
        return 2, "Б"

    # ── MATCHING → positions 1, 3, 5, 7 (distinguished by content) ──
    if subtype == "matching":
        # EXCLUSION: "фрагменты/отрывки исторических источников" = position 3, NOT 5
        if re.search(r'(?:фрагмент\w*\s+(?:историческ\w*\s+)?источник\w*|отрывк\w*\s+(?:историческ\w*\s+)?источник\w*)', text, re.IGNORECASE):
            return 3, "Б"
        if _FIGURE_PATTERNS.search(text):
            return 5, "Б"
        if _CULTURE_PATTERNS.search(text):
            return 7, "Б"
        # Date-heavy content = position 1
        date_count = len(re.findall(r'\b(?:1[0-9]{3}|20[0-2][0-9])\b', text))
        if date_count >= 3:
            return 1, "Б"
        # Default matching = facts/processes (pos 3)
        return 3, "Б"

    # ── SHORT ANSWER → positions 4, 6, 8-12 (content-based) ──
    if subtype == "short_answer":
        # №8: STRICT — must have image AND WWII markers
        if has_image and _WWII_PATTERNS.search(text):
            return 8, "Б"

        # №9, 10, 12: map work — allow if text clearly indicates map, even without stored image
        if _MAP_PATTERNS.search(text):
            # №11: map + text correlation
            if re.search(r'(?:соотнес|сопостав|установите|определите.*по.*карт)', text, re.IGNORECASE):
                return 11, "П"
            return 9, "Б"

        # №10: image work (without map markers) — "рассмотрите изображение"
        if _IMAGE_PATTERNS.search(text):
            return 10, "Б"

        # №4: table-based data
        if _TABLE_PATTERNS.search(text):
            return 4, "П"

        # №6: written source analysis
        if _INFO_EXTRACT_PATTERNS.search(text):
            return 6, "П"

        # №12: multiple choice map
        if re.search(r'(?:назовите.*правител|укажите.*фамили|напишите.*название)', text, re.IGNORECASE):
            return 12, "Б"

        # №5: figure matching (short_answer with figure keywords)
        if _FIGURE_PATTERNS.search(text):
            return 5, "Б"

        # №3: term/list matching (default for short_answer)
        if re.search(r'(?:ниже приведён.*список|ниже приведён.*перечень|запишите термин|напишите термин|напишите пропущенное|историческ.*термин|пропущенное слово)', text, re.IGNORECASE):
            return 3, "Б"

        # №7: culture (short_answer with culture keywords)
        if _CULTURE_PATTERNS.search(text):
            return 7, "Б"

        # №5: figure matching (short_answer with figure keywords)
        if re.search(r'(?:какие.*здания|какие.*сооружени|какие.*плакат|укажите.*афиш)', text, re.IGNORECASE):
            return 5, "Б"

        # Default: position 3 (facts/processes) for any remaining short_answer
        return 3, "Б"

    # ── ESSAY → positions 13-21 (content-based) ──
    if subtype == "essay":
        # №17: STRICT — WWII sources
        if has_image and _WWII_PATTERNS.search(text):
            return 17, "П"
        if _WWII_PATTERNS.search(text) and _INFO_EXTRACT_PATTERNS.search(text):
            return 17, "П"

        # №15, 16: image analysis
        if has_image and _IMAGE_PATTERNS.search(text):
            return 15, "П"

        # №13: source attribution
        if _ATTRIBUTION_PATTERNS.search(text):
            return 13, "П"

        # №18: cause-effect
        if _CAUSE_EFFECT_PATTERNS.search(text):
            return 18, "В"

        # №19: terms/concepts
        if _TERMS_PATTERNS.search(text):
            return 19, "П"

        # №20: comparison
        if _COMPARISON_PATTERNS.search(text):
            return 20, "В"

        # №21: argumentation
        if _ARGUMENT_PATTERNS.search(text):
            return 21, "В"

        # №14: default essay = source info extraction
        if _INFO_EXTRACT_PATTERNS.search(text):
            return 14, "Б"

        # №16: image essay without map markers
        if _IMAGE_PATTERNS.search(text):
            return 16, "П"

        # №13: date-specific essay ("укажите с точностью до десятилетия")
        if re.search(r'(?:укажите.*десятилети|укажите.*год.*когда|назовите.*год)', text, re.IGNORECASE):
            return 13, "П"

        # Default essay = source info extraction (position 14)
        return 14, "Б"

    # ── EMPTY SUBTYPE (seed data) → default to position 3 ──
    if not subtype:
        return 3, "Б"

    return None, None
