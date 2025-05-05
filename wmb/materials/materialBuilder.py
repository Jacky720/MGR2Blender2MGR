import bpy
from ... import consts

def invertGreenChannel(nodes, normal_node_pos=0):
    # Thanks Naq, you're a king fr
    invert_node = nodes.new("ShaderNodeRGBCurve")
    invert_node.name = "invert"
    invert_node.label = "Invert Green Channel"
    invert_node.location = 450, normal_node_pos
    invert_node.hide = True
    #node.label = texture_nrm.name

    # Let's invert the green channel
    green_channel = invert_node.mapping.curves[1] # Second curve is for green
    green_channel.points[0].location.y = 1
    green_channel.points[1].location.y = 0
    
    return invert_node




def buildMaterialNodes(material, uniforms):
    # Better idea than cramming it all in wmb importer 
    material.use_nodes = True
    # Clear Nodes and Links
    material.node_tree.links.clear()
    material.node_tree.nodes.clear()
    # Recreate Nodes and Links with references
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    # PrincipledBSDF and Ouput Shader
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = 2000,0
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = 1600,0
    output_link = links.new( principled.outputs['BSDF'], output.inputs['Surface'] )
    
    for key in uniforms.keys():
        material[key] = uniforms.get(key)
        #print(key, material[key])
        if key.lower().find("g_glossiness") > -1:
            principled.inputs['Roughness'].default_value = 1 - uniforms[key]
    
    node_dict = {}
    mixedAlbedoNode = None
    mixedLightmapNode = None
    hasMixedAlbedo=False
    normalShader = None
    uv_lightmap_node = None
    albedoInverterNode = None
    
    for i, texentry in enumerate(material.mgr_data.textures):
        if bpy.data.images.get(str(texentry.id) + ".dds") is not None:
            image_node = nodes.new(type='ShaderNodeTexImage')
            image_node.location = 0,i*-60
            image_node.image = bpy.data.images.get(str(texentry.id) + ".dds")
            image_node.hide = True
            image_node.label = consts.getTextureFlagFromDict(texentry.flag)
            if texentry.flag == 0:                 
                albedoInverterNode = nodes.new(type="ShaderNodeInvert")
                albedoInverterNode.location = 300, 0
                albedoInverterNode.inputs[0].default_value = 1.0
            
            elif texentry.flag == 1:
                hasMixedAlbedo = True
                mixedAlbedoNode = nodes.new(type='ShaderNodeMixRGB')
                mixedAlbedoNode.location = 300, i*-60
                mixedAlbedoNode.hide = True
                
            elif texentry.flag == 2:
                image_node.image.colorspace_settings.name = 'Non-Color'
                
            elif texentry.flag == 7:
                mixedLightmapNode = nodes.new(type='ShaderNodeMixRGB')
                mixedLightmapNode.location = 500, i*-60
                mixedLightmapNode.hide = True
                
                mixedLightmapNode.blend_type = 'SOFT_LIGHT'
                mixedLightmapNode.label = "Lightmap Mixer"
                
            
            node_dict[texentry.flag] = image_node
    
    
    albedoNode = None
    if not mixedLightmapNode == None:
        uv_lightmap_node = nodes.new(type="ShaderNodeUVMap")
        uv_lightmap_node.uv_map = "LightMap"
        uv_lightmap_node.location = (-200, -150)
        uv_lightmap_node.label = "LightMap UV"
    

    
    for flag, node in node_dict.items():
        if flag == 0: # Base Color
            links.new(node.outputs['Color'], principled.inputs['Base Color'])
            if material.mgr_data.shader_name in consts.transparentShaders:
                links.new(node.outputs['Alpha'], principled.inputs['Alpha'])
                material.blend_method = 'HASHED'
            elif not material.mgr_data.shader_name in consts.reflectiveBlacklist:
                links.new(node.outputs['Alpha'], albedoInverterNode.inputs['Color'])
                links.new(albedoInverterNode.outputs['Color'], principled.inputs['Roughness'])
                
            
            
            albedoNode = node
        if flag == 2:
            if normalShader == None:
                normalShader = nodes.new(type='ShaderNodeNormalMap')
                normalShader.location = 600, 0
                normalShader.hide = True
                links.new(normalShader.outputs['Normal'], principled.inputs['Normal'])
            
            invertGreen = invertGreenChannel(nodes, node.location[1])
            links.new(node.outputs["Color"], invertGreen.inputs["Color"])
            links.new(invertGreen.outputs["Color"], normalShader.inputs["Color"])
        
        if flag == 7:
            if not "skn" in material.mgr_data.shader_name:
                mixedLightmapNode.inputs[0].default_value = 0.792
                links.new(uv_lightmap_node.outputs['UV'], node.inputs['Vector'])
                links.new(albedoNode.outputs['Color'], mixedLightmapNode.inputs[1])
                links.new(node.outputs['Color'], mixedLightmapNode.inputs[2])
                links.new(mixedLightmapNode.outputs['Color'], principled.inputs['Base Color'])