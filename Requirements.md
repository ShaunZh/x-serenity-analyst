你现在扮演一位顶尖的全栈工程师与自动化专家。你的任务是在我当前的项目工作区中，自主实现一个名为 "x-analyst" 的自定义 Claude Code Skill。这个 Skill 的核心功能是自动抓取并深度分析 X.com 用户 @aleabitoreddit 自 2025 年以来的所有推文。

请在我的工作区中自主、有条不紊地执行以下步骤：

### 步骤 1：环境与依赖检查
1. 检查本地环境是否已安装 Python 3.10+。
2. 检查并自动通过 pip 安装数据抓取所需的 `twikit` 库（如果尚未安装）。

### 步骤 2：创建抓取脚本
在 `.claude/skills/x-analyst/scraper.py` 创建一个 Python 脚本，要求满足以下技术标准：
1. 使用 `twikit.Client` 处理所有 X.com 的请求。
2. 脚本需接收 `username`、`cookie_path` 和 `output_path` 作为命令行参数。
3. 从本地 `x_cookies.json` 文件中读取并注入 Session Cookies，以绕过 X 的登录墙和反爬机制。
4. 实现基于游标（Cursor-based）的分页功能，以完整获取历史推文。
5. **严格的边界过滤**：过滤掉所有 2025 年 1 月 1 日之前的推文。一旦时间轴触及 2024 年，立即停止抓取并断开连接。
6. 提取并存储关键字段：`id`、`text`、`created_at`、`retweet_count`、`favorite_count`，并以结构化的 JSON 格式保存。
7. 必须包含完备的异常处理（如速率限制 Rate Limit、Cookies 失效、网络超时），并在终端打印清晰的进度日志。

### 步骤 3：创建 Skill 定义文件
在 `.claude/skills/x-analyst/SKILL.md` 创建 Skill 配置文件，内容必须包含：
1. 符合 Claude Code 规范的 Frontmatter 元数据头部（包含 name, description, dependencies）。
2. 触发与执行指南：明确指示 Claude Code，当用户输入包含 "分析 X 用户 @[用户名]" 时，自动在终端后台调用 python 脚本，并将生成的 JSON 作为上下文读取。
3. **顶级的硬核半导体与金融供应链分析框架**。强制分析引擎在解析推文文本时，重点提炼以下维度：
   - **未知的结构性瓶颈（Unknown Structural Bottlenecks）**：如 CPO（光电共封装）、硅光子学（Silicon Photonics）、先进封装、化合物半导体等利基环节的物理或产能限制。
   - **标的与供应链图谱（Ticker & Supply Chain Mapping）**：精准提取所有股票代码（如 $AXTI, $AAOI），理清它们在产业链中的利基生态位，以及上游供应商与下游大客户的动态。
   - **逻辑主线演变（Thesis Evolution）**：纵向追踪博主的叙事逻辑从 2025 年初到 2026 年当下的变化和修正。
   - **风险与流动性矩阵（Risk & Liquidity Vector Analysis）**：清晰区分技术路线更迭的毁灭性风险与小市值标的的流动性/空头挤压（Short Squeeze）风险。

### 步骤 4：完美性验证
验证工作区的目录结构是否完全符合以下规范：
└── .claude/
    └── skills/
        └── x-analyst/
            ├── SKILL.md
            └── scraper.py

当所有文件生成完毕且语法检查无误后，向我清晰地汇报你所构建的内容，并指导我如何从浏览器导出 X 的 Cookies 并保存为 `x_cookies.json`，以便我们进行第一次实际运行测试。现在请开始执行。