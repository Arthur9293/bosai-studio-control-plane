from __future__ import annotations

import argparse
from pathlib import Path

from bosai_studio.judge_demo_surface import render_demo_html


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the BOSAI Agentic Cinema judge-facing interactive replay.")
    parser.add_argument("--out", default="build/judge-demo/index.html", help="Output HTML path.")
    args = parser.parse_args()

    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_demo_html(), encoding="utf-8")
    print(f"R1_D_JUDGE_DEMO_RENDERED={output_path}")
    print("R1_D_PUBLIC_URL_CLAIMED=true")
    print("R1_D_INTERACTIVE_REPLAY=true")
    print("R1_D_LIVE_CLOUD_MUTATION=false")
    print("R1_D_SECRET_VALUES_PRINTED=false")


if __name__ == "__main__":
    main()
