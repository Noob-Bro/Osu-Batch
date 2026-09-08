# osu! Batch — Windows 谱面批量下载工具

> **安全提示 / Security notice**
>
> Windows 可执行文件由 PyInstaller 打包且未进行代码签名，部分防护软件可能因此拦截或报错。请勿为运行本程序关闭防护功能；请确认下载来源，必要时先扫描文件。若仍有疑虑，请审阅源码并自行构建。
>
> The Windows executable is packaged with PyInstaller and is not code-signed. Some security products may therefore block or flag it. Do not disable security protection to run this program. Verify the download source, scan the files if needed, or review and build the source code yourself.

**本仓库为 UI 修复与中英文切换版本（2026-09-09）**，保留高级筛选功能。源码位于仓库根目录；Windows x64 免安装版请从 Releases 下载，完整解压后运行 `OsuBatch.exe`。

**源码启动：** 克隆或下载源码到可写目录，双击 `start.cmd`。需要 Python 3.12+；依赖不足时首次运行会在工具目录创建 `.venv` 并从 PyPI 安装依赖。后续运行无需再次安装。升级前关闭旧版程序，原队列与设置会保留。

**Language / 界面语言：** 主窗口右上角选择中文或 English，立即生效并保存偏好。用户输入、谱面标题和艺术家保持原文，筛选值与下载状态不随显示语言改变。

本次修复：
- 日历星期表头、周末文字和翻月按钮适配深色主题，移除多余周数栏，加大日期选择区。
- 补齐小数输入框、上下箭头、下拉按钮和复选框的主题样式。
- 高级筛选分行显示，可滚动访问；窗口初始尺寸参考屏幕可用区域。
- 搜索结果排序按谱面集 ID 保留选中项，避免排序后误选另一套谱面。
- 切换语言不重载下载队列，保留当前进度、选中项和输入内容。

