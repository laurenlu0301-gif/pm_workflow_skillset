# -*- coding: utf-8 -*-
"""从 quizdata.py 生成交付文档：测试文字版.md"""
import quizdata as q

ABC = "ABCDEF"
L = []
w = L.append


def header(meta, n_q, minutes, n_results):
    w(f"\n---\n\n# {meta['kind']}｜{meta['title']}\n")
    w(f"**角度**：{meta['angle']}  ")
    w(f"**规格**：{n_q} 题｜约 {minutes} 分钟｜结果：{n_results}\n")
    w("### 标题备选\n")
    for i, t in enumerate(meta["titles"], 1):
        w(f"{i}. {t}")
    w(f"\n### 封面钩子\n\n{meta['cover']}\n")


def post_copy(intro, cta):
    w("（【】里的内容请换成你自己真实测出来的结果，不要编造他人的反馈。）\n")
    w("### 正文话术（站内闭环：不放外链、不用任何导流暗号）\n")
    w(f"> {intro}\n>\n> 👉 题目在图 2～图 N，拿张纸记下选项，最后一页对答案。\n>\n> {cta}\n>\n> #性格测试 #职业规划 #打工人 #自我探索 #娱乐测试\n")
    w(f"### 测试开场白\n\n> 凭第一反应选，不用想太久，没有好坏之分。\n>\n> {q.DISCLAIMER}\n")


def card(lines):
    w("```\n" + "\n".join(lines) + "\n```\n")


def roast_block(r):
    w("**戳你一下**：")
    for x in r["roast"]:
        w(f"- {x}")
    w(f"\n**其实你很会**：{r['shine']}\n")


# ---------------------------------------------------------------- 封面页
w("# 小红书文字版测试 · 4 套（2 套职业 + 2 套性格）\n")
w("Lauren，这份文档里是四套可以直接做成图文笔记的测试，每套都包括标题备选、封面钩子、正文话术、题目、计分规则、结果文案和分享卡片模板。"
  "所有计分规则都已经用 `validate.py` 跑过：所有答案组合都精确算过，并模拟了真实答题人，详见《校验报告.md》。\n")
w("| # | 测试 | 类型 | 角度 | 题数 | 用时 | 结果数 |\n|---|---|---|---|---:|---:|---:|")
w(f"| 1 | {q.T1_META['title']} | 职业 | 兴趣：愿意把时间花在哪 | 25 | ~4.5 分钟 | 6+双核+隐藏 |")
w(f"| 2 | {q.T2_META['title']} | 职业 | 工作风格：怎么干活 | 15 | ~2 分钟 | 8 |")
w(f"| 3 | {q.T3_META['title']} | 性格 | 五维性格里最突出的一面 | 21 | ~3.5 分钟 | 10+隐藏 |")
w(f"| 4 | {q.T4_META['title']} | 性格 | 压力下的应对形态 | 12 | ~1.5 分钟 | 9 |")
w("\n**通用设计原则**（来自调研）：结果标签自带梗、一句能直接发朋友圈的金句、三条“戳小毛病”比夸奖更容易转发、"
  "结果卡里带匹配度和“搭子/相克”，用来@朋友；题量控制在 30 题以内、5 分钟内做完。\n")
w("**图文笔记推荐结构**：图1 封面钩子 → 图2～N 题目（每图 4～6 题）→ 计分页 → 结果总览九宫格 → 每个结果一张卡片 → 最后一页放免责声明。"
  "文字版本身就是测试，**用户不用点外链**，正好避开小红书对站外导流的限制。\n")
w("**合规底线**：不用任何 MBTI 名称、代码或题目；不沿用 SBTI 的题目、标签或脏话梗；不写统计数字或稀有度；不说“科学测出”。"
  "每套测试的开头和结尾都放免责声明。\n")

# ================================================================ 测试 1
header(q.T1_META, 25, "4.5", "6 种主结果 + 双核 + 1 个隐藏结果")
post_copy("一直觉得自己“投错了岗”？做了这套 25 题的小测试，按你愿意把时间花在哪类事上，看看你的工牌最该印哪个部门。我测出来是【你的结果】，【一句真实的感受】😅",
          "评论区报出你的工牌，再@一个你觉得是“人形工具箱”的朋友～")
