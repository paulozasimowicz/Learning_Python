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

INTEGRATION_ABSOLUTE_TOLERANCE = 1e-8
INTEGRATION_RELATIVE_TOLERANCE = 1e-8


def closed_polyline_length(points):
    """Calculates the length of a closed polyline."""
    pts = np.asarray(points, dtype=float)

    if pts.ndim != 2 or len(pts) < 2:
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
        raise ValueError(
            "A closed curve with at least three points is required."
        )

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
            interpolation = (target - start_length) / interval
            point = (
                (1.0 - interpolation) * closed[segment_index]
                + interpolation * closed[segment_index + 1]
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
    epsabs=1e-8,
    epsrel=1e-8,
):
    """Calculates B-spline arc length over separate knot spans."""
    def speed(parameter):
        derivative = np.asarray(
            splev(parameter, tck, der=1),
            dtype=float,
        )

        speed_value = float(np.linalg.norm(derivative))

        if not np.isfinite(speed_value):
            raise ValueError(
                "The B-spline derivative produced a non-finite speed."
            )

        return speed_value

    knots = np.unique(
        np.asarray(tck[0], dtype=float)
    )

    interval_boundaries = knots[
        (knots >= u_start)
        & (knots <= u_end)
    ]

    interval_boundaries = np.unique(
        np.concatenate([
            [u_start],
            interval_boundaries,
            [u_end],
        ])
    )

    intervals = [
        (float(start), float(end))
        for start, end in zip(
            interval_boundaries[:-1],
            interval_boundaries[1:],
        )
        if end > start
    ]

    if not intervals:
        raise RuntimeError(
            "The B-spline contains no valid integration intervals."
        )

    interval_epsabs = epsabs / len(intervals)

    total_length = 0.0
    total_error = 0.0

    for interval_start, interval_end in intervals:
        interval_length, interval_error = quad(
            speed,
            interval_start,
            interval_end,
            epsabs=interval_epsabs,
            epsrel=epsrel,
            limit=50,
        )

        total_length += interval_length
        total_error += interval_error

    return float(total_length), float(total_error)


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

    return np.asarray(
        splev(parameters, tck),
        dtype=float,
    ).T


def extract_closed_section(
    mesh,
    cut_y,
    duplicate_tolerance=1e-10,
    max_gap_factor=8.0,
):
    """Extracts and orders a horizontal closed section."""
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

    raw_points = raw_points[
        np.all(np.isfinite(raw_points), axis=1)
    ]

    if len(raw_points) < 3:
        raise RuntimeError(
            "Too few finite points remain in the section."
        )

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

    center_x = np.mean(points[:, 0])
    center_z = np.mean(points[:, 2])

    angles = np.arctan2(
        points[:, 2] - center_z,
        points[:, 0] - center_x,
    )

    points = points[np.argsort(angles)]

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


def measure_section(mesh, cut_y, sigma):
    """Measures one section using a closed line and a smoothing B-spline."""
    loop_points_3d, section_actor = extract_closed_section(
        mesh,
        cut_y=cut_y,
    )

    loop_points_2d = loop_points_3d[:, [0, 2]]

    line_length = closed_polyline_length(
        loop_points_2d
    )

    uniform_points_2d = resample_closed_curve(
        loop_points_2d,
        n_samples=RESAMPLED_POINTS,
    )

    smoothing_value = (
        RESAMPLED_POINTS
        * (SMOOTHING_FACTOR * sigma) ** 2
    )

    tck, u_start, u_end = fit_periodic_bspline(
        uniform_points_2d,
        degree=BSPLINE_DEGREE,
        smoothing=smoothing_value,
    )

    spline_length, integration_error = (
        integrated_bspline_length(
            tck,
            u_start,
            u_end,
            epsabs=INTEGRATION_ABSOLUTE_TOLERANCE,
            epsrel=INTEGRATION_RELATIVE_TOLERANCE,
        )
    )

    return {
        "line_length": line_length,
        "spline_length": spline_length,
        "integration_error": integration_error,
        "smoothing_value": smoothing_value,
        "loop_points_3d": loop_points_3d,
        "section_actor": section_actor,
        "spline_tck": tck,
        "u_start": u_start,
        "u_end": u_end,
    }


def percentage_change(value, reference):
    """Calculates percentage change relative to a reference value."""
    return 100.0 * (value - reference) / reference


def values_for(records, noise_percent, measurement):
    """Returns all recorded values for one noise level and measurement."""
    return np.asarray([
        record[measurement]
        for record in records
        if record["noise_percent"] == noise_percent
    ])


