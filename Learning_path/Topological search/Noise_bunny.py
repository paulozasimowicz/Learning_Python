import numpy as np
import matplotlib.pyplot as plt

from scipy.interpolate import splprep, splev
from scipy.integrate import quad

from vedo import (
    Mesh,
    Line,
    Plane,
    Plotter,
    Text2D,
    dataurl,
)


NOISE_LEVELS_PERCENT = [
    0.00,
    0.05,
    0.10,
    0.25,
    0.50,
    1.00,
]

N_REPEATS = 10
RANDOM_SEED = 42

CUT_FRACTION = 0.45

RESAMPLED_POINTS = 300
BSPLINE_DEGREE = 3

SMOOTHING_FACTOR = 1.0
DISPLAY_SPLINE_RESOLUTION = 2000


def clean_closed_curve_points(points, tolerance=1e-12):
    """Removes consecutive duplicates and a duplicated closing point."""
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

    return pts


def closed_polyline_length(points):
    """Calculates the length of a closed polyline."""
    pts = np.asarray(points, dtype=float)

    if len(pts) < 2:
        return 0.0

    next_points = np.roll(pts, -1, axis=0)
    segment_vectors = next_points - pts

    return float(
        np.sum(
            np.linalg.norm(segment_vectors, axis=1)
        )
    )


def resample_closed_curve(points, n_samples=300):
    """Resamples a closed curve uniformly along arc length."""
    pts = np.asarray(points, dtype=float)

    if pts.ndim != 2 or len(pts) < 3:
        raise ValueError("A closed curve with at least three points is required.")

    closed = np.vstack([pts, pts[0]])

    segment_vectors = np.diff(closed, axis=0)
    segment_lengths = np.linalg.norm(
        segment_vectors,
        axis=1,
    )

    cumulative_length = np.concatenate([
        [0.0],
        np.cumsum(segment_lengths),
    ])

    total_length = cumulative_length[-1]

    if total_length < 1e-15:
        raise ValueError("Curve length is effectively zero.")

    target_lengths = np.linspace(
        0.0,
        total_length,
        n_samples + 1,
    )[:-1]

    resampled = []
    segment_index = 0

    for target in target_lengths:
        while (
            segment_index < len(segment_lengths) - 1
            and cumulative_length[segment_index + 1] < target
        ):
            segment_index += 1

        start_length = cumulative_length[segment_index]
        end_length = cumulative_length[segment_index + 1]

        interval = end_length - start_length

        if interval < 1e-15:
            point = closed[segment_index].copy()
        else:
            t = (target - start_length) / interval

            point = (
                (1.0 - t) * closed[segment_index]
                + t * closed[segment_index + 1]
            )

        resampled.append(point)

    return np.asarray(resampled, dtype=float)


def fit_periodic_bspline(
    points_2d,
    degree=3,
    smoothing=0.0,
):
    """Fits a periodic B-spline to a closed two-dimensional contour."""
    pts = np.asarray(points_2d, dtype=float)

    if pts.ndim != 2 or pts.shape[1] != 2:
        raise ValueError("points_2d must have shape (N, 2).")

    if len(pts) <= degree:
        raise ValueError(
            f"At least {degree + 1} points are required."
        )

    fit_points = np.vstack([pts, pts[0]])

    tck, parameters = splprep(
        fit_points.T,
        k=degree,
        s=smoothing,
        per=1,
    )

    return (
        tck,
        float(parameters[0]),
        float(parameters[-1]),
    )


def integrated_bspline_length(
    tck,
    u_start,
    u_end,
    epsabs=1e-10,
    epsrel=1e-10,
):
    """Calculates B-spline length by integrating its speed."""
    def speed(parameter):
        derivative = np.asarray(
            splev(parameter, tck, der=1),
            dtype=float,
        )

        return float(np.linalg.norm(derivative))

    knots = np.unique(
        np.asarray(tck[0], dtype=float)
    )

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
        limit=max(
            200,
            len(internal_knots) + 20,
        ),
    )

    return float(length), float(estimated_error)


def sample_bspline(
    tck,
    u_start,
    u_end,
    resolution=2000,
):
    """Samples points from a fitted B-spline."""
    parameters = np.linspace(
        u_start,
        u_end,
        resolution + 1,
    )

    sampled = np.asarray(
        splev(parameters, tck),
        dtype=float,
    ).T

    return sampled

