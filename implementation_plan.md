# 方案设计：构建月份归档中英文对照时间线 (Phase 2: Monthly Bilingual Timeline)

> **本文件为项目本地的重大功能设计与演进方案（Implementation Plan）记录本。后续大功能设计均将在此追加与沉淀。**

## 🎯 目标描述

为了让用户能够以时间线维度直观回溯博主的 Thesis 逻辑，我们将在个人投资知识库中增设一个 **「月份中英双语归档网络」**。每一只股票与前沿技术（如 `$SIVE`, `CPO` 等）在双语对照推文中的提及都将被自动识别，并打上 `[[Obsidian]]` 双向链接，使时间线网络与个股、概念数据库融为一体。

---

## 🛠️ 设计方案

升级后的项目架构将扩展为：

```
wiki/
├── index.md                    # 【升级】主门户首页：增设月份时间轴导航
├── raw/
│   ├── tweets_aleabitoreddit.json
│   └── translations_cache.json  # 【新建】本地增量翻译缓存 (保存 ID ➔ 译文 对照)
├── monthly/                     # 【新建】月份归档目录
│   ├── 2026-05.md               # 2026年5月份中英对照推文
│   ├── 2026-04.md               # 2026年4月份中英对照推文
│   └── ...
```

---

## 🚀 提议的变更

### 1. 增量翻译缓存机制与数据结构

#### [NEW] `wiki/raw/translations_cache.json`
我们将使用一个结构化的 JSON 文件作为翻译缓存。数据格式如下：
```json
{
  "2058644487224848654": {
    "zh": "有趣的行业事实：许多相同的公司往往被跨界应用于不同的供应链中。例如：Sivers 作为 Boston Dynamics 的上游激光供应商...",
    "translated_at": "2026-05-25T14:10:00Z"
  }
}
```
*   **缓存加载与判定**：每次编译时，读取此缓存。仅将新抓取且在缓存中不存在的推文发送给强大的 AI 代理（您当前的 AI 助手）进行高精度金融级翻译，完成翻译后回写缓存。
*   **防爆与零成本**：由于 100% 本地缓存已翻译推文，后续执行编译时，**0 token 额外消耗，瞬间渲染**！

---

### 2. 双引擎选择性收录设计 (Selective Curation Design)

由于博主日常包含大量庆祝订阅数、碎碎念等无研究价值推文，我们将采用**“自动降噪 + 手动ID指派”**的双引擎设计：

#### 引擎 A：自动高频降噪过滤器 (Auto-Filter Base)
在自动编译时，仅对符合以下“行研级门槛”的推文进行自动收录：
*   **长度过滤**：推文正文长度 $\ge 100$ 个字符（过滤简短调侃与短回复）。
*   **关联特征**：推文正文必须提及至少一个核心 Ticker (如 `$SIVE`, `$AXTI`) 或核心 Concept (如 `CPO`, `Glass Substrate`)。
*   **影响力门槛**：点赞数 `favorite_count > 50`。

#### 引擎 B：手动指派精选命令 (Targeted ID Curation)
*   **强制收录机制**：提供命令行/Skill 指令，支持用户直接输入想要强行收录的推文 ID。
*   **执行方式**：当检测到手动指定的 ID 时，自动绕过过滤器进行强制翻译，写入翻译缓存并高亮显示（★ 精选 Thesis）渲染进对应的月份归档。

---

### 3. 升级 Wiki 编译器支持月份时间轴

#### [MODIFY] [compile_wiki.py](file:///Users/zhangjie/MyWorkspace/x-serenity-analyst/.claude/skills/x-analyst/compile_wiki.py)
*   **按月份聚类**：解析 `created_at` 字段，将推文按照 `YYYY-MM` 进行聚类。
*   **中英对照排版生成**：在 `wiki/monthly/` 下自动生成 `YYYY-MM.md` 文件。排版采用极具极客质感的 Markdown 分隔模块，每个推文包含：
    *   📅 精确发布日期（带 X 推文原链接跳转）
    *   Original 英文原文
    *   中文专业对照（自动为英文中的 `$SIVE`、`CPO` 实体在中文译文里植入 `[[SIVE]]` 和 `[[CPO]]` 双向链接）
    *   统计互动数据（❤️ 赞数，🔁 转发数）
