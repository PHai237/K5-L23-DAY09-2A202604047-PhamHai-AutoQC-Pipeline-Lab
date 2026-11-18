"""Choose the release state from mandatory errors and unresolved image warnings."""
from __future__ import annotations

from ..common import ERROR, WARN


def decide(issues, image_stems, cfg, reviewed=frozenset()):
    stems = set(image_stems)
    seen = set(reviewed)
    n_errors = sum(issue.severity == ERROR for issue in issues)
    warned = {issue.image for issue in issues
              if issue.severity == WARN and issue.image in stems and issue.image not in seen}
    n_images = len(stems)
    ratio = len(warned) / n_images if n_images else 0.0
    hold_at = cfg["gate"]["warn_ratio_hold"]

    if n_errors:
        decision = "Rework"
        reasons = [f"Còn {n_errors} lỗi bắt buộc; không được xuất bộ dữ liệu."]
    elif ratio >= hold_at:
        decision = "Hold"
        reasons = [f"Còn {len(warned)}/{n_images} ảnh cảnh báo chưa được duyệt "
                   f"({ratio:.2%}), đạt/vượt ngưỡng Hold {hold_at:.2%}."]
    else:
        decision = "Release"
        reasons = [f"Không còn lỗi bắt buộc; còn {len(warned)}/{n_images} ảnh cảnh báo "
                   f"chưa duyệt ({ratio:.2%}) dưới ngưỡng {hold_at:.2%}."]

    return {"decision": decision, "n_errors": n_errors,
            "n_warn_images": len(warned), "n_images": n_images,
            "warn_ratio": round(ratio, 4), "reasons": reasons}