def extract_closed_section(
    mesh,
    cut_y,
    duplicate_tolerance=1e-10,
    max_gap_factor=8.0,
):
    """
    Extracts and orders a horizontal closed section without traversing VTK cells.
    """
    section = mesh.intersect_with_plane(
        origin=(0.0, cut_y, 0.0),
        normal=(0.0, 1.0, 0.0),
    )

    if section is None or section.npoints < 3:
        raise RuntimeError(
            f"No valid section was found at y={cut_y:.8f}."
        )

    raw_points = np.asarray(
        section.coordinates,
        dtype=float,
    )

    if raw_points.ndim != 2 or raw_points.shape[1] != 3:
        raise RuntimeError(
            "The extracted section does not contain valid 3D points."
        )

    # Remove non-finite coordinates.
    raw_points = raw_points[
        np.all(np.isfinite(raw_points), axis=1)
    ]

    if len(raw_points) < 3:
        raise RuntimeError(
            "Too few finite points remain in the section."
        )

    # Remove duplicate points using rounded coordinates.
    scale = max(
        np.ptp(raw_points[:, 0]),
        np.ptp(raw_points[:, 2]),
        1.0,
    )

    tolerance = duplicate_tolerance * scale

    rounded = np.round(
        raw_points / tolerance
    ).astype(np.int64)

    _, unique_indices = np.unique(
        rounded,
        axis=0,
        return_index=True,
    )

    points = raw_points[
        np.sort(unique_indices)
    ]

    if len(points) < 3:
        raise RuntimeError(
            "Too few unique intersection points remain."
        )

    # The plane is horizontal, so order in the XZ plane.
    center_x = np.mean(points[:, 0])
    center_z = np.mean(points[:, 2])

    angles = np.arctan2(
        points[:, 2] - center_z,
        points[:, 0] - center_x,
    )

    order = np.argsort(angles)
    points = points[order]

    # Check whether all points plausibly belong to one contour.
    closed_points = np.vstack([
        points,
        points[0],
    ])

    segment_lengths = np.linalg.norm(
        np.diff(closed_points, axis=0),
        axis=1,
    )

    positive_segments = segment_lengths[
        segment_lengths > tolerance
    ]

    if len(positive_segments) == 0:
        raise RuntimeError(
            "The section has zero effective length."
        )

    median_segment = float(
        np.median(positive_segments)
    )

    maximum_segment = float(
        np.max(positive_segments)
    )

    gap_ratio = maximum_segment / max(
        median_segment,
        tolerance,
    )

    if gap_ratio > max_gap_factor:
        raise RuntimeError(
            "The cutting plane appears to intersect multiple disconnected "
            f"regions. Maximum/median segment ratio = {gap_ratio:.2f}. "
            "Change CUT_FRACTION to cut only through the bunny torso."
        )

    return points, section


def add_normal_noise(
    reference_mesh,
    reference_points,
    reference_normals,
    standard_noise,
    sigma,
):
    """Adds scaled Gaussian noise along the reference vertex normals."""
    noisy_mesh = reference_mesh.clone()

    displacement = (
        sigma
        * standard_noise[:, None]
        * reference_normals
    )

    noisy_mesh.points = (
        reference_points
        + displacement
    )

    return noisy_mesh


bunny = (
    Mesh(dataurl + "bunny.obj")
    .clean()
)

bunny.compute_normals(
    points=True,
    cells=False,
)

reference_points = np.asarray(
    bunny.points,
    dtype=float,
).copy()

reference_normals = np.asarray(
    bunny.point_normals,
    dtype=float,
).copy()

normal_lengths = np.linalg.norm(
    reference_normals,
    axis=1,
    keepdims=True,
)

reference_normals /= np.maximum(
    normal_lengths,
    1e-15,
)


bounds = bunny.bounds()

x_min, x_max = bounds[0], bounds[1]
y_min, y_max = bounds[2], bounds[3]
z_min, z_max = bounds[4], bounds[5]

bunny_height = y_max - y_min

cut_y = (
    y_min
    + CUT_FRACTION * bunny_height
)

print("Bunny information")
print(f"  Vertices:       {bunny.npoints}")
print(f"  Cells:          {bunny.ncells}")
print(f"  Bunny height:   {bunny_height:.8f}")
print(f"  Cut height:     {cut_y:.8f}")
print(f"  Cut fraction:   {CUT_FRACTION:.2f}")
print()


