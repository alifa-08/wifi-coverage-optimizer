import math
from typing import List, Tuple, Dict, Any

def ccw(A: Tuple[float, float], B: Tuple[float, float], C: Tuple[float, float]) -> float:
    """Return cross product (B - A) x (C - A). Positive = CCW, Negative = CW, 0 = Collinear."""
    return (B[0] - A[0]) * (C[1] - A[1]) - (B[1] - A[1]) * (C[0] - A[0])

def segments_intersect(p1: Tuple[float, float], p2: Tuple[float, float],
                       q1: Tuple[float, float], q2: Tuple[float, float]) -> bool:
    """Check if line segment p1-p2 intersects line segment q1-q2."""
    ccw1 = ccw(p1, p2, q1)
    ccw2 = ccw(p1, p2, q2)
    ccw3 = ccw(q1, q2, p1)
    ccw4 = ccw(q1, q2, p2)

    return ((ccw1 * ccw2 < 0) and (ccw3 * ccw4 < 0))

def point_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Euclidean distance in 2D."""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def calculate_polygon_area(points: List[List[float]]) -> float:
    """Calculate 2D polygon area using Shoelace formula."""
    if len(points) < 3:
        return 0.0
    area = 0.0
    n = len(points)
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    return abs(area) / 2.0

def convex_hull_2d(points: List[Tuple[float, float]]) -> List[List[float]]:
    """Compute 2D convex hull of a set of points using Monotone Chain algorithm."""
    unique_pts = sorted(list(set(points)))
    if len(unique_pts) <= 2:
        return [[p[0], p[1]] for p in unique_pts]

    # Lower hull
    lower: List[Tuple[float, float]] = []
    for p in unique_pts:
        while len(lower) >= 2 and ccw(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    # Upper hull
    upper: List[Tuple[float, float]] = []
    for p in reversed(unique_pts):
        while len(upper) >= 2 and ccw(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    hull = lower[:-1] + upper[:-1]
    return [[p[0], p[1]] for p in hull]

def compute_bounding_box(points: List[Tuple[float, float]]) -> Dict[str, float]:
    """Compute min/max bounding box for points."""
    if not points:
        return {"min_x": 0.0, "min_y": 0.0, "max_x": 0.0, "max_y": 0.0}
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return {
        "min_x": round(min(xs), 2),
        "min_y": round(min(ys), 2),
        "max_x": round(max(xs), 2),
        "max_y": round(max(ys), 2)
    }
