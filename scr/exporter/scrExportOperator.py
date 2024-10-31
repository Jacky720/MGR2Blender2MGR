import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper

#from ...utils.visibilitySwitcher import enableVisibilitySelector
#from ...utils.util import setExportFieldsFromImportFile


class ExportSCR(bpy.types.Operator, ExportHelper):
    '''Export a MGR SCR File.'''
    bl_idname = "export.scr_data"
    bl_label = "Export SCR Data"
    bl_options = {'PRESET'}
    filename_ext = ".scr"
    filter_glob: StringProperty(default="*.scr", options={'HIDDEN'})

    export_ly2: bpy.props.BoolProperty(name="Export LY2 prop file", default=False)

    def execute(self, context):
        from . import scr_exporter

        #setExportFieldsFromImportFile(self.filepath, False)
        #enableVisibilitySelector()
        
        return scr_exporter.main(self.filepath, self.export_ly2)
        #
