# load from Python object into Blender (way too many custom properties)
from time import time
import bpy
import bmesh
import math
from typing import List, Tuple
from mathutils import Vector, Matrix
from .bonenames import wmb4_bonenames

from ...utils.util import ShowMessageBox, getPreferences, printTimings
from .wmb import *
from ...wta_wtp.exporter.wta_wtp_ui_manager import makeWtaMaterial
from ..materials import materialBuilder 


def reset_blend():
    #bpy.ops.object.mode_set(mode='OBJECT')
    for collection in bpy.data.collections:
        for obj in collection.objects:
            collection.objects.unlink(obj)
        bpy.data.collections.remove(collection)
    for bpy_data_iter in (bpy.data.objects, bpy.data.meshes, bpy.data.lights, bpy.data.cameras, bpy.data.libraries):
        for id_data in bpy_data_iter:
            bpy_data_iter.remove(id_data)
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)
    for amt in bpy.data.armatures:
        bpy.data.armatures.remove(amt)
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj)
        obj.user_clear()

def construct_armature(name, bone_data_array, firstLevel, secondLevel, thirdLevel, boneMap, boneSetArray, collection_name, transform=None):            # bone_data =[boneIndex, boneName, parentIndex, parentName, bone_pos, optional, boneNumber, localPos, local_rotation, world_rotation, world_position_tpose]
    print('[+] importing armature')
    amt = bpy.data.armatures.new(name +'Amt')
    ob = bpy.data.objects.new(name, amt)
    #ob = bpy.context.active_object
    if getPreferences().armatureDefaultDisplayType != "DEFAULT":
        amt.display_type = getPreferences().armatureDefaultDisplayType
    ob.show_in_front = getPreferences().armatureDefaultInFront
    ob.name = name
    bpy.data.collections.get(collection_name).objects.link(ob)

    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')
     
    amt['firstLevel'] = firstLevel
    amt['secondLevel'] = secondLevel
    amt['thirdLevel'] = thirdLevel
    
    if boneMap is not None:
        amt['boneMap'] = boneMap

    amt['boneSetArray'] = boneSetArray
    #print([bone[1] for bone in bone_data_array])
    
    for bone_data in bone_data_array:
        #print(bone_data[1])
        bone = amt.edit_bones.new(bone_data[1])
        #print("Creating bone", bone.name)
        bone.head = Vector(bone_data[4]) #- Vector((0 , 0.01, 0))  
        bone.tail = Vector(bone_data[4]) + Vector((0 , 0.01, 0))                
        bone['ID'] = bone_data[6]

        #bone['localPosition'] = bone_data[7]
        bone['localRotation'] = bone_data[8]
        #bone['worldRotation'] = bone_data[9]
        #bone['TPOSE_worldPosition'] = bone_data[10]

    bones = amt.edit_bones
    for bone_data in bone_data_array:
        if bone_data[2] != -1:
            #print(bone_data[1])
            bone = bones[bone_data[1]]
            bone.parent = bones[bone_data[3]]
            # this doesn't work on animations but i like it so fixing in the tpose code
            if bone.parent.tail == bone.parent.head + Vector((0, 0.01, 0)):
                bone.parent.tail = bone.head
                dist = bone.parent.head - bone.parent.tail
                if abs(dist.x) + abs(dist.y) + abs(dist.z) < 0.01:
                    bone.parent.tail += Vector((0, 0.01, 0))
    
    # mot posing stuff
    bpy.ops.object.mode_set(mode='POSE')

    for pose_bone in ob.pose.bones:
        #print("Posing", pose_bone.name)
        rot_mat = Matrix.Rotation(pose_bone.bone["localRotation"][2], 4, 'Z') @ Matrix.Rotation(pose_bone.bone["localRotation"][1], 4, 'Y') @ Matrix.Rotation(pose_bone.bone["localRotation"][0], 4, 'X')

        pose_bone.matrix_basis = rot_mat @ pose_bone.matrix_basis
        bpy.context.view_layer.update()

    bpy.ops.pose.armature_apply()

    for pose_bone in ob.pose.bones:
        rot_mat = Matrix.Rotation(pose_bone.bone["localRotation"][2], 4, 'Z') @ Matrix.Rotation(pose_bone.bone["localRotation"][1], 4, 'Y') @ Matrix.Rotation(pose_bone.bone["localRotation"][0], 4, 'X')

        pose_bone.matrix_basis = rot_mat.inverted() @ pose_bone.matrix_basis
        bpy.context.view_layer.update()
    
    #for bone in amt.edit_bones:
    #    if bone.tail == bone.head + Vector((0, 0.01, 0)):
    #        bone.tail = bone.head
    #        bone.head = bone.parent.head
    
    #for bone_data in bone_data_array:
    #    if bone_data[6] > len(bones):
    #        bones[bone_data[1]].name = "fakeBone%d" % bone_data[6]
    
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.rotation_euler = (math.radians(90),0,0)
    if transform is not None:
        ob.location = Vector((transform[0], -transform[2], transform[1]))
        ob.rotation_euler = (math.radians(90) + transform[3], transform[5], transform[4])
        ob.scale = Vector((transform[6], transform[8], transform[7]))
    
    # split armature
    return ob

def split_armature(name):
    amt = bpy.data.armatures[name]
    name = name.replace('Amt','')
    bones = amt.bones
    root_bones = [bone for bone in bones if not bone.parent]
    for i in range(len(root_bones)):
        bpy.ops.object.add(
            type='ARMATURE', 
            enter_editmode=True,
            location=(i * 2,0,0))
        ob_new = bpy.context.object
        ob_new.show_x_ray = False
        ob_new.name = "%s_%d" % (name, i)
        amt_new = ob_new.data
        amt_new.name = '%s_%d_Amt' % (name, i)
        copy_bone_tree(root_bones[i] ,amt_new)
        bpy.ops.object.mode_set(mode="OBJECT")
        ob_new.rotation_euler = (math.radians(90),0,0)
    bpy.ops.object.select_all(action="DESELECT")
    obj = bpy.data.objects[name]
    scene = bpy.context.scene
    scene.objects.unlink(obj)
    return False

def copy_bone_tree(source_root, target_amt):
    bone = target_amt.edit_bones.new(source_root.name)
    bone.head = source_root.head_local
    bone.tail = source_root.tail_local
    if source_root.parent:
        bone.parent = target_amt.edit_bones[source_root.parent.name]
    for child in source_root.children:
        copy_bone_tree(child, target_amt)

