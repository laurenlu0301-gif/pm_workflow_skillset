# -*- coding: utf-8 -*-
"""校验脚本：精确枚举所有答案组合 + 模拟答题人 + 题量时长 + 文案合规扫描。
运行：python3 validate.py  →  生成 校验报告.md
"""
import itertools
import math
import random
import re
from collections import Counter, defaultdict

import engine
import quizdata as q

random.seed(20261027)
DIMS = engine.DIMS
READ_SPEED = 400       # 字/分钟，按手机端中文轻松阅读的保守估计
THINK_SEC = 3          # 每题思考与点选时间（秒）
PERSONAS = 20000       # 每套测试模拟的答题人数


# =====================================================================
# 一、精确分布：所有答案组合逐一计入（等价于穷举，用动态规划加速）
# =====================================================================
def exact_t1():
    states = {tuple([0] * 6): 1}
    for _, opts in q.T1_QUESTIONS:
        nxt = defaultdict(int)
        idxs = [DIMS.index(d) for _, d in opts]
        for st, n in states.items():
            for i in idxs:
                s = list(st)
                s[i] += 1
                nxt[tuple(s)] += n
        states = nxt
    dist, match_hist, dual_pairs = Counter(), Counter(), Counter()
    for st, n in states.items():
        for _, fd in q.T1_FINAL[1]:
            sc = dict(zip(DIMS, st))
            sc[fd] += 1
            key, m, tied = engine.t1_result(sc, fd)
            dist[key] += n
            if m is not None:
                match_hist[m] += n
            if tied:
                dual_pairs[len(tied)] += n
    total = 4 ** len(q.T1_QUESTIONS) * 6
    assert sum(dist.values()) == total
    return dist, total, match_hist, dual_pairs


def exact_t2():
    dist, mh = Counter(), Counter()
    for ans in itertools.product((0, 1), repeat=len(q.T2_QUESTIONS)):
        k, m = engine.t2_score(ans)
        dist[k] += 1
        mh[m] += 1
    return dist, 2 ** len(q.T2_QUESTIONS), mh


def exact_t3():
    per_trait = {}
    for t in q.T3_TRAITS:
        d = Counter({(0, 0): 1})  # (分数, ±2 档次数)
        for _, trait, opts in q.T3_QUESTIONS:
            if trait != t:
                continue
            nd = Counter()
            for (s, e), n in d.items():
                for _, v in opts:
                    nd[(s + v, e + (abs(v) == 2))] += n
            d = nd
        per_trait[t] = d
    traits = list(q.T3_TRAITS)
    dist, mh = Counter(), Counter()
    tb_traits = [t for _, t in q.T3_TIEBREAK[1]]
    for combo in itertools.product(*[list(per_trait[t].items()) for t in traits]):
        n = math.prod(c for _, c in combo)
        sc = {t: se[0] for t, (se, _) in zip(traits, combo)}
        ex = {t: se[1] for t, (se, _) in zip(traits, combo)}
        for tb in tb_traits:
            k, m = engine.t3_result(sc, ex, tb)
            dist[k] += n
            if m is not None:
                mh[m] += n
    total = 4 ** len(q.T3_QUESTIONS) * len(tb_traits)
    assert sum(dist.values()) == total
    return dist, total, mh


def exact_t4():
    dist, mh = Counter(), Counter()
    for ans in itertools.product((0, 1), repeat=len(q.T4_QUESTIONS)):
        k, m = engine.t4_score(ans)
        dist[k] += 1
        mh[m] += 1
    return dist, 2 ** len(q.T4_QUESTIONS), mh


# =====================================================================
# 二、模拟答题人：有“真实倾向”的人，答题时有一定随机性
# =====================================================================
def sim_t1(consistency):
    hits, dist = 0, Counter()
    for _ in range(PERSONAS):
        true = random.choice(DIMS)
        ans = []
        for _, opts in q.T1_QUESTIONS:
            ds = [d for _, d in opts]
            if true in ds and random.random() < consistency:
                ans.append(ds.index(true))
            else:
                ans.append(random.randrange(4))
        fds = [d for _, d in q.T1_FINAL[1]]
        final = fds.index(true) if random.random() < consistency else random.randrange(6)
        key, _, tied = engine.t1_score(ans, final)
        dist[key] += 1
        hits += 1 if key == true else (0.5 if key == "DUAL" and true in tied else 0)
    return hits / PERSONAS, dist


def sim_t2(consistency):
    hits, dist = 0, Counter()
    for _ in range(PERSONAS):
        true = tuple(random.randrange(2) for _ in range(3))
        pole = dict(zip(("pace", "focus", "mode"), true))
        ans = []
        for i, (*_, ax) in enumerate(q.T2_QUESTIONS, 1):
            p = pole[ax] if random.random() < consistency else 1 - pole[ax]
            ans.append(1 - p if i in q.T2_FLIPPED else p)
        key, _ = engine.t2_score(ans)
        dist[key] += 1
        hits += key == true
    return hits / PERSONAS, dist


