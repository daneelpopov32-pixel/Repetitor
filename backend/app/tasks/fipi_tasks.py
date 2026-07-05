"""
Celery tasks for FIPI integration.
Uses sync SQLAlchemy to avoid event loop issues in Celery workers.
"""
import re
from copy import copy
import httpx
from bs4 import BeautifulSoup
import logging

from celery import Celery
from app.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "repetitor",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

BASE_URL = "https://ege.fipi.ru/bank"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://ege.fipi.ru/bank/index.php?proj=068A227D253BA6C04D0C832387FD0D89",
}

FIPI_PROJECT_ID = "068A227D253BA6C04D0C832387FD0D89"

# History codifier — official 2025 (ИС-11 ЕГЭ, Таблица 3)
# Codes must match DB (trailing dots: "1.", "7.1.", etc.)
CODIFIER_THEMES_HISTORY = {
    "1.": "История России. Древнейший период",
    "2.": "История России. Средние века",
    "3.": "История России. XVI – XVII вв.",
    "4.": "История России. XVIII в.",
    "5.": "История России. Первая половина XIX в.",
    "6.": "История России. Вторая половина XIX в.",
    "7.": "История России. 1914–1945 гг.",
    "7.1.": "Россия в Первой мировой войне (1914–1918)",
    "7.2.": "1917 год: от Февраля к Октябрю",
    "7.3.": "Первые революционные преобразования большевиков",
    "7.4.": "Гражданская война и её последствия",
    "7.5.": "Идеология и культура Советской России периода Гражданской войны",
    "7.6.": "СССР в годы нэпа (1921–1928)",
    "7.7.": "Советский Союз в 1929–1941 гг.",
    "7.8.": "Культурное пространство советского общества в 1920–1930-е гг.",
    "7.9.": "Внешняя политика СССР в 1920–1930-е гг.",
    "8.": "Великая Отечественная война (1941–1945)",
    "8.1.": "Первый период войны (июнь 1941 – осень 1942 г.)",
    "8.2.": "Коренной перелом в ходе войны (осень 1942 – 1943 г.)",
    "8.3.": "Человек и война: единство фронта и тыла",
    "8.4.": "Победа СССР в Великой Отечественной войне. Окончание Второй мировой войны (1944–сентябрь 1945 г.)",
    "9.": "СССР в 1945–1991 гг.",
    "9.1.": "СССР в 1945–1953 гг.",
    "9.2.": "СССР в середине 1950-х – первой половине 1960-х гг.",
    "9.3.": "Советское государство и общество в середине 1960-х – начале 1980-х гг.",
    "9.4.": "Политика перестройки. Распад СССР (1985–1991)",
    "10.": "Российская Федерация в 1992–2022 гг.",
    "10.1.": "Становление новой России (1992–1999)",
    "10.2.": "Россия в XXI в.: вызовы времени и задачи модернизации",
    "11.": "Всеобщая история. 1914–1945 гг.",
    "11.1.": "Мир накануне и в годы Первой мировой войны",
    "11.2.": "Мир в 1918–1939 гг.",
    "11.3.": "Вторая мировая война",
    "12.": "Всеобщая история. 1945–2022 гг.",
    "12.1.": "Страны Северной Америки и Европы во второй половине XX – начале XXI в.",
    "12.2.": "Страны Азии, Африки во второй половине XX – начале XXI в.",
    "12.3": "Страны Латинской Америки во второй половине XX – начале XXI в.",
    "12.3.": "Страны Латинской Америки во второй половине XX – начале XXI в.",
    "12.4.": "Международные отношения во второй половине XX – начале XXI в.",
    "12.5.": "Развитие науки и культуры во второй половине XX – начале XXI в.",
    "12.6.": "Современный мир",
}

# Social studies codifier (separate from History)
CODIFIER_THEMES_SOCIAL = {
    "1.": "Человек и общество",
    "1.1.": "Понятие личности",
    "1.2.": "Общественные ценности",
    "2.": "Экономика",
    "2.1.": "Экономические системы",
    "2.2.": "Рыночная экономика",
    "3.": "Социальная сфера",
    "3.1.": "Социальные группы",
    "3.2.": "Семья",
    "4.": "Политическая сфера",
    "4.1.": "Формы правления",
    "4.2.": "Политические партии",
    "5.": "Правовая сфера",
    "5.1.": "Конституционное право",
    "5.2.": "Уголовное право",
    "6.": "Духовная сфера",
    "6.1.": "Культура",
    "6.2.": "Религия",
}

