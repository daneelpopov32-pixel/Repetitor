"""
FIPI Bank Parser - Full implementation with DB import and rate limiting.
Run: python -m scripts.fipi_parser
"""
import asyncio
import httpx
from bs4 import BeautifulSoup
import re
import json
import time
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://repetitor:repetitor@localhost:5432/repetitor")

from app.database import async_session
from app.models import Subject, Theme, Task
from app.services.content_parser import compute_text_hash
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://ege.fipi.ru/bank"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://ege.fipi.ru/bank/index.php?proj=068A227D253BA6C04D0C832387FD0D89",
}

THEME_NAMES = {
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


async def fetch_page(client, theme=None, page=1, pagesize=100):
    url = f"{BASE_URL}/questions.php"
    data = {
        "search": "1",
        "pagesize": str(pagesize),
        "proj": "068A227D253BA6C04D0C832387FD0D89",
        "page": str(page),
    }
    if theme:
        data["theme"] = theme
    resp = await client.post(url, data=data, headers=HEADERS)
    return resp.content.decode("windows-1251", errors="replace")


def extract_tasks_from_html(html):
    """Wrapper that delegates to the main parser in app.tasks.fipi_tasks."""
    from app.tasks.fipi_tasks import _extract_tasks_from_html
    return _extract_tasks_from_html(html)


async def parse_fipi_history(project_id="068A227D253BA6C04D0C832387FD0D89"):
    stats = {
        "themes_processed": 0,
        "themes_error": 0,
        "tasks_imported": 0,
        "tasks_skipped": 0,
        "tasks_error": 0,
    }

    async with httpx.AsyncClient(timeout=30, follow_redirects=True, verify=False) as client:
        async with async_session() as db:
            # Get or create subject
            result = await db.execute(select(Subject).where(Subject.name == "История"))
            subject = result.scalar_one_or_none()
            if not subject:
                subject = Subject(name="История")
                db.add(subject)
                await db.flush()
            subject_id = subject.id

            # Get existing task hashes for deduplication
            result = await db.execute(select(Task.text_content))
            existing_hashes = set()
            for row in result.scalars():
                if row:
                    existing_hashes.add(compute_text_hash(row))

        for theme_code, theme_name in THEME_NAMES.items():
            logger.info(f"Processing theme {theme_code} ({theme_name})...")

            try:
                async with async_session() as db:
                    result = await db.execute(
                        select(Theme).where(
                            Theme.subject_id == subject_id,
                            Theme.fipi_code == theme_code,
                        )
                    )
                    theme = result.scalar_one_or_none()
                    if not theme:
                        theme = Theme(
                            subject_id=subject_id,
                            fipi_code=theme_code,
                            name=theme_name,
                        )
                        db.add(theme)
                        await db.commit()
                        await db.refresh(theme)
                    theme_id = theme.id

                html = await fetch_page(client, theme=theme_code, page=1, pagesize=100)
                tasks = extract_tasks_from_html(html)

                if not tasks:
                    logger.info(f"  No tasks found")
                    stats["themes_processed"] += 1
                    continue

                imported, skipped, errors = 0, 0, 0
                async with async_session() as db:
                    for task_data in tasks:
                        try:
                            from app.tasks.fipi_tasks import _build_text_content
                            text_content = _build_text_content(task_data)

                            text_hash = compute_text_hash(text_content)
                            if text_hash in existing_hashes:
                                skipped += 1
                                continue
                            existing_hashes.add(text_hash)

                            task = Task(
                                subject_id=subject_id,
                                theme_id=theme_id,
                                type=task_data["type"],
                                text_content=text_content,
                                correct_answer_key=None,
                                fipi_criteria=None,
                                source_url=f"{BASE_URL}/questions.php?proj={project_id}&theme={theme_code}",
                                metadata_={
                                    "text_hash": text_hash,
                                    "fipi_guid": task_data.get("guid"),
                                    "fipi_block_id": task_data.get("block_id"),
                                    "subtype": task_data.get("subtype"),
                                    "hint": task_data.get("hint"),
                                },
                            )
                            db.add(task)
                            imported += 1
                        except Exception as e:
                            logger.error(f"  Error importing task: {e}")
                            errors += 1

                    await db.commit()

                stats["themes_processed"] += 1
                stats["tasks_imported"] += imported
                stats["tasks_skipped"] += skipped
                stats["tasks_error"] += errors

                logger.info(
                    f"  {len(tasks)} found, {imported} imported, "
                    f"{skipped} skipped, {errors} errors"
                )

                # Rate limiting: 1.5 seconds between requests
                await asyncio.sleep(1.5)

            except Exception as e:
                logger.error(f"Error processing theme {theme_code}: {e}")
                stats["themes_error"] += 1
                continue

    logger.info("\n=== PARSING COMPLETE ===")
    logger.info(f"Themes processed: {stats['themes_processed']}")
    logger.info(f"Themes with errors: {stats['themes_error']}")
    logger.info(f"Tasks imported: {stats['tasks_imported']}")
    logger.info(f"Tasks skipped (duplicates): {stats['tasks_skipped']}")
    logger.info(f"Tasks with errors: {stats['tasks_error']}")

    return stats


if __name__ == "__main__":
    asyncio.run(parse_fipi_history())
