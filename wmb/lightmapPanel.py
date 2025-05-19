import bpy

class B2MMakeLightmaps(bpy.types.Operator):
    bl_idname = "lmp.build_lightmap"
    bl_label = "Make Lightmap"
    bl_description = "Make Lightmap"

    def execute(self, context):
        scene = context.scene
        scene.render.engine = 'CYCLES'
        scene.cycles.bake_type = 'COMBINED'
        scene.cycles.samples = 64

        scene.render.bake.use_pass_direct = True
        scene.render.bake.use_pass_indirect = True
        scene.render.bake.use_pass_diffuse = True
        scene.render.bake.margin = 4

        prefs = bpy.context.preferences
        cprefs = prefs.addons['cycles'].preferences
        cprefs.compute_device_type = 'CUDA'  # or 'OPTIX' or 'METAL'
        for device in cprefs.devices:
            device.use = True
        scene.cycles.device = 'GPU'

        baked_count = 0
        print("LIGHTMAP BAKE START!")
        print("(C) GAMING WITH PORTALS - 2025")
        triedCount = 0
        meshCount = 0
        for col in bpy.data.collections.get("WMB").children:
            for obj in col.objects:
                if (obj.type == 'MESH'):
                    meshCount+=1


        for col in bpy.data.collections.get("WMB").children:
            for obj in col.objects:
                if (obj.type != 'MESH'):
                    continue
                else:
                    bpy.context.view_layer.objects.active = obj
                    mat = obj.active_material
                    nodes = mat.node_tree.nodes
                    image_node = None
                    for node in nodes:
                        if node.type == 'TEX_IMAGE' and "lightmap" in node.name.lower():
                            image_node = node
                            break
                    nodes.active = image_node

                    print("Baking: " + obj.name + " (" + str(triedCount) + "/" + str(meshCount) + "..." + str((triedCount / meshCount) * 100.0) + "%)")
                    triedCount+=1
                    try:
                        bpy.ops.object.bake(type='COMBINED')
                        baked_count += 1
                    except Exception as e:
                        self.report({'ERROR'}, f"Bake failed on {obj.name}: {e}")

        self.report({'INFO'}, f"Rebaked lightmaps on {baked_count} objects.")
        return {'FINISHED'}


class B2MLightmapEditor(bpy.types.Panel):
    bl_label = "MGR:Revengeance Lighting Editor"
    bl_idname = "B2M_PT_LightingEditorToplevel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MGR:R Lighting Editor"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("lmp.build_lightmap", text="Build Lightmap")