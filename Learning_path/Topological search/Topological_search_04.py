from vedo import *
import numpy as np
from collections import deque
from scipy.spatial import cKDTree


# path = "/Users/paulovitor/Desktop/WE-TEAM/4 Semester Germany/data_scans/Capoeira_movement/capoeira_frame0001.obj"
path = "/Users/paulovitor/Desktop/WE-TEAM/4 Semester Germany/Data from Thesis/Thesis_Calaca_Paulo/Dynamic_Sequences/CONVENTIONAL_SQUAT_30FPS/OBJ/fps30_2_0000.obj"

mesh = Mesh(path)
V = np.asarray(mesh.points, dtype=float)

WELD_DUPLICATE_POSITIONS = True
WELD_TOLERANCE = 1e-6

BAND_HALF_WIDTH_EDGES = 5
CENTERLINE_HALF_WIDTH_EDGES = 1.2
ANGLE_BINS = 120

DRAW_PARTIAL_LOOP_IF_FAILED = False

POINT_RADIUS = 0.008
SELECTED_POINT_SIZE = 7
ANCHOR_POINT_SIZE = 10
PATH_LINE_WIDTH = 5


def nearest_vertex_id(point, vertices):
    """Finds the closest mesh vertex to the clicked point."""
    point = np.asarray(point, dtype=float)
    d2 = np.sum((vertices - point.reshape(1, 3)) ** 2, axis=1)
    return int(np.argmin(d2))


def build_vertex_adjacency(mesh):
    """Builds vertex adjacency from mesh faces."""
    n_vertices = mesh.npoints
    adjacency = [set() for _ in range(n_vertices)]

    for face in mesh.cells:
        face = np.asarray(face, dtype=int).ravel()

        if len(face) < 2:
            continue

        for i in range(len(face)):
            a = int(face[i])
            b = int(face[(i + 1) % len(face)])

            if a != b:
                adjacency[a].add(b)
                adjacency[b].add(a)

    return adjacency


def add_duplicate_position_links_kdtree(adjacency, vertices, tolerance=1e-6):
    """Adds links between vertices with nearly identical coordinates using cKDTree."""
    print("Using scipy.spatial.cKDTree for duplicate-position search.")
    print(f"Weld tolerance: {tolerance}")

    tree = cKDTree(vertices)
    pairs = tree.query_pairs(r=tolerance)

    for a, b in pairs:
        adjacency[a].add(b)
        adjacency[b].add(a)

    print(f"Duplicate-position pairs found: {len(pairs)}")

    return len(pairs)


def estimate_median_edge_length(vertices, adjacency, max_edges=200000):
    """Estimates the median mesh edge length."""
    lengths = []
    count = 0

    for a, nbs in enumerate(adjacency):
        for b in nbs:
            b = int(b)

            if b <= a:
                continue

            length = np.linalg.norm(vertices[b] - vertices[a])

            if length > 1e-12:
                lengths.append(length)
                count += 1

            if count >= max_edges:
                break

        if count >= max_edges:
            break

    if len(lengths) == 0:
        return 0.001

    return float(np.median(lengths))


def restricted_connected_component(start_vertex_id, adjacency, allowed_mask):
    """Returns the connected component inside an allowed mask."""
    start_vertex_id = int(start_vertex_id)

    if not allowed_mask[start_vertex_id]:
        return np.array([], dtype=int)

    visited = {start_vertex_id}
    queue = deque([start_vertex_id])

    while queue:
        current = queue.popleft()

        for nb in adjacency[current]:
            nb = int(nb)

            if nb in visited:
                continue

            if not allowed_mask[nb]:
                continue

            visited.add(nb)
            queue.append(nb)

    return np.array(sorted(visited), dtype=int)


def build_colored_band_points(vertices, selected_ids):
    """Creates selected band vertices."""
    pts = vertices[selected_ids]

    actor = Points(pts, r=SELECTED_POINT_SIZE)
    actor.c("orange")

    return actor


