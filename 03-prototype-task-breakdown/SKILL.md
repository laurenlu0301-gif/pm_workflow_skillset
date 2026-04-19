# Skill: 原型验证任务拆解

## 元信息

```yaml
name: prototype-task-breakdown
version: 2.0
author: LU
trigger: 当用户有一份 PRD 或需求描述，想要快速搭建可交互原型进行验证时
tools: Coze + NoCode(美团) / Lovable / Cursor / Claude Code
```

---

## 📌 What This Skill Does

将产品需求（口述或 PRD）拆解为可直接交给 AI 编程工具执行的任务包，帮助 PM 快速搭建可交互验证原型。

支持前端工具：**NoCode（美团）/ Cursor / Claude Code / Lovable**  
支持后端方案：**纯前端 Mock / Coze 工作流 / 真实后端（Supabase 等）**

---

## 🎯 When to Use

当用户说以下任意一种话时触发此 Skill：

- "帮我把这个需求拆解成可以给 Cursor/NoCode 执行的任务"
- "我想快速做个原型验证一下这个功能"
- "把这个 PRD 转成 vibe coding 的执行指令"
- "我要搭一个 demo，帮我规划一下"
- 用户提供了需求描述或 PRD，并表示想要快速实现

---

## 📥 Input

支持两种输入方式，自动识别：

**方式 A：口述需求**  
用户直接描述产品功能和验证目标，无需结构化文档。

**方式 B：PRD 文档**  
用户粘贴已有 PRD，Skill 从中提取关键信息进行拆解。

---

## 📤 Output

输出一份结构化「原型任务包」，包含以下六个模块：

1. 验证目标确认
2. 后端方案推荐
3. 页面清单 + 字段定义
4. 后端工作流节点（如需要）
5. 给目标工具的执行指令
6. 验收标准

---

## 🔄 Steps

### Step 0：信息澄清（优先执行）

在开始拆解之前，检查用户是否提供了以下信息。**缺哪个问哪个，不要一次问超过 2 个问题。**

| 缺失信息 | 询问方式 |
|----------|----------|
| 不知道要验证什么 | "你最想通过这个原型验证的一件事是什么？" |
| 不知道用哪个前端工具 | "你打算用 NoCode、Cursor 还是其他工具来搭？" |
| 需求太模糊，无法拆解 | "能描述一下用户的核心操作路径吗？比如：用户进来→做了什么→看到什么结果" |
| 不确定是否需要后端 | "这个原型需要真实的 AI 处理，还是用假数据展示交互流程就够了？" |

> ⚠️ 如果用户提供了 PRD，优先从 PRD 中提取信息，不要重复问 PRD 里已有的内容。  
> 如果信息足够，直接跳到 Step 1，不要为了澄清而澄清。

---

### Step 1：提取验证目标

无论输入是口述还是 PRD，首先输出以下确认摘要：

```
【验证目标】这个原型要验证什么假设
【核心操作路径】用户进来 → 做了什么 → 看到什么结果（一句话）
【数据流向】输入什么 → 经过什么处理 → 返回什么
【验证成功标志】什么情况下可以说这个原型验证成功了
```

输出后问用户："以上理解是否正确？确认后我开始拆解。"

---

### Step 2：判断后端复杂度，推荐方案

根据功能特征，**主动推荐**以下三种方案之一，并说明推荐理由：

| 方案 | 适用场景 | 工具组合 |
|------|----------|----------|
| **A. 纯前端 Mock** | 只需验证交互流程、UI 布局，数据可以写死 | NoCode / Cursor 单独完成 |
| **B. Coze 工作流** | 需要 AI 处理、多步骤逻辑、但不需要持久化数据库 | NoCode/Cursor 前端 + Coze 后端 |
| **C. 真实后端** | 需要用户登录、数据存储、多用户协作 | Cursor + Supabase / Claude Code |

判断逻辑：
- 有 AI 生成/分析内容 → 至少选方案 B
- 只是展示固定内容或走流程 → 方案 A 够了
- 需要保存用户数据、登录态 → 方案 C

> ⚠️ 提醒用户：原型验证阶段优先选最简单的方案，能用 Mock 就不上 Coze，能用 Coze 就不上真实数据库。过度设计是原型阶段最大的时间杀手。

