import math
import matplotlib.pyplot as plt

def _draw_radar_chart(scores, title, out_path, figsize=(8, 8)):
    labels = list(scores.keys())
    values = [scores[k] if scores[k] is not None else 0 for k in labels]

    angles = [n / float(len(labels)) * 2 * math.pi for n in range(len(labels))]
    values += values[:1]
    angles += angles[:1]

    fig = plt.figure(figsize=figsize)
    ax = plt.subplot(111, polar=True)

    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids([a * 180 / math.pi for a in angles[:-1]], labels, fontsize=8)
    ax.set_ylim(0, 5)
    ax.plot(angles, values, linewidth=2, marker="o")
    ax.fill(angles, values, alpha=0.25)
    ax.set_title(title, y=1.08)
    ax.grid(True)

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close(fig)


def radar_chart(level_scores, out_path):
    _draw_radar_chart(level_scores, "Ebenen-Scores", out_path, figsize=(8, 8))


def block_radar_chart(block_scores, out_path):
    _draw_radar_chart(block_scores, "Block-Scores", out_path, figsize=(10, 10))
