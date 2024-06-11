import ifcopenshell
import matplotlib.pyplot as plt
from shapely.geometry import LineString, Point, Polygon

# Load the IFC file
ifc_file = ifcopenshell.open("./Dataset/Modell_V2_IFC_4.ifc")


# Function to get a component name or identifier
def get_component_identifier(entity):
    if hasattr(entity, "Name") and entity.Name:
        return entity.Name
    elif hasattr(entity, "Description") and entity.Description:
        return entity.Description
    elif hasattr(entity, "GlobalId") and entity.GlobalId:
        return entity.GlobalId
    else:
        return "Unnamed"


# Extract geometric data (example: extracting IfcCartesianPoint)
def get_cartesian_points(ifc_file):
    cartesian_points = ifc_file.by_type("IfcCartesianPoint")
    wkt_points_with_names = []
    for point in cartesian_points:
        coordinates = point.Coordinates
        wkt_point = Point(
            coordinates[0],
            coordinates[1],
            coordinates[2] if len(coordinates) > 2 else 0,
        )
        point_identifier = get_component_identifier(point)
        wkt_points_with_names.append((point_identifier, wkt_point))
    return wkt_points_with_names


# Extract geometric data for IfcPolyline
def get_polylines(ifc_file):
    polylines = ifc_file.by_type("IfcPolyline")
    wkt_lines_with_names = []
    for polyline in polylines:
        points = [
            (
                point.Coordinates[0],
                point.Coordinates[1],
                point.Coordinates[2] if len(point.Coordinates) > 2 else 0,
            )
            for point in polyline.Points
        ]
        wkt_line = LineString(points)
        line_identifier = get_component_identifier(polyline)
        wkt_lines_with_names.append((line_identifier, wkt_line))
    return wkt_lines_with_names


# Extract geometric data for IfcSurface
def get_surfaces(ifc_file):
    surfaces = ifc_file.by_type("IfcSurface")
    wkt_surfaces_with_names = []
    for surface in surfaces:
        if hasattr(surface, "Outer"):
            boundary = surface.Outer.CfsFaces[0].Bounds[0].Bound
            points = [
                (
                    point.Coordinates[0],
                    point.Coordinates[1],
                    point.Coordinates[2] if len(point.Coordinates) > 2 else 0,
                )
                for point in boundary.Points
            ]
            wkt_polygon = Polygon(points)
            surface_identifier = get_component_identifier(surface)
            wkt_surfaces_with_names.append((surface_identifier, wkt_polygon))
    return wkt_surfaces_with_names


# Extract geometric data for IfcIndexedPolygonalFace
def get_indexed_polygonal_faces(ifc_file):
    vertices = ifc_file.by_type("IfcCartesianPointList3D")[0].CoordList
    faces = ifc_file.by_type("IfcIndexedPolygonalFace")
    wkt_faces_with_names = []

    print(f"Total number of vertices available: {len(vertices)}")
    for face in faces:
        indices = face.CoordIndex
        points = []
        for idx in indices:
            if 0 < idx <= len(vertices):
                points.append(vertices[idx - 1])  # Adjust for 1-based indexing
            else:
                print(f"Warning: Index {idx} is out of range for vertices.")
        if len(points) >= 3:  # Ensure there are at least 3 points to form a valid face
            try:
                wkt_polygon = Polygon(points)
                if wkt_polygon.is_valid and not wkt_polygon.is_empty:
                    face_identifier = get_component_identifier(face)
                    wkt_faces_with_names.append((face_identifier, wkt_polygon))
                else:
                    print(
                        f"Warning: Face with indices {indices} is not a valid polygon. Points: {points}"
                    )
            except ValueError as e:
                print(f"Error creating polygon for face with indices {indices}: {e}")
        else:
            print(
                f"Warning: Face with indices {indices} does not have enough points to form a polygon. Points: {points}"
            )
    return wkt_faces_with_names


# Extracting and converting data
wkt_points_with_names = get_cartesian_points(ifc_file)
wkt_lines_with_names = get_polylines(ifc_file)
wkt_surfaces_with_names = get_surfaces(ifc_file)
wkt_faces_with_names = get_indexed_polygonal_faces(ifc_file)

# Output all points, lines, and surfaces details
print("Points:")
for name, point in wkt_points_with_names:
    print(f"{name}: {point}")

print("Lines:")
for name, line in wkt_lines_with_names:
    print(f"{name}: {line}")

print("Surfaces:")
for name, surface in wkt_surfaces_with_names:
    print(f"{name}: {surface}")

print("Faces:")
for name, face in wkt_faces_with_names:
    print(f"{name}: {face}")

# Rendering the points and lines using matplotlib in 3D
fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")

# Plot points
for name, point in wkt_points_with_names:
    ax.scatter(point.x, point.y, point.z, color="red")

# Plot lines
for name, line in wkt_lines_with_names:
    x, y, z = zip(*line.coords)
    ax.plot(x, y, z, color="red")

# Plot surfaces (if represented as polygons)
for name, surface in wkt_surfaces_with_names:
    if isinstance(surface, Polygon):
        x, y = surface.exterior.xy
        z = [0] * len(x)  # Simplification for the z-coordinates
        if (
            len(x) > 2 and len(set(x)) > 1 and len(set(y)) > 1
        ):  # Check for valid coordinates
            ax.plot_trisurf(x, y, z, color="red", alpha=0.5)
        else:
            print(
                f"Warning: Surface {name} has degenerate coordinates and will not be plotted."
            )

# Plot indexed polygonal faces
for name, face in wkt_faces_with_names:
    if isinstance(face, Polygon):
        x, y = face.exterior.xy
        z = [0] * len(x)  # Simplification for the z-coordinates
        if (
            len(x) > 2 and len(set(x)) > 1 and len(set(y)) > 1
        ):  # Check for valid coordinates
            ax.plot_trisurf(x, y, z, color="red", alpha=0.5)
        else:
            print(
                f"Warning: Face {name} has degenerate coordinates and will not be plotted."
            )

# Set labels
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.set_title("IFC Geometries")

# Save the plot as a PNG file
plt.savefig("ifc_geometries_3d.png")
