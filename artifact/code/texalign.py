"""Digit alignment for LaTeX tables without siunitx (2026-11-20).
pad_cols(L, cols) left-pads the unsigned numbers of the given 0-based columns of every data row in L with
\\hphantom{0} so that, in a centred (c) column, numbers of different length align on the units digit while the block
stays centred under its header. Only presentation changes: the printed digits are untouched."""
import re
NUM = re.compile(r"^\d+(\.\d+)?$")
def _is_row(l):
    return l.rstrip().endswith("\\\\") and " & " in l and "\\multicolumn" not in l and not l.lstrip().startswith(("\\toprule", "\\midrule"))
def pad_cols(L, cols):
    rows = [i for i, l in enumerate(L) if _is_row(l)]
    split = {i: L[i].rstrip()[:-2].rstrip().split(" & ") for i in rows}
    for c in cols:
        w = max((len(split[i][c].strip().split(".")[0]) for i in rows if c < len(split[i]) and NUM.match(split[i][c].strip())), default=0)
        for i in rows:
            if c < len(split[i]) and NUM.match(split[i][c].strip()):
                v = split[i][c].strip(); k = w - len(v.split(".")[0])
                split[i][c] = ("\\hphantom{" + "0" * k + "}" if k > 0 else "") + v
    for i in rows:
        tail = L[i].rstrip()[len(L[i].rstrip()[:-2].rstrip()):]
        L[i] = " & ".join(split[i]) + " " + tail.strip()
    return L