def construct_mesh(mesh_data, collection_name):
    # [meshName, vertices, faces, has_bone,
    #  boneWeightInfoArray, boneSetIndex, meshGroupIndex, vertex_colors,
    #  LOD_name, LOD_level, colTreeNodeIndex, unknownWorldDataIndex,
    #  boundingBox, vertexGroupIndex, batchID?, materialArray?,
    #  boneSet?, vertexStart?, batchGroup?, wmb4_transform?,
    #  vertexCount?, normals?], collection_name
    name = mesh_data[0]
    matched_objs = 0
    for obj in bpy.data.objects:
        if len(obj.name.split("-")) > 2:
            truename = obj.name.split("-")
            truename.pop()
            truename = "-".join(truename) # i love loose typing
        else:
            truename = obj.name
        if truename == name:
            matched_objs += 1
    # i'd prefer to avoid the numbers when there's only one mesh, but it's
    # basically impossible to tell once the names contain hyphens
    name += "-%d" % matched_objs
    vertices = mesh_data[1]
    faces = mesh_data[2]
    has_bone = mesh_data[3]
    normals = mesh_data[21] if len(mesh_data) > 21 else None
    weight_infos = [[[],[]]] # A real fan can recognize me even I am a 2 dimensional array
    print("[+] importing %s" % name)
    objmesh = bpy.data.meshes.new(name)
    if not name in bpy.data.objects.keys(): 
        obj = bpy.data.objects.new(name, objmesh)
    else:
        obj = bpy.data.objects[name] # what??
    obj.location = Vector((0,0,0))
    bpy.data.collections.get(collection_name).objects.link(obj)
    objmesh.from_pydata(vertices, [], faces)
    if normals is not None:
        objmesh.normals_split_custom_set_from_vertices(normals)
    objmesh.update(calc_edges=True)

    if len(mesh_data[7]) != 0:
        if objmesh.vertex_colors:
            vcol_layer = objmesh.vertex_colors.active
        else:
            vcol_layer = objmesh.vertex_colors.new()
        
        for loop_idx, loop in enumerate(objmesh.loops):
            meshColor = vcol_layer.data[loop_idx]
            dataColor = mesh_data[7][loop.vertex_index]
            meshColor.color = [
                dataColor[0]/255,
                dataColor[1]/255,
                dataColor[2]/255,
                dataColor[3]/255
            ]
            

    if has_bone:
        weight_infos = mesh_data[4]
        group_names = sorted(list(set(["bone%d" % i  for weight_info in weight_infos for i in weight_info[0]])))
        for group_name in group_names:
            obj.vertex_groups.new(name=group_name)
        for i, weightinfo in enumerate(weight_infos):
            for index in range(4):
                group_name = "bone%d"%weightinfo[0][index]
                weight = weightinfo[1][index]
                group = obj.vertex_groups[group_name]
                if weight:
                    group.add([i], weight, "REPLACE")
    obj.rotation_euler = (math.radians(90),0,0)
    if mesh_data[5] != "None":
        obj['boneSetIndex'] = mesh_data[5]
    obj['meshGroupIndex'] = mesh_data[6]
    if len(mesh_data) <= 14: # let's only do these in WMB3
        obj['LOD_Name'] = mesh_data[8]
        obj['LOD_Level'] = mesh_data[9]
        obj['colTreeNodeIndex'] = mesh_data[10]
        obj['unknownWorldDataIndex'] = mesh_data[11]
        # this one is in both but we have it in the name
        obj['vertexGroup'] = mesh_data[13]
    if len(mesh_data) > 14: # wmb4
        obj['ID'] = mesh_data[14]
        obj['batchGroup'] = mesh_data[18]
        # can't ditch these two, they're used later during import
        obj['Materials'] = mesh_data[15]
        obj['VertexIndexStart'] = mesh_data[17]
        obj['VertexIndexCount'] = mesh_data[20]
        if mesh_data[19] is not None: # scr import
            transform = mesh_data[19]
            #print(mesh_data[19])
            obj.location = Vector((transform[0], -transform[2], transform[1]))
            obj.rotation_euler = (math.radians(90) + transform[3], transform[5], transform[4])
            obj.scale = Vector((transform[6], transform[7], transform[8]))

    # obj.data.flip_normals()
    
    return obj

def set_partent(parent, child):
    bpy.context.view_layer.objects.active = parent
    child.select_set(True)
    parent.select_set(True)
    bpy.ops.object.parent_set(type="ARMATURE")
    child.select_set(False)
    parent.select_set(False)

def addWtaExportMaterial(texture_dir, material):
    material_name = material[0]
    textures = material[1]
    wtaTextures: List[Tuple[int, str, str]] = [
        (int(flag), id, os.path.join(texture_dir, f"{id}.dds"))
        for flag, id in textures.items()
    ]
    makeWtaMaterial(material_name, wtaTextures)

