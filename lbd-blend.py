import bpy
import rdflib
from rdflib.namespace import RDF


# Function to parse the Turtle file and extract detailed information
def parse_turtle_file(file_path):
    g = rdflib.Graph()
    g.parse(file_path, format="turtle")

    components = {}
    relationships = []

    for subj, pred, obj in g:
        subj = str(subj)
        pred = str(pred)
        obj = str(obj)

        if "RelocBridgeModel" in subj:
            if subj not in components:
                components[subj] = {"id": subj, "relations": []}

            if pred == RDF.type:
                components[subj]["type"] = obj
            elif pred == "http://example.org/hasPosition":
                components[subj]["position"] = [float(x) for x in obj.split(",")]
            elif pred == "http://example.org/hasDimensions":
                components[subj]["dimensions"] = [float(x) for x in obj.split(",")]
            elif pred.startswith("https://w3id.org/reloc#"):
                components[subj]["relations"].append((pred, obj))
                relationships.append((subj, pred, obj))

    return components, relationships


# Create specific 3D geometries for bridge components
def create_component_geometry(comp_id, comp_type, position, dimensions):
    if "Footing" in comp_id:
        bpy.ops.mesh.primitive_cube_add(size=2, location=position)
    elif "Abutment" in comp_id:
        bpy.ops.mesh.primitive_cube_add(size=3, location=position)
    elif "Joint" in comp_id:
        bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=position)
    elif "Girder" in comp_id:
        bpy.ops.mesh.primitive_cube_add(size=4, location=position)
    else:
        # Default geometry for unrecognized types
        bpy.ops.mesh.primitive_cube_add(size=1, location=position)

    obj = bpy.context.object
    obj.name = comp_id.split("#")[-1]

    if dimensions:
        obj.scale = [d / 2 for d in dimensions]

    return obj


# Create 3D model in Blender
def create_3d_model(components, relationships):
    component_objects = {}

    for comp_id, comp_data in components.items():
        name = comp_id.split("#")[-1]
        position = comp_data.get("position", [0, 0, 0])
        dimensions = comp_data.get("dimensions", [1, 1, 1])

        # Check if the component has a type, otherwise use a default
        comp_type = comp_data.get("type", "Default")

        obj = create_component_geometry(name, comp_type, position, dimensions)
        component_objects[comp_id] = obj

    # Handle relationships
    for subj, pred, obj in relationships:
        subj_obj = component_objects[subj]
        obj_obj = component_objects[obj]

        if pred == "https://w3id.org/reloc#meetBottom":
            # Position obj below subj
            obj_obj.location = subj_obj.location.copy()
            obj_obj.location.z -= subj_obj.dimensions.z / 2 + obj_obj.dimensions.z / 2
        elif pred == "https://w3id.org/reloc#equalTransversal":
            # Align obj transversally with subj
            obj_obj.location.x = subj_obj.location.x
            obj_obj.location.z = subj_obj.location.z


# Save the Blender model
def save_blender_model(output_file_path):
    bpy.ops.wm.save_as_mainfile(filepath=output_file_path)


# Main function to convert Turtle file to Blender 3D model
def main(turtle_file_path, blender_file_path):
    components, relationships = parse_turtle_file(turtle_file_path)
    create_3d_model(components, relationships)
    save_blender_model(blender_file_path)


# Set file paths
turtle_file_path = "/var/home/nat/LDAC/Outer-Space/Dataset/MaintenanceBridgeModel.ttl"
blender_file_path = "/var/home/nat/LDAC/Outer-Space/output/MaintenanceBridgeModel.blend"

# Run the conversion
main(turtle_file_path, blender_file_path)
