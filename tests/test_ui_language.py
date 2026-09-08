import pytest
from PySide6.QtCore import QDate, QTimer
from PySide6.QtWidgets import QApplication, QCalendarWidget, QDialog, QPushButton
from PySide6.QtGui import QPalette
from app import Window, STYLE
from search_dialog import SearchDialog
from search import SearchResult
from ui_theme import dark_palette
import i18n


@pytest.fixture
def window(tmp_path):
    application = QApplication.instance() or QApplication([])
    application.setStyle('Fusion')
    application.setPalette(dark_palette())
    application.setStyleSheet(STYLE)
    w = Window(tmp_path)
    yield w
    w.close()
    i18n.set_language('zh')


def test_language_preserves_queue_progress_and_settings(window):
    window.input.setPlainText('123')
    window.add_input()
    window.table.item(0, 3).setText('42%')
    window.table.selectRow(0)
    window.language.setCurrentIndex(1)
    assert window.start_button.text() == 'Start / resume'
    assert window.table.item(0, 3).text() == '42%'
    assert window.table.selectionModel().selectedRows()
    assert window.tasks[123]['status'] == '等待'
    assert window.store.settings()['language'] == 'en'
    assert window.settings()['mode'] == 'official'
    window.language.setCurrentIndex(0)
    assert window.start_button.text() == '开始 / 继续'


def test_filters_and_user_text_survive_language_switch(window):
    dialog = SearchDialog(window)
    dialog.example()
    dialog.title.setText('中文')
    dialog.submitted_from.set_value('2026-09-09')
    before = dialog.filters_from_ui()
    i18n.set_language('en')
    assert dialog.search_button.text() == 'Search all pages'
    assert dialog.filters_from_ui() == before
    assert dialog.title.text() == '中文'
    assert dialog.submitted_from.value_or_none() == '2026-09-09'
    dialog.reset_filters()
    assert dialog.status.currentText() == '缺省'
    dialog.reject()


@pytest.mark.parametrize('action,expected', [('OK', '2026-09-12'), ('Cancel', '2026-09-09'), ('Clear', None)])
def test_calendar_actions(window, action, expected):
    dialog = SearchDialog(window)
    i18n.set_language('en')
    field = dialog.submitted_from
    field.set_value('2026-09-09')
    errors = []

    def interact():
        popup = QApplication.activeModalWidget()
        try:
            calendar = popup.findChild(QCalendarWidget)
            assert calendar.selectedDate() == QDate(2026, 9, 9)
            assert calendar.headerTextFormat().background().color().name() == '#252a3a'
            assert calendar.verticalHeaderFormat() == QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
            calendar.setSelectedDate(QDate(2026, 9, 12))
            next(b for b in popup.findChildren(QPushButton) if b.text() == action).click()
        except BaseException as exc:
            errors.append(exc)
            popup.reject()

    QTimer.singleShot(0, interact)
    field.pick_date()
    assert not errors, errors
    assert field.value_or_none() == expected
    dialog.reject()


def test_sort_preserves_selected_beatmap(window):
    dialog = SearchDialog(window)
    rows = [dict(sid=2, title='Z', artist='X', modes=[0]),
            dict(sid=1, title='A', artist='Y', modes=[0])]
    dialog.finished_search(SearchResult(rows, True, '搜索完成'))
    dialog.table.selectRow(0)
    dialog.sort_field.setCurrentText('标题')
    assert [dialog.table.item(index.row(), 0).text()
            for index in dialog.table.selectionModel().selectedRows()] == ['2']
    dialog.reject()


def test_small_screen_filters_remain_reachable(window):
    i18n.set_language('en')
    dialog = SearchDialog(window)
    dialog.resize(800, 600)
    dialog.show()
    QApplication.processEvents()
    assert dialog.width() <= 800
    assert dialog.height() <= 600
    dialog.filter_scroll.ensureWidgetVisible(dialog.status_changed_to)
    QApplication.processEvents()
    assert dialog.filter_scroll.verticalScrollBar().value() > 0
    assert dialog.add_all.geometry().bottom() < dialog.height()
    dialog.reject()

