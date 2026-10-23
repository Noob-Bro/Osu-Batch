# osu! Batch Web — osu! 谱面批量下载工具

[English](README.md) | **简体中文**

osu! Batch Web 是运行在 [osu.ppy.sh](https://osu.ppy.sh/) 上的 Tampermonkey 用户脚本，支持筛选、收集并批量下载谱面集。官方下载使用当前浏览器的登录状态，镜像来源由用户明确选择。

> [!IMPORTANT]
> **项目方向调整（2026-10-24）：** 后续开发集中于 `tampermonkey-web` 分支的 Web / Tampermonkey 版。
> **Python 桌面程序及 Windows 可执行版已停止开发**，不再新增功能、修复或发布新的打包版本。已有源码与历史发行包保留，供现有用户使用和参考。

## 版本选择

| 版本 | 状态 | 入口 |
| --- | --- | --- |
| **Web / Tampermonkey 版** | **持续开发**；本次文档更新时脚本版本为 **0.3.4** | [安装脚本](https://raw.githubusercontent.com/Noob-Bro/Osu-Batch/tampermonkey-web/tampermonkey/osu-batch.user.js) · [详细说明（英文）](tampermonkey/README.md) |
| Python / Windows 可执行版 | **停止开发**；最近发布的桌面版本为 **1.1.1** | [旧版分支与使用说明](https://github.com/Noob-Bro/Osu-Batch/tree/main) · [历史 Releases](https://github.com/Noob-Bro/Osu-Batch/releases) |

本分支保留的 Python 文件属于桌面版历史代码，运行用户脚本无需使用它们，后续也不再以桌面版为开发目标。

## 安装与启动

1. 在浏览器安装 Tampermonkey。
2. 打开[脚本原始文件](https://raw.githubusercontent.com/Noob-Bro/Osu-Batch/tampermonkey-web/tampermonkey/osu-batch.user.js)，在 Tampermonkey 中确认安装。
3. 使用官网搜索和下载前先登录 [osu!](https://osu.ppy.sh/home)，再点击页面上的 **osu! Batch** 悬浮按钮。
4. 选择下载来源与保存方式，导入谱面集链接 / ID 或搜索谱面，然后点击 **开始 / 继续**。

无需安装 Python，也无需运行 Windows EXE。界面初始语言为 English，可切换中文。下载期间请保持 osu! 页面打开。

## 搜索与队列

- 粘贴谱面集 ID、`osu.ppy.sh/beatmapsets/...` 链接，或收集当前网页上的谱面集链接。
- 遍历官网谱面搜索接口返回的全部分页。
- 按标题 / 艺术家（含罗马字字段）、谱师、来源、状态、模式、流派、语言、BPM、时长、星数以及提交 / 更新 / 上架或达标日期筛选。
- 分页预览结果，可逐项选择或全选，再明确点击 **加入选中**。搜索本身不会自动添加下载任务。
- 按支持的字段升序或降序排列。
- 队列保存在 Tampermonkey 存储中；支持 **1–6 个并发下载**，默认 **3**，可设置新任务启动间隔。暂停会取消当前请求，再次开始时重试未完成项。

### 示例：Ranked + Laur + osu! standard

1. 在 **艺术家** 中填写 `Laur`，开启 **精确艺术家**。
2. 状态选择 `Ranked`，模式选择 `osu! standard`。
3. 点击 **搜索全部分页**。
4. 核对结果，点击 **全选** 或逐项勾选，再点击 **加入选中**。
5. 选择下载来源，点击 **开始 / 继续**。

精确艺术家匹配会归一化字符宽度和大小写，`Laur feat. Sennzai` 不等于 `Laur`。独立的艺术家罗马字字段使用包含匹配，因此本例的精确匹配应填写在 **艺术家** 字段。下载单位始终为完整 `.osz` 谱面集，不会删去其他难度或模式。

“全部分页”指该接口在本次搜索中返回的全部页面，不保证跨来源或长期不变的绝对全集；账号访问权限、搜索上限、镜像同步延迟及内容变动均可能影响结果。

## 下载来源与保存方式

默认下载来源为 **osu! 官方**，使用当前浏览器的 osu! 登录状态，不要求复制或保存 `osu_session` Cookie。Sayobot、Nerinyan、Mino 为可选下载镜像，必须由用户主动选择，脚本不会静默切换来源。搜索始终使用官网，与下载镜像选择独立。不含视频选项是否可用取决于来源。

在 Edge / Chrome 中，推荐使用 **选择文件夹一次**。开始时授权目标目录后，队列会把文件保存到该目录，无需逐个确认。目录句柄只在当前页面会话内保留，刷新后需要重新选择。**目录中已有的同名文件可能被覆盖。**

也可以选择 **浏览器下载** 兼容模式，此时仍可能需要浏览器多文件下载权限或 Tampermonkey 下载设置。若 `.osz` 被提示 `not_whitelisted`，可使用目录保存模式、原生浏览器下载回退，或在 Tampermonkey 中允许该扩展名。

文件命名为 `ID 艺术家 - 标题.osz`，无视频版本为 `ID-novideo 艺术家 - 标题.osz`。仅有链接 / ID 时，下载前会尝试补全元数据；无法获得名称时退回已有字段或 ID。目录模式会在内存中缓冲完整文件，谱面较大或设备内存不足时应降低并发数。

## 检测已有 osu!stable 曲库

点击 **加载 osu!.db**，手动选择 stable 数据库，通常位于：

```text
%LOCALAPPDATA%\osu!\osu!.db
```

文件只在浏览器内本地解析，不会上传。提取的 BeatmapSet ID 保存在 Tampermonkey 存储中，队列及官网页面中已安装的谱面会显示淡绿色。安装或移除谱面后，需要重新加载数据库以刷新索引。

脚本无法静默监控 `Songs`；暂不支持 osu!lazer 的 `client.realm`。

## 与桌面版的区别及迁移

| 项目 | Web 版 | 已停止开发的桌面版 |
| --- | --- | --- |
| 官网会话 | 使用当前浏览器登录 | 每次运行时向程序提供 Cookie |
| 队列 / 设置 | Tampermonkey 扩展存储 | `%LOCALAPPDATA%\OsuBatch` 下的 SQLite |
| 暂停 / 继续 | 继续队列；未完成的文件重新下载 | 下载源支持时可续传部分文件 |
| 压缩包验证 | 不进行 ZIP CRC 或下载内容校验 | CRC、`.osu` 与谱面集 ID 校验 |
| 本地曲库 | 用户手选 stable 的 `osu!.db` | 桌面源码支持只读扫描 stable `Songs` |

Web 版不会自动导入桌面版 SQLite 队列或设置。需要重新加入链接 / ID，也可从桌面版导出失败清单后粘贴到 Web 队列。本次文档更新不会更改本机已有队列、数据库或下载文件。

官网和镜像行为可能变化。本次文档更新不代表已重新验证线上服务的兼容性。

## 开发

后续维护的代码位于 `tampermonkey/`：

- `osu-batch.user.js`：可安装用户脚本。
- `osu-batch.test.js`：解析与筛选测试。
- `osu-batch.concurrent.test.js`：并发队列测试。
- `README.md`：Web 版详细使用说明。

使用 Node.js 运行模拟下载的离线测试：

```powershell
node --test tampermonkey/osu-batch.test.js tampermonkey/osu-batch.concurrent.test.js
```

后续贡献应以 `tampermonkey-web` 为目标分支，集中修改用户脚本。Python 程序、PyInstaller 构建文件与历史 Windows 发行包保留，但不再持续维护。

## 许可证

参阅 [LICENSE](LICENSE)。本项目与 osu! 及各镜像运营方无隶属关系。
