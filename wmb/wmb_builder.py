import bpy

class MakeNewWMB(bpy.types.Operator):
    """Make a fresh mesh for editing"""
    bl_idname = "m2b.recalculateobjectindices"
    bl_label = "Make A New WMB Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        wmb_col = bpy.data.collections.new("WMB")
        wmb_col["mystery"]=False
        bpy.context.scene.collection.children.link(wmb_col)
        obj_col = bpy.data.collections.new("em0000")
        obj_col["vertexFormat"] = 65847
        wmb_col.children.link(obj_col)

        return {"FINISHED"}
