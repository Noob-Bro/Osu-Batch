# osu! Batch — Web 谱面批量下载工具
<img width="2172" height="724" alt="image" src="https://github.com/user-attachments/assets/b2b373ab-3664-4033-92d9-98a12d4d4227" />


[English](README.md) | **简体中文**

> [!WARNING]
> **安全提示**
>
> 请从本仓库安装用户脚本，并核对 Tampermonkey 请求的权限。官方下载使用浏览器当前的 osu! 登录状态，不要求复制或保存会话 Cookie。
>
> **请保持浏览器和安全软件的防护功能开启。**
>
> 历史 Windows 可执行版仍可从 Releases 获取，但已停止开发，运行 Web 版无需使用它。

本分支为 **osu! Batch Web 0.3.4**，即后续维护的 Tampermonkey 版，支持中英文界面切换和高级筛选。

仓库默认及后续开发分支为 **`tampermonkey-web`**。**Python 桌面程序及 Windows 可执行版自 2026-10-24 起停止开发**；源码保留在 [`main`](https://github.com/Noob-Bro/Osu-Batch/tree/main)，[历史 Releases](https://github.com/Noob-Bro/Osu-Batch/releases) 继续保留。

**源码启动：** 安装 Tampermonkey，打开[用户脚本原始文件](https://raw.githubusercontent.com/Noob-Bro/Osu-Batch/tampermonkey-web/tampermonkey/osu-batch.user.js)并确认安装。登录 [osu.ppy.sh](https://osu.ppy.sh/home)，点击页面上的 **osu! Batch** 悬浮按钮。

用户脚本位于 `tampermonkey/`。无需 Python 环境，也无需 Windows EXE。浏览器与下载权限的详细说明见 [Web 使用文档（英文）](tampermonkey/README.md)。

队列与设置保存在 Tampermonkey 存储中，与桌面 SQLite 队列相互独立；迁移时请重新加入需要的链接 / ID。

**Language / 界面语言：** 首次运行默认为 **English**。使用面板中的 **中文** / **English** 按钮切换，语言偏好会保存。

用户输入、谱面标题和艺术家名称保持原文。筛选值与下载状态不受界面语言影响。

---

## 按条件批量下载

在 osu! 官网打开 **osu! Batch** 面板。

例如：

1. 先登录 osu!；搜索始终使用官网，与下载来源选择独立。
2. 在 **艺术家** 中填写 `Laur`，开启 **精确艺术家**。
3. 状态选择 `Ranked`，模式选择 `osu! standard`。
4. 点击 **搜索全部分页**，查看分页结果。
5. 点击 **全选** 或逐项勾选，再点击 **加入选中**，选择下载来源后点击 **开始 / 继续**。

搜索不会自动添加任务。下载开始时使用队列控件及选定的保存方式。

**搜索来源**与**下载来源**相互独立：官网搜索的结果既可从官方下载，也可使用你主动选择的镜像。

检测已有曲库时，点击 **加载 osu!.db**，手动选择 osu!stable 数据库，通常为 `%LOCALAPPDATA%\osu!\osu!.db`。文件只在浏览器内本地解析，不会上传。提取的 BeatmapSet ID 保存在 Tampermonkey 存储中，命中的队列行和官网谱面链接会显示淡绿色。安装或移除谱面后需要重新加载数据库。脚本无法静默监控 `Songs`，也不读取 osu!lazer 的 `client.realm`。

### 筛选语义

* **精确艺术家匹配**会归一化字符宽度、大小写和首尾空格，并核对普通及 Unicode 艺术家字段。`Laur feat. Sennzai`、`Laurinha Costa` 不等于 `Laur`。
* **包含匹配**可能包含合作曲或相近名称。独立的 **艺术家（罗马字）** 字段使用包含匹配；上面的精确匹配示例应填写在 **艺术家** 字段。脚本不推断艺名别名。
* `Ranked` 严格指 `ranked`；`Approved` 是独立状态。
* 模式、BPM、时长和星数条件须由同一个难度满足。下载完整的 `.osz` 谱面集，不会删除其他难度或模式。
* 高级筛选包括标题 / 艺术家及罗马字字段、谱师、来源、流派、语言、BPM、时长、难度，以及提交 / 更新 / 上架或达标日期。支持升序、降序排列。日期使用官网对应字段，不推测缺失值。
* 脚本跟随官网游标分页，并在本地核对返回元数据。当前搜索设有 **200 页安全上限**，触发后请缩小筛选范围。
* 搜索失败或取消会在面板显示，不视为完整搜索成功；请重新搜索后选择结果。
* **全部分页**指官网接口在本次搜索中返回的页面。访问限制、结果上限及内容变化均可能影响结果，不保证跨来源或长期不变的绝对全集。
* 搜索也请求带 NSFW 标记的谱面。面板只展示文本元数据，不显示封面。

---


## 快速开始

安装 Tampermonkey 后，打开用户脚本原始地址：

```text
https://raw.githubusercontent.com/Noob-Bro/Osu-Batch/tampermonkey-web/tampermonkey/osu-batch.user.js
```

目录直接保存模式推荐：

* Edge 或 Chrome，配合 Tampermonkey
* 浏览器需支持目录选择；不支持时改用 **浏览器下载**

1. 登录 osu!，打开 **osu! Batch** 悬浮面板。
2. 选择来源，默认为 **osu! 官方**；镜像由用户手动选择。
3. 粘贴谱面集链接 / ID、收集当前页面链接，或搜索后加入选中结果。
4. 点击 **开始 / 继续**。目录模式会要求选择一次保存目录；浏览器下载模式可能请求多文件下载权限。
5. 下载期间保持页面打开，完成后将 `.osz` 文件拖入 osu!。

目录句柄仅在当前页面会话内保留，刷新后需要重新选择。脚本不会自动把文件导入 stable 或 lazer。

---


## 下载来源由用户决定

| 来源 | 行为 |
| --- | --- |
| **osu! 官方（默认）** | 使用当前浏览器的登录状态与官网网页下载路由 |
| **Sayobot / Nerinyan / Mino** | 使用用户主动选择的镜像 |
| **更换来源** | 由用户自行调整；脚本不会静默回退到镜像 |

搜索使用官网接口，与下载来源独立。

默认并发数为 **3**，可设为 **1–6**。新任务默认启动间隔为 **1.5 秒**，可在面板修改。遇到服务限流时，请暂停等待、降低并发或增加间隔；用户脚本不具备桌面程序的重试 / 共享冷却机制。

**不含视频**支持：

* osu! 官方
* Sayobot
* Nerinyan

脚本未提供经过验证的 Mino 无视频地址。实际资源是否可用取决于下载源。

**选择文件夹一次**模式会先在内存缓冲完整文件；目录中已有的同名文件可能被覆盖。并发越高，内存占用越多。**浏览器下载**作为兼容模式保留。

---


## 官方登录方式与限制

脚本运行于 `https://osu.ppy.sh/*`，使用官网已有的登录搜索与下载路由。

不需要创建 OAuth 应用，不要求输入 osu! 密码或手动粘贴 Cookie。

### 设置官网会话

1. 使用浏览器登录 [osu! 官网](https://osu.ppy.sh/home)。
2. 完成官网要求的验证。
3. 打开 **osu! Batch** 面板，选择官方下载来源。

> [!IMPORTANT]
> 登录会话由浏览器管理。
>
> **不要将会话 Cookie 粘贴到聊天、Issue、截图或公开日志中。**

脚本不会把 `osu_session` 的值复制到设置中。官网请求使用当前登录状态，镜像下载不要求提供官网会话。

官方请求被拒绝时，重新登录并完成网站验证；也可手动选择下载镜像，但镜像不会替代官网搜索接口。

Tampermonkey 需要允许脚本声明的网络与下载操作。`ppy.sh` 连接声明用于涵盖带编号的官方下载主机。

---


## 输入格式

支持例如：

```text
https://osu.ppy.sh/beatmapsets/123456#osu/789012
https://osu.ppy.sh/s/234567
345678
456789, 567890
```

规则：

* 纯数字按 **Beatmapset ID（谱面集 ID）** 解释，下载完整谱面集。
* 已存在于队列中的 ID 不会重复添加。
* 不解析 `/beatmaps/123`、`/b/123` 等单难度链接，请使用谱面集 URL。
* **收集当前页面**会获取当前 osu! 网页上的谱面集链接。
* 搜索结果先预览，再由用户明确加入选中记录。
* 已有曲库标记来自手动加载的 stable `osu!.db` 索引，不代表文件为最新版，也不会触发自动本地文件扫描。

---


## 暂停、续传和校验

* **暂停**会取消当前请求；**开始 / 继续**重试未完成队列项，不具备部分文件断点续传。
* 队列状态保存在 Tampermonkey 存储中，与桌面 SQLite 相互独立，不会自动迁移桌面队列。
* 下载时请保持 osu! 页面打开。刷新后不会保留已选目录。
* 用户脚本**不提供 ZIP CRC、下载包内 `.osu` 内容或谱面集 ID 校验**。桌面版的验证机制及文件大小限制不适用于本脚本。
* 目录模式会先在内存缓冲每个完整下载再写入。较大谱面请降低并发。
* 保存目录中已有的同名文件可能被覆盖；浏览器下载模式的重名处理由浏览器决定。
* 普通文件命名：

```text
谱面集ID 艺术家 - 标题.osz
```

* 无视频文件命名：

```text
谱面集ID-novideo 艺术家 - 标题.osz
```

* 只有链接 / ID 时，下载前尝试补齐名称；获取不到时使用已知字段或 ID。Windows 文件名非法字符会替换，过长名称会截短。
* **清除已完成**移除已完成记录，**清空全部**经确认后清空记录，均不删除已下载文件。
* **浏览器下载**可能需要多文件下载权限。若 Tampermonkey 对 `.osz` 报 `not_whitelisted`，可使用目录模式、原生浏览器下载回退，或在 Tampermonkey 下载设置中允许 `osz`。
* 原生浏览器回退表示已启动浏览器下载，最终结果请查看浏览器下载列表。
* 本地曲库索引保存在 Tampermonkey 存储中，直到清除或重新加载；选中的 `osu!.db` 只在本地解析，不会上传。

---


## 源码运行

完整用户脚本位于：

```text
tampermonkey/osu-batch.user.js
```

打开[原始脚本](https://raw.githubusercontent.com/Noob-Bro/Osu-Batch/tampermonkey-web/tampermonkey/osu-batch.user.js)安装，或把内容复制到 Tampermonkey 新建脚本中。无需 Python 环境或 EXE 构建。

### 开发验证与打包

使用 Node.js 运行 JavaScript 测试：

```powershell
node --test tampermonkey/osu-batch.test.js tampermonkey/osu-batch.concurrent.test.js
```

测试模拟下载，不访问线上服务。分发 `osu-batch.user.js` 即可，保留脚本元数据及指向本分支的更新 / 下载地址。

Python 程序、构建文件及桌面验证文档保留在 [`main`](https://github.com/Noob-Bro/Osu-Batch/tree/main)，不再放在 Web 分支，也不再持续维护。

---


## 文件结构

* `tampermonkey/osu-batch.user.js`：脚本界面、筛选、本地数据库解析和下载队列。
* `tampermonkey/osu-batch.test.js`：解析及筛选测试。
* `tampermonkey/osu-batch.concurrent.test.js`：并发队列与下载测试。
* [`tampermonkey/README.md`](tampermonkey/README.md)：Web 版详细使用说明。
* `README.md` / `README.zh-CN.md`：中英文项目介绍。
* [`LICENSE`](LICENSE)：项目许可证。

---


## 接口与实现依据

文档更新日期：**2026-10-24**。本次更新不代表重新进行了线上接口兼容性验证。

外部服务行为可能变化。已实现的地址和限制以当前用户脚本为准。

* [官方认证与 API 文档](https://osu.ppy.sh/docs/)。
* [官方 BeatmapsetsController](https://github.com/ppy/osu-web/blob/master/app/Http/Controllers/BeatmapsetsController.php)：网页搜索与下载实现。
* [Nerinyan 下载服务](https://github.com/Nerinyan/nerinyan-download-apiv1/blob/main/route/download/downloadBeatmapSetV2.go)。
* [Mino](https://catboy.best/) 与其 [API 文档](https://catboy.best/docs)。
* [Sayobot](https://osu.sayobot.cn/) 下载地址：

```text
https://txy1.sayobot.cn/beatmaps/download/full/{id}
https://txy1.sayobot.cn/beatmaps/download/novideo/{id}
```

实现与离线测试：

* [用户脚本](tampermonkey/osu-batch.user.js)
* [解析 / 筛选测试](tampermonkey/osu-batch.test.js)
* [并发队列测试](tampermonkey/osu-batch.concurrent.test.js)

Python / Windows 历史验证文档仍在 [`main`](https://github.com/Noob-Bro/Osu-Batch/tree/main)，不能视为本 Web 版的验证结论。

---


## License / 许可证

许可证信息请参阅 [`LICENSE`](LICENSE)。
