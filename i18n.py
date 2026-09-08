"""Presentation-only translations; combo values and persisted task states stay stable."""
import weakref
from PySide6 import QtWidgets as W
from PySide6.QtCore import QLocale, QSignalBlocker
from shiboken6 import isValid

language = 'zh'
_widgets = weakref.WeakSet()
EN = dict(line.split('|', 1) for line in '''
选择日期|Choose date
清空|Clear
取消|Cancel
确定|OK
日历|Calendar
上个月|Previous month
下个月|Next month
YYYY-MM-DD（缺省）|YYYY-MM-DD (optional)
可直接输入 YYYY-MM-DD；留空表示不筛选。|Enter YYYY-MM-DD or leave blank for any date.
打开日历选择日期|Choose a date from the calendar
筛选谱面 · 搜索并加入队列|Filter beatmaps · Search and queue
搜索来源|Search source
osu! 官方（需官网会话）|osu! official (session required)
Sayobot 小夜（无需登录）|Sayobot (no login required)
清空筛选|Reset filters
填入 Laur / Ranked / std 示例|Laur / Ranked / std example
基础信息|Basic information
标题|Title
标题（罗马化）|Title (romanized)
艺术家|Artist
艺术家（罗马化）|Artist (romanized)
来源|Source
谱面作者|Mapper
艺术家精确匹配|Exact artist match
艺术家包含匹配（可含合作曲）|Artist contains (includes collaborations)
缺省；匹配原文/Unicode 或罗马化标题|Optional; original / Unicode or romanized title
缺省；仅匹配罗马化标题|Optional; romanized title only
缺省；匹配原文/Unicode 或罗马化艺术家|Optional; original / Unicode or romanized artist
缺省；仅匹配罗马化艺术家|Optional; romanized artist only
缺省；歌曲 / 作品来源|Optional; song / work source
缺省；谱面作者|Optional; mapper
分类|Categories
流派|Genre
语言|Language
谱面模式|Game mode
谱面状态|Beatmap status
数值范围|Numeric ranges
长度（秒）|Length (seconds)
谱面难度（★）|Difficulty (stars)
日期（可直接输入，也可点击日历选择）|Dates (type a date or use the calendar)
提交日期|Submitted
更新日期|Updated
状态改变日期|Status changed
当前列表排序|Sort loaded results
（排序只重排已加载列表，不重新搜索、不清空结果）|(Sorting keeps loaded results; no new search)
搜索全部分页|Search all pages
取消搜索|Cancel search
所有筛选条件默认为缺省；设置条件后搜索。|All filters are optional. Set filters, then search.
谱面集 ID|Beatmapset ID
长度|Length
模式|Mode
谱面难度|Difficulty
状态|Status
全部加入下载队列|Queue all results
加入选中项|Queue selected
关闭|Close
缺省|Any / unset
未指定|Unspecified
电子游戏|Video game
动漫|Anime
摇滚|Rock
流行|Pop
其他|Other
新奇 / Novelty|Novelty
嘻哈|Hip hop
电子|Electronic
金属|Metal
古典|Classical
民谣|Folk
爵士|Jazz
英语|English
日语|Japanese
中文|Chinese
纯音乐|Instrumental
韩语|Korean
法语|French
德语|German
瑞典语|Swedish
西班牙语|Spanish
意大利语|Italian
俄语|Russian
波兰语|Polish
其他语言|Other languages
升序|Ascending
降序|Descending
筛选条件已更改，请重新搜索。列表排序本身不会触发重新搜索。|Filters changed. Search again. Changing sort order does not require a new search.
请先在主窗口设置官网会话，或选择 Sayobot 搜索。|Set an official session in the main window, or select Sayobot.
搜索发生内部错误，未确认结果完整性。请重试。|Search failed internally. Results may be incomplete; please retry.
正在结束搜索，请稍候…|Stopping search, please wait…
当前列表保持搜索源原始顺序。|Results are in the source's original order.
osu! Batch 1.1 · 谱面批量下载|osu! Batch 1.1 · Beatmap downloader
官网登录会话 · 仅本次运行|Official session · This run only
打开 osu! 官网|Open osu! website
Cookie 请求标头，或 osu_session 的值|Cookie header or osu_session value
显示内容|Show content
本次使用|Use for this session
请先粘贴会话内容。|Paste your session first.
设置官网会话|Set official session
清除会话|Clear session
把谱面清单变成下载队列。支持整套难度去重、断点恢复与文件校验。|Queue beatmapsets with deduplication, resumable downloads and file validation.
下载策略|Download policy
仅官方（默认）|Official only (default)
官方优先，失败后尝试所选镜像|Official first, then selected mirror
仅所选镜像|Selected mirror only
Sayobot 小夜|Sayobot
并发|Concurrency
不含视频|No video
保存位置|Save location
选择目录|Browse
打开目录|Open folder
＋ 加入队列|+ Add to queue
导入 TXT|Import TXT
筛选搜索 / 批量下载|Filter / batch download
实际来源|Actual source
进度|Progress
速度|Speed
详情|Details
开始 / 继续|Start / resume
全部暂停|Pause all
取消选中|Cancel selected
重试失败 / 已取消|Retry failed / canceled
移除选中记录|Remove selected
导出失败清单|Export failures
就绪 · 双击任务可打开官网谱面页。下载完成后将 .osz 拖入 osu! 导入。|Ready. Double-click a task to open its osu! page. Drag downloaded .osz files into osu! to import.
官网会话已设置 · 未验证|Official session set · Unverified
该目录尚不存在，开始下载时会创建。|This folder will be created when downloading starts.
无法读取|Cannot read file
请使用 UTF-8 编码的 TXT 文件。|Use a UTF-8 encoded TXT file.
请选择保存目录。|Choose a save folder.
无法创建目录，请检查路径与写入权限。|Cannot create folder. Check the path and write permissions.
下载中 · 暂停会保留临时文件，服务器支持时可续传。|Downloading. Pausing keeps partial files for resuming where supported.
本轮队列已结束。失败任务可查看详情后重试；已完成 .osz 可拖入 osu! 导入。|Queue finished. Review failed tasks before retrying; drag completed .osz files into osu! to import.
正在暂停；当前网络请求最多约 20 秒结束，临时文件将保留。|Pausing; current requests may take about 20 seconds to stop. Partial files are kept.
已移除未运行的选中记录；下载文件和临时文件仍保留在保存目录。|Removed selected inactive records. Downloads and partial files are kept.
当前没有失败任务。|There are no failed tasks.
导出失败|Export failed
无法写入所选文件。|Cannot write to the selected file.
正在保存队列并结束下载，请稍候…|Saving queue and stopping downloads, please wait…
工具已在运行，请使用已打开的窗口。|The application is already running. Use its existing window.
已完成|Completed
失败|Failed
下载中|Downloading
已暂停|Paused
已取消|Canceled
等待中|Waiting
官网需要有效登录会话；会话仅用于本次运行。|Official downloads require a valid session, kept only for this run.
 已选择第三方来源：| Selected third-party source: 
 官方失败可切换镜像；限流时等待，不自动切换。| A failed official request may fall back to the mirror. Rate limits are respected without switching sources.
搜索来源和下载来源相互独立；完整结果指当前搜索源本次返回的全部分页。|Search and download sources are independent. Complete results mean all pages returned by this source in this search.
Sayobot 当前只可靠支持标题/艺术家（含罗马化字段）、谱面作者、模式、状态及这些字段的列表排序；来源、流派、语言、BPM、长度、难度和日期筛选需要 osu! 官方搜索。|Sayobot supports title/artist (including romanized fields), mapper, mode, status and sorting by these fields. Source, genre, language, BPM, length, difficulty and date filters require official search.
标题/艺术家可同时搜索 Unicode 与罗马化字段；模式、BPM、长度和星数必须由同一个难度同时满足。提交日期对应 submitted_date，更新日期对应 last_updated；状态改变日期使用官网 ranked_date。对 Pending/WIP/Graveyard 等没有 ranked_date 的状态不会猜测状态改变时间。|Title/artist can match Unicode and romanized fields. Mode, BPM, length and stars must match the same difficulty. Dates use submitted_date, last_updated and ranked_date. Status-change dates are unavailable when ranked_date is missing.
粘贴谱面集链接或 ID，每行一个，也可用逗号分隔|Paste beatmapset links or IDs, one per line or separated by commas
完成|completed
失败|failed
就绪|Ready
官方|Official
等待下载|Waiting
正在连接|Connecting
校验中|Validating
搜索完成|Search complete
结果不完整|Incomplete results
。|.
（| (
）|)
，|, 
：|: 
；|; 
'''.strip().splitlines())