def extract_patch_from_vertex_ids(mesh, vertices, selected_ids):
    """Creates a mesh patch from faces fully contained in the selected vertices."""
    selected_set = set(int(i) for i in selected_ids)

    selected_faces_original = []

    for face in mesh.cells:
        face = np.asarray(face, dtype=int).ravel()

        if all(int(v) in selected_set for v in face):
            selected_faces_original.append(face)

    if len(selected_faces_original) == 0:
        return None

    used_original_ids = sorted(
        set(int(v) for face in selected_faces_original for v in face)
    )

    old_to_new = {
        old_id: new_id
        for new_id, old_id in enumerate(used_original_ids)
    }

    patch_vertices = vertices[used_original_ids]

    patch_faces = []

    for face in selected_faces_original:
        patch_faces.append([old_to_new[int(v)] for v in face])

    return Mesh([patch_vertices, patch_faces])


def choose_centerline_anchor_vertices(
    vertices,
    band_ids,
    clicked_vertex_id,
    clicked_y,
    centerline_y_tolerance,
    angle_bins=120,
):
    """Chooses ordered anchor vertices around the selected band."""
    band_ids = np.asarray(band_ids, dtype=int)

    if len(band_ids) < 3:
        return np.array([], dtype=int)

    pts = vertices[band_ids]
    xz = pts[:, [0, 2]]

    center_xz = xz.mean(axis=0)

    dx = xz[:, 0] - center_xz[0]
    dz = xz[:, 1] - center_xz[1]

    angles = np.arctan2(dz, dx)
    bin_edges = np.linspace(-np.pi, np.pi, angle_bins + 1)

    anchor_ids = []

    for i in range(angle_bins):
        a0 = bin_edges[i]
        a1 = bin_edges[i + 1]

        if i == angle_bins - 1:
            in_bin = (angles >= a0) & (angles <= a1)
        else:
            in_bin = (angles >= a0) & (angles < a1)

        candidate_ids = band_ids[in_bin]

        if len(candidate_ids) == 0:
            continue

        y_error = np.abs(vertices[candidate_ids, 1] - clicked_y)
        near_centerline = candidate_ids[y_error <= centerline_y_tolerance]

        if len(near_centerline) > 0:
            candidate_ids = near_centerline
            y_error = np.abs(vertices[candidate_ids, 1] - clicked_y)

        best_id = int(candidate_ids[int(np.argmin(y_error))])
        anchor_ids.append(best_id)

    anchor_ids = np.array(anchor_ids, dtype=int)

    if len(anchor_ids) < 3:
        return np.array([], dtype=int)

    _, unique_idx = np.unique(anchor_ids, return_index=True)
    unique_idx = np.sort(unique_idx)
    anchor_ids = anchor_ids[unique_idx]

    start_idx = int(
        np.argmin(
            np.linalg.norm(
                vertices[anchor_ids] - vertices[int(clicked_vertex_id)].reshape(1, 3),
                axis=1,
            )
        )
    )

    forward = np.concatenate([anchor_ids[start_idx:], anchor_ids[:start_idx]])

    backward_raw = anchor_ids[::-1]
    start_idx_backward = int(
        np.argmin(
            np.linalg.norm(
                vertices[backward_raw] - vertices[int(clicked_vertex_id)].reshape(1, 3),
                axis=1,
            )
        )
    )

    backward = np.concatenate(
        [backward_raw[start_idx_backward:], backward_raw[:start_idx_backward]]
    )

    x_positive = np.array([1.0, 0.0, 0.0], dtype=float)

    if len(forward) > 1:
        score_forward = float(
            np.dot(vertices[forward[1]] - vertices[forward[0]], x_positive)
        )
    else:
        score_forward = -np.inf

    if len(backward) > 1:
        score_backward = float(
            np.dot(vertices[backward[1]] - vertices[backward[0]], x_positive)
        )
    else:
        score_backward = -np.inf

    if score_backward > score_forward:
        return backward

    return forward


def topological_shortest_path_restricted(start_id, end_id, adjacency, allowed_mask):
    """Finds the shortest path by number of mesh-edge steps."""
    start_id = int(start_id)
    end_id = int(end_id)

    if start_id == end_id:
        return [start_id]

    if not allowed_mask[start_id]:
        return []

    if not allowed_mask[end_id]:
        return []

    visited = {start_id}
    previous = {}
    queue = deque([start_id])

    while queue:
        current = queue.popleft()

        for nb in adjacency[current]:
            nb = int(nb)

            if nb in visited:
                continue

            if not allowed_mask[nb]:
                continue

            visited.add(nb)
            previous[nb] = current

            if nb == end_id:
                path = [end_id]
                cur = end_id

                while cur != start_id:
                    cur = previous[cur]
                    path.append(cur)

                path.reverse()

                return path

            queue.append(nb)

    return []