def construct_materials(texture_dir, material, material_index=-1):
    material_name = material[0]
    textures = material[1]
    uniforms = material[2]
    shader_name = material[3]
    parameterGroups = material[4]
    print('[+] importing material %s' % material_name)
    
    material = bpy.data.materials.new( '%s' % (material_name))
    material.mgr_data.id = material_index
    material.mgr_data.shader_name = shader_name
    
    for tex_flag, tex_id in textures.items():
        entry = material.mgr_data.textures.add()  
        entry.flag = tex_flag
        entry.id = str(tex_id)
    
    for i, parameter in enumerate(parameterGroups):
        material.mgr_data.parameters.add()
        material.mgr_data.parameters[i].value = (parameter.x, parameter.y, parameter.z, parameter.w)
    
    materialBuilder.buildMaterialNodes(material, uniforms)
    return material
    # Enable Nodes
    material.use_nodes = True
    # Clear Nodes and Links
    material.node_tree.links.clear()
    material.node_tree.nodes.clear()
    # Recreate Nodes and Links with references
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    # PrincipledBSDF and Ouput Shader
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = 1200,0
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = 900,0
    output_link = links.new( principled.outputs['BSDF'], output.inputs['Surface'] )
    # Normal Map Amount Counter
    normal_map_count = 0
    # Mask Map Count
    mask_map_count = 0
    # Alpha Channel
    material.surface_render_method = 'DITHERED'

    #print("\n".join(["%s:%f" %(key, uniforms[key]) for key in sorted(uniforms.keys())]))
    # Shader Parameters
    for key in uniforms.keys():
        material[key] = uniforms.get(key)
        #print(key, material[key])
        if key.lower().find("g_glossiness") > -1:
            principled.inputs['Roughness'].default_value = 1 - uniforms[key]

    # Custom Shader Parameters
    shaderFile = open(os.path.dirname(os.path.realpath(__file__)) + "/shader_params.json", "r")
    shaders = json.load(shaderFile)

    albedo_maps = {}
    normal_maps = {}
    mask_maps = {}
    curvature_maps = {}

    for texturesType in textures.keys():
        textures_type = texturesType
        #material[texturesType] = textures.get(texturesType)
        if bpy.data.images.get("%s.dds" % textures[texturesType]) is not None:
            print(textures_type)
            if textures_type in {0,1}:
                albedo_maps[textures_type] = textures.get(texturesType)
            elif textures_type in {2,3}:
                normal_maps[textures_type] = textures.get(texturesType)
        else:
            pass#print("Couldn't find", texture_file, "for", textures_type)

    # Albedo Nodes
    albedo_nodes = []
    albedo_mixRGB_nodes = []
    albedo_invert_nodes = []
    colornode = None
    for i, textureID in enumerate(albedo_maps.values()):
        if bpy.data.images.get(str(textureID) + ".dds") is not None:
            albedo_image = nodes.new(type='ShaderNodeTexImage')
            albedo_nodes.append(albedo_image)
            albedo_image.location = 0,i*-60
            albedo_image.image = bpy.data.images.get(str(textureID) + ".dds")
            albedo_image.hide = True
            
            invert_shader = nodes.new(type="ShaderNodeInvert")
            albedo_invert_nodes.append(invert_shader)
            invert_shader.location = 600, (i-1)*-60
            invert_shader.hide = True
            if i > 0:
                albedo_image.label = "g_AlbedoMap" + str(i-1)
            else:
                albedo_image.label = "g_AlbedoMap"

            if i > 0:
                mixRGB_shader = nodes.new(type='ShaderNodeMixRGB')
                albedo_mixRGB_nodes.append(mixRGB_shader)
                mixRGB_shader.location = 300,(i-1)*-60
                mixRGB_shader.hide = True
                
                colornode = nodes.new(type='ShaderNodeAttribute')
                colornode.attribute_name = "Col"
                colornode.location = 100,(i-1)*-30
                colornode.hide = True
    # Albedo Links
    organic = shader_name[0:3] in {"eye", "har", "skn"}
    if len(albedo_nodes) == 1 or (organic and len(albedo_nodes) >= 1):
        albedo_principled = links.new(albedo_nodes[0].outputs['Color'], principled.inputs['Base Color'])
        if shader_name[3:5] == "00" and not organic:
            glossy_in_link = links.new(albedo_nodes[0].outputs['Alpha'], albedo_invert_nodes[0].inputs['Color'])
            rough_link = links.new(albedo_invert_nodes[0].outputs['Color'], principled.inputs['Roughness'])
            if 'Specular' in principled.inputs:
                specular_link = links.new(albedo_nodes[0].outputs['Alpha'], principled.inputs['Specular'])
            else:
                specular_link = links.new(albedo_nodes[0].outputs['Alpha'], principled.inputs['Specular IOR Level'])
            albedo_nodes[0].image.alpha_mode = "CHANNEL_PACKED"
        elif shader_name[4] != "0" or shader_name[0:3] == "har":
            alpha_link = links.new(albedo_nodes[0].outputs['Alpha'], principled.inputs['Alpha'])
        else: # disable alpha
            albedo_nodes[0].image.alpha_mode = "NONE"
    elif len(albedo_mixRGB_nodes) > 0:
        # first mixer node has two input albedos
        # subsequently each has one albedo and one mixer node
        for i, node in enumerate(albedo_mixRGB_nodes):
            # input 1
            if i == 0:
                albedoInFirst = albedo_nodes[i]
                albedo_link = links.new(albedoInFirst.outputs['Color'], node.inputs['Color1'])
            else:
                previousRGBNode = albedo_mixRGB_nodes[i-1]
                mixRGB_link = links.new(previousRGBNode.outputs['Color'], node.inputs['Color1'])
            
            # input 2 and blend (or should blend come from input 1? how do i do that? reverse node order?)
            albedoInSecond = albedo_nodes[i+1]
            albedo_link = links.new(albedoInSecond.outputs['Color'], node.inputs['Color2'])
            #alpha_link = links.new(albedoInSecond.outputs['Alpha'], node.inputs['Fac']) # the blend i think
            # screw texture alpha, vertex color alpha is my new best friend
            alpha_link = links.new(colornode.outputs['Alpha'], node.inputs['Fac'])
        mixRGB_link = links.new(albedo_mixRGB_nodes[-1].outputs['Color'], principled.inputs['Base Color'])

    # Mask Nodes
    # Mask Image Texture (R = Metallic, G = Glossines (Inverted Roughness), B = AO)
    mask_nodes = []
    mask_sepRGB_nodes = []
    mask_invert_nodes = []
    for i, textureID in enumerate(mask_maps.values()):
        if bpy.data.images.get(str(textureID) + ".dds") is not None:
            mask_image = nodes.new(type='ShaderNodeTexImage')
            mask_nodes.append(mask_image)
            mask_image.location = 0, ((len(albedo_maps)+1)*-60)-i*60
            mask_image.image = bpy.data.images.get(str(textureID) + ".dds")
            mask_image.image.colorspace_settings.name = 'Non-Color'
            mask_image.hide = True
            if i > 0:
                mask_image.label = "g_MaskMap" + str(i-1)
            else:
                mask_image.label = "g_MaskMap"

            if 'Hair' not in material['Shader_Name']:
                sepRGB_shader = nodes.new(type="ShaderNodeSeparateRGB")
                mask_sepRGB_nodes.append(sepRGB_shader)
                sepRGB_shader.location = 300, ((len(albedo_maps)+1)*-60)-i*60
                sepRGB_shader.hide = True
                
                invert_shader = nodes.new(type="ShaderNodeInvert")
                mask_invert_nodes.append(invert_shader)
                invert_shader.location = 600, ((len(albedo_maps)+1)*-60)-i*60
                invert_shader.hide = True
    #Mask Links
    if len(mask_nodes) > 0:
        if 'Hair' not in material['Shader_Name']:
            mask_link = links.new(mask_nodes[0].outputs['Color'], mask_sepRGB_nodes[0].inputs['Image'])
            r_link = links.new(mask_sepRGB_nodes[0].outputs['R'], principled.inputs['Metallic'])
            g_link = links.new(mask_sepRGB_nodes[0].outputs['G'], mask_invert_nodes[0].inputs['Color'])
            invert_link = links.new(mask_invert_nodes[0].outputs['Color'], principled.inputs['Roughness'])
        else:
            mask_link = links.new(mask_nodes[0].outputs['Color'], principled.inputs['Metallic'])

    # Normal Nodes
    # God fucking dammit Aura, how the fuck did you screw this up
    normal_nodes = []
    normal_mixRGB_nodes = []
    for i, textureID in enumerate(normal_maps.values()):
        if bpy.data.images.get(str(textureID) + ".dds") is not None:
            normal_image = nodes.new(type='ShaderNodeTexImage')
            normal_nodes.append(normal_image)
            normal_image.location = 0, (len(albedo_maps)+1 + len(mask_maps)+1 + i) * -60
            normal_image.image = bpy.data.images.get(str(textureID) + ".dds")
            normal_image.image.colorspace_settings.name = 'Non-Color'
            normal_image.hide = True
            if i > 0:
                normal_image.label = "g_NormalMap" + str(i-1)
            else:
                normal_image.label = "g_NormalMap"

            if i > 0:
                n_mixRGB_shader = nodes.new(type='ShaderNodeMixRGB')
                normal_mixRGB_nodes.append(n_mixRGB_shader)
                n_mixRGB_shader.location = 300, (len(albedo_maps)+1 + len(mask_maps)+1 + i-1) * -60
                n_mixRGB_shader.hide = True
        else:
            pass#print("Looking for", textureID, "in normalMaps, couldn't find it")
    if len(normal_nodes) > 0:
        normalmap_shader = nodes.new(type='ShaderNodeNormalMap')
        normalmap_shader.location = 600, (len(albedo_maps)+1 + len(mask_maps)+1 + i-1) * -60
        normalmap_link = links.new(normalmap_shader.outputs['Normal'], principled.inputs['Normal'])
        normalmap_shader.hide = True
    # Normal Links
    if len(normal_nodes) == 1:
        #normal_link = links.new(normal_nodes[0].outputs['Color'], normalmap_shader.inputs['Color'])
        # RGB Curve code by Naq
        # Creating new node
        invert_node = nodes.new("ShaderNodeRGBCurve")
        invert_node.name = "invert"
        invert_node.label = "Invert Green Channel"
        invert_node.location = 250, normal_nodes[0].location[1]
        invert_node.hide = True
        #node.label = texture_nrm.name

        # Let's invert the green channel
        green_channel = invert_node.mapping.curves[1] # Second curve is for green
        green_channel.points[0].location.y = 1
        green_channel.points[1].location.y = 0


        # Connecting
        links.new(normal_nodes[0].outputs["Color"], invert_node.inputs["Color"])
        links.new(invert_node.outputs["Color"], normalmap_shader.inputs["Color"])
    elif len(normal_mixRGB_nodes) > 0:
        normal_link = links.new(normal_nodes[0].outputs['Color'], normal_mixRGB_nodes[0].inputs['Color2'])
        for i, node in enumerate(normal_mixRGB_nodes):
            normal_link = links.new(normal_nodes[i+1].outputs['Color'], node.inputs['Color1'])
            if i > 0:
                n_mixRGB_link = links.new(normal_mixRGB_nodes[i-1].outputs['Color'], node.inputs['Color2'])
        mixRGB_link = links.new(normal_mixRGB_nodes[-1].outputs['Color'], normalmap_shader.inputs['Color'])

    # Curvature Nodes
    curvature_nodes = []
    curvature_sepRGB_nodes = []
    curvature_mul_nodes = []
    for i, textureID in enumerate(curvature_maps.values()):
        if bpy.data.images.get(textureID + ".dds") is not None:
            curvature_image = nodes.new(type='ShaderNodeTexImage')
            curvature_nodes.append(curvature_image)
            curvature_image.location = -600, ((len(albedo_maps)+1)*-60)-i*60+50
            curvature_image.image = bpy.data.images.get(textureID + ".dds")
            curvature_image.hide = True
            if i > 0:
                curvature_image.label = "g_CurvatureMap" + str(i-1)
            else:
                curvature_image.label = "g_CurvatureMap"
            sepRGB_shader = nodes.new(type="ShaderNodeSeparateRGB")
            curvature_sepRGB_nodes.append(sepRGB_shader)
            sepRGB_shader.location = -350, ((len(albedo_maps)+1)*-60)-i*60+50
            sepRGB_shader.hide = True
            
            multiply_shader = nodes.new(type="ShaderNodeMath")
            mask_invert_nodes.append(multiply_shader)
            multiply_shader.location = -200, ((len(albedo_maps)+1)*-60)-i*60+50
            multiply_shader.hide = True
            multiply_shader.operation = "MULTIPLY"
            curvature_mul_nodes.append(multiply_shader)
    # Curvature Links
    if len(curvature_nodes) > 0:
        curvature_link = links.new(curvature_nodes[0].outputs['Color'], curvature_sepRGB_nodes[0].inputs['Image'])
        r_link = links.new(curvature_sepRGB_nodes[0].outputs['R'], curvature_mul_nodes[0].inputs[0])
        g_link = links.new(curvature_sepRGB_nodes[0].outputs['G'], curvature_mul_nodes[0].inputs[1])
        mul_link = links.new(curvature_mul_nodes[0].outputs['Value'], principled.inputs['Subsurface'])
        principled.inputs[2].default_value[0] = 0.6
        principled.inputs[2].default_value[1] = 0.2
        principled.inputs[2].default_value[2] = 0.2

    return material

