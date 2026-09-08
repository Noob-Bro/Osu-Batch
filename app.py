from __future__ import annotations

import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Qt, QTimer, QUrl, QLockFile
from PySide6.QtGui import QDesktopServices, QColor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QPlainTextEdit, QLineEdit, QComboBox, QSpinBox, QCheckBox,
    QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QDialog, QDialogButtonBox, QProgressBar, QFrame, QScrollArea,
)

from engine import Downloader, DownloadError, Options, Stopped, MIRRORS, clean_cookie, parse_input
from store import Store
from search_dialog import SearchDialog
from ui_theme import dark_palette
import i18n
from i18n import (QLabel, QPushButton, QCheckBox, QMainWindow, QDialog,
                  QLineEdit, QPlainTextEdit, QComboBox, QSpinBox, QTableWidget,
                  QMessageBox, QFileDialog, tr)

MODES = {"仅官方（默认）": "official", "官方优先，失败后尝试所选镜像": "fallback", "仅所选镜像": "mirror"}
STATUS_COLORS = {"已完成": "#77dfaf", "失败": "#ff899c", "下载中": "#f5a6d5", "已暂停": "#edc77f"}


def size(n):
    for unit in ("B", "KiB", "MiB", "GiB"):
        if n < 1024 or unit == "GiB":
            return f"{n:.1f} {unit}"
        n /= 1024


class Events(QObject):
    progress = Signal(int, str, object, object, float, str)
    result = Signal(int, str, str, str, str)


class SessionDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("官网登录会话 · 仅本次运行")
        self.resize(660, 410)
        layout = QVBoxLayout(self)
        guide = QLabel(
            "<b>使用你自己的 osu! 官网登录会话</b><br><br>"
            "1. 在浏览器登录 osu.ppy.sh，打开任意谱面集页面。<br>"
            "2. 按 F12 → Network / 网络，点击官网的下载按钮。<br>"
            "3. 找到官网 /beatmapsets/.../download 请求，在 Request Headers / 请求标头中<br>"
            "　复制 Cookie 的值并粘贴到下方。也可在 Application → Cookies 中复制 osu_session。<br><br>"
            "此会话可访问你的账号，请勿分享。工具只在内存中使用，退出即清除。<br>"
            "会话不会写入配置、队列、日志，也不会发送给第三方镜像。<br>"
            "若官网拒绝程序请求，请在浏览器完成验证，或手动选择镜像。"
        )
        guide.setWordWrap(True)
        layout.addWidget(guide)
        open_button = QPushButton("打开 osu! 官网")
        open_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://osu.ppy.sh/home")))
        layout.addWidget(open_button)
        self.cookie = QLineEdit()
        self.cookie.setEchoMode(QLineEdit.EchoMode.Password)
        self.cookie.setPlaceholderText("Cookie 请求标头，或 osu_session 的值")
        layout.addWidget(self.cookie)
        reveal = QCheckBox("显示内容")
        reveal.toggled.connect(lambda v: self.cookie.setEchoMode(QLineEdit.EchoMode.Normal if v else QLineEdit.EchoMode.Password))
        layout.addWidget(reveal)
        self.error = QLabel("")
        self.error.setStyleSheet("color:#ff899c")
        layout.addWidget(self.error)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(tr("本次使用"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("取消"))
        buttons.accepted.connect(self.accept_cookie)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.value = ""

    def accept_cookie(self):
        try:
            self.value = clean_cookie(self.cookie.text())
            if not self.value:
                raise ValueError("请先粘贴会话内容。")
        except ValueError as exc:
            self.error.setText(str(exc))
            return
        self.cookie.clear()
        self.accept()


class Window(QMainWindow):
    def __init__(self, data_dir: Path):
        super().__init__()
        self.setWindowTitle("osu! Batch 1.1 · 谱面批量下载")
        available = self.screen().availableGeometry()
        self.resize(min(1120, available.width() - 40), min(800, available.height() - 80))
        self.store = Store(data_dir)
        self.downloader = Downloader()
        self.pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="download")
        self.events = Events()
        self.events.progress.connect(self.on_progress)
        self.events.result.connect(self.on_result)
        self.active, self.reasons, self.tasks, self.cells, self.speeds = {}, {}, {}, {}, {}
        self.cookie = ""
        self.running, self.closing = False, False
        self.batch_options = None
        settings = self.store.settings()
        i18n.set_language(settings.get('language', 'zh'))

        root = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(root)
        self.setCentralWidget(scroll)
        main = QVBoxLayout(root)
        main.setContentsMargins(28, 22, 28, 20)
        main.setSpacing(14)
        top = QHBoxLayout()
        title = QLabel("osu! <span style='color:#f396c8'>Batch</span>")
        title.setStyleSheet("font-size:30px;font-weight:700")
        top.addWidget(title)
        top.addStretch()
        self.language = QComboBox()
        self.language.addItem('中文', 'zh')
        self.language.addItem('English', 'en')
        self.language.setCurrentIndex(1 if i18n.language == 'en' else 0)
        self.language.setAccessibleName('界面语言 / Interface language')
        self.language.currentIndexChanged.connect(self.change_language)
        top.addWidget(self.language)
        self.session = QPushButton("设置官网会话")
        self.session.clicked.connect(self.set_session)
        top.addWidget(self.session)
        self.clear_session = QPushButton("清除会话")
        self.clear_session.clicked.connect(self.forget_session)
        top.addWidget(self.clear_session)
        main.addLayout(top)
        sub = QLabel("把谱面清单变成下载队列。支持整套难度去重、断点恢复与文件校验。")
        sub.setStyleSheet("color:#a6acc2")
        main.addWidget(sub)

        config = QFrame()
        config.setObjectName("card")
        config_layout = QVBoxLayout(config)
        source_row = QHBoxLayout()
        source_row.addWidget(QLabel("下载策略"))
        self.mode = QComboBox()
        self.mode.addItems(MODES)
        self.mode.setCurrentIndex(list(MODES.values()).index(settings.get("mode", "official")) if settings.get("mode", "official") in MODES.values() else 0)
        source_row.addWidget(self.mode, 2)
        self.mirror = QComboBox()
        self.mirror.addItems(MIRRORS)
        self.mirror.setCurrentText(settings.get("mirror", "Sayobot 小夜"))
        source_row.addWidget(self.mirror, 1)
        source_row.addWidget(QLabel("并发"))
        self.concurrency = QSpinBox()
        self.concurrency.setRange(1, 3)
        self.concurrency.setValue(settings.get("concurrency", 1))
        source_row.addWidget(self.concurrency)
        self.no_video = QCheckBox("不含视频")
        self.no_video.setChecked(settings.get("no_video", False))
        source_row.addWidget(self.no_video)
        config_layout.addLayout(source_row)
        path_row = QHBoxLayout()
        path_row.addWidget(QLabel("保存位置"))
        self.directory = QLineEdit(settings.get("directory", str(Path.home() / "Downloads" / "osu-beatmaps")))
        path_row.addWidget(self.directory, 1)
        self.browse = QPushButton("选择目录")
        self.browse.clicked.connect(self.pick_directory)
        path_row.addWidget(self.browse)
        open_folder = QPushButton("打开目录")
        open_folder.clicked.connect(self.open_directory)
        path_row.addWidget(open_folder)
        config_layout.addLayout(path_row)
        self.source_note = QLabel()
        self.source_note.setWordWrap(True)
        self.source_note.setStyleSheet("color:#a6acc2;font-size:12px")
        config_layout.addWidget(self.source_note)
        main.addWidget(config)
        self.mode.currentIndexChanged.connect(self.source_changed)
        self.mirror.currentIndexChanged.connect(self.source_changed)

        self.input = QPlainTextEdit()
        self.input.setPlaceholderText("粘贴谱面集链接或 ID，每行一个，也可用逗号分隔\nhttps://osu.ppy.sh/beatmapsets/123456#osu/789012\n123456, 234567")
        self.input.setMaximumHeight(105)
        main.addWidget(self.input)
        import_row = QHBoxLayout()
        add = QPushButton("＋ 加入队列")
        add.setObjectName("accent")
        add.clicked.connect(self.add_input)
        import_row.addWidget(add)
        txt = QPushButton("导入 TXT")
        txt.clicked.connect(self.import_text)
        import_row.addWidget(txt)
        filter_button = QPushButton('筛选搜索 / 批量下载')
        filter_button.clicked.connect(self.open_search)
        import_row.addWidget(filter_button)
        import_row.addStretch()
        self.summary = QLabel()
        import_row.addWidget(self.summary)
        main.addLayout(import_row)
        self.table = QTableWidget(0, 6)
        self.table.setMinimumHeight(180)
        self.table.setHorizontalHeaderLabels(["谱面集 ID", "状态", "实际来源", "进度", "速度", "详情"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 110)
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(3, 175)
        self.table.setColumnWidth(4, 95)
        self.table.cellDoubleClicked.connect(self.open_beatmap)
        main.addWidget(self.table, 1)
        self.total_progress = QProgressBar()
        self.total_progress.setFixedHeight(10)
        self.total_progress.setTextVisible(False)
        main.addWidget(self.total_progress)
        actions = QHBoxLayout()
        self.start_button = QPushButton("开始 / 继续")
        self.start_button.setObjectName("accent")
        self.start_button.clicked.connect(self.start)
        actions.addWidget(self.start_button)
        self.pause_button = QPushButton("全部暂停")
        self.pause_button.clicked.connect(self.pause)
        actions.addWidget(self.pause_button)
        cancel = QPushButton("取消选中")
        cancel.clicked.connect(self.cancel_selected)
        actions.addWidget(cancel)
        self.retry_button = QPushButton("重试失败 / 已取消")
        self.retry_button.clicked.connect(self.retry)
        actions.addWidget(self.retry_button)
        remove = QPushButton("移除选中记录")
        remove.clicked.connect(self.remove_selected)
        actions.addWidget(remove)
        actions.addStretch()
        export = QPushButton("导出失败清单")
        export.clicked.connect(self.export_failed)
        actions.addWidget(export)
        main.addLayout(actions)
        self.notice = QLabel("就绪 · 双击任务可打开官网谱面页。下载完成后将 .osz 拖入 osu! 导入。")
        self.notice.setWordWrap(True)
        self.notice.setStyleSheet("color:#a6acc2;font-size:12px")
        main.addWidget(self.notice)
        self.reload()
        self.source_changed()
        self.refresh_controls()

    def change_language(self):
        i18n.set_language(self.language.currentData())
        self.store.save_settings(self.settings())
        for sid, task in self.tasks.items():
            row = self.cells[sid]
            for col, key in ((1, 'status'), (2, 'source'), (5, 'message')):
                self.table.item(row, col).setText(tr(task[key]))
                self.table.item(row, col).setToolTip(tr(task[key]))
        self.stats()

    def reload(self):
        self.tasks = {r["sid"]: r for r in self.store.rows()}
        self.table.setRowCount(len(self.tasks))
        self.cells.clear()
        for row, (sid, task) in enumerate(self.tasks.items()):
            self.cells[sid] = row
            values = [str(sid), task["status"], task["source"], "100%" if task["status"] == "已完成" else "—", "—", task["message"]]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(tr(value) if col in (1, 2, 5) else value))
            self.paint(sid)
        self.stats()

    def update_task(self, sid, **fields):
        self.tasks[sid].update(fields)
        self.store.update(sid, **fields)
        row = self.cells[sid]
        for key, col in (("status", 1), ("source", 2), ("message", 5)):
            self.table.item(row, col).setText(tr(self.tasks[sid][key]))
            self.table.item(row, col).setToolTip(self.tasks[sid][key])
        self.paint(sid)
        self.stats()

    def paint(self, sid):
        self.table.item(self.cells[sid], 1).setForeground(QColor(STATUS_COLORS.get(self.tasks[sid]["status"], "#a6acc2")))

    def stats(self):
        total = len(self.tasks)
        done = sum(t["status"] == "已完成" for t in self.tasks.values())
        failed = sum(t["status"] == "失败" for t in self.tasks.values())
        self.summary.setText(f"{done} / {total} 完成 · {failed} 失败 · {size(sum(self.speeds.values()))}/s")
        self.total_progress.setRange(0, max(1, total))
        self.total_progress.setValue(done)

    def settings(self):
        return dict(language=i18n.language, directory=self.directory.text().strip(), mode=MODES[self.mode.currentText()],
                    mirror=self.mirror.currentText(), no_video=self.no_video.isChecked(),
                    concurrency=self.concurrency.value())

    def source_changed(self):
        use_mirror = MODES[self.mode.currentText()] != "official"
        self.mirror.setEnabled(use_mirror and not self.active)
        supported = not use_mirror or self.mirror.currentText() in ("Nerinyan", "Sayobot 小夜")
        if not supported:
            self.no_video.setChecked(False)
        self.no_video.setEnabled(supported and not self.active)
        text = "官网需要有效登录会话；会话仅用于本次运行。"
        if use_mirror:
            text += " 已选择第三方来源：" + self.mirror.currentText() + "。"
        if MODES[self.mode.currentText()] == "fallback":
            text += " 官方失败可切换镜像；限流时等待，不自动切换。"
        self.source_note.setText(text)

    def set_session(self):
        dialog = SessionDialog(self)
        if dialog.exec():
            self.cookie = dialog.value
            dialog.value = ""
            self.session.setText("官网会话已设置 · 未验证")
            self.downloader.clear_blocks()

    def forget_session(self):
        self.cookie = ""
        self.session.setText("设置官网会话")
        self.downloader.clear_blocks()

    def pick_directory(self):
        value = QFileDialog.getExistingDirectory(self, "选择保存目录", self.directory.text())
        if value:
            self.directory.setText(value)

    def open_directory(self):
        folder = Path(self.directory.text()).expanduser()
        if folder.is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder.resolve())))
        else:
            self.notice.setText("该目录尚不存在，开始下载时会创建。")

    def open_beatmap(self, row, col):
        sid = self.table.item(row, 0).text()
        QDesktopServices.openUrl(QUrl(f"https://osu.ppy.sh/beatmapsets/{sid}"))

    def open_search(self):
        dialog = SearchDialog(self)
        if dialog.exec() and dialog.chosen_ids:
            added = self.store.add(dialog.chosen_ids)
            self.reload()
            self.notice.setText(f'筛选结果新增 {added} 套，跳过 {len(dialog.chosen_ids)-added} 个已有任务。下载使用主窗口所选来源。')
            if self.running:
                self.schedule()
        dialog.deleteLater()

    def add_input(self):
        ids, errors = parse_input(self.input.toPlainText())
        added = self.store.add(ids)
        self.reload()
        self.input.setPlainText("\n".join(errors))
        self.notice.setText(f"新增 {added} 项，跳过 {len(ids) - added} 个已有任务。" +
                            (f" {len(errors)} 项无法识别，已留在输入框；请使用谱面集链接，而非 /beatmaps/ 难度链接。" if errors else ""))
        if self.running:
            self.schedule()

    def import_text(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入清单", "", "文本文件 (*.txt);;所有文件 (*)")
        if path:
            try:
                self.input.setPlainText(Path(path).read_text(encoding="utf-8-sig"))
                self.add_input()
            except (OSError, UnicodeError):
                QMessageBox.warning(self, "无法读取", "请使用 UTF-8 编码的 TXT 文件。")

    def start(self):
        if self.active:
            return
        settings = self.settings()
        if not settings["directory"]:
            QMessageBox.warning(self, "保存位置", "请选择保存目录。")
            return
        if settings["mode"] == "official" and not self.cookie:
            self.set_session()
            if not self.cookie:
                return
        try:
            folder = Path(settings["directory"]).expanduser().resolve()
            folder.mkdir(parents=True, exist_ok=True)
        except OSError:
            QMessageBox.warning(self, "保存位置", "无法创建目录，请检查路径与写入权限。")
            return
        self.store.save_settings(settings)
        self.batch_options = Options(folder, settings["mode"], settings["mirror"], settings["no_video"], self.cookie)
        self.downloader.clear_blocks()
        self.running = True
        self.notice.setText("下载中 · 暂停会保留临时文件，服务器支持时可续传。")
        self.schedule()

    def schedule(self):
        if not self.running or self.closing:
            return
        for sid, task in self.tasks.items():
            if len(self.active) >= self.concurrency.value():
                break
            if sid not in self.active and task["status"] in ("等待", "已暂停"):
                stop = threading.Event()
                self.active[sid] = stop
                self.update_task(sid, status="下载中", message="等待下载源", source="")
                self.pool.submit(self.run_worker, sid, self.batch_options, stop)
        if not self.active:
            self.running = False
            self.batch_options = None
            self.notice.setText("本轮队列已结束。失败任务可查看详情后重试；已完成 .osz 可拖入 osu! 导入。")
        self.refresh_controls()

    def run_worker(self, sid, options, stop):
        try:
            path, source = self.downloader.download(sid, options, stop,
                lambda source, done, total, speed, message: self.events.progress.emit(sid, source, done, total, speed, message))
            self.events.result.emit(sid, "已完成", path, source, "已校验 · " + path)
        except Stopped:
            self.events.result.emit(sid, "stopped", "", "", "临时文件已保留")
        except DownloadError as exc:
            self.events.result.emit(sid, "失败", "", "", str(exc))
        except OSError:
            self.events.result.emit(sid, "失败", "", "", "文件读写失败，请检查空间、文件占用与目录权限。")
        except Exception:
            self.events.result.emit(sid, "失败", "", "", "发生未预期的内部错误，请重试并报告所选模式和操作步骤。")

    def on_progress(self, sid, source, done, total, speed, message):
        if sid not in self.cells:
            return
        row = self.cells[sid]
        self.tasks[sid]["source"] = source
        self.table.item(row, 2).setText(source)
        progress = f"{done / total:.0%} · {size(done)}" if total else (size(done) if done else "—")
        self.table.item(row, 3).setText(progress)
        self.table.item(row, 4).setText(size(speed) + "/s" if speed else "—")
        self.table.item(row, 5).setText(tr(message))
        self.table.item(row, 5).setToolTip(message)
        self.speeds[sid] = speed
        self.stats()

    def on_result(self, sid, status, path, source, message):
        self.active.pop(sid, None)
        self.speeds.pop(sid, None)
        reason = self.reasons.pop(sid, "已暂停")
        if status == "stopped":
            status = reason
        self.update_task(sid, status=status, path=path, source=source or self.tasks[sid]["source"], message=message)
        self.table.item(self.cells[sid], 4).setText("—")
        if status == "已完成":
            self.table.item(self.cells[sid], 3).setText("100%")
        if self.running:
            self.schedule()
        if not self.active:
            self.batch_options = None
        self.refresh_controls()
        if self.closing and not self.active:
            self.close()

    def pause(self):
        self.running = False
        for sid, stop in self.active.items():
            self.reasons[sid] = "已暂停"
            self.update_task(sid, status="正在暂停")
            stop.set()
        for sid, task in self.tasks.items():
            if task["status"] == "等待":
                self.update_task(sid, status="已暂停")
        self.notice.setText("正在暂停；当前网络请求最多约 20 秒结束，临时文件将保留。")
        self.refresh_controls()

    def selected(self):
        return [int(self.table.item(index.row(), 0).text()) for index in self.table.selectionModel().selectedRows()]

    def cancel_selected(self):
        for sid in self.selected():
            if sid in self.active:
                self.reasons[sid] = "已取消"
                self.update_task(sid, status="正在取消")
                self.active[sid].set()
            elif self.tasks[sid]["status"] != "已完成":
                self.update_task(sid, status="已取消", message="已取消，临时文件保留")

    def retry(self):
        for sid, task in self.tasks.items():
            if task["status"] in ("失败", "已取消"):
                self.update_task(sid, status="等待", message="等待重试")
        self.start()

    def remove_selected(self):
        for sid in self.selected():
            if sid not in self.active:
                self.store.remove(sid)
        self.reload()
        self.notice.setText("已移除未运行的选中记录；下载文件和临时文件仍保留在保存目录。")

    def export_failed(self):
        ids = [sid for sid, t in self.tasks.items() if t["status"] == "失败"]
        if not ids:
            self.notice.setText("当前没有失败任务。")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "导出失败清单", "failed-beatmaps.txt", "文本文件 (*.txt)")
        if filename:
            try:
                Path(filename).write_text("\n".join(f"https://osu.ppy.sh/beatmapsets/{sid}" for sid in ids) + "\n", encoding="utf-8")
                self.notice.setText(f"已导出 {len(ids)} 项失败任务。")
            except OSError:
                QMessageBox.warning(self, "导出失败", "无法写入所选文件。")

    def refresh_controls(self):
        idle = not self.active
        for control in (self.mode, self.mirror, self.directory, self.browse, self.concurrency, self.no_video, self.session, self.clear_session):
            control.setEnabled(idle)
        self.source_changed()
        self.start_button.setEnabled(idle and not self.closing)
        self.retry_button.setEnabled(idle and not self.closing)
        self.pause_button.setEnabled(bool(self.active) and self.running)

    def closeEvent(self, event):
        if self.active:
            self.closing = True
            self.pause()
            self.centralWidget().setEnabled(False)
            self.notice.setText("正在保存队列并结束下载，请稍候…")
            event.ignore()
            return
        self.store.save_settings(self.settings())
        self.store.close()
        self.cookie, self.batch_options = "", None
        self.pool.shutdown(wait=False, cancel_futures=True)
        event.accept()


