"""Types that represent what's inside a reMarkable .rm annotation file.

A .rm file is a list of Strokes. Each Stroke is a list of Points drawn
in one pen color. Points use the tablet's own coordinate system (roughly
0-20967 on the long axis), so they need a CalibrationTransform to land
on the right spot in the PDF.

    tablet coords          CalibrationTransform          PDF points
    (x=5200, y=3100)  ──────────────────────────▶  (x=575+1650, y=934-980)
                         pdf_x = 0.318 * rm_x + 575
                         pdf_y = -0.316 * rm_y + 934
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import NamedTuple


class PenColor(IntEnum):
    """Pen color index from the .rm binary spec.

    These aren't sequential -- the gaps (2-5) are reserved for colors
    the reMarkable 2 doesn't expose.
    """

    BLACK = 0
    GRAY = 1
    BLUE = 6
    RED = 7


class Point(NamedTuple):
    """One sampled point in a stroke.

    x/y are tablet coordinates (0-20967), width is pen pressure
    (light touch ~0.1, full press ~1.5).
    """

    x: float
    y: float
    width: float


class Stroke(NamedTuple):
    """One continuous pen stroke in drawing order, all the same color."""

    points: list[Point]
    color: PenColor


@dataclass(frozen=True, slots=True)
class CalibrationTransform:
    """Maps tablet coordinates to PDF points with a per-axis affine transform.

    The coefficients come from a 9-point crosshair calibration (run
    ``remarkable-ai calibrate``, circle each crosshair, fetch it back).
    scale_y is negative because the tablet's y-axis points down but
    PDF's y-axis points up.

        reMarkable (top-left origin)     PDF (bottom-left origin)
        ┌──────────────┐                 ┌──────────────┐
        │ (0,0)        │                 │        (w,h) │
        │         ●    │    to_pdf()     │         ●    │
        │   (5200,3100)│  ──────────▶    │  (2225, 955) │
        │              │                 │              │
        │       (20967,│                 │ (0,0)        │
        └──────────────┘                 └──────────────┘
    """

    scale_x: float
    offset_x: float
    scale_y: float
    offset_y: float

    def to_pdf(self, rm_x: float, rm_y: float) -> tuple[float, float]:
        """Map a tablet coordinate pair to PDF points."""
        return (
            self.scale_x * rm_x + self.offset_x,
            self.scale_y * rm_y + self.offset_y,
        )