def add_material_to_mesh(mesh, materials , uvs):
    for material in materials:
        #print('linking material %s to mesh object %s' % (material.name, mesh.name))
        mesh.data.materials.append(material)
    bpy.context.view_layer.objects.active = mesh
    # bpy.ops.object.mode_set(mode="EDIT")
    # bm = bmesh.from_edit_mesh(mesh.data)
    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    uv_layer = bm.loops.layers.uv.verify()
    #bm.faces.layers.tex.verify()
    for face in bm.faces:
        face.material_index = 0
        for l in face.loops:
            #luv = l[uv_layer]
            ind = l.vert.index
            #print(l.vert)
            l[uv_layer].uv = Vector(uvs[0][ind])
    
    for i in range(1, 5): # 0 handled above
        if len(uvs[i]) > 0:
            #print("Creating UV layer for", material.name)
            
            new_uv_layer = None
            if i == 1:
                new_uv_layer = bm.loops.layers.uv.new("LightMap")
            else:
                new_uv_layer = bm.loops.layers.uv.new("UVMap" + str(i + 1))
            
            for face in bm.faces:
                face.material_index = 0
                for l in face.loops:
                    #luv = l[new_uv_layer]
                    ind = l.vert.index
                    #print(ind)
                    l[new_uv_layer].uv = Vector(uvs[i][ind])
        else:
            pass#print("Weird, no UV[%d] for %s" % (i, material.name))

    #bpy.ops.object.mode_set(mode='OBJECT')
    #mesh.select_set(True)
    #bpy.ops.object.shade_smooth()
    #mesh.hide = True
    #mesh.select_set(False)
    bm.to_mesh(mesh.data)
    bm.free()
    if bpy.app.version < (4, 1):
        mesh.data.use_auto_smooth = True