STYLE = """
QWidget { background:#171a25; color:#e6e8f1; font-family:'Microsoft YaHei UI','Segoe UI'; font-size:13px; }
QFrame#card { background:#202432; border:1px solid #33394d; border-radius:12px; padding:10px; }
QFrame#card QLabel, QFrame#card QCheckBox { background:transparent; }
QPushButton { background:#30364a; border:1px solid #434b64; border-radius:7px; padding:8px 13px; }
QPushButton:hover { background:#424a64; }
QPushButton:disabled { color:#72788c; background:#222634; border-color:#303547; }
QPushButton#accent { background:#e789bc; color:#211a26; border:0; font-weight:700; }
QPushButton#accent:hover { background:#f5a6ce; }
QPushButton#accent:disabled { background:#624459; color:#a6909e; }
QLineEdit,QPlainTextEdit,QComboBox,QSpinBox,QDoubleSpinBox { background:#121620; border:1px solid #3b4258; border-radius:6px; padding:7px; selection-background-color:#875c81; }
QLineEdit:disabled,QComboBox:disabled,QSpinBox:disabled,QDoubleSpinBox:disabled { color:#9299af; background:#222634; }
QGroupBox { border:1px solid #33394d; border-radius:6px; margin-top:10px; padding:12px 8px 8px; }
QGroupBox::title { subcontrol-origin:margin; left:10px; padding:0 4px; }
QMenu { background:#252a3a; color:#e6e8f1; border:1px solid #434b64; }
QMenu::item:selected { background:#53516e; }
QScrollArea { border:0; }
QLineEdit:focus,QPlainTextEdit:focus { border-color:#e789bc; }
QComboBox QAbstractItemView { selection-background-color:#53516e; }
QTableWidget { background:#1c202c; border:1px solid #33394d; border-radius:8px; gridline-color:#2d3345; selection-background-color:#45405d; }
QHeaderView::section { background:#252a3a; color:#aeb5cb; border:0; border-bottom:1px solid #3b4258; padding:10px; }
QProgressBar { background:#2b3040; border:0; border-radius:5px; }
QProgressBar::chunk { background:#e789bc; border-radius:5px; }
QToolTip { background:#353b50; color:white; border:1px solid #66708c; }
"""


