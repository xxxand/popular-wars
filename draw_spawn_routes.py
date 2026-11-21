import itertools
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src/resource/model/scene0/")
CFG = os.path.join(ROOT, "src/resource/configs/configs.json")
OUT = os.path.join(ROOT, "spawn-routes")

from matplotlib import font_manager as fm
for _w in ("Regular", "Bold"):
    fm.fontManager.addfont(f"/usr/local/share/fonts/sarasa-mono-sc/SarasaMonoSC-{_w}.ttf")
plt.rcParams["font.family"] = ["Sarasa Mono SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

d = json.load(open(SRC + "scene0.json"))
gs = json.load(open(CFG))["globalSet"]
W, H = int(d["width"]), int(d["height"])
HW, HH = W / 2, H / 2
grid = np.array(json.load(open(SRC + "scene0_c.json"))["mapData"]).reshape(H * 2, W * 2)
ROWS, COLS = grid.shape

SPEED = float(gs["moveSpeed"]) if not isinstance(gs, list) else 4.0
HORIZON = 30.0
DISCOUNT = 0.04
MAX_LEGS = 3

spawns = [(p["x"], p["z"]) for p in d["spawns"]]
wilds = d["wilds"]
wpos = [(w["position"]["x"], w["position"]["z"]) for w in wilds]

# ---------- 栅格与寻路 ----------
blocked = grid == -1
lab, _ = ndimage.label(blocked)
border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
outside = np.isin(lab, list(border))
img = np.zeros(grid.shape + (3,))
img[grid == 0] = (0.93, 0.95, 0.97)
img[blocked & ~outside] = (0.55, 0.60, 0.68)
img[outside] = (0.20, 0.23, 0.29)

free = ndimage.binary_erosion(grid == 0, iterations=1)
lab2, n2 = ndimage.label(free)
free = lab2 == (np.argmax(np.bincount(lab2.ravel())[1:]) + 1)


def to_cell(x, z):
    return min(round((z + HH) * 2), ROWS - 1), min(round((x + HW) * 2), COLS - 1)


def to_world(r, c):
    return c / 2 - HW, r / 2 - HH


def snap(x, z):
    r, c = to_cell(x, z)
    if free[r, c]:
        return r, c
    rr, cc = np.nonzero(free)
    k = np.argmin((rr - r) ** 2 + (cc - c) ** 2)
    return int(rr[k]), int(cc[k])


idx = -np.ones(grid.shape, dtype=int)
idx[free] = np.arange(free.sum())
src_i, dst_i, wt = [], [], []
for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
    r0, r1 = max(0, -dr), ROWS - max(0, dr)
    c0, c1 = max(0, -dc), COLS - max(0, dc)
    a = free[r0:r1, c0:c1] & free[r0 + dr:r1 + dr, c0 + dc:c1 + dc]
    if dr and dc:
        a &= free[r0 + dr:r1 + dr, c0:c1] & free[r0:r1, c0 + dc:c1 + dc]
    ra, ca = np.nonzero(a)
    ra += r0
    ca += c0
    src_i.append(idx[ra, ca])
    dst_i.append(idx[ra + dr, ca + dc])
    wt.append(np.full(len(ra), 0.5 * (2 ** 0.5 if dr and dc else 1)))
src_i, dst_i, wt = map(np.concatenate, (src_i, dst_i, wt))
N = int(free.sum())
G = coo_matrix((wt, (src_i, dst_i)), shape=(N, N)).tocsr()
cells = np.argwhere(free)

nodes = [snap(*p) for p in spawns] + [snap(*p) for p in wpos]
NS = len(spawns)
dist, pred = dijkstra(G, directed=False, indices=[idx[r, c] for r, c in nodes], return_predecessors=True)
nid = [idx[r, c] for r, c in nodes]


def los(a, b):
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) * 2 + 1
    rs = np.rint(np.linspace(a[0], b[0], n)).astype(int)
    cs = np.rint(np.linspace(a[1], b[1], n)).astype(int)
    return free[rs, cs].all()


def path(i, j):
    """节点 i → j 的最短路径（世界坐标折线，已做视线简化）"""
    k = nid[j]
    cs = []
    while k >= 0 and k != nid[i]:
        cs.append(tuple(cells[k]))
        k = pred[i, k]
    cs.append(tuple(cells[nid[i]]))
    cs.reverse()
    out, a = [cs[0]], 0
    while a < len(cs) - 1:
        b = len(cs) - 1
        while b > a + 1 and not los(cs[a], cs[b]):
            b -= 1
        out.append(cs[b])
        a = b
    return [to_world(r, c) for r, c in out]


