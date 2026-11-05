from collections import Counter
from datetime import date, timedelta
from pathlib import Path
import subprocess
import sys


MONTH_NAMES = ("Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
               "Jul", "Ago", "Set", "Out", "Nov", "Dez")
SERIES = (("Frontend", "#ff9e6e"), ("Backend", "#a9c5e0"))
CHART = Path(__file__).resolve().parents[1] / "profile/assets/commits.svg"
BASELINE = 256
PLOT_HEIGHT = 160


def recent_months(today):
    month = today.replace(day=1)
    months = []
    for _ in range(4):
        months.append(month)
        month = (month - timedelta(days=1)).replace(day=1)
    return months[::-1]


def commit_counts(repository, months):
    log = subprocess.check_output(
        ["git", "-C", repository, "log", "refs/remotes/origin/main", "--format=%cs"],
        text=True,
    )
    counts = Counter(day[:7] for day in log.splitlines())
    return [counts[month.isoformat()[:7]] for month in months]


def render_chart(months, counts):
    # Five horizontal gridlines with at least ten commits between them.
    step = max(10, (max(max(series) for series in counts) + 19) // 20 * 5)
    scale = PLOT_HEIGHT / (4 * step)
    labels = [f"{MONTH_NAMES[month.month - 1]}/{month.year % 100:02}" for month in months]
    summary = ". ".join(
        f"{label}: {frontend} no frontend e {backend} no backend"
        for label, frontend, backend in zip(labels, *counts)
    )
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 896 318" width="896" height="318" role="img" aria-labelledby="title desc">',
        '  <title id="title">Commits por mês</title>',
        f'  <desc id="desc">{summary}.</desc>',
        '  <rect width="896" height="318" rx="18" fill="#101822"/>',
        '  <g font-family="system-ui, -apple-system, Segoe UI, sans-serif">',
        '    <text x="35" y="43" fill="#fff5e9" font-size="25" font-weight="700">Commits por mês</text>',
        '    <text x="35" y="68" fill="#b7c5d4" font-size="16">Últimos 4 meses · histórico da branch main</text>',
    ]
    for index, (name, color) in enumerate(SERIES):
        x = 597 + index * 132
        svg.append(f'    <rect x="{x}" y="32" width="14" height="14" rx="3" fill="{color}"/>')
        svg.append(f'    <text x="{x + 22}" y="45" fill="#fff5e9" font-size="17">{name}</text>')

    for index in range(5):
        y = BASELINE - index * 40
        svg.append(f'    <path d="M75 {y}h785" stroke="#435265"/>')
        svg.append(f'    <text x="61" y="{y + 5}" fill="#b7c5d4" font-size="15" text-anchor="end">{index * step}</text>')

    for index, label in enumerate(labels):
        center = 173 + index * 191
        svg.append(f'    <text x="{center}" y="288" fill="#d3dce6" font-size="17" text-anchor="middle">{label}</text>')
        for offset, (_, color), series in zip((-19, 19), SERIES, counts):
            x = center + offset
            count = series[index]
            height = count * scale
            top = BASELINE - height
            if count:
                svg.append(f'    <rect x="{x - 15}" y="{top:g}" width="30" height="{height:g}" rx="3" fill="{color}"/>')
            svg.append(f'    <text x="{x}" y="{top - 6:g}" fill="#fff5e9" font-size="17" font-weight="650" text-anchor="middle">{count}</text>')

    return "\n".join([*svg, "  </g>", "</svg>", ""])


if __name__ == "__main__":
    frontend, backend = sys.argv[1:]
    months = recent_months(date.today())
    counts = [commit_counts(repo, months) for repo in (frontend, backend)]
    CHART.write_bytes(render_chart(months, counts).encode("utf-8"))
    for (name, _), series in zip(SERIES, counts):
        print(f"{name}: {series}")
