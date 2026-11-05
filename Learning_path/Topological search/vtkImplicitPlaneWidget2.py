import numpy as np
from vedo import Plotter, Sphere

from vtkmodules.vtkCommonCore import vtkCommand
from vtkmodules.vtkCommonDataModel import vtkPlane
from vtkmodules.vtkInteractionWidgets import (
    vtkImplicitPlaneRepresentation,
    vtkImplicitPlaneWidget2,
)


# Create an example object
mesh = Sphere(r=1.0, res=60).triangulate()
mesh.c("lightgray").alpha(0.7)

# Create the vedo viewer
plt = Plotter(
    title="Interactive VTK Plane",
    size=(1200, 900),
)

# Initialize the window without starting interaction yet
plt.show(
    mesh,
    axes=1,
    resetcam=True,
    interactive=False,
)

# Plane storing the current origin and normal
vtk_plane = vtkPlane()
vtk_plane.SetOrigin(0.0, 0.0, 0.0)
vtk_plane.SetNormal(0.0, 1.0, 0.0)

# Create the plane representation
plane_representation = vtkImplicitPlaneRepresentation()
plane_representation.SetPlaceFactor(1.1)
plane_representation.PlaceWidget(mesh.bounds())

plane_representation.SetOrigin(vtk_plane.GetOrigin())
plane_representation.SetNormal(vtk_plane.GetNormal())

plane_representation.DrawPlaneOn()
plane_representation.GetPlaneProperty().SetOpacity(0.25)
plane_representation.GetPlaneProperty().SetColor(0.2, 0.7, 1.0)
plane_representation.GetNormalProperty().SetLineWidth(4)

# Create the interactive plane widget
plane_widget = vtkImplicitPlaneWidget2()
plane_widget.SetInteractor(plt.interactor)
plane_widget.SetCurrentRenderer(plt.renderer)
plane_widget.SetRepresentation(plane_representation)

# Store the current intersection actor
state = {
    "intersection_actor": None,
}


def update_intersection(origin, normal):
    """
    Updates the intersection between the mesh and the plane.
    """

    old_actor = state["intersection_actor"]

    if old_actor is not None:
        plt.remove(old_actor)

    intersection = mesh.intersect_with_plane(
        origin=origin,
        normal=normal,
    )

    if intersection is not None and intersection.npoints > 1:
        intersection.c("red").lw(5)
        plt.add(intersection)
        state["intersection_actor"] = intersection
    else:
        state["intersection_actor"] = None


def on_plane_interaction(widget, event):
    """
    Reads the updated plane and refreshes its mesh intersection.
    """

    representation = widget.GetRepresentation()
    representation.GetPlane(vtk_plane)

    origin = np.asarray(vtk_plane.GetOrigin(), dtype=float)
    normal = np.asarray(vtk_plane.GetNormal(), dtype=float)

    print(
        f"Origin: {np.round(origin, 4)} | "
        f"Normal: {np.round(normal, 4)}"
    )

    update_intersection(origin, normal)
    plt.render()


# Update the intersection whenever the plane moves
plane_widget.AddObserver(
    vtkCommand.InteractionEvent,
    on_plane_interaction,
)

# Create the initial intersection
update_intersection(
    vtk_plane.GetOrigin(),
    vtk_plane.GetNormal(),
)

# Activate the widget
plane_widget.On()

print("Drag the normal arrow to rotate the plane.")
print("Drag the center handle to translate the plane.")
print("Drag outside the widget to rotate the camera.")

plt.interactive().close()