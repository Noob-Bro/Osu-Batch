import time
import threading
from pathlib import Path

import httpx
import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from app import Window, STYLE
from engine import Downloader, RateGate, Stopped


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    return app


def pump(qapp, predicate, seconds=3):
    until = time.monotonic() + seconds
    while not predicate() and time.monotonic() < until:
        qapp.processEvents()
        time.sleep(.005)
    qapp.processEvents()
    assert predicate()


@pytest.fixture
def window(tmp_path, qapp):
    w = Window(tmp_path / "data")
    w.directory.setText(str(tmp_path / "downloads"))
    w.mode.setCurrentIndex(2)
    w.show()
    yield w
    if w.active:
        w.pause()
        pump(qapp, lambda: not w.active)
    w.close()
    qapp.processEvents()


def test_queue_import_and_cancel(window):
    window.input.setPlainText("123\n123\nhttps://osu.ppy.sh/beatmapsets/456#osu/789\ninvalid")
    window.add_input()
    assert len(window.tasks) == 2
    assert window.input.toPlainText() == "invalid"
    window.table.selectRow(0)
    window.cancel_selected()
    assert window.tasks[123]["status"] == "已取消"
    window.remove_selected()
    assert list(window.tasks) == [456]


def test_mirror_video_options(window):
    window.no_video.setChecked(True)
    window.mirror.setCurrentIndex(1)
    assert not window.no_video.isChecked()
    assert not window.no_video.isEnabled()
    window.mode.setCurrentIndex(0)
    assert window.no_video.isEnabled()
    assert not window.mirror.isEnabled()


def test_queue_completes_multiple_tasks(window, qapp, tmp_path):
    class Fake:
        def clear_blocks(self): pass
        def download(self, sid, options, stop, emit):
            emit("测试源", 50, 100, 10, "下载中")
            return str(tmp_path / f"{sid}.osz"), "测试源"
    window.downloader = Fake()
    window.input.setPlainText("123 456 789")
    window.add_input()
    window.start()
    pump(qapp, lambda: all(t["status"] == "已完成" for t in window.tasks.values()))
    assert not window.running
    assert window.start_button.isEnabled()
    assert window.batch_options is None


def test_pause_and_resume_queue(window, qapp, tmp_path):
    class Blocking:
        def clear_blocks(self): pass
        def download(self, sid, options, stop, emit):
            stop.wait(2)
            if stop.is_set(): raise Stopped()
            return str(tmp_path / f"{sid}.osz"), "测试源"
    window.downloader = Blocking()
    window.input.setPlainText("123 456")
    window.add_input()
    window.start()
    assert len(window.active) == 1
    window.pause()
    pump(qapp, lambda: not window.active)
    assert all(t["status"] == "已暂停" for t in window.tasks.values())
    assert window.start_button.isEnabled()


def test_failed_task_and_retry(window, qapp, tmp_path):
    class FailOnce:
        count = 0
        def clear_blocks(self): pass
        def download(self, sid, options, stop, emit):
            self.count += 1
            if self.count == 1: raise OSError("private filesystem detail")
            return str(tmp_path / "123.osz"), "测试源"
    window.downloader = FailOnce()
    window.input.setPlainText("123")
    window.add_input()
    window.start()
    pump(qapp, lambda: window.tasks[123]["status"] == "失败")
    assert "private" not in window.tasks[123]["message"]
    window.retry()
    pump(qapp, lambda: window.tasks[123]["status"] == "已完成")


def test_search_dialog_full_results_and_invalidation(window,qapp):
    from search_dialog import SearchDialog
    from search import SearchResult
    row=dict(sid=123,artist='Laur',title='Song',creator='Mapper',status='ranked',modes=[0])
    class FakeSearch:
        def search(self,*args):
            return SearchResult([row],True,'搜索完成',2,4)
    dialog=SearchDialog(window,FakeSearch())
    dialog.source.setCurrentIndex(1)
    dialog.start_search()
    pump(qapp,lambda:not dialog.busy)
    assert dialog.add_all.isEnabled()
    dialog.artist.setText('Different')
    assert not dialog.add_all.isEnabled() and dialog.table.rowCount()==0
    dialog.reject()


def test_search_dialog_partial_requires_explicit_selection(window,qapp):
    from search_dialog import SearchDialog
    from search import SearchResult
    row=dict(sid=123,artist='Laur',title='Song',creator='Mapper',status='ranked',modes=[0])
    dialog=SearchDialog(window)
    dialog.finished_search(SearchResult([row],False,'结果不完整'))
    assert not dialog.add_all.isEnabled()
    dialog.choose(True)
    assert not dialog.chosen_ids
    dialog.table.selectRow(0)
    assert dialog.add_selected.isEnabled()
    dialog.choose(False)
    assert dialog.chosen_ids==[123]


