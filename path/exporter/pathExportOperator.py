import traceback

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper
from ...utils.utilOperators import RipMeshByUVIslands

class ExportMGRPath(bpy.types.Operator, ExportHelper):
    '''Export PATH Data.'''
    bl_idname = "export.path_data"
    bl_label = "Export PATH File"
    bl_options = {'PRESET'}
    filename_ext = ".bin"
    filter_glob: StringProperty(default="*.bin", options={'HIDDEN'})

    def execute(self, context):
        from .. import pathData

        pathData.export(self.filepath)

        return {'FINISHED'}