EN.update(dict(line.split('|', 1) for line in '''
导入清单|Import list
 项无法识别，已留在输入框；请使用谱面集链接，而非 /beatmaps/ 难度链接。| unrecognized entries remain. Use beatmapset links, not /beatmaps/ difficulty links.
等待|Waiting
正在暂停|Pausing
正在取消|Canceling
上次运行未完成，可继续下载|Previous run unfinished; ready to resume
选择保存目录|Choose download folder
失败清单|Failed tasks
文本文件 (*.txt)|Text files (*.txt)
文本文件 (*.txt);;所有文件 (*)|Text files (*.txt);;All files (*)
导入谱面清单|Import beatmap list
正在准备下载|Preparing download
等待下载源|Waiting for download source
等待重试|Waiting to retry
已取消，临时文件保留|Canceled; partial files kept
临时文件已保留|Partial files kept
已校验，跳过重复文件|Validated; skipping existing file
校验压缩包与谱面 ID|Validating archive and beatmap ID
已校验 · |Validated · 
网络连接失败、超时或响应内容损坏。|Connection failed, timed out or returned corrupt data.
文件读写失败，请检查空间、文件占用与目录权限。|File I/O failed. Check free space, file locks and folder permissions.
发生未预期的内部错误；请重试并反馈所选模式和操作步骤。|Unexpected internal error. Retry and report the selected mode and steps.
请先设置官网登录会话。|Set an official login session first.
Cookie 必须为单行内容。|Cookie must be a single line.
Cookie 格式无效。|Invalid cookie format.
未找到 osu_session。请粘贴完整请求 Cookie，或单独粘贴 osu_session 值。|osu_session not found. Paste the full Cookie header or the osu_session value.
文件名无效、内容为空或超出安全大小限制。|Invalid filename, empty content or file size limit exceeded.
谱面压缩包损坏或格式不受支持。|Beatmap archive is corrupt or unsupported.
谱面包中没有有效 .osu 文件。|No valid .osu file in the beatmap archive.
下载内容的谱面集 ID 不匹配。|Downloaded beatmapset ID does not match.
下载内容超出预期大小。|Download exceeds expected size.
谱面包超过 2 GiB 限制。|Beatmap archive exceeds the 2 GiB limit.
同名文件已存在但校验失败；请移走该文件后重试，未覆盖原文件。|An existing file failed validation. Move it aside and retry; it was not overwritten.
目标文件在下载期间已被其他程序创建；未覆盖，请重试。|Another program created the destination file during download. It was not overwritten; retry.
文件未完整下载。|Download is incomplete.
此镜像尚未提供经过验证的无视频模式。|This mirror has no verified no-video mode.
此镜像不支持当前模式。|This mirror does not support this mode.
下载源繁忙，|Download source is busy; 
下载源受到限流，|Download source rate limit; 
下载源返回 HTTP |Download source returned HTTP 
下载重定向次数过多，请检查登录状态。|Too many download redirects. Check your login session.
下载源返回了网页或错误信息，请检查登录或网站验证。|Download source returned a web page or error. Check login or website verification.
下载源返回了不安全的跳转地址。|Download source returned an unsafe redirect URL.
下载源的跳转地址为空。|Download source returned an empty redirect URL.
下载源返回不支持的压缩传输格式。|Download source returned unsupported content encoding.
服务器无法恢复进度，重新下载。|Server cannot resume this download; restarting.
续传响应不一致，重新完整下载。|Inconsistent resume response; restarting download.
续传总长度不一致，重新完整下载。|Resume length changed; restarting download.
登录失效或暂时被拒绝；请重新登录官网，也可能需要在浏览器完成验证。|Session expired or access denied. Log in again; browser verification may be required.
网站拒绝访问，请稍后重试或更换下载源。|Access denied. Retry later or choose another download source.
谱面不存在、已被移除或该来源不提供下载。|Beatmap missing, removed or unavailable from this source.
排序字段无效。|Invalid sort field.
排序方向无效。|Invalid sort direction.
筛选值无效。|Invalid filter value.
筛选条件无效。|Invalid filter criteria.
流派或语言筛选无效。|Invalid genre or language filter.
最小值不能大于最大值。|Minimum cannot exceed maximum.
的起始日期不能晚于结束日期。|: start date cannot be after end date.
格式无效，请使用 YYYY-MM-DD。|: invalid date; use YYYY-MM-DD.
最长 200 字符且不能包含换行、双引号或斜杠。|: max 200 characters; no newlines, double quotes or slashes.
搜索源无效。|Invalid search source.
搜索网络超时或连接失败。|Search connection failed or timed out.
搜索响应格式异常。|Invalid search response format.
搜索源未返回 JSON，可能需要在浏览器完成验证。|Search source did not return JSON. Browser verification may be required.
搜索源返回 HTTP |Search source returned HTTP 
搜索源受到限流，|Search source rate limit; 
搜索被暂时拒绝或需要登录；请重新设置官网会话，或手动选择 Sayobot 搜索。|Search denied or login required. Reset the official session or select Sayobot.
官网筛选需要有效登录会话；请先设置官网会话，或选择 Sayobot（无需登录）。|Official filters require a valid session. Set a session or select Sayobot (no login).
官网未应用搜索条件，请检查登录会话与筛选条件。|Official search did not apply filters. Check your session and filters.
官网忽略了筛选或排序条件（常见于会话失效）；已停止，未下载默认列表。|Official search ignored filters or sorting (often an expired session). Stopped without downloading the default list.
官网分页游标格式异常。|Invalid official pagination cursor.
官网缺少分页信息，无法确认是否已读完。|Official pagination information is missing; completeness is unknown.
官网缺少结果总数，无法确认完整性。|Official result count is missing; completeness is unknown.
分页已结束但读取量小于官网结果数；可能存在搜索上限或数据变化，请缩小范围。|Pagination ended before the reported total. A result limit or data change is possible; narrow your filters.
搜索源重复返回同一页，已停止；当前结果不完整。|Search source repeated a page. Stopped with incomplete results.
搜索结果列表格式异常。|Invalid search result list.
搜索结果记录格式异常。|Invalid search result record.
搜索结果缺少可靠的谱面 ID、状态或模式信息，已停止以避免错误筛选。|Results lack reliable IDs, status or mode. Stopped to avoid incorrect filtering.
搜索已取消，当前仅为部分结果。|Search canceled; results are partial.
Sayobot 搜索返回错误。|Sayobot search returned an error.
Sayobot 缺少有效分页标记，无法确认完整性。|Sayobot pagination marker is missing or invalid; completeness is unknown.
Sayobot 当前元数据不足以可靠按该字段排序，请使用 osu! 官方搜索或选择“缺省”。|Sayobot metadata cannot reliably sort this field. Use official search or select Any / unset.
Sayobot 当前返回的元数据不足以可靠执行：|Sayobot metadata cannot reliably apply: 
。请改用 osu! 官方搜索。|. Use official search instead.
读取到|Read
正在读取第 |Reading page 
 页；核对 |; checking 
 页；已匹配 |; matched 
 套，匹配 | sets; matched 
 套，跳过 | sets; skipped 
 项，跳过 | tasks; skipped 
 项失败任务。| failed tasks.
 个已有任务。下载使用主窗口所选来源。| existing tasks. Downloads use the source selected in the main window.
 个已有任务。| existing tasks.
 套。| sets.
搜索完成：读取 |Search complete: read 
筛选结果新增 |Added from search: 
新增 |Added 
已导出 |Exported 
当前列表已按“|Results sorted by: 
”| 
排列。|.
 当前结果未确认完整。| Results are not confirmed complete.
 等待 | Wait 
 秒后重试。| seconds before retrying.
 已阻止重复导入。| Duplicate import prevented.
 处无法识别的输入留在输入框；请使用谱面集链接，而非 /beatmaps/ 难度链接。| unrecognized entries remain. Use beatmapset links, not /beatmaps/ difficulty links.
。|.
'''.strip().splitlines()))