def test_search_dialog_defaults_are_unset(window, qapp):
    from search_dialog import SearchDialog
    dialog = SearchDialog(window)
    assert dialog.title.text() == ''
    assert dialog.title_romanized.text() == ''
    assert dialog.artist.text() == ''
    assert dialog.artist_romanized.text() == ''
    assert dialog.source_text.text() == ''
    assert dialog.creator.text() == ''
    assert dialog.genre.currentText() == '缺省'
    assert dialog.language.currentText() == '缺省'
    assert dialog.mode.currentText() == '缺省'
    assert dialog.status.currentText() == '缺省'
    assert dialog.bpm_min.value() == -1 and dialog.bpm_max.value() == -1
    assert dialog.length_min.value() == -1 and dialog.length_max.value() == -1
    assert dialog.difficulty_min.value() == -1 and dialog.difficulty_max.value() == -1
    assert dialog.submitted_from.value_or_none() is None and dialog.submitted_to.value_or_none() is None
    assert dialog.updated_from.value_or_none() is None and dialog.updated_to.value_or_none() is None
    assert dialog.status_changed_from.value_or_none() is None and dialog.status_changed_to.value_or_none() is None
    assert dialog.submitted_from.calendar_button.isEnabled() and dialog.updated_from.calendar_button.isEnabled() and dialog.status_changed_from.calendar_button.isEnabled()
    assert dialog.sort_field.currentText() == '缺省'
    assert dialog.table.columnCount() == 17
    dialog.reject()


def test_search_dialog_builds_advanced_filters_and_sort(window, qapp):
    from search_dialog import SearchDialog
    dialog = SearchDialog(window)
    dialog.title.setText('純粋なルビー')
    dialog.title_romanized.setText('Pure Ruby')
    dialog.artist.setText('シキ')
    dialog.artist_romanized.setText('SHIKI')
    dialog.source_text.setText('BMS')
    dialog.creator.setText('Mapper')
    dialog.genre.setCurrentText('电子')
    dialog.language.setCurrentText('纯音乐')
    dialog.mode.setCurrentText('osu! standard (std)')
    dialog.status.setCurrentText('Ranked')
    dialog.bpm_min.setValue(180)
    dialog.bpm_max.setValue(190)
    dialog.length_min.setValue(120)
    dialog.length_max.setValue(180)
    dialog.difficulty_min.setValue(4)
    dialog.difficulty_max.setValue(6)
    dialog.submitted_from.set_value('2025-12-01')
    dialog.submitted_to.set_value('2025-12-31')
    dialog.updated_from.set_value('2026-01-01')
    dialog.updated_to.set_value('2026-09-01')
    dialog.status_changed_from.set_value('2026-08-01')
    dialog.status_changed_to.set_value('2026-08-31')
    dialog.sort_field.setCurrentText('谱面难度')
    dialog.sort_direction.setCurrentText('降序')
    filters = dialog.filters_from_ui()
    sort_spec = dialog.sort_from_ui()
    assert filters.title == '純粋なルビー' and filters.title_romanized == 'Pure Ruby'
    assert filters.artist == 'シキ' and filters.artist_romanized == 'SHIKI'
    assert filters.genre == 10 and filters.language == 5
    assert filters.mode == 0 and filters.status == 'ranked'
    assert filters.bpm_min == 180 and filters.bpm_max == 190
    assert filters.difficulty_min == 4 and filters.difficulty_max == 6
    assert filters.submitted_from == '2025-12-01' and filters.submitted_to == '2025-12-31'
    assert filters.updated_from == '2026-01-01' and filters.updated_to == '2026-09-01'
    assert filters.status_changed_from == '2026-08-01' and filters.status_changed_to == '2026-08-31'
    assert sort_spec.field == 'difficulty' and sort_spec.descending
    dialog.reject()


def test_search_dialog_sort_reorders_loaded_list_without_invalidating(window, qapp):
    from search_dialog import SearchDialog
    from search import SearchResult
    rows = [
        dict(sid=2, artist='Zed', artist_unicode='', title='Zulu', title_unicode='', creator='Mapper', status='ranked', modes=[0], beatmaps=[]),
        dict(sid=1, artist='Ann', artist_unicode='', title='Alpha', title_unicode='', creator='Mapper', status='ranked', modes=[0], beatmaps=[]),
    ]
    dialog = SearchDialog(window)
    dialog.finished_search(SearchResult(rows, True, '搜索完成'))
    assert dialog.table.rowCount() == 2
    assert dialog.result_data is not None
    dialog.sort_field.setCurrentText('标题（罗马化）')
    dialog.sort_direction.setCurrentText('升序')
    assert dialog.table.rowCount() == 2
    assert [row['sid'] for row in dialog.result_data.rows] == [1, 2]
    assert dialog.result_data is not None
    dialog.sort_direction.setCurrentText('降序')
    assert [row['sid'] for row in dialog.result_data.rows] == [2, 1]
    dialog.sort_field.setCurrentText('缺省')
    assert [row['sid'] for row in dialog.result_data.rows] == [2, 1]
    dialog.reject()