def build_topological_loop_from_anchors(anchor_ids, adjacency, allowed_mask):
    """Connects ordered anchor vertices using topological shortest paths."""
    anchor_ids = np.asarray(anchor_ids, dtype=int)

    if len(anchor_ids) < 3:
        return np.array([], dtype=int), 0, []

    full_path = []
    failed_segments = 0
    failed_pairs = []

    for i in range(len(anchor_ids)):
        start_id = int(anchor_ids[i])
        end_id = int(anchor_ids[(i + 1) % len(anchor_ids)])

        segment = topological_shortest_path_restricted(
            start_id=start_id,
            end_id=end_id,
            adjacency=adjacency,
            allowed_mask=allowed_mask,
        )

        if len(segment) == 0:
            failed_segments += 1
            failed_pairs.append((start_id, end_id))

            if not DRAW_PARTIAL_LOOP_IF_FAILED:
                continue

        if len(segment) == 0:
            continue

        if len(full_path) == 0:
            full_path.extend(segment)
        else:
            full_path.extend(segment[1:])

    if failed_segments > 0 and not DRAW_PARTIAL_LOOP_IF_FAILED:
        return np.array([], dtype=int), failed_segments, failed_pairs

    if len(full_path) < 3:
        return np.array([], dtype=int), failed_segments, failed_pairs

    return np.array(full_path, dtype=int), failed_segments, failed_pairs


print(mesh)
print(f"Loaded mesh with {mesh.npoints} vertices and {mesh.ncells} cells.")

print("Building vertex adjacency...")
ADJACENCY = build_vertex_adjacency(mesh)

if WELD_DUPLICATE_POSITIONS:
    links_added = add_duplicate_position_links_kdtree(
        ADJACENCY,
        V,
        tolerance=WELD_TOLERANCE,
    )
    print(f"Duplicate-position links added: {links_added}")
else:
    print("Duplicate-position welding is OFF.")

valence = np.array([len(nbs) for nbs in ADJACENCY], dtype=int)

print("Adjacency statistics:")
print(f"Mean valence: {valence.mean():.2f}")
print(f"Min valence: {valence.min()}")
print(f"Max valence: {valence.max()}")

median_edge_length = estimate_median_edge_length(V, ADJACENCY)

band_y_tolerance = BAND_HALF_WIDTH_EDGES * median_edge_length
centerline_y_tolerance = CENTERLINE_HALF_WIDTH_EDGES * median_edge_length

print("Band settings:")
print(f"Median edge length: {median_edge_length:.8f}")
print(f"Band half-width tolerance: {band_y_tolerance:.8f}")
print(f"Centerline tolerance: {centerline_y_tolerance:.8f}")


plt = Plotter(axes=1)

mesh_actor = mesh.clone().c("lightgray").alpha(0.35)

info_text = Text2D(
    "Click on the mesh to create a topological loop inside the selected band",
    pos="top-left",
    s=0.75,
)

clicked_actor = None
band_points_actor = None
band_patch_actor = None
anchor_points_actor = None
polyline_actor = None
end_actor = None


def clear_previous():
    """Removes actors from the previous click."""
    global clicked_actor
    global band_points_actor
    global band_patch_actor
    global anchor_points_actor
    global polyline_actor
    global end_actor

    for actor in [
        clicked_actor,
        band_points_actor,
        band_patch_actor,
        anchor_points_actor,
        polyline_actor,
        end_actor,
    ]:
        if actor is not None:
            try:
                plt.remove(actor)
            except Exception:
                pass

    clicked_actor = None
    band_points_actor = None
    band_patch_actor = None
    anchor_points_actor = None
    polyline_actor = None
    end_actor = None


