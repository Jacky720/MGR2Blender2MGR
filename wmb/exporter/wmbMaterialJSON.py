# wmbMaterialJSON.py
import bpy, json, idprop

def get_materials(self, context):
    return [(mat.name, mat.name, "") for mat in bpy.data.materials]

class WMBMaterialToJSON(bpy.types.Operator):
    bl_idname = "b2n.materialtojson"
    bl_label = "Store Material As JSON"
    
    def execute(self, context):
        material = bpy.context.material
        textureArray = []
        parameterArray = []
        
        for index in range(len(material.mgr_data.textures)):
            textureObject = material.mgr_data.textures[index]
            textureArray.append(textureObject)

        for param in material.mgr_data.parameters:
            parameterObject = {
                "x": param.value[0],
                "y": param.value[1],
                "z": param.value[2],
                "w": param.value[3]
            }

            parameterArray.append(parameterObject)
        
        
        dictForString = {
            "shaderID" : str(material.mgr_data.shader_name),
            "textures" : textureArray,
            "parameters":parameterArray
        }
        

        material["wmb_mat_as_json"] = json.dumps(dictForString)
        bpy.context.window_manager.clipboard = bpy.context.material["wmb_mat_as_json"]
        self.report({'INFO'}, "Copied JSON")
        return {'FINISHED'}

class WMBMaterialFromJSON(bpy.types.Operator):
    bl_idname = "b2n.jsontomaterial"
    bl_label = "Load Material From JSON"
    
    def execute(self, context):
        material = bpy.context.material
        bpy.context.material["wmb_mat_as_json"] = bpy.context.window_manager.clipboard
        try:
            dictFromString = json.loads(material["wmb_mat_as_json"])
        except:
            self.report({'ERROR'}, "Invalid JSON")
            return {'FINISHED'}
        
        # clear custom properties
        material.mgr_data.textures.clear()
        material.mgr_data.parameters.clear()
        material.mgr_data.shader_name = ""
        
        dictFromString = json.loads(material["wmb_mat_as_json"])
        material.mgr_data.shader_name = dictFromString["shaderID"]
        for texture in dictFromString["textures"]:
            entry = material.mgr_data.textures.add()  
            entry.flag = texture["flag"]
            entry.id = texture["id"] 
        
        for i, param in enumerate(dictFromString["parameters"]):
            material.mgr_data.parameters.add()
            material.mgr_data.parameters[i].value = (param["x"], param["y"], param["z"], param["w"])
        
        self.report({'INFO'}, "Pasted JSON")
        return {'FINISHED'}


class WMBCopyMaterialJSON(bpy.types.Operator):
    # TODO Delete
    bl_idname = "b2n.copymaterialjson"
    bl_label = "Copy Material JSON"
    
    def execute(self, context):
        bpy.context.window_manager.clipboard = bpy.context.material["wmb_mat_as_json"]
        return {'FINISHED'}

class WMBPasteMaterialJSON(bpy.types.Operator):
    # TODO: Delete
    bl_idname = "b2n.pastematerialjson"
    bl_label = "Paste Material JSON"
    
    def execute(self, context):
        bpy.context.material["wmb_mat_as_json"] = bpy.context.window_manager.clipboard
        return {'FINISHED'}

class WMBMaterialJSONPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = 'material'
    bl_label = "MGRR Material Copy"

    def draw(self, context):
        layout = self.layout
        layout.operator(WMBMaterialToJSON.bl_idname, text="Copy Material")
        
        if hasattr(bpy.context.material, "wmb_mat_as_json"):
            layout.prop(context.material, "wmb_mat_as_json")
        
        layout.operator(WMBMaterialFromJSON.bl_idname, text="Paste Material")