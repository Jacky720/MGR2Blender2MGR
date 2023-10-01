import traceback

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper


class ExportNierWmb(bpy.types.Operator, ExportHelper):
    '''Export a NieR:Automata WMB File'''
    bl_idname = "export.wmb_data"
    bl_label = "Export WMB File"
    bl_options = {'PRESET'}
    filename_ext = ".wmb"
    filter_glob: StringProperty(default="*.wmb", options={'HIDDEN'})

    centre_origins: bpy.props.BoolProperty(name="Centre Origins", description="This automatically centres the origins of all your objects. (Recommended)", default=True)
    triangulate_meshes: bpy.props.BoolProperty(name="Triangulate Meshes", description="This automatically adds and applies the Triangulate Modifier on all your objects. Only disable if you know your meshes are triangulated and you wish to reduce export times", default=True)
    delete_loose_geometry: bpy.props.BoolProperty(name="Delete Loose Geometry", description="This automatically runs the 'Delete Loose Geometry (All)' operator before exporting. It deletes all loose vertices or edges that could result in unwanted results in-game", default=True)
    delete_unused_vertexgroups: bpy.props.BoolProperty(name="Delete Unused Vertex Groups", description="This authomatically runs the 'Remove Unused Vertex Groups' operator before exporting. It removes all vertex groups (bone weights) which are not applied to any vertices on a mesh, which can reduce the number of bones per boneSet and avoid 'white-out' glitches", default=True)

    def execute(self, context):
        from . import wmb_exporter

        bpy.data.collections['WMB'].all_objects[0].select_set(True)

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

    def execute(self, context):
        from . import wmb_exporter

        bpy.data.collections['WMB'].all_objects[0].select_set(True)
        
        print("\n==== BEGIN WMB4 EXPORT ====")
        
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
            for mesh in [x for x in bpy.data.collections['WMB'].all_objects if x.type == "MESH"]:
                bpy.context.view_layer.objects.active = mesh
                bpy.ops.b2n.removeunusedvertexgroups()
            bpy.data.collections['WMB'].all_objects[0].select_set(True)
        
        try:
            print("Starting export...")
            wmb_exporter.main(self.filepath, True)
            return wmb_exporter.restore_blend()
        except:
            print(traceback.format_exc())
            self.report({'ERROR'}, "An unexpected error has occurred during export. Please check the console for more info.")
            return {'CANCELLED'}