w("### 题目\n")
for i, (t, opts) in enumerate(q.T1_QUESTIONS, 1):
    w(f"**{i}. {t}**  ")
    w("  ".join(f"{ABC[j]}. {o}" for j, (o, _) in enumerate(opts)) + "\n")
w(f"**25. {q.T1_FINAL[0]}**  ")
w("  ".join(f"{ABC[j]}. {o}" for j, (o, _) in enumerate(q.T1_FINAL[1])) + "\n")

w("### 计分规则\n")
w("每道题的选项对应一个派别，选了就给那个派别 +1 分。六个派别：" +
  "、".join(f"**{v}**（{q.T1_RESULTS[k]['name']}）" for k, v in q.T1_DIMS.items()) + "。\n")
w("| 题 | A | B | C | D | E | F |\n|---|---|---|---|---|---|---|")
for i, (_, opts) in enumerate(q.T1_QUESTIONS, 1):
    w(f"| {i} | " + " | ".join(q.T1_DIMS[d] for _, d in opts) + " | | |")
w("| 25 | " + " | ".join(q.T1_DIMS[d] for _, d in q.T1_FINAL[1]) + " |")
w(f"""
**出结果**：
1. 如果六个派别里最高分和最低分只差 {q.T1_HEX_GAP} 分以内 → 隐藏结果 **{q.T1_SPECIAL['HEX']['name']}**。
2. 否则，最高分的派别就是你的结果。
3. 最高分有并列时，看第 25 题：你选的派别在并列里，就是它；不在 → **{q.T1_SPECIAL['DUAL']['name']}**，并列的几张卡都属于你。
4. **副属性**：第二高分的派别（有并列就任选一个），读对应的“副属性”一句话。

**匹配度** = 70 + 4×(最高分 − 第二高分) + 最高分，最低 72%，最高 98%。（例：最高 9 分、第二 6 分 → 70+12+9 = 91%）
""")

w("### 结果文案\n")
for k, r in q.T1_RESULTS.items():
    w(f"#### 【{r['name']}】· {r['alias']}\n")
    w(f"> **“{r['quote']}”**\n")
    roast_block(r)
    w(f"**天选工位**：{r['fit']}\n")
    b, rv = q.T1_RESULTS[r["buddy"]], q.T1_RESULTS[r["rival"]]
    w(f"**天生搭子**：{b['name']}（{r['buddy_line']}）  ")
    w(f"**最容易互相看不顺眼**：{rv['name']}（{r['rival_line']}）\n")
    w(f"**副属性台词**（第二高分是{r['alias']}时读这句）：{r['sub']}\n")
    card([f"🪪 我的天选工位", f"【{r['name']}】匹配度 __%", f"“{r['quote']}”",
          f"天生搭子：{b['name']}", f"副属性：______", "你的工牌上印着什么？"])
for k in ("DUAL", "HEX"):
    r = q.T1_SPECIAL[k]
    w(f"#### 【{r['name']}】· {r['alias']}\n")
    w(f"> **“{r['quote']}”**\n")
    roast_block(r)
    w(f"**天选工位**：{r['fit']}\n")
    card([f"🪪 我的天选工位", f"【{r['name']}】" + ("（隐藏结果）" if k == "HEX" else "＝ ____ + ____"),
          f"“{r['quote']}”", "你的工牌上印着什么？"])
w(f"> {q.DISCLAIMER}\n")

# ================================================================ 测试 2
header(q.T2_META, 15, "2", "8 种")
post_copy("同样是加班，有人是救火队长，有人是 DDL 收割机。15 道二选一，2 分钟就能测出你的工位人格，测完直接转给你的工作搭子👀",
          "评论区留下你的工位人格，看看你们组是不是全员救火队长🔥")
w("### 题目\n")
for i, (t, a, b, _) in enumerate(q.T2_QUESTIONS, 1):
    w(f"**{i}. {t}**  \nA. {a}　　B. {b}\n")
w("### 计分规则\n")
w("三组题各 5 题，按下面的对照数一数每组更偏哪一边（5 题不会打平）：\n")
groups = {}
for i, (*_, ax) in enumerate(q.T2_QUESTIONS, 1):
    groups.setdefault(ax, []).append(i)