# Mapping: subject name -> codifier dict
SUBJECT_CODIFIERS = {
    "История": CODIFIER_THEMES_HISTORY,
    "Обществознание": CODIFIER_THEMES_SOCIAL,
}


def _get_sync_session():
    """Create a sync SQLAlchemy session."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(settings.DATABASE_URL_SYNC, pool_size=2, max_overflow=5)
    return sessionmaker(bind=engine)()


def _clean_cell_text(cell):
    """Extract text from cell_0, excluding UI elements (selects, answer inputs)."""
    if not cell:
        return ""
    # Clone the cell to avoid modifying the original
    cell_copy = copy(cell)
    # Remove select elements and their parent labels (answer widgets)
    for select in cell_copy.find_all("select"):
        select.decompose()
    # Remove hidden inputs and text inputs inside the cell (answer widgets)
    for inp in cell_copy.find_all("input"):
        inp.decompose()
    # Remove button elements (answer buttons)
    for btn in cell_copy.find_all("button"):
        btn.decompose()
    # Get clean text
    text = cell_copy.get_text(separator="\n", strip=True)
    # Clean up excessive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# Column headers that should be excluded from stem text
_COLUMN_HEADERS = re.compile(
    r'^(?:НАЧАЛА СУЖДЕНИЙ|ВАРИАНТЫ ЗАВЕРШЕНИЯ СУЖДЕНИЙ|'
    r'ПРОЦЕССЫ|ФАКТЫ|СОБЫТИЯ|УЧАСТНИКИ|ГОДЫ|'
    r'ФРАГМЕНТЫ ИСТОЧНИКОВ|ХАРАКТЕРИСТИКИ|'
    r'ПАМЯТНИКИ КУЛЬТУРЫ|ПРОИЗВЕДЕНИЯ КУЛЬТУРЫ|'
    r'ПРОИСХОЖДЕНИЕ|НАЗВАНИЕ|'
    r'НАЧАЛА|ВАРИАНТЫ ЗАВЕРШЕНИЯ)\s*$',
    re.MULTILINE | re.IGNORECASE
)


def _clean_stem_text(text):
    """Remove column headers and clean up stem text."""
    # Remove lines that are just column headers
    text = _COLUMN_HEADERS.sub('', text)
    # Remove multiple blank lines left after header removal
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


_ANSWERS_PER_STEM_MARKERS = [
    "подберите по две",
    "подберите две",
    "к каждой позиции.*подберите две",
    "по две соответствующие",
    "две соответствующие",
]


def _detect_answers_per_stem(text):
    """Detect how many answers per stem from text markers.
    Returns 1 (default) or 2 (for "подберите по две" type tasks).
    """
    lower = text.lower()
    for marker in _ANSWERS_PER_STEM_MARKERS:
        if re.search(marker, lower):
            return 2
    return 1


def _extract_item_list(table):
    """Extract items from a table that has rows like <td><b>Label)</b></td><td>Text</td>.
    Returns list of {label, text} dicts.
    """
    items = []
    if not table:
        return items
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        label_cell = cells[0]
        text_cell = cells[1]
        # Extract label (e.g., "А", "Б", "1", "2")
        label_text = label_cell.get_text(strip=True).rstrip(")")
        label_text = label_text.strip()
        # Extract content text
        content = text_cell.get_text(separator=" ", strip=True)
        if content:
            items.append({"label": label_text, "text": content})
    return items


def _extract_matching_pairs(cell):
    """Extract matching pairs from cell_0.

    FIPI matching tasks have left/right columns as SEPARATE tables deep in nested structure.
    We find tables where first cell contains a label pattern like "А)", "Б)", "1)", "2)".

    Returns (left_items, right_items) where each is a list of {label, text} dicts.
    """
    if not cell:
        return None, None

    all_tables = cell.find_all("table")
    if len(all_tables) < 2:
        return None, None

    left_table = None
    right_table = None

    for t in all_tables:
        rows = t.find_all("tr")
        if len(rows) < 2:
            continue
        # Check if this table has the label+text pattern
        first_label = None
        is_valid = True
        for row in rows[:1]:
            tds = row.find_all("td")
            if len(tds) == 2:
                label_text = tds[0].get_text(strip=True).rstrip(")").strip()
                if re.match(r'^[А-Я]$', label_text):
                    first_label = "letter"
                elif re.match(r'^\d+$', label_text):
                    first_label = "number"
                else:
                    is_valid = False
            else:
                is_valid = False

        if not is_valid or not first_label:
            continue

        # Verify all rows have the same pattern
        labels_ok = True
        for row in rows:
            tds = row.find_all("td")
            if len(tds) != 2:
                labels_ok = False
                break
            lbl = tds[0].get_text(strip=True).rstrip(")").strip()
            if first_label == "letter" and not re.match(r'^[А-Я]$', lbl):
                labels_ok = False
                break
            if first_label == "number" and not re.match(r'^\d+$', lbl):
                labels_ok = False
                break

        if not labels_ok:
            continue

        items = _extract_item_list(t)
        if first_label == "letter" and left_table is None:
            left_table = items
        elif first_label == "number" and right_table is None:
            right_table = items

        if left_table and right_table:
            break

    if left_table and right_table:
        return left_table, right_table
    return None, None


def _detect_task_type(form, cell_text="", cell=None):
    """Detect task subtype from form structure, cleaned text, and cell DOM.
    Both matching and sequence tasks use <select> widgets on FIPI,
    so we must inspect the text and DOM to distinguish them.

    Returns (type, subtype) tuple.
    """
    selects = form.find_all("select")
    text_inputs = form.find_all("input", type="text")

    if selects:
        # Both matching and sequence tasks have selects.
        # Priority 1: explicit text keywords (most reliable)
        if _is_sequence_task(cell_text):
            return "TEST", "sequence"
        if _is_matching_task(cell_text):
            return "TEST", "matching"
        # Priority 2: DOM structure — matching tasks have a two-column table
        if cell and _has_matching_table(cell):
            return "TEST", "matching"
        # Fallback: assume matching (most common select-based type)
        return "TEST", "matching"
    elif text_inputs:
        return "TEST", "short_answer"
    else:
        return "ESSAY", "essay"


_SEQUENCE_MARKERS = [
    "хронологическ",
    "последовательност",
    "расположите в правильн",
    "расположите события",
    "расположите цифры",
    "запишите цифры",
    "правильном порядке",
]

_MATCHING_MARKERS = [
    "установите соответствие",
    "соедините",
    "пары",
    "соответстви",
]


def _is_sequence_task(text):
    """Determine if a task is a chronological-sequence task based on text markers."""
    lower = text.lower()
    for marker in _SEQUENCE_MARKERS:
        if marker in lower:
            return True
    return False


def _is_matching_task(text):
    """Determine if a task is a matching task based on text markers."""
    lower = text.lower()
    for marker in _MATCHING_MARKERS:
        if marker in lower:
            return True
    return False


def _has_matching_table(cell):
    """Check if the cell contains a two-column table (characteristic of matching tasks)."""
    if not cell:
        return False
    table = cell.find("table")
    if not table:
        return False
    rows = table.find_all("tr")
    if len(rows) < 2:
        return False
    # Check that rows have at least 2 columns
    for row in rows[:2]:
        cells = row.find_all("td")
        if len(cells) < 2:
            return False
    return True


def _extract_sequence_items(text):
    """Extract numbered items from a sequence task.
    Returns a list of {position, text} dicts for items like "1) event description".
    """
    items = []
    pattern = re.compile(r'(\d+)\)\s*(.+?)(?=\n\d+\)|$)', re.DOTALL)
    for match in pattern.finditer(text):
        num = match.group(1)
        item_text = match.group(2).strip()
        items.append({"position": int(num), "text": item_text})
    return items


def _extract_tasks_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    qblocks = soup.find_all("div", class_="qblock")
    tasks = []
    for qb in qblocks:
        task = {"block_id": qb.get("id", "").replace("q", "")}
        hint = qb.find("div", class_="hint")
        if hint:
            task["hint"] = hint.get_text(strip=True)
        form = qb.find("form", id=lambda x: x and x.startswith("checkform"))
        if not form:
            continue
        guid_input = form.find("input", {"name": "guid"})
        if not guid_input:
            continue
        task["guid"] = guid_input.get("value", "")

        cell = qb.find("td", class_="cell_0")
        if not cell:
            continue

        # Extract images from <img> tags AND ShowPictureQ() JavaScript calls
        images = [img.get("src", "") for img in cell.find_all("img") if img.get("src")]
        # Also extract from ShowPictureQ() calls in the full qblock HTML
        js_images = re.findall(r"ShowPictureQ\('([^']+)'\)", str(qb))
        images.extend(js_images)
        task["images"] = images

        # Clean text FIRST — remove UI elements before type detection
        task["text"] = _clean_cell_text(cell)

        # Detect task type using form structure + cleaned text + cell DOM
        task_type, subtype = _detect_task_type(form, task["text"], cell)
        task["type"] = task_type
        task["subtype"] = subtype

        # Type-specific processing
        if subtype == "matching":
            left_items, right_items = _extract_matching_pairs(cell)
            if left_items and right_items:
                # Clean stem text (remove column headers)
                for item in left_items:
                    item["text"] = _clean_stem_text(item["text"])
                for item in right_items:
                    item["text"] = _clean_stem_text(item["text"])

                task["matching_left"] = left_items
                task["matching_right"] = right_items
                task["answers_per_stem"] = _detect_answers_per_stem(task["text"])
                # Build options: for each left stem, offer all right column items
                task["options"] = [[{"value": item["label"], "text": item["text"]} for item in right_items]]

        elif subtype == "sequence":
            seq_items = _extract_sequence_items(task["text"])
            if seq_items:
                task["sequence_items"] = seq_items
                # The correct answer for a sequence is the permutation of positions
                # in correct order. We store the items as-is; the answer key
                # will be filled when the tutor reviews or from answer data.
                # For now, store the detected items as structured data.
                task["correct_answer_key"] = {
                    "type": "sequence",
                    "item_count": len(seq_items),
                }

        # Skip tasks with no usable text content
        if not task.get("text") and not task.get("images"):
            continue

        tasks.append(task)
    return tasks


def _build_text_content(task_data):
    """Build text_content dict from parsed task data, handling all subtypes."""
    text_content = {"text": task_data.get("text", "")}
    if task_data.get("images"):
        text_content["images"] = task_data["images"]
    if task_data.get("matching_left"):
        text_content["matching_left"] = task_data["matching_left"]
    if task_data.get("matching_right"):
        text_content["matching_right"] = task_data["matching_right"]
        text_content["options"] = [[{"value": item["label"], "text": item["text"]} for item in task_data["matching_right"]]]
    if task_data.get("answers_per_stem"):
        text_content["answers_per_stem"] = task_data["answers_per_stem"]
    elif task_data.get("options"):
        text_content["options"] = [[o["text"] if isinstance(o, dict) else o for o in opts] for opts in task_data["options"]]
    if task_data.get("sequence_items"):
        text_content["sequence_items"] = task_data["sequence_items"]
    return text_content


def _fetch_tasks_for_theme(theme_code, needed_count=None, task_type=None):
    """Fetch tasks from FIPI by paginating through all available pages.

    Uses pagesize=10 (FIPI returns 0 results for pagesize >= 50).
    If needed_count is None, fetches ALL available tasks.
    Stops when: enough tasks collected, or empty page reached, or 100 pages max.
    """
    import time

    all_tasks = []
    page = 1
    max_pages = 100  # safety limit (100 pages × 10 per page = 1000 max)

    with httpx.Client(timeout=30, follow_redirects=True, verify=False) as client:
        while page <= max_pages:
            resp = client.post(
                f"{BASE_URL}/questions.php",
                data={
                    "search": "1",
                    "pagesize": "10",
                    "proj": FIPI_PROJECT_ID,
                    "theme": theme_code,
                    "page": str(page),
                },
                headers=HEADERS,
            )
            html = resp.content.decode("windows-1251", errors="replace")
            page_tasks = _extract_tasks_from_html(html)

            if not page_tasks:
                break  # no more tasks on this theme

            all_tasks.extend(page_tasks)

            if needed_count and len(all_tasks) >= needed_count:
                break

            page += 1
            time.sleep(0.5)  # polite delay between requests

    if task_type and task_type != "MIX":
        all_tasks = [t for t in all_tasks if t.get("type") == task_type]

    if needed_count:
        return all_tasks[:needed_count]
    return all_tasks


def _save_tasks_to_db(db, theme, fetched_tasks):
    """Save fetched tasks to DB with deduplication per theme. Returns count of new tasks added."""
    from app.models import Task
    from app.services.content_parser import compute_text_hash
    from app.services.kim_mapping import classify_task
    from app.services.image_downloader import download_task_images

    added = 0
    for task_data in fetched_tasks:
        text_content = _build_text_content(task_data)

        # Download images if present
        raw_images = text_content.get("images", [])
        if raw_images:
            local_paths = download_task_images(raw_images)
            text_content["images"] = local_paths

        text_hash = compute_text_hash(text_content)

        # Dedup within this theme only (not globally)
        existing = db.query(Task).filter(
            Task.theme_id == theme.id,
            Task.metadata_["text_hash"].as_string() == text_hash,
        ).first()
        if existing:
            continue

        # Auto-classify KIM position and difficulty
        subtype = task_data.get("subtype", "")
        text = task_data.get("text", "")
        exam_position, difficulty_level = classify_task(subtype, text, text_content)

        task = Task(
            subject_id=theme.subject_id,
            theme_id=theme.id,
            type=task_data["type"],
            text_content=text_content,
            correct_answer_key=None,
            fipi_criteria=None,
            source_url=f"{BASE_URL}/questions.php?proj={FIPI_PROJECT_ID}&theme={theme.fipi_code}",
            metadata_={
                "text_hash": text_hash,
                "fipi_guid": task_data.get("guid"),
                "subtype": subtype,
            },
            exam_position=exam_position,
            difficulty_level=difficulty_level,
        )
        db.add(task)
        added += 1

    db.commit()
    return added


@celery_app.task(bind=True, name="sync_codifier")
def sync_codifier(self, subject_name="История"):
    from app.models import Subject, Theme
    db = _get_sync_session()
    try:
        subject = db.query(Subject).filter(Subject.name == subject_name).first()
        if not subject:
            subject = Subject(name=subject_name)
            db.add(subject)
            db.flush()

        codifier = SUBJECT_CODIFIERS.get(subject_name, CODIFIER_THEMES_HISTORY)

        created = 0
        for code, name in codifier.items():
            existing = db.query(Theme).filter(Theme.subject_id == subject.id, Theme.fipi_code == code).first()
            if not existing:
                db.add(Theme(subject_id=subject.id, fipi_code=code, name=name))
                created += 1

        db.commit()
        return {"created": created, "total": len(codifier)}
    finally:
        db.close()


def _sync_theme_core(theme_code, subject_id=None):
    """Core logic for full theme sync. Returns result dict."""
    from app.models import Theme, Task

    db = _get_sync_session()
    try:
        query = db.query(Theme).filter(Theme.fipi_code == theme_code)
        if subject_id:
            from uuid import UUID
            query = query.filter(Theme.subject_id == UUID(subject_id))
        theme = query.first()
        if not theme:
            return {"error": f"Theme {theme_code} not found in DB"}

        existing_count = db.query(Task).filter(Task.theme_id == theme.id).count()

        fetched = _fetch_tasks_for_theme(theme_code, needed_count=None)

        added = _save_tasks_to_db(db, theme, fetched)
        total = db.query(Task).filter(Task.theme_id == theme.id).count()

        return {
            "theme_code": theme_code,
            "theme_name": theme.name,
            "fetched_from_fipi": len(fetched),
            "added_new": added,
            "skipped_duplicates": len(fetched) - added,
            "total_in_db": total,
        }
    finally:
        db.close()


@celery_app.task(bind=True, name="sync_theme_full")
def sync_theme_full(self, theme_code):
    """Celery wrapper for full theme sync with progress reporting."""
    self.update_state(state="PROGRESS", meta={
        "status": f"Синхронизация темы {theme_code}...",
    })
    return _sync_theme_core(theme_code)


@celery_app.task(bind=True, name="sync_subject_full")
def sync_subject_full(self, subject_name="История"):
    """Full sync for all themes of a subject. Reports per-theme progress."""
    from app.models import Theme

    codifier = SUBJECT_CODIFIERS.get(subject_name, CODIFIER_THEMES_HISTORY)
    db = _get_sync_session()
    try:
        subject = db.query(Theme).filter(Theme.fipi_code == list(codifier.keys())[0]).first()
        if not subject:
            return {"error": f"Subject {subject_name} not found"}

        themes = db.query(Theme).filter(Theme.subject_id == subject.subject_id).all()
        theme_codes = [t.fipi_code for t in themes]
    finally:
        db.close()

    results = {}
    for i, code in enumerate(theme_codes):
        self.update_state(state="PROGRESS", meta={
            "current": i + 1,
            "total": len(theme_codes),
            "theme": code,
        })
        result = sync_theme_full(code)
        results[code] = result

    total_added = sum(r.get("added_new", 0) for r in results.values() if isinstance(r, dict))
    total_fetched = sum(r.get("fetched_from_fipi", 0) for r in results.values() if isinstance(r, dict))

    return {
        "subject": subject_name,
        "themes_processed": len(theme_codes),
        "total_fetched": total_fetched,
        "total_added": total_added,
        "per_theme": results,
    }


@celery_app.task(bind=True, name="create_test_from_fipi")
def create_test_from_fipi(self, tutor_id, title, theme_codes, count_per_theme, task_type, time_limit_minutes=None):
    """Create a test from LOCAL database only. No live FIPI requests."""
    from app.models import Theme, Task, Test, TestTask
    from uuid import UUID
    import random

    db = _get_sync_session()
    try:
        selected_task_ids = []
        theme_stats = {}
        warnings = []

        for theme_code in theme_codes:
            theme = db.query(Theme).filter(Theme.fipi_code == theme_code).first()
            if not theme:
                warnings.append(f"Тема {theme_code} не найдена в базе")
                theme_stats[theme_code] = 0
                continue

            query = db.query(Task).filter(Task.theme_id == theme.id)
            if task_type and task_type != "MIX":
                query = query.filter(Task.type == task_type)

            available = query.all()
            available_count = len(available)

            if available_count == 0:
                warnings.append(f"Тема {theme_code}: нет заданий в базе (нужна синхронизация)")
                theme_stats[theme_code] = 0
                continue

            take = min(count_per_theme, available_count)
            if take < count_per_theme:
                warnings.append(
                    f"Тема {theme_code}: доступно {available_count} заданий, "
                    f"запрошено {count_per_theme} (взято {take})"
                )

            chosen = random.sample(available, take)
            for t in chosen:
                selected_task_ids.append(str(t.id))
            theme_stats[theme_code] = take

        self.update_state(state="PROGRESS", meta={
            "stage": "creating",
            "status": f"Собрано {len(selected_task_ids)} заданий из локальной базы...",
            "tasks_found": len(selected_task_ids),
            "theme_stats": theme_stats,
        })

        if not selected_task_ids:
            return {
                "error": "Нет заданий в локальной базе. Запустите синхронизацию с ФИПИ.",
                "warnings": warnings,
            }

        test = Test(tutor_id=UUID(tutor_id), title=title, time_limit_minutes=time_limit_minutes)
        db.add(test)
        db.flush()

        random.shuffle(selected_task_ids)
        for i, task_id in enumerate(selected_task_ids):
            db.add(TestTask(test_id=test.id, task_id=UUID(task_id), order_number=i + 1))

        db.commit()
        db.refresh(test)

        result = {
            "test_id": str(test.id),
            "title": test.title,
            "tasks_count": len(selected_task_ids),
            "theme_stats": theme_stats,
        }
        if warnings:
            result["warnings"] = warnings
        return result
    finally:
        db.close()