def _pick_by_latent(values, theta, temp=0.8):
    w = [math.exp(-((v - theta) ** 2) / temp) for v in values]
    r, acc = random.random() * sum(w), 0
    for i, x in enumerate(w):
        acc += x
        if r <= acc:
            return i
    return len(w) - 1


def sim_t3(dominant_level):
    """每人一个主导特质（潜在值 ±dominant_level），其余特质在 [-1, 1] 内随机。"""
    hits, dist = 0, Counter()
    traits = list(q.T3_TRAITS)
    tb_traits = [t for _, t in q.T3_TIEBREAK[1]]
    for _ in range(PERSONAS):
        dom, sign = random.choice(traits), random.choice((1, -1))
        theta = {t: random.uniform(-1, 1) for t in traits}
        theta[dom] = sign * dominant_level
        ans = [_pick_by_latent([v for _, v in opts], theta[tr]) for _, tr, opts in q.T3_QUESTIONS]
        tb = tb_traits.index(dom) if random.random() < 0.6 else random.randrange(5)
        key, _ = engine.t3_score(ans, tb)
        dist[key] += 1
        hits += key == (dom, sign)
    return hits / PERSONAS, dist


def sim_t4(consistency):
    """每人在两条轴上各有一个真实档位：低/中/高 → 答 A 的概率 1-c / 0.5 / c。"""
    hits, dist = 0, Counter()
    for _ in range(PERSONAS):
        true = (random.randrange(3), random.randrange(3))
        p = {ax: [1 - consistency, 0.5, consistency][lv] for ax, lv in zip(("act", "show"), true)}
        ans = []
        for i, (*_, ax) in enumerate(q.T4_QUESTIONS, 1):
            hit = random.random() < p[ax]          # True = 选了“记分”的那一项
            ans.append((0 if hit else 1) if i not in q.T4_FLIPPED else (1 if hit else 0))
        key, _ = engine.t4_score(ans)
        dist[key] += 1
        hits += key == true
    return hits / PERSONAS, dist


# =====================================================================
# 三、可达性证明：为每个结果构造一组具体答案
# =====================================================================
def witness_t1():
    found = {}
    for target in DIMS:
        ans = [next((i for i, (_, d) in enumerate(o) if d == target), 0) for _, o in q.T1_QUESTIONS]
        final = [d for _, d in q.T1_FINAL[1]].index(target)
        found[engine.t1_score(ans, final)[0]] = (ans, final)
    for _ in range(200000):
        if "HEX" in found and "DUAL" in found:
            break
        ans = [random.randrange(4) for _ in q.T1_QUESTIONS]
        final = random.randrange(6)
        k = engine.t1_score(ans, final)[0]
        found.setdefault(k, (ans, final))
    return found


def witness_generic(score_fn, n_q, n_opt, extra=None, tries=300000):
    found = {}
    for _ in range(tries):
        ans = [random.randrange(n_opt) for _ in range(n_q)]
        args = (ans,) if extra is None else (ans, random.randrange(extra))
        k = score_fn(*args)[0]
        found.setdefault(k, args)
    return found


def letters(ans):
    return "".join("ABCDEF"[a] for a in ans)


# =====================================================================
# 三点五、文档手算规则 vs 程序计分：按《测试文字版.md》里读者看到的规则独立重写，随机对拍
# =====================================================================
def parse_doc_keys():
    """从生成的文档里读出 T2 / T4 的“哪题选哪个字母记分”清单，按读者视角计分。"""
    doc = open("测试文字版.md", encoding="utf-8").read()
    t2 = re.findall(r"- \*\*(\S+) / (\S+)\*\*（第 [^）]+题）：选了 ([^记]+) 记为", doc)
    t4 = dict(re.findall(r"- \*\*(行动分|外放分)\*\* = 下列选项你选中了几个（0～6）：(.+)", doc))
    def items(s):
        return [(int(x[:-1]), x[-1]) for x in s.split("、")]
    return [(a, b, items(lst)) for a, b, lst in t2], {k: items(v) for k, v in t4.items()}


