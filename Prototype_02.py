"""
Live MediaPipe 33-landmark displacement -> man.vtk TPS warp.

Meaning:
    MediaPipe detects 33 body landmarks.
    Each visible landmark controls one corresponding point on man.vtk.
    The corresponding man.vtk point translates by the landmark displacement.
    TPS warps the whole mesh.

Install:
    pip install opencv-python mediapipe vedo numpy

Run:
    python Prototype.py

Controls:
    q = quit
    c = calibrate current pose
    r = reset calibration
    m = toggle MediaPipe X mirror
    p = pause/resume warp
    o = show/hide original mesh
    a = toggle anchors
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

# Use all 33 MediaPipe Pose landmarks.
SELECTED_IDS = list(range(33))

# If True, the code waits until all 33 landmarks are visible enough.
# For a laptop webcam this is usually too strict.
REQUIRE_ALL_SELECTED_VISIBLE = False

# Minimum number of active landmarks needed to compute a warp.
MIN_ACTIVE_LANDMARKS = 6

MIN_VISIBILITY = 0.30
MIN_PRESENCE = 0.30

SMOOTHING_ALPHA = 0.35

MIRROR_MEDIAPIPE_X = False

AUTO_CALIBRATE_ON_FIRST_VALID_POSE = True

# Increase if the mesh barely moves.
# Decrease if the mesh deforms too much.
DISPLACEMENT_GAIN = 1.0

# Decimate man.vtk for faster live TPS.
# None = full mesh.
DECIMATE_TARGET_POINTS = 5000

SHOW_ORIGINAL_MESH = True
DRAW_REFERENCE_POINTS = True
DRAW_LIVE_POINTS = True
DRAW_ARROWS = True

USE_ANCHORS = True
N_FIXED_ANCHORS = 120


LANDMARK_NAMES = {
    0: "nose",
    1: "left_eye_inner",
    2: "left_eye",
    3: "left_eye_outer",
    4: "right_eye_inner",
    5: "right_eye",
    6: "right_eye_outer",
    7: "left_ear",
    8: "right_ear",
    9: "mouth_left",
    10: "mouth_right",
    11: "left_shoulder",
    12: "right_shoulder",
    13: "left_elbow",
    14: "right_elbow",
    15: "left_wrist",
    16: "right_wrist",
    17: "left_pinky",
    18: "right_pinky",
    19: "left_index",
    20: "right_index",
    21: "left_thumb",
    22: "right_thumb",
    23: "left_hip",
    24: "right_hip",
    25: "left_knee",
    26: "right_knee",
    27: "left_ankle",
    28: "right_ankle",
    29: "left_heel",
    30: "right_heel",
    31: "left_foot_index",
    32: "right_foot_index",
}


POSE_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7),
    (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10),

    (11, 12),
    (11, 13), (13, 15),
    (12, 14), (14, 16),

    (15, 17), (15, 19), (15, 21),
    (17, 19),
    (16, 18), (16, 20), (16, 22),
    (18, 20),

    (11, 23),
    (12, 24),
    (23, 24),

    (23, 25), (25, 27),
    (24, 26), (26, 28),

    (27, 29), (29, 31), (27, 31),
    (28, 30), (30, 32), (28, 32),
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


def get_visibility_presence(image_landmarks):
    visibility = np.array(
        [getattr(lm, "visibility", 1.0) for lm in image_landmarks],
        dtype=float,
    )

    presence = np.array(
        [getattr(lm, "presence", 1.0) for lm in image_landmarks],
        dtype=float,
    )

    return visibility, presence


def get_active_landmark_ids(image_landmarks, selected_ids):
    visibility, presence = get_visibility_presence(image_landmarks)

    active = []

    for i in selected_ids:
        if visibility[i] >= MIN_VISIBILITY and presence[i] >= MIN_PRESENCE:
            active.append(i)

    return active


def draw_landmarks(frame_bgr, image_landmarks, active_ids=None, mirror_display=True):
    h, w = frame_bgr.shape[:2]

    active_ids = set(active_ids or [])

    pts_2d = []

    for lm in image_landmarks:
        if mirror_display:
            x = int((1.0 - lm.x) * w)
        else:
            x = int(lm.x * w)

        y = int(lm.y * h)
        pts_2d.append((x, y))

    for a, b in POSE_CONNECTIONS:
        if a < len(pts_2d) and b < len(pts_2d):
            cv2.line(frame_bgr, pts_2d[a], pts_2d[b], (0, 255, 0), 2)

    for i, p in enumerate(pts_2d):
        if i in SELECTED_IDS:
            if i in active_ids:
                cv2.circle(frame_bgr, p, 6, (0, 0, 255), -1)
                cv2.circle(frame_bgr, p, 9, (255, 0, 0), 2)
            else:
                cv2.circle(frame_bgr, p, 4, (120, 120, 120), -1)

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


def apply_mediapipe_pre_transform(points, mirror_x=False):
    points = np.asarray(points, dtype=float).copy()

    if mirror_x:
        points[:, 0] *= -1.0

    return points


# ============================================================
# ALIGNMENT
# ============================================================

def similarity_align(A, B, allow_scale=True):
    """
    Fit transform from MediaPipe reference points A to mesh control points B.

    Absolute points:
        P_mesh = scale * P_mediapipe @ R.T + translation

    Displacements:
        delta_mesh = scale * delta_mediapipe @ R.T

    For displacement transfer, translation is not used.
    """
    A = np.asarray(A, dtype=float)
    B = np.asarray(B, dtype=float)

    if len(A) < 3:
        raise ValueError("Need at least 3 points for similarity alignment.")

    ca = A.mean(axis=0)
    cb = B.mean(axis=0)

    A0 = A - ca
    B0 = B - cb

    H = A0.T @ B0
    U, S, Vt = np.linalg.svd(H)

    R = Vt.T @ U.T

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


def transform_displacements(deltas, scale, R):
    deltas = np.asarray(deltas, dtype=float)
    return scale * (deltas @ R.T)


# ============================================================
# man.vtk CONTROL POINT TEMPLATE
# ============================================================

def nearest_vertices(mesh_points, query_points):
    mesh_points = np.asarray(mesh_points, dtype=float)
    query_points = np.asarray(query_points, dtype=float)

    nearest = []

    for q in query_points:
        d2 = np.sum((mesh_points - q.reshape(1, 3)) ** 2, axis=1)
        idx = int(np.argmin(d2))
        nearest.append(mesh_points[idx])

    return np.asarray(nearest, dtype=float)


def estimate_33_control_points_on_man_zup(mesh):
    """
    Approximate MediaPipe's 33 landmarks on man.vtk.

    Important:
        man.vtk is treated as Z-up.
        x = left/right
        y = depth/front-back
        z = vertical height

    This is only a prototype mapping.
    For a serious version, manually pick the control points on man.vtk.
    """
    pts = np.asarray(mesh.vertices, dtype=float)

    mn = pts.min(axis=0)
    mx = pts.max(axis=0)

    center = 0.5 * (mn + mx)
    size = mx - mn

    width_x = size[0]
    depth_y = size[1]
    height_z = size[2]

    z_min = mn[2]

    left = -1.0
    right = 1.0

    def p(side, z_frac, x_frac, y_frac=0.0):
        x = center[0] + side * x_frac * width_x
        y = center[1] + y_frac * depth_y
        z = z_min + z_frac * height_z
        return [x, y, z]

    # y_frac:
    # negative/positive front-back may depend on the model orientation.
    # It is not critical for the first prototype because points are snapped to vertices.
    template = {
        # Face/head
        0:  p(0.0,   0.935, 0.000, -0.20),  # nose

        1:  p(left,  0.950, 0.025, -0.18),  # left eye inner
        2:  p(left,  0.952, 0.040, -0.18),  # left eye
        3:  p(left,  0.948, 0.060, -0.17),  # left eye outer

        4:  p(right, 0.950, 0.025, -0.18),  # right eye inner
        5:  p(right, 0.952, 0.040, -0.18),  # right eye
        6:  p(right, 0.948, 0.060, -0.17),  # right eye outer

        7:  p(left,  0.925, 0.090, -0.02),  # left ear
        8:  p(right, 0.925, 0.090, -0.02),  # right ear

        9:  p(left,  0.900, 0.035, -0.20),  # mouth left
        10: p(right, 0.900, 0.035, -0.20),  # mouth right

        # Torso and arms
        11: p(left,  0.785, 0.220, 0.00),   # left shoulder
        12: p(right, 0.785, 0.220, 0.00),   # right shoulder

        13: p(left,  0.620, 0.340, 0.00),   # left elbow
        14: p(right, 0.620, 0.340, 0.00),   # right elbow

        15: p(left,  0.455, 0.385, 0.00),   # left wrist
        16: p(right, 0.455, 0.385, 0.00),   # right wrist

        17: p(left,  0.430, 0.410, -0.03),  # left pinky
        18: p(right, 0.430, 0.410, -0.03),  # right pinky

        19: p(left,  0.425, 0.400, -0.08),  # left index
        20: p(right, 0.425, 0.400, -0.08),  # right index

        21: p(left,  0.445, 0.370, -0.05),  # left thumb
        22: p(right, 0.445, 0.370, -0.05),  # right thumb

        # Pelvis and legs
        23: p(left,  0.525, 0.145, 0.00),   # left hip
        24: p(right, 0.525, 0.145, 0.00),   # right hip

        25: p(left,  0.300, 0.115, 0.00),   # left knee
        26: p(right, 0.300, 0.115, 0.00),   # right knee

        27: p(left,  0.095, 0.090, 0.00),   # left ankle
        28: p(right, 0.095, 0.090, 0.00),   # right ankle

        29: p(left,  0.055, 0.090, 0.09),   # left heel
        30: p(right, 0.055, 0.090, 0.09),   # right heel

        31: p(left,  0.035, 0.100, -0.14),  # left foot index
        32: p(right, 0.035, 0.100, -0.14),  # right foot index
    }

    rough = np.asarray([template[i] for i in range(33)], dtype=float)
    snapped = nearest_vertices(pts, rough)

    return snapped


def build_fixed_anchors(mesh, n_anchors=120):
    """
    Bottom anchors stabilize the TPS warp.
    """
    pts = np.asarray(mesh.vertices, dtype=float)

    z = pts[:, 2]
    threshold = np.percentile(z, 4)
    idx = np.where(z <= threshold)[0]

    if len(idx) == 0:
        return None

    n = min(n_anchors, len(idx))
    pick = np.linspace(0, len(idx) - 1, n).astype(int)

    return pts[idx[pick]]


def make_sources_targets(reference_control_points, live_control_points, active_ids, anchors):
    sources = reference_control_points[active_ids]
    targets = live_control_points[active_ids]

    if anchors is not None and USE_ANCHORS:
        sources = np.vstack([sources, anchors])
        targets = np.vstack([targets, anchors])

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
    global USE_ANCHORS

    settings.use_depth_peeling = True

    download_model_if_needed(MODEL_PATH, MODEL_URL)

    print("Loading vedo built-in man.vtk...")
    mesh_ref = Mesh(dataurl + "man.vtk").triangulate()

    if DECIMATE_TARGET_POINTS is not None:
        mesh_ref = mesh_ref.clone().decimate(n=DECIMATE_TARGET_POINTS)

    mesh_ref.color("white")
    mesh_ref.alpha(0.20)

    reference_control_points_33 = estimate_33_control_points_on_man_zup(mesh_ref)

    anchors = build_fixed_anchors(mesh_ref, n_anchors=N_FIXED_ANCHORS)

    # --------------------------------------------------------
    # vedo window
    # --------------------------------------------------------

    plt = Plotter(
        title="man.vtk controlled by all visible MediaPipe Pose landmarks",
        size=(1000, 850),
        axes=1,
    )

    original_actor = mesh_ref.clone().color("white")
    original_actor.alpha(0.18)

    reference_points_actor = Points(reference_control_points_33).c("red").ps(10)

    initial_actors = []

    if SHOW_ORIGINAL_MESH:
        initial_actors.append(original_actor)

    if DRAW_REFERENCE_POINTS:
        initial_actors.append(reference_points_actor)

    plt.show(
        *initial_actors,
        "Red = 33 reference points on man.vtk | Green = live MediaPipe-driven points",
        interactive=False,
    )

    dynamic_actors = []
    original_visible = SHOW_ORIGINAL_MESH

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

    mp_reference_points_33 = None
    calibration_ids = None

    scale = None
    R = None
    translation = None

    smoothed_world_points = None
    last_valid_world_points = None
    last_active_ids = []

    print("\nControls:")
    print("q = quit")
    print("c = calibrate current pose")
    print("r = reset calibration")
    print("m = mirror X")
    print("p = pause")
    print("o = show/hide original mesh")
    print("a = toggle anchors")
    print("\nFor all 33 landmarks, stand far enough so the full body is visible.\n")

    with PoseLandmarker.create_from_options(options) as landmarker:
        while True:
            ok, frame_raw_bgr = cap.read()

            if not ok:
                print("Could not read camera frame.")
                break

            frame_id += 1
            timestamp_ms = int(frame_id * 1000.0 / fps)

            # Important:
            # Detection is done on the raw camera frame.
            # Only the displayed frame is mirrored.
            frame_rgb = cv2.cvtColor(frame_raw_bgr, cv2.COLOR_BGR2RGB)

            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=frame_rgb,
            )

            result = landmarker.detect_for_video(mp_image, timestamp_ms)

            frame_display_bgr = cv2.flip(frame_raw_bgr, 1)

            pose_found = (
                result.pose_landmarks is not None
                and len(result.pose_landmarks) > 0
                and result.pose_world_landmarks is not None
                and len(result.pose_world_landmarks) > 0
            )

            active_ids = []

            if pose_found:
                image_landmarks = result.pose_landmarks[0]
                world_landmarks = result.pose_world_landmarks[0]

                active_ids = get_active_landmark_ids(
                    image_landmarks,
                    SELECTED_IDS,
                )

                if REQUIRE_ALL_SELECTED_VISIBLE:
                    valid_for_warp = len(active_ids) == len(SELECTED_IDS)
                else:
                    valid_for_warp = len(active_ids) >= MIN_ACTIVE_LANDMARKS

                frame_display_bgr = draw_landmarks(
                    frame_display_bgr,
                    image_landmarks,
                    active_ids=active_ids,
                    mirror_display=True,
                )

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
                last_active_ids = active_ids.copy()

                # ------------------------------------------------
                # Calibration
                # ------------------------------------------------

                if (
                    AUTO_CALIBRATE_ON_FIRST_VALID_POSE
                    and not calibrated
                    and valid_for_warp
                ):
                    mp_reference_points_33 = smoothed_world_points.copy()
                    calibration_ids = active_ids.copy()

                    scale, R, translation = similarity_align(
                        mp_reference_points_33[calibration_ids],
                        reference_control_points_33[calibration_ids],
                        allow_scale=True,
                    )

                    calibrated = True

                    print("Auto calibration done.")
                    print(f"Calibration landmarks: {len(calibration_ids)}")
                    print(f"Scale: {scale:.4f}")

                # ------------------------------------------------
                # Landmark displacement -> man.vtk point displacement
                # ------------------------------------------------

                if calibrated and valid_for_warp and not paused:
                    current_points_33 = smoothed_world_points.copy()

                    mp_delta_33 = current_points_33 - mp_reference_points_33

                    mesh_delta_33 = transform_displacements(
                        mp_delta_33,
                        scale,
                        R,
                    )

                    live_control_points_33 = (
                        reference_control_points_33
                        + DISPLACEMENT_GAIN * mesh_delta_33
                    )

                    sources, targets = make_sources_targets(
                        reference_control_points_33,
                        live_control_points_33,
                        active_ids,
                        anchors,
                    )

                    try:
                        warped_mesh = mesh_ref.clone().warp(sources, targets)
                        warped_mesh.c("blue")
                        warped_mesh.alpha(0.50)

                        new_actors = [warped_mesh]

                        if DRAW_LIVE_POINTS:
                            live_points_actor = Points(
                                live_control_points_33[active_ids]
                            ).c("green").ps(13)
                            new_actors.append(live_points_actor)

                        if DRAW_ARROWS:
                            arrow_actor = Arrows(
                                reference_control_points_33[active_ids],
                                live_control_points_33[active_ids],
                            )
                            new_actors.append(arrow_actor)

                        safe_remove(plt, dynamic_actors)
                        dynamic_actors = new_actors
                        safe_add(plt, dynamic_actors)

                        plt.render()

                    except Exception as e:
                        print(f"Warp failed: {e}")

            else:
                valid_for_warp = False

            status = [
                "MediaPipe 33 pose landmarks -> man.vtk TPS warp",
                f"Pose found: {pose_found}",
                f"Active landmarks: {len(active_ids)} / 33",
                f"Calibrated: {calibrated}",
                f"Mirror X: {MIRROR_MEDIAPIPE_X}",
                f"Anchors: {USE_ANCHORS}",
                f"Gain: {DISPLACEMENT_GAIN}",
                "q quit | c calibrate | r reset | m mirror | p pause | o original | a anchors",
            ]

            frame_display_bgr = draw_text(frame_display_bgr, status)

            cv2.imshow("Camera MediaPipe landmarks", frame_display_bgr)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            elif key == ord("c"):
                if last_valid_world_points is not None and len(last_active_ids) >= MIN_ACTIVE_LANDMARKS:
                    mp_reference_points_33 = last_valid_world_points.copy()
                    calibration_ids = last_active_ids.copy()

                    scale, R, translation = similarity_align(
                        mp_reference_points_33[calibration_ids],
                        reference_control_points_33[calibration_ids],
                        allow_scale=True,
                    )

                    calibrated = True

                    print("Manual calibration done.")
                    print(f"Calibration landmarks: {len(calibration_ids)}")
                    print(f"Scale: {scale:.4f}")

                else:
                    print("No valid pose available for calibration.")

            elif key == ord("r"):
                calibrated = False
                mp_reference_points_33 = None
                calibration_ids = None
                scale = None
                R = None
                translation = None
                smoothed_world_points = None
                last_valid_world_points = None
                last_active_ids = []

                safe_remove(plt, dynamic_actors)
                dynamic_actors = []
                plt.render()

                print("Calibration reset.")

            elif key == ord("m"):
                MIRROR_MEDIAPIPE_X = not MIRROR_MEDIAPIPE_X

                calibrated = False
                smoothed_world_points = None
                last_valid_world_points = None
                last_active_ids = []

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

            elif key == ord("a"):
                USE_ANCHORS = not USE_ANCHORS
                print(f"Anchors: {USE_ANCHORS}")

    cap.release()
    cv2.destroyAllWindows()

    try:
        plt.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()