records = []
visualization_data = {}

rng = np.random.default_rng(RANDOM_SEED)


for repeat in range(N_REPEATS):
    standard_noise = rng.normal(
        loc=0.0,
        scale=1.0,
        size=bunny.npoints,
    )

    for noise_percent in NOISE_LEVELS_PERCENT:
        sigma = (
            noise_percent
            / 100.0
            * bunny_height
        )

        noisy_bunny = add_normal_noise(
            reference_mesh=bunny,
            reference_points=reference_points,
            reference_normals=reference_normals,
            standard_noise=standard_noise,
            sigma=sigma,
        )

        loop_points_3d, section_actor = extract_closed_section(
            noisy_bunny,
            cut_y=cut_y,
        )

        loop_points_2d = loop_points_3d[:, [0, 2]]

        uniform_points_2d = resample_closed_curve(
            loop_points_2d,
            n_samples=RESAMPLED_POINTS,
        )

        raw_polyline_length = closed_polyline_length(
            loop_points_2d
        )

        interpolating_tck, u0, u1 = fit_periodic_bspline(
            uniform_points_2d,
            degree=BSPLINE_DEGREE,
            smoothing=0.0,
        )

        interpolating_length, interpolating_error = (
            integrated_bspline_length(
                interpolating_tck,
                u0,
                u1,
            )
        )

        smoothing_value = (
            RESAMPLED_POINTS
            * (
                SMOOTHING_FACTOR
                * sigma
            ) ** 2
        )

        smoothing_tck, su0, su1 = fit_periodic_bspline(
            uniform_points_2d,
            degree=BSPLINE_DEGREE,
            smoothing=smoothing_value,
        )

        smoothing_length, smoothing_error = (
            integrated_bspline_length(
                smoothing_tck,
                su0,
                su1,
            )
        )

        records.append({
            "repeat": repeat,
            "noise_percent": noise_percent,
            "sigma": sigma,
            "raw": raw_polyline_length,
            "interpolating": interpolating_length,
            "smoothing": smoothing_length,
            "smoothing_value": smoothing_value,
        })

        if repeat == 0:
            visualization_data[noise_percent] = {
                "mesh": noisy_bunny,
                "loop": loop_points_3d,
                "smoothing_tck": smoothing_tck,
                "u_start": su0,
                "u_end": su1,
            }


def values_for(noise_percent, measurement):
    return np.asarray([
        record[measurement]
        for record in records
        if record["noise_percent"] == noise_percent
    ])


summary = []

for noise_percent in NOISE_LEVELS_PERCENT:
    raw_values = values_for(
        noise_percent,
        "raw",
    )

    interpolating_values = values_for(
        noise_percent,
        "interpolating",
    )

    smoothing_values = values_for(
        noise_percent,
        "smoothing",
    )

    summary.append({
        "noise_percent": noise_percent,
        "sigma": (
            noise_percent
            / 100.0
            * bunny_height
        ),
        "raw_mean": float(np.mean(raw_values)),
        "raw_std": float(np.std(raw_values, ddof=1)),
        "interpolating_mean": float(
            np.mean(interpolating_values)
        ),
        "interpolating_std": float(
            np.std(interpolating_values, ddof=1)
        ),
        "smoothing_mean": float(
            np.mean(smoothing_values)
        ),
        "smoothing_std": float(
            np.std(smoothing_values, ddof=1)
        ),
    })


reference_raw = summary[0]["raw_mean"]
reference_interpolating = summary[0]["interpolating_mean"]
reference_smoothing = summary[0]["smoothing_mean"]


print("Perimeter sensitivity to added normal noise")
print()
print(
    f"{'Noise':>8}"
    f"{'Sigma':>13}"
    f"{'Raw mean':>14}"
    f"{'Raw SD':>12}"
    f"{'Raw Δ%':>11}"
    f"{'Interp. mean':>15}"
    f"{'Interp. Δ%':>13}"
    f"{'Smooth mean':>15}"
    f"{'Smooth Δ%':>13}"
)

print("-" * 114)

