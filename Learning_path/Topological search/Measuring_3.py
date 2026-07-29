import numpy as np
from scipy.interpolate import splprep, splev
from scipy.integrate import quad
from vedo import Cylinder, Plane, Line, Spline, show


RADIUS = 2.0
CYLINDER_RESOLUTION = 100
SPLINE_DEGREE = 3
SPLINE_RESOLUTION = 2000


def prepare_closed_curve_points(points, tolerance=1e-12):
    """
    Removes consecutive duplicate points and a duplicated closing point.
    """
    pts = np.asarray(points, dtype=float)

    cleaned = [pts[0]]

    for point in pts[1:]:
        if np.linalg.norm(point - cleaned[-1]) > tolerance:
            cleaned.append(point)

    pts = np.asarray(cleaned, dtype=float)

    if len(pts) > 1 and np.linalg.norm(pts[-1] - pts[0]) <= tolerance:
        pts = pts[:-1]

    return pts


def fit_periodic_bspline(points, degree=3, smooth=0.0):
    """
    Fits a periodic parametric B-spline.
    """
    pts = np.asarray(points, dtype=float)

    if len(pts) <= degree:
        raise ValueError(
            f"At least {degree + 1} points are required."
        )

    closed_points = np.vstack([pts, pts[0]])

    tck, _ = splprep(
        closed_points.T,
        s=smooth,
        k=degree,
        per=1,
    )

    return tck


def integrated_bspline_length(tck):
    """
    Calculates B-spline arc length by integrating its speed.
    """
    def speed(u):
        derivative = np.asarray(
            splev(u, tck, der=1),
            dtype=float,
        )

        return float(np.linalg.norm(derivative))

    knots = np.unique(np.asarray(tck[0], dtype=float))
    internal_knots = knots[(knots > 0.0) & (knots < 1.0)]

    length, error = quad(
        speed,
        0.0,
        1.0,
        points=internal_knots,
        epsabs=1e-11,
        epsrel=1e-11,
        limit=500,
    )

    return float(length), float(error)


def sampled_bspline_length(tck, resolution=2000):
    """
    Calculates B-spline length from sampled points.
    """
    parameters = np.linspace(
        0.0,
        1.0,
        resolution,
        endpoint=True,
    )

    sampled_points = np.asarray(
        splev(parameters, tck),
        dtype=float,
    ).T

    segment_vectors = np.diff(sampled_points, axis=0)
    segment_lengths = np.linalg.norm(segment_vectors, axis=1)

    return float(np.sum(segment_lengths)), sampled_points


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

intersection = cylinder.intersect_with(plane).join(reset=True)

points = prepare_closed_curve_points(
    intersection.coordinates
)

tck = fit_periodic_bspline(
    points,
    degree=SPLINE_DEGREE,
    smooth=0.0,
)

integrated_length, integration_error = integrated_bspline_length(
    tck
)

sampled_length, sampled_points = sampled_bspline_length(
    tck,
    resolution=SPLINE_RESOLUTION,
)

analytical_circumference = 2.0 * np.pi * RADIUS

print(f"Degree: {SPLINE_DEGREE}")
print(f"Input points: {len(points)}")
print()

print(f"Integrated spline length: {integrated_length:.10f}")
print(f"Sampled spline length:    {sampled_length:.10f}")
print(
    f"Sampling difference:      "
    f"{sampled_length - integrated_length:+.10f}"
)
print(f"Integration error:        {integration_error:.3e}")
print()

print(
    f"Analytical circumference: "
    f"{analytical_circumference:.10f}"
)

print(
    f"Spline-circle difference: "
    f"{integrated_length - analytical_circumference:+.10f}"
)

spline_actor = Line(
    sampled_points,
    closed=False,
).c("blue").lw(5)

vedo_spline = Spline(
    points,
    closed=True,
    degree=SPLINE_DEGREE,
    smooth=0.0,
    res=SPLINE_RESOLUTION,
).c("red").lw(2)

print(f"Vedo spline length:       {vedo_spline.length():.10f}")

show(
    cylinder,
    plane,
    spline_actor,
    vedo_spline,
    axes=1,
).close()