---

### Step 3：输出页面清单 + 字段定义

列出所有需要的页面，每个页面包含：

```
页面名称：[名称]
路由路径：/[path]
核心功能：[一句话]
UI 组件清单：
  - 组件名称 | 类型（输入框/按钮/列表/卡片等）| 字段名(英文) | 数据类型 | 说明
接口/数据来源：[Mock数据 / Coze节点名 / Supabase表名]
```

**示例（简历优化工具的输入页）：**

```
页面名称：简历上传页
路由路径：/upload
核心功能：用户上传简历并输入目标职位，提交后触发优化
UI 组件清单：
  - 文件上传区   | file input  | resume_file  | File   | 支持 PDF/Word
  - 目标职位输入 | text input  | target_role  | string | placeholder: "如：产品经理"
  - 提交按钮     | button      | -            | -      | 点击后 loading 状态，调用后端
接口/数据来源：Coze workflow /optimize
```

> ⚠️ 字段名必须用英文，NoCode 等平台不支持中文 key。

---

### Step 4：后端工作流节点定义（方案 B/C 时输出）

#### 如果选择方案 B（Coze）：

**4.1 整体节点结构**

根据需求复杂度选择以下之一：

```
方案 B-1：简单场景（单 LLM 节点）
Start → LLM节点 → End
适用：用户输入文本，AI 处理后直接返回结果

方案 B-2：中等场景（条件分支）
Start → Condition节点 → LLM节点A / LLM节点B → End
适用：需要根据用户意图走不同处理逻辑

方案 B-3：外部数据场景（插件节点）
Start → Plugin节点（调用外部API）→ LLM节点（整理数据）→ End
适用：需要实时数据、搜索、天气、数据库查询等
```

**4.2 输出完整节点配置清单**

```
工作流名称：[名称]
触发方式：HTTP 请求（POST）

【Start 节点】
字段名（英文）| 类型   | 说明          | 是否必填
user_input    | String | 用户输入内容  | 是
task_type     | String | 任务类型      | 否（有分支时才需要）

【LLM 节点 #1】
节点名称：[有意义的名字]
模型：Gemini 1.5 Flash（推荐）/ GPT-4o mini（备选）

System Prompt（直接复制粘贴到配置框）：
---
你是一个[角色]。你的任务是[具体任务]。

输出要求：
- [格式要求]
- [字数要求]
- 只返回结果本身，不要加任何说明文字，不要加 ```json 代码块标记
---

User Prompt（直接复制粘贴到配置框）：
---
用户输入：{{user_input}}
---

输出变量：output_text（String）

【Condition 节点】（如有分支）
条件写法：{{task_type}} == "类型A"
if 分支 → LLM节点A
else 分支 → LLM节点B

【Plugin 节点】（如需外部数据）
操作：左侧面板 → Plugin → 搜索插件名 → 拖入画布
输入参数 query → 引用 start.user_input
输出：在下一节点 prompt 里用 {{pluginName.output}} 引用

【End 节点】
输出变量：result → 引用 LLM节点.output_text
发布后记录：Workflow ID + Bot Token（前端调用需要）

【前端调用 Coze 的接口格式】
POST https://api.coze.com/v1/workflow/run
Headers: { "Authorization": "Bearer {{Bot Token}}", "Content-Type": "application/json" }
Body: { "workflow_id": "{{Workflow ID}}", "parameters": { "user_input": "..." } }
返回值: data.result
```

#### 如果选择方案 C（真实后端）：

```
数据表清单：
  表名 | 字段名 | 类型 | 说明

Edge Function 清单：
  函数名 | 触发条件 | 调用的外部 API | 返回格式
