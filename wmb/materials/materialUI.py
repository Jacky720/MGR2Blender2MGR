import bpy

textureFlagDictonary = {
    0 : "Albedo 0",
    1 : "Albedo 1",
    2 : "Normal",
    3 : "Blended Normal",
    7 : "Light Map",
    10 : "Tension Map"
}


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
        
        layout.label(text="Texture Flags:")
        row = layout.row()
        row.template_list("MGR_UL_texture_flags", "", mat, "mgr_texture_flags", mat, "mgr_texture_flags_index")
        
        layout.label(text="Texture IDs:")
        row = layout.row()
        row.template_list(
            "MGR_UL_TextureIDList",  # Name of the UI List class (defined below)
            "", 
            mat, "mgr_texture_ids",  # Collection property
            mat, "mgr_texture_flags_index"  # Active item index property
        )

        # Draw individual texture properties if an item is selected
        for i in range(len(mat.mgr_texture_flags)):
            active_entry = mat.mgr_texture_ids[i]
            
            generatedTextureFlagName = GrabTextureNameViaFlag(mat.mgr_texture_flags[i].value)
            
            layout.prop(active_entry, "value", text=generatedTextureFlagName)  # Text reflects the name propert