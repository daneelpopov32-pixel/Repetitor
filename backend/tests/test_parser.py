"""Unit tests for the FIPI HTML parser."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.tasks.fipi_tasks import (
    _extract_tasks_from_html,
    _clean_cell_text,
    _extract_matching_pairs,
    _detect_task_type,
    _build_text_content,
)


# --- Mock HTML templates ---

SHORT_ANSWER_HTML = """
<div class="qblock" id="q123">
  <div class="hint">Краткий ответ</div>
  <table><tr><td class="cell_0">
    <p>В каком году произошло Крещение Руси?</p>
  </td></tr></table>
  <form id="checkform123">
    <input type="hidden" name="guid" value="abc-123-guid" />
    <input type="text" name="answer" />
  </form>
</div>
"""

MATCHING_HTML = """
<div class="qblock" id="q456">
  <div class="hint">Соответствие</div>
  <table><tr><td class="cell_0">
    <table><tr><td>Установите соответствие между событиями и датами:</td></tr></table>
    <table>
      <tr><td><b>А)</b></td><td>Битва на Куликовом поле</td></tr>
      <tr><td><b>Б)</b></td><td>Стояние на Угре</td></tr>
      <tr><td><b>В)</b></td><td>Ледовое побоище</td></tr>
    </table>
    <table>
      <tr><td><b>1)</b></td><td>1380 год</td></tr>
      <tr><td><b>2)</b></td><td>1480 год</td></tr>
      <tr><td><b>3)</b></td><td>1242 год</td></tr>
    </table>
  </td></tr></table>
  <form id="checkform456">
    <input type="hidden" name="guid" value="def-456-guid" />
    <select name="ans_1"><option value="1">1</option><option value="2">2</option><option value="3">3</option></select>
    <select name="ans_2"><option value="1">1</option><option value="2">2</option><option value="3">3</option></select>
    <select name="ans_3"><option value="1">1</option><option value="2">2</option><option value="3">3</option></select>
  </form>
</div>
"""

ESSAY_HTML = """
<div class="qblock" id="q789">
  <div class="hint">Развёрнутый ответ</div>
  <table><tr><td class="cell_0">
    <p>Используя исторические знания, приведите три аргумента в пользу того,
    что реформы Петра I способствовали модернизации России.</p>
  </td></tr></table>
  <form id="checkform789">
    <input type="hidden" name="guid" value="ghi-789-guid" />
  </form>
</div>
"""

MAP_TASK_HTML = """
<div class="qblock" id="q101">
  <div class="hint">Работа с картой</div>
  <table><tr><td class="cell_0">
    <p>Определите государство, территория которого показана на карте.</p>
    <img src="/images/map_task_1.png" />
  </td></tr></table>
  <form id="checkform101">
    <input type="hidden" name="guid" value="jkl-101-guid" />
    <input type="text" name="answer" />
  </form>
</div>
"""

SEQUENCE_HTML = """
<div class="qblock" id="q202">
  <div class="hint">Хронологическая последовательность</div>
  <table><tr><td class="cell_0">
    <p>Расположите в хронологической последовательности исторические события:</p>
    <p>1) создание Союза благоденствия</p>
    <p>2) созыв первого Земского собора</p>
    <p>3) заключение Вестфальского мира</p>
  </td></tr></table>
  <form id="checkform202">
    <input type="hidden" name="guid" value="mno-202-guid" />
    <select name="ans_1"><option value="1">1</option><option value="2">2</option><option value="3">3</option></select>
    <select name="ans_2"><option value="1">1</option><option value="2">2</option><option value="3">3</option></select>
    <select name="ans_3"><option value="1">1</option><option value="2">2</option><option value="3">3</option></select>
  </form>
</div>
"""

SEQUENCE_HTML_WITH_GARBAGE = """
<div class="qblock" id="q303">
  <div class="hint">Хронологическая последовательность</div>
  <table><tr><td class="cell_0">
    <p>Расположите в хронологической последовательности исторические события:</p>
    <p>1) заключение Туркманчайского мирного договора между Россией и Персией</p>
    <p>2) начало старообрядческого раскола в Русской Православной Церкви</p>
    <p>3) издание Генрихом IV Нантского эдикта</p>
  </td></tr></table>
  <form id="checkform303">
    <input type="hidden" name="guid" value="pqr-303-guid" />
    <select name="ans_1"><option value="1">1</option><option value="2">2</option><option value="3">3</option></select>
    <select name="ans_2"><option value="1">1</option><option value="2">2</option><option value="3">3</option></select>
    <select name="ans_3"><option value="1">1</option><option value="2">2</option><option value="3">3</option></select>
  </form>