**Windows Defender：** 构建配置已经使用目录模式并关闭 UPX，未发现可确定消除告警的打包配置修复。本次没有重新生成或认证 EXE，也没有修改 Defender 设置。源码运行不构成安全保证；此前 EXE 的检测结论仍需微软复核。可使用 [Microsoft 文件提交入口](https://www.microsoft.com/en-us/wdsi/filesubmission) 提交疑似误报；本工具不会自动上传文件。

## 新增：按条件批量下载

点击主窗口「筛选搜索 / 批量下载」，例如：

1. 搜索来源：`osu! 官方`（先在主窗口设置官网会话），或手动选择 `Sayobot 小夜`（无需登录）。
2. 艺术家填 `Laur`，选择「精确匹配」。
3. 状态选择 `Ranked`，模式选择 `osu! standard (std)`。
4. 点击「搜索全部分页」，查看艺术家、曲名、谱师、状态和包含模式。
5. 搜索完成后点击「全部加入下载队列」，返回主窗口点击「开始 / 继续」。主窗口已在下载时，新增任务会继续排队执行。

搜索来源与下载来源相互独立：可以用 Sayobot 找谱，再用主窗口的官方来源下载。不会自动更换搜索源。新版沿用原队列数据库，升级前关闭旧版程序。

### 筛选语义

- 精确艺术家匹配：忽略大小写、首尾空格和全半角差别，对艺术家及 Unicode 艺术家字段核对；`Laur feat. Sennzai`、`Laurinha Costa` 不等于 `Laur`。
- 包含匹配：可包含合作曲，也可能包含 `Laura` 等相似名字，需查看预览；不推断艺名别名。艺术家留空表示不限。
- Ranked 严格指 `ranked`，不会混入旧 `approved`；Approved 可单独选择。
- 模式筛选指该谱面集至少包含一个对应的原生难度。混合模式谱面集可入选；下载仍为完整 `.osz`，不删除其他难度。
- 官网游标分页和 Sayobot 的 `endid` 分页分别处理；自动去重，并对返回的艺术家、状态及模式再次核对。
- 官网未登录或会话失效时可能忽略条件返回默认列表，工具会检测并拒绝使用该列表。
- 取消、网络错误、分页重复或官网结果数量不足时不会标为完整，「全部加入」禁用；可以明确选中当前部分结果后加入。
- “全部”指所选搜索源本次提供的全部分页。镜像可能有同步延迟，官网也可能受账号屏蔽列表、下架、搜索上限和搜索期间数据变化影响，不保证跨来源、跨时间的绝对全集。新谱面不会在搜索结束后自动追加。
- 官网搜索包含 NSFW 标记谱面，避免隐式漏项；只展示文本元数据，不显示封面。

2026-09-07 本机 Sayobot 实测：`Laur` 精确匹配 + Ranked + std 得到 **15 套**；这是当时镜像的结果，不是对官网总数的承诺。

## 快速开始

解压 Windows 免安装版，运行 `OsuBatch.exe`。面向 Windows 10 22H2 / Windows 11 64 位，本次在 Windows 11 验证。

1. 选择保存位置。
2. 默认使用「仅官方」。点击「设置官网会话」，按窗口内步骤提供你自己的官网 Cookie；会话只在本次运行使用。
3. 粘贴谱面集链接或 ID，或导入 UTF-8 TXT，然后点击「加入队列」。
4. 点击「开始 / 继续」。需要镜像时，在下载策略中选择自动回退或仅镜像。
5. 完成后把 `.osz` 文件拖入 osu!。工具不直接修改 stable 的 Songs 或 lazer 的内部文件存储。

## 下载来源由用户决定

| 策略 | 行为 |
|---|---|
| 仅官方（默认） | 仅从官网请求下载，需要有效网页登录会话 |
| 官方优先，失败后尝试所选镜像 | 官方连接失败、登录失效、不可用等情况下，可尝试指定镜像；没有会话时直接尝试镜像 |
| 仅所选镜像 | 使用 Sayobot 小夜、Nerinyan 或 Mino (catboy.best)，不发送官网会话 |

HTTP 429 限流会遵守 Retry-After 等待，同一来源的并发任务共享冷却时间。连续三次失败后标记失败，不因限流自动切换来源。默认并发 1，最多 3；新下载请求间隔至少约 1.5 秒。

「不含视频」支持官方、Sayobot 和 Nerinyan；选择 Mino 时禁用此选项。服务器实际是否提供对应版本由来源决定。

## 官方登录方式与限制

官方公开文档说明：标记 `lazer` 的接口不向普通 Authorization Code / Client Credentials OAuth 应用开放。因此本工具使用官网已有的网页登录下载路由，不要求创建 OAuth 应用，也不接收账号密码。

设置会话的方法：

1. 在你自己的浏览器中登录 [osu! 官网](https://osu.ppy.sh/home)。
2. 打开任意谱面集页面，按 F12，进入 **Network / 网络**，再点击官网「下载」。
3. 找到 **osu.ppy.sh 域名下** `/beatmapsets/数字/download` 的请求。
4. 在 **Request Headers / 请求标头** 中复制 `Cookie` 的值，粘贴到工具的会话窗口。
5. 也可以在 **Application / 应用程序 → Cookies → https://osu.ppy.sh** 中复制 `osu_session` 的值。

Cookie 相当于当前登录会话，不要发给别人，也不要粘贴进聊天。工具仅保存在进程内存中，退出后需要重新设置；配置、队列和错误消息不保存 Cookie。Cookie 只发送到 `https://osu.ppy.sh:443`，跳转到文件服务器时不携带。

官网可能要求浏览器验证，或拒绝非浏览器网络客户端。复制会话不能保证绕过这类限制，本工具也不会自动处理验证。出现 401 / 403 时，重新在浏览器登录并完成验证；如果仍不可用，可由你选择镜像。按钮显示「会话已设置 · 未验证」表示只接受了输入，实际下载成功前不宣称已验证登录。

## 输入格式

```text
https://osu.ppy.sh/beatmapsets/123456#osu/789012
https://osu.ppy.sh/s/234567
345678
456789, 567890
```

- 数字始终按 **Beatmapset ID（谱面集 ID）** 解释。
- 下载整套谱面集；同一套下不同难度链接会去重。
- 首版不解析只含单个难度 ID 的 `/beatmaps/123`、`/b/123` 链接。请打开官网复制包含 `beatmapsets` 的完整链接。
- 同一队列中已存在的 ID 不重复添加。要重新下载已完成任务、改目录或切换含视频版本，请先移除该任务记录，再加入队列。
- 去重检查下载目录中工具生成的文件名，不扫描游戏曲库，也不检查服务器是否更新了谱面。

## 暂停、续传和校验

- 暂停与取消都会保留 `.part` 临时文件。取消的任务不自动继续，可用「重试失败 / 已取消」恢复。
- 关闭窗口时先停止下载并保存队列。正在等待网络响应时通常最多约 20 秒；多次跳转等情况下可能更久。
- 仅在来源、谱面集、视频选项一致，且存在可用 ETag 或 Last-Modified 时发送续传请求。
- 服务器忽略 Range、返回不一致 Content-Range 或无法续传时会重新下载，避免拼接不同版本。
- 下载后读取压缩包全部条目验证 CRC，检查 `.osu` 格式；存在有效 BeatmapSetID 字段时核对 ID。旧谱面可能缺少该字段，此时不能据此确认 ID。
- 文件通过校验后才改名为 `.osz`。单包上限 2 GiB，解压后总内容上限 4 GiB；不在磁盘解压压缩包。
- 同名已有文件会先校验；有效则跳过，无效则报错，保留用户原文件。
- 普通文件命名为 `谱面集ID.osz`，无视频版本为 `谱面集ID-novideo.osz`。
- 「移除选中记录」仅移除记录，不删除 `.osz` 或临时文件。无需继续的 `.part` 及其 `.json` 可以在关闭程序后手动删除。

队列与设置默认存放在 `%LOCALAPPDATA%\OsuBatch\queue.sqlite3`。开发测试可用 `OSU_BATCH_DATA_DIR` 指定其他目录。程序使用单实例锁防止重复运行写入同一队列。

## 源码运行

Python 3.12+，在此源码目录中执行：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

开发验证与打包：

```powershell
.\.venv\Scripts\python.exe -m pip install pytest==9.1.1 pyinstaller==6.22.2
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe build.py
```

便携版输出到 `dist/OsuBatch/`，请分发整个文件夹。使用 onedir 动态库布局，可替换依赖库。第三方组件保留各自许可。

## 文件结构

- `app.py`：中文桌面界面、线程任务调度。
- `engine.py`：下载源适配、重试、续传、内容校验。
- `store.py`：队列与设置存储。
- `search.py`：官网与 Sayobot 分页搜索、本地筛选及完整性判断。
- `search_dialog.py`：筛选窗口、预览与加入队列。
- `tests/`：下载异常、凭据隔离、持久化及界面流程测试。
- `build.py`：Windows 便携版构建入口。
- `OsuBatch.spec`：依赖收集规则，排除构建环境中可能冲突的 ICU 动态库。

## 接口依据

核对日期：2026-09-06。来源状态会变化，源码依据不等于当前网络上的成功下载保证。

- [官方认证与 API 文档](https://osu.ppy.sh/docs/)：lazer 接口授权限制。
- [官方 BeatmapsetsController](https://github.com/ppy/osu-web/blob/master/app/Http/Controllers/BeatmapsetsController.php)：网页下载、noVideo、配额和重定向。
- [官方辅助函数](https://github.com/ppy/osu-web/blob/master/app/helpers.php)：官网 Referer / Origin 检查。
- [Nerinyan 下载服务](https://github.com/Nerinyan/nerinyan-download-apiv1/blob/main/route/download/downloadBeatmapSetV2.go)：下载请求和 nv / noVideo 参数。
- [Mino 服务](https://catboy.best/) 与 [API 文档入口](https://catboy.best/docs)。
- [Sayobot 网站](https://osu.sayobot.cn/) 的实际前端下载链接：`https://txy1.sayobot.cn/beatmaps/download/full/{id}`，无视频为 `novideo/{id}`。

真实联网验证结果与测试结果见同目录 `VALIDATION.md`。

