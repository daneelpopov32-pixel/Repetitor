"""
Celery tasks for FIPI integration.
Uses sync SQLAlchemy to avoid event loop issues in Celery workers.
"""
import re
from copy import copy
import httpx
from bs4 import BeautifulSoup
import json
import logging
from datetime import datetime

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

CODIFIER_THEMES = {
    "1.": "Древний мир",
    "2.": "Россия в IX - начале XII в.",
    "3.": "Россия в XII - XV вв.",
    "4.": "Россия в XVI - XVII вв.",
    "5.": "Россия в XVIII в.",
    "6.": "Россия в первой половине XIX в.",
    "7.": "Россия во второй половине XIX в.",
    "7.1.": "Отмена крепостного права",
    "7.2.": "Реформы Александра II",
    "7.3.": "Культура второй половины XIX в.",
    "7.4.": "Экономика второй половины XIX в.",
    "7.5.": "Общественное движение",
    "7.6.": "Политический строй",
    "7.7.": "Россия в 1917-1941 гг.",
    "7.8.": "Великая Отечественная война",
    "7.9.": "Послевоенная Россия",
    "8.": "Россия в 1990-2000-х гг.",
    "8.1.": "Перестройка",
    "8.2.": "Распад СССР",
    "8.3.": "Россия в 1990-е годы",
    "8.4.": "Россия в 2000-е годы",
    "9.": "Всеобщая история",
    "9.1.": "Древний мир (всеобщая)",
    "9.2.": "Средние века (всеобщая)",
    "9.3.": "Новое время",
    "9.4.": "Новейшее время",
    "10.": "Право",
    "10.1.": "Конституционное право",
    "10.2.": "Уголовное право",
    "11.": "Обществознание",
    "11.1.": "Человек и общество",
    "11.2.": "Экономика",
    "12.": "География",
    "12.1.": "Физическая география",
    "12.2.": "Экономическая география",
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

        # Extract images
        images = cell.find_all("img")
        task["images"] = [img.get("src", "") for img in images if img.get("src")]

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


def _fetch_tasks_for_theme(theme_code, needed_count, task_type=None):
    with httpx.Client(timeout=30, follow_redirects=True, verify=False) as client:
        resp = client.post(
            f"{BASE_URL}/questions.php",
            data={"search": "1", "pagesize": "100", "proj": FIPI_PROJECT_ID, "theme": theme_code, "page": "1"},
            headers=HEADERS,
        )
        html = resp.content.decode("windows-1251", errors="replace")
        all_tasks = _extract_tasks_from_html(html)
        if task_type and task_type != "MIX":
            all_tasks = [t for t in all_tasks if t.get("type") == task_type]
        return all_tasks[:needed_count]


@celery_app.task(bind=True, name="sync_codifier")
def sync_codifier(self, subject_name="История"):
    from app.models import Subject, Theme
    from app.services.content_parser import compute_text_hash
    db = _get_sync_session()
    try:
        subject = db.query(Subject).filter(Subject.name == subject_name).first()
        if not subject:
            subject = Subject(name=subject_name)
            db.add(subject)
            db.flush()

        created = 0
        for code, name in CODIFIER_THEMES.items():
            existing = db.query(Theme).filter(Theme.subject_id == subject.id, Theme.fipi_code == code).first()
            if not existing:
                db.add(Theme(subject_id=subject.id, fipi_code=code, name=name))
                created += 1

        db.commit()
        return {"created": created, "total": len(CODIFIER_THEMES)}
    finally:
        db.close()


@celery_app.task(bind=True, name="fetch_fipi_tasks")
def fetch_fipi_tasks(self, theme_codes, count_per_theme=5, task_type="TEST"):
    from app.models import Theme, Task
    from app.services.content_parser import compute_text_hash
    import time

    results = {}
    for i, theme_code in enumerate(theme_codes):
        self.update_state(state="PROGRESS", meta={"current": i + 1, "total": len(theme_codes), "theme": theme_code})
        db = _get_sync_session()
        try:
            theme = db.query(Theme).filter(Theme.fipi_code == theme_code).first()
            if not theme:
                results[theme_code] = []
                continue

            existing = db.query(Task).filter(Task.theme_id == theme.id).count()
            needed = max(0, count_per_theme - existing)

            if needed == 0:
                tasks = db.query(Task).filter(Task.theme_id == theme.id).limit(count_per_theme).all()
                results[theme_code] = [{"id": str(t.id), "type": t.type} for t in tasks]
                continue

            fetched = _fetch_tasks_for_theme(theme_code, needed, task_type)
            for task_data in fetched:
                text_content = _build_text_content(task_data)

                text_hash = compute_text_hash(text_content)
                if db.query(Task).filter(Task.metadata_["text_hash"].as_string() == text_hash).first():
                    continue

                task = Task(
                    subject_id=theme.subject_id, theme_id=theme.id, type=task_data["type"],
                    text_content=text_content, correct_answer_key=None, fipi_criteria=None,
                    source_url=f"{BASE_URL}/questions.php?proj={FIPI_PROJECT_ID}&theme={theme_code}",
                    metadata_={"text_hash": text_hash, "fipi_guid": task_data.get("guid"), "subtype": task_data.get("subtype")},
                )
                db.add(task)

            db.commit()

            tasks = db.query(Task).filter(Task.theme_id == theme.id).limit(count_per_theme).all()
            results[theme_code] = [{"id": str(t.id), "type": t.type} for t in tasks]
            time.sleep(1.5)
        except Exception as e:
            logger.error(f"Error fetching theme {theme_code}: {e}")
            results[theme_code] = []
        finally:
            db.close()

    return results


@celery_app.task(bind=True, name="create_test_from_fipi")
def create_test_from_fipi(self, tutor_id, title, theme_codes, count_per_theme, task_type, time_limit_minutes=None):
    from app.models import Theme, Task, Test, TestTask
    from app.services.content_parser import compute_text_hash
    import time

    self.update_state(state="PROGRESS", meta={"stage": "fetching", "status": "Ищем задания на ФИПИ..."})

    # Fetch tasks
    results = {}
    for i, theme_code in enumerate(theme_codes):
        self.update_state(state="PROGRESS", meta={"stage": "fetching", "status": f"Обработка темы {theme_code} ({i+1}/{len(theme_codes)})..."})
        db = _get_sync_session()
        try:
            theme = db.query(Theme).filter(Theme.fipi_code == theme_code).first()
            if not theme:
                results[theme_code] = []
                continue

            existing = db.query(Task).filter(Task.theme_id == theme.id).count()
            needed = max(0, count_per_theme - existing)

            if needed == 0:
                tasks = db.query(Task).filter(Task.theme_id == theme.id).limit(count_per_theme).all()
                results[theme_code] = [{"id": str(t.id), "type": t.type} for t in tasks]
                continue

            fetched = _fetch_tasks_for_theme(theme_code, needed, task_type)
            for task_data in fetched:
                text_content = _build_text_content(task_data)

                text_hash = compute_text_hash(text_content)
                if db.query(Task).filter(Task.metadata_["text_hash"].as_string() == text_hash).first():
                    continue

                task = Task(
                    subject_id=theme.subject_id, theme_id=theme.id, type=task_data["type"],
                    text_content=text_content, correct_answer_key=None, fipi_criteria=None,
                    source_url=f"{BASE_URL}/questions.php?proj={FIPI_PROJECT_ID}&theme={theme_code}",
                    metadata_={"text_hash": text_hash, "fipi_guid": task_data.get("guid"), "subtype": task_data.get("subtype")},
                )
                db.add(task)

            db.commit()
            tasks = db.query(Task).filter(Task.theme_id == theme.id).limit(count_per_theme).all()
            results[theme_code] = [{"id": str(t.id), "type": t.type} for t in tasks]
            time.sleep(1.5)
        except Exception as e:
            logger.error(f"Error: {e}")
            results[theme_code] = []
        finally:
            db.close()

    # Collect task IDs
    all_task_ids = []
    theme_stats = {}
    for theme_code, tasks in results.items():
        theme_stats[theme_code] = len(tasks)
        for t in tasks:
            if t.get("id"):
                all_task_ids.append(t["id"])

    self.update_state(state="PROGRESS", meta={"stage": "creating", "status": f"Найдено {len(all_task_ids)} заданий. Создаём тест...", "tasks_found": len(all_task_ids), "theme_stats": theme_stats})

    # Create test
    from uuid import UUID
    db = _get_sync_session()
    try:
        test = Test(tutor_id=UUID(tutor_id), title=title, time_limit_minutes=time_limit_minutes)
        db.add(test)
        db.flush()

        for i, task_id in enumerate(all_task_ids):
            db.add(TestTask(test_id=test.id, task_id=UUID(task_id), order_number=i + 1))

        db.commit()
        db.refresh(test)

        return {"test_id": str(test.id), "title": test.title, "tasks_count": len(all_task_ids), "theme_stats": theme_stats}
    finally:
        db.close()