def crosscheck(n=50000):
    t2_rules, t4_rules = parse_doc_keys()
    assert len(t2_rules) == 3 and len(t4_rules) == 2, "文档计分规则解析失败"
    mism = Counter()
    name2 = {r["name"]: k for k, r in q.T2_RESULTS.items()}
    table2 = {}
    for (a, b, c), r in q.T2_RESULTS.items():
        table2[(q.T2_AXES["pace"][a], q.T2_AXES["focus"][b], q.T2_AXES["mode"][c])] = (a, b, c)
    for _ in range(n):
        # 测试 1：读者规则
        ans = [random.randrange(4) for _ in q.T1_QUESTIONS]
        fi = random.randrange(6)
        sc = Counter({d: 0 for d in DIMS})
        for (_, o), a in zip(q.T1_QUESTIONS, ans):
            sc[o[a][1]] += 1
        fd = q.T1_FINAL[1][fi][1]
        sc[fd] += 1
        hi, lo = max(sc.values()), min(sc.values())
        if hi - lo <= q.T1_HEX_GAP:
            doc_k = "HEX"
        else:
            tops = [d for d in DIMS if sc[d] == hi]
            doc_k = tops[0] if len(tops) == 1 else (fd if fd in tops else "DUAL")
        mism["t1"] += doc_k != engine.t1_score(ans, fi)[0]
        # 测试 2：用文档里的字母清单
        ans = [random.randrange(2) for _ in q.T2_QUESTIONS]
        poles = []
        for pa, pb, lst in t2_rules:
            hit = sum(1 for qi, L in lst if "AB"[ans[qi - 1]] == L)
            poles.append(pa if hit >= 3 else pb)
        mism["t2"] += table2[tuple(poles)] != engine.t2_score(ans)[0]
        # 测试 3：读者规则
        ans = [random.randrange(4) for _ in q.T3_QUESTIONS]
        tb = random.randrange(5)
        sc = {t: 0 for t in q.T3_TRAITS}
        ex = {t: 0 for t in q.T3_TRAITS}
        for (_, tr, o), a in zip(q.T3_QUESTIONS, ans):
            sc[tr] += o[a][1]
            ex[tr] += abs(o[a][1]) == 2
        m = max(abs(v) for v in sc.values())
        if m <= q.T3_HIDDEN_MAX:
            doc_k = "HIDDEN"
        else:
            tied = [t for t in sc if abs(sc[t]) == m]
            tied = [t for t in tied if ex[t] == max(ex[x] for x in tied)]
            ring = ["O", "C", "E", "A", "N"]  # 文档：好奇心→自律度→社交能量→随和度→情绪敏感度
            st = ring.index(q.T3_TIEBREAK[1][tb][1])
            t = next(ring[(st + i) % 5] for i in range(5) if ring[(st + i) % 5] in tied)
            doc_k = (t, 1 if sc[t] > 0 else -1)
        mism["t3"] += doc_k != engine.t3_score(ans, tb)[0]
        # 测试 4：用文档里的字母清单
        ans = [random.randrange(2) for _ in q.T4_QUESTIONS]
        lv = []
        for k in ("行动分", "外放分"):
            v = sum(1 for qi, L in t4_rules[k] if "AB"[ans[qi - 1]] == L)
            lv.append(0 if v <= 2 else 1 if v == 3 else 2)
        mism["t4"] += tuple(lv) != engine.t4_score(ans)[0]
    return n, mism


# =====================================================================
# 四、题量、字数、阅读时长
# =====================================================================
def zh_len(s):
    return len(re.sub(r"\s", "", s))


def length_stats():
    out = {}
    t1 = sum(zh_len(t) + sum(zh_len(o) for o, _ in opts) for t, opts in q.T1_QUESTIONS)
    t1 += zh_len(q.T1_FINAL[0]) + sum(zh_len(o) for o, _ in q.T1_FINAL[1])
    out["t1"] = (len(q.T1_QUESTIONS) + 1, t1)
    t2 = sum(zh_len(t) + zh_len(a) + zh_len(b) for t, a, b, _ in q.T2_QUESTIONS)
    out["t2"] = (len(q.T2_QUESTIONS), t2)
    t3 = sum(zh_len(t) + sum(zh_len(o) for o, _ in opts) for t, _, opts in q.T3_QUESTIONS)
    t3 += zh_len(q.T3_TIEBREAK[0]) + sum(zh_len(o) for o, _ in q.T3_TIEBREAK[1])
    out["t3"] = (len(q.T3_QUESTIONS) + 1, t3)
    t4 = sum(zh_len(t) + zh_len(a) + zh_len(b) for t, a, b, _ in q.T4_QUESTIONS)
    out["t4"] = (len(q.T4_QUESTIONS), t4)
    return {k: (n, c, c / READ_SPEED + n * THINK_SEC / 60) for k, (n, c) in out.items()}


