"""Unit tests for FIPI image extraction scenarios."""
import pytest
from app.tasks.fipi_tasks import _extract_tasks_from_html, _resolve_image_url

# ─── Mock HTML templates for each scenario ────────────────────────────

# Standalone block with ShowPicture (context image)
STANDALONE_BLOCK = '''
<div class="qblock">
  <div class="hint">Прочитайте текст и выполните задания.</div>
  <script>ShowPicture('docs/068A227D253BA6C04D0C832387FD0D89/docs/AAAA1111BBBB2222CCCC3333DDDD4444/xs3docsrcAAAA1111BBBB2222CCCC3333DDDD4444_1_1234567890.jpg');</script>
</div>
'''

# Task block with ShowPictureQ (own image)
TASK_WITH_OWN_IMAGE = '''
<div class="qblock" id="qTEST01">
  <div class="hint">Задание 1.</div>
  <form id="checkformTEST01" method="get">
    <input name="guid" type="hidden" value="AAAA1111BBBB2222CCCC3333DDDD4444"/>
  </form>
  <td class="cell_0">
    <p>Какое изображение изображено на картинке?</p>
    <script>ShowPictureQ('docs/068A227D253BA6C04D0C832387FD0D89/questions/EEEE5555FFFF6666AAAA7777BBBB8888(copy1)/xs3qstsrcEEEE5555FFFF6666AAAA7777BBBB8888_1_9876543210.jpg');</script>
  </td>
</div>
'''

# Task block WITHOUT ShowPictureQ (no own image)
TASK_WITHOUT_IMAGE = '''
<div class="qblock" id="qTEST02">
  <div class="hint">Задание 2.</div>
  <form id="checkformTEST02" method="get">
    <input name="guid" type="hidden" value="11112222333344445555666677778888"/>
  </form>
  <td class="cell_0">
    <p>Заполните пропуск в предложении.</p>
  </td>
</div>
'''

# Empty qblock (no form, no images)
EMPTY_BLOCK = '''
<div class="qblock">
  <div class="hint">Прочитайте текст.</div>
</div>
'''


class TestImageScenario1_OwnOnly:
    """Scenario 1: Task has own ShowPictureQ, no active context."""

    def test_own_image_no_context(self):
        """Task with ShowPictureQ but no preceding standalone block."""
        html = f"""
        <html><body>
        {TASK_WITH_OWN_IMAGE}
        </body></html>
        """
        tasks = _extract_tasks_from_html(html)
        assert len(tasks) == 1
        task = tasks[0]
        assert task["image_scenario"] == "own_only"
        assert len(task["images"]) == 1
        assert "xs3qstsrc" in task["images"][0]
        assert "questions/" in task["images"][0]


class TestImageScenario2_InheritedContext:
    """Scenario 2: Task has no own image, inherits from preceding standalone block."""

    def test_inherited_from_standalone(self):
        """Task without ShowPictureQ inherits context from preceding standalone block."""
        html = f"""
        <html><body>
        {STANDALONE_BLOCK}
        {TASK_WITHOUT_IMAGE}
        </body></html>
        """
        tasks = _extract_tasks_from_html(html)
        assert len(tasks) == 1
        task = tasks[0]
        assert task["image_scenario"] == "inherited_context"
        assert len(task["images"]) == 1
        assert "xs3docsrc" in task["images"][0]

    def test_context_carries_forward(self):
        """Context image persists across multiple tasks."""
        html = f"""
        <html><body>
        {STANDALONE_BLOCK}
        {TASK_WITHOUT_IMAGE}
        {TASK_WITHOUT_IMAGE.replace('qTEST02', 'qTEST03').replace('checkformTEST02', 'checkformTEST03').replace('11112222333344445555666677778888', '22223333444455556666777788889999')}
        {TASK_WITHOUT_IMAGE.replace('qTEST02', 'qTEST04').replace('checkformTEST02', 'checkformTEST04').replace('11112222333344445555666677778888', '33334444555566667777888899990000')}
        </body></html>
        """
        tasks = _extract_tasks_from_html(html)
        assert len(tasks) == 3
        for i, task in enumerate(tasks):
            assert task["image_scenario"] == "inherited_context", f"Task {i} should inherit context"
            assert len(task["images"]) == 1
            assert "xs3docsrc" in task["images"][0]
            # All should have the SAME context image
            assert task["images"][0] == tasks[0]["images"][0]


