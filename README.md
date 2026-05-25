# 🧭 Personal Investment Knowledge Base (x-analyst)

> **基于 Andrej Karpathy "LLM Compiles Personal Wiki" 理念构建的半导体与金融供应链个人投资知识库。**

本系统能够自动、增量式抓取 X.com (原 Twitter) 深度行业专家的历史推文，通过 AI 将零散的推文碎片“编译”为结构清晰、带有双向链接（Bi-directional Links）的 Obsidian 本地 Wiki 网络，并将每一次的 AI 交互问答与深度研究报告自动持久化归档（Filing），实现个人投资资产的良性生长。

---

## 📂 项目目录结构

```
. (工作区根目录)
├── README.md                   # 本说明文件
├── Requirements.md             # 原始设计需求
├── x_cookies.json              # 从浏览器导出的 X.com Session Cookies
├── .venv/                      # Python 3.10+ 虚拟运行环境
│
├── .claude/skills/x-analyst/   # 🤖 Claude Code 智能 Skill 插件
│   ├── SKILL.md                # Skill 激活与自动化流程指南
│   ├── scraper.py              # 增量式网络抓取引擎 (基于 twscrape)
│   ├── compile_wiki.py         # Wiki 增量编译器
│   └── accounts.db             # 抓取会话管理数据库 (SQLite)
│
└── wiki/                       # 🧭 个人投资知识库 (可作为 Obsidian Vault 直接打开)
    ├── index.md                # 🧭 Wiki 主导航门户 (主索引页面)
    ├── raw/
    │   └── tweets_aleabitoreddit.json # 原始推文数据 (850+ 条, 2025年至今)
    ├── concepts/               # 🧪 前沿核心概念卡片 (CPO, Silicon Photonics, Glass Substrates 等)
    ├── tickers/                # 📈 供应链个股研究卡片 (SIVE, AXTI, LPK, SOI 等)
    └── reports/                # 📂 历史深度分析与 Q&A 问答归档目录
```

---

## 🚀 核心功能与使用指南

### 1. 本地可视化探索（作为您的“第二大脑”）

知识库完美适配 **Obsidian**（行业最顶尖的本地 Markdown 知识库阅读器），可在本地渲染出震撼的关系拓扑图谱：

1. **下载并安装 Obsidian**（完全免费且支持多端同步）。
2. **加载知识库**：打开 Obsidian，选择 **"Open folder as vault" (将文件夹作为库打开)**，选择工作区根目录下的 `wiki/` 目录。
3. **双向链接冲浪**：
   * 打开 `index.md` 首页，您可以按住键盘 `Cmd` (Mac) 或 `Ctrl` (Windows) 并将鼠标悬停在 `[[SIVE]]` 或 `[[CPO]]` 上进行**浮窗预览**，点击直接跳转。
4. **开启“全局关系图谱” (Graph View)**：
   * 点击左侧工具栏的 **"Open graph view" (打开关系图谱)** 按钮，瞬间获得以技术瓶颈（如 CPO）为核心辐射全产业链标的的视觉星空图，洞察核心 chokepoints。

---

### 🔄 2. 增量式极速同步（保持数据最新，省时省力）

当博主 `@aleabitoreddit` 发布新内容后，您只需在终端中运行以下命令（自动跳过已缓存推文，保护账号额度）：

```bash
# 1. 增量同步新推文并与本地合并去重（当连续遇到 5 条已缓存推文时自动熔断退出，极大节省时间与频次）
.venv/bin/python3 .claude/skills/x-analyst/scraper.py \
  --username aleabitoreddit \
  --cookie-path x_cookies.json \
  --output-path wiki/raw/tweets_aleabitoreddit.json

# 2. 重新编译 Wiki，自动更新 tickers 和 concepts 下的笔记卡片与时间轴
.venv/bin/python3 .claude/skills/x-analyst/compile_wiki.py
```