def tr(text):
    text = str(text)
    if language == 'zh':
        return text
    if text.startswith('<b>使用你自己的 osu! 官网登录会话</b>'):
        return ('<b>Use your own osu! website session</b><br><br>'
                '1. Log in at osu.ppy.sh and open a beatmapset page.<br>'
                '2. Open F12 → Network and click the website download button.<br>'
                '3. Select the /beatmapsets/.../download request and copy its Cookie '
                'request header below. Alternatively copy osu_session from Application → Cookies.<br><br>'
                'This session grants access to your account. Do not share it. '
                'It stays in memory and is cleared on exit.<br>'
                'It is never saved in settings, queue or logs, or sent to mirrors.<br>'
                'If access is denied, complete browser verification or select a mirror.')
    if text in EN:
        return EN[text]
    for source in sorted(EN, key=len, reverse=True):
        if len(source) > 1:
            text = text.replace(source, EN[source])
    return text


def set_language(value):
    global language
    language = value if value in ('zh', 'en') else 'zh'
    locale = QLocale('zh_CN' if language == 'zh' else 'en_US')
    QLocale.setDefault(locale)
    for widget in list(_widgets):
        if isValid(widget):
            widget.retranslate()
    for widget in W.QApplication.allWidgets():
        if isinstance(widget, W.QCalendarWidget):
            widget.setLocale(locale)