for ax, (pa, pb) in q.T2_AXES.items():
    toa = "、".join(f"{i}{'B' if i in q.T2_FLIPPED else 'A'}" for i in groups[ax])
    w(f"- **{pa} / {pb}**（第 {'、'.join(map(str, groups[ax]))} 题）：选了 {toa} 记为{pa}，其余记为{pb}；{pa}≥3 题 → {pa}，否则 → {pb}")
w("\n| 节奏 | 对象 | 方式 | 你的工位人格 |\n|---|---|---|---|")
for (a, b, c), r in q.T2_RESULTS.items():
    w(f"| {q.T2_AXES['pace'][a]} | {q.T2_AXES['focus'][b]} | {q.T2_AXES['mode'][c]} | {r['name']} |")
w("\n**匹配度** = 三组里“多数票”的题数加起来 ÷ 15。（例：3+4+5 = 12 → 80%）\n")
w("### 结果文案\n")
keys = list(q.T2_RESULTS)
for k, r in q.T2_RESULTS.items():
    opposite = tuple(1 - x for x in k)
    rival = (1 - k[0], k[1], k[2])
    w(f"#### 【{r['name']}】· {q.T2_AXES['pace'][k[0]]} × {q.T2_AXES['focus'][k[1]]} × {q.T2_AXES['mode'][k[2]]}\n")
    w(f"> **“{r['quote']}”**\n")
    roast_block(r)
    w(f"**适合的岗位方向**：{r['fit']}\n")
    w(f"**互补搭子**：{q.T2_RESULTS[opposite]['name']}（你们三项全反，正好补位）  ")
    w(f"**最容易急眼**：{q.T2_RESULTS[rival]['name']}（只差节奏：你嫌TA{'慢' if k[0] == 0 else '急'}，TA嫌你{'急' if k[0] == 0 else '慢'}）\n")
    card(["💼 我的工位人格", f"【{r['name']}】匹配度 __%", f"“{r['quote']}”",
          f"互补搭子：{q.T2_RESULTS[opposite]['name']}", "@你的工作搭子来测"])
w(f"> {q.DISCLAIMER}\n")

# ================================================================ 测试 3
header(q.T3_META, 21, "3.5", "10 种 + 1 个隐藏结果")
post_copy("如果人出厂时附带一本说明书，第一页会写什么？21 道情景题，测测你性格里最突出的那一面。第一行就戳中我了🤣",
          "评论区报型号，再转给最懂你的那个人，看TA能不能猜中～")
w("### 题目\n")
for i, (t, _, opts) in enumerate(q.T3_QUESTIONS, 1):
    w(f"**{i}. {t}**  ")
    w("  ".join(f"{ABC[j]}. {o}" for j, (o, _) in enumerate(opts)) + "\n")
w(f"**21. {q.T3_TIEBREAK[0]}**  ")
w("  ".join(f"{ABC[j]}. {o}" for j, (o, _) in enumerate(q.T3_TIEBREAK[1])) + "\n")
w("### 计分规则\n")
w("第 1～20 题，每题只给一个维度加分或减分。按下表把五个维度的分数各自加起来：\n")
w("| 题 | 维度 | A | B | C | D |\n|---|---|---|---|---|---|")
for i, (_, tr, opts) in enumerate(q.T3_QUESTIONS, 1):
    w(f"| {i} | {q.T3_TRAITS[tr]} | " + " | ".join(f"{v:+d}" for _, v in opts) + " |")
w(f"""
第 21 题不计分，只用来决胜：A 好奇心、B 自律度、C 社交能量、D 随和度、E 情绪敏感度。

**出结果**：
1. 五个维度的分数（−8～+8）里，如果每一项的绝对值都 ≤ {q.T3_HIDDEN_MAX} → 隐藏结果 **{q.T3_HIDDEN['name']}**。
2. 否则找出**绝对值最大**的那个维度，正分读“高”结果，负分读“低”结果。
3. 绝对值并列时：先比较这几个维度里你选到 ±2 档的次数，多的胜出；还是并列，就从第 21 题选的那个维度开始，按“好奇心 → 自律度 → 社交能量 → 随和度 → 情绪敏感度 → 回到好奇心”的顺序往后数，最先数到的并列维度胜出。

**匹配度** = 66 + 4 × 主导维度分数的绝对值，最高 98%。（例：社交能量 −6 → 90%）
""")
w("| 维度 | 正分（高） | 负分（低） |\n|---|---|---|")
for tr, nm in q.T3_TRAITS.items():
    w(f"| {nm} | {q.T3_RESULTS[(tr, 1)]['name']} | {q.T3_RESULTS[(tr, -1)]['name']} |")