</div>
"""

MIXED_HTML = SHORT_ANSWER_HTML + MATCHING_HTML + SEQUENCE_HTML + ESSAY_HTML + MAP_TASK_HTML


# --- Tests ---

def test_detect_short_answer():
    from bs4 import BeautifulSoup
    html = '<form id="checkform"><input type="text" name="answer" /></form>'
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form")
    assert _detect_task_type(form, "Какой-то текст") == ("TEST", "short_answer")


def test_detect_matching():
    from bs4 import BeautifulSoup
    html = '<form id="checkform"><select name="a"><option>1</option></select></form>'
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form")
    assert _detect_task_type(form, "Установите соответствие между ПРОЦЕССАМИ и ФАКТАМИ") == ("TEST", "matching")


def test_detect_sequence():
    from bs4 import BeautifulSoup
    html = '<form id="checkform"><select name="a"><option>1</option></select></form>'
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form")
    assert _detect_task_type(form, "Расположите в хронологической последовательности") == ("TEST", "sequence")


def test_detect_essay():
    from bs4 import BeautifulSoup
    html = '<form id="checkform"><input type="hidden" name="guid" value="x" /></form>'
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form")
    assert _detect_task_type(form, "Напишите сочинение") == ("ESSAY", "essay")


def test_clean_cell_text_removes_selects():
    from bs4 import BeautifulSoup
    html = '<td class="cell_0"><p>Вопрос</p><select><option>1</option></select></td>'
    soup = BeautifulSoup(html, "html.parser")
    cell = soup.find("td")
    text = _clean_cell_text(cell)
    assert "select" not in text.lower()
    assert "Вопрос" in text


def test_clean_cell_text_removes_inputs():
    from bs4 import BeautifulSoup
    html = '<td class="cell_0"><p>Текст задания</p><input type="text" name="ans" /></td>'
    soup = BeautifulSoup(html, "html.parser")
    cell = soup.find("td")
    text = _clean_cell_text(cell)
    assert "ans" not in text
    assert "Текст задания" in text


def test_clean_cell_text_preserves_table():
    from bs4 import BeautifulSoup
    html = '<td class="cell_0"><p>Условие</p><table><tr><td>А</td><td>Описание</td></tr></table></td>'
    soup = BeautifulSoup(html, "html.parser")
    cell = soup.find("td")
    text = _clean_cell_text(cell)
    assert "Условие" in text
    assert "А" in text
    assert "Описание" in text


def test_extract_matching_pairs():
    from bs4 import BeautifulSoup
    # FIPI format: separate left and right tables
    html = '''<td class="cell_0">
      <table><tr><td>Condition text</td></tr></table>
      <table>
        <tr><td><b>А)</b></td><td>Кресло</td></tr>
        <tr><td><b>Б)</b></td><td>Стул</td></tr>
      </table>
      <table>
        <tr><td><b>1)</b></td><td>Мебель</td></tr>
        <tr><td><b>2)</b></td><td>Предмет</td></tr>
      </table>
    </td>'''
    soup = BeautifulSoup(html, "html.parser")
    cell = soup.find("td")
    left, right = _extract_matching_pairs(cell)
    assert left is not None
    assert right is not None
    assert len(left) == 2
    assert len(right) == 2
    assert left[0]["label"] == "А"
    assert left[0]["text"] == "Кресло"
    assert right[0]["label"] == "1"
    assert right[0]["text"] == "Мебель"


def test_extract_matching_pairs_3x6():
    """Real FIPI task: 4 stems (А-Г) and 6 options (1-6)."""
    from bs4 import BeautifulSoup
    html = '''<td class="cell_0">
      <table><tr><td>Установите соответствие:</td></tr></table>
      <table>
        <tr><td><b>А)</b></td><td>Событие 1</td></tr>
        <tr><td><b>Б)</b></td><td>Событие 2</td></tr>
        <tr><td><b>В)</b></td><td>Событие 3</td></tr>
        <tr><td><b>Г)</b></td><td>Событие 4</td></tr>
      </table>
      <table>
        <tr><td><b>1)</b></td><td>Вариант 1</td></tr>
        <tr><td><b>2)</b></td><td>Вариант 2</td></tr>
        <tr><td><b>3)</b></td><td>Вариант 3</td></tr>
        <tr><td><b>4)</b></td><td>Вариант 4</td></tr>
        <tr><td><b>5)</b></td><td>Вариант 5</td></tr>
        <tr><td><b>6)</b></td><td>Вариант 6</td></tr>
      </table>
    </td>'''
    soup = BeautifulSoup(html, "html.parser")
    cell = soup.find("td")
    left, right = _extract_matching_pairs(cell)
    assert left is not None
    assert right is not None
    assert len(left) == 4
    assert len(right) == 6
    assert [i["label"] for i in left] == ["А", "Б", "В", "Г"]
    assert [i["label"] for i in right] == ["1", "2", "3", "4", "5", "6"]


def test_extract_short_answer_task():
    tasks = _extract_tasks_from_html(SHORT_ANSWER_HTML)
    assert len(tasks) == 1
    t = tasks[0]
    assert t["type"] == "TEST"
    assert t["subtype"] == "short_answer"
    assert "Крещение Руси" in t["text"]
    assert t["guid"] == "abc-123-guid"
    # No garbage digits from UI elements
    assert "123456" not in t["text"]


def test_extract_matching_task():
    tasks = _extract_tasks_from_html(MATCHING_HTML)
    assert len(tasks) == 1
    t = tasks[0]
    assert t["type"] == "TEST"
    assert t["subtype"] == "matching"
    # Text should contain the condition, not select garbage
    assert "установите соответствие" in t["text"].lower()
    assert "123456" not in t["text"]
    # Matching pairs should be extracted
    assert t.get("matching_left") is not None
    assert t.get("matching_right") is not None
    assert len(t["matching_left"]) == 3
    assert len(t["matching_right"]) == 3


def test_extract_essay_task():
    tasks = _extract_tasks_from_html(ESSAY_HTML)
    assert len(tasks) == 1
    t = tasks[0]
    assert t["type"] == "ESSAY"
    assert t["subtype"] == "essay"
    assert "Петр" in t["text"] or "Петра" in t["text"]
    assert t["guid"] == "ghi-789-guid"


def test_extract_map_task():
    tasks = _extract_tasks_from_html(MAP_TASK_HTML)
    assert len(tasks) == 1
    t = tasks[0]
    assert t["type"] == "TEST"
    assert t["subtype"] == "short_answer"
    assert "карте" in t["text"]
    assert len(t.get("images", [])) == 1
    assert "map_task_1" in t["images"][0]


def test_mixed_html():
    tasks = _extract_tasks_from_html(MIXED_HTML)
    assert len(tasks) == 5
    types = [t["subtype"] for t in tasks]
    assert "short_answer" in types
    assert "matching" in types
    assert "sequence" in types
    assert "essay" in types


def test_extract_sequence_task():
    """Sequence task with selects must be classified as 'sequence', not 'matching'."""
    tasks = _extract_tasks_from_html(SEQUENCE_HTML)
    assert len(tasks) == 1
    t = tasks[0]
    assert t["type"] == "TEST"
    assert t["subtype"] == "sequence"
    # Text should contain the condition and numbered events, no select garbage
    assert "хронологической последовательности" in t["text"].lower()
    assert "123456" not in t["text"]
    assert "А123" not in t["text"]
    assert "Б123" not in t["text"]
    # Numbered items should be in the text
    assert "Союза благоденствия" in t["text"]
    assert "Земского собора" in t["text"]
    assert "Вестфальского мира" in t["text"]
    # Sequence items should be extracted
    assert t.get("sequence_items") is not None
    assert len(t["sequence_items"]) == 3
    # correct_answer_key should be sequence type
    assert t.get("correct_answer_key", {}).get("type") == "sequence"


def test_extract_sequence_task_with_garbageselects():
    """Even with select garbage in the HTML, sequence text must be clean."""
    tasks = _extract_tasks_from_html(SEQUENCE_HTML_WITH_GARBAGE)
    assert len(tasks) == 1
    t = tasks[0]
    assert t["subtype"] == "sequence"
    assert "Туркманчайского" in t["text"]
    assert "старообрядческого" in t["text"]
    assert "Нантского" in t["text"]
    # No UI garbage
    assert "123456" not in t["text"]
    assert "А123" not in t["text"]
    assert "Б123" not in t["text"]
    assert "В23" not in t["text"]
    assert "Г3" not in t["text"]


def test_sequence_not_confused_with_matching():
    """A matching task with 'Установите соответствие' must NOT be classified as sequence."""
    tasks = _extract_tasks_from_html(MATCHING_HTML)
    assert len(tasks) == 1
    t = tasks[0]
    assert t["subtype"] == "matching"
    assert t.get("matching_left") is not None


def test_build_text_content_sequence():
    data = {
        "text": "Хронология",
        "sequence_items": [{"position": 1, "text": "Event A"}, {"position": 2, "text": "Event B"}],
    }
    result = _build_text_content(data)
    assert result["sequence_items"] == [{"position": 1, "text": "Event A"}, {"position": 2, "text": "Event B"}]


def test_build_text_content_basic():
    data = {"text": "Hello", "images": ["img.png"], "options": [[{"text": "A"}, {"text": "B"}]]}
    result = _build_text_content(data)
    assert result["text"] == "Hello"
    assert result["images"] == ["img.png"]
    assert result["options"] == [["A", "B"]]


def test_build_text_content_matching():
    data = {
        "text": "Соответствие",
        "matching_left": [{"label": "А", "text": "Левый"}],
        "matching_right": [{"label": "1", "text": "Правый"}],
    }
    result = _build_text_content(data)
    assert result["matching_left"] == [{"label": "А", "text": "Левый"}]
    assert result["matching_right"] == [{"label": "1", "text": "Правый"}]


def test_no_garbage_in_any_task():
    """Ensure no task text contains digit-only sequences like '123456' or '23456'."""
    tasks = _extract_tasks_from_html(MIXED_HTML)
    for t in tasks:
        text = t.get("text", "")
        # Check for the specific garbage patterns the user reported
        assert "123456" not in text, f"Task {t.get('block_id')} has garbage '123456'"
        assert "23456" not in text, f"Task {t.get('block_id')} has garbage '23456'"
        assert "3456" not in text, f"Task {t.get('block_id')} has garbage '3456'"


def test_no_7letter_garbage_pattern():
    """The specific garbage pattern from the bug report: А123456/Б123456/.../Ж6.
    This is a FIPI UI widget with 7 letters and decreasing digits.
    It must never appear in parsed task text.
    """
    from bs4 import BeautifulSoup
    import re

    # Simulate the exact garbage pattern the user reported
    garbage_html = """
    <div class="qblock" id="q_garbage">
      <div class="hint">Соответствие</div>
      <table><tr><td class="cell_0">
        <p>Установите соответствие между событиями и участниками:</p>
        <table>
          <tr><td>А) Событие 1</td><td>1) Участник 1</td></tr>
          <tr><td>Б) Событие 2</td><td>2) Участник 2</td></tr>
        </table>
      </td></tr></table>
      <form id="checkform_garbage">
        <input type="hidden" name="guid" value="garbage-guid" />
        <select name="ans0"><option value="1">1</option><option value="2">2</option></select>
        <select name="ans1"><option value="1">1</option><option value="2">2</option></select>
      </form>
    </div>
    """

    tasks = _extract_tasks_from_html(garbage_html)
    assert len(tasks) == 1
    t = tasks[0]
    text = t["text"]

    # The 7-letter garbage pattern must NOT appear
    garbage_pattern = re.compile(r'[А-Я]\d{2,}')
    assert not garbage_pattern.search(text), f"Garbage pattern found in text: {text}"
    # Specific patterns from the bug report
    assert "А123456" not in text
    assert "Б123456" not in text
    assert "В23456" not in text
    assert "Г3456" not in text
    assert "Д456" not in text
    assert "Е56" not in text
    assert "Ж6" not in text
    # But the actual task content should be present
    assert "Событие 1" in text
    assert "Участник 1" in text


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