```

---

### Step 5：生成给目标工具的执行指令

根据用户使用的工具，生成对应格式的 prompt，可直接复制使用：

**给 NoCode（美团）的指令格式：**
```
请帮我创建一个[功能名称]页面，具体要求：
1. 页面包含以下组件：[组件清单]
2. 点击[按钮名]后，调用以下接口：[接口地址/Coze webhook]
3. 接口返回的[字段名]展示在[位置]
4. 样式要求：[简单描述风格]
```

**给 Cursor 的指令格式：**
```
请在现有项目中新建 [文件路径] 文件，不要修改其他文件，实现以下功能：
- 组件：[清单]
- 状态管理：[需要哪些 state]
- API 调用：POST [接口地址]，入参 [字段]，处理返回的 [字段] 并展示
- 错误处理：loading / error / empty state 都要处理
技术栈：[React/Vue + Tailwind 等，根据用户项目]
```

**给 Claude Code 的指令格式：**
```
我需要搭建一个[功能描述]的原型，请帮我：
1. 初始化项目结构（[技术栈]）
2. 创建以下文件：[文件路径列表]
3. 实现核心功能：[功能描述]
4. 连接后端：[接口/数据库配置]
当前项目结构如下：[粘贴文件树]
```

---

### Step 6：输出验收标准

```
✅ 验收 Checklist

页面层面：
  □ [页面名] 可以正常打开，无报错
  □ [关键交互] 按预期响应

数据层面：
  □ 提交后能收到后端返回数据
  □ 返回数据正确展示在页面上
  □ 异常情况（空数据/报错）有处理

验证目标层面：
  □ 用户可以完整走完 [核心操作路径]
  □ [验证假设] 可以通过这个原型得出初步结论
```

---

## ⚠️ Common Pitfalls（踩坑记录）

> 这是这个 Skill 最有价值的部分，根据实际使用持续补充。

**Coze 相关：**
- LLM 节点输出如果包含 markdown 格式（` ```json ``` ` 包裹），前端需要做两层解析：先 strip 掉 markdown fence，再 JSON.parse。在 System Prompt 里明确禁止可以从源头避免
- Coze workflow 免费版有输出长度限制，长文本场景建议分段输出或换 Dify
- Gemini Flash 有时会截断输出，max_tokens 建议设 2048 以上
- 前端调用 Coze webhook 时注意跨域问题，NoCode 平台通常需要走平台自己的 HTTP 节点中转
- Condition 节点字符串匹配不稳定，能用精确匹配（==）就不用 contains
- 变量引用失效 99% 是因为节点没连线，或者变量名大小写不一致

**NoCode（美团）相关：**
- 组件字段名不支持中文，必须用英文 key
- 图片上传组件返回 base64，直接传给 Coze 可能超出大小限制，考虑先上传到 OSS 再传 URL
- API 调用结果的嵌套字段（如 data.result.text）有时需要用平台自带的数据处理节点拍平

**Cursor 相关：**
- 给 Cursor 的指令要包含完整文件路径，不然它会随机创建文件位置
- 让 Cursor 改已有文件时，先说"不要修改其他文件"，不然它会乱动
- 改动较大时，先让它列出修改计划再执行，减少返工

**Claude Code 相关：**
- 适合从零初始化项目，不适合接手已有复杂项目
- 每次对话要把当前文件结构贴给它，不然容易重复创建文件
- 长对话后容易"失忆"，关键约定要在每轮 prompt 开头重申

---

## 💡 使用示例

**输入给 Claude 的内容：**
```
我要做一个简历优化工具的原型，用户输入简历文本，
选择优化类型（语言润色 or 岗位匹配），
AI 返回优化后的简历内容。
前端用 NoCode，后端用 Coze。
```

**Claude 应输出：**
- Step 1：结构化摘要（确认数据流）
- Step 2：推荐方案 B-2（Condition 分支，两个 LLM 节点）
- Step 3：前端页面组件清单（2个输入 + 1个下拉 + 1个结果区）
- Step 4：Coze 完整节点配置（含可直接粘贴的 System Prompt）
- Step 5：NoCode 格式的执行指令
- Step 6：验收 Checklist

---

## 📁 Skill 文件结构

```
03-prototype-task-breakdown/
├── SKILL.md                          ← 本文件
├── templates/
│   ├── task-package-template.md      ← 空白任务包模板
│   └── coze-workflow-template.md     ← Coze 工作流模板
└── examples/
    └── resume-optimizer-example.md   ← 简历优化工具的完整任务包示例
```

---

*最后更新：2026-04 | 作者：LU | 基于 NoCode + Coze + Cursor + Claude Code 真实项目沉淀*
