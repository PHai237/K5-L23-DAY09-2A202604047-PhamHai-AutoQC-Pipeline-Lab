"""Apply only safe deterministic repairs to a working copy of a YOLO dataset.

Destructive actions are restricted to images/labels in ``ds``. All changes
are logged with original line numbers, and dropping a line overrides clipping.
"""
from __future__ import annotations

from collections import defaultdict

import yaml

from ..common import ERROR, parse_yolo_line

DROP_CODES = {"BAD_FORMAT", "BAD_CLASS_ID", "BOX_ZERO", "DUP_BOX"}
REMOVE_CODES = {"DUP_IMAGE_EXACT", "DUP_IMAGE_NEAR", "LEAK_TEST", "CORRUPT_IMAGE", "BAD_SIZE"}


def _clip(line):
    """Return a safe normalized box, or None if clipped completely away."""
    cls, x, y, w, h = parse_yolo_line(line)
    left, right = max(0.0, x - w / 2), min(1.0, x + w / 2)
    top, bottom = max(0.0, y - h / 2), min(1.0, y + h / 2)
    if left >= right or top >= bottom:
        return None
    return f"{cls} {(left + right) / 2:.6f} {(top + bottom) / 2:.6f} {right - left:.6f} {bottom - top:.6f}"


def fix(ds, issues, cfg):
    errors = [i for i in issues if i.severity == ERROR]
    fixes = []

    # Removing rejected images must precede edits to their label files.
    removed = set()
    for issue in errors:
        if issue.code not in REMOVE_CODES or issue.image in removed:
            continue
        stem = issue.image
        image = ds.image_path(stem)
        if image is None:
            continue
        image.unlink()
        label = ds.label_path(stem)
        if label.exists():
            label.unlink()
        ds._size_cache.pop(stem, None)
        removed.add(stem)
        fixes.append(dict(image=stem, line="", action="remove_image",
                          before=image.name, after=f"đã loại: {issue.code}"))

    # Rename the entire mapping once, preserving all unrelated YAML fields.
    if any(i.code == "BAD_CLASS_NAME" for i in errors):
        previous = yaml.safe_load(ds.yaml_path.read_text(encoding="utf-8")) if ds.yaml_path.exists() else {}
        previous = previous or {}
        old_names = previous.get("names", None)
        new_names = {i: name for i, name in enumerate(cfg["classes"])}
        if old_names != new_names:
            previous["names"] = new_names
            ds.yaml_path.write_text(yaml.safe_dump(previous, allow_unicode=True, sort_keys=False), encoding="utf-8")
            fixes.append(dict(image="data.yaml", line="", action="rename_classes",
                              before=str(old_names), after=str(new_names)))

    # Missing labels are human-only: an empty file would falsely mean background.
    for stem in dict.fromkeys(i.image for i in errors if i.code == "MISSING_LABEL_FILE"):
        if stem not in removed and ds.image_path(stem) is not None and not ds.label_path(stem).exists():
            fixes.append(dict(image=stem, line="", action="needs_label",
                              before="(không có file)", after="chuyển người gán"))

    grouped = defaultdict(lambda: defaultdict(set))
    for issue in errors:
        if (issue.image not in removed and issue.line is not None
                and issue.code in DROP_CODES | {"BOX_OUT_OF_IMAGE"}):
            grouped[issue.image][issue.line].add(issue.code)

    for stem in sorted(grouped):
        path = ds.label_path(stem)
        if not path.exists():
            continue
        original = path.read_text(encoding="utf-8", errors="replace").splitlines()
        changed = False
        result = []
        for line_no, line in enumerate(original, 1):
            codes = grouped[stem].get(line_no, set())
            if codes & DROP_CODES:
                fixes.append(dict(image=stem, line=line_no, action="drop_line",
                                  before=line, after="(đã xóa dòng)"))
                changed = True
                continue
            if "BOX_OUT_OF_IMAGE" in codes:
                try:
                    corrected = _clip(line)
                except (ValueError, OverflowError):
                    corrected = None
                if corrected is None:
                    fixes.append(dict(image=stem, line=line_no, action="drop_line",
                                      before=line, after="(box ngoài ảnh hoặc không hợp lệ)"))
                    changed = True
                    continue
                if corrected != line:
                    fixes.append(dict(image=stem, line=line_no, action="clip_box",
                                      before=line, after=corrected))
                    changed = True
                result.append(corrected)
            else:
                result.append(line)
        if changed:
            path.write_text("\n".join(result) + ("\n" if result else ""), encoding="utf-8")
    return fixes
