import numpy as np

from scipy.interpolate import splprep, splev
from scipy.integrate import quad

from vedo import (
    Cylinder,
    Plane,
    Line,
    Spline,
    CSpline,
    show,
)


RADIUS = 2.0
CYLINDER_RESOLUTION = 100
CURVE_RESOLUTION = 5000

BSPLINE_DEGREE = 3
BSPLINE_SMOOTH = 1


def clean_closed_curve_points(points, tolerance=1e-12):
    """
    Removes consecutive duplicates and a duplicated closing point.
    """
    pts = np.asarray(points, dtype=float)

    if pts.ndim != 2 or pts.shape[1] != 3:
        raise ValueError("points must have shape (N, 3).")

    if len(pts) < 3:
        raise ValueError("At least three points are required.")

    cleaned = [pts[0]]

    for point in pts[1:]:
        if np.linalg.norm(point - cleaned[-1]) > tolerance:
            cleaned.append(point)

    pts = np.asarray(cleaned, dtype=float)

    if (
        len(pts) >= 2
        and np.linalg.norm(pts[-1] - pts[0]) <= tolerance
    ):
        pts = pts[:-1]

    if len(pts) < 3:
        raise ValueError("Too few distinct contour points remain.")

    return pts


def closed_polyline_length(points):
    """
    Calculates the exact length of a closed polyline.
    """
    pts = np.asarray(points, dtype=float)

    next_points = np.roll(pts, -1, axis=0)
    segment_vectors = next_points - pts
    segment_lengths = np.linalg.norm(segment_vectors, axis=1)

    return float(np.sum(segment_lengths))


def fit_periodic_bspline(
    points,
    degree=3,
    smooth=0.0,
):
    """
    Fits a periodic parametric B-spline to closed contour points.
    """
    pts = np.asarray(points, dtype=float)

    if len(pts) <= degree:
        raise ValueError(
            f"At least {degree + 1} points are required "
            f"for degree {degree}."
        )

    fit_points = np.vstack([pts, pts[0]])

    coordinate_range = np.ptp(fit_points, axis=0)
    max_dimension = float(np.max(coordinate_range))

    absolute_smoothing = smooth * max_dimension / 2.0

    tck, u = splprep(
        fit_points.T,
        task=0,
        s=absolute_smoothing,
        k=degree,
        per=1,
    )

    return tck, float(u[0]), float(u[-1])


def integrated_bspline_length(
    tck,
    u_start,
    u_end,
    epsabs=1e-10,
    epsrel=1e-10,
):
    """
    Calculates B-spline arc length by integrating its speed.
    """
    def speed(parameter):
        derivative = np.asarray(
            splev(parameter, tck, der=1),
            dtype=float,
        )

        return float(np.linalg.norm(derivative))

    knots = np.unique(np.asarray(tck[0], dtype=float))

    internal_knots = knots[
        (knots > u_start)
        & (knots < u_end)
    ]

    length, estimated_error = quad(
        speed,
        u_start,
        u_end,
        points=internal_knots,
        epsabs=epsabs,
        epsrel=epsrel,
        limit=max(200, len(internal_knots) + 20),
    )

    return float(length), float(estimated_error)


def sampled_bspline_length(
    tck,
    u_start,
    u_end,
    resolution=5000,
):
    """
    Samples a fitted B-spline and sums its chord lengths.
    """
    parameters = np.linspace(
        u_start,
        u_end,
        resolution + 1,
        endpoint=True,
    )

    sampled_points = np.asarray(
        splev(parameters, tck),
        dtype=float,
    ).T

    segment_vectors = np.diff(sampled_points, axis=0)
    segment_lengths = np.linalg.norm(segment_vectors, axis=1)

    length = float(np.sum(segment_lengths))

    return length, sampled_points


def print_result(name, value, reference):
    """
    Prints length and error relative to a reference.
    """
    difference = value - reference
    percentage = 100.0 * difference / reference

    print(
        f"{name:<36}"
        f"{value:>15.10f}"
        f"{difference:>+16.10f}"
        f"{percentage:>+14.6f} %"
    )


cylinder = Cylinder(
    pos=(0, 0, 0),
    r=RADIUS,
    height=3,
    axis=(1, 0, 0),
    res=CYLINDER_RESOLUTION,
    alpha=0.1,
).triangulate()

plane = Plane(
    pos=(0, 0, 0),
    normal=(1, 0, 0),
    s=(6, 6),
).triangulate()