def format_wmb_mesh(wmb, collection_name, wmb4_transform=None):
    meshes = []
    uvMaps = [[], [], [], [], []]
    usedVerticeIndexArrays = []
    mesh_array = wmb.meshArray
    #each vertexgroup -> each lod -> each group -> mesh
    for vertexGroupIndex in range(wmb.wmb_header.vertexGroupCount):
        if wmb.vertexGroupArray[vertexGroupIndex].vertexFlags is not None:
            vertex_flags = wmb.vertexGroupArray[vertexGroupIndex].vertexFlags
        else: # wmb4
            if (wmb.wmb_header.vertexFormat & 0x337) == 0x337: # in exData
                vertex_flags = -1
            elif wmb.wmb_header.vertexFormat == 0x10307:       # in vertex
                vertex_flags = -2
            else:                                              # only one texture
                vertex_flags = -3
        
        if vertex_flags == -3:
            uv = [(vertex.textureU, 1 - vertex.textureV) for vertex in wmb.vertexGroupArray[vertexGroupIndex].vertexArray]
            uvMaps[0].append(uv)
            uvMaps[1].append(None)
            uvMaps[2].append(None)
            uvMaps[3].append(None)
            uvMaps[4].append(None)

        elif vertex_flags in {-2, 0, 1, 4}:
            uv = [(vertex.textureU, 1 - vertex.textureV) for vertex in wmb.vertexGroupArray[vertexGroupIndex].vertexArray]
            uvMaps[0].append(uv)
            uv = [(vertex.textureU2, 1 - vertex.textureV2) for vertex in wmb.vertexGroupArray[vertexGroupIndex].vertexArray]
            uvMaps[1].append(uv)
            uvMaps[2].append(None)
            uvMaps[3].append(None)
            uvMaps[4].append(None)

        elif vertex_flags == 5:
            uv = [(vertex.textureU, 1 - vertex.textureV) for vertex in wmb.vertexGroupArray[vertexGroupIndex].vertexArray]
            uvMaps[0].append(uv)
            uv = [(vertex.textureU2, 1 - vertex.textureV2) for vertex in wmb.vertexGroupArray[vertexGroupIndex].vertexArray]
            uvMaps[1].append(uv)
            uv = [(vertexExData.textureU3, 1 - vertexExData.textureV3) for vertexExData in wmb.vertexGroupArray[vertexGroupIndex].vertexesExDataArray]
            uvMaps[2].append(uv)
            uvMaps[3].append(None)
            uvMaps[4].append(None)

        elif vertex_flags in {-1, 7, 10}:
            uv = [(vertex.textureU, 1 - vertex.textureV) for vertex in wmb.vertexGroupArray[vertexGroupIndex].vertexArray]
            uvMaps[0].append(uv)
            uv = [(vertexExData.textureU2, 1 - vertexExData.textureV2) for vertexExData in wmb.vertexGroupArray[vertexGroupIndex].vertexesExDataArray]
            uvMaps[1].append(uv)
            uvMaps[2].append(None)
            uvMaps[3].append(None)
            uvMaps[4].append(None)

        elif vertex_flags == 11:
            uv = [(vertex.textureU, 1 - vertex.textureV) for vertex in wmb.vertexGroupArray[vertexGroupIndex].vertexArray]
            uvMaps[0].append(uv)
            uv = [(vertexExData.textureU2, 1 - vertexExData.textureV2) for vertexExData in wmb.vertexGroupArray[vertexGroupIndex].vertexesExDataArray]
            uvMaps[1].append(uv)
            uv = [(vertexExData.textureU3, 1 - vertexExData.textureV3) for vertexExData in wmb.vertexGroupArray[vertexGroupIndex].vertexesExDataArray]
            uvMaps[2].append(uv)
            uvMaps[3].append(None)
            uvMaps[4].append(None)

        elif vertex_flags == 12:
            uv = [(vertex.textureU, 1 - vertex.textureV) for vertex in wmb.vertexGroupArray[vertexGroupIndex].vertexArray]
            uvMaps[0].append(uv)
            uv = [(vertex.textureU2, 1 - vertex.textureV2) for vertex in wmb.vertexGroupArray[vertexGroupIndex].vertexArray]
            uvMaps[1].append(uv)
            uv = [(vertexExData.textureU3, 1 - vertexExData.textureV3) for vertexExData in wmb.vertexGroupArray[vertexGroupIndex].vertexesExDataArray]
            uvMaps[2].append(uv)
            uv = [(vertexExData.textureU4, 1 - vertexExData.textureV4) for vertexExData in wmb.vertexGroupArray[vertexGroupIndex].vertexesExDataArray]
            uvMaps[3].append(uv)
            uv = [(vertexExData.textureU5, 1 - vertexExData.textureV5) for vertexExData in wmb.vertexGroupArray[vertexGroupIndex].vertexesExDataArray]
            uvMaps[4].append(uv)

        elif vertex_flags == 14:
            uv = [(vertex.textureU, 1 - vertex.textureV) for vertex in wmb.vertexGroupArray[vertexGroupIndex].vertexArray]
            uvMaps[0].append(uv)
            uv = [(vertex.textureU2, 1 - vertex.textureV2) for vertex in wmb.vertexGroupArray[vertexGroupIndex].vertexArray]
            uvMaps[1].append(uv)
            uv = [(vertexExData.textureU3, 1 - vertexExData.textureV3) for vertexExData in wmb.vertexGroupArray[vertexGroupIndex].vertexesExDataArray]
            uvMaps[2].append(uv)
            uv = [(vertexExData.textureU4, 1 - vertexExData.textureV4) for vertexExData in wmb.vertexGroupArray[vertexGroupIndex].vertexesExDataArray]
            uvMaps[3].append(uv)
            uvMaps[4].append(None)
        
        if vertex_flags >= 0: # wmb3
            for meshGroupInfo in wmb.meshGroupInfoArray:
                groupedMeshArray = meshGroupInfo.groupedMeshArray
                mesh_start = meshGroupInfo.meshStart
                LOD_name = meshGroupInfo.meshGroupInfoname
                LOD_level = meshGroupInfo.lodLevel
                for meshGroupIndex in range(wmb.wmb_header.meshGroupCount):
                    meshIndexArray = []
                    for groupedMeshIndex, groupedMesh in enumerate(groupedMeshArray):
                        if groupedMesh.meshGroupIndex == meshGroupIndex:
                            meshIndexArray.append([mesh_start + groupedMeshIndex, groupedMesh.colTreeNodeIndex, groupedMesh.unknownWorldDataIndex])
                    meshGroup = wmb.meshGroupArray[meshGroupIndex]
                    for meshArrayData in (meshIndexArray):
                        meshArrayIndex = meshArrayData[0]
                        colTreeNodeIndex = meshArrayData[1]
                        unknownWorldDataIndex = meshArrayData[2]
                        meshVertexGroupIndex = wmb.meshArray[meshArrayIndex].vertexGroupIndex
                        if meshVertexGroupIndex == vertexGroupIndex:
                            meshName = "%d-%s-%d"%(meshArrayIndex, meshGroup.meshGroupname, vertexGroupIndex)
                            meshInfo = wmb.clear_unused_vertex(meshArrayIndex, meshVertexGroupIndex)
                            vertices = meshInfo[0]
                            faces =  meshInfo[1]
                            usedVerticeIndexArray = meshInfo[2]
                            boneWeightInfoArray = meshInfo[3]
                            vertex_colors = meshInfo[4]
                            usedVerticeIndexArrays.append(usedVerticeIndexArray)
                            flag = False # unused?
                            has_bone = wmb.hasBone
                            boneSetIndex = wmb.meshArray[meshArrayIndex].bonesetIndex
                            if boneSetIndex == 0xffffffff:
                                boneSetIndex = -1
                            boundingBox = meshGroup.boundingBox
                            obj = construct_mesh([meshName, vertices, faces, has_bone, boneWeightInfoArray, boneSetIndex, meshGroupIndex, vertex_colors, LOD_name, LOD_level, colTreeNodeIndex, unknownWorldDataIndex, boundingBox, vertexGroupIndex], collection_name)
                            meshes.append(obj)
        
    if wmb.wmb_header.magicNumber == b'WMB4':
        # very important, should be somewhere else
        # bpy.data.collections['WMB']['vertexFormat'] = wmb.wmb_header.vertexFormat
        if wmb.mystery is not None:
            load_mysterychunk(wmb.mystery, collection_name)
        else:
            bpy.data.collections['WMB']['mystery'] = False
        bpy.data.collections[collection_name]['vertexFormat'] = wmb.wmb_header.vertexFormat
        
        for batchIndex, batch in enumerate(wmb.batchArray):
            batchData = wmb.batchDataArray[batchIndex]
            vertexGroup = wmb.vertexGroupArray[batch.vertexGroupIndex]
            
            mesh = wmb.meshArray[batchData.meshIndex]
            
            mesh.faceStart = batch.indexStart
            mesh.faceCount = batch.numIndexes
            mesh.vertexStart = batch.vertexStart
            mesh.vertexCount = batch.numVertexes
            mesh.bonesetIndex = batchData.boneSetsIndex
            
            meshInfo = wmb.clear_unused_vertex(batchData.meshIndex, batch.vertexGroupIndex, True)
            usedVerticeIndexArrays.append(meshInfo[2]) # usedVerticeIndexArray
            
            
            meshName = "%d-%s"%(batch.vertexGroupIndex, mesh.name)
            # duplicate objects during prop import
            # TODO make less hacky (ba0010.002 is ten chars)
            if collection_name[-4] == "." and collection_name[-3:].isnumeric():
                meshName += collection_name[-4:]
            
            materials = [batchData.materialIndex]
            if (len(mesh.materials) == 0) or materials[0] not in mesh.materials:
                print("Huh, mismatched material index.")
                print(materials, mesh.materials)
                materials.extend(mesh.materials)
            else:
                print("A material matches")
                print(materials, mesh.materials)
                for mat in mesh.materials:
                    if mat not in materials:
                        materials.append(mat)
            
            obj = construct_mesh([
                meshName,    # meshName
                meshInfo[0], # vertices
                meshInfo[1], # faces
                wmb.hasBone, # has_bone
                meshInfo[3], # boneWeightInfoArray
                batchData.boneSetsIndex, # boneSetIndex
                batchData.meshIndex,     # meshGroupIndex
                meshInfo[4], # vertex_colors
                "NoLOD",     # LOD_name
                -1,          # LOD_level
                None,        # colTreeNodeIndex
                None,        # unknownWorldDataIndex
                mesh.boundingBox,       # boundingBox
                batch.vertexGroupIndex, # vertexGroupIndex
                batchIndex,
                materials,
                wmb.boneSetArray[batchData.boneSetsIndex] if batchData.boneSetsIndex > -1 else None, # boneSet
                meshInfo[5], # vertexStart
                batch.batchGroup,       # batch group, which of the four supplements
                wmb4_transform,  # header data for SCR transformations
                meshInfo[6], # vertexCount
                meshInfo[7]  # normals
            ], collection_name)
            meshes.append(obj)
    
    return meshes, uvMaps, usedVerticeIndexArrays

