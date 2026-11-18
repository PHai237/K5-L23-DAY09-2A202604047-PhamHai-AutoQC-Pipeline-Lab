"""Check 6: compare YOLO annotations with cached larger-model predictions.

This check raises review warnings only; a model prediction is NOT ground truth.
"""
from __future__ import annotations

from ..common import WARN, Issue, iou_xywh, parse_yolo_line
from ..model_cache import get_preds


def run(ds, cfg, preds=None):
    if preds is None:
        preds = get_preds(ds, cfg, "checker")
    rules = cfg["second_opinion"]
    out = []
    for image in ds.image_files():
        stem = image.stem
        if stem not in preds or not ds.label_path(stem).exists():
            continue
        size = ds.image_size(stem)
        if size is None:
            continue

        # Keep original line numbers: valid_boxes() by itself loses blank lines.
        labels = []
        for number, raw in ds.read_label_lines(stem) or []:
            try:
                row = parse_yolo_line(raw)
            except (ValueError, OverflowError):
                continue
            if 0 <= row[0] < len(ds.classes) and row[3] > 0 and row[4] > 0:
                labels.append((number, row))

        predictions = preds[stem]
        trusted = [p for p in predictions if len(p) == 6 and p[1] >= rules["conf"]
                   and p[4] * size[0] * p[5] * size[1] >= rules["min_area_px"]]
        for p in trusted:
            pid, confidence, *p_box = p
            candidates = [(iou_xywh(p_box, lab[1:]), lab[0]) for _, lab in labels
                          if iou_xywh(p_box, lab[1:]) >= rules["iou_missing"]]
            if not candidates:
                out.append(Issue("second_opinion", WARN, "POSSIBLE_MISSING", stem,
                                 "model thấy một vật nhưng nhãn không có box phù hợp",
                                 extra={"conf": confidence}))
                continue
            same = [iou for iou, cls in candidates if cls == pid]
            if same:
                best = max(same)
                if best < rules["iou_loose"]:
                    out.append(Issue("second_opinion", WARN, "POSSIBLE_LOOSE_BOX", stem,
                                     "box nhãn cùng lớp chưa khớp sát dự đoán",
                                     extra={"conf": confidence, "iou": round(best, 6)}))
                continue
            best_other = max(iou for iou, _ in candidates)
            if best_other >= rules["iou_match"]:
                out.append(Issue("second_opinion", WARN, "POSSIBLE_WRONG_CLASS", stem,
                                 "model nghi nhãn đang chọn nhầm lớp",
                                 extra={"conf": confidence, "iou": round(best_other, 6)}))

        # False-positive check deliberately uses a looser confidence threshold
        # and does not filter by size (a tiny valid box can still be supported).
        fp_predictions = [p for p in predictions if len(p) == 6 and p[1] >= rules["fp_conf"]]
        for line_no, label in labels:
            if all(iou_xywh(label[1:], p[2:]) < rules["iou_missing"] for p in fp_predictions):
                out.append(Issue("second_opinion", WARN, "POSSIBLE_FALSE_POS", stem,
                                 "box nhãn không khớp dự đoán nào ở ngưỡng FP",
                                 line=line_no))
    return out