intersection = (
    cylinder
    .intersect_with(plane)
    .join(reset=True)
    .clean()
)

points = clean_closed_curve_points(
    intersection.coordinates
)

if len(points) < 3:
    raise RuntimeError(
        "The intersection did not produce a valid closed contour."
    )


analytical_circumference = 2.0 * np.pi * RADIUS

theoretical_polygon_perimeter = (
    2.0
    * CYLINDER_RESOLUTION
    * RADIUS
    * np.sin(np.pi / CYLINDER_RESOLUTION)
)


manual_polyline_length = closed_polyline_length(points)

vedo_line = Line(
    points,
    closed=True,
).c("green").lw(5)

vedo_line_length = vedo_line.length()


tck, u_start, u_end = fit_periodic_bspline(
    points,
    degree=BSPLINE_DEGREE,
    smooth=BSPLINE_SMOOTH,
)

integrated_length, integration_error = integrated_bspline_length(
    tck,
    u_start,
    u_end,
)

sampled_length, scipy_bspline_points = sampled_bspline_length(
    tck,
    u_start,
    u_end,
    resolution=CURVE_RESOLUTION,
)


scipy_bspline_actor = Line(
    scipy_bspline_points,
    closed=False,
).c("magenta").lw(3)


vedo_bspline = Spline(
    points,
    closed=True,
    degree=BSPLINE_DEGREE,
    smooth=BSPLINE_SMOOTH,
    res=CURVE_RESOLUTION,
).c("blue").lw(5)

vedo_bspline_length = vedo_bspline.length()


vedo_cardinal = CSpline(
    points,
    closed=True,
    res=CURVE_RESOLUTION,
).c("red").lw(5)

vedo_cardinal_length = vedo_cardinal.length()


results = {
    "Theoretical mesh polygon": theoretical_polygon_perimeter,
    "Manual closed polyline": manual_polyline_length,
    "Vedo Line.length()": vedo_line_length,
    "SciPy B-spline integrated": integrated_length,
    "Same SciPy B-spline sampled": sampled_length,
    "Vedo B-spline length()": vedo_bspline_length,
    "Vedo Cardinal spline": vedo_cardinal_length,
}


print()
print("Configuration")
print(f"  Radius:                    {RADIUS}")
print(f"  Cylinder resolution:       {CYLINDER_RESOLUTION}")
print(f"  Intersection points:       {len(points)}")
print(f"  B-spline degree:           {BSPLINE_DEGREE}")
print(f"  B-spline smoothing:        {BSPLINE_SMOOTH}")
print(f"  Curve sampling resolution: {CURVE_RESOLUTION}")

print()
print(f"Analytical circle circumference: {analytical_circumference:.10f}")
print()
print(
    f"{'Method':<36}"
    f"{'Length':>15}"
    f"{'Difference':>16}"
    f"{'Relative error':>16}"
)
print("-" * 83)

for name, value in results.items():
    print_result(
        name,
        value,
        analytical_circumference,
    )


print()
print("Consistency checks")

polyline_difference = (
    vedo_line_length
    - manual_polyline_length
)

polygon_difference = (
    manual_polyline_length
    - theoretical_polygon_perimeter
)

sampling_difference = (
    sampled_length
    - integrated_length
)

vedo_scipy_sampled_difference = (
    vedo_bspline_length
    - sampled_length
)

vedo_integrated_difference = (
    vedo_bspline_length
    - integrated_length
)

print(
    "Vedo line - manual polyline:        "
    f"{polyline_difference:+.12e}"
)

print(
    "Manual polyline - polygon formula:  "
    f"{polygon_difference:+.12e}"
)

print(
    "Sampled SciPy - integrated SciPy:   "
    f"{sampling_difference:+.12e}"
)

print(
    "Vedo B-spline - sampled SciPy:      "
    f"{vedo_scipy_sampled_difference:+.12e}"
)

print(
    "Vedo B-spline - integrated SciPy:   "
    f"{vedo_integrated_difference:+.12e}"
)

print(
    "Estimated integration error:        "
    f"{integration_error:.12e}"
)


closest_method = min(
    results,
    key=lambda name: abs(
        results[name] - analytical_circumference
    ),
)

print()
print(
    "Closest method to analytical circle:",
    closest_method,
)


show(
    cylinder,
    plane,
    vedo_line,
    vedo_bspline,
    scipy_bspline_actor,
    vedo_cardinal,
    intersection.labels("id"),
    axes=1,
).close()