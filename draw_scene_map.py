import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Rectangle
from scipy import ndimage

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src/resource/model/scene0/")
OUT = os.path.join(ROOT, "scene-map")

from matplotlib import font_manager as fm
for _w in ("Regular", "Bold"):
    fm.fontManager.addfont(f"/usr/local/share/fonts/sarasa-mono-sc/SarasaMonoSC-{_w}.ttf")
plt.rcParams["font.family"] = ["Sarasa Mono SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

d = json.load(open(SRC + "scene0.json"))
W, H = int(d["width"]), int(d["height"])
HW, HH = W / 2, H / 2
grid = np.array(json.load(open(SRC + "scene0_c.json"))["mapData"]).reshape(H * 2, W * 2)

# 区分「地图外」与「建筑/障碍块」：与图像边界连通的不可走区域视为地图外
blocked = grid == -1
lab, _ = ndimage.label(blocked)
border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
outside = np.isin(lab, list(border))
img = np.zeros(grid.shape + (3,))
img[grid == 0] = (0.93, 0.95, 0.97)
img[blocked & ~outside] = (0.55, 0.60, 0.68)
img[outside] = (0.20, 0.23, 0.29)

spawns = [(p["x"], p["z"]) for p in d["spawns"]]
points = [(p["x"], p["z"]) for p in d["points"]]
roads = [(p["x"], p["z"]) for p in d["roads"]]
wilds = d["wilds"]
blds = d["buildingInfos"]


def wild_class(w):
    if w["maxCount"] >= 20:
        return "hot"
    if w["onceCount"] >= 8:
        return "rich"
    if w["radius"] >= 6:
        return "wide"
    return "normal"


WCOL = {"normal": "#2f9e44", "wide": "#1098ad", "rich": "#e67700", "hot": "#e03131"}
WNAME = {
    "normal": "普通刷新点",
    "wide": "大范围刷新点",
    "rich": "高产刷新点",
    "hot": "热点刷新点",
}
cnt = {k: 0 for k in WCOL}
for w in wilds:
    cnt[wild_class(w)] += 1

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

# 建筑中心
bx = [b["position"]["x"] for b in blds]
bz = [b["position"]["z"] for b in blds]
ax.scatter(bx, bz, marker="s", s=14, c="#fff3bf", ec="#5c4b00", lw=0.6, zorder=3)

# 野生刷新点
for i, w in enumerate(wilds, 1):
    c = WCOL[wild_class(w)]
    p = w["position"]
    ax.add_patch(Circle((p["x"], p["z"]), w["radius"], fc=c, alpha=0.18, ec=c, lw=1.4, zorder=2))
    ax.text(p["x"], p["z"] - w["radius"] * 0.45, f"W{i}", ha="center", va="center", fontsize=7.5, color=c,
            fontweight="bold", zorder=7,
            bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.75))

# 路点
ax.scatter([r[0] for r in roads], [r[1] for r in roads], s=10, c="#7048e8", zorder=4)

# AI 目标点
ax.scatter([p[0] for p in points], [p[1] for p in points], marker="D", s=75,
           c="#fd7e14", ec="white", lw=1, zorder=8)
for i, (x, z) in enumerate(points, 1):
    ax.annotate(f"P{i}", (x, z), xytext=(7, -12), textcoords="offset points", fontsize=8,
                color="#d9480f", fontweight="bold", zorder=9)

# 出生点
ax.scatter([s[0] for s in spawns], [s[1] for s in spawns], marker="*", s=300,
           c="#1971c2", ec="white", lw=1, zorder=10)
for i, (x, z) in enumerate(spawns, 1):
    ax.annotate(f"S{i}", (x, z), xytext=(6, 6), textcoords="offset points", fontsize=8.5,
                color="#1864ab", fontweight="bold", zorder=11,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.8))

# 比例尺
sx, sz = -HW + 3, -HH + 5
ax.plot([sx, sx + 10], [sz, sz], color="white", lw=4, zorder=12)
ax.text(sx + 5, sz + 2.4, "10 单位", color="white", ha="center", va="top", fontsize=9, zorder=12)

fig.text(0.04, 0.955, "《人气大战》游戏场景平面图（scene0 · 默认地图）", fontsize=22,
         fontweight="bold", color="#212529")
