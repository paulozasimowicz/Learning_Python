"""
Live MediaPipe landmark displacement transferred to man.vtk control points.

Meaning:
    When a MediaPipe landmark moves in the camera,
    the corresponding control point on man.vtk translates.
    Then a Thin Plate Spline warp deforms the whole mesh from those moving points.

Install:
    pip install opencv-python mediapipe vedo numpy

Run:
    python Prototype.py

Controls:
    q = quit
    c = calibrate current pose as reference
    r = reset calibration
    m = toggle X mirror
    p = pause/resume warp
    o = show/hide original mesh
"""

from pathlib import Path
import urllib.request

import cv2
import numpy as np
import mediapipe as mp

from vedo import Mesh, Plotter, Points, Arrows, settings, dataurl


# ============================================================
# SETTINGS
# ============================================================

MODEL_PATH = "pose_landmarker_full.task"

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_full/float16/latest/pose_landmarker_full.task"
)

CAMERA_ID = 0

# For normal laptop webcam testing, use upper body first.
# You can add knees/ankles later if the full body is visible.
SELECTED_IDS = [11, 12, 13, 14, 15, 16, 23, 24]

# 11 left shoulder
# 12 right shoulder
# 13 left elbow
# 14 right elbow
# 15 left wrist
# 16 right wrist
# 23 left hip
# 24 right hip

MIN_VISIBILITY = 0.35
MIN_PRESENCE = 0.35

SMOOTHING_ALPHA = 0.35

MIRROR_MEDIAPIPE_X = False

AUTO_CALIBRATE_ON_FIRST_VALID_POSE = True

DRAW_ARROWS = True
DRAW_LIVE_TARGET_POINTS = True
DRAW_REFERENCE_POINTS = True

SHOW_ORIGINAL_MESH = True

# Multiply landmark displacement.
# Increase if the mesh barely moves.
# Decrease if deformation is too aggressive.
DISPLACEMENT_GAIN = 1.0

# Add anchors to reduce global distortion.
# "none", "bottom", or "random"
FIXED_ANCHOR_MODE = "bottom"
N_FIXED_ANCHORS = 120

# Decimate man.vtk for faster live warp.
# None = full mesh
DECIMATE_TARGET_POINTS = 5000


POSE_CONNECTIONS = [
    (11, 12),
    (11, 13),
    (13, 15),
    (12, 14),
    (14, 16),
    (11, 23),
    (12, 24),
    (23, 24),
]


# ============================================================
# BASIC HELPERS
# ============================================================

def download_model_if_needed(model_path, model_url):
    model_path = Path(model_path)

    if model_path.exists():
        return

    print("Downloading MediaPipe model...")
    urllib.request.urlretrieve(model_url, model_path)
    print(f"Saved model to: {model_path}")


def np_points_from_landmarks(landmarks):
    return np.array([[lm.x, lm.y, lm.z] for lm in landmarks], dtype=float)


def visibility_presence_ok(image_landmarks, selected_ids):
    visibility = np.array(
        [getattr(lm, "visibility", 1.0) for lm in image_landmarks],
        dtype=float,
    )

    presence = np.array(
        [getattr(lm, "presence", 1.0) for lm in image_landmarks],
        dtype=float,
    )

    return bool(
        np.all(visibility[selected_ids] >= MIN_VISIBILITY)
        and np.all(presence[selected_ids] >= MIN_PRESENCE)
    )


def draw_landmarks(frame_bgr, image_landmarks):
    h, w = frame_bgr.shape[:2]

    pts_2d = []

    for lm in image_landmarks:
        x = int(lm.x * w)
        y = int(lm.y * h)
        pts_2d.append((x, y))

    for a, b in POSE_CONNECTIONS:
        if a < len(pts_2d) and b < len(pts_2d):
            cv2.line(frame_bgr, pts_2d[a], pts_2d[b], (0, 255, 0), 2)

    for i, p in enumerate(pts_2d):
        if i in SELECTED_IDS:
            cv2.circle(frame_bgr, p, 8, (255, 0, 0), 2)
            cv2.circle(frame_bgr, p, 4, (0, 0, 255), -1)

    return frame_bgr