*   **首页挂载**：在 `wiki/index.md` 主门户首页上增设月份时间轴链接（例如 `[[2026-05]]` | `[[2026-04]]`），方便一键直达。

---

### 4. 升级自动化 Skill 指南

#### [MODIFY] [SKILL.md](file:///Users/zhangjie/MyWorkspace/x-serenity-analyst/.claude/skills/x-analyst/SKILL.md)
*   **抓取 ➔ 翻译 ➔ 编译全自动流**：当执行 `分析 X 用户 @[用户名]` 时：
    1. 运行增量抓取，得到最新 raw 数据。
    2. **AI 自动提取新增推文并增量编译翻译缓存**。
    3. 运行 `compile_wiki.py` 一键生成月份对照文档和个股卡片。
*   **手动指派精选指令支持**：当用户输入 `翻译并归档推文 <ID1>, <ID2>` 时，系统单独触发翻译引擎，绕过自动降噪器，将目标推文强制载入编译体系！

---

## 🎯 验证计划

1.  **缓存回写测试**：
    *   选择最新 5 条推文进行模拟增量翻译，检查 `translations_cache.json` 是否生成并写入了正确的中英对照译文。
2.  **过滤器门槛测试**：
    *   验证短于 100 字符或无 Ticker 的推文是否已被正确剔除出默认月份渲染列表。
3.  **月份生成测试**：
    *   执行完整编译，检查 `wiki/monthly/2026-05.md` 是否正确建立，是否包含中英排版，且中文译文中包含 `[[Obsidian]]` 双向引用。
4.  **导航验证**：
    *   查看 `wiki/index.md`，验证月份导航条是否挂载成功。

---

## 📅 Phase 2.1: 个股与概念卡片双语推文 ID 与链接集成 (ID & X Link Integration)

### 🎯 目标描述
为了让用户在浏览 `wiki/tickers/` 和 `wiki/concepts/` 的研究笔记时，能够对高价值但尚未翻译的推文进行“一键精准翻译”，我们将在所有个股与概念卡片涉及的推文旁，明文展示其唯一的 Tweet ID 并提供跳转链接。

### 🛠️ 变更内容

#### [MODIFY] [compile_wiki.py](file:///Users/zhangjie/MyWorkspace/x-serenity-analyst/.claude/skills/x-analyst/compile_wiki.py)
*   **个股 Thesis 模块**：在 `## 💡 Core Investment Thesis` 的引用块下方，追加 `— *来源推文 ID: `2058343691996282903` ([X.com 原帖链接](https://x.com/...))*` 的元数据标示。
*   **个股 Timeline 模块**：将 `1. **2026-05-20** (❤️ 120 | 🔁 15)` 升级为 `1. **2026-05-20** (❤️ 120 | 🔁 15 | ID: `2058343691996282903` | [X.com 原帖链接](https://x.com/...))`。
*   **行业概念 Quotes 模块**：将 `1. **2026-05-20**` 升级为 `1. **2026-05-20** (ID: `2058343691996282903` | [X.com 原帖链接](https://x.com/...))`。

### 🎯 验证计划
1.  **代码修改验证**：修改 `compile_wiki.py` 并运行 `python3 .claude/skills/x-analyst/compile_wiki.py`。
2.  **生成结果核对**：
    *   检查任意个股研究文件（如 `wiki/tickers/SIVE.md`），验证 Thesis 和 Historical Timeline 列表中是否已包含 ID 反引号标注与 X.com 链接。
    *   检查任意概念文件（如 `wiki/concepts/CPO.md`），验证 Quotes 列表中是否已包含 ID 反引号与 X.com 链接。

