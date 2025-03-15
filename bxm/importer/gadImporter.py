import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from ...utils.visibilitySwitcher import enableVisibilitySelector
from ...utils.util import setExportFieldsFromImportFile

class ImportMGRGad(bpy.types.Operator, ImportHelper):
    '''Import GAD Data.'''
    bl_idname = "import_scene.gad_data"
    bl_label = "Import GAD Data"
    bl_options = {'PRESET'}
    filename_ext = ".gad"
    filter_glob: StringProperty(default="*.gad", options={'HIDDEN'})

    reset_blend: bpy.props.BoolProperty(name="Reset Blender Scene on Import", default=True)

    def execute(self, context):
        GADTree = bpy.data.collections.new("GAD")
        
        from ...bxm.common.bxm import bxmToXml
        import xml.etree.ElementTree as ET

        bxmroot = bxmToXml(self.filepath)
        worknos = bxmroot.findall(".//Work")
        workidx = 0
        for work in worknos:
            wid = work.find("No")
            wcol = bpy.data.collections.new(str(wid.text))
            filterchunk = work.find("Filter")
            flagdata = filterchunk.find("flag")
            pntdata = filterchunk.find("pnt")

            filterflags = []
            for flagobj in flagdata.findall("value"):
                filterflags.append(str(flagobj.text))
            
            pntFlags = []
            for flagobj in pntdata.findall("value"):
                pntFlags.append(int(flagobj.text))
            
            wcol["flags"] = filterflags
            wcol["pointNum"] = int(filterchunk.find("pointNum").text)
            wcol["pnt"] = pntFlags

            GADTree.children.link(wcol)

            if workidx != 0:
                wcol.hide_viewport = True

            workidx+=1

        bpy.context.scene.collection.children.link(GADTree)

        return {'FINISHED'}