def draw_text(frame_bgr, lines):
    y = 28

    for line in lines:
        cv2.putText(
            frame_bgr,
            line,
            (20, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        cv2.putText(
            frame_bgr,
            line,
            (20, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )

        y += 28

    return frame_bgr


# ============================================================
# ALIGNMENT HELPERS
# ============================================================

def similarity_align(A, B, allow_scale=True):
    """
    Find transform from MediaPipe reference landmarks A
    to mesh reference control points B.

    Important:
        For absolute points:
            P_mesh = scale * P_mediapipe @ R.T + translation

        For displacements:
            delta_mesh = scale * delta_mediapipe @ R.T

        Translation is NOT used for displacements.
    """
    A = np.asarray(A, dtype=float)
    B = np.asarray(B, dtype=float)

    ca = A.mean(axis=0)
    cb = B.mean(axis=0)

    A0 = A - ca
    B0 = B - cb

    H = A0.T @ B0
    U, S, Vt = np.linalg.svd(H)

    R = Vt.T @ U.T

    # Prevent mirrored solution
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1.0
        R = Vt.T @ U.T

    if allow_scale:
        denom = np.sum(A0 ** 2)
        scale = np.sum(S) / denom if denom > 1e-12 else 1.0
    else:
        scale = 1.0

    translation = cb - scale * (ca @ R.T)

    return scale, R, translation


def transform_absolute_points(points, scale, R, translation):
    points = np.asarray(points, dtype=float)
    return scale * (points @ R.T) + translation


def transform_displacements(deltas, scale, R):
    """
    Convert MediaPipe landmark movement into mesh-space movement.

    No translation here.
    """
    deltas = np.asarray(deltas, dtype=float)
    return scale * (deltas @ R.T)


def apply_mediapipe_pre_transform(points, mirror_x=False):
    points = np.asarray(points, dtype=float).copy()

    if mirror_x:
        points[:, 0] *= -1.0

    return points


# ============================================================
# MESH CONTROL POINTS
# ============================================================

def nearest_vertices(mesh_points, query_points):
    mesh_points = np.asarray(mesh_points, dtype=float)
    query_points = np.asarray(query_points, dtype=float)

    result = []

    for q in query_points:
        d2 = np.sum((mesh_points - q.reshape(1, 3)) ** 2, axis=1)
        idx = int(np.argmin(d2))
        result.append(mesh_points[idx])

    return np.asarray(result, dtype=float)


def estimate_control_points_on_man(mesh, selected_ids):
    """
    Approximate selected body control points on man.vtk.

    This is not anatomical precision.
    It only gives corresponding points so the prototype can run.
    """
    pts = np.asarray(mesh.vertices, dtype=float)

    mn = pts.min(axis=0)
    mx = pts.max(axis=0)

    center = 0.5 * (mn + mx)
    size = mx - mn

    width = size[0]
    height = size[1]
    depth = size[2]

    y_min = mn[1]

    left = -1.0
    right = 1.0

    def p(side, y_frac, x_frac, z_frac=0.0):
        return [
            center[0] + side * x_frac * width,
            y_min + y_frac * height,
            center[2] + z_frac * depth,
        ]

    template = {
        11: p(left,  0.78, 0.22, 0.00),  # left shoulder
        12: p(right, 0.78, 0.22, 0.00),  # right shoulder

        13: p(left,  0.62, 0.34, 0.00),  # left elbow
        14: p(right, 0.62, 0.34, 0.00),  # right elbow

        15: p(left,  0.48, 0.39, 0.00),  # left wrist
        16: p(right, 0.48, 0.39, 0.00),  # right wrist

        23: p(left,  0.52, 0.16, 0.00),  # left hip
        24: p(right, 0.52, 0.16, 0.00),  # right hip
    }

    approximate = np.asarray([template[i] for i in selected_ids], dtype=float)

    snapped = nearest_vertices(pts, approximate)

    return snapped


def build_fixed_anchors(mesh, mode="bottom", n_anchors=120):
    if mode == "none":
        return None

    pts = np.asarray(mesh.vertices, dtype=float)

    if mode == "bottom":
        y = pts[:, 1]
        threshold = np.percentile(y, 4)
        idx = np.where(y <= threshold)[0]

        if len(idx) == 0:
            return None

        n = min(n_anchors, len(idx))
        pick = np.linspace(0, len(idx) - 1, n).astype(int)

        return pts[idx[pick]]

    if mode == "random":
        rng = np.random.default_rng(42)
        n = min(n_anchors, len(pts))
        idx = rng.choice(len(pts), size=n, replace=False)

        return pts[idx]

    raise ValueError(f"Unknown anchor mode: {mode}")


def make_sources_targets(reference_control_points, live_control_points, anchors):
    if anchors is None:
        return reference_control_points, live_control_points

    sources = np.vstack([reference_control_points, anchors])
    targets = np.vstack([live_control_points, anchors])

    return sources, targets


# ============================================================
# VEDO HELPERS
# ============================================================

def safe_remove(plotter, actors):
    if actors is None:
        return

    if not isinstance(actors, list):
        actors = [actors]

    for actor in actors:
        try:
            plotter.remove(actor)
        except Exception:
            pass


def safe_add(plotter, actors):
    if actors is None:
        return

    if not isinstance(actors, list):
        actors = [actors]

    for actor in actors:
        try:
            plotter.add(actor)
        except Exception:
            try:
                plotter.show(actor, interactive=False, resetcam=False)
            except Exception:
                pass


# ============================================================
# MAIN
# ============================================================

def main():
    global MIRROR_MEDIAPIPE_X

    settings.use_depth_peeling = True

    download_model_if_needed(MODEL_PATH, MODEL_URL)

    # --------------------------------------------------------
    # Load man.vtk
    # --------------------------------------------------------

    print("Loading vedo built-in man.vtk...")
    mesh_ref = Mesh(dataurl + "man.vtk").triangulate()

    if DECIMATE_TARGET_POINTS is not None:
        mesh_ref = mesh_ref.clone().decimate(n=DECIMATE_TARGET_POINTS)

    mesh_ref.color("white")
    mesh_ref.alpha(0.20)

    reference_control_points = estimate_control_points_on_man(
        mesh_ref,
        SELECTED_IDS,
    )

    anchors = build_fixed_anchors(
        mesh_ref,
        mode=FIXED_ANCHOR_MODE,
        n_anchors=N_FIXED_ANCHORS,
    )

    # --------------------------------------------------------
    # vedo window
    # --------------------------------------------------------

    plt = Plotter(
        title="man.vtk points translated by MediaPipe landmarks",
        size=(1000, 850),
        axes=1,
    )

    original_actor = mesh_ref.clone().color("white")
    original_actor.alpha(0.18)

    reference_points_actor = Points(reference_control_points).c("red").ps(16)

    initial_actors = []

    if SHOW_ORIGINAL_MESH:
        initial_actors.append(original_actor)

    if DRAW_REFERENCE_POINTS:
        initial_actors.append(reference_points_actor)

    plt.show(
        *initial_actors,
        "Red = reference points on man.vtk | Green = live translated points",
        interactive=False,
    )

    dynamic_actors = []

    # --------------------------------------------------------
    # MediaPipe setup
    # --------------------------------------------------------

    BaseOptions = mp.tasks.BaseOptions
    PoseLandmarker = mp.tasks.vision.PoseLandmarker
    PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=VisionRunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        output_segmentation_masks=False,
    )

    cap = cv2.VideoCapture(CAMERA_ID)

    if not cap.isOpened():
        raise RuntimeError("Could not open camera.")

    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps is None or fps <= 1:
        fps = 30.0

    frame_id = 0

    calibrated = False
    paused = False

    mp_reference_points = None
    scale = None
    R = None
    translation = None

    smoothed_world_points = None
    last_valid_world_points = None

    print("\nControls:")
    print("q = quit")
    print("c = calibrate")
    print("r = reset")
    print("m = mirror X")
    print("p = pause")
    print("o = show/hide original mesh")
    print("\nStand in the reference pose. The first valid pose will calibrate automatically.\n")

    with PoseLandmarker.create_from_options(options) as landmarker:
        original_visible = SHOW_ORIGINAL_MESH

        while True:
            ok, frame_bgr = cap.read()

            if not ok:
                print("Could not read camera frame.")
                break

            frame_id += 1
            timestamp_ms = int(frame_id * 1000.0 / fps)

            # Mirror camera for easier interaction
            frame_bgr = cv2.flip(frame_bgr, 1)

            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=frame_rgb,
            )

            result = landmarker.detect_for_video(mp_image, timestamp_ms)

            pose_found = (
                result.pose_landmarks is not None
                and len(result.pose_landmarks) > 0
                and result.pose_world_landmarks is not None
                and len(result.pose_world_landmarks) > 0
            )

            valid = False

            if pose_found:
                image_landmarks = result.pose_landmarks[0]
                world_landmarks = result.pose_world_landmarks[0]

                frame_bgr = draw_landmarks(frame_bgr, image_landmarks)

                valid = visibility_presence_ok(image_landmarks, SELECTED_IDS)

                world_points = np_points_from_landmarks(world_landmarks)
                world_points = apply_mediapipe_pre_transform(
                    world_points,
                    mirror_x=MIRROR_MEDIAPIPE_X,
                )

                if smoothed_world_points is None:
                    smoothed_world_points = world_points.copy()
                else:
                    smoothed_world_points = (
                        SMOOTHING_ALPHA * world_points
                        + (1.0 - SMOOTHING_ALPHA) * smoothed_world_points
                    )

                last_valid_world_points = smoothed_world_points.copy()

                current_mp_points = smoothed_world_points[SELECTED_IDS].copy()

                # ------------------------------------------------
                # Calibration
                # ------------------------------------------------
                if (
                    AUTO_CALIBRATE_ON_FIRST_VALID_POSE
                    and not calibrated
                    and valid
                ):
                    mp_reference_points = current_mp_points.copy()

                    scale, R, translation = similarity_align(
                        mp_reference_points,
                        reference_control_points,
                        allow_scale=True,
                    )

                    calibrated = True

                    print("Auto calibration done.")
                    print(f"Scale: {scale:.4f}")

                # ------------------------------------------------
                # IMPORTANT PART:
                # landmark displacement -> mesh control displacement
                # ------------------------------------------------
                if calibrated and valid and not paused:
                    mp_delta = current_mp_points - mp_reference_points

                    mesh_delta = transform_displacements(
                        mp_delta,
                        scale,
                        R,
                    )

                    live_control_points = (
                        reference_control_points
                        + DISPLACEMENT_GAIN * mesh_delta
                    )

                    sources, targets = make_sources_targets(
                        reference_control_points,
                        live_control_points,
                        anchors,
                    )

                    try:
                        warped_mesh = mesh_ref.clone().warp(sources, targets)
                        warped_mesh.c("blue")
                        warped_mesh.alpha(0.50)

                        new_actors = [warped_mesh]

                        if DRAW_LIVE_TARGET_POINTS:
                            live_points_actor = Points(live_control_points).c("green").ps(16)
                            new_actors.append(live_points_actor)

                        if DRAW_ARROWS:
                            arrow_actor = Arrows(
                                reference_control_points,
                                live_control_points,
                            )
                            new_actors.append(arrow_actor)

                        safe_remove(plt, dynamic_actors)
                        dynamic_actors = new_actors
                        safe_add(plt, dynamic_actors)

                        plt.render()

                    except Exception as e:
                        print(f"Warp failed: {e}")

            status = [
                "MediaPipe displacement -> man.vtk point translation",
                f"Pose found: {pose_found}",
                f"Selected landmarks valid: {valid}",
                f"Calibrated: {calibrated}",
                f"Mirror X: {MIRROR_MEDIAPIPE_X}",
                f"Gain: {DISPLACEMENT_GAIN}",
                "q quit | c calibrate | r reset | m mirror | p pause | o original",
            ]

            frame_bgr = draw_text(frame_bgr, status)

            cv2.imshow("Camera MediaPipe landmarks", frame_bgr)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            elif key == ord("c"):
                if last_valid_world_points is not None:
                    mp_reference_points = last_valid_world_points[SELECTED_IDS].copy()

                    scale, R, translation = similarity_align(
                        mp_reference_points,
                        reference_control_points,
                        allow_scale=True,
                    )

                    calibrated = True

                    print("Manual calibration done.")
                    print(f"Scale: {scale:.4f}")
                else:
                    print("No valid pose available for calibration.")

            elif key == ord("r"):
                calibrated = False
                mp_reference_points = None
                scale = None
                R = None
                translation = None
                smoothed_world_points = None
                last_valid_world_points = None

                safe_remove(plt, dynamic_actors)
                dynamic_actors = []
                plt.render()

                print("Calibration reset.")

            elif key == ord("m"):
                MIRROR_MEDIAPIPE_X = not MIRROR_MEDIAPIPE_X

                calibrated = False
                smoothed_world_points = None
                last_valid_world_points = None

                safe_remove(plt, dynamic_actors)
                dynamic_actors = []
                plt.render()

                print(f"Mirror X: {MIRROR_MEDIAPIPE_X}")
                print("Calibration reset.")

            elif key == ord("p"):
                paused = not paused
                print(f"Paused: {paused}")

            elif key == ord("o"):
                original_visible = not original_visible

                if original_visible:
                    safe_add(plt, original_actor)
                else:
                    safe_remove(plt, original_actor)

                plt.render()

    cap.release()
    cv2.destroyAllWindows()

    try:
        plt.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()