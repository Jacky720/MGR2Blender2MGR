import bpy
from ...consts import *




class MGRTextureFlagProperty(bpy.types.PropertyGroup):
    value: bpy.props.IntProperty(name="Texture Flag")

class MGRMaterialProperty(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Property Name")
    value: bpy.props.StringProperty(name="Value")

class MGRULTextureFlagPanel(bpy.types.UIList):
    bl_idname = "MGR_UL_texture_flags"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if item:
            layout.prop(item, "value", text="")

def GrabTextureNameViaFlag(id):
    if (id in textureFlagDictonary):
        return str(textureFlagDictonary.get(id))
    else:
        return "tex" + str(id)




class MGRMaterialPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = 'material'
    bl_label = "MGRR Material Properties"
    bl_idname = "MATERIAL_PT_mgr_material"
    
    def draw(self, context):
        layout = self.layout
        mat = context.material
        layout.prop(mat, "mgr_material_id", text="Material ID")
        layout.prop(mat, "mgr_shader_name", text="Shader Name")


        propbox = layout.box()
        propbox.label(text="Parameters")
        i = 0
        
        for mgrprop in mat.mgr_parameters:
            subbox = propbox.row()
            param_identifier = str(i)
            if (i in parameterIDs):
                param_identifier = parameterIDs[i]
            
            
            subbox.prop(mgrprop, "value", text=str(param_identifier))
            i+=1
        
        
        
        row = layout.row()
        row.template_list(
            "MGR_UL_TextureIDList",  # Name of the UI List class (defined below)
            "", 
            mat, "mgr_texture_ids",  # Collection property
            mat, "mgr_texture_flags_index"  # Active item index property
        )
        box = layout.box()
        box.label(text="Texture File Reference")
        # Draw individual texture properties if an item is selected
        for i in range(len(mat.mgr_texture_flags)):
            active_entry = mat.mgr_texture_ids[i]
            
            generatedTextureFlagName = GrabTextureNameViaFlag(mat.mgr_texture_flags[i].value)
            
            box.prop(active_entry, "value", text=generatedTextureFlagName)  # Text reflects the name propert
        
        