# =====================================================================
# 五、文案与合规扫描
# =====================================================================
BANNED = {
    "MBTI 名称/代码": [r"MBTI", r"[EI][NS][TF][JP]", r"十六型", r"16\s*型", r"16\s*种人格"],
    "SBTI 相关": [r"SBTI", r"死者", r"拿捏者", r"吗喽", r"傻乐", r"酒鬼", r"CTRL", r"HHHH", r"DRUNK"],
    "脏话/低俗": [r"傻[逼比]", r"(?<![A-Za-z])SB(?![A-Za-z])", r"卧槽", r"他妈", r"操你", r"屌", r"废物", r"nmsl", r"去死"],
    "伪科学/绝对化": [r"科学测", r"科学证明", r"心理学证明", r"天命", r"命中注定", r"注定", r"100\s*%", r"百分百准",
                  r"精准测", r"权威", r"准到", r"超准", r"最准", r"测出你的命运"],
    "编造统计": [r"\d+(\.\d+)?\s*%\s*的人", r"[0-9一二三四五六七八九十百千万]+万人", r"数据显示", r"研究表明",
             r"统计显示", r"只有\s*\d", r"仅有?\s*\d+\s*%", r"全国", r"稀有度"],
    "临床/诊断用语": [r"抑郁症", r"焦虑症", r"人格障碍", r"躁郁", r"精神病", r"确诊"],
    "站外导流暗号": [r"扣\s*1", r"私信.*链接", r"评论区.*链接", r"加[微Vv]", r"二维码", r"vx", r"wx"],
}
REVIEW = {"需人工过目": [r"命运", r"测出", r"天选", r"焦虑"]}


def all_copy():
    """收集要发布的全部文案（不含免责声明本身），返回 [(位置, 文本)]。"""
    items = []
    for meta in (q.T1_META, q.T2_META, q.T3_META, q.T4_META):
        k = meta["key"]
        items += [(f"{k}.标题", meta["title"])] + [(f"{k}.标题备选", t) for t in meta["titles"]]
        items += [(f"{k}.封面", meta["cover"]), (f"{k}.角度", meta["angle"])]
    for i, (t, opts) in enumerate(q.T1_QUESTIONS, 1):
        items += [(f"t1.Q{i}", t)] + [(f"t1.Q{i}", o) for o, _ in opts]
    items += [("t1.Q25", q.T1_FINAL[0])] + [("t1.Q25", o) for o, _ in q.T1_FINAL[1]]
    for i, (t, a, b, _) in enumerate(q.T2_QUESTIONS, 1):
        items += [(f"t2.Q{i}", t), (f"t2.Q{i}", a), (f"t2.Q{i}", b)]
    for i, (t, _, opts) in enumerate(q.T3_QUESTIONS, 1):
        items += [(f"t3.Q{i}", t)] + [(f"t3.Q{i}", o) for o, _ in opts]
    items += [("t3.Q21", q.T3_TIEBREAK[0])] + [("t3.Q21", o) for o, _ in q.T3_TIEBREAK[1]]
    for i, (t, a, b, _) in enumerate(q.T4_QUESTIONS, 1):
        items += [(f"t4.Q{i}", t), (f"t4.Q{i}", a), (f"t4.Q{i}", b)]
    results = ([("t1", k, r) for k, r in {**q.T1_RESULTS, **q.T1_SPECIAL}.items()]
               + [("t2", k, r) for k, r in q.T2_RESULTS.items()]
               + [("t3", k, r) for k, r in q.T3_RESULTS.items()] + [("t3", "HIDDEN", q.T3_HIDDEN)]
               + [("t4", k, r) for k, r in q.T4_RESULTS.items()])
    for t, k, r in results:
        for field in ("name", "quote", "shine", "fit", "manual", "tip", "sub", "buddy_line", "rival_line"):
            if r.get(field):
                items.append((f"{t}.结果[{r['name']}].{field}", r[field]))
        items += [(f"{t}.结果[{r['name']}].roast", x) for x in r["roast"]]
    return items, results


