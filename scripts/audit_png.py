"""Read-only audit of production UI PNG files; requires Pillow."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


def audit_file(path, tight=False, require_clear=False):
    record = {"file": str(path.resolve()), "issues": []}
    try:
        raw = path.read_bytes()
        record["sha256"] = hashlib.sha256(raw).hexdigest()
        with Image.open(path) as image:
            image.load()
            record.update(format=image.format, mode=image.mode, size_px=list(image.size))
            if image.format != "PNG":
                record["issues"].append("not_png")
            if image.mode != "RGBA":
                record["issues"].append("not_rgba")
            alpha = image.convert("RGBA").getchannel("A")
            low, high = alpha.getextrema()
            bounds = alpha.getbbox()
            record.update(
                alpha_extrema=[low, high],
                alpha_bounds=list(bounds) if bounds else None,
                has_clear_pixels=low == 0,
                has_nonopaque_pixels=low < 255,
            )
            if bounds is None:
                record["issues"].append("fully_transparent")
            else:
                width, height = image.size
                margins = [bounds[0], bounds[1], width - bounds[2], height - bounds[3]]
                record["transparent_margins_ltrb_px"] = margins
                if require_clear and low != 0:
                    record["issues"].append("no_fully_transparent_pixel")
                if tight and any(margins):
                    record["issues"].append("extra_transparent_margin")
    except (OSError, ValueError, Image.DecompressionBombError) as exc:
        record["issues"].append("read_error")
        record["error"] = str(exc)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--tight", action="store_true", help="Require no completely transparent outer margin.")
    parser.add_argument("--require-clear", action="store_true", help="Require at least one alpha=0 pixel; omit for solid fills.")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    files = []
    bad_inputs = []
    for item in args.inputs:
        if item.is_dir():
            found = sorted((item.rglob("*") if args.recursive else item.iterdir()), key=str)
            candidates = [p for p in found if p.is_file() and p.suffix.lower() == ".png"]
            if not candidates:
                bad_inputs.append(str(item))
            files.extend(candidates)
        elif item.is_file():
            files.append(item)
        else:
            bad_inputs.append(str(item))
    files = list(dict.fromkeys(p.resolve() for p in files))
    if args.out and args.out.resolve() in files:
        parser.error("Report path must not overwrite an input asset.")
    records = [audit_file(p, args.tight, args.require_clear) for p in files]
    report = {
        "count": len(records),
        "failed": sum(bool(r["issues"]) for r in records),
        "tight_required": args.tight,
        "clear_pixels_required": args.require_clear,
        "invalid_or_empty_inputs": bad_inputs,
        "assets": records,
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "assets"}, ensure_ascii=False))
    for record in records:
        if record["issues"]:
            print(json.dumps({"file": record["file"], "issues": record["issues"]}, ensure_ascii=False))
    return 2 if bad_inputs or not records else 1 if report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
