import numpy as np
from vedo import Cylinder, Plane, Line, Spline, CSpline, show


RADIUS = 2.0
CYLINDER_RESOLUTION = 100
CURVE_RESOLUTION = 2000


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


intersection = cylinder.intersect_with(plane).join(reset=True).clean()

points = np.asarray(intersection.coordinates, dtype=float)

if len(points) < 3:
    raise RuntimeError("The intersection did not produce a valid closed contour.")

# Avoid supplying a duplicated closing point to the spline constructors.
if np.linalg.norm(points[0] - points[-1]) < 1e-12:
    points = points[:-1]


line = Line(
    points,
    closed=True,
).c("green").lw(5)

spline = Spline(
    points,
    closed=True,
    degree=3,
    smooth=0.0,
    res=CURVE_RESOLUTION,
).c("blue").lw(5)

cardinal_spline = CSpline(
    points,
    closed=True,
    res=CURVE_RESOLUTION,
).c("red").lw(5)


analytical_circumference = 2.0 * np.pi * RADIUS

results = {
    "Closed polyline": line.length(),
    "Closed B-spline": spline.length(),
    "Closed Cardinal spline": cardinal_spline.length(),
}


print(f"Analytical circumference: {analytical_circumference:.8f}")
print(f"Cylinder resolution: {CYLINDER_RESOLUTION} sides")
print(f"Number of intersection points: {len(points)}")
print()

for name, measured_length in results.items():
    error = measured_length - analytical_circumference
    error_percent = 100.0 * error / analytical_circumference

    print(name)
    print(f"  Measured length: {measured_length:.8f}")
    print(f"  Signed error:    {error:+.8f}")
    print(f"  Relative error:  {error_percent:+.6f} %")
    print()


closest_method = min(
    results,
    key=lambda name: abs(results[name] - analytical_circumference),
)

print(
    "Closest method for this analytical circle:",
    closest_method,
)


show(
    cylinder,
    plane,
    line,
    spline,
    cardinal_spline,
    intersection.labels("id"),
    axes=1,
).close()