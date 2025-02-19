import traceback

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper
from ...utils.utilOperators import RipMeshByUVIslands

class ExportNierWmb(bpy.types.Operator, ExportHelper):
    '''Export a NieR:Automata WMB File'''
    bl_idname = "export.wmb_data"
    bl_label = "Export WMB File"
    bl_options = {'PRESET'}
    filename_ext = ".wmb"
    filter_glob: StringProperty(default="*.wmb", options={'HIDDEN'})

    rip_mesh_by_uv_islands: bpy.props.BoolProperty(name="Rip Mesh By UV Islands", description="Splits the mesh by 'island'd' UVs, which can fix texture issues (Recommended)", default=True)
    centre_origins: bpy.props.BoolProperty(name="Centre Origins", description="This automatically centres the origins of all your objects. (Recommended)", default=True)
    triangulate_meshes: bpy.props.BoolProperty(name="Triangulate Meshes", description="This automatically adds and applies the Triangulate Modifier on all your objects. Only disable if you know your meshes are triangulated and you wish to reduce export times", default=True)
    delete_loose_geometry: bpy.props.BoolProperty(name="Delete Loose Geometry", description="This automatically runs the 'Delete Loose Geometry (All)' operator before exporting. It deletes all loose vertices or edges that could result in unwanted results in-game", default=True)
    delete_unused_vertexgroups: bpy.props.BoolProperty(name="Delete Unused Vertex Groups", description="This authomatically runs the 'Remove Unused Vertex Groups' operator before exporting. It removes all vertex groups (bone weights) which are not applied to any vertices on a mesh, which can reduce the number of bones per boneSet and avoid 'white-out' glitches", default=True)

    def execute(self, context):
        from . import wmb_exporter

        bpy.data.collections['WMB'].all_objects[0].select_set(True)

        if self.rip_mesh_by_uv_islands:
            # TODO Add
            pass

        if self.centre_origins:
            print("Centering origins...")
            wmb_exporter.centre_origins("WMB")

        """
        if self.purge_materials:
            print("Purging materials...")
            wmb_exporter.purge_unused_materials()
        """

        if self.triangulate_meshes:
            print("Triangulating meshes...")
            wmb_exporter.triangulate_meshes("WMB")

        if self.delete_loose_geometry:
            print("Deleting loose geometry...")
            bpy.ops.b2n.deleteloosegeometryall()
        
        if self.delete_unused_vertexgroups:
            print("Deleting unused vertex groups...")
            bpy.ops.b2n.removeunusedvertexgroups()
        
        try:
            print("Starting export...")
            wmb_exporter.main(self.filepath)
            return wmb_exporter.restore_blend()
        except:
            print(traceback.format_exc())
            self.report({'ERROR'}, "An unexpected error has occurred during export. Please check the console for more info.")
            return {'CANCELLED'}

class ExportMGRRWmb(bpy.types.Operator, ExportHelper):
    '''Export a Metal Gear Rising: Revengeance WMB File'''
    bl_idname = "export.wmb_data"
    bl_label = "Export WMB File"
    bl_options = {'PRESET'}
    filename_ext = ".wmb"
    filter_glob: StringProperty(default="*.wmb", options={'HIDDEN'})

    centre_origins: bpy.props.BoolProperty(name="Centre Origins", description="This automatically centres the origins of all your objects. (Recommended)", default=True)
    triangulate_meshes: bpy.props.BoolProperty(name="Triangulate Meshes", description="This automatically adds and applies the Triangulate Modifier on all your objects. Only disable if you know your meshes are triangulated and you wish to reduce export times", default=True)
    delete_loose_geometry: bpy.props.BoolProperty(name="Delete Loose Geometry", description="This automatically runs the 'Delete Loose Geometry (All)' operator before exporting. It deletes all loose vertices or edges that could result in unwanted results in-game", default=True)
    delete_unused_vertexgroups: bpy.props.BoolProperty(name="Delete Unused Vertex Groups", description="This authomatically runs the 'Remove Unused Vertex Groups' operator before exporting. It removes all vertex groups (bone weights) which are not applied to any vertices on a mesh, which can reduce the number of bones per boneSet and avoid 'white-out' glitches", default=True)
    regenerate_slice_data: bpy.props.BoolProperty(name="Re-generate Slice Data", description="This attempts to modify the slice data (documented in custom properties of the WMB collection) to work with model modifications. Disable for minor texture edits that you wish to preserve the original data.", default=True)
    rip_mesh_by_uv_islands: bpy.props.BoolProperty(name="Rip Mesh By UV Islands", description="Splits the mesh by 'island'd' UVs, which can fix texture issues (Recommended)", default=True)
    def execute(self, context):
        from . import wmb_exporter

        wmbLayerCollection = bpy.context.view_layer.layer_collection.children['WMB']
        subCollection = [x for x in wmbLayerCollection.children if x.is_visible][0] # If this crashes, you disabled all the WMB sub-collections.
        subCollection.collection.all_objects[0].select_set(True)
        
        print("\n==== BEGIN WMB4 EXPORT ====")
        
        
        if self.rip_mesh_by_uv_islands:
            print("Ripping islands...")
            # TODO Add
        
        if self.centre_origins:
            print("Centering origins...")
            wmb_exporter.centre_origins("WMB")

        """
        if self.purge_materials:
            print("Purging materials...")
            wmb_exporter.purge_unused_materials()
        """

        if self.triangulate_meshes:
            print("Triangulating meshes...")
            wmb_exporter.triangulate_meshes("WMB")

        if self.delete_loose_geometry:
            print("Deleting loose geometry...")
            bpy.ops.b2n.deleteloosegeometryall()

        if self.delete_unused_vertexgroups:
            print("Deleting unused vertex groups...")
            for mesh in [x for x in subCollection.collection.all_objects if x.type == "MESH"]:
                bpy.context.view_layer.objects.active = mesh
                bpy.ops.b2n.removeunusedvertexgroups()
            subCollection.collection.all_objects[0].select_set(True)

        try:
            print("Starting export...")
            wmb_exporter.main(self.filepath, True, BALLIN=self.regenerate_slice_data)
            return wmb_exporter.restore_blend()
        except:
            print(traceback.format_exc())
            self.report({'ERROR'}, "An unexpected error has occurred during export. Please check the console for more info.")
            return {'CANCELLED'}
