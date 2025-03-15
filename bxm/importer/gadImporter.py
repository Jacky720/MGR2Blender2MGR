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
            wcol["saido"] = list(map(float, filterchunk.find("saido").text.split()))
            wcol["color"] = list(map(float, filterchunk.find("color").text.split()))
            wcol["bgColor"] = list(map(float, filterchunk.find("bgColor").text.split()))
            wcol["glareColor"] = list(map(float, filterchunk.find("glareColor").text.split()))
            wcol["addColor"] = list(map(float, filterchunk.find("addColor").text.split()))
            wcol["hdr_range"] = float(filterchunk.find("hdr_range").text)
            wcol["kido_base"] = float(filterchunk.find("kido_base").text)
            wcol["kido_range"] = float(filterchunk.find("kido_range").text)
            wcol["kido_min"] = float(filterchunk.find("kido_min").text)
            wcol["kido_max"] = float(filterchunk.find("kido_max").text)
            wcol["saido_range"] = float(filterchunk.find("saido_range").text)
            wcol["kido_spd"] = float(filterchunk.find("kido_spd").text)
            wcol["glareRange"] = float(filterchunk.find("glareRange").text)
            wcol["glareRangeAlphaMul"] = float(filterchunk.find("glareRangeAlphaMul").text)
            
            lightContainer = work.find("light")
            
            lightWork = lightContainer.find(".//prop[@name='m_RoomLightWork']")

            lightidx = 0
            for light in lightWork.findall("value"):
                light_string = "Light_" + str(workidx) + "_" + str(lightidx)
                light_data = bpy.data.lights.new(name=light_string, type='POINT')
                light_object = bpy.data.objects.new(name=light_string, object_data=light_data)
                wcol.objects.link(light_object)
                
                lightidx+=1
                
                for prop in light.findall("prop"):
                    name = prop.get("name")
                    value = prop.text

                    if name == "m_flag":
                        light_object["m_flag"] = int(value)
                    elif name == "m_priority":
                        light_object["m_priority"] = int(value)
                    elif name == "m_applyFlag":
                        light_object["m_applyFlag"] = int(value)
                    elif name == "m_lightType":
                        light_object["m_lightType"] = int(value)
                    
                    elif name == "m_pos":
                        m_pos = list(map(float, value.split()))  # Convert space-separated values to a list of floats
                        light_object.location = (m_pos[0], -m_pos[2], m_pos[1] ) # X, -Z, Y
                    elif name == "m_color":
                        m_color = list(map(float, value.split()))
                        light_data.color = (m_color[0], m_color[1], m_color[2])
                        light_data.energy = (m_color[3] * 100)
                
            
            
            GADTree.children.link(wcol)

            if workidx != 0:
                pass
                #wcol.hide_viewport = True

            workidx+=1

        bpy.context.scene.collection.children.link(GADTree)

        return {'FINISHED'}