class Translated:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._texts = {}
        _widgets.add(self)
        if args and isinstance(args[0], str) and hasattr(super(), 'setText') and not isinstance(self, W.QLineEdit):
            self.setText(args[0])
        if isinstance(self, W.QGroupBox) and args and isinstance(args[0], str):
            self.setTitle(args[0])

    def retranslate(self):
        for setter, text in self._texts.items():
            getattr(super(), setter)(tr(text))


def _setter(name):
    def set_value(self, text):
        self._texts[name] = str(text)
        getattr(super(Translated, self), name)(tr(text))
    return set_value


for _name in ('setText', 'setTitle', 'setWindowTitle', 'setPlaceholderText', 'setToolTip', 'setSpecialValueText'):
    setattr(Translated, _name, _setter(_name))


QLabel = type('QLabel', (Translated, W.QLabel), {})
QPushButton = type('QPushButton', (Translated, W.QPushButton), {})
QCheckBox = type('QCheckBox', (Translated, W.QCheckBox), {})
QGroupBox = type('QGroupBox', (Translated, W.QGroupBox), {})
QDialog = type('QDialog', (Translated, W.QDialog), {})
QMainWindow = type('QMainWindow', (Translated, W.QMainWindow), {})
QSpinBox = type('QSpinBox', (Translated, W.QSpinBox), {})
QDoubleSpinBox = type('QDoubleSpinBox', (Translated, W.QDoubleSpinBox), {})
QPlainTextEdit = type('QPlainTextEdit', (Translated, W.QPlainTextEdit), {})


