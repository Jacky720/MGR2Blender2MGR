# wmbMaterialJSON.py
import bpy, json, idprop

class WMBMaterialToJSON(bpy.types.Operator):
    bl_idname = "b2n.materialtojson"
    bl_label = "Store Material As JSON"
    
    def execute(self, context):
        material = bpy.context.material
        textureArray = []
        parameterArray = []
        
        for index in range(len(material.mgr_texture_ids)):
            textureObject = {"id":material.mgr_texture_ids[index].value,
                             "flag":material.mgr_texture_flags[index].value}
            textureArray.append(textureObject)

        for param in material.mgr_parameters:
            parameterObject = {
                "x": param.value[0],
                "y": param.value[1],
                "z": param.value[2],
                "w": param.value[3]
            }

            parameterArray.append(parameterObject)
        
        
        dictForString = {
            "shaderID" : str(material.mgr_shader_name),
            "textures" : textureArray,
            "parameters":parameterArray
        }
        

        material["wmb_mat_as_json"] = json.dumps(dictForString)
        return {'FINISHED'}

class WMBMaterialFromJSON(bpy.types.Operator):
    bl_idname = "b2n.jsontomaterial"
    bl_label = "Load Material From JSON"
    
    def execute(self, context):
        material = bpy.context.material
        # clear custom properties
        keys = list(material.keys())
        for key in keys:
            if key not in ["wmb_mat_as_json", "ID"]:
                del material[key]
        
        dictFromString = json.loads(material["wmb_mat_as_json"])
        for item in dictFromString:
            key, value = item[0], item[1]
            material[key] = value
            
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
        
        layout.prop(bpy.context.material, "wmb_mat_as_json")
        
        layout.operator(WMBMaterialFromJSON.bl_idname, text="Paste Material")