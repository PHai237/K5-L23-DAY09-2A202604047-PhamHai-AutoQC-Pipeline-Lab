"""Check 2: validate YOLO rows and geometry without modifying label files.

Each finding keeps the original one-based line number; malformed rows do not
prevent later rows from being checked. All thresholds come from the config.
"""
from __future__ import annotations

from ..common import ERROR, WARN, Issue, iou_xywh, parse_yolo_line


def run(ds, cfg):
    rules = cfg["label_format"]
    issues = []
    for file in ds.label_files():
        stem = file.stem
        size = ds.image_size(stem)
        prior = []  # only rows with a valid class and positive dimensions
        for line_no, raw in ds.read_label_lines(stem) or []:
            try:
                cls, x, y, w, h = parse_yolo_line(raw)
            except (ValueError, OverflowError):
                issues.append(Issue("label_format", ERROR, "BAD_FORMAT", stem,
                                    "dòng nhãn không gồm đúng 5 số hợp lệ", line=line_no))
                continue

            if not 0 <= cls < len(ds.classes):
                issues.append(Issue("label_format", ERROR, "BAD_CLASS_ID", stem,
                                    f"ID lớp {cls} ngoài khoảng 0..{len(ds.classes) - 1}", line=line_no))
                continue
            if w <= 0 or h <= 0:
                issues.append(Issue("label_format", ERROR, "BOX_ZERO", stem,
                                    f"chiều rộng/cao không dương: {w}, {h}", line=line_no))
                continue

            left, right = x - w / 2, x + w / 2
            top, bottom = y - h / 2, y + h / 2
            overflow = max(0.0, -left, right - 1.0, -top, bottom - 1.0)
            if overflow > rules["overflow_tol"]:
                issues.append(Issue("label_format", ERROR, "BOX_OUT_OF_IMAGE", stem,
                                    f"box vượt mép ảnh {overflow:.6f}", line=line_no,
                                    extra={"overflow": round(overflow, 8)}))

            if any(old_cls == cls and iou_xywh((x, y, w, h), old_box) > rules["dup_box_iou"]
                   for old_cls, old_box in prior):
                issues.append(Issue("label_format", ERROR, "DUP_BOX", stem,
                                    "box lặp với một dòng trước cùng lớp", line=line_no))
            prior.append((cls, (x, y, w, h)))

            if size is not None and min(w * size[0], h * size[1]) < rules["min_box_px"]:
                issues.append(Issue("label_format", WARN, "BOX_TINY", stem,
                                    "cạnh ngắn của box nhỏ hơn ngưỡng pixel", line=line_no))
            if w * h > rules["max_box_frac"]:
                issues.append(Issue("label_format", WARN, "BOX_HUGE", stem,
                                    "box chiếm diện tích quá lớn so với ảnh", line=line_no))
    return issues
