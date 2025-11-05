"""차트 생성 유틸리티 (Matplotlib).

간단한 추세 차트를 PNG로 생성하여 블로그 포스트에 삽입할 수 있도록 한다.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib

# Windows/서버 환경에서 GUI 백엔드 사용 방지
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def generate_trend_chart(
    x_labels: Sequence[str],
    y_values: Sequence[float],
    *,
    title: str = "Trend",
    xlabel: str = "",
    ylabel: str = "Value",
    output_path: Path | str = "chart.png",
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    ax.plot(range(len(y_values)), y_values, marker="o", color="#0056b3", linewidth=2)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.set_xticks(range(len(x_labels)))
    ax.set_xticklabels(list(x_labels), rotation=30, ha="right")
    fig.tight_layout()

    fig.savefig(output_path)
    plt.close(fig)
    return output_path