STYLE += """
QComboBox { padding-right:25px; }
QComboBox::drop-down { width:22px; border:0; }
QComboBox::down-arrow { image:url('@ASSETS@/down.svg'); width:10px; height:7px; }
QSpinBox,QDoubleSpinBox { padding-right:23px; }
QSpinBox::up-button,QDoubleSpinBox::up-button { subcontrol-origin:border; subcontrol-position:top right; width:21px; background:#30364a; border:1px solid #434b64; }
QSpinBox::down-button,QDoubleSpinBox::down-button { subcontrol-origin:border; subcontrol-position:bottom right; width:21px; background:#30364a; border:1px solid #434b64; }
QSpinBox::up-arrow,QDoubleSpinBox::up-arrow { image:url('@ASSETS@/up.svg'); width:10px; height:7px; }
QSpinBox::down-arrow,QDoubleSpinBox::down-arrow { image:url('@ASSETS@/down.svg'); width:10px; height:7px; }
QCheckBox::indicator { width:16px; height:16px; background:#121620; border:1px solid #77809b; border-radius:3px; }
QCheckBox::indicator:checked { background:#e789bc; image:url('@ASSETS@/check.svg'); }
QCheckBox::indicator:disabled { border-color:#434b64; background:#30364a; }
""".replace('@ASSETS@', Path(__file__).with_name('assets').as_posix())


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(dark_palette())
    app.setStyleSheet(STYLE)
    app.setApplicationName("OsuBatch")
    app.setOrganizationName("OsuBatch")
    data_dir = Path(os.environ.get("OSU_BATCH_DATA_DIR", str(Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "OsuBatch")))
    data_dir.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(data_dir / "app.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        QMessageBox.information(None, "osu! Batch", "工具已在运行，请使用已打开的窗口。")
        return 1
    window = Window(data_dir)
    window.show()
    if "--smoke-test" in sys.argv:
        QTimer.singleShot(1000, window.close)
    result = app.exec()
    lock.unlock()
    return result


if __name__ == "__main__":
    sys.exit(main())

