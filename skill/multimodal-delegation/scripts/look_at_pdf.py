#!/usr/bin/env python3
"""Look_at PDF — 自动 PDF 多模态分析封装。

流程：PDF → pdf_to_images.py 渲染每页 PNG → 逐页 look_at → 汇总输出。

依赖：pymupdf（PDF 渲染）、opencode CLI（look_at 工具调用）

用法：
    python look_at_pdf.py <input.pdf> --goal "提取文档标题和结构" [--outdir DIR] [--dpi 144]

输出：
    汇总各页 look_at 结果到 stdout。若 opencode CLI 不可用，回退为仅渲染 PNG + 提示手动调 look_at。
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", help="Path to the input PDF file")
    parser.add_argument("--goal", required=True, help="Analysis goal passed to look_at for each page")
    parser.add_argument("--outdir", default=None, help="Output directory for PNG pages (default: temp dir)")
    parser.add_argument("--dpi", type=int, default=144, help="Render DPI (default 144)")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}", file=sys.stderr)
        return 1

    # Locate the sibling pdf_to_images.py
    script_dir = Path(__file__).resolve().parent
    pdf_to_images = script_dir / "pdf_to_images.py"
    if not pdf_to_images.exists():
        print(f"Error: pdf_to_images.py not found at {pdf_to_images}", file=sys.stderr)
        return 1

    # Determine output dir
    import tempfile
    outdir = Path(args.outdir) if args.outdir else Path(tempfile.mkdtemp(prefix="look_at_pdf_"))
    outdir.mkdir(parents=True, exist_ok=True)

    # Step 1: render PDF to PNG pages
    print(f"[1/2] Rendering {pdf_path.name} to PNG at {args.dpi} DPI...", file=sys.stderr)
    render_cmd = [sys.executable, str(pdf_to_images), str(pdf_path), "--outdir", str(outdir), "--dpi", str(args.dpi)]
    result = subprocess.run(render_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: pdf_to_images failed: {result.stderr}", file=sys.stderr)
        return 1
    png_paths = [line for line in result.stdout.strip().splitlines() if line.endswith(".png")]
    if not png_paths:
        print("Error: no PNG pages rendered", file=sys.stderr)
        return 1
    print(f"[1/2] Rendered {len(png_paths)} page(s).", file=sys.stderr)

    # Step 2: call look_at for each page via opencode CLI
    print(f"[2/2] Calling look_at on {len(png_paths)} page(s)...", file=sys.stderr)
    opencode_bin = shutil.which("opencode")
    if not opencode_bin:
        print("[2/2] opencode CLI not found — pages rendered, call look_at manually:", file=sys.stderr)
        for p in png_paths:
            print(p)
        print("\nManual command per page:", file=sys.stderr)
        print(f'  opencode run "look_at(file_path=\"{png_paths[0]}\", goal=\"{args.goal}\")"', file=sys.stderr)
        return 0

    summaries = []
    for i, png_path in enumerate(png_paths, 1):
        prompt = f'Use the look_at tool: look_at(file_path="{png_path}", goal="{args.goal}"). Return only the look_at result.'
        print(f"  page {i}/{len(png_paths)}: {png_path}", file=sys.stderr)
        oc_result = subprocess.run(
            [opencode_bin, "run", prompt],
            capture_output=True, text=True, timeout=180,
        )
        if oc_result.returncode != 0:
            print(f"  [warn] opencode run failed (exit {oc_result.returncode}): {oc_result.stderr[:200]}", file=sys.stderr)
            summaries.append(f"## Page {i} ({Path(png_path).name})\n[look_at failed: exit {oc_result.returncode}]")
        else:
            summaries.append(f"## Page {i} ({Path(png_path).name})\n{oc_result.stdout.strip()}")

    # Final aggregated output
    print("\n" + "=" * 60)
    print(f"# PDF Analysis: {pdf_path.name} ({len(png_paths)} pages)")
    print(f"# Goal: {args.goal}")
    print("=" * 60)
    for s in summaries:
        print(s)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