class QLineEdit(Translated, W.QLineEdit):
    # Never translate user-entered paths, cookies or search terms.
    def setText(self, text):
        W.QLineEdit.setText(self, text)


class QComboBox(Translated, W.QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._source_items = []

    def addItem(self, text, userData=None):
        self._source_items.append(text)
        super().addItem(tr(text), userData)

    def addItems(self, texts):
        for text in texts:
            self.addItem(text)

    def currentText(self):
        index = self.currentIndex()
        return self._source_items[index] if index >= 0 else ''

    def setCurrentText(self, text):
        if text in self._source_items:
            self.setCurrentIndex(self._source_items.index(text))

    def retranslate(self):
        super().retranslate()
        blocker = QSignalBlocker(self)
        for index, text in enumerate(self._source_items):
            self.setItemText(index, tr(text))


class QTableWidget(Translated, W.QTableWidget):
    def setHorizontalHeaderLabels(self, labels):
        self._headers = list(labels)
        super().setHorizontalHeaderLabels([tr(t) for t in labels])

    def retranslate(self):
        super().retranslate()
        if hasattr(self, '_headers'):
            super().setHorizontalHeaderLabels([tr(t) for t in self._headers])


class QMessageBox(W.QMessageBox):
    @staticmethod
    def warning(parent, title, text):
        return W.QMessageBox.warning(parent, tr(title), tr(text))

    @staticmethod
    def information(parent, title, text):
        return W.QMessageBox.information(parent, tr(title), tr(text))


class QFileDialog(W.QFileDialog):
    @staticmethod
    def getExistingDirectory(parent, caption, directory):
        return W.QFileDialog.getExistingDirectory(parent, tr(caption), directory)

    @staticmethod
    def getOpenFileName(parent, caption, directory, filters):
        return W.QFileDialog.getOpenFileName(parent, tr(caption), directory, tr(filters))

    @staticmethod
    def getSaveFileName(parent, caption, directory, filters):
        return W.QFileDialog.getSaveFileName(parent, tr(caption), directory, tr(filters))

