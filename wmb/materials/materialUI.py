import bpy
from ...consts import *
from ...utils.util import MGRVector4Property
from ...utils.util import crc32

# TODO: More material presets
# TODO: Add picker for presets
materialPresets = {
    "basic": {
        "name": "Basic",
        "desc": "Basic preset that is generally used on characters and weapons",

        "shader": "ois00_xbxeX",
        "textures": [
            {"id": "0", "flag": 0},
            {"id": "0", "flag": 1},
            {"id": "0", "flag": 2},
            {"id": "0", "flag": 3}
        ],
        "parameters": [
            (0.5, 0.5, 0.5,  -1.0),
            (0.5, 0.0, 40.0,  1.0),
            (1.0, 0.0, 0.0,  -1.0),
            (1.0, 1.0, -1.0, -1.0)
        ]
    },
    "skin": {
        "name": "Skin",
        "desc": "Preset that is used for skin (eg. Raiden's/Sam's Face)",

        "shader": "skn20_xbXxX",
        "textures": [
            {"id": "0", "flag": 0},
            {"id": "0", "flag": 1},
            {"id": "0", "flag": 2},
            {"id": "0", "flag": 3},
            {"id": "0", "flag": 4},
            {"id": "0", "flag": 5}
        ],
        "parameters": [
            (0.5,  0.5,  0.5,  -1.0),
            (0.8,  0.97, 50.0, 1.0 ),
            (1.0,  0.0,  -1.0, -1.0),
            (0.0,  0.0,  0.0,  0.0 ),
            (0.5,  -1.0, -1.0, -1.0),
            (10.0, 15.0, 2.0,  -1.0),
            (1.0,  1.0,  -1.0, -1.0),
        ]
    }
}

class MGRMaterialProperty(bpy.types.PropertyGroup):
    flag: bpy.props.IntProperty(name="Texture Flag")
    id: bpy.props.StringProperty(name="Texture ID")

def material_presets(self, context):
    return [
        (key, materialPresets[key]["name"], materialPresets[key]["desc"])
        for key in materialPresets.keys()
    ]

class MGRMaterialDataProperty(bpy.types.PropertyGroup):
    id: bpy.props.IntProperty(
        name="Material ID",
        description="Unique Material Index",
        default=-1
    )

    shader_name: bpy.props.StringProperty(
        name="Shader Name",
        description="Shader used by this material"
    )

    material_preset: bpy.props.EnumProperty(items=material_presets, default=0)
    
    textures: bpy.props.CollectionProperty(type=MGRMaterialProperty)
    parameters: bpy.props.CollectionProperty(type=MGRVector4Property)

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

class MGRMaterialCreateOperator(bpy.types.Operator):
    '''Creates an export-ready material.'''
    bl_idname = "materialui.creatematerial"
    bl_context = 'material'
    bl_label = "New Basic Material"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        material = bpy.context.material
        
        preset = material.mgr_data.material_preset

        material.mgr_data.parameters.clear()
        material.mgr_data.shader_name = materialPresets[preset]["shader"]
        
        for texture in materialPresets[preset]["textures"]:
            if not any(tex.flag == texture["flag"] for tex in material.mgr_data.textures):        
                entry = material.mgr_data.textures.add()
                entry.flag = texture["flag"]
                entry.id = texture["id"]
        
        for i, param in enumerate(materialPresets[preset]["parameters"]):
            material.mgr_data.parameters.add()
            material.mgr_data.parameters[i].value = (param[0], param[1], param[2], param[3])
        return {'FINISHED'}

class MGRMaterialPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = 'material'
    bl_label = "MGRR Material Properties"
    bl_idname = "MATERIAL_PT_mgr_material"

    def draw(self, context):
        layout = self.layout
        mat = context.material

        if mat is None:
            layout.label("Select a material first")
            return

        layout.prop(mat.mgr_data, "id", text="Material ID")
        layout.prop(mat.mgr_data, "shader_name", text="Shader Name")

        propbox = layout.box()
        propbox.label(text="Parameters")
        
        for i, mgrprop in enumerate(mat.mgr_data.parameters):
            subbox = propbox.row()
            param_identifier = str(i)
            if (i in parameterIDs):
                param_identifier = parameterIDs[i]
            
            subbox.prop(mgrprop, "value", text=str(param_identifier))

        box = layout.box()
        box.label(text="Texture File Reference")
        # Draw individual texture properties if an item is selected
        for i in range(len(mat.mgr_data.textures)):
            active_entry = mat.mgr_data.textures[i]
            
            generatedTextureFlagName = GrabTextureNameViaFlag(int(mat.mgr_data.textures[i].flag))
            
            box.prop(active_entry, "id", text=generatedTextureFlagName)  # Text reflects the name propert
        
        box = layout.box()
        row = box.row()
        row.prop(mat.mgr_data, "material_preset", text="Preset")
        row.operator(MGRMaterialCreateOperator.bl_idname)

classes = (
    MGRMaterialProperty,
    MGRMaterialDataProperty,

    MGRMaterialCreateOperator,
    MGRMaterialPanel,
    MGRULTextureFlagPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Material.mgr_data = bpy.props.PointerProperty(type=MGRMaterialDataProperty)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Material.mgr_data