def get_wmb_material(wmb, texture_dir):
    materials = []
    if wmb.wta:
        if hasattr(wmb, 'materialArray'):
            for materialIndex, material in enumerate(wmb.materialArray):
                material_name = material.materialName
                shader_name = material.effectName
                uniforms = material.uniformArray
                textures = material.textureArray
                if hasattr(material, "textureFlagArray"): # wmb4
                    textureFlags = material.textureFlagArray
                else:
                    textureFlags = None
                if hasattr(wmb, 'textureArray'):
                    for index, texture in textures.items():
                        if texture == -1:
                            continue
                        try:
                            textures[index] = wmb.textureArray[texture].id # change index to WTA identifier
                        except:
                            print("An error has occured! It seems that the global texture array doesn't have enough elements (%d). I think. This is a generic exception." % texture)
                            #print("I'm deleting this.")
                            textures[index] = -1
                    for index, texture in textures.copy().items():
                        if texture == -1:
                            del textures[index]
                    print("Textures on %s:"%material_name, textures)
                parameterGroups = material.parameterGroups
                for textureIndex in range(wmb.wta.textureCount):        # for key in textures.keys():
                    #identifier = textures[key]
                    identifier = wmb.wta.wtaTextureIdentifier[textureIndex]
                    texture_file_name = identifier + '.dds'
                    texture_filepath = os.path.join(texture_dir, texture_file_name)
                    try:
                        texture_stream = wmb.wta.getTextureByIdentifier(identifier,wmb.wtp_fp)
                        if texture_stream:
                            if not os.path.exists(texture_filepath):
                                create_dir(texture_dir)
                                texture_fp = open(texture_filepath, "wb")
                                print('[+] could not find DDS texture, trying to find it in WTA;', texture_file_name)
                                texture_fp.write(texture_stream)
                                texture_fp.close()
                            else:
                                pass#print('[+] Found %s.dds'% identifier)
                        else:
                            print("Texture identifier %s does not exist in WTA, despite being fetched from a WTA identifier list." % identifier)
                    except:
                        continue

                    if bpy.data.images.get(texture_file_name) is None:
                        bpy.data.images.load(texture_filepath)
                
                materials.append([material_name,textures,uniforms,shader_name,parameterGroups, textureFlags])
                #print(materials)
        else:
            texture_dir = texture_dir.replace('.dat','.dtt')
            for textureIndex in range(wmb.wta.textureCount):
                #print(textureIndex)
                identifier = wmb.wta.wtaTextureIdentifier[textureIndex]
                texture_stream = wmb.wta.getTextureByIdentifier(identifier,wmb.wtp_fp)
                if texture_stream:
                    if not os.path.exists(os.path.join(texture_dir, identifier + '.dds')):
                        create_dir(texture_dir)
                        texture_fp = open(os.path.join(texture_dir, identifier + '.dds'), "wb")
                        print('[+] dumping %s.dds'% identifier)
                        texture_fp.write(texture_stream)
                        texture_fp.close()

    else:
        print('Missing .wta')
        ShowMessageBox("Error: Could not open .wta file, textures not imported. Is it missing? (Maybe DAT not extracted?)", 'Could Not Open .wta File', 'ERROR')
        for materialIndex, material in enumerate(wmb.materialArray):
            material_name = material.materialName
            shader_name = material.effectName
            uniforms = material.uniformArray
            textures = material.textureArray
            # why the fuck was this not already here, it doesn't need the wta
            if hasattr(wmb, 'textureArray'):
                for index, texture in textures.items():
                    if texture == -1:
                        continue
                    try:
                        textures[index] = wmb.textureArray[texture].id # change index to WTA identifier
                    except:
                        print("An error has occured! It seems that the global texture array doesn't have enough elements (%d). I think. This is a generic exception." % texture)
                        #print("I'm deleting this.")
                        textures[index] = -1
                for index, texture in textures.copy().items():
                    if texture == -1:
                        del textures[index]
                print("Textures on %s:"%material_name, textures)
            parameterGroups = material.parameterGroups
            if hasattr(material, "textureFlagArray"): # wmb4
                textureFlags = material.textureFlagArray
            else:
                textureFlags = None
            materials.append([material_name,textures,uniforms,shader_name,parameterGroups,textureFlags])
        
    return materials

def import_colTreeNodes(wmb, collection):
    colTreeNodesDict = {}
    #collision_col = bpy.data.collections.new("CollisionNodes")
    #collection.children.link(collision_col)

    colTreeNodesCollection = bpy.data.collections.get("wmb_colTreeNodes")
    if not colTreeNodesCollection:
        colTreeNodesCollection = bpy.data.collections.new("wmb_colTreeNodes")
        collection.children.link(colTreeNodesCollection)

    bpy.context.view_layer.active_layer_collection.children["WMB"].children[collection.name].children["wmb_colTreeNodes"].hide_viewport = True

    rootNode = bpy.data.objects.new("Root_wmb", None)
    rootNode.hide_viewport = True
    colTreeNodesCollection.objects.link(rootNode)
    rootNode.rotation_euler = (math.radians(90),0,0)
    for nodeIdx, node in enumerate(wmb.colTreeNodes):
        colTreeNodeName = 'colTreeNode' + str(nodeIdx)
        objName = str(nodeIdx) + "_" + str(node.left) + "_" + str(node.right) + "_wmb"
        obj = bpy.data.objects.new(objName, None)
        colTreeNodesCollection.objects.link(obj)
        obj.parent = rootNode
        obj.empty_display_type = 'CUBE'

        obj.location = node.p1
        obj.scale = node.p2
        meshIndices = []
        for bObj in (x for x in bpy.data.collections['WMB'].all_objects if x.type == "MESH"):
            if bObj["colTreeNodeIndex"] == nodeIdx:
                idx = int(bObj.name.split("-")[0])
                meshIndices.append(idx)
        
        if len(meshIndices) > 0:
            obj["meshIndices"] = meshIndices
        colTreeNode = [node.p1[0], node.p1[1], node.p1[2], node.p2[0], node.p2[1], node.p2[2], node.left, node.right]
        colTreeNodesDict[colTreeNodeName] = colTreeNode

    bpy.context.scene['colTreeNodes'] = colTreeNodesDict

def import_unknowWorldDataArray(wmb):
    unknownWorldDataDict = {}
    for index, unknownWorldData in enumerate(wmb.unknownWorldDataArray):
        unknownWorldDataName = 'unknownWorldData' + str(index)
        unknownWorldDataDict[unknownWorldDataName] = unknownWorldData.unknownWorldData
    bpy.context.scene['unknownWorldData'] = unknownWorldDataDict