class TestImageScenario3_ContextAndOwn:
    """Scenario 3: Task has own image AND inherits context."""

    def test_context_plus_own(self):
        """Task with ShowPictureQ inherits context from preceding standalone block."""
        html = f"""
        <html><body>
        {STANDALONE_BLOCK}
        {TASK_WITH_OWN_IMAGE}
        </body></html>
        """
        tasks = _extract_tasks_from_html(html)
        assert len(tasks) == 1
        task = tasks[0]
        assert task["image_scenario"] == "context_and_own"
        assert len(task["images"]) == 2
        # First image is context (xs3docsrc), second is own (xs3qstsrc)
        assert "xs3docsrc" in task["images"][0]
        assert "xs3qstsrc" in task["images"][1]


class TestImageScenario_LongChain:
    """Test long chain of tasks inheriting the same context image."""

    def test_5_tasks_one_context(self):
        """5 consecutive tasks all inherit the same context image."""
        # Create 5 task blocks with different GUIDs
        tasks_html = ""
        guids = [f"{i:032x}" for i in range(1, 6)]
        for i, guid in enumerate(guids):
            tasks_html += f'''
            <div class="qblock" id="qCHAIN{i}">
              <div class="hint">Задание {i+1}.</div>
              <form id="checkformCHAIN{i}" method="get">
                <input name="guid" type="hidden" value="{guid}"/>
              </form>
              <td class="cell_0">
                <p>Вопрос {i+1} по схеме.</p>
              </td>
            </div>
            '''

        html = f"""
        <html><body>
        {STANDALONE_BLOCK}
        {tasks_html}
        </body></html>
        """
        tasks = _extract_tasks_from_html(html)
        assert len(tasks) == 5

        # All 5 should inherit the same context image
        context_url = tasks[0]["images"][0]
        for i, task in enumerate(tasks):
            assert task["image_scenario"] == "inherited_context", f"Task {i} should inherit"
            assert len(task["images"]) == 1
            assert task["images"][0] == context_url, f"Task {i} should have same context image"

    def test_context_overwritten_by_new_standalone(self):
        """New standalone block resets the context for subsequent tasks."""
        html = f"""
        <html><body>
        {STANDALONE_BLOCK}
        {TASK_WITHOUT_IMAGE}
        {TASK_WITHOUT_IMAGE.replace('qTEST02', 'qTEST03').replace('checkformTEST02', 'checkformTEST03').replace('11112222333344445555666677778888', '22223333444455556666777788889999')}
        <div class="qblock">
          <div class="hint">Новый текст.</div>
          <script>ShowPicture('docs/068A227D253BA6C04D0C832387FD0D89/docs/BBBB1111CCCC2222DDDD3333EEEE4444/xs3docsrcBBBB1111CCCC2222DDDD3333EEEE4444_1_1111111111.jpg');</script>
        </div>
        {TASK_WITHOUT_IMAGE.replace('qTEST02', 'qTEST04').replace('checkformTEST02', 'checkformTEST04').replace('11112222333344445555666677778888', '33334444555566667777888899990000')}
        </body></html>
        """
        tasks = _extract_tasks_from_html(html)
        assert len(tasks) == 3

        # First two tasks have context from first standalone block
        assert "AAAA1111" in tasks[0]["images"][0]
        assert "AAAA1111" in tasks[1]["images"][0]

        # Third task has context from second standalone block
        assert "BBBB1111" in tasks[2]["images"][0]


class TestImageUrlResolution:
    """Test _resolve_image_url for all known patterns."""

    def test_relative_path(self):
        url = _resolve_image_url("../../docs/test.jpg")
        assert url == "https://ege.fipi.ru/docs/test.jpg"

    def test_docs_prefix(self):
        url = _resolve_image_url("docs/test.jpg")
        assert url == "https://ege.fipi.ru/docs/test.jpg"

    def test_xs3docsrc_bare(self):
        url = _resolve_image_url("xs3docsrcAAAA1111BBBB2222CCCC3333DDDD4444_1_123.jpg")
        assert "docs/068A227D253BA6C04D0C832387FD0D89/docs/AAAA1111BBBB2222CCCC3333DDDD4444/" in url
        assert url.endswith("xs3docsrcAAAA1111BBBB2222CCCC3333DDDD4444_1_123.jpg")

    def test_xs3qstsrc_bare(self):
        url = _resolve_image_url("xs3qstsrcEEEE5555FFFF6666AAAA7777BBBB8888_1_456.jpg")
        assert "questions/EEEE5555FFFF6666AAAA7777BBBB8888(copy1)/" in url
        assert url.endswith("xs3qstsrcEEEE5555FFFF6666AAAA7777BBBB8888_1_456.jpg")

    def test_already_absolute(self):
        url = _resolve_image_url("https://ege.fipi.ru/docs/test.jpg")
        assert url == "https://ege.fipi.ru/docs/test.jpg"
