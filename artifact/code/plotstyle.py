import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
def setup():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                         "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "lines.linewidth": 1.6,
                         "legend.frameon": False, "savefig.bbox": "tight", "savefig.dpi": 300, "axes.titlesize": 8,
                         "pdf.fonttype": 42, "ps.fonttype": 42})  # TrueType, no Type 3 fonts
MODEL_ORDER = ["qwen2.5-0.5b", "qwen2.5-1.5b", "smollm2-1.7b", "qwen2.5-3b", "phi3.5-mini", "qwen3.5-4b", "qwen2.5-7b", "mistral-7b"]
PRETTY = {"qwen2.5-0.5b": "Qwen2.5-0.5B", "qwen2.5-1.5b": "Qwen2.5-1.5B", "qwen2.5-3b": "Qwen2.5-3B", "qwen2.5-7b": "Qwen2.5-7B",
          "smollm2-1.7b": "SmolLM2-1.7B", "phi3.5-mini": "Phi-3.5-mini", "mistral-7b": "Mistral-7B-v0.3", "qwen3.5-4b": "Qwen3.5-4B"}

# ---- warm amber/brown style of Figure 1 (make_comic.py), used by every data figure since 2026-11-20 ----
# Two categorical hues (BROWN, AMBER; validated colour-blind safe, deutan dE 29.8) plus the ink neutral for
# reference / "no intervention" marks. Amber is below 3:1 contrast on white, so amber marks are always direct-labelled.
CM = 1 / 2.54
COL_W, TEXT_W = 7.7 * CM, 16.0 * CM          # ACL column / text width in inches
W_INK, W_MUTED, W_GRID = "#3a2414", "#7a6352", "#ece6dd"
W_BROWN, W_AMBER, W_SAND, W_BAND = "#87431a", "#e3a03a", "#ebe5dc", "#f6e3c2"
def setup_warm():
    """Figure-1 style: Trebuchet MS, >= 7 pt at print size, hairline solid grid, TrueType fonts, exact figure size."""
    plt.rcParams.update({"font.family": "Trebuchet MS", "font.size": 7, "axes.titlesize": 7, "axes.labelsize": 7,
                         "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
                         "text.color": W_INK, "axes.edgecolor": W_MUTED, "axes.labelcolor": W_INK, "axes.linewidth": 0.6,
                         "xtick.color": W_MUTED, "ytick.color": W_MUTED, "xtick.labelcolor": W_INK, "ytick.labelcolor": W_INK,
                         "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
                         "xtick.major.pad": 2, "ytick.major.pad": 2, "axes.labelpad": 2,
                         "axes.spines.top": False, "axes.spines.right": False, "axes.axisbelow": True,
                         "axes.grid": True, "grid.color": W_GRID, "grid.linewidth": 0.5, "grid.linestyle": "-",
                         "lines.linewidth": 1.2, "legend.frameon": False, "axes.unicode_minus": False,
                         "savefig.bbox": None, "savefig.dpi": 300, "pdf.fonttype": 42, "ps.fonttype": 42})