def load_mysterychunk(chunk, collection_name):
    col = bpy.data.collections.new("looseCoords")
    bpy.context.scene.collection.children.link(col)
    print("Processing mystery chunk!")
    def mset(name, val): # short for mystery should rename
        bpy.data.collections["WMB"][name] = val # formerly collection name
    def makeobj(coords, name="Holder of Place"):
        target = bpy.data.objects.new(name, None)
        target.empty_display_size = 0.15
        target.location = coords
        bpy.data.collections["looseCoords"].objects.link(target)
    
    mset("mystery", True)
    
    for i, one in enumerate(chunk.mystery1):
        mset("1-%2d-name"%i, one.name)
        mset("1-%2d-parent"%i, one.parent)
        mset("1-%2d-B"%i, one.mysteryB)
    
    for i, two in enumerate(chunk.mystery2):
        mset("2-%2d-A"%i, two.posA)
        mset("2-%2d-Aflag"%i, two.flagA)
        mset("2-%2d-B"%i, two.posB)
        mset("2-%2d-Bflag"%i, two.flagB)
        mset("2-%2d-C"%i, two.posC)
        mset("2-%2d-Cflag"%i, two.flagC)
        mset("2-%2d-D"%i, two.posD)
    
    for i, three in enumerate(chunk.mystery3):
        for j, content in enumerate(three.vectors):
            mset("3-%2d-%2d-A"%(i,j), content.mysteryA)
            #makeobj(content.mysteryA[:3], "3-%2d-%2d-A"%(i,j))
            mset("3-%2d-%2d-B"%(i,j), content.mysteryB)
            #makeobj(content.mysteryB[:3], "3-%2d-%2d-B"%(i,j))
            mset("3-%2d-%2d-C"%(i,j), content.mysteryC)
            #makeobj(content.mysteryC[:3], "3-%2d-%2d-C"%(i,j))
            mset("3-%2d-%2d-D"%(i,j), content.mysteryD)
            #makeobj(content.mysteryD[:3], "3-%2d-%2d-D"%(i,j))
            mset("3-%2d-%2d-E"%(i,j), content.mysteryE)
            #makeobj(content.mysteryE[:3], "3-%2d-%2d-E"%(i,j))
            mset("3-%2d-%2d-F"%(i,j), content.mysteryF)
    
    for i, four in enumerate(chunk.mystery4):
        mset("4-%2d-A"%i, four.posA)
        #makeobj([four.posA[0], four.posA[2], four.posA[1]], "4-%2d-A"%i)
        mset("4-%2d-B"%i, four.posB)
        #makeobj([four.posB[0], four.posB[2], four.posB[1]], "4-%2d-B"%i)
        mset("4-%2d-C"%i, four.mysteryC)
        mset("4-%2d-D"%i, four.mysteryD) # batch index
        mset("4-%2d-E"%i, four.mysteryE) # usually 0, a couple 1
        mset("4-%2d-E2"%i, four.mysteryE2)
        mset("4-%2d-F"%i, four.mysteryF) # always 1? (0 in some other model)
        mset("4-%2d-array"%i, four.twentyElements)
        mset("4-%2d-startVertex"%i, four.startVertex)
        mset("4-%2d-vertexCount"%i, four.vertexCount)
        mset("4-%2d-startIndex"%i, four.startIndex)
        mset("4-%2d-indexCount"%i, four.indexCount)
    _4A = ["%d-%d %d-%d" % (x.startVertex, x.startVertex+x.vertexCount, x.startIndex, x.startIndex+x.indexCount) for x in chunk.mystery4]
    print("4 Vertexes and indexes:")
    print("\n".join(_4A))
    
    for i, five in enumerate(chunk.mystery5):
        mset("5-%2d-A"%i, five.mysteryA)
        mset("5-%2d-B"%i, five.mysteryB) # cut group index
        mset("5-%2d-B2"%i, five.mysteryB2) # usually 0, a couple 1
        mset("5-%2d-C"%i, five.mysteryC) # parent cut group?
        mset("5-%2d-C2"%i, five.mysteryC2) # always 0
        
        for j, content in enumerate(five.mysteryD):
            mset("5-%2d-D-%2d"%(i,j), content.content)
    myList = [x.mysteryA for x in chunk.mystery5]
    print("5A:")
    print(min(myList), max(myList), myList)
    myList = [x.mysteryB for x in chunk.mystery5]
    print("5B:")
    print(min(myList), max(myList), myList)
    myList = [x.mysteryC for x in chunk.mystery5]
    print("5C:")
    print(min(myList), max(myList), myList)
    myList = [x.mysteryC2 for x in chunk.mystery5]
    print("5C2:")
    print(min(myList), max(myList), myList)
    print()
    
    for i, six in enumerate(chunk.mystery6):
        sixAFlat = []
        for vec in six.mysteryA:
            sixAFlat.extend([vec.x, vec.y, vec.z, vec.w])
            offsetted = chunk.mystery7[i].unknownA
            #makeobj([vec.x + offsetted[0], vec.z + offsetted[2], vec.y + offsetted[1]], "6-%2d-A-%2d" % (i, len(sixAFlat) // 4))
        mset("6-%2d-A"%i, sixAFlat)
        mset("6-%2d-B"%i, six.mysteryB)
    myList = [x.mysteryB for x in chunk.mystery6]
    print("6B:")
    print(min([min(x) for x in myList]), max([max(x) for x in myList]), myList)
    
    for i, seven in enumerate(chunk.mystery7):
        mset("7-%2d-A"%i, seven.unknownA)
        x = seven.unknownA
        #makeobj([x[0], -x[2], x[1]], "7A-%2d"%i)
        mset("7-%2d-B"%i, seven.unknownB)
        x = seven.unknownB
        #makeobj([x[0], -x[2], x[1]], "7B-%2d"%i)
        mset("7-%2d-C"%i, seven.unknownC)
        mset("7-%2d-D"%i, seven.unknownD)
        
        mset("7-%2d-startVertex"%i, seven.startVertex)
        mset("7-%2d-vertexCount"%i, seven.vertexCount)
        mset("7-%2d-startIndex"%i, seven.startIndex)
        mset("7-%2d-indexCount"%i, seven.indexCount)
    
    for i, eight in enumerate(chunk.mystery8):
        eightVectorsFlat = []
        for vec in eight.vectors:
            eightVectorsFlat.extend(vec)
            #makeobj(vec, "8-%2d-%2d"%(i, len(eightVectorsFlat)//3))
        mset("8-%2d-vectors"%i, eightVectorsFlat)
        mset("8-%2d-A"%i, eight.mysteryA)
        mset("8-%2d-B"%i, eight.mysteryB)
        mset("8-%2d-C"%i, eight.mysteryC)
        mset("8-%2d-D"%i, eight.mysteryD)
        mset("8-%2d-E"%i, eight.mysteryE)
        mset("8-%2d-F"%i, eight.mysteryF)
        mset("8-%2d-G"%i, eight.mysteryG)
    myList = [x.mysteryA for x in chunk.mystery8]
    print("8A:")
    print(min(myList), max(myList), myList)
    myList = [x.mysteryC for x in chunk.mystery8]
    print("8C:")
    print(min(myList), max(myList), myList)
    myList = [x.mysteryD for x in chunk.mystery8]
    print("8D:")
    print(min(myList), max(myList), myList)
    myList = [x.mysteryE for x in chunk.mystery8]
    print("8E:")
    print(min(myList), max(myList), myList)
    myList = [x.mysteryF for x in chunk.mystery8]
    print("8F:")
    print(min(myList), max(myList), myList)
    myList = [x.mysteryG for x in chunk.mystery8]
    print("8G:")
    print(min(myList), max(myList), myList)
    
    for i, nine in enumerate(chunk.mystery9):
        mset("9-%2d-A"%i, nine.mysteryA)
        mset("9-%2d-parent"%i, nine.mysteryParent)
        mset("9-%2d-C"%i, nine.mysteryC)
        mset("9-%2d-D"%i, nine.mysteryD)
        mset("9-%2d-E"%i, nine.mysteryE)
    myList = [x.mysteryA for x in chunk.mystery9]
    print("9A:")
    print(min(myList), max(myList), myList)
    #myList = [x.mysteryB for x in chunk.mystery9]
    #print("9B:")
    #print(min(myList), max(myList), myList)
    myList = [x.mysteryC for x in chunk.mystery9]
    print("9C:")
    print(min(myList), max(myList), myList)
    myList = [x.mysteryD for x in chunk.mystery9]
    print("9D:")
    print(min(myList), max(myList), myList)
    myList = [x.mysteryE for x in chunk.mystery9]
    print("9E:")
    print(min(myList), max(myList), myList)
    print("\n\n")

