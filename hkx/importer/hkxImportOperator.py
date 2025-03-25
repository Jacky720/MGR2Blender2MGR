import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from ...utils.visibilitySwitcher import enableVisibilitySelector
from ...utils.util import setExportFieldsFromImportFile


class ImportMGRHavokPackfile(bpy.types.Operator, ImportHelper):
    '''Import HKX Data.'''
    bl_idname = "import_scene.hkxpak"
    bl_label = "Import HKX Data"
    bl_options = {'PRESET'}
    filename_ext = ".hkx"
    filter_glob: StringProperty(default="*.hkx", options={'HIDDEN'})

    reset_blend: bpy.props.BoolProperty(name="Reset Blender Scene on Import", default=True)

    def execute(self, context):
        setExportFieldsFromImportFile(self.filepath, False)
        enableVisibilitySelector()
        
        from .. import Havok
        Havok.ImportHKXFile(self.filepath)
        
        return {'FINISHED'}
        

class ImportMGRHavokTagfile(bpy.types.Operator, ImportHelper):
    '''Import HKX Data.'''
    bl_idname = "import_scene.hkxtag"
    bl_label = "Import HKX Data"
    bl_options = {'PRESET'}
    filename_ext = ".xml"
    filter_glob: StringProperty(default="*.xml", options={'HIDDEN'})

    reset_blend: bpy.props.BoolProperty(name="Reset Blender Scene on Import", default=True)

    def execute(self, context):
        setExportFieldsFromImportFile(self.filepath, False)
        enableVisibilitySelector()

