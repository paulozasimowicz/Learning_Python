from vedo import *
import numpy as np
from scipy.interpolate import splprep, splev
from scipy.integrate import quad


def bspline_arc_length(
    points,
    closed=True,
    degree=2,
    smooth=0.0,
    epsabs=1e-10,
    epsrel=1e-10,
):
    """
    Fits a parametric B-spline and calculates its arc length by integrating
    the magnitude of its first derivative.
    """
    pts = np.asarray(points, dtype=float)

    if pts.ndim != 2 or pts.shape[1] != 3:
        raise ValueError("points must have shape (N, 3).")

    if len(pts) <= degree:
        raise ValueError(
            f"At least {degree + 1} points are required for degree {degree}."
        )

    # Remove duplicated closing point before creating a periodic spline.
    if closed and np.allclose(pts[0], pts[-1]):
        pts = pts[:-1]

    fit_points = pts.copy()

    if closed:
        fit_points = np.vstack([fit_points, fit_points[0]])

    # Match the smoothing conversion used internally by vedo.Spline.
    coordinate_range = np.ptp(fit_points, axis=0)
    max_dimension = float(np.max(coordinate_range))
    absolute_smoothing = smooth * max_dimension / 2.0

    tck, u = splprep(
        fit_points.T,
        task=0,
        s=absolute_smoothing,
        k=degree,
        per=int(closed),
    )

    u_start = float(u[0])
    u_end = float(u[-1])

    def speed(parameter):
        derivative = np.asarray(
            splev(parameter, tck, der=1),
            dtype=float,
        )

        return float(np.linalg.norm(derivative))

    # Include the internal spline knots as quadrature breakpoints.
    knots = np.unique(np.asarray(tck[0], dtype=float))

    internal_knots = knots[
        (knots > u_start) &
        (knots < u_end)
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

    return float(length), float(estimated_error), tck

radius = 2.0

c1 = Cylinder(
    pos=(0, 0, 0),
    r=radius,
    height=3,
    axis=(1, 0, 0),
    res=24,
    alpha=0.1,
).triangulate()

c2 = Plane(
    pos=(0, 0, 0),
    normal=(1, 0, 0),
    s=(6, 6),
).triangulate()

intersection = c1.intersect_with(c2).join(reset=True).clean()
points = np.asarray(intersection.coordinates, dtype=float)


bspline_length, integration_error, tck = bspline_arc_length(
    points,
    closed=True,
    degree=2,   # Same as the vedo.Spline default
    smooth=0.0,
)

true_circle_length = 2.0 * np.pi * radius

difference = bspline_length - true_circle_length
difference_percent = 100.0 * difference / true_circle_length

print(f"Integrated B-spline length: {bspline_length:.10f}")
print(f"Estimated integration error: {integration_error:.3e}")
print(f"Analytical circle length:    {true_circle_length:.10f}")
print(f"Difference:                   {difference:+.10f}")
print(f"Difference percentage:        {difference_percent:+.8f} %")


# Vedo spline only for visualization.
spline_actor = Spline(
    points,
    closed=True,
    degree=2,
    smooth=0.0,
    res=1000,
).c("blue").lw(5)

show(
    c1,
    c2,
    spline_actor,
    intersection.labels("id"),
    axes=1,
).close()