def print_single_measurement(
    label,
    noise_percent,
    repeat,
    measurement,
    reference_line,
    reference_spline,
):
    """Prints line and spline lengths for one measurement."""
    line_length = measurement["line_length"]
    spline_length = measurement["spline_length"]

    print(label)
    print(f"  Noise level:             {noise_percent:.2f} %")

    if repeat is not None:
        print(f"  Repeat:                  {repeat + 1}/{N_REPEATS}")

    print(f"  Closed line length:      {line_length:.10f}")
    print(f"  Smoothing spline length: {spline_length:.10f}")
    print(
        "  Spline - line:           "
        f"{spline_length - line_length:+.10f}"
    )
    print(
        "  Spline integration err.: "
        f"{measurement['integration_error']:.3e}"
    )

    if reference_line is not None:
        print(
            "  Line change from normal: "
            f"{line_length - reference_line:+.10f} "
            f"({percentage_change(line_length, reference_line):+.6f} %)"
        )

    if reference_spline is not None:
        print(
            "  Spline change normal:    "
            f"{spline_length - reference_spline:+.10f} "
            f"({percentage_change(spline_length, reference_spline):+.6f} %)"
        )

    print()


def main():
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

    normal_measurement = measure_section(
        bunny,
        cut_y=cut_y,
        sigma=0.0,
    )

    reference_line = normal_measurement["line_length"]
    reference_spline = normal_measurement["spline_length"]

    print_single_measurement(
        label="Normal bunny reference",
        noise_percent=0.0,
        repeat=None,
        measurement=normal_measurement,
        reference_line=None,
        reference_spline=None,
    )

    records = []
    visualization_data = {
        0.0: {
            "mesh": bunny.clone(),
            "measurement": normal_measurement,
        }
    }

    rng = np.random.default_rng(RANDOM_SEED)

    noisy_levels = [
        noise_percent
        for noise_percent in NOISE_LEVELS_PERCENT
        if noise_percent > 0.0
    ]

    for repeat in range(N_REPEATS):
        standard_noise = rng.normal(
            loc=0.0,
            scale=1.0,
            size=bunny.npoints,
        )

        for noise_percent in noisy_levels:
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

            measurement = measure_section(
                noisy_bunny,
                cut_y=cut_y,
                sigma=sigma,
            )

            print_single_measurement(
                label="Noisy bunny measurement",
                noise_percent=noise_percent,
                repeat=repeat,
                measurement=measurement,
                reference_line=reference_line,
                reference_spline=reference_spline,
            )

            records.append({
                "repeat": repeat,
                "noise_percent": noise_percent,
                "sigma": sigma,
                "line_length": measurement["line_length"],
                "spline_length": measurement["spline_length"],
                "integration_error": measurement["integration_error"],
                "smoothing_value": measurement["smoothing_value"],
            })

            if repeat == 0:
                visualization_data[noise_percent] = {
                    "mesh": noisy_bunny,
                    "measurement": measurement,
                }

    summary = [{
        "noise_percent": 0.0,
        "sigma": 0.0,
        "line_mean": reference_line,
        "line_std": 0.0,
        "spline_mean": reference_spline,
        "spline_std": 0.0,
    }]

    for noise_percent in noisy_levels:
        line_values = values_for(
            records,
            noise_percent,
            "line_length",
        )

        spline_values = values_for(
            records,
            noise_percent,
            "spline_length",
        )

        summary.append({
            "noise_percent": noise_percent,
            "sigma": (
                noise_percent
                / 100.0
                * bunny_height
            ),
            "line_mean": float(np.mean(line_values)),
            "line_std": float(np.std(line_values, ddof=1)),
            "spline_mean": float(np.mean(spline_values)),
            "spline_std": float(np.std(spline_values, ddof=1)),
        })

    print("Mean perimeter comparison")
    print()
    print(
        f"{'Noise':>8}"
        f"{'Sigma':>13}"
        f"{'Line mean':>15}"
        f"{'Line SD':>13}"
        f"{'Line Δ%':>12}"
        f"{'Spline mean':>16}"
        f"{'Spline SD':>13}"
        f"{'Spline Δ%':>13}"
    )
    print("-" * 103)

    for item in summary:
        line_delta_percent = percentage_change(
            item["line_mean"],
            reference_line,
        )

        spline_delta_percent = percentage_change(
            item["spline_mean"],
            reference_spline,
        )

        print(
            f"{item['noise_percent']:>7.2f}%"
            f"{item['sigma']:>13.8f}"
            f"{item['line_mean']:>15.8f}"
            f"{item['line_std']:>13.8f}"
            f"{line_delta_percent:>+11.4f}%"
            f"{item['spline_mean']:>16.8f}"
            f"{item['spline_std']:>13.8f}"
            f"{spline_delta_percent:>+12.4f}%"
        )

    noise_axis = np.asarray([
        item["noise_percent"]
        for item in summary
    ])

    line_means = np.asarray([
        item["line_mean"]
        for item in summary
    ])

    line_stds = np.asarray([
        item["line_std"]
        for item in summary
    ])

    spline_means = np.asarray([
        item["spline_mean"]
        for item in summary
    ])

    spline_stds = np.asarray([
        item["spline_std"]
        for item in summary
    ])

    plt.figure(figsize=(10, 6))

    plt.errorbar(
        noise_axis,
        line_means,
        yerr=line_stds,
        marker="o",
        capsize=4,
        label="Closed line",
    )

    plt.errorbar(
        noise_axis,
        spline_means,
        yerr=spline_stds,
        marker="o",
        capsize=4,
        label="Smoothing cubic B-spline",
    )

    plt.axhline(
        reference_line,
        linestyle="--",
        label="Normal bunny line",
    )

    plt.axhline(
        reference_spline,
        linestyle=":",
        label="Normal bunny spline",
    )

    plt.xlabel(
        "Added normal noise, σ [% of bunny height]"
    )
    plt.ylabel("Section perimeter [model units]")
    plt.title(
        "Stanford Bunny section perimeter versus noise"
    )
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()

    maximum_noise = max(noisy_levels)

    clean_data = visualization_data[0.0]
    noisy_data = visualization_data[maximum_noise]

    clean_measurement = clean_data["measurement"]
    noisy_measurement = noisy_data["measurement"]

    clean_line_actor = Line(
        clean_measurement["loop_points_3d"],
        closed=True,
    ).c("green").lw(5)

    noisy_line_actor = Line(
        noisy_measurement["loop_points_3d"],
        closed=True,
    ).c("red").lw(4)

    clean_spline_2d = sample_bspline(
        clean_measurement["spline_tck"],
        clean_measurement["u_start"],
        clean_measurement["u_end"],
        resolution=DISPLAY_SPLINE_RESOLUTION,
    )

    noisy_spline_2d = sample_bspline(
        noisy_measurement["spline_tck"],
        noisy_measurement["u_start"],
        noisy_measurement["u_end"],
        resolution=DISPLAY_SPLINE_RESOLUTION,
    )

    clean_spline_3d = np.column_stack([
        clean_spline_2d[:, 0],
        np.full(len(clean_spline_2d), cut_y),
        clean_spline_2d[:, 1],
    ])

    noisy_spline_3d = np.column_stack([
        noisy_spline_2d[:, 0],
        np.full(len(noisy_spline_2d), cut_y),
        noisy_spline_2d[:, 1],
    ])

    clean_spline_actor = Line(
        clean_spline_3d,
        closed=True,
    ).c("blue").lw(3)

    noisy_spline_actor = Line(
        noisy_spline_3d,
        closed=True,
    ).c("blue").lw(5)

    plane_width = 1.1 * (x_max - x_min)
    plane_depth = 1.1 * (z_max - z_min)

    cut_plane = Plane(
        pos=(
            0.5 * (x_min + x_max),
            cut_y,
            0.5 * (z_min + z_max),
        ),
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
        clean_line_actor,
        clean_spline_actor,
        Text2D(
            "Normal bunny\n"
            f"Line: {reference_line:.8f}\n"
            f"Spline: {reference_spline:.8f}\n"
            "Green: line | Blue: spline",
            pos="top-left",
        ),
        axes=1,
        resetcam=True,
    )

    plotter.at(1).show(
        noisy_data["mesh"].clone().alpha(0.35),
        cut_plane.clone(),
        noisy_line_actor,
        noisy_spline_actor,
        Text2D(
            f"Noise σ = {maximum_noise:.2f}% of height\n"
            f"Line: {noisy_measurement['line_length']:.8f}\n"
            f"Spline: {noisy_measurement['spline_length']:.8f}\n"
            "Red: line | Blue: spline",
            pos="top-left",
        ),
        axes=1,
        resetcam=True,
    )

    plotter.interactive().close()


if __name__ == "__main__":
    main()
