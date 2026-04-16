import math
from collections.abc import Mapping

import matplotlib.pyplot as plt


def _draw_radar_chart(
    scores: Mapping[str, float | None],
    title: str,
    out_path: str,
    figsize: tuple[int, int],
) -> None:
    labels = list(scores.keys())
    values = [scores[label] if scores[label] is not None else 0 for label in labels]

    angles = [index / float(len(labels)) * 2 * math.pi for index in range(len(labels))]
    chart_values = values + values[:1]
    chart_angles = angles + angles[:1]

    figure = plt.figure(figsize=figsize)
    axis = plt.subplot(111, polar=True)

    axis.set_theta_offset(math.pi / 2)
    axis.set_theta_direction(-1)
    axis.set_thetagrids([angle * 180 / math.pi for angle in angles], labels, fontsize=8)
    axis.set_ylim(0, 5)
    axis.plot(chart_angles, chart_values, linewidth=2, marker="o")
    axis.fill(chart_angles, chart_values, alpha=0.25)
    axis.set_title(title, y=1.08)
    axis.grid(True)

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close(figure)


def radar_chart(level_scores: Mapping[str, float | None], out_path: str) -> None:
    _draw_radar_chart(level_scores, "Ebenen-Scores", out_path, figsize=(8, 8))


def block_radar_chart(block_scores: Mapping[str, float | None], out_path: str) -> None:
    _draw_radar_chart(block_scores, "Block-Scores", out_path, figsize=(10, 10))