w("\n### 结果文案\n")
for k, r in q.T3_RESULTS.items():
    tr, sign = k
    w(f"#### 【{r['name']}】· {q.T3_TRAITS[tr]}{'偏高' if sign > 0 else '偏低'}\n")
    w(f"> **“{r['quote']}”**\n")
    roast_block(r)
    w(f"**使用说明（转给身边人）**：{r['manual'].removeprefix('跟TA相处：')}\n")
    w(f"**最佳搭档**：{q.T3_RESULTS[r['buddy']]['name']}　**最容易起摩擦**：{q.T3_RESULTS[r['rival']]['name']}\n")
    card(["📄 我的出厂说明书 · 第一页", f"型号：【{r['name']}】匹配度 __%", f"“{r['quote']}”",
          r["manual"], "转给最懂你的人，看TA能不能猜中"])
r = q.T3_HIDDEN
w(f"#### 【{r['name']}】· 隐藏结果\n\n> **“{r['quote']}”**\n")
roast_block(r)
w(f"**使用说明（转给身边人）**：{r['manual'].removeprefix('跟TA相处：')}\n")
card(["📄 我的出厂说明书 · 第一页", f"型号：【{r['name']}】（隐藏型号）", f"“{r['quote']}”", "转给最懂你的人，看TA能不能猜中"])
w(f"> {q.DISCLAIMER}\n")

# ================================================================ 测试 4
header(q.T4_META, 12, "1.5", "9 种")
post_copy("同样是 deadline 前崩溃，有人边骂边干，有人直接隐身。12 道二选一，测测你在压力下会变成哪一种形态。我是【你的结果】，【一句真实的感受】😶",
          "评论区报格子，再转给那个总说“我没事”的朋友🫂")
w("### 题目\n")
for i, (t, a, b, _) in enumerate(q.T4_QUESTIONS, 1):
    w(f"**{i}. {t}**  \nA. {a}　　B. {b}\n")
w("### 计分规则\n")
def _pick(ax):
    return "、".join(f"{i}{'B' if i in q.T4_FLIPPED else 'A'}"
                    for i, (*_, a) in enumerate(q.T4_QUESTIONS, 1) if a == ax)
w(f"- **行动分** = 下列选项你选中了几个（0～6）：{_pick('act')}")
w(f"- **外放分** = 下列选项你选中了几个（0～6）：{_pick('show')}")
w("- 每项分三档：0～2 低，3 中，4～6 高\n")
lv = ["低", "中", "高"]
w("| 行动 ＼ 外放 | 低（憋着） | 中 | 高（说出来） |\n|---|---|---|---|")
for a in (2, 1, 0):
    w(f"| {lv[a]}（{'先动' if a == 2 else '看情况' if a == 1 else '先停'}） | " +
      " | ".join(q.T4_RESULTS[(a, s)]["name"] for s in (0, 1, 2)) + " |")
w("\n**匹配度** = 70 + 4 ×（|行动分 − 3| + |外放分 − 3|），范围 70%～94%。\n")
w("### 结果文案\n")
for (a, s), r in q.T4_RESULTS.items():
    w(f"#### 【{r['name']}】· 行动{lv[a]} × 外放{lv[s]}\n")
    w(f"> **“{r['quote']}”**\n")
    roast_block(r)
    w(f"**给你的小提醒**：{r['tip'].removeprefix('提醒：')}\n")
    card(["🌀 我的压力形态", f"【{r['name']}】匹配度 __%", f"“{r['quote']}”", "转给那个总说“我没事”的朋友"])
w(f"> {q.DISCLAIMER}\n>\n> 如果压力已经长期影响到你的睡眠、饮食或日常生活，请寻求专业心理咨询或医疗帮助。\n")

open("测试文字版.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
print("ok", sum(len(x) for x in L), "chars")
