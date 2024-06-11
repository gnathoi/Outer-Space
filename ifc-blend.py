import os

import bpy


# Function to import IFC file using BlenderBIM
def import_ifc(ifc_file_path):
    # Check if the file exists
    if not os.path.isfile(ifc_file_path):
        raise FileNotFoundError(f"IFC file not found: {ifc_file_path}")

    # Ensure the BlenderBIM add-on is enabled
    if not bpy.ops.bim.enable_addon("BlenderBIM"):
        raise RuntimeError("BlenderBIM add-on is not enabled")

    # Import the IFC file
    bpy.ops.bim.import_ifc(filepath=ifc_file_path)


# Set file paths
ifc_file_path = "/var/home/nat/LDAC/Outer-Space/Dataset/Modell_V2_IFC_4.ifc"
blender_file_path = "/var/home/nat/LDAC/Outer-Space/output/Modell_V2_IFC_4.blend"

# Import IFC file using BlenderBIM
import_ifc(ifc_file_path)

# Save the Blender model
bpy.ops.wm.save_as_mainfile(filepath=blender_file_path)