def lint():
    items, results = all_copy()
    hard, review = [], []
    for loc, text in items:
        for cat, pats in BANNED.items():
            for p in pats:
                if re.search(p, text):
                    hard.append((cat, loc, text, p))
        for cat, pats in REVIEW.items():
            for p in pats:
                if re.search(p, text):
                    review.append((loc, text, p))
    # 结构性检查
    struct = []
    for t, k, r in results:
        if not (2 <= zh_len(r["name"]) <= 7):
            struct.append(f"{t} {r['name']}：标签长度 {zh_len(r['name'])} 字，建议 2~7 字")
        if zh_len(r["quote"]) > 24:
            struct.append(f"{t} {r['name']}：金句 {zh_len(r['quote'])} 字，超过 24 字不利于截图转发")
        if len(r["roast"]) < 3:
            struct.append(f"{t} {r['name']}：戳点少于 3 条")
    names = [r["name"] for *_, r in results]
    dup = [n for n, c in Counter(names).items() if c > 1]
    if dup:
        struct.append(f"标签重名：{dup}")
    quotes = [r["quote"] for *_, r in results]
    if len(set(quotes)) != len(quotes):
        struct.append("存在重复金句")
    # 搭子/相克引用有效
    for k, r in q.T1_RESULTS.items():
        for f in ("buddy", "rival"):
            if r[f] not in q.T1_RESULTS or r[f] == k:
                struct.append(f"t1 {r['name']} 的 {f} 引用无效")
    for k, r in q.T3_RESULTS.items():
        for f in ("buddy", "rival"):
            if r[f] not in q.T3_RESULTS or r[f] == k:
                struct.append(f"t3 {r['name']} 的 {f} 引用无效")
    for t, res in (("t1", q.T1_RESULTS), ("t3", q.T3_RESULTS)):
        for k, r in res.items():
            if r["buddy"] == r["rival"]:
                struct.append(f"{t} {r['name']} 的搭子和相克是同一个结果")
    # 题目重复
    qtexts = [t for loc, t in items if ".Q" in loc]
    if len(set(q.T1_QUESTIONS[i][0] for i in range(len(q.T1_QUESTIONS)))) != len(q.T1_QUESTIONS):
        struct.append("t1 题干重复")
    return hard, review, struct, len(items), sum(zh_len(t) for _, t in items), len(qtexts)


def balance_checks():
    out = []
    c = Counter(d for _, o in q.T1_QUESTIONS for _, d in o)
    out.append(("t1 各维度出现次数（前 24 题）", dict(c), len(set(c.values())) == 1))
    pos = defaultdict(Counter)
    for _, o in q.T1_QUESTIONS:
        for j, (_, d) in enumerate(o):
            pos[d][j] += 1
    worst = max(max(v.values()) for v in pos.values())
    out.append(("t1 同一维度落在同一字母位置的最多次数（24 题中）", worst, worst <= 7))
    c3 = Counter(tr for _, tr, _ in q.T3_QUESTIONS)
    out.append(("t3 各特质题数", dict(c3), len(set(c3.values())) == 1))
    for i, (_, tr, opts) in enumerate(q.T3_QUESTIONS, 1):
        if sorted(v for _, v in opts) != [-2, -1, 1, 2]:
            out.append((f"t3 Q{i} 分值不是 -2/-1/+1/+2", None, False))
    top_pos = Counter(next(j for j, (_, v) in enumerate(o) if v == 2) for _, _, o in q.T3_QUESTIONS)
    out.append(("t3 “+2 分”选项落在 A/B/C/D 的次数", {"ABCD"[k]: v for k, v in sorted(top_pos.items())},
                max(top_pos.values()) <= 7))
    c2 = Counter(ax for *_, ax in q.T2_QUESTIONS)
    out.append(("t2 各轴题数（须为奇数，避免平局）", dict(c2), all(v % 2 == 1 for v in c2.values())))
    c4 = Counter(ax for *_, ax in q.T4_QUESTIONS)
    out.append(("t4 各轴题数", dict(c4), len(set(c4.values())) == 1))
    return out


# =====================================================================
# 报告
# =====================================================================
def pct(n, total):
    return f"{100 * n / total:.1f}%"


def dist_table(dist, total, namer, expected_keys):
    rows = ["| 结果 | 占全部答案组合 | 可达 |", "|---|---:|:---:|"]
    for k in expected_keys:
        n = dist.get(k, 0)
        rows.append(f"| {namer(k)} | {pct(n, total)} | {'✅' if n else '❌'} |")
    extra = set(dist) - set(expected_keys)
    for k in extra:
        rows.append(f"| ⚠️ 未定义结果 {k} | {pct(dist[k], total)} | — |")
    return "\n".join(rows)


def sim_table(dist, namer, keys):
    total = sum(dist.values())
    return " ｜ ".join(f"{namer(k)} {pct(dist.get(k, 0), total)}" for k in keys)


def ratio(dist, keys):
    vals = [dist.get(k, 0) for k in keys]
    return max(vals) / min(vals) if min(vals) else float("inf")


