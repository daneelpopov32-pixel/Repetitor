import hashlib
import json
import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Task, Theme, Subject


async def parse_fipi_page(url: str, subject_id: int, theme_id: int) -> list[dict]:
    """Parse a FIPI bank page and extract tasks."""
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    tasks = []

    task_blocks = soup.select(".task-item, .question-block, .exam-task")

    if not task_blocks:
        task_blocks = soup.find_all("div", class_=re.compile(r"task|question|problem", re.I))

    for block in task_blocks:
        task_data = _extract_task(block, url)
        if task_data:
            tasks.append(task_data)

    return tasks


def _extract_task(block, source_url: str) -> dict | None:
    """Extract task data from a single HTML block."""
    from app.tasks.fipi_tasks import _clean_cell_text

    text_div = block.find("div", class_=re.compile(r"text|content|body", re.I))
    if not text_div:
        text_div = block

    # Use cleaning function to remove UI elements (selects, inputs, buttons)
    text = _clean_cell_text(text_div)
    if not text or len(text) < 10:
        return None

    images = []
    for img in text_div.find_all("img"):
        src = img.get("src", "")
        if src:
            full_url = urljoin(source_url, src)
            images.append(full_url)

    task_type = "TEST"
    criteria_block = block.find("div", class_=re.compile(r"criter|критер", re.I))
    fipi_criteria = None
    if criteria_block:
        task_type = "ESSAY"
        fipi_criteria = _parse_criteria(criteria_block)

    answer_block = block.find("div", class_=re.compile(r"answer|key|ответ", re.I))
    correct_answer_key = None
    if answer_block:
        correct_answer_key = _parse_answer_key(answer_block)

    text_content = {"text": text, "images": images}

    options_block = block.find("ol") or block.find("ul")
    if options_block:
        options = [li.get_text(strip=True) for li in options_block.find_all("li")]
        if options:
            text_content["options"] = options

    return {
        "text_content": text_content,
        "type": task_type,
        "correct_answer_key": correct_answer_key,
        "fipi_criteria": fipi_criteria,
        "source_url": source_url,
    }


def _parse_criteria(block) -> list[dict]:
    """Parse FIPI criteria from HTML block."""
    criteria = []
    items = block.find_all("li") or block.find_all("p")
    for i, item in enumerate(items, 1):
        text = item.get_text(strip=True)
        score_match = re.search(r"(\d+)\s*(?:балл|макс)", text, re.I)
        max_score = int(score_match.group(1)) if score_match else 1
        criteria.append({
            "id": f"criterion_{i}",
            "name": text,
            "max_score": max_score,
        })
    return criteria


def _parse_answer_key(block) -> dict:
    """Parse answer key from HTML block."""
    text = block.get_text(strip=True)

    numbers = re.findall(r"(\d+)", text)
    if len(numbers) > 1:
        return {"type": "multiple_choice", "correct_answer": [int(n) for n in numbers]}
    elif len(numbers) == 1:
        return {"type": "single_choice", "correct_answer": int(numbers[0])}

    return {"type": "short_answer", "correct_answer": text}


def compute_text_hash(text_content: dict) -> str:
    """Compute a hash of text_content for duplicate detection."""
    normalized = json.dumps(text_content, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(normalized.encode()).hexdigest()


async def check_duplicate(db: AsyncSession, text_content: dict) -> bool:
    """Check if a task with identical text_content already exists."""
    text_hash = compute_text_hash(text_content)
    result = await db.execute(
        select(Task).where(
            Task.metadata_["text_hash"].as_string() == text_hash
        )
    )
    return result.scalar_one_or_none() is not None


async def import_task(
    db: AsyncSession,
    subject_id: int,
    theme_id: int,
    task_type: str,
    text_content: dict,
    correct_answer_key: dict | None = None,
    fipi_criteria: list | None = None,
    source_url: str | None = None,
) -> dict:
    """Import a single task with duplicate check."""
    if await check_duplicate(db, text_content):
        raise ValueError("Task already exists (duplicate detected)")

    if task_type == "TEST" and not correct_answer_key:
        raise ValueError("TEST tasks require correct_answer_key")
    if task_type == "ESSAY" and not fipi_criteria:
        raise ValueError("ESSAY tasks require fipi_criteria")

    text_hash = compute_text_hash(text_content)
    task = Task(
        subject_id=subject_id,
        theme_id=theme_id,
        type=task_type,
        text_content=text_content,
        correct_answer_key=correct_answer_key,
        fipi_criteria=fipi_criteria,
        source_url=source_url,
        metadata_={"text_hash": text_hash},
    )
    db.add(task)
    await db.commit()

    return {
        "task_id": task.id,
        "type": task.type,
        "theme_id": task.theme_id,
    }


async def import_from_url(
    db: AsyncSession,
    url: str,
    subject_id: int,
    theme_id: int,
) -> dict:
    """Parse FIPI page and import all tasks found."""
    parsed_tasks = await parse_fipi_page(url, subject_id, theme_id)

    imported = 0
    skipped = 0
    errors = []

    for pt in parsed_tasks:
        try:
            await import_task(
                db,
                subject_id=subject_id,
                theme_id=theme_id,
                task_type=pt["type"],
                text_content=pt["text_content"],
                correct_answer_key=pt.get("correct_answer_key"),
                fipi_criteria=pt.get("fipi_criteria"),
                source_url=pt.get("source_url"),
            )
            imported += 1
        except ValueError as e:
            if "already exists" in str(e):
                skipped += 1
            else:
                errors.append(str(e))

    return {
        "total_parsed": len(parsed_tasks),
        "imported": imported,
        "skipped_duplicates": skipped,
        "errors": errors,
    }
