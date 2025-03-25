import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from ...utils.visibilitySwitcher import enableVisibilitySelector
from ...utils.util import setExportFieldsFromImportFile


class ImportMGRPath(bpy.types.Operator, ImportHelper):
    '''Import PATH Data.'''
    bl_idname = "import_scene.path_data"
    bl_label = "Import PATH Data"
    bl_options = {'PRESET'}
    filename_ext = ".bin"
    filter_glob: StringProperty(default="*.bin", options={'HIDDEN'})

    reset_blend: bpy.props.BoolProperty(name="Reset Blender Scene on Import", default=True)

    def execute(self, context):
        from .. import pathData
        

        setExportFieldsFromImportFile(self.filepath, False)
        enableVisibilitySelector()

        pathData.main(self.filepath)
        
        
        
        return {'FINISHED'}
