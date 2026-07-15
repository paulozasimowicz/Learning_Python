from vedo import *
import numpy as np
from collections import deque


path = "/Users/paulovitor/Desktop/WE-TEAM/4 Semester Germany/data_scans/Capoeira_movement/capoeira_frame0001.obj"

mesh = Mesh(path)
V = np.asarray(mesh.points, dtype=float)

TOPOLOGICAL_RADIUS = 20
WELD_DUPLICATE_POSITIONS = True
WELD_TOLERANCE = 1e-6

POINT_RADIUS = 0.008
SELECTED_POINT_SIZE = 10


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


def add_duplicate_position_links(adjacency, vertices, tolerance=1e-6):
    """Adds links between vertices with nearly identical coordinates."""
    try:
        from scipy.spatial import cKDTree

        tree = cKDTree(vertices)
        pairs = tree.query_pairs(r=tolerance)

        for a, b in pairs:
            adjacency[a].add(b)
            adjacency[b].add(a)

        return len(pairs)

    except Exception:
        keys = np.round(vertices / tolerance).astype(np.int64)
        groups = {}

        for i, key in enumerate(map(tuple, keys)):
            groups.setdefault(key, []).append(i)

        links_added = 0

        for group in groups.values():
            if len(group) < 2:
                continue

            for a in group:
                for b in group:
                    if a != b:
                        adjacency[a].add(b)
                        links_added += 1

        return links_added


def k_ring_vertices(start_vertex_id, adjacency, k):
    """Returns all vertices within k edge steps from the start vertex."""
    start_vertex_id = int(start_vertex_id)

    visited = {start_vertex_id}
    ring_level = {start_vertex_id: 0}

    queue = deque([start_vertex_id])

    while queue:
        current = queue.popleft()
        current_level = ring_level[current]

        if current_level >= k:
            continue

        for nb in adjacency[current]:
            nb = int(nb)

            if nb not in visited:
                visited.add(nb)
                ring_level[nb] = current_level + 1
                queue.append(nb)

    selected_ids = np.array(sorted(visited), dtype=int)

    return selected_ids, ring_level


def connected_component_vertices(start_vertex_id, adjacency):
    """Returns all vertices connected to the start vertex."""
    start_vertex_id = int(start_vertex_id)

    visited = {start_vertex_id}
    queue = deque([start_vertex_id])

    while queue:
        current = queue.popleft()

        for nb in adjacency[current]:
            nb = int(nb)

            if nb not in visited:
                visited.add(nb)
                queue.append(nb)

    return np.array(sorted(visited), dtype=int)


def build_colored_ring_points(vertices, selected_ids, ring_level):
    """Creates selected vertices colored by ring level."""
    pts = vertices[selected_ids]

    levels = np.array(
        [ring_level[int(i)] for i in selected_ids],
        dtype=float,
    )

    actor = Points(pts, r=SELECTED_POINT_SIZE)
    actor.pointdata["TopologicalRing"] = levels
    actor.cmap("viridis", levels, on="points")

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


print(mesh)
print(f"Loaded mesh with {mesh.npoints} vertices and {mesh.ncells} cells.")

print("Building vertex adjacency...")
ADJACENCY = build_vertex_adjacency(mesh)

if WELD_DUPLICATE_POSITIONS:
    links_added = add_duplicate_position_links(
        ADJACENCY,
        V,
        tolerance=WELD_TOLERANCE,
    )
    print(f"Duplicate-position links added: {links_added}")

valence = np.array([len(nbs) for nbs in ADJACENCY], dtype=int)

print("Adjacency statistics:")
print(f"Mean valence: {valence.mean():.2f}")
print(f"Min valence: {valence.min()}")
print(f"Max valence: {valence.max()}")


plt = Plotter(axes=1)

mesh_actor = mesh.clone().c("lightgray").alpha(0.35)

info_text = Text2D(
    "Click on the mesh to select k-ring connected vertices",
    pos="top-left",
    s=0.75,
)

clicked_actor = None
selected_points_actor = None
selected_patch_actor = None


def clear_previous():
    global clicked_actor
    global selected_points_actor
    global selected_patch_actor

    for actor in [
        clicked_actor,
        selected_points_actor,
        selected_patch_actor,
    ]:
        if actor is not None:
            try:
                plt.remove(actor)
            except Exception:
                pass

    clicked_actor = None
    selected_points_actor = None
    selected_patch_actor = None


def on_click(evt):
    global clicked_actor
    global selected_points_actor
    global selected_patch_actor

    if evt.picked3d is None:
        return

    clear_previous()

    clicked_point = np.asarray(evt.picked3d, dtype=float)
    clicked_vertex_id = nearest_vertex_id(clicked_point, V)

    selected_ids, ring_level = k_ring_vertices(
        start_vertex_id=clicked_vertex_id,
        adjacency=ADJACENCY,
        k=TOPOLOGICAL_RADIUS,
    )

    component_ids = connected_component_vertices(
        start_vertex_id=clicked_vertex_id,
        adjacency=ADJACENCY,
    )

    print("\nClicked vertex")
    print(f"Clicked coordinate: {clicked_point}")
    print(f"Nearest vertex ID: {clicked_vertex_id}")
    print(f"Nearest vertex coordinate: {V[clicked_vertex_id]}")
    print(f"One-ring neighbors: {len(ADJACENCY[clicked_vertex_id])}")

    print("\nTopological selection")
    print(f"Topological radius: {TOPOLOGICAL_RADIUS} rings")
    print(f"Selected vertices: {len(selected_ids)}")
    print(f"Connected component size: {len(component_ids)} / {len(V)}")

    if len(component_ids) <= len(selected_ids):
        print("The k-ring reached the full connected component of this clicked vertex.")

    clicked_actor = Sphere(
        pos=V[clicked_vertex_id],
        r=POINT_RADIUS,
        c="red",
    )

    selected_points_actor = build_colored_ring_points(
        vertices=V,
        selected_ids=selected_ids,
        ring_level=ring_level,
    )

    selected_patch = extract_patch_from_vertex_ids(
        mesh=mesh,
        vertices=V,
        selected_ids=selected_ids,
    )

    if selected_patch is not None:
        selected_patch_actor = selected_patch.c("orange").alpha(0.55)
        plt.add(selected_patch_actor)
    else:
        selected_patch_actor = None

    plt.add(selected_points_actor)
    plt.add(clicked_actor)

    info_text.text(
        f"Clicked vertex: {clicked_vertex_id}\n"
        f"Topological radius: {TOPOLOGICAL_RADIUS} rings\n"
        f"Selected vertices: {len(selected_ids)}\n"
        f"One-ring neighbors: {len(ADJACENCY[clicked_vertex_id])}\n"
        f"Connected component size: {len(component_ids)} / {len(V)}\n\n"
        f"Weld duplicate positions: {WELD_DUPLICATE_POSITIONS}\n"
        f"Weld tolerance: {WELD_TOLERANCE}"
    )

    plt.render()


plt.add_callback("LeftButtonPress", on_click)

plt.show(
    mesh_actor,
    info_text,
    "K-ring connected vertex search",
    interactive=False,
)

plt.interactive().close()