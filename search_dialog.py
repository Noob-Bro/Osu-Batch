import threading
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import QObject, QDate, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView, QCalendarWidget, QComboBox, QDialog, QDoubleSpinBox, QGridLayout,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton, QSpinBox,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QScrollArea, QSizePolicy,
)
from ui_theme import configure_calendar
from i18n import (QComboBox, QDialog, QDoubleSpinBox, QGroupBox, QLabel,
                  QLineEdit, QPushButton, QSpinBox, QTableWidget, tr)

from search import (
    Filters, GAME_MODES, GENRES, LANGUAGES, MODE_NAMES, Searcher, SearchResult,
    SORT_DIRECTIONS, SORT_FIELDS, STATUSES, SortSpec, sort_rows,
)


class SearchEvents(QObject):
    progress = Signal(str)
    result = Signal(object)


def _number_text(value, decimals=1):
    if value is None:
        return '—'
    value = float(value)
    if decimals == 0 or value.is_integer():
        return str(int(value))
    return f'{value:.{decimals}f}'.rstrip('0').rstrip('.')


def _range_text(values, formatter):
    values = sorted(set(values))
    if not values:
        return '—'
    if len(values) == 1:
        return formatter(values[0])
    return f'{formatter(values[0])} ～ {formatter(values[-1])}'


def _length_text(seconds):
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f'{hours}:{minutes:02d}:{seconds:02d}' if hours else f'{minutes}:{seconds:02d}'


def _date_text(value):
    value = str(value or '')
    return value[:10] if len(value) >= 10 else (value or '—')


class OptionalDateInput(QWidget):
    """Clearable date input with both keyboard entry and a calendar picker."""

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)
        self.edit = QLineEdit()
        self.edit.setPlaceholderText('YYYY-MM-DD（缺省）')
        self.edit.setMaxLength(10)
        self.edit.setToolTip('可直接输入 YYYY-MM-DD；留空表示不筛选。')
        self.calendar_button = QPushButton('日历')
        self.calendar_button.setToolTip('打开日历选择日期')
        self.calendar_button.setMinimumWidth(60)
        self.calendar_button.setAutoDefault(False)
        row.addWidget(self.edit, 1)
        row.addWidget(self.calendar_button)
        self.edit.textChanged.connect(lambda _text: self.changed.emit())
        self.calendar_button.clicked.connect(self.pick_date)

    def value_or_none(self):
        return self.edit.text().strip() or None

    def clear_value(self):
        self.edit.clear()

    def set_value(self, value):
        if isinstance(value, QDate):
            value = value.toString('yyyy-MM-dd')
        self.edit.setText(str(value or ''))

    def pick_date(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('选择日期')
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)
        calendar = QCalendarWidget(dialog)
        configure_calendar(calendar)
        calendar.setMinimumSize(350, 270)
        current = QDate.fromString(self.edit.text().strip(), 'yyyy-MM-dd')
        if current.isValid():
            calendar.setSelectedDate(current)
        layout.addWidget(calendar)
        actions = QHBoxLayout()
        clear = QPushButton('清空')
        cancel = QPushButton('取消')
        ok = QPushButton('确定')
        clear.setAutoDefault(False)
        cancel.setAutoDefault(False)
        ok.setDefault(True)
        ok.setObjectName('accent')
        actions.addWidget(clear)
        actions.addStretch()
        actions.addWidget(cancel)
        actions.addWidget(ok)
        layout.addLayout(actions)

        cleared = {'value': False}

        def clear_and_accept():
            cleared['value'] = True
            self.clear_value()
            dialog.accept()

        clear.clicked.connect(clear_and_accept)
        cancel.clicked.connect(dialog.reject)
        ok.clicked.connect(dialog.accept)
        calendar.activated.connect(lambda _date: dialog.accept())
        if dialog.exec() == QDialog.DialogCode.Accepted and not cleared['value']:
            self.set_value(calendar.selectedDate())


