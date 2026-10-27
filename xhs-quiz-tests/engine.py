# -*- coding: utf-8 -*-
"""计分引擎：与文档里写给读者的计分规则一一对应。"""
from collections import Counter

import quizdata as q

DIMS = list(q.T1_DIMS)


# ---------- 测试 1 ----------
def t1_result(scores, final):
    """scores: 维度->分数（已含第 25 题）；final: 第 25 题所选维度。
    返回 (结果键, 匹配度, 并列维度)；结果键为维度字母、'DUAL' 或 'HEX'。"""
    vals = sorted(scores.values(), reverse=True)
    top, second, low = vals[0], vals[1], vals[-1]
    if top - low <= q.T1_HEX_GAP:
        return "HEX", None, ()
    tied = [d for d in DIMS if scores[d] == top]
    if len(tied) == 1:
        return tied[0], q.t1_match(top, second), ()
    if final in tied:
        return final, q.t1_match(top, second), ()
    return "DUAL", None, tuple(tied)


def t1_score(answers, final):
    """answers: 24 个选项下标（0~3）；final: 第 25 题选项下标（0~5）。"""
    c = Counter({d: 0 for d in DIMS})
    for (_, opts), a in zip(q.T1_QUESTIONS, answers):
        c[opts[a][1]] += 1
    fd = q.T1_FINAL[1][final][1]
    c[fd] += 1
    return t1_result(c, fd)


# ---------- 测试 2 ----------
def t2_score(answers):
    """answers: 15 个 0/1（0=A，1=B）。返回 (结果键, 匹配度)。"""
    count = {ax: [0, 0] for ax in q.T2_AXES}
    for i, ((_, _, _, ax), a) in enumerate(zip(q.T2_QUESTIONS, answers), 1):
        count[ax][1 - a if i in q.T2_FLIPPED else a] += 1
    key, maj = [], 0
    for ax in ("pace", "focus", "mode"):
        a_cnt, b_cnt = count[ax]
        key.append(0 if a_cnt > b_cnt else 1)
        maj += max(a_cnt, b_cnt)
    return tuple(key), q.t2_match(maj)


# ---------- 测试 3 ----------
def t3_result(scores, extremes, tiebreak_trait):
    """extremes: 特质 -> 该特质下选了几次 ±2 档。"""
    strength = max(abs(v) for v in scores.values())
    if strength <= q.T3_HIDDEN_MAX:
        return "HIDDEN", None
    tied = [t for t in q.T3_TRAITS if abs(scores[t]) == strength]
    if len(tied) > 1:
        most = max(extremes[t] for t in tied)
        tied = [t for t in tied if extremes[t] == most]
    # 仍并列：从第 21 题所选特质起，按环形顺序往后数，最先遇到的并列特质胜出
    ring = q.T3_RING
    start = ring.index(tiebreak_trait)
    t = next(ring[(start + i) % len(ring)] for i in range(len(ring)) if ring[(start + i) % len(ring)] in tied)
    return (t, 1 if scores[t] > 0 else -1), q.t3_match(strength)


def t3_score(answers, tiebreak):
    """answers: 20 个选项下标（0~3）；tiebreak: 第 21 题选项下标（0~4）。"""
    s = {t: 0 for t in q.T3_TRAITS}
    ext = {t: 0 for t in q.T3_TRAITS}
    for (_, trait, opts), a in zip(q.T3_QUESTIONS, answers):
        s[trait] += opts[a][1]
        ext[trait] += abs(opts[a][1]) == 2
    return t3_result(s, ext, q.T3_TIEBREAK[1][tiebreak][1])


# ---------- 测试 4 ----------
def t4_score(answers):
    """answers: 12 个 0/1（0=A，1=B）。返回 (结果键, 匹配度)。"""
    s = {"act": 0, "show": 0}
    for i, ((_, _, _, ax), a) in enumerate(zip(q.T4_QUESTIONS, answers), 1):
        s[ax] += 1 if a == (1 if i in q.T4_FLIPPED else 0) else 0
    key = (q.t4_level(s["act"]), q.t4_level(s["show"]))
    return key, q.t4_match(s["act"], s["show"])