def main():
    L = []
    w = L.append
    w("# 校验报告：四套文字版测试\n")
    w("> 由 `validate.py` 自动生成。所有数字都是脚本对本测试题目本身的计算结果，"
      "**不是**真实用户数据，也不能当作人群统计。\n")
    summary = []

    # ---------- 测试 1 ----------
    d1, tot1, mh1, dual1 = exact_t1()
    n1 = lambda k: (q.T1_RESULTS.get(k) or q.T1_SPECIAL[k])["name"]
    main6 = DIMS
    w("## 测试 1｜命运给你发工牌：你的天选工位是？\n")
    w(f"**精确枚举**：24 道四选一 + 1 道六选一，共 4²⁴×6 = {tot1:,} 种答案组合，全部计入（动态规划合并同分状态，结果与逐一穷举相同）。\n")
    w(dist_table(d1, tot1, n1, main6 + ["DUAL", "HEX"]))
    r1 = ratio(d1, main6)
    w(f"\n- 六个主结果最多/最少之比：**{r1:.3f}**（1.000 为完全均衡）")
    w(f"- 「双核打工人」占 {pct(d1['DUAL'], tot1)}：其中两维并列 {pct(dual1.get(2, 0), tot1)}，三维及以上并列 {pct(sum(v for k, v in dual1.items() if k >= 3), tot1)}")
    w(f"- 隐藏结果「六边形打工人」占 {pct(d1['HEX'], tot1)}（随机乱答时；认真答题的人更少触发，见下方模拟）")
    w(f"- 匹配度区间：{min(mh1)}%～{max(mh1)}%；分布 " + "、".join(f"{m}%:{pct(c, sum(mh1.values()))}" for m, c in sorted(mh1.items()) if c / sum(mh1.values()) > 0.03) + "（只列出 >3% 的档位）")
    w("\n**模拟答题人**（每人有一个真实偏好，每题以一定概率按偏好作答，否则随机）：\n")
    w("| 答题一致性 | 测出真实偏好的比例 | 结果分布 |\n|---|---:|---|")
    for c in (0.5, 0.65, 0.8):
        acc, dist = sim_t1(c)
        w(f"| {int(c * 100)}% | {acc:.1%} | {sim_table(dist, n1, main6 + ['DUAL', 'HEX'])} |")
    wit = witness_t1()
    w("\n**可达性证明**（每个结果给出一组能得到它的具体答案）：\n")
    for k in main6 + ["DUAL", "HEX"]:
        if k in wit:
            ans, final = wit[k]
            w(f"- {n1(k)}：前24题 `{letters(ans)}`，第25题 `{'ABCDEF'[final]}`")
        else:
            w(f"- {n1(k)}：❌ 未找到")
    ok1 = all(d1.get(k) for k in main6 + ["DUAL", "HEX"]) and r1 < 1.05
    summary.append(("测试1 天选工位", ok1, f"8/8 结果可达；主结果均衡度 {r1:.3f}"))

    # ---------- 测试 2 ----------
    d2, tot2, mh2 = exact_t2()
    keys2 = list(q.T2_RESULTS)
    n2 = lambda k: q.T2_RESULTS[k]["name"]
    w("\n## 测试 2｜你在工位上是哪种人格？\n")
    w(f"**精确穷举**：15 道二选一，共 2¹⁵ = {tot2:,} 种组合，逐一计算。\n")
    w(dist_table(d2, tot2, n2, keys2))
    r2 = ratio(d2, keys2)
    w(f"\n- 最多/最少之比：**{r2:.3f}**；每条轴 5 题（奇数），不存在平局")
    w("- 匹配度分布：" + "、".join(f"{m}%:{pct(c, tot2)}" for m, c in sorted(mh2.items())))
    w("\n**模拟答题人**：\n\n| 答题一致性 | 测出真实类型的比例 | 结果分布 |\n|---|---:|---|")
    for c in (0.65, 0.75, 0.85):
        acc, dist = sim_t2(c)
        w(f"| {int(c * 100)}% | {acc:.1%} | {sim_table(dist, n2, keys2)} |")
    wit2 = witness_generic(engine.t2_score, len(q.T2_QUESTIONS), 2)
    w("\n**可达性证明**：\n")
    for k in keys2:
        w(f"- {n2(k)}：`{letters(wit2[k][0])}`" if k in wit2 else f"- {n2(k)}：❌")
    ok2 = all(d2.get(k) for k in keys2) and r2 < 1.05
    summary.append(("测试2 工位人格", ok2, f"8/8 结果可达；均衡度 {r2:.3f}"))

    # ---------- 测试 3 ----------
    d3, tot3, mh3 = exact_t3()
    keys3 = list(q.T3_RESULTS) + ["HIDDEN"]
    n3 = lambda k: q.T3_HIDDEN["name"] if k == "HIDDEN" else q.T3_RESULTS[k]["name"]
    w("\n## 测试 3｜你的出厂说明书，第一页写着什么？\n")
    w(f"**精确枚举**：20 道四选一 + 1 道五选一决胜题，共 4²⁰×5 = {tot3:,} 种组合（按特质分别卷积后合并，结果与穷举相同）。\n")
    w(dist_table(d3, tot3, n3, keys3))
    r3 = ratio(d3, list(q.T3_RESULTS))
    w(f"\n- 十个主结果最多/最少之比：**{r3:.3f}**")
    w(f"- 隐藏结果「{q.T3_HIDDEN['name']}」占 {pct(d3['HIDDEN'], tot3)}（五项分数绝对值都 ≤ {q.T3_HIDDEN_MAX}）")
    w("- 匹配度分布：" + "、".join(f"{m}%:{pct(c, sum(mh3.values()))}" for m, c in sorted(mh3.items())))
    w("\n**模拟答题人**（每人一个主导特质，其余特质中等偏随机；按潜在倾向概率选项）：\n")
    w("| 主导特质强度 | 测出主导特质及方向的比例 | 隐藏结果占比 |\n|---|---:|---:|")
    sim3 = {}
    for lv in (1.0, 1.5, 2.0):
        acc, dist = sim_t3(lv)
        sim3[lv] = dist
        w(f"| {lv} | {acc:.1%} | {pct(dist['HIDDEN'], sum(dist.values()))} |")
    w("\n强度 1.5 时的结果分布：" + sim_table(sim3[1.5], n3, keys3))
    wit3 = witness_generic(engine.t3_score, len(q.T3_QUESTIONS), 4, extra=5)
    w("\n**可达性证明**：\n")
    for k in keys3:
        if k in wit3:
            ans, tb = wit3[k]
            w(f"- {n3(k)}：前20题 `{letters(ans)}`，第21题 `{'ABCDE'[tb]}`")
        else:
            w(f"- {n3(k)}：❌")
    ok3 = all(d3.get(k) for k in keys3) and r3 < 1.10
    summary.append(("测试3 出厂说明书", ok3, f"11/11 结果可达；主结果均衡度 {r3:.3f}"))

    # ---------- 测试 4 ----------
    d4, tot4, mh4 = exact_t4()
    keys4 = list(q.T4_RESULTS)
    n4 = lambda k: q.T4_RESULTS[k]["name"]
    w("\n## 测试 4｜压力来了，你会变成哪种形态？\n")
    w(f"**精确穷举**：12 道二选一，共 2¹² = {tot4:,} 种组合。\n")
    w(dist_table(d4, tot4, n4, keys4))
    r4 = ratio(d4, keys4)
    w(f"\n- 最多/最少之比：**{r4:.3f}**（每轴 0~2 / 3 / 4~6 分三档，乱答时概率为 22/64、20/64、22/64；6 道二选一分三档，这已是最均衡的切法，理论最小比值即 (22/20)² = 1.21）")
    w("- 匹配度分布：" + "、".join(f"{m}%:{pct(c, tot4)}" for m, c in sorted(mh4.items())))
    w("\n**模拟答题人**：\n\n| 答题一致性 | 测出真实格子的比例 |\n|---|---:|")
    for c in (0.7, 0.8, 0.9):
        acc, _ = sim_t4(c)
        w(f"| {int(c * 100)}% | {acc:.1%} |")
    wit4 = witness_generic(engine.t4_score, len(q.T4_QUESTIONS), 2)
    w("\n**可达性证明**：\n")
    for k in keys4:
        w(f"- {n4(k)}：`{letters(wit4[k][0])}`" if k in wit4 else f"- {n4(k)}：❌")
    ok4 = all(d4.get(k) for k in keys4) and r4 < 1.25
    summary.append(("测试4 压力形态", ok4, f"9/9 结果可达；均衡度 {r4:.3f}"))

    # ---------- 文档规则对拍 ----------
    n_cc, mism = crosscheck()
    w("\n## 文档手算规则 vs 程序计分（对拍）\n")
    w(f"按《测试文字版.md》里写给读者的规则独立重写计分（测试 2、4 直接从文档里解析“哪题选哪个字母记分”），"
      f"每套随机生成 {n_cc:,} 份答卷，与程序结果逐一比对：\n")
    for k, nm in (("t1", "天选工位"), ("t2", "工位人格"), ("t3", "出厂说明书"), ("t4", "压力形态")):
        w(f"- {nm}：不一致 {mism[k]} 份 {'✅' if mism[k] == 0 else '❌'}")
    summary.append(("文档规则与程序一致", sum(mism.values()) == 0, f"4×{n_cc:,} 份随机答卷，不一致 {sum(mism.values())} 份"))

    # ---------- 题量与时长 ----------
    w("\n## 题量与阅读时长\n")
    w(f"估算方法：题干+选项字数 ÷ {READ_SPEED} 字/分钟 + 每题 {THINK_SEC} 秒作答。\n")
    w("| 测试 | 题数 | 题目总字数 | 预计用时 | ≤30题 | ≤5分钟 |\n|---|---:|---:|---:|:---:|:---:|")
    ls = length_stats()
    names = {"t1": "天选工位", "t2": "工位人格", "t3": "出厂说明书", "t4": "压力形态"}
    for k, (n, c, mins) in ls.items():
        ok = n <= 30 and mins <= 5
        w(f"| {names[k]} | {n} | {c} | {mins:.1f} 分钟 | {'✅' if n <= 30 else '❌'} | {'✅' if mins <= 5 else '❌'} |")
        summary.append((f"{names[k]} 题量/时长", ok, f"{n} 题，约 {mins:.1f} 分钟"))

    # ---------- 结构平衡 ----------
    w("\n## 题目结构检查\n")
    for name, val, ok in balance_checks():
        w(f"- {'✅' if ok else '❌'} {name}：{val if val is not None else ''}")
        if not ok:
            summary.append((name, False, str(val)))

    # ---------- 合规 ----------
    hard, review, struct, n_items, n_chars, _ = lint()
    w("\n## 合规与文案扫描\n")
    w(f"扫描范围：标题、封面、全部题目选项、全部结果文案，共 {n_items} 段、{n_chars} 字（免责声明本身不扫）。\n")
    w("| 规则类别 | 命中 |\n|---|---:|")
    for cat in BANNED:
        w(f"| {cat} | {sum(1 for h in hard if h[0] == cat)} |")
    if hard:
        w("\n**硬性命中明细（必须修改）**：\n")
        for cat, loc, text, p in hard:
            w(f"- [{cat}] {loc}：「{text}」（规则 `{p}`）")
    w("\n**需人工过目的词**（不违规，但请 Lauren 确认语气）：\n")
    for loc, text, p in review:
        w(f"- {loc}：「{text}」（含“{p.strip('r')}”）")
    w("\n**结构检查**（标签 2~7 字、金句 ≤24 字、每个结果至少 3 条戳点、无重名、搭子/相克引用有效）：")
    w("\n- " + ("\n- ".join(struct) if struct else "✅ 全部通过"))
    w(f"\n- 免责声明：每套测试的题目前和结果后各出现一次（见文档），文本：\n\n> {q.DISCLAIMER}")
    # 对生成的成品文档整篇再扫一遍（含正文话术、计分说明），免责声明行除外
    doc_hits = []
    try:
        for ln, line in enumerate(open("测试文字版.md", encoding="utf-8"), 1):
            if "免责声明" in line or "合规底线" in line:  # 写给 Lauren 的内部说明，不发布
                continue
            for cat, pats in BANNED.items():
                for p in pats:
                    if re.search(p, line):
                        doc_hits.append((ln, cat, line.strip()[:60], p))
        w(f"\n**成品文档整篇复扫**（《测试文字版.md》，免责声明行和写给 Lauren 的“合规底线”说明除外）：命中 {len(doc_hits)} 处")
        for ln, cat, txt, p in doc_hits:
            w(f"- 第 {ln} 行 [{cat}] {txt}（规则 `{p}`）")
    except FileNotFoundError:
        w("\n⚠️ 未找到《测试文字版.md》，请先运行 build_doc.py")
        doc_hits.append(None)
    hard_all = len(hard) + len(doc_hits)
    summary.append(("合规硬性规则", not hard_all, f"文案库命中 {len(hard)} 处，成品文档命中 {len(doc_hits)} 处"))
    summary.append(("文案结构", not struct, f"问题 {len(struct)} 处"))

    # ---------- 吸引力 ----------
    w("\n## 吸引力自查（对照调研得出的爆款要素）\n")
    w("这是规则清单，不能代替真实发布数据；建议发布后看收藏率、评论里报结果的比例，再迭代。\n")
    w("| 要素 | 天选工位 | 工位人格 | 出厂说明书 | 压力形态 |\n|---|:---:|:---:|:---:|:---:|")
    rows = [
        ("一句可直接发朋友圈的金句", "✅", "✅", "✅", "✅"),
        ("有梗的标签名（2~7 字）", "✅", "✅", "✅", "✅"),
        ("戳小毛病（每个结果 3 条）", "✅", "✅", "✅", "✅"),
        ("匹配度百分比", "✅", "✅", "✅", "✅"),
        ("隐藏/稀有结果，制造“晒”的理由", "✅ 六边形/双核", "—", "✅ 未拆封", "—（中间格“弹簧人”）"),
        ("社交钩子：@朋友", "✅ 搭子/相克", "✅ 搭子/相克", "✅ 搭子/相克", "✅ 转给“总说没事”的人"),
        ("≤30 题、≤5 分钟", "✅", "✅", "✅", "✅"),
        ("结果卡片模板", "✅", "✅", "✅", "✅"),
    ]
    for r in rows:
        w("| " + " | ".join(r) + " |")

    # ---------- 总结 ----------
    head = ["\n## 总结\n", "| 检查项 | 结论 | 说明 |", "|---|:---:|---|"]
    head += [f"| {a} | {'✅ 通过' if ok else '❌ 未通过'} | {b} |" for a, ok, b in summary]
    L[2:2] = head
    open("校验报告.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(head))


if __name__ == "__main__":
    main()