def on_click(evt):
    """Handles click selection and displays the topological loop."""
    global clicked_actor
    global band_points_actor
    global band_patch_actor
    global anchor_points_actor
    global polyline_actor
    global end_actor

    if evt.picked3d is None:
        return

    clear_previous()

    clicked_point = np.asarray(evt.picked3d, dtype=float)
    clicked_vertex_id = nearest_vertex_id(clicked_point, V)

    clicked_y = float(V[clicked_vertex_id, 1])

    band_mask = np.abs(V[:, 1] - clicked_y) <= band_y_tolerance

    band_ids = restricted_connected_component(
        start_vertex_id=clicked_vertex_id,
        adjacency=ADJACENCY,
        allowed_mask=band_mask,
    )

    restricted_mask = np.zeros(len(V), dtype=bool)
    restricted_mask[band_ids] = True

    anchor_ids = choose_centerline_anchor_vertices(
        vertices=V,
        band_ids=band_ids,
        clicked_vertex_id=clicked_vertex_id,
        clicked_y=clicked_y,
        centerline_y_tolerance=centerline_y_tolerance,
        angle_bins=ANGLE_BINS,
    )

    topological_loop_ids, failed_segments, failed_pairs = build_topological_loop_from_anchors(
        anchor_ids=anchor_ids,
        adjacency=ADJACENCY,
        allowed_mask=restricted_mask,
    )

    print("\nClicked vertex")
    print(f"Clicked coordinate: {clicked_point}")
    print(f"Nearest vertex ID: {clicked_vertex_id}")
    print(f"Nearest vertex coordinate: {V[clicked_vertex_id]}")
    print(f"Clicked Y: {clicked_y:.8f}")
    print(f"One-ring neighbors: {len(ADJACENCY[clicked_vertex_id])}")

    print("\nTopological band loop")
    print(f"Band half-width edges: {BAND_HALF_WIDTH_EDGES}")
    print(f"Band Y tolerance: {band_y_tolerance:.8f}")
    print(f"Band vertices: {len(band_ids)}")
    print(f"Anchor vertices: {len(anchor_ids)}")
    print(f"Topological loop vertices: {len(topological_loop_ids)}")
    print(f"Failed topological segments: {failed_segments}")

    if failed_segments > 0:
        print("No red loop was drawn because at least one anchor segment failed.")
        print("Try increasing BAND_HALF_WIDTH_EDGES or reducing ANGLE_BINS.")
        print(f"First failed pairs: {failed_pairs[:10]}")

    clicked_actor = Sphere(
        pos=V[clicked_vertex_id],
        r=POINT_RADIUS,
        c="blue",
    )

    plt.add(clicked_actor)

    if len(band_ids) > 0:
        band_points_actor = build_colored_band_points(
            vertices=V,
            selected_ids=band_ids,
        )
        plt.add(band_points_actor)

        selected_patch = extract_patch_from_vertex_ids(
            mesh=mesh,
            vertices=V,
            selected_ids=band_ids,
        )

        if selected_patch is not None:
            band_patch_actor = selected_patch.c("orange").alpha(0.30)
            plt.add(band_patch_actor)
        else:
            band_patch_actor = None
            print("No complete faces found for the selected band.")
    else:
        band_points_actor = None
        band_patch_actor = None
        print("No band vertices found.")

    if len(anchor_ids) > 0:
        anchor_points_actor = Points(V[anchor_ids], r=ANCHOR_POINT_SIZE).c("green")
        plt.add(anchor_points_actor)
    else:
        anchor_points_actor = None

    if len(topological_loop_ids) >= 3:
        path_points = V[topological_loop_ids]

        polyline_actor = Line(
            path_points,
            c="red",
            lw=PATH_LINE_WIDTH,
        )

        end_actor = Sphere(
            pos=path_points[-1],
            r=POINT_RADIUS,
            c="red",
        )

        plt.add(polyline_actor)
        plt.add(end_actor)
    else:
        polyline_actor = None
        end_actor = None

    info_text.text(
        f"Clicked vertex: {clicked_vertex_id}\n"
        f"Search: topological path inside band\n"
        f"Band width: {BAND_HALF_WIDTH_EDGES} edges above/below\n"
        f"Band vertices: {len(band_ids)}\n"
        f"Anchor vertices: {len(anchor_ids)}\n"
        f"Topological loop vertices: {len(topological_loop_ids)}\n"
        f"Failed segments: {failed_segments}\n"
        f"One-ring neighbors: {len(ADJACENCY[clicked_vertex_id])}\n\n"
        f"Angle bins: {ANGLE_BINS}\n"
        f"Median edge length: {median_edge_length:.6f}\n"
        f"Band Y tolerance: {band_y_tolerance:.6f}\n"
        f"Centerline tolerance: {centerline_y_tolerance:.6f}\n"
        f"Weld tolerance: {WELD_TOLERANCE}"
    )

    plt.render()


plt.add_callback("LeftButtonPress", on_click)

plt.show(
    mesh_actor,
    info_text,
    "Topological loop inside selected band",
    interactive=False,
)

plt.interactive().close()