class SearchDialog(QDialog):
    def __init__(self, parent, searcher=None):
        super().__init__(parent)
        self.setWindowTitle('筛选谱面 · 搜索并加入队列')
        available = self.screen().availableGeometry()
        self.resize(min(1380, available.width() - 40), min(860, available.height() - 80))
        self.searcher = searcher or Searcher()
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='search')
        self.events = SearchEvents()
        self.events.progress.connect(self.show_progress)
        self.events.result.connect(self.finished_search)
        self.busy = self.closing = False
        self.stop = threading.Event()
        self.result_data = None
        self.base_rows = []
        self.last_search_message = ''
        self.chosen_ids = []

        layout = QVBoxLayout(self)

        top = QGridLayout()
        top.addWidget(QLabel('搜索来源'), 0, 0)
        self.source = QComboBox()
        self.source.addItem('osu! 官方（需官网会话）', 'official')
        self.source.addItem('Sayobot 小夜（无需登录）', 'sayobot')
        top.addWidget(self.source, 0, 1)
        top.setColumnStretch(1, 1)
        self.reset_button = QPushButton('清空筛选')
        self.reset_button.clicked.connect(self.reset_filters)
        top.addWidget(self.reset_button, 1, 0)
        self.preset = QPushButton('填入 Laur / Ranked / std 示例')
        self.preset.clicked.connect(self.example)
        top.addWidget(self.preset, 1, 1)
        layout.addLayout(top)

        self.filter_scroll = QScrollArea()
        self.filter_scroll.setWidgetResizable(True)
        filter_content = QWidget()
        filters_layout = QVBoxLayout(filter_content)
        filters_layout.setContentsMargins(0, 0, 0, 0)
        self.filter_scroll.setWidget(filter_content)
        layout.addWidget(self.filter_scroll, 2)

        # ---------- Basic metadata ----------
        basic_group = QGroupBox('基础信息')
        basic = QGridLayout(basic_group)
        self.title = QLineEdit()
        self.title.setPlaceholderText('缺省；匹配原文/Unicode 或罗马化标题')
        self.title_romanized = QLineEdit()
        self.title_romanized.setPlaceholderText('缺省；仅匹配罗马化标题')
        self.artist = QLineEdit()
        self.artist.setPlaceholderText('缺省；匹配原文/Unicode 或罗马化艺术家')
        self.artist_romanized = QLineEdit()
        self.artist_romanized.setPlaceholderText('缺省；仅匹配罗马化艺术家')
        self.source_text = QLineEdit()
        self.source_text.setPlaceholderText('缺省；歌曲 / 作品来源')
        self.creator = QLineEdit()
        self.creator.setPlaceholderText('缺省；谱面作者')
        for widget in (
            self.title, self.title_romanized, self.artist, self.artist_romanized,
            self.source_text, self.creator,
        ):
            widget.setMaxLength(200)
        self.match = QComboBox()
        self.match.addItems(['艺术家精确匹配', '艺术家包含匹配（可含合作曲）'])

        basic.addWidget(QLabel('标题'), 0, 0)
        basic.addWidget(self.title, 0, 1)
        basic.addWidget(QLabel('标题（罗马化）'), 0, 2)
        basic.addWidget(self.title_romanized, 0, 3)
        basic.addWidget(QLabel('艺术家'), 1, 0)
        basic.addWidget(self.artist, 1, 1)
        basic.addWidget(QLabel('艺术家（罗马化）'), 1, 2)
        basic.addWidget(self.artist_romanized, 1, 3)
        basic.addWidget(self.match, 3, 1, 1, 3)
        basic.addWidget(QLabel('来源'), 2, 0)
        basic.addWidget(self.source_text, 2, 1)
        basic.addWidget(QLabel('谱面作者'), 2, 2)
        basic.addWidget(self.creator, 2, 3)
        basic.setColumnStretch(1, 1)
        basic.setColumnStretch(3, 1)
        filters_layout.addWidget(basic_group)

        # ---------- Category filters ----------
        category_group = QGroupBox('分类')
        category = QGridLayout(category_group)
        self.genre = QComboBox()
        self.genre.addItems(GENRES)
        self.language = QComboBox()
        self.language.addItems(LANGUAGES)
        self.mode = QComboBox()
        self.mode.addItems(GAME_MODES)
        self.status = QComboBox()
        self.status.addItems(STATUSES)
        category.addWidget(QLabel('流派'), 0, 0)
        category.addWidget(self.genre, 0, 1)
        category.addWidget(QLabel('语言'), 0, 2)
        category.addWidget(self.language, 0, 3)
        category.addWidget(QLabel('谱面模式'), 1, 0)
        category.addWidget(self.mode, 1, 1)
        category.addWidget(QLabel('谱面状态'), 1, 2)
        category.addWidget(self.status, 1, 3)
        for col in (1, 3):
            category.setColumnStretch(col, 1)
        filters_layout.addWidget(category_group)

        # ---------- Numeric range filters ----------
        range_group = QGroupBox('数值范围')
        ranges = QGridLayout(range_group)
        self.bpm_min = self._double_spin(1000, 1)
        self.bpm_max = self._double_spin(1000, 1)
        self.length_min = self._int_spin(24 * 60 * 60)
        self.length_max = self._int_spin(24 * 60 * 60)
        self.difficulty_min = self._double_spin(100, 2)
        self.difficulty_max = self._double_spin(100, 2)
        ranges.addWidget(QLabel('BPM'), 0, 0)
        ranges.addWidget(self.bpm_min, 0, 1)
        ranges.addWidget(QLabel('～'), 0, 2)
        ranges.addWidget(self.bpm_max, 0, 3)
        ranges.addWidget(QLabel('长度（秒）'), 1, 0)
        ranges.addWidget(self.length_min, 1, 1)
        ranges.addWidget(QLabel('～'), 1, 2)
        ranges.addWidget(self.length_max, 1, 3)
        ranges.addWidget(QLabel('谱面难度（★）'), 2, 0)
        ranges.addWidget(self.difficulty_min, 2, 1)
        ranges.addWidget(QLabel('～'), 2, 2)
        ranges.addWidget(self.difficulty_max, 2, 3)
        for col in (1, 3):
            ranges.setColumnStretch(col, 1)
        filters_layout.addWidget(range_group)

        # ---------- Date filters ----------
        date_group = QGroupBox('日期（可直接输入，也可点击日历选择）')
        dates = QGridLayout(date_group)
        self.submitted_from = OptionalDateInput()
        self.submitted_to = OptionalDateInput()
        self.updated_from = OptionalDateInput()
        self.updated_to = OptionalDateInput()
        self.status_changed_from = OptionalDateInput()
        self.status_changed_to = OptionalDateInput()

        dates.addWidget(QLabel('提交日期'), 0, 0)
        dates.addWidget(self.submitted_from, 0, 1)
        dates.addWidget(QLabel('～'), 0, 2)
        dates.addWidget(self.submitted_to, 0, 3)
        dates.addWidget(QLabel('更新日期'), 1, 0)
        dates.addWidget(self.updated_from, 1, 1)
        dates.addWidget(QLabel('～'), 1, 2)
        dates.addWidget(self.updated_to, 1, 3)
        dates.addWidget(QLabel('状态改变日期'), 2, 0)
        dates.addWidget(self.status_changed_from, 2, 1)
        dates.addWidget(QLabel('～'), 2, 2)
        dates.addWidget(self.status_changed_to, 2, 3)
        for col in (1, 3):
            dates.setColumnStretch(col, 1)
        filters_layout.addWidget(date_group)

        # ---------- Sorting ----------
        sort_row = QHBoxLayout()
        sort_row.addWidget(QLabel('当前列表排序'))
        self.sort_field = QComboBox()
        self.sort_field.addItems(SORT_FIELDS)
        self.sort_field.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.sort_field.setMinimumContentsLength(12)
        sort_row.addWidget(self.sort_field)
        self.sort_direction = QComboBox()
        self.sort_direction.addItems(SORT_DIRECTIONS)
        self.sort_direction.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.sort_direction.setMinimumContentsLength(8)
        sort_row.addWidget(self.sort_direction)
        sort_hint = QLabel('（排序只重排已加载列表，不重新搜索、不清空结果）')
        sort_hint.setWordWrap(True)
        sort_hint.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        sort_row.addWidget(sort_hint, 1)
        sort_row.addStretch()
        layout.addLayout(sort_row)

        self.note = QLabel()
        self.note.setWordWrap(True)
        self.note.setStyleSheet('color:#a6acc2;font-size:12px')
        layout.addWidget(self.note)
        self.update_source_note()

        controls = QHBoxLayout()
        self.search_button = QPushButton('搜索全部分页')
        self.search_button.setObjectName('accent')
        self.search_button.clicked.connect(self.start_search)
        controls.addWidget(self.search_button)
        self.cancel_button = QPushButton('取消搜索')
        self.cancel_button.clicked.connect(self.stop.set)
        self.cancel_button.setEnabled(False)
        controls.addWidget(self.cancel_button)
        controls.addStretch()
        self.state = QLabel('所有筛选条件默认为缺省；设置条件后搜索。')
        self.state.setWordWrap(True)
        controls.addWidget(self.state, 1)
        layout.addLayout(controls)

        headers = [
            '谱面集 ID', '标题', '标题（罗马化）', '艺术家', '艺术家（罗马化）',
            '来源', '流派', '语言', 'BPM', '长度', '谱面作者', '模式', '谱面难度',
            '状态', '提交日期', '更新日期', '状态改变日期',
        ]
        self.table = QTableWidget(0, len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().hide()
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(1, 240)
        for col, width in [
            (0, 120), (2, 180), (3, 170), (4, 180), (5, 170), (6, 100), (7, 90),
            (8, 90), (9, 90), (10, 130), (11, 100), (12, 190), (13, 90),
            (14, 110), (15, 110), (16, 120),
        ]:
            self.table.setColumnWidth(col, width)
        self.table.cellDoubleClicked.connect(
            lambda row, col: QDesktopServices.openUrl(QUrl(f'https://osu.ppy.sh/beatmapsets/{self.table.item(row, 0).text()}'))
        )
        layout.addWidget(self.table, 1)

        actions = QHBoxLayout()
        self.add_all = QPushButton('全部加入下载队列')
        self.add_all.setObjectName('accent')
        self.add_all.clicked.connect(lambda: self.choose(True))
        actions.addWidget(self.add_all)
        self.add_selected = QPushButton('加入选中项')
        self.add_selected.clicked.connect(lambda: self.choose(False))
        actions.addWidget(self.add_selected)
        actions.addStretch()
        close = QPushButton('关闭')
        close.clicked.connect(self.reject)
        actions.addWidget(close)
        layout.addLayout(actions)

        self.filter_inputs = [
            self.source, self.title, self.title_romanized, self.artist, self.artist_romanized,
            self.source_text, self.creator, self.match, self.genre, self.language, self.mode,
            self.status, self.bpm_min, self.bpm_max, self.length_min, self.length_max,
            self.difficulty_min, self.difficulty_max, self.submitted_from, self.submitted_to,
            self.updated_from, self.updated_to, self.status_changed_from, self.status_changed_to,
            self.preset, self.reset_button,
        ]

        self.source.currentIndexChanged.connect(self.source_changed)
        for widget in [self.match, self.genre, self.language, self.mode, self.status]:
            widget.currentIndexChanged.connect(self.invalidate)
        for widget in [
            self.title, self.title_romanized, self.artist, self.artist_romanized,
            self.source_text, self.creator,
        ]:
            widget.textChanged.connect(self.invalidate)
        for widget in [
            self.bpm_min, self.bpm_max, self.length_min, self.length_max,
            self.difficulty_min, self.difficulty_max,
        ]:
            widget.valueChanged.connect(self.invalidate)
        for widget in [
            self.submitted_from, self.submitted_to, self.updated_from, self.updated_to,
            self.status_changed_from, self.status_changed_to,
        ]:
            widget.changed.connect(self.invalidate)

        # Sorting deliberately does NOT invalidate the search. It only reorders the
        # currently loaded rows and can be changed repeatedly after a search completes.
        self.sort_field.currentIndexChanged.connect(self.apply_sort)
        self.sort_field.currentIndexChanged.connect(self.update_sort_state)
        self.sort_direction.currentIndexChanged.connect(self.apply_sort)
        self.table.itemSelectionChanged.connect(self.buttons)
        self.update_sort_state()
        self.buttons()

    @staticmethod
    def _double_spin(maximum, decimals):
        widget = QDoubleSpinBox()
        widget.setRange(-1, maximum)
        widget.setDecimals(decimals)
        widget.setSpecialValueText('缺省')
        widget.setValue(-1)
        return widget

    @staticmethod
    def _int_spin(maximum):
        widget = QSpinBox()
        widget.setRange(-1, maximum)
        widget.setSpecialValueText('缺省')
        widget.setValue(-1)
        return widget

    @staticmethod
    def _optional_spin(widget):
        return None if widget.value() < 0 else widget.value()

    def example(self):
        self.reset_filters()
        self.artist_romanized.setText('Laur')
        self.status.setCurrentText('Ranked')
        self.mode.setCurrentText('osu! standard (std)')
        self.match.setCurrentIndex(0)

    def reset_filters(self):
        for widget in (
            self.title, self.title_romanized, self.artist, self.artist_romanized,
            self.source_text, self.creator,
        ):
            widget.clear()
        self.match.setCurrentIndex(0)
        self.genre.setCurrentText('缺省')
        self.language.setCurrentText('缺省')
        self.mode.setCurrentText('缺省')
        self.status.setCurrentText('缺省')
        for widget in [
            self.bpm_min, self.bpm_max, self.length_min, self.length_max,
            self.difficulty_min, self.difficulty_max,
        ]:
            widget.setValue(-1)
        for widget in [
            self.submitted_from, self.submitted_to, self.updated_from, self.updated_to,
            self.status_changed_from, self.status_changed_to,
        ]:
            widget.clear_value()
        self.sort_field.setCurrentText('缺省')
        self.sort_direction.setCurrentText('升序')
        self.invalidate()

    def source_changed(self):
        self.update_source_note()
        self.invalidate()

    def update_source_note(self):
        if self.source.currentData() == 'sayobot':
            text = (
                'Sayobot 当前只可靠支持标题/艺术家（含罗马化字段）、谱面作者、模式、状态及这些字段的列表排序；'
                '来源、流派、语言、BPM、长度、难度和日期筛选需要 osu! 官方搜索。'
            )
        else:
            text = (
                '标题/艺术家可同时搜索 Unicode 与罗马化字段；模式、BPM、长度和星数必须由同一个难度同时满足。'
                '提交日期对应 submitted_date，更新日期对应 last_updated；状态改变日期使用官网 ranked_date。'
                '对 Pending/WIP/Graveyard 等没有 ranked_date 的状态不会猜测状态改变时间。'
            )
        self.note.setText(text + '\n搜索来源和下载来源相互独立；完整结果指当前搜索源本次返回的全部分页。')

    def update_sort_state(self):
        self.sort_direction.setEnabled(self.sort_field.currentText() != '缺省')

    def invalidate(self):
        self.result_data = None
        self.base_rows = []
        self.last_search_message = ''
        self.table.setRowCount(0)
        self.state.setText('筛选条件已更改，请重新搜索。列表排序本身不会触发重新搜索。')
        self.buttons()

    def buttons(self):
        available = not self.busy and self.result_data is not None
        self.add_all.setEnabled(available and self.result_data.complete and bool(self.result_data.rows))
        self.add_selected.setEnabled(available and bool(self.table.selectionModel().selectedRows()))

    def filters_from_ui(self):
        return Filters(
            title=self.title.text().strip(),
            title_romanized=self.title_romanized.text().strip(),
            artist=self.artist.text().strip(),
            artist_romanized=self.artist_romanized.text().strip(),
            source_text=self.source_text.text().strip(),
            genre=GENRES[self.genre.currentText()],
            language=LANGUAGES[self.language.currentText()],
            bpm_min=self._optional_spin(self.bpm_min),
            bpm_max=self._optional_spin(self.bpm_max),
            length_min=self._optional_spin(self.length_min),
            length_max=self._optional_spin(self.length_max),
            creator=self.creator.text().strip(),
            mode=GAME_MODES[self.mode.currentText()],
            difficulty_min=self._optional_spin(self.difficulty_min),
            difficulty_max=self._optional_spin(self.difficulty_max),
            status=STATUSES[self.status.currentText()],
            submitted_from=self.submitted_from.value_or_none(),
            submitted_to=self.submitted_to.value_or_none(),
            updated_from=self.updated_from.value_or_none(),
            updated_to=self.updated_to.value_or_none(),
            status_changed_from=self.status_changed_from.value_or_none(),
            status_changed_to=self.status_changed_to.value_or_none(),
            exact_artist=self.match.currentIndex() == 0,
        )

    def sort_from_ui(self):
        return SortSpec(
            field=SORT_FIELDS[self.sort_field.currentText()],
            descending=SORT_DIRECTIONS[self.sort_direction.currentText()],
        )

    def start_search(self):
        if self.busy:
            return
        if self.source.currentData() == 'official' and not self.parent().cookie:
            self.state.setText('请先在主窗口设置官网会话，或选择 Sayobot 搜索。')
            return
        self.invalidate()
        self.stop = threading.Event()
        self.busy = True
        for widget in self.filter_inputs:
            widget.setEnabled(False)
        self.search_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.buttons()
        filters = self.filters_from_ui()
        self.pool.submit(self.worker, filters, self.source.currentData(), self.parent().cookie)

    def worker(self, filters, source, cookie):
        try:
            # Search always returns the source's natural order. Sorting is intentionally
            # a separate, local operation on the already loaded result list.
            result = self.searcher.search(filters, source, cookie, self.stop, self.events.progress.emit)
        except Exception:
            result = SearchResult(message='搜索发生内部错误，未确认结果完整性。请重试。')
        self.events.result.emit(result)

    def show_progress(self, message):
        self.state.setText(message)

    def finished_search(self, result):
        self.busy = False
        self.result_data = result
        self.base_rows = list(result.rows)
        self.last_search_message = result.message
        for widget in self.filter_inputs:
            widget.setEnabled(True)
        self.update_sort_state()
        self.search_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.apply_sort()
        self.buttons()
        if self.closing:
            self.reject()

    def apply_sort(self, *_args):
        self.update_sort_state()
        if self.result_data is None:
            return
        selected_ids = {self.table.item(index.row(), 0).text()
                        for index in self.table.selectionModel().selectedRows()}
        spec = self.sort_from_ui()
        self.result_data.rows = sort_rows(self.base_rows, spec)
        self.render_table()
        from PySide6.QtCore import QItemSelectionModel
        self.table.clearSelection()
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() in selected_ids:
                self.table.selectionModel().select(
                    self.table.model().index(row, 0),
                    QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)
        if spec.field == 'default':
            suffix = '当前列表保持搜索源原始顺序。'
        else:
            suffix = f'当前列表已按“{self.sort_field.currentText()}”{self.sort_direction.currentText()}排列。'
        self.state.setText((self.last_search_message + ' ' + suffix).strip())
        self.buttons()

    def render_table(self):
        rows = self.result_data.rows if self.result_data is not None else []
        self.table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            beatmaps = row.get('matched_beatmaps') or row.get('beatmaps') or []
            bpm_values = [b.get('bpm') for b in beatmaps if b.get('bpm') is not None]
            length_values = [b.get('length') for b in beatmaps if b.get('length') is not None]
            modes = sorted({b.get('mode') for b in beatmaps if b.get('mode') in MODE_NAMES}) or row.get('modes', [])
            difficulties = []
            for beatmap in beatmaps:
                name = str(beatmap.get('version') or '').strip()
                stars = beatmap.get('stars')
                if name and stars is not None:
                    difficulties.append(f'{name} {float(stars):.2f}★')
                elif stars is not None:
                    difficulties.append(f'{float(stars):.2f}★')
                elif name:
                    difficulties.append(name)

            values = [
                str(row['sid']),
                str(row.get('title_unicode') or row.get('title') or ''),
                str(row.get('title') or ''),
                str(row.get('artist_unicode') or row.get('artist') or ''),
                str(row.get('artist') or ''),
                str(row.get('source') or '—'),
                str(row.get('genre') or '—'),
                str(row.get('language') or '—'),
                _range_text(bpm_values, lambda value: _number_text(value, 1)),
                _range_text(length_values, _length_text),
                str(row.get('creator') or ''),
                ', '.join(MODE_NAMES[mode] for mode in modes),
                '; '.join(difficulties) if difficulties else '—',
                str(row.get('status') or ''),
                _date_text(row.get('submitted_date')),
                _date_text(row.get('last_updated')),
                _date_text(row.get('status_changed_date')),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(tr(value) if col in (6, 7, 13) else value)
                item.setToolTip(value)
                self.table.setItem(index, col, item)

    def choose(self, all_rows):
        if self.busy or self.result_data is None:
            return
        if all_rows:
            if not self.result_data.complete:
                return
            self.chosen_ids = [row['sid'] for row in self.result_data.rows]
        else:
            self.chosen_ids = [self.result_data.rows[index.row()]['sid'] for index in self.table.selectionModel().selectedRows()]
        if self.chosen_ids:
            self.pool.shutdown(wait=False)
            self.accept()

    def reject(self):
        if self.busy:
            self.closing = True
            self.stop.set()
            self.state.setText('正在结束搜索，请稍候…')
            return
        self.pool.shutdown(wait=False)
        super().reject()

    def closeEvent(self, event):
        if self.busy:
            event.ignore()
            self.reject()
        else:
            self.pool.shutdown(wait=False)
            event.accept()

