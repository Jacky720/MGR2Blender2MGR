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
    hasMixedAlbedo=False
    normalShader = None
    
    
    
    for i, texentry in enumerate(material.mgr_data.textures):
        if bpy.data.images.get(str(texentry.id) + ".dds") is not None:
            image_node = nodes.new(type='ShaderNodeTexImage')
            image_node.location = 0,i*-60
            image_node.image = bpy.data.images.get(str(texentry.id) + ".dds")
            image_node.hide = True
            image_node.label = consts.getTextureFlagFromDict(texentry.flag)
            if texentry.flag == 1:
                hasMixedAlbedo = True
                mixedAlbedoNode = nodes.new(type='ShaderNodeMixRGB')
                mixedAlbedoNode.location = 300, 100
                mixedAlbedoNode.hide = True
            
            node_dict[texentry.flag] = image_node
    

    
    for flag, node in node_dict.items():
        if flag == 0: # Base Color
            links.new(node.outputs['Color'], principled.inputs['Base Color'])
        
        if flag == 3:
            if normalShader == None:
                normalShader = nodes.new(type='ShaderNodeNormalMap')
                normalShader.location = 600, 0
                normalShader.hide = True
                links.new(normalShader.outputs['Normal'], principled.inputs['Normal'])
            
            invertGreen = invertGreenChannel(nodes, node.location[1])
            links.new(node.outputs["Color"], invertGreen.inputs["Color"])
            links.new(invertGreen.outputs["Color"], normalShader.inputs["Color"])