> **💡 Session 过期如何重置 Cookies？**
> 1. 在 Chrome/Firefox 浏览器中登录 [x.com](https://x.com)。
> 2. 使用 Chrome 插件 **"Get cookies.txt LOCALLY"**，将 `x.com` 的 Cookies 导出为 **JSON 格式**。
> 3. 将导出的文件重命名为 `x_cookies.json` 并覆盖存放在项目根目录下，重新运行抓取即可。

---

### 🤖 3. AI 智能问答与研报自动归档（沉淀投资资产）

在 Claude Code 终端中，您可以对本地知识库发起极高质量的产业链与估值问答。您的每一次提问，都将被**自动持久化为本地资产**：

#### **💡 提问示例**
> * “请帮我深入分析一下存储领域的 $SNDK (闪迪) 与 $MU (美光)，看看 Serenity 在 2025 到 2026 年关于他们的 Thesis 演进是怎样的？在分析完后，请将其自动归档为研报。”
> * “读取我们知识库的 InP 衬底概念，结合 $AXTI、美国芯片法案、以及中国 humanoid 供应链，分析地缘战争溢价对持仓的结构性影响，并将其自动归档为研报。”

#### **⚙️ 问答执行背后的自动化闭环**
1. **AI 智能解析**：Claude 自动以极其硬核的四支柱行研框架（物理瓶颈、个股映射、主线演变、风险流动性矩阵）生成 publication 水准的报告。
2. **自动归档 (Filing)**：报告以 `wiki/reports/Report-<YYYY-MM-DD>-<Topic>.md` 格式自动被 AI 写入您的本地。
3. **一键自动索引**：系统自动调用 `compile_wiki.py`，将这篇报告自动登记在您的 `wiki/index.md` 导航首页上。您在 Obsidian 中无需任何操作，即可见证知识的自然生长！

---

### 🌐 4. 手动指派与高品质翻译归档（手动降噪精选）

由于博主日常发言包含很多无行研价值的普通社交发帖，系统默认应用了**自动高频降噪**规则。但如果您在时间线中发现了一条具有深度研究价值、但默认尚未翻译的推文，您可以进行**手动指派翻译**：

#### **💡 操作指南**
1. **获取推文 ID**：在 Obsidian 中打开 `wiki/monthly/YYYY-MM.md` 查找对应推文卡片，从卡片顶部的 X.com Link 链接末尾复制那一长串数字 ID（例如 `2058644487224848654`）。
2. **在 Claude 中发号施令**：直接对 Claude 说：
   > **`翻译并归档推文 2058644487224848654`** *(支持输入多个 ID，用逗号或空格隔开)*
3. **AI 代理自动化流水线**：
   * Claude 会自动抓取原推文英文正文；
   * 输出符合半导体产业链金融水准的高质量中英对照翻译，并为译文自动提取 `[[SIVE]]`、`[[JBL]]` 等核心 Obsidian 实体链接；
   * 翻译结果自动存入本地缓存 `wiki/raw/translations_cache.json`；
   * 自动重新跑一遍 Wiki 编译器，将这篇译文渲染到对应的月份归档 Markdown 中。您再次查看月份文件，该推文已瞬间转变为精美的 **`★ 中文精选对照 (Bilingual)`** 双语卡片！

---

## 🧭 投资实战与深度学习指南 (Investing & Learning Playbook)

将这个自动化 Obsidian 知识库转化为您的 **Alpha（超额收益）发生器** 与 **半导体认知演进沙盘**，我们推荐您从以下两个维度进行实战运作：

### 📈 维度一：如何利用知识库进行“投资实战（Alpha Generator）”

#### 1. 概念联想与技术卡脖子排查 (Physics-Level Chokepoints)
*   **方法**：当市场炒作某个热门宏观概念（如 CPO、玻璃基板、先进包装）时，不要去追拥挤的主线龙头。
*   **操作**：在 Obsidian 中打开对应的 Concept 笔记卡片（如 `[[Glass Substrates]]`），查看 Serenity 提炼出的底层技术瓶颈，顺藤摸瓜找到指向的**隐秘、小市值“物理级卖水人”**（如 `[[LPK]]` — 玻璃基板激光钻孔垄断；`[[AXTI]]` — 磷化铟衬底核心垄断；`[[SIVE]]` — CPO 独家高功率激光源）。
*   **看点**：在主流机构反应过来之前，提前建仓未被充分定价的行业咽喉标的。

#### 2. 追踪“资质认证周期”确定建仓窗口 (Qualification & Vol.Ramp Timeline)
*   **方法**：半导体设备与芯片公司的营收往往滞后于资质认定 6-18 个月。通过时间线锁定真正的“放量中点（Volume Ramp Midpoint）”。
*   **操作**：按月追踪 [wiki/monthly/](file:///Users/zhangjie/MyWorkspace/x-serenity-analyst/wiki/monthly/) 的中英对照时间线，重点检索博主提及的 **资质认证节点（Qualifications）**。例如 [2026-05.md](file:///Users/zhangjie/MyWorkspace/x-serenity-analyst/wiki/monthly/2026-05.md) 中关于 `[[SIVE]]` 与 `[[JBL]]` 的译文，摩根大通指出量产中点前移至 2026 年底。
*   **看点**：利用“量产催化剂时间戳”与公司财报交叉比对，作为您**建仓、加仓、分批止盈的绝对时间窗口指引**。

#### 3. AI 终端情境测试与研报沉淀 (AI Scenario Analysis & Filing)
*   **方法**：利用 AI 代理（Claude）作为您的 24 小时顶级半导体行业分析师。
*   **操作**：每当有重大地缘政治事件、财报发布时，在终端中直接向 AI 提问（例如：*“读取本地 `[[AXTI]]` 笔记，结合最新稀土出口管制，分析地缘战争溢价对 Nvidia TPU 供应链的卡脖子程度，生成评估报告”*）。AI 会自动生成 publication 水准的报告存入 `wiki/reports/` 并登记在首页导航。
*   **看点**：见证您的个人独家特许认知资产库（Proprietary Research Vault）随时间呈复利自然生长。

---

### 🧪 维度二：如何利用知识库“深度学习博主的底层认知框架”

#### 1. 拆解博主的“第一性原理”思维 (Physics-Level First Principles)
*   **学习要点**：避开碎片化推文的“信息肥胖症”，直接学习博主是如何从“硬物理限制/工程瓶颈”出发倒推商业壁垒的。
*   **操作方法**：打开 `wiki/concepts/` 文件夹，学习博主是如何从“电信号传输面临物理衰减极限，所以光互连是物理学上的唯一出路”这类底层科学常识出发，寻找并锁定具有技术代际差的投资标的的。

#### 2. 追踪 Thesis 演进与时空复盘 (Cognitive Endurance)
*   **学习要点**：不要只看博主封神的涨幅，要重点学习他是如何在公司没有业绩、全网群嘲的巨大波动中坚守 Thesis 并在几个月后迎来市场验证的。
*   **操作方法**：打开任何一个 Ticker 笔记（如 `wiki/tickers/AAOI.md`），**从时间轴最底部的第一条推文开始往上读**，还原他在股价极度被市场扭曲时的心理建设与判断细节，锤仁您在风浪中的“持股认知耐力（Cognitive Endurance）”。

#### 3. “苏格拉底式”AI 交互对抗学习 (Socratic Confrontational Learning)
*   **学习要点**：通过“辩论”与“教授”内化知识。
*   **操作方法**：在 Claude 终端中，让 AI 扮演您的辩论对手（空头机构），发起对抗性推演。
    *   *提问示例*：“我现在扮演一个不看好 Sivers 的空头机构，认为激光器只是普通二极管商品毫无门槛。请你根据 Serenity 的历史 Thesis 储备，找出 3 个核心反驳论点，与我发起辩论并生成辩论研报。”

---

## ⚖️ 许可与免责声明

* **免责声明**：本知识库包含的所有内容（包括 AI 生成的研报及博主推文）均属于独立研究与信息汇编，不构成任何形式的投资建议（NFA - Not Financial Advice）。
* **知识产权**：本项目抓取的原始数据归原作者所有，本地 Wiki 仅用于个人离线研究与学习目的。