fig.text(0.04, 0.925,
         f"俯视图 · 地图 {W} × {H} 单位（X ∈ [{-HW:.0f}, {HW:.0f}]，Z ∈ [{-HH:.1f}, {HH:.1f}]）"
         f" · 碰撞栅格 {W*2} × {H*2}（每格 0.5 单位）",
         fontsize=12, color="#495057")

# 侧栏
walk = int((grid == 0).sum())
info = fig.add_axes([0.665, 0.05, 0.32, 0.86])
info.axis("off")
info.set_xlim(0, 1)
info.set_ylim(0, 1)

handles = [
    Rectangle((0, 0), 1, 1, fc=(0.93, 0.95, 0.97), ec="#868e96"),
    Rectangle((0, 0), 1, 1, fc=(0.55, 0.60, 0.68), ec="#868e96"),
    Rectangle((0, 0), 1, 1, fc=(0.20, 0.23, 0.29), ec="#868e96"),
    Line2D([], [], marker="s", ls="", mfc="#fff3bf", mec="#5c4b00", ms=6),
    Line2D([], [], marker="*", ls="", mfc="#1971c2", mec="white", ms=15),
    Line2D([], [], marker="D", ls="", mfc="#fd7e14", mec="white", ms=8),
    Line2D([], [], marker="o", ls="", mfc="#7048e8", mec="#7048e8", ms=4),
] + [Circle((0, 0), 1, fc=WCOL[k], alpha=0.35, ec=WCOL[k]) for k in WCOL]
labels = [
    f"可通行地面（0），共 {walk} 格",
    "建筑 / 障碍块（-1，不可通行）",
    "外围障碍区（-1，与地图边界相连）",
    f"建筑中心（{len(blds)} 个；后方有单位时建筑变半透明）",
    f"S1–S{len(spawns)}  出生 / 复活点（{len(spawns)} 个，随机选取）",
    f"P1–P{len(points)}  AI 随机目标点（{len(points)} 个）",
    f"路点（{len(roads)} 个，移动撞墙时取最近路点作临时目标）",
] + [f"{WNAME[k]}（{cnt[k]} 个）" for k in WCOL]
leg = info.legend(handles, labels, loc="upper left", bbox_to_anchor=(0, 1.0), fontsize=10.5,
                  frameon=True, title="图例", title_fontsize=12.5, labelspacing=0.85,
                  borderpad=1.0, handlelength=1.8)
leg.get_frame().set_facecolor("white")
leg.get_frame().set_edgecolor("#ced4da")

wl = {k: [w for w in wilds if wild_class(w) == k] for k in WCOL}


def rng(k, f):
    v = sorted({w[f] for w in wl[k]})
    return "/".join(str(x) for x in v)


notes = (
    "刷新点参数（圈半径 = 随机散布半径）\n"
    f"  普通：半径 {rng('normal','radius')}，每 {rng('normal','interval')}s 刷 {rng('normal','onceCount')} 个，上限 {rng('normal','maxCount')}\n"
    f"  大范围：半径 {rng('wide','radius')}，每 {rng('wide','interval')}s 刷 {rng('wide','onceCount')} 个，上限 {rng('wide','maxCount')}\n"
    f"  高产：半径 {rng('rich','radius')}，每 {rng('rich','interval')}s 刷 {rng('rich','onceCount')} 个，上限 {rng('rich','maxCount')}\n"
    f"  热点：半径 {rng('hot','radius')}，每 {rng('hot','interval')}s 刷 {rng('hot','onceCount')} 个，上限 {rng('hot','maxCount')}\n"
    "  全图中立士兵总数上限 2000\n"
    "\n关键数值（configs.json · globalSet）\n"
    "  单局时长 120 秒　玩家上限 10 人\n"
    "  领队移速 4　中立士兵移速 1.8\n"
    "\n坐标说明\n"
    "  世界 (x, z) → 栅格列 = round((x+61)×2)\n"
    "                 栅格行 = round((z+67.5)×2)\n"
    "  数据来源：scene0.json（点位）\n"
    "                scene0_c.json（碰撞栅格）"
)
info.text(0.0, 0.60, notes, fontsize=10.2, va="top", ha="left", color="#343a40",
          linespacing=1.55,
          bbox=dict(boxstyle="round,pad=0.7", fc="white", ec="#ced4da"))

fig.savefig(OUT + ".png", facecolor=fig.get_facecolor())
fig.savefig(OUT + ".svg", facecolor=fig.get_facecolor())
print("walk cells", walk, "outside cells", int(outside.sum()), "block cells", int((blocked & ~outside).sum()))
print(cnt)
