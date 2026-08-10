from __future__ import annotations

import argparse
from pathlib import Path

from bosai_studio.judge_demo_surface import render_demo_html


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the Phase 10 judge-facing BOSAI demo surface.")
    parser.add_argument("--out", default="build/judge-demo/index.html", help="Output HTML path.")
    args = parser.parse_args()

    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_demo_html(), encoding="utf-8")
    print(f"PHASE_10_DEMO_RENDERED={output_path}")
    print("PHASE_10_PUBLIC_URL_CLAIMED=false")
    print("PHASE_10_SECRET_VALUES_PRINTED=false")


if __name__ == "__main__":
    main()