def main(only_extract = False, wmb_file = os.path.join(os.path.split(os.path.realpath(__file__))[0], 'test', 'pl0000.dtt', 'pl0000.wmb'), wmb4_transform = None):
    #reset_blend()
    wmb = WMB(wmb_file, only_extract)
    wmbname = os.path.split(wmb_file)[-1] # Split only splits into head and tail, but since we want the last part, we don't need to split the head with wmb_file.split(os.sep)
    wmb4 = wmb.wmb_header.magicNumber == b'WMB4'
    
    if only_extract:
        texture_dir = wmb_file.replace(wmbname, 'textures')
        wmb_materials = get_wmb_material(wmb, texture_dir)
        print('Extraction finished. ;)')
        return {'FINISHED'}

    wmbCollection = bpy.data.collections.get("WMB")
    if not wmbCollection:
        wmbCollection = bpy.data.collections.new("WMB")
        bpy.context.scene.collection.children.link(wmbCollection)

    collection_name = wmbname[:-4]
    if bpy.data.collections.get(collection_name): # oops, duplicate
        collection_suffix = 1
        while True:
            if not bpy.data.collections.get(collection_name + "." + ("%03d" % collection_suffix)):
                collection_name += "." + ("%03d" % collection_suffix)
                break
            collection_suffix += 1
    col = bpy.data.collections.new(collection_name)
    
    wmbCollection.children.link(col)
    #bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[-1]
    
    texture_dir = wmb_file.replace(wmbname, 'textures')
    armature_name = ""
    if hasattr(wmb, 'hasBone') and wmb.hasBone:
        boneArray = [[
            bone.boneIndex,
            "bone%d" % bone.boneIndex,
            bone.parentIndex,
            "bone%d" % bone.parentIndex,
            bone.world_position,
            bone.world_rotation,
            bone.boneNumber,
            bone.local_position,
            bone.local_rotation,
            bone.world_rotation,
            bone.world_position_tpose] for bone in wmb.boneArray]
        armature_no_wmb = wmbname.replace('.wmb','')
        armature_name_split = armature_no_wmb.split('/')
        armature_name = armature_name_split[-1]
        construct_armature(armature_name, boneArray, wmb.firstLevel, wmb.secondLevel, wmb.thirdLevel, wmb.boneMap, wmb.boneSetArray, collection_name, wmb4_transform)
    
    meshes, uvs, usedVerticeIndexArrays = format_wmb_mesh(wmb, collection_name, wmb4_transform)
    wmb_materials = get_wmb_material(wmb, texture_dir)
    materials = []
    bpy.context.scene.WTAMaterials.clear()
    for materialIndex, material in enumerate(wmb_materials):
        addWtaExportMaterial(texture_dir, material)
        materials.append(construct_materials(texture_dir, material, materialIndex))
    print('Linking materials to objects...')
    if not wmb4: # formerly "hasattr(wmb, "meshGroupInfoArray")":
        for meshGroupInfo in wmb.meshGroupInfoArray:
            mesh_start = meshGroupInfo.meshStart
            for Index in range(len(meshGroupInfo.groupedMeshArray)):
                meshIndex = int(meshes[Index + mesh_start].name.split('-')[0])
                materialIndex = meshGroupInfo.groupedMeshArray[meshIndex - mesh_start].materialIndex
                groupIndex = int(meshes[Index + mesh_start].name.split('-')[2])
                uvMaps = [[], [], [], [], []]
                for i, VertexIndex in enumerate(usedVerticeIndexArrays[Index + mesh_start]):
                    for k in range(5):
                        if uvs[k][groupIndex] != None:
                            uvMaps[k].append( uvs[k][groupIndex][VertexIndex])
                if len(materials) > 0:
                    add_material_to_mesh(meshes[Index + mesh_start], [materials[materialIndex]], uvMaps)
    else:
        for mesh in meshes:
            meshIndex = int(mesh['ID'])
            groupIndex = int(mesh.name.split('-')[0])
            uvMaps = [[], [], [], [], []]
            vertexStart = mesh['VertexIndexStart']
            for VertexIndex in usedVerticeIndexArrays[meshIndex]:
                for k in range(5):
                    if uvs[k][groupIndex] != None:
                        #print("Found a UV!", k, groupIndex, VertexIndex, uvs[k][groupIndex][VertexIndex])
                        uvMaps[k].append( uvs[k][groupIndex][vertexStart + VertexIndex])
            for materialIndex in mesh['Materials']:
                #if len(materials) > 0:
                    #print("Some materials made for", mesh.name)
                # sanity checks are for wimps
                #print(mesh.name, materialIndex)
                add_material_to_mesh(mesh, [materials[materialIndex]], uvMaps)
    
    amt = bpy.data.objects.get(armature_name)
    if amt is not None:
        for mesh in meshes:
            set_partent(amt,mesh)
    
    if wmb4:
        # batchgroup sets some meshes as shadow only or low-LOD
        for obj in [x for x in col.all_objects if x.type == "MESH"]:
            if obj['batchGroup'] > 0:
                obj.hide_set(True)
                obj.hide_render = True
        # more descriptive bone names where possible
        if amt is not None:
            if wmb.wmb_header.vertexFormat == 0x107: # wmb.wmb_header.referenceBone != -1
                #bpy.ops.object.mode_set(mode='EDIT')
                for mesh in meshes:
                    mesh.vertex_groups.new(name="bone%d"%wmb.wmb_header.referenceBone)
                    mesh.vertex_groups["bone%d"%wmb.wmb_header.referenceBone].add(
                        list(range(len(mesh.data.vertices))), 1.0, "REPLACE")
                #bpy.ops.object.mode_set(mode='OBJECT')
                    
            for bone in amt.data.bones:
                oldBoneName = bone.name
                if bone["ID"] in wmb4_bonenames:
                    #print("Renaming %s to %s" % (bone.name, wmb4_bonenames[bone["ID"]]))
                    bone.name = wmb4_bonenames[bone["ID"]]
                else:
                    bone.name = "bone%d" % bone["ID"]
                for mesh in [x for x in col.objects if x.type == "MESH"]:
                    for vertexGroup in [y for y in mesh.vertex_groups if y.name == oldBoneName]:
                        vertexGroup.name = bone.name
                    
        else:
            print("Huh, no armature. hasBone is", wmb.hasBone)
            
    if wmb.hasColTreeNodes:
        import_colTreeNodes(wmb, col)
    if wmb.hasUnknownWorldData:
        import_unknowWorldDataArray(wmb)

    print('Importing finished. ;)')
    return {'FINISHED'}

if __name__ == '__main__':
    main()
