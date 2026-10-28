import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.text import Text

from topside import style


def test_text_prints_at_least_min_size():
    style.apply_publication_style()
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot([0, 1], [0, 1])
    ax.text(0.5, 0.5, "small note", fontsize=6)
    ax.set_xlabel("x label")
    style.enforce_min_text_size(fig)
    scale = style.PRINT_WIDTH_IN / style._saved_width_in(fig)
    sizes = [t.get_fontsize() * scale for t in fig.findobj(Text) if t.get_text().strip()]
    plt.close(fig)
    assert min(sizes) >= style.MIN_PRINT_PT - 0.1


def test_text_is_black():
    style.apply_publication_style()
    assert plt.rcParams["text.color"] == "black"
    assert plt.rcParams["xtick.color"] == "black"
    assert style.PALETTE["ink"] == "#000000"
