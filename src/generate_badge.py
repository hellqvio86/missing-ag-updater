import json
import os
import subprocess
import sys


def main():
    # Generate coverage.json using the coverage tool via the active python environment
    subprocess.run([sys.executable, "-m", "coverage", "json"], check=True)

    # Load percentage
    with open("coverage.json") as f:
        data = json.load(f)

    percent = round(data["totals"]["percent_covered"])

    # Clean up coverage.json
    if os.path.exists("coverage.json"):
        os.remove("coverage.json")

    # Determine color based on coverage percentage
    if percent >= 95:
        color = "#4c1"  # brightgreen
    elif percent >= 90:
        color = "#97ca00"  # green
    elif percent >= 75:
        color = "#dfb317"  # yellow
    elif percent >= 60:
        color = "#fe7d37"  # orange
    else:
        color = "#e05d44"  # red

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="90" height="20">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <mask id="a">
    <rect width="90" height="20" rx="3" fill="#fff"/>
  </mask>
  <g mask="url(#a)">
    <rect width="61" height="20" fill="#555"/>
    <rect x="61" width="29" height="20" fill="{color}"/>
    <rect width="90" height="20" fill="url(#b)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="31.5" y="15" fill="#010101" fill-opacity=".3">coverage</text>
    <text x="31.5" y="14">coverage</text>
    <text x="75.5" y="15" fill="#010101" fill-opacity=".3">{percent}%</text>
    <text x="75.5" y="14">{percent}%</text>
  </g>
</svg>"""

    with open("coverage.svg", "w") as f:
        f.write(svg)

    print(f"Generated coverage.svg with {percent}% ({color})")


if __name__ == "__main__":
    main()