for item in summary:
    raw_delta_percent = (
        100.0
        * (
            item["raw_mean"]
            - reference_raw
        )
        / reference_raw
    )

    interpolating_delta_percent = (
        100.0
        * (
            item["interpolating_mean"]
            - reference_interpolating
        )
        / reference_interpolating
    )

    smoothing_delta_percent = (
        100.0
        * (
            item["smoothing_mean"]
            - reference_smoothing
        )
        / reference_smoothing
    )

    print(
        f"{item['noise_percent']:>7.2f}%"
        f"{item['sigma']:>13.8f}"
        f"{item['raw_mean']:>14.8f}"
        f"{item['raw_std']:>12.8f}"
        f"{raw_delta_percent:>+10.4f}%"
        f"{item['interpolating_mean']:>15.8f}"
        f"{interpolating_delta_percent:>+12.4f}%"
        f"{item['smoothing_mean']:>15.8f}"
        f"{smoothing_delta_percent:>+12.4f}%"
    )


noise_axis = np.asarray([
    item["noise_percent"]
    for item in summary
])

raw_means = np.asarray([
    item["raw_mean"]
    for item in summary
])

raw_stds = np.asarray([
    item["raw_std"]
    for item in summary
])

interpolating_means = np.asarray([
    item["interpolating_mean"]
    for item in summary
])

interpolating_stds = np.asarray([
    item["interpolating_std"]
    for item in summary
])

smoothing_means = np.asarray([
    item["smoothing_mean"]
    for item in summary
])

smoothing_stds = np.asarray([
    item["smoothing_std"]
    for item in summary
])


plt.figure(figsize=(10, 6))

plt.errorbar(
    noise_axis,
    raw_means,
    yerr=raw_stds,
    marker="o",
    capsize=4,
    label="Raw closed polyline",
)

plt.errorbar(
    noise_axis,
    interpolating_means,
    yerr=interpolating_stds,
    marker="o",
    capsize=4,
    label="Interpolating cubic B-spline",
)

plt.errorbar(
    noise_axis,
    smoothing_means,
    yerr=smoothing_stds,
    marker="o",
    capsize=4,
    label="Smoothing cubic B-spline",
)

plt.axhline(
    reference_smoothing,
    linestyle="--",
    label="Noise-free reference",
)

plt.xlabel("Added normal noise,  [% of bunny height]")
plt.ylabel("Section perimeter [model units]")
plt.title("Stanford Bunny section perimeter versus noise")
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()


minimum_noise = NOISE_LEVELS_PERCENT[0]
maximum_noise = NOISE_LEVELS_PERCENT[-1]

clean_data = visualization_data[minimum_noise]
noisy_data = visualization_data[maximum_noise]

clean_loop_actor = Line(
    clean_data["loop"],
    closed=True,
).c("green").lw(5)

noisy_loop_actor = Line(
    noisy_data["loop"],
    closed=True,
).c("red").lw(4)

smoothed_2d = sample_bspline(
    noisy_data["smoothing_tck"],
    noisy_data["u_start"],
    noisy_data["u_end"],
    resolution=DISPLAY_SPLINE_RESOLUTION,
)

smoothed_3d = np.column_stack([
    smoothed_2d[:, 0],
    np.full(len(smoothed_2d), cut_y),
    smoothed_2d[:, 1],
])

smoothed_loop_actor = Line(
    smoothed_3d,
    closed=True,
).c("blue").lw(5)


plane_width = 1.1 * (x_max - x_min)
plane_depth = 1.1 * (z_max - z_min)

cut_plane = Plane(
    pos=(0.5 * (x_min + x_max), cut_y, 0.5 * (z_min + z_max)),
    normal=(0, 1, 0),
    s=(plane_width, plane_depth),
).c("gray").alpha(0.15)


plotter = Plotter(
    shape=(1, 2),
    size=(1800, 900),
    title="Stanford Bunny Noise and Perimeter Test",
)

plotter.at(0).show(
    clean_data["mesh"].clone().alpha(0.35),
    cut_plane.clone(),
    clean_loop_actor,
    Text2D(
        "Noise-free bunny\nGreen: raw section",
        pos="top-left",
    ),
    axes=1,
    resetcam=True,
)

plotter.at(1).show(
    noisy_data["mesh"].clone().alpha(0.35),
    cut_plane.clone(),
    noisy_loop_actor,
    smoothed_loop_actor,
    Text2D(
        f"Noise  = {maximum_noise:.2f}% of height\n"
        "Red: raw section\n"
        "Blue: smoothing B-spline",
        pos="top-left",
    ),
    axes=1,
    resetcam=True,
)

plotter.interactive().close()