_pass = {}


def passes(i, j):
    """节点 i → j 的路线上顺路穿过（距中心 ≤ 0.7 倍半径）的其他刷新点"""
    if (i, j) not in _pass:
        pts = path(i, j)
        dense = []
        for (ax_, az_), (bx_, bz_) in zip(pts[:-1], pts[1:]):
            n = max(2, int(np.hypot(bx_ - ax_, bz_ - az_) * 2))
            dense += list(zip(np.linspace(ax_, bx_, n), np.linspace(az_, bz_, n)))
        dense = np.array(dense)
        hit = set()
        for k, (cx, cz) in enumerate(wpos):
            if k != j - NS and np.hypot(dense[:, 0] - cx, dense[:, 1] - cz).min() <= 0.7 * wilds[k]["radius"]:
                hit.add(k)
        _pass[(i, j)] = hit
    return _pass[(i, j)]


def avail(w, t):
    """t 秒时该刷新点上累计的野生 NPC 数（开局先刷一批，之后每 interval 秒刷一批，受 maxCount 限制）"""
    once = max(w["onceCount"], 1)
    n = once * (1 + int(t // w["interval"]))
    return min(n, w["maxCount"]) if w["maxCount"] > 0 else n


# 争抢折扣：某刷新点离别的出生点更近时，本出生点到达时能拿到的人数按距离比打折
dmin = np.array([min(dist[o, nid[NS + w]] for o in range(NS)) for w in range(len(wilds))])


def share(s, w):
    ds = dist[s, nid[NS + w]]
    return 1.0 if ds <= 1.15 * dmin[w] else (dmin[w] / ds) ** 2


# ---------- 规划：每个出生点枚举最多 3 段的访问序列，取 HORIZON 秒内期望人数最多者 ----------
def plan(s):
    best = None
    for L in range(1, MAX_LEGS + 1):
        for seq in itertools.permutations(range(len(wilds)), L):
            t, cur, got, legs = 0.0, s, 0, []
            ok = True
            for pos, w in enumerate(seq):
                if passes(cur, NS + w) - set(seq[:pos]) - {w}:
                    ok = False
                    break
                dt = dist[cur, nid[NS + w]] / SPEED
                if t + dt > HORIZON:
                    break
                t += dt
                n = avail(wilds[w], t)
                got += n * share(s, w) * np.exp(-DISCOUNT * t)
                legs.append((w, dt, t, n))

                cur = NS + w
            if not ok or not legs:
                continue
            score = got - 0.1 * t
            if best is None or score > best[0]:
                best = (score, legs, got, t)
    return best


plans = []
for s in range(NS):
    _, legs, got, t = plan(s)
    plans.append((legs, got, t))

# 首段目标被更近的其他出生点抢占？（仅提示：同局只会随机选用其中 10 个）
contest = []
for s, (legs, _, _) in enumerate(plans):
    w = legs[0][0]
    mine = dist[s, nid[NS + w]]
    rivals = [o for o in range(NS) if o != s and dist[o, nid[NS + w]] < mine - 1e-6]
    contest.append(min(rivals, key=lambda o: dist[o, nid[NS + w]]) if rivals else None)

# ---------- 绘图 ----------
COL = ["#e03131", "#1971c2", "#2f9e44", "#f08c00", "#9c36b5", "#0c8599", "#c2255c", "#5c940d",
       "#e8590c", "#3b5bdb", "#099268", "#a61e4d", "#845ef7", "#364fc7", "#d9480f", "#087f5b"]
WCOL = {"normal": "#2f9e44", "wide": "#1098ad", "rich": "#e67700", "hot": "#e03131"}


def wild_class(w):
    if w["maxCount"] >= 20:
        return "hot"
    if w["onceCount"] >= 8:
        return "rich"
    if w["radius"] >= 6:
        return "wide"
    return "normal"


fig = plt.figure(figsize=(18, 13.2), dpi=110, facecolor="#f8f9fa")
ax = fig.add_axes([0.04, 0.05, 0.60, 0.86])
ax.imshow(img, extent=[-HW, HW, HH, -HH], interpolation="nearest", zorder=0)
ax.set_xlim(-HW - 2, HW + 2)
ax.set_ylim(HH + 2, -HH - 2)
ax.set_aspect("equal")
ax.set_xticks(range(-60, 61, 10))
ax.set_yticks(range(-60, 61, 10))
ax.tick_params(labelsize=9, colors="#495057")
ax.grid(color="#adb5bd", lw=0.4, alpha=0.5, zorder=1)
ax.set_xlabel("X（向右为正）", fontsize=11)
ax.set_ylabel("Z（向下为正；游戏画面中屏幕上方 = -Z）", fontsize=11)
ax.add_patch(Rectangle((-HW, -HH), W, H, fill=False, ec="#c92a2a", lw=2.2, zorder=6))

for i, w in enumerate(wilds, 1):
    c = WCOL[wild_class(w)]
    p = w["position"]
    ax.add_patch(Circle((p["x"], p["z"]), w["radius"], fc=c, alpha=0.16, ec=c, lw=1.2, zorder=2))
    ax.text(p["x"], p["z"] + w["radius"] * 0.62, f"W{i}", ha="center", va="center", fontsize=7,
            color=c, fontweight="bold", zorder=5,
            bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.7))

halo = [pe.withStroke(linewidth=5.5, foreground="white")]
halo_t = [pe.withStroke(linewidth=8, foreground="white")]
for s, (legs, got, t) in enumerate(plans):
    col = COL[s]
    cur = s
    for k, (w, dt, tt, n) in enumerate(legs):
        pts = path(cur, NS + w)
        xs, zs = zip(*pts)
        first = k == 0
        ax.plot(xs, zs, color=col, lw=2.2 if first else 1.5, ls="-" if first else (0, (4, 3)),
                alpha=0.95 if first else 0.8, zorder=7, solid_capstyle="round", path_effects=halo)
        (x0, z0), (x1, z1) = pts[-2], pts[-1]
        ax.add_patch(FancyArrowPatch((x0, z0), (x1, z1), arrowstyle="-|>", mutation_scale=15 if first else 11,
                                     color=col, lw=0, zorder=8, shrinkA=0, shrinkB=0,
                                     path_effects=[pe.withStroke(linewidth=1.5, foreground="white")]))
        wx, wz = wpos[w]
        ax.text(wx, wz, str(k + 1), ha="center", va="center", fontsize=8, color="white", fontweight="bold",
                zorder=9, bbox=dict(boxstyle="circle,pad=0.22", fc=col, ec="white", lw=1))
        cur = NS + w
    # 开局朝向箭头：沿首段起点方向
    pts = path(s, NS + legs[0][0])
    (sx, sz) = pts[0]
    acc, tx, tz = 0.0, sx, sz
    for (ax_, az_), (bx_, bz_) in zip(pts[:-1], pts[1:]):
        seg = float(np.hypot(bx_ - ax_, bz_ - az_))
        if acc + seg >= 7.0:
            f = (7.0 - acc) / seg
            tx, tz = ax_ + (bx_ - ax_) * f, az_ + (bz_ - az_) * f
            break
        acc += seg
        tx, tz = bx_, bz_
    ax.add_patch(FancyArrowPatch((sx, sz), (tx, tz), arrowstyle="simple,head_width=1.0,head_length=1.0,tail_width=0.38",
                                 mutation_scale=22, fc=col, ec="white", lw=1.6, zorder=10, shrinkA=0, shrinkB=0))

for i, (x, z) in enumerate(spawns):
    ax.scatter([x], [z], marker="*", s=330, c=COL[i], ec="white", lw=1.3, zorder=11)
    ax.annotate(f"S{i+1}", (x, z), xytext=(8, 8), textcoords="offset points", fontsize=9, color=COL[i],
                fontweight="bold", zorder=12, bbox=dict(boxstyle="round,pad=0.14", fc="white", ec=COL[i], lw=0.8))

sx, sz = -HW + 3, -HH + 5
ax.plot([sx, sx + 10], [sz, sz], color="white", lw=4, zorder=12)
ax.text(sx + 5, sz + 2.4, "10 单位", color="white", ha="center", va="top", fontsize=9, zorder=12)

fig.text(0.04, 0.955, "《人气大战》各出生点开局建议动向", fontsize=22, fontweight="bold", color="#212529")
fig.text(0.04, 0.925,
         f"scene0 · 以领队移速 {SPEED:g} 单位/秒沿栅格最短路估算 · 规划窗口前 {HORIZON:g} 秒，每个出生点最多连续 {MAX_LEGS} 个招募目标",
         fontsize=12, color="#495057")

# ---------- 侧栏 ----------
info = fig.add_axes([0.665, 0.05, 0.32, 0.86])
info.axis("off")
info.set_xlim(0, 1)
info.set_ylim(0, 1)

handles = [
    Line2D([], [], marker=">", ls="", mfc="#495057", mec="white", ms=13),
    Line2D([], [], color="#495057", lw=2.2),
    Line2D([], [], color="#495057", lw=1.5, ls=(0, (4, 3))),
    Line2D([], [], marker="o", ls="", mfc="#495057", mec="white", ms=10),
    Line2D([], [], marker="*", ls="", mfc="#495057", mec="white", ms=15),
] + [Circle((0, 0), 1, fc=WCOL[k], alpha=0.35, ec=WCOL[k]) for k in ("normal", "wide", "rich", "hot")]
labels = [
    "开局朝向箭头（出生后先朝这个方向走）",
    "第 1 目标路线（避开障碍的最短路）",
    "第 2、3 目标路线（虚线）",
    "目标顺序编号（位于刷新点中心）",
    "S1–S16 出生点（颜色 = 各自路线颜色）",
    "普通刷新点（每 5s 刷 4）",
    "大范围刷新点（半径 6）",
    "高产刷新点（每 5s 刷 8）",
    "热点刷新点（每 4s 刷 6，上限 20）",
]
leg = info.legend(handles, labels, loc="upper left", bbox_to_anchor=(0, 1.0), fontsize=10,
                  frameon=True, title="图例", title_fontsize=12.5, labelspacing=0.7, borderpad=0.9,
                  handlelength=2.0)
leg.get_frame().set_facecolor("white")
leg.get_frame().set_edgecolor("#ced4da")

# 路线表
tbl_top, row_h = 0.650, 0.0232
n_rows = NS + 1
info.add_patch(FancyBboxPatch((0.0, tbl_top - row_h * n_rows - 0.008), 0.985, row_h * n_rows + 0.026,
                              boxstyle="round,pad=0.0,rounding_size=0.01", fc="white", ec="#ced4da", zorder=0))
info.text(0.015, tbl_top, "出生点", fontsize=9.6, va="top", fontweight="bold", color="#343a40")
info.text(0.14, tbl_top, "建议路线（W = 刷新点）", fontsize=9.6, va="top", fontweight="bold", color="#343a40")
info.text(0.72, tbl_top, "预计人数 / 用时", fontsize=9.6, va="top", fontweight="bold", color="#343a40")
for s, (legs, got, t) in enumerate(plans):
    y = tbl_top - row_h * (s + 1)
    expect = sum(n * share(s, w) for w, _, _, n in legs)
    route = " -> ".join(f"W{w+1}" for w, *_ in legs)
    flag = f"  (抢:S{contest[s]+1})" if contest[s] is not None else ""
    info.text(0.015, y, f"\u2605 S{s+1}", fontsize=9.6, va="top", fontweight="bold", color=COL[s])
    info.text(0.14, y, route + flag, fontsize=9.6, va="top", color="#343a40")
    info.text(0.72, y, f"~{expect:4.0f} 人 / {t:4.1f}s", fontsize=9.6, va="top", color="#343a40")

notes = (
    "估算方法\n"
    "  · 路程：scene0_c.json 栅格（收缩 1 格防贴墙）上的 8 邻域最短路\n"
    "  · 到达时刷新点上的人数 = min(maxCount, onceCount × (1 + ⌊t / interval⌋))\n"
    "  · 争抢折扣：某刷新点离别的出生点更近（距离比 > 1.15）时，人数 × 距离比⁻²\n"
    "  · 枚举最多 3 个目标的全部顺序，取 30 秒内人数最多者；\n"
    "    越晚到手越不值钱（每秒折 4%），沿途顺路穿过的刷新点必须先作目标\n"
    "  · “预计人数” 为各目标折扣后人数之和，“用时” 为到最后一个目标的行走时间\n"
    "  · (抢:Sx) 首个目标离 Sx 更近；同局只随机选用 16 个出生点中的 10 个\n"
    "  · 未计入敌方 AI 实际行动，也未计入野生 NPC 沿路点游走造成的位置偏差"
)
info.text(0.0, 0.0, notes, fontsize=8.8, va="bottom", ha="left", color="#343a40", linespacing=1.55,
          bbox=dict(boxstyle="round,pad=0.7", fc="white", ec="#ced4da"))

fig.savefig(OUT + ".png", facecolor=fig.get_facecolor())
fig.savefig(OUT + ".svg", facecolor=fig.get_facecolor())
for s, (legs, got, t) in enumerate(plans, 1):
    print(f"S{s}", [(f"W{w+1}", round(float(dt), 1), n) for w, dt, tt, n in legs], round(got, 1), round(t, 1), f"vs S{contest[s-1]+1}" if contest[s-1] is not None else "")
print("speed", SPEED)
