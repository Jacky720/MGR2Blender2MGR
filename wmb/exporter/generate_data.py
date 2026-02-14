# save data from Blender to Python object (still dependent on too many custom properties)
from ...utils.util import *
import bpy, math
from mathutils import Vector
from time import time
# these two are for bones
import numpy as np
import mathutils as mu
from .materials.material import c_material
from .materials.create_materials import c_materials
from ..slice_data import *

def getRealName(name):
    splitname = name.split('-')
    return '-'.join(splitname[1:-1])

class c_batch(object):
    def __init__(self, obj, vertexGroupIndex, indexStart, prev_numVertexes, boneSetIndex, vertexStart=0):
        self.vertexGroupIndex = vertexGroupIndex
        self.boneSetIndex = boneSetIndex
        self.vertexStart = vertexStart
        self.indexStart = indexStart
        self.numVertexes = len(obj.data.vertices) + prev_numVertexes
        self.numIndexes = len(obj.data.loops)
        self.numPrimitives = len(obj.data.polygons)
        self.blenderObj = obj

class c_batch_supplements(object):
    def __init__(self, startPointer, collectionName='WMB'):
        allBatches = [x for x in allObjectsInCollectionInOrder(collectionName) if x.type == "MESH"]
        allBatches = sorted(allBatches, key=lambda batch: batch['ID'])
        self.batchData = [[], [], [], []] # stupid pass by reference
        
        # sort meshes
        meshNames = []
        for obj in allBatches:
            obj_name = getRealName(obj.name)
            if obj_name not in meshNames:
                meshNames.append(obj_name)

        numMeshes = len(meshNames)
        meshNamesSorted = [None] * numMeshes
        apparentNewMeshes = []
        for meshName in meshNames:
            for obj in allBatches:
                obj_name = getRealName(obj.name)
                if obj_name == meshName:
                    if (meshNamesSorted[obj["meshGroupIndex"]] is None):
                        meshNamesSorted[obj["meshGroupIndex"]] = meshName
                    else: # someone made a new mesh and didn't fix it
                        apparentNewMeshes.append(meshName)
                    break
        
        for meshName in apparentNewMeshes:
            for i, name in enumerate(meshNamesSorted):
                if (name is not None):
                    continue
                meshNamesSorted[i] = meshName
                for obj in allBatches: # rename
                    if getRealName(obj.name) == meshName:
                        obj["meshGroupIndex"] = i
        
        # okay back to batch supplements
        for batch in allBatches:
            batchDatum = [0] * 4
            batchDatum[0] = batch['ID']
            batchDatum[1] = batch['meshGroupIndex']
            batchDatum[2] = batch.material_slots[0].material['ID']

            if not 'boneSetIndex' in batch: # this *probably* should never happen, that being said if it does happen I wont be suprised
                batch["boneSetIndex"] = -1

            batchDatum[3] = batch['boneSetIndex']
            if 'batchGroup' not in batch or batch['batchGroup'] < 0:
                batch['batchGroup'] = 0
            self.batchData[batch['batchGroup']].append(batchDatum)
        
        self.batchOffsets = [-1] * 4
        curOffset = startPointer + 32
        if curOffset % 16 > 0:
            curOffset += 16 - (curOffset % 16)
        for index, batchGroup in enumerate(self.batchData):
            if len(batchGroup) == 0:
                continue # break might work here
            #print(batchGroup)
            self.batchOffsets[index] = curOffset
            curOffset += 16 * len(batchGroup)
        
        self.supplementStructSize = curOffset - startPointer

class c_batches(object):
    def __init__(self, vertexGroupsCount, collectionName='WMB'):
    
        self.vertexGroupsCount = vertexGroupsCount
        
        def get_batches(self):
            batches = []
            currentVertexGroup = -1
            
            allBatches = [x for x in allObjectsInCollectionInOrder(collectionName) if x.type == "MESH"]
            indexNums = [0] * self.vertexGroupsCount
            vertexNums = [0] * self.vertexGroupsCount
            cur_indexStart = 0
            cur_numVertexes = 0
            ballin_index = 0
            boundingBoxXYZ, boundingBoxUVW = getGlobalBoundingBox()
            
            for obj in sorted(allBatches, key=lambda batch: batch['ID']):
                obj_name = obj.name.split('-')
                obj_vertexGroupIndex = int(obj_name[0])
                print('[+] Generating Batch', obj.name)
                if obj_vertexGroupIndex != currentVertexGroup:      # Start of new vertex group
                    indexNums[currentVertexGroup] = cur_indexStart
                    vertexNums[currentVertexGroup] = cur_numVertexes
                    currentVertexGroup = obj_vertexGroupIndex
                    cur_indexStart = indexNums[currentVertexGroup]
                    cur_numVertexes = vertexNums[currentVertexGroup]

                if 'boneSetIndex' in obj:
                    obj_boneSetIndex = obj['boneSetIndex']
                else:
                    obj_boneSetIndex = -1
                
                batches.append(c_batch(obj, obj_vertexGroupIndex, cur_indexStart, 0, obj_boneSetIndex, cur_numVertexes))
                if BALLIN and obj.get('batchGroup') == 0:
                    col = bpy.data.collections["WMB"]
                    Slice4Data(
                        SVector3(boundingBoxXYZ),
                        SVector3(boundingBoxUVW),
                        obj_vertexGroupIndex,  # Slice5Data index
                        len(batches) - 1,  # Submesh index
                        0, obj['Materials'][0],
                        1,
                        [],
                        SFaceSet(0, batches[-1].numVertexes, 0, batches[-1].numIndexes)
                    ).to_collection(ballin_index)
                    
                    # Keep previously generated array, just add one more sub-array
                    persist_slice5_array = []
                    
                    add_item_index = 0
                    while "5-%2d-array-%2d"%(obj_vertexGroupIndex,add_item_index) in col:
                        persist_slice5_array.append(
                            col["5-%2d-array-%2d"%(obj_vertexGroupIndex,add_item_index)]
                        )
                        add_item_index += 1
                    
                    # Get existing index, or append
                    if len(persist_slice5_array) > 0:
                        gen5_ind = [x.vertgroup_ind for x in Slice5Data.fetch_section()].index(obj_vertexGroupIndex)
                    else:
                        gen5_ind = len(Slice5Data.fetch_section())
                    Slice5Data(
                        obj_vertexGroupIndex,
                        0, 0,  # Slice1Data index, suspected
                        0 if any(k.startswith("3-") for k in col.keys()) else -1, 0,  # Slice3Data (materials) index, suspected
                        persist_slice5_array + [[ballin_index]]
                    ).to_collection(gen5_ind)
                    
                    ballin_index += 1
                cur_indexStart += batches[-1].numIndexes
                cur_numVertexes = batches[-1].vertexStart + batches[-1].numVertexes
            #print([batch.vertexStart for batch in batches])
            return batches

        self.batches = get_batches(self)
        self.batches_StructSize = len(self.batches) * 20

class c_boneIndexTranslateTable(object):
    def __init__(self, collectionName): # formerly included bones


        # Generate empty table
        fullLookup = [0xfff] * 0x1000
        
        # Populate the third level
        for i, bone in enumerate(getAllBonesInOrder("WMB")):
            if 'ID' not in bone: # generate later
                continue
            if not 0 <= bone['ID'] < 0x1000: # force re-generate
                del bone['ID']
                continue
            fullLookup[bone['ID']] = i

        newBones = []
        # Add new bones that dont have ID
        for i, bone in enumerate(getAllBonesInOrder("WMB")):
            if 'ID' in bone:
                continue
            for k in range(0x1000 - 1, 0, -1):
                if fullLookup[k] == 0xfff:
                    fullLookup[k] = i
                    bone['ID'] = k
                    print("Added new bone to table", bone.name, "assigning ID", bone['ID'])
                    newBones.append(bone)
                    break

        # Generate levels from fullLookup
        # The boneIndexTranslateTable is a compressed reverse lookup for bone IDs.
        self.firstLevel = [-1] * 0x10
        self.secondLevel = []
        self.thirdLevel = []

        # firstLevel -- skip ranges of 0x100 that are completely empty
        curIndex = 0x10
        for i in range(0x10):
            partialLookup = fullLookup[0x100 * i : 0x100 * (i + 1)]
            if all([x == 0xfff for x in partialLookup]):
                continue
            self.firstLevel[i] = curIndex
            curIndex += 0x10

        # secondLevel -- skip ranges of 0x10 that are completely empty
        for i in range(0x10):
            if self.firstLevel[i] == -1:
                continue
            # i corresponds to the start of a chunk of 0x100 bone indexes
            partialLookup = fullLookup[0x100 * i : 0x100 * (i + 1)]
            newSecondLevel = [-1] * 0x10
            for j in range(0x10):
                partialPartialLookup = partialLookup[0x10 * j : 0x10 * (j + 1)]
                if all([x == 0xfff for x in partialPartialLookup]):
                    continue
                newSecondLevel[j] = curIndex
                curIndex += 0x10

            self.secondLevel.extend(newSecondLevel)

        # thirdLevel -- just chunks from fullLookup according to secondLevel
        for i, firstLevelItem in enumerate(self.firstLevel):
            if firstLevelItem == -1:
                continue
            # -0x10 because the first level is considered under the same index system
            secondLevelPortion = self.secondLevel[firstLevelItem - 0x10 : firstLevelItem]
            for j, secondLevelItem in enumerate(secondLevelPortion):
                if secondLevelItem == -1:
                    continue
                self.thirdLevel.extend(fullLookup[i * 0x100 + j * 0x10 : i * 0x100 + (j + 1) * 0x10])


        self.firstLevel_Size = len(self.firstLevel)

        self.secondLevel_Size = len(self.secondLevel)   

        self.thirdLevel_Size = len(self.thirdLevel)

        self.boneIndexTranslateTable_StructSize = self.firstLevel_Size*2 + self.secondLevel_Size*2 + self.thirdLevel_Size*2

class c_boneSet(object):
    def __init__(self, boneMap, boneSets_Offset, collectionName='WMB'):

        def get_blender_boneSets(self):
            b_boneSets = []
            for obj in bpy.data.collections[collectionName].all_objects:
                if obj.type == 'ARMATURE':
                    for boneSet in obj.data['boneSetArray']:
                        if max(boneSet) > 255:
                            ShowMessageBox("Bone index %d outside of byte range, please reduce the number of bones in your model." % max(boneSet), "Too Many Bones", "ERROR")
                            print("Bone index %d outside of byte range, please reduce the number of bones in your model." % max(boneSet))
                            assert max(boneSet) <= 255
                        b_boneSets.append(boneSet)
                    break
            
            return b_boneSets

        def get_boneSets(self, b_boneSets, boneSets_Offset):
            boneSets = []

            b_offset = boneSets_Offset + len(b_boneSets) * 8
            

            for b_boneSet in b_boneSets:
                if b_offset % 16 > 0:
                    b_offset += 16 - (b_offset % 16)
                
                numBoneIndexes = len(b_boneSet)

                boneSets.append([b_offset, numBoneIndexes, b_boneSet])
                b_offset += len(b_boneSet)

            return boneSets, b_offset - boneSets_Offset
        
        blender_boneSets = get_blender_boneSets(self)

        self.boneSet, self.boneSet_StructSize = get_boneSets(self, blender_boneSets, boneSets_Offset)

        def get_boneSet_StructSize(self):
            boneSet_StructSize = len(self.boneSet) * 8
            for boneSet in self.boneSet:
                boneSet_StructSize += len(boneSet[2])
                
            return boneSet_StructSize

class c_b_boneSets(object):
    def __init__(self, collectionName='WMB'):
        # Find Armature
        for obj in bpy.data.collections[collectionName].all_objects:
            if obj.type == 'ARMATURE':
                amt = obj
                break

        #fuck it
        wmbCol = bpy.data.collections["WMB"]
        if 'mystery' in wmbCol and wmbCol['mystery']:
            return
        
        
        # Get boneSets
        b_boneSets = []
        allmeshes = [x for x in bpy.data.collections['WMB'].all_objects if x.type == 'MESH']
        allmeshes = sorted(allmeshes, key=lambda x: x['boneSetIndex'])
        for obj in allmeshes:
            vertex_group_bones = []
            if obj['boneSetIndex'] != -1:
                for group in obj.vertex_groups:
                    boneID = getBoneIndexByName("WMB", group.name)
                    if boneID != None:
                        vertex_group_bones.append(boneID)
                vertex_group_bones = sorted(vertex_group_bones)
                print(obj.name, vertex_group_bones)
                assert len(vertex_group_bones) > 0 # This mesh has no bone weights, it should have a boneSetIndex of -1
                if vertex_group_bones not in b_boneSets:
                    #if wmb4:
                    #    if len(b_boneSets) <= obj["boneSetIndex"]:
                    #        b_boneSets.append(vertex_group_bones)
                    #    else: # no idea how often this ends up called
                    #        b_boneSets[obj["boneSetIndex"]].extend(vertex_group_bones)
                    #else:
                    b_boneSets.append(vertex_group_bones)
                    obj["boneSetIndex"] = len(b_boneSets)-1
                else:#if not wmb4:
                    obj["boneSetIndex"] = b_boneSets.index(vertex_group_bones)
        
        #if wmb4:
        #    b_boneSets = [sorted(list(set(boneSet))) for boneSet in b_boneSets] # removing duplicates trick
        
        amt.data['boneSetArray'] = b_boneSets

def get_bone_tPosition(bone):
    if 'TPOSE_worldPosition' in bone:
        return Vector3(bone['TPOSE_worldPosition'][0], bone['TPOSE_worldPosition'][1], bone['TPOSE_worldPosition'][2])
    else:
        return Vector3(bone.head_local[0], bone.head_local[1], bone.head_local[2])

def get_bone_localPosition(bone):
    if bone.parent:
        if 'TPOSE_worldPosition' in bone.parent:
            parentTPosition = Vector3(bone.parent['TPOSE_worldPosition'][0], bone.parent['TPOSE_worldPosition'][1], bone.parent['TPOSE_worldPosition'][2])
            return get_bone_tPosition(bone) - parentTPosition
        else:
            return get_bone_tPosition(bone) - bone.parent.head_local
    else:
        return Vector3(0, 0, 0)

class c_bones(object):
    def __init__(self, collectionName='WMB'):

        def get_bones(self):
            _bones = []
            numBones = 0
            armatures = [x for x in bpy.data.collections[collectionName].all_objects if x.type == 'ARMATURE']
            for obj in armatures:
                numBones = len(obj.data.bones)
                first_bone = obj.data.bones[0]

            if numBones > 1:
                for bone in getAllBonesInOrder(collectionName):
                    ID = bone['ID']
                    
                    if bone.parent:
                        parentIndex = getAllBonesInOrder(collectionName).index(bone.parent)
                    else:
                        parentIndex = -1

                    #localPosition = Vector3(bone['localPosition'][0], bone['localPosition'][1], bone['localPosition'][2])

                    #localRotation = Vector3(bone['localRotation'][0], bone['localRotation'][1], bone['localRotation'][2])
                    #localScale = Vector3(1, 1, 1) # Same here but 1, 1, 1. Makes sense. Bones don't "really" have scale.
                    
                    # APOSE_position
                    position = Vector3(bone.head_local[0], bone.head_local[1], bone.head_local[2])
                    
                    localRotation = [0, 0, 0]
                    rotation = [0, 0, 0]
                    
                    tPosition = [0, 0, 0]
                    localPosition = [0, 0, 0]
                    
                    armature = [x for x in bpy.data.collections[collectionName].all_objects if x.type == "ARMATURE"][0]
                    for pBone in armature.pose.bones:
                        if pBone.name == bone.name:
                            #localRotation
                            mat = pBone.matrix_basis.inverted().to_euler()
                            localRotation[0] = mat.x
                            localRotation[1] = mat.y
                            localRotation[2] = mat.z

                            #rotation
                            full_rot_mat = pBone.matrix_basis.inverted().copy()
                            for parent_pb in pBone.parent_recursive:
                                full_rot_mat = parent_pb.matrix_basis.inverted() @ full_rot_mat
                            euler = full_rot_mat.to_euler()
                            rotation[0] = euler.x
                            rotation[1] = euler.y
                            rotation[2] = euler.z
                            
                            #TPOSE_worldPosition
                            full_trans = pBone.head
                            tPosition[0] = full_trans.x
                            tPosition[1] = full_trans.y
                            tPosition[2] = full_trans.z

                            #TPOSE_localPosition
                            trans = pBone.head - (pBone.parent.head if pBone.parent else mu.Vector([0, 0, 0]))
                            localPosition[0] = trans[0]
                            localPosition[1] = trans[1]
                            localPosition[2] = trans[2]
                            # it's funny that I'm copying all this useless garbage
                            break
                    
                    localScale = Vector3(1, 1, 1)                           
                    scale = localScale
                    
                    blenderName = bone.name

                    bone = [ID, parentIndex, localPosition, localRotation, localScale.xyz, position.xyz, rotation, scale.xyz, tPosition, blenderName]
                    _bones.append(bone)
                
            elif numBones == 1:
                bone = getAllBonesInOrder(collectionName)[0]
                ID = bone['ID']
                parentIndex = -1
                
                #localPosition = Vector3(bone['localPosition'][0], bone['localPosition'][1], bone['localPosition'][2])
                trans = bone.head - mu.Vector([0, 0, 0])
                localPosition = [0, 0, 0]
                localPosition[0] = trans[0]
                localPosition[1] = trans[1]
                localPosition[2] = trans[2] # or list()?
                
                localRotation = Vector3(0, 0, 0) # I haven't seen anything here besides 0, 0, 0.
                localScale = Vector3(1, 1, 1) # Same here but 1, 1, 1. Makes sense. Bones don't "really" have scale.

                position = localPosition
                rotation = localRotation
                scale = localScale

                tPosition = localPosition

                blenderName = bone.name
                bone = [ID, parentIndex, localPosition, localRotation.xyz, localScale.xyz, position, rotation.xyz, scale.xyz, tPosition, blenderName]
                _bones.append(bone)

            return _bones
                        
        self.bones = get_bones(self)
        self.bones_StructSize = len(self.bones) * 32

def getColMeshIndex(objToFind):
    colMeshObjs = [obj for obj in bpy.data.collections['WMB'].all_objects if obj.type == 'MESH']
    for i, obj in enumerate(colMeshObjs):
        if obj == objToFind:
            return i
    return -1

# Basic generation algorithm:
# 1. Find unassigned mesh with the largest volume and create a volume for it.
# 2. Look for any other meshes that are also in aforementioned volume and assign to it.
# 3. If no more meshes can be assigned to the volume, return to step 1 until all meshes are assigned to a volume.

def generate_colTreeNodes():
    print("[+] Generating custom colTreeNodes")
    # Create and setup collection
    colCollection = bpy.data.collections.get("WMB")
    custom_colTreeNodesCollection = bpy.data.collections.get("custom_wmb_colTreeNodes")
    if not custom_colTreeNodesCollection:
        custom_colTreeNodesCollection = bpy.data.collections.new("custom_wmb_colTreeNodes")
        colCollection.children.link(custom_colTreeNodesCollection)
    for obj in [o for o in custom_colTreeNodesCollection.objects]:
        bpy.data.objects.remove(obj)

    # Create Root Node
    rootNode = bpy.data.objects.new("custom_Root_wmb", None)
    rootNode.hide_viewport = True
    custom_colTreeNodesCollection.objects.link(rootNode)
    rootNode.rotation_euler = (math.radians(90),0,0)

    unassigned_objs = [obj for obj in bpy.data.collections['WMB'].all_objects if obj.type == 'MESH']

    nodes = []
    while len(unassigned_objs) > 0:
        largest_obj = max(unassigned_objs, key=lambda x: getObjectVolume(x))
        unassigned_objs.remove(largest_obj)

        sub_objects = []
        for obj in unassigned_objs:
            #if len(sub_objects) >= 15:    # Do not put more than 15 + 1 meshes in a volume
            #    break

            if volumeInsideOther(getObjectCenter(obj), obj.dimensions, getObjectCenter(largest_obj), largest_obj.dimensions):
                sub_objects.append(obj)

        for obj in sub_objects:
            unassigned_objs.remove(obj)

        # Create Empty
        colEmptyName = str(len(nodes)) + "_wmb"
        colEmpty = bpy.data.objects.new(colEmptyName, None)
        custom_colTreeNodesCollection.objects.link(colEmpty)
        colEmpty.parent = rootNode
        colEmpty.empty_display_type = 'CUBE'

        colEmpty.location = getObjectCenter(largest_obj)
        colEmpty.scale = np.divide(largest_obj.dimensions, 2)

        meshIndices = [getColMeshIndex(largest_obj)]
        for obj in sub_objects:
            meshIndices.append(getColMeshIndex(obj))

        colEmpty["meshIndices"] = meshIndices

        # Create Custom ColTreeNode
        node = custom_ColTreeNode()
        node.index = len(nodes)
        node.bObj = colEmpty
        node.position = colEmpty.location
        node.scale = colEmpty.scale
        node.meshIndices = meshIndices
        node.meshIndexCount = len(node.meshIndices)

        colEmpty.name = str(node.index) + "_" + str(node.left) + "_" + str(node.right) + "_wmb"

        nodes.append(node)

    print("   [>] Number of leaf nodes generated...", len(nodes))

    # Start connecting leaf nodes up into tree
    deepest_nodes = nodes
    while len(deepest_nodes) > 1:
        deepest_nodes_sorted = sorted(deepest_nodes, key=lambda x: x.getVolume())
        joined_nodes = []
        new_nodes = []
        for i in range(len(deepest_nodes_sorted)-1):
            if deepest_nodes_sorted[i] in joined_nodes:
                continue
            closest_dist = getDistanceTo(deepest_nodes_sorted[i].position, deepest_nodes_sorted[i+1].position)
            closest_node = deepest_nodes_sorted[i+1]
            for j in range(len(deepest_nodes_sorted)):
                if deepest_nodes_sorted[i] == deepest_nodes_sorted[j] or deepest_nodes_sorted[j] in joined_nodes:
                    continue
                dist = getDistanceTo(deepest_nodes_sorted[i].position, deepest_nodes_sorted[j].position)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_node = deepest_nodes_sorted[j]
            
            # deepest_Nodes[i] and closest_node should be joined
            colEmptyName = str(len(nodes)) + "_wmb"
            colEmpty = bpy.data.objects.new(colEmptyName, None)
            custom_colTreeNodesCollection.objects.link(colEmpty)
            colEmpty.parent = rootNode
            colEmpty.empty_display_type = 'CUBE'
            loc, scale = getVolumeSurrounding(deepest_nodes_sorted[i].position, deepest_nodes_sorted[i].scale*2, closest_node.position, closest_node.scale*2)

            colEmpty.location = loc
            colEmpty.scale = scale

            node = custom_ColTreeNode()
            node.index = len(nodes)
            node.bObj = colEmpty
            node.position = colEmpty.location
            node.scale = colEmpty.scale
            node.left = deepest_nodes_sorted[i].index
            node.right = closest_node.index

            colEmpty.name = str(node.index) + "_" + str(node.left) + "_" + str(node.right) + "_wmb"

            joined_nodes.append(deepest_nodes_sorted[i])
            joined_nodes.append(closest_node)
            nodes.append(node)
            new_nodes.append(node)


        unassigned_nodes= []
        for node in deepest_nodes_sorted:
            if node not in joined_nodes:
                unassigned_nodes.append(node)

        deepest_nodes = new_nodes + unassigned_nodes
        print("   [>] Number of new nodes generated for upper level...", len(deepest_nodes))

    # Let's fix the ordering of the tree in Blender
    indexOffset = len(nodes) - 1
    for node in nodes:
        node.index = indexOffset - node.index
        if (node.left != -1):
            node.left = indexOffset - node.left
        if (node.left != -1):
            node.right = indexOffset - node.right
        node.bObj.name = str(node.index) + "_" + str(node.left) + "_" + str(node.right) + "_wmb"

    # Clean up Blender's duplicate nam
    for node in nodes:
        splitName = node.bObj.name.split(".")
        node.bObj.name = splitName[0]


    nodes = sorted(nodes, key=lambda x: x.index) 
    return nodes

def updateMeshColTreeNodeIndices(colTreeNodes):
    batchObjs = [obj for obj in bpy.data.collections['WMB'].all_objects if obj.type == 'MESH']

    for node in colTreeNodes:
        for meshIndex in node.meshIndices:
            batchObjs[meshIndex]["colTreeNodeIndex"] = node.index

class c_colTreeNodes(object):
    def __init__(self):
        def get_colTreeNodes():
            customColTreeNodes = generate_colTreeNodes()
            updateMeshColTreeNodeIndices(customColTreeNodes)

            colTreeNodes = []
            #b_colTreeNodes = bpy.context.scene['colTreeNodes']
            for node in customColTreeNodes:
                colTreeNodes.append([node.position, node.scale, node.left, node.right])
            """
            for key in b_colTreeNodes.keys():
                val = b_colTreeNodes[key]
                p1 = [val[0], val[1], val[2]]
                p2 = [val[3], val[4], val[5]]
                left = int(val[6])
                right = int(val[7])
                colTreeNodes.append([p1, p2, left, right])
            """
            return colTreeNodes

        def get_colTreeNodesSize(colTreeNodes):
            colTreeNodesSize = len(colTreeNodes) * 32
            return colTreeNodesSize

        self.colTreeNodes = get_colTreeNodes()
        self.colTreeNodesSize = get_colTreeNodesSize(self.colTreeNodes)
        self.colTreeNodesCount = len(self.colTreeNodes)

def getObjectCenter(obj):
    obj_local_bbox_center = 0.125 * sum((Vector(b) for b in obj.bound_box), Vector())
    #obj_global_bbox_center = obj.matrix_world @ obj_local_bbox_center
    return obj_local_bbox_center

def getMeshBoundingBox(meshObj):
    xVals = []
    yVals = []
    zVals = []

    meshName = getRealName(meshObj.name)
    for obj in (x for x in bpy.data.collections['WMB'].all_objects if x.type == "MESH"):
        if getRealName(obj.name) == meshName:
            xVals.extend([getObjectCenter(obj)[0] - obj.dimensions[0]/2, getObjectCenter(obj)[0] + obj.dimensions[0]/2])
            yVals.extend([getObjectCenter(obj)[1] - obj.dimensions[1]/2, getObjectCenter(obj)[1] + obj.dimensions[1]/2])
            zVals.extend([getObjectCenter(obj)[2] - obj.dimensions[2]/2, getObjectCenter(obj)[2] + obj.dimensions[2]/2])

    minX = min(xVals)
    maxX = max(xVals)
    minY = min(yVals)
    maxY = max(yVals)
    minZ = min(zVals)
    maxZ = max(zVals)

    midPoint = [(minX + maxX)/2, (minY + maxY)/2, (minZ + maxZ)/2]
    scale = [maxX - midPoint[0], maxY - midPoint[1], maxZ - midPoint[2]]
    return midPoint, scale

class c_mesh(object):
    def __init__(self, offsetMeshes, numMeshes, obj, meshIDOffset=0, collectionName='WMB', batchDescriptions=None):

        def get_BoundingBox(self, obj):
            midPoint, scale = getMeshBoundingBox(obj)
            return midPoint + scale

        def get_materials(self, obj):
            materials = []
            obj_mesh_name = getRealName(obj.name)
            for mesh in (x for x in allObjectsInCollectionInOrder(collectionName) if x.type == "MESH"):
                if getRealName(mesh.name) == obj_mesh_name:
                    for slot in mesh.material_slots:
                        material = slot.material
                        if "-x-" in material.name:
                            continue
                        for indx, mat in enumerate(getUsedMaterials(collectionName)):
                            if mat == material:
                                matID = indx
                                if matID not in materials:
                                    materials.append(matID)

            materials.sort()
            return materials

        def get_bones(self, obj):
            bones = []
            numBones = 0
            obj_mesh_name = getRealName(obj.name)
            for mesh in (x for x in allObjectsInCollectionInOrder(collectionName) if x.type == "MESH"):
                if getRealName(mesh.name) == obj_mesh_name:
                    for vertexGroup in mesh.vertex_groups:
                        boneName = getBoneIndexByName("WMB", vertexGroup.name)
                        if boneName not in bones:
                            if boneName is None:
                                bones.append(0xff)
                            else:
                                bones.append(boneName)
                            numBones += 1
            if len(bones) == 0:
                bones.append(0)

            bones.sort()
            return bones, numBones
      
        self.bones, self.numBones = get_bones(self, obj)

        self.nameOffset = offsetMeshes + numMeshes * 68

        self.boundingBox = get_BoundingBox(self, obj)

        self.name = getRealName(obj.name)
        
        # TODO this is just broken add a separate parameter
        # detects SCR export
        # if collectionName != 'WMB':
        #     self.name = 'SCR_MESH'
        self.batches0 = []
        self.batches1 = []
        self.batches2 = []
        self.batches3 = []
        for mesh in (x for x in allObjectsInCollectionInOrder(collectionName) if x.type == "MESH"):
            if getRealName(mesh.name) == getRealName(obj.name):
                if 'batchGroup' not in mesh:
                    mesh['batchGroup'] = 0
                relevantBatchData = batchDescriptions.batchData[mesh['batchGroup']]
                idToAppend = [x[0] for x in relevantBatchData].index(mesh['ID'])
                if mesh['batchGroup'] == 0:
                    self.batches0.append(idToAppend)
                elif mesh['batchGroup'] == 1:
                    self.batches1.append(idToAppend)
                elif mesh['batchGroup'] == 2:
                    self.batches2.append(idToAppend)
                elif mesh['batchGroup'] == 3:
                    self.batches3.append(idToAppend)
        
        # this code was garbage let us never speak of it again
        """
        self.batches = sorted(self.batches)
        
        if meshIDOffset == 0:
            prevBatch = self.batches[0] - 1
            for batch in self.batches:
                if prevBatch + 1 < batch:
                    meshIDOffset = batch - 1
                    break
                prevBatch = batch
        
        self.batches0 = self.batches
        self.batches1 = []
        self.batches2 = []
        self.batches3 = []
        if meshIDOffset > 0:
            for i, batch in enumerate(self.batches):
                if batch > meshIDOffset:
                    self.batches0 = self.batches[0:i]
                    self.batches3 = self.batches[i:]
                    break
            
            self.batches3 = [batch - meshIDOffset - 1 for batch in self.batches3]
        """
        
        #print(self.name, self.batches0, self.batches1, self.batches2, self.batches3)
        
        self.meshIDOffset = meshIDOffset
        
        self.batch0Pointer = self.nameOffset + len(self.name) + 1
        
        self.batch1Pointer = self.batch0Pointer
        self.batch1Pointer += len(self.batches0) * 2
        if (self.batch1Pointer % 16) > 0:
            self.batch1Pointer += 16 - (self.batch1Pointer % 16)
        
        self.batch2Pointer = self.batch1Pointer
        self.batch2Pointer += len(self.batches1) * 2
        if (self.batch2Pointer % 16) > 0:
            self.batch2Pointer += 16 - (self.batch2Pointer % 16)
        
        self.batch3Pointer = self.batch2Pointer
        self.batch3Pointer += len(self.batches2) * 2
        if (self.batch3Pointer % 16) > 0:
            self.batch3Pointer += 16 - (self.batch3Pointer % 16)
        
        self.offsetMaterials = self.batch3Pointer
        self.offsetMaterials += len(self.batches3) * 2
        if (self.offsetMaterials % 16) > 0:
            self.offsetMaterials += 16 - (self.offsetMaterials % 16)
        
        if len(self.batches1) == 0:
            self.batch1Pointer = 0
        if len(self.batches2) == 0:
            self.batch2Pointer = 0
        if len(self.batches3) == 0:
            self.batch3Pointer = 0

        self.materials = get_materials(self, obj)

        self.numMaterials = len(self.materials)

        self.offsetBones = 0 
        self.numBones = 0    
        self.lastOffset = self.offsetMaterials

        def get_mesh_StructSize(self):
            mesh_StructSize = 68 + len(self.name) + 1
            #print(mesh_StructSize % 16)
            mesh_StructSize += self.offsetMaterials - self.batch0Pointer
            mesh_StructSize += len(self.materials) * 2
            return mesh_StructSize

        self.mesh_StructSize = get_mesh_StructSize(self)

        self.blenderObj = obj

class c_meshes(object):
    def __init__(self, offsetMeshes, collectionName='WMB', batchDescriptions=None):
        
        self.meshIDOffset = 0
        def get_meshes(self, offsetMeshes):
            meshes = []

            meshNames = []
            
            for obj in (x for x in allObjectsInCollectionInOrder(collectionName) if x.type == "MESH"):
                obj_name = getRealName(obj.name)
                if obj_name not in meshNames:
                    meshNames.append(obj_name)

            numMeshes = len(meshNames)

            #sort mesh names by meshGroupIndex
            meshNamesSorted = [None] * numMeshes
            for meshName in meshNames:
                for obj in (x for x in allObjectsInCollectionInOrder(collectionName) if x.type == "MESH"):
                    obj_name = getRealName(obj.name)
                    if obj_name == meshName:
                        meshNamesSorted[obj["meshGroupIndex"]] = meshName
                        break
            print("Meshes to generate:", meshNamesSorted)

            meshes_added = []
            # first name pointer is aligned
            catchPadding = 0
            if (offsetMeshes + numMeshes*68) % 16 > 0:
                catchPadding = 16 - ((offsetMeshes + numMeshes*68) % 16)
                offsetMeshes += catchPadding
            
            for meshName in meshNamesSorted:
                for obj in (x for x in allObjectsInCollectionInOrder(collectionName) if x.type == "MESH"):
                    obj_name = getRealName(obj.name)
                    if obj_name == meshName:
                        if obj_name not in meshes_added:
                            print('[+] Generating Mesh', meshName)
                            mesh = c_mesh(offsetMeshes, numMeshes, obj, self.meshIDOffset, collectionName, batchDescriptions)
                            self.meshIDOffset = mesh.meshIDOffset
                            meshes.append(mesh)
                            meshes_added.append(obj_name)
                            offsetMeshes += mesh.mesh_StructSize
                            offsetMeshes -= 68
                            break

            return meshes, catchPadding

        def get_meshes_StructSize(self, meshes):
            meshes_StructSize = 0
            for mesh in meshes:
                meshes_StructSize += mesh.mesh_StructSize
            return meshes_StructSize

        self.meshes, catchPadding = get_meshes(self, offsetMeshes)

        #self.meshes_StructSize = newOffset - offsetMeshes
        #print(newOffset, newOffset - offsetMeshes)
        self.meshes_StructSize = get_meshes_StructSize(self, self.meshes) + catchPadding

class c_mystery(object):
    def __init__(self, mysteryPointer):
        def mystery1(offset):
            values = Slice1Data.fetch_section()
            mysteryValues = []
            currentOffset = offset
            currentOffset += 8 * len(values)
            if (currentOffset % 16) > 0:
                currentOffset += 16 - (currentOffset % 16)
            for data in values:
                appendVal = {
                    "offsetName": currentOffset,
                    "name": data.name,
                    "parent": data.parent_ind,
                    "short_6": data.unk_6
                }
                currentOffset += len(data.name) + 1
                mysteryValues.append(appendVal)
            
            return {"size": currentOffset - offset, "content": mysteryValues}
                
        def mystery2(offset):
            values = Slice2Data.fetch_section()
            mysteryValues = []
            currentOffset = offset
            currentOffset += 60 * len(values)
            for data in values:
                appendVal = {
                    "vec_0": data.unk_0,
                    "flag_C": [data.unk_C, data.unk_E],
                    "vec_10": data.unk_10,
                    "flag_1C": [data.unk_1C, data.unk_1E],
                    "vec_20": data.unk_20,
                    "flag_2C": [data.unk_2C, data.unk_2E],
                    "vec_30": data.unk_30
                }
                mysteryValues.append(appendVal)
            return {"size": currentOffset - offset, "content": mysteryValues}
                
        def mystery3(offset):
            # ik ik it's incomprehensible
            values = Slice3Data.fetch_section()
            mysteryValues = []
            currentOffset = offset
            currentOffset += 8 * len(values)
            if (currentOffset % 16) > 0:
                currentOffset += 16 - (currentOffset % 16)
            for data in values:
                #print(data, data.entries)
                appendVal = {
                    "content": [{
                        "vecs": [dd.unk_0,
                                 dd.unk_C,
                                 dd.unk_18,
                                 dd.unk_24,
                                 dd.unk_30],
                        "material": dd.mat_index
                    } for dd in data.entries],
                    "offset": currentOffset
                }
                currentOffset += 64 * len(data.entries) # 5 vector3's + 1 int/group
                mysteryValues.append(appendVal)
            return {"size": currentOffset - offset, "content": mysteryValues}
                
        def mystery4(offset):
            values = Slice4Data.fetch_section()
            mysteryValues = []
            currentOffset = offset
            currentOffset += 60 * len(values)
            for data in values:
                appendVal = {
                    "vec_0": data.unk_0,
                    "vec_C": data.unk_C,
                    "ref5": data.chunk5_ind,
                    "refBatch": data.batch_ind,
                    "short_20": data.unk_20,
                    "short_22": data.unk_22,
                    "int_24": data.unk_24,
                    "array": data.unk_array,
                    "faces": data.faces,
                    "offset": currentOffset if (len(data.unk_array) > 0) else 0
                }
                currentOffset += 4 * len(data.unk_array)
                mysteryValues.append(appendVal)
            
            if (currentOffset % 16) > 0:
                currentOffset += 16 - (currentOffset % 16)
            return {"size": currentOffset - offset, "content": mysteryValues}
                
        def mystery5(offset):
            values = Slice5Data.fetch_section()
            mysteryValues = []
            currentOffset = offset
            mysteryD = []
            currentOffset += 20 * len(values)
            if (currentOffset % 16) > 0:
                currentOffset += 16 - (currentOffset % 16)
            for data in values:
                appendVal = {
                    "refVertexGroup": data.vertgroup_ind,
                    "ref1": data.chunk1_ind,
                    "short_6": data.unk_6,
                    "ref3": data.chunk3_ind,
                    "short_A": data.unk_A,
                    "array": data.unk_array,
                    "offset": currentOffset,
                    "offsetTwo": []
                }
                currentOffset += 8 * len(data.unk_array)
                if (currentOffset % 16) > 0:
                    currentOffset += 16 - (currentOffset % 16)
                for nums in data.unk_array:
                    appendVal["offsetTwo"].append(currentOffset)
                    currentOffset += 2 * len(nums)
                    if (currentOffset % 16) > 0:
                        currentOffset += 16 - (currentOffset % 16)
                mysteryValues.append(appendVal)
            return {"size": currentOffset - offset, "content": mysteryValues}
                
        def mystery6(offset):
            values = Slice6Data.fetch_section()
            mysteryValues = []
            currentOffsetA = offset
            currentOffsetA += 16 * len(values)
            currentOffsetB = currentOffsetA
            for data in values:
                currentOffsetB += 16 * len(data.data.vertexes)
            for data in values:
                appendVal = {
                    "vertexes": data.data.vertexes,
                    "faces": data.data.faces,
                    "offsetVert": currentOffsetA,
                    "offsetFace": currentOffsetB
                }
                currentOffsetA += 16 * len(data.data.vertexes) # vec4
                currentOffsetB += 2 * len(data.data.faces) # short
                mysteryValues.append(appendVal)
            return {"size": currentOffsetB - offset, "content": mysteryValues}
                
        def mystery7(offset):
            values = Slice7Data.fetch_section()
            mysteryValues = []
            currentOffset = offset
            currentOffset += 48 * len(values)
            for data in values:
                appendVal = {
                    "vec_0": data.unk_0,
                    "vec_C": data.unk_C,
                    "ref6": data.chunk6_ind,
                    "float_1C": data.unk_1C,
                    "faces": data.faces
                }
                mysteryValues.append(appendVal)
            return {"size": currentOffset - offset, "content": mysteryValues}
                
        def mystery8(offset):
            values = Slice8Data.fetch_section()
            mysteryValues = []
            currentOffset = offset
            currentOffset += 88 * len(values)
            for data in values:
                appendVal = {
                    "vec_0": data.unk_0,
                    "vec_10": data.unk_10,
                    "vec_20": data.unk_20,
                    "vec_30": data.unk_30,
                    "ref1": data.chunk1_ind,
                    "float_40": data.unk_40,
                    "float_44": data.unk_44,
                    "short_48": data.unk_48,
                    "short_4A": data.unk_4A,
                    "int_4C": data.unk_4C,
                    "ref7": data.chunk7_ind,
                    "int_54": data.unk_54
                }
                mysteryValues.append(appendVal)
            return {"size": currentOffset - offset, "content": mysteryValues}
                
        def mystery9(offset):
            values = Slice9Data.fetch_section()
            mysteryValues = []
            currentOffset = offset
            currentOffset += 12 * len(values)
            for data in values:
                appendVal = {
                    "short_0": data.unk_0,
                    "parent": data.parent,
                    "ref8": data.chunk8_ind,
                    "short_6": data.unk_6,
                    "int_8": data.unk_8
                }
                mysteryValues.append(appendVal)
            return {"size": currentOffset - offset, "content": mysteryValues}
                
        
        mysteryCounts = [0] * 9
        for key, value in bpy.data.collections['WMB'].items():
            if key[0].isnumeric():
                splitkey = key.split("-")
                i = int(splitkey.pop(0)) - 1
                j = int(splitkey.pop(0))
                if mysteryCounts[i] < j + 1:
                    mysteryCounts[i] = j + 1
        
        self.mysteryOffsets = [0] * 9
        self.mysteryCounts = mysteryCounts
        self.mysterySizes = [0] * 9
        self.mystery = []
        mysteryFuncs = [mystery1, mystery2, mystery3, mystery4, mystery5, mystery6, mystery7, mystery8, mystery9]
        for i in range(9):
            if i == 0:
                self.mysteryOffsets[i] = mysteryPointer + 9 * 8
                if (self.mysteryOffsets[i] % 16) > 0:
                    self.mysteryOffsets[i] += 16 - (self.mysteryOffsets[i] % 16)
            else:
                self.mysteryOffsets[i] = self.mysteryOffsets[i-1] + self.mysterySizes[i-1]
            self.mystery.append(mysteryFuncs[i](self.mysteryOffsets[i]))
            self.mysterySizes[i] = self.mystery[i]["size"]
        for i in range(9):
            if self.mysteryCounts[i] == 0:
                self.mysteryOffsets[i] = 0
        self.mystery_StructSize = self.mysteryOffsets[-1] + self.mysterySizes[-1] - mysteryPointer
        

class c_textures(object):
    def __init__(self, texturesPointer, materials):
        self.textures = []
        for mat in materials:
            #for tex in mat.textures:
            """
             1 (maybe 0 too) is first
             then 3
             then 5 OR 6
             then 7
             then 4 OR 9
             1 is BEFORE 7
             no 2 or 8
             1 is BEFORE 3... ok
             is it just skipping 2, 4, 8?
             wtf platinum
            """
            # Wonderful news! All of that was just because evens are a myth. They've been culled.
            #for index in [0, 1, 3, 5, 6, 7, 9, 10, 11, 12, 13]:
            for tex in mat.textures:
                if tex[1] not in (x[1] for x in self.textures):
                    self.textures.append([0x63, tex[1]]) # gotta fix these flags sometime
        
        #print(self.textures)
        self.textures_StructSize = 8 * len(self.textures)

class c_unknownWorldData(object):
    def __init__(self):
        def get_unknownWorldData():
            unknownWorldData = []
            b_unknownWorldData = bpy.context.scene['unknownWorldData']
            for key in b_unknownWorldData.keys():
                val = b_unknownWorldData[key]
                unknownWorldData.append([val[0], val[1], val[2], val[3], val[4], val[5]])
            return unknownWorldData

        def get_unknownWorldDataSize(unknownWorldData):
            unknownWorldDataSize = len(unknownWorldData) * 24
            return unknownWorldDataSize

        self.unknownWorldData = get_unknownWorldData()
        self.unknownWorldDataSize = get_unknownWorldDataSize(self.unknownWorldData)
        self.unknownWorldDataCount = len(self.unknownWorldData)

class c_vertexGroup(object):
    def __init__(self, vertexGroupIndex, vertexesStart, collectionName='WMB'):
        self.vertexGroupIndex = vertexGroupIndex
        self.vertexGroupStart = vertexesStart

        def get_blenderObjects(self):
            objs = {}
            meshes = sorted([x for x in allObjectsInCollectionInOrder(collectionName) if x.type == "MESH"], key=lambda mesh: mesh['ID'])
            
            for index, obj in enumerate(meshes):
                obj_name = obj.name.split('-')
                if int(obj_name[0]) == vertexGroupIndex:
                    if len(obj.data.uv_layers) == 0:
                        obj.data.uv_layers.new()
                    obj.data.calc_tangents()
                    #if len(obj_name) == 2:
                    #    objs[0] = obj # didn't put a number on the first one
                    #else:
                    #    objs[int(obj_name[-1])] = obj
                    objs[index] = obj

            blenderObjects = []
            for key in sorted (objs):
                blenderObjects.append(objs[key])
            print(blenderObjects)
            return blenderObjects
        
        self.blenderObjects = get_blenderObjects(self)
        
        def get_numVertices(self):
            numVertices = 0
            for obj in self.blenderObjects:
                numVertices += len(obj.data.vertices)
            return numVertices
        numVertices = get_numVertices(self)

        def get_numIndexes(self):
            numIndexes = 0
            for obj in self.blenderObjects:
                numIndexes += len(obj.data.polygons)
            return numIndexes * 3
        
        def get_blenderVertices(self):
            blenderVertices = []
            blenderObjects = self.blenderObjects

            for obj in blenderObjects:
                blenderVertices.append([obj.data.vertices, obj])
            return blenderVertices
            
        blenderVertices = get_blenderVertices(self)

        def get_blenderLoops(self, objOwner):
            blenderLoops = []
            blenderLoops += objOwner.data.loops

            return blenderLoops

        def get_blenderUVCoords(self, objOwner, loopIndex, uvSlot):
            if uvSlot > len(objOwner.data.uv_layers)-1:
                print(" - UV Maps Error: Not enough UV Map layers! (Tried accessing UV layer number", uvSlot + 1, "of object", objOwner.name, "but it does not exist. Adding one!")
                objOwner.data.uv_layers.new()
            uv_coords = objOwner.data.uv_layers[uvSlot].data[loopIndex].uv
            return [uv_coords.x, 1-uv_coords.y]

        # Has bones = TODO: new listing for these
        
        #print(len(self.blenderObjects[0].data.uv_layers))
        
        #print("   Vertex Group %d has vertexFlags %d" % (vertexGroupIndex, self.vertexFlags))
        
        vertexFormat = bpy.data.collections[collectionName]['vertexFormat']
        if vertexFormat in {0x10337, 0x00337}:
            self.vertexExDataSize = 8
        elif vertexFormat == 0x10137:
            self.vertexExDataSize = 4
        else:
            self.vertexExDataSize = 0

        def get_boneMap(self):
            boneMap = []
            for obj in bpy.data.collections[collectionName].all_objects:
                if obj.type == 'ARMATURE':
                    boneMapRef = obj.data["boneMap"]
                    for val in boneMapRef:
                        boneMap.append(val)
                    return boneMap

        self.boneMap = None

        def get_boneSet(self, boneSetIndex):
            boneSet = []
            if boneSetIndex == -1:
                return boneSet
            for obj in bpy.data.collections[collectionName].all_objects:
                if obj.type == 'ARMATURE':
                    boneSetArrayRef = obj.data["boneSetArray"][boneSetIndex]
                    #print(boneSetArrayRef)
                    #print(obj.data["boneSetArray"])
                    for val in boneSetArrayRef:
                        boneSet.append(val)
                    #print(boneSet)
                    return boneSet

        def get_vertexesData(self):
            vertexes = []
            vertexesExData = []
            # used for child constraints, define here to optimize
            possibleArmatures = [x for x in allObjectsInCollectionInOrder(collectionName) if x.type == "ARMATURE"]
            amt = possibleArmatures[0] if len(possibleArmatures) > 0 else None
            for bvertex_obj in blenderVertices:
                bvertex_obj_obj = bvertex_obj[1]
                print('   [>] Generating vertex data for object', bvertex_obj_obj.name)
                loops = get_blenderLoops(self, bvertex_obj_obj)
                sorted_loops = sorted(loops, key=lambda loop: loop.vertex_index)
                
                if 'boneSetIndex' in bvertex_obj_obj:
                    boneSet = get_boneSet(self, bvertex_obj_obj["boneSetIndex"])
                else:
                    bvertex_obj_obj["boneSetIndex"] = -1
                    boneSet = get_boneSet(self, -1)

                
                previousIndex = -1
                
                missingBones = set()
                
                for loop in sorted_loops:
                    if loop.vertex_index == previousIndex:
                        continue

                    previousIndex = loop.vertex_index
            
                    bvertex = bvertex_obj[0][loop.vertex_index]
                    # XYZ Position
                    position = [bvertex.co.x, bvertex.co.y, bvertex.co.z]

                    # Tangents
                    loopTangent = loop.tangent * 127
                    tx = int(loopTangent[0] + 127.0)
                    ty = int(loopTangent[1] + 127.0)
                    tz = int(loopTangent[2] + 127.0)
                    sign = 0xff if loop.bitangent_sign == -1 else 0

                    tangents = [tx, ty, tz, sign]

                    # Normal
                    normal = [loop.normal[0], loop.normal[1], loop.normal[2], 0]
                    #print(normal)
                    # what the fuck is this, 11 bit values?
                    """
                    if (normal[0] < 0):
                        normal[0] = -(0x400-normal[0])
                        normal[0] ^= 0x400
                    if (normal[1] < 0):
                        normal[1] = -(0x400-normal[1])
                        normal[1] ^= 0x400
                    if (normal[2] < 0):
                        normal[2] = -(0x200-normal[2])
                        normal[2] ^= 0x200
                    true_normal = normal[0] # bits 0-11
                    true_normal |= normal[1]<<11
                    true_normal |= normal[2]<<22
                    normal = true_normal
                    """
                    # help me chatgpt, you're my only hope
                    nx = int(round(normal[0] * float((1<<10)-1)))
                    ny = int(round(normal[1] * float((1<<10)-1)))
                    nz = int(round(normal[2] * float((1<<9 )-1)))
                    if nx < 0:
                        nx += (1 << 10)
                        nx ^= 1 << 10
                    if ny < 0:
                        ny += (1 << 10)
                        ny ^= 1 << 10
                    if nz < 0:
                        nz += (1 << 9)
                        nz ^= 1 << 9
                    normal = nx | (ny << 11) | (nz << 22)
                        
                    # UVs
                    uv_maps = []

                    uv1 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 0)
                    uv_maps.append(uv1)
                    
                    if vertexFormat == 0x10307:
                        uv2 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 1)
                        uv_maps.append(uv2)

                    # Bones
                    boneIndexes = []
                    boneWeights = []
                    if vertexFormat & 0x30 == 0x30:
                        # Bone Indices
                        for groupRef in bvertex.groups:
                            if len(boneIndexes) >= 4:
                                break
                            boneGroupName = bvertex_obj_obj.vertex_groups[groupRef.group].name
                            boneID = getBoneIndexByName(collectionName, boneGroupName)
                            if boneID is None: # nonexistent group epic fail
                                missingBones.add(boneGroupName)
                                continue
                            if boneID in boneSet:
                                boneSetIndx = boneSet.index(boneID)
                            else: # bone not in set? well fuck that
                                for obj in bpy.data.collections[collectionName].all_objects:
                                    if obj.type != 'ARMATURE':
                                        continue
                                    allbonesets = list(obj.data["boneSetArray"])
                                    boneSet = list(allbonesets[bvertex_obj_obj["boneSetIndex"]])
                                    if boneID not in boneSet:
                                        boneSet.append(boneID)
                                    allbonesets[bvertex_obj_obj["boneSetIndex"]] = boneSet
                                    obj.data["boneSetArray"] = allbonesets
                                    boneSetIndx = boneSet.index(boneID) # i swear to god # !!!
                                    break
                            
                            if boneSetIndx < 0 or boneSetIndx > 255:
                                print("Hmm, boneID of", boneSetIndx, "could be a problem...")
                                print(boneSet)
                            
                            boneIndexes.append(boneSetIndx)
                        
                        if len(boneIndexes) == 0:
                            print(len(vertexes) ,"- Vertex Weights Error: Vertex has no assigned groups. At least 1 required. Try using Blender's [Select -> Select All By Trait > Ungrouped Verts] function to find them.")

                        while len(boneIndexes) < 4:
                            boneIndexes.append(0)
                        
                        # Bone Weights
                        weights = [group.weight for group in bvertex.groups]

                        if len(weights) >  4:
                            print(len(vertexes), "- Vertex Weights Error: Vertex has weights assigned to more than 4 groups. Try using Blender's [Weights -> Limit Total] function.")
                            weights = weights[:4]
                        
                        if any([x < 0 for x in weights]):
                            print(len(vertexes), "- Vertex Weights Error: Vertex has negative bone weights.")
                            weights = [x if x > 0 else 0 for x in weights]
                        
                        weightsSum = sum(weights)

                        normalized_weights = []                                             # Force normalize the weights as Blender's normalization sometimes get some rounding issues.
                        for val in weights:
                            if val > 0:
                                normalized_weights.append(float(val)/weightsSum)
                            else:
                                normalized_weights.append(0)

                        for val in normalized_weights:
                            if len(boneWeights) >= 4:
                                break
                            weight = math.floor(val * 256.0)
                            if weight > 255:
                                weight = 255
                            boneWeights.append(weight)
                        
                        usableBoneWeightCount = len(boneWeights)
                        if usableBoneWeightCount == 0:
                            boneWeights.append(255)
                        
                        while len(boneWeights) < 4:
                            boneWeights.append(0)
                        
                        currentShiftWeight = 0
                        stuckBones = set()

                        while sum(boneWeights) < 255:                     # MOAR checks to make sure weights are normalized but in bytes. (A bit cheating but these values should make such a minor impact.)
                            boneWeights[currentShiftWeight] += 1
                            if boneWeights[currentShiftWeight] > 255:
                                boneWeights[currentShiftWeight] = 255
                                stuckBones.add(currentShiftWeight)
                                if len(stuckBones) == usableBoneWeightCount: # ok what the fuck, but just avoid the infinite loop
                                    break
                            currentShiftWeight = (currentShiftWeight + 1) % usableBoneWeightCount # minimize impact on one particular weight with this stuff

                        stuckBones = set()
                        
                        while sum(boneWeights) > 255:                     
                            boneWeights[currentShiftWeight] -= 1
                            if boneWeights[currentShiftWeight] < 0:
                                boneWeights[currentShiftWeight] = 0
                                stuckBones.add(currentShiftWeight)
                                if len(stuckBones) == usableBoneWeightCount: # ok what the fuck, but just avoid the infinite loop
                                    break
                            currentShiftWeight = (currentShiftWeight + 1) % usableBoneWeightCount # minimize impact on one particular weight with this stuff

                        if sum(boneWeights) != 255:                       # If EVEN the FORCED normalization doesn't work, say something :/
                            print(len(vertexes), "- Vertex Weights Error: Vertex has a total weight not equal to 1.0. Try using Blender's [Weights -> Normalize All] function.")
                        if not all([0 <= x < 256 for x in boneWeights]):
                            print(len(vertexes), "- Vertex Weights Error: Vertex weight is outside the standard byte range, absolutely giving up now, enjoy your writing error")
                    else:
                        for groupRef in bvertex.groups:
                            boneGroupName = bvertex_obj_obj.vertex_groups[groupRef.group].name
                            boneIndexes.append(getBoneIndexByName(collectionName, boneGroupName))
                            break

                    color = []
                    if vertexFormat >= 0x337:
                        if len (bvertex_obj_obj.data.vertex_colors) == 0:
                            print("Object had no vertex colour layer when one was expected - creating one.")
                            new_vertex_colors = bvertex_obj_obj.data.vertex_colors.new()
                        loop_color = bvertex_obj_obj.data.vertex_colors.active.data[loop.index].color
                        color = [int(loop_color[0]*255), int(loop_color[1]*255), int(loop_color[2]*255), int(loop_color[3]*255)]

                    vertexes.append([position, tangents, normal, uv_maps, boneIndexes, boneWeights, color])
                    
                    ##################################################
                    ###### Now lets do the extra data shit ###########
                    ##################################################
                    normal = []
                    uv_maps = []
                    color = []
                    if vertexFormat in {0x10337, 0x10137, 0x00337}:
                        if vertexFormat != 0x10137:
                            uv2 = get_blenderUVCoords(self, bvertex_obj_obj, loop.index, 1)
                            uv_maps.append(uv2)
                        loop_color = bvertex_obj_obj.data.vertex_colors.active.data[loop.index].color
                        color = [int(loop_color[0]*255), int(loop_color[1]*255), int(loop_color[2]*255), int(loop_color[3]*255)]
                    
                    vertexExData = [normal, uv_maps, color]
                    vertexesExData.append(vertexExData)
                
                if len(missingBones) > 0:
                    print("The following bones were not found on the armature: %s" % ', '.join(list(missingBones)))
            #print(hex(len(vertexes)))
            
            return vertexes, vertexesExData

        def get_indexes(self):
            indexesOffset = 0
            indexes = []
            for obj in self.blenderObjects:
                for loop in obj.data.loops:
                    indexes.append(loop.vertex_index + indexesOffset)

            # Reverse this loop order
            flip_counter = 0
            for i, index in enumerate(indexes):
                if flip_counter == 2:
                    # 2, 1, 0 -> 0, 1, 2
                    indexes[i], indexes[i-2] = indexes[i-2], index
                    flip_counter = 0
                    continue
                flip_counter += 1
            
            return indexes

        self.vertexSize = 32

        self.vertexOffset = self.vertexGroupStart                       
        self.vertexExDataOffset = self.vertexOffset + numVertices * self.vertexSize
        if self.vertexExDataSize == 0:
            self.vertexExDataOffset = 0

        self.unknownOffset = [0, 0]  # Don't question it, it's unknown okay?

        self.unknownSize = [0, 0]    # THIS IS UNKOWN TOO OKAY? LEAVE ME BE
        # *unknown

        self.numVertexes = numVertices

        self.indexBufferOffset = self.vertexOffset + numVertices * (self.vertexSize + self.vertexExDataSize)
        if self.indexBufferOffset % 16 > 0:
            self.indexBufferOffset += 16 - (self.indexBufferOffset % 16)
        
        self.numIndexes = get_numIndexes(self)

        self.vertexes, self.vertexesExData = get_vertexesData(self)
        
        self.indexes = get_indexes(self)

        self.vertexGroupSize = (self.indexBufferOffset - self.vertexOffset) + (self.numIndexes * 2)

class c_vertexGroups(object):
    def __init__(self, offsetVertexGroups, collectionName='WMB'):
        self.offsetVertexGroups = offsetVertexGroups
        
        # Alright, before we do anything, let's fix the mess that is object IDs
        allMeshes = [obj for obj in bpy.data.collections[collectionName].all_objects if obj.type == 'MESH']
        for i, obj in enumerate(allMeshes):
            if 'ID' not in obj:
                obj['ID'] = 900
            if 'batchGroup' in obj:
                obj['ID'] += 1000 * obj['batchGroup'] # make sure it's sorted by batch group
            # obj['ID'] += i # avoid duplicate items, more trouble than it's worth
        
        allIDs = sorted([obj['ID'] for obj in allMeshes])
        allMeshes = sorted(allMeshes, key=lambda batch: batch['ID']) # sort
        
        for obj in allMeshes:
            newID = allIDs.index(obj['ID'])
            allIDs[newID] = -1 # prevent duplicate objects getting the same index
            obj['ID'] = newID # masterstroke, fix the several-hundred sized gaps
        
        print("New IDs generated:")
        print([(obj.name, obj['ID']) for obj in allMeshes])
        
        # And mesh group IDs (grouping is based on name)
        allMeshGroupIDs = set()
        meshesWithNoMeshGroup = []
        meshGroupIDsByName = {}
        for obj in allMeshes:
            if 'meshGroupIndex' not in obj:
                meshesWithNoMeshGroup.append(obj)
                continue
            
            if getRealName(obj.name) in meshGroupIDsByName: # already have it?
                if meshGroupIDsByName[getRealName(obj.name)] == obj['meshGroupIndex']:
                    continue # already have it
                
                # you go into the regeneration chamber
                del obj['meshGroupIndex']
                meshesWithNoMeshGroup.append(obj)
                continue
            
            # ok let's add it to the 'already handled' group
            meshGroupIDsByName[getRealName(obj.name)] = obj['meshGroupIndex']
            allMeshGroupIDs.add(obj['meshGroupIndex'])
        
        for obj in meshesWithNoMeshGroup:
            if getRealName(obj.name) in meshGroupIDsByName:
                obj['meshGroupIndex'] = meshGroupIDsByName[getRealName(obj.name)]
                continue
            
            i = 0
            while i in allMeshGroupIDs:
                i += 1
            obj['meshGroupIndex'] = i
            allMeshGroupIDs.add(obj['meshGroupIndex'])
            meshGroupIDsByName[getRealName(obj.name)] = obj['meshGroupIndex']
        
        # fix gaps
        meshGroupIDList = sorted(list(allMeshGroupIDs))
        for obj in allMeshes:
            obj['meshGroupIndex'] = meshGroupIDList.index(obj['meshGroupIndex'])
        
        print("New mesh group IDs generated:")
        print([(obj.name, obj['meshGroupIndex']) for obj in allMeshes])
        
        # Bone set indexes handled earlier by c_b_boneSets
        
        # Material indexes lfg
        # first, I made this helper function regenerate all the IDs, so we can just...
        getUsedMaterials(collectionName)
        # don't even have to do anything with it, the IDs on the materials are good now
        for obj in allMeshes:
            if 'Materials' not in obj:
                obj['Materials'] = [-1]
            matCount = len(obj.material_slots)
            if matCount > 0:
                firstMat = obj.material_slots[0].material
                obj['Materials'][0] = firstMat['ID']
            else:
                obj['Materials'][0] = 0 # idk probably safe-ish
        
        

        def get_vertexGroups(self, offsetVertexGroups):
            vertexGroupIndex = []

            for obj in bpy.data.collections[collectionName].all_objects:
                if obj.type == 'MESH':
                    obj_name = obj.name.split('-')
                    obj_vertexGroupIndex = int(obj_name[0])
                    if obj_vertexGroupIndex not in vertexGroupIndex:
                        vertexGroupIndex.append(obj_vertexGroupIndex)

            vertexGroupIndex.sort()
            
            vertexGroupHeaderSize = 28
            
            vertexesOffset = offsetVertexGroups + len(vertexGroupIndex) * vertexGroupHeaderSize
            if vertexesOffset % 16 > 0:
                vertexesOffset += 16 - (vertexesOffset % 16)
            
            vertexGroups = []
            for index in vertexGroupIndex:
                print('[+] Creating Vertex Group', index)
                vertexGroups.append(c_vertexGroup(index, vertexesOffset, collectionName))
                vertexesOffset += vertexGroups[index].vertexGroupSize
                padAmount = 0
                if vertexesOffset % 16 > 0:
                    padAmount = 16 - (vertexesOffset % 16)
                    vertexesOffset += padAmount
                    vertexGroups[index].vertexGroupSize += padAmount
            
            if padAmount > 0: # no padding on end
                print("Removing excess padding of %d bytes from vertex group %d" % (padAmount, index))
                print("This leaves the offset at", hex(vertexesOffset-padAmount))
                vertexGroups[index].vertexGroupSize -= padAmount
            
            return vertexGroups

        self.vertexGroups = get_vertexGroups(self, self.offsetVertexGroups)

        def get_vertexGroupsSize(self, vertexGroups):
            vertexGroupsSize = len(vertexGroups) * 28
            if vertexGroupsSize % 16 > 0:
                vertexGroupsSize += 16 - (vertexGroupsSize % 16)

            for vertexGroup in vertexGroups:
                vertexGroupsSize += vertexGroup.vertexGroupSize
            return vertexGroupsSize

        self.vertexGroups_StructSize = get_vertexGroupsSize(self, self.vertexGroups)



class c_generate_data(object):
    def __init__(self, collectionName='WMB', BALLER=True):
        global BALLIN
        BALLIN = BALLER
        hasArmature = False
        hasColTreeNodes = False
        hasUnknownWorldData = False
        
        # Delete attack hitbox visualizers
        for obj in bpy.data.objects:
            if obj.name.startswith("Attack") and obj.type == "MESH":
                bpy.data.objects.remove(obj)
        
        if collectionName == 'WMB':
            collectionName = bpy.data.collections['WMB'].children[0].name
            print("\n\n===== Exporting collection %s, please remove other collections to ensure stable export =====\n\n" % collectionName)

        for obj in bpy.data.collections[collectionName].all_objects:
            if obj.type == 'ARMATURE':
                print('Armature found, exporting bones structures.')
                hasArmature = True
                break

        if 'colTreeNodes' in bpy.context.scene:
            hasColTreeNodes = True

        if 'unknownWorldData' in bpy.context.scene:
            hasUnknownWorldData = True

        # Generate custom boneSets from Blender vertex groups
        if hasArmature:
            self.b_boneSets = c_b_boneSets(collectionName)

        currentOffset = 0

        self.header_Offset = currentOffset
        self.header_Size = 112
        currentOffset += self.header_Size
        print('header_Size: ', self.header_Size)

        currentOffset += 16 - (currentOffset % 16)
        
        if 'vertexFormat' in bpy.data.collections[collectionName]:
            self.vertexFormat = bpy.data.collections[collectionName]['vertexFormat']
        else:
            self.vertexFormat = 65799
            bpy.data.collections[collectionName]['info'] = "Some of these properties were auto-generated... good luck"
            bpy.data.collections[collectionName]['vertexFormat'] = 65799
        
        if BALLIN:
            # FUCK YOU BALTIMORE
            # IF YOU'RE DUMB ENOUGH TO MAKE A DYNAMICALLY CUTTABLE MODEL THIS WEEKEND
            # YOU'RE A BIG ENOUGH SCHMUCK TO DELETE CUT GROUPS WITH RECKLESS ABANDON
            for key in list(bpy.data.collections["WMB"].keys()):
                if key[:1].isnumeric() and not key[:1] == "3":
                    del bpy.data.collections["WMB"][key]
            # Most default value here possible
            Slice1Data.store_section([Slice1Data()])
            
            # Slice4Data defined dynamically
            # Slice5Data defined dynamically
            
            boundingBoxXYZ, boundingBoxUVW = getGlobalBoundingBox()
            minX, maxX = boundingBoxXYZ[0] - boundingBoxUVW[0], boundingBoxXYZ[0] + boundingBoxUVW[0]
            minY, maxY = boundingBoxXYZ[1] - boundingBoxUVW[1], boundingBoxXYZ[1] + boundingBoxUVW[1]
            minZ, maxZ = boundingBoxXYZ[2] - boundingBoxUVW[2], boundingBoxXYZ[2] + boundingBoxUVW[2]
            Slice6Data.store_section([Slice6Data(SGeometry(
                # Vertexes (SVector4)
                [SVector4(minX, minY, minZ),
                 SVector4(maxX, minY, maxZ),
                 SVector4(minX, minY, maxZ),
                 SVector4(maxX, minY, minZ),
                 SVector4(maxX, maxY, minZ),
                 SVector4(minX, maxY, minZ),
                 SVector4(minX, maxY, maxZ),
                 SVector4(maxX, maxY, maxZ)],
                # Face indexes
                [0, 1, 2,
                 0, 3, 1,
                 0, 4, 3,
                 0, 5, 4,
                 0, 6, 5,
                 0, 2, 6,
                 3, 7, 1,
                 3, 4, 7,
                 2, 7, 6,
                 2, 1, 7,
                 5, 7, 4,
                 5, 6, 7]
            ))])
            
            Slice7Data.store_section([Slice7Data(
                SVector3(0.0, 0.0, 0.0),  # offset for Slice6Data coordinates
                SVector3(0.25, 0.25, 0.25),  # idk a scale factor or something
                0,  # Slice6Data index
                0.3,
                SFaceSet(0, 8, 0, 36)
            )])
            
            Slice8Data.store_section([Slice8Data(
                SVector4(0.0, -0.025317, 0.004611),
                SVector4(0.0, 0.0, 0.0),
                SVector4(0.0, 0.0, 0.0),
                SVector3(0.277, 0.230695, 0.273966),
                0,  # Slice1Data index
                1.0, 0.3,
                # Several default values...
                chunk7_ind = 0
            )])
            
            Slice9Data.store_section([Slice9Data(
                0,  # or -1?
                -1,  # parent (I think)
                0,  # index in Slice8Data?
                1,  # amount of referenced Slice8Data groups
                1  # 0 may be acceptable here
            )])
            
            # IF YOU CAN SLICE SIX FEET IN THE AIR STRAIGHT UP AND NOT CRASH THE GAME,
            # YOU GET NO DOWN PAYMENT

        self.vertexGroups_Offset = currentOffset
        self.vertexGroups = c_vertexGroups(self.vertexGroups_Offset, collectionName)
        self.vertexGroupsCount = len(self.vertexGroups.vertexGroups)
        self.vertexGroups_Size = self.vertexGroups.vertexGroups_StructSize
        currentOffset += self.vertexGroups_Size
        print('vertexGroups_Size: ', self.vertexGroups_Size)

        #currentOffset += 16 - (currentOffset % 16)
        
        self.batches_Offset = currentOffset
        self.batches = c_batches(self.vertexGroupsCount, collectionName)
        self.batches_Size = self.batches.batches_StructSize
        currentOffset += self.batches_Size
        print('batches_Size: ', self.batches_Size)

        #currentOffset += 16 - (currentOffset % 16)
        
        self.batchDescPointer = currentOffset
        self.batchDescriptions = c_batch_supplements(currentOffset, collectionName)
        self.batchDescSize = self.batchDescriptions.supplementStructSize
        currentOffset += self.batchDescSize
        print('batchDescSize: ', self.batchDescSize)
        
        #currentOffset += 16 - (currentOffset % 16)
        
        if hasArmature:
            self.boneIndexTranslateTable = c_boneIndexTranslateTable(collectionName)
        
            self.bones_Offset = currentOffset
            self.bones = c_bones(collectionName)
            self.numBones = len(self.bones.bones)
            self.bones_Size = self.bones.bones_StructSize
            currentOffset += self.bones_Size
            print('bones_Size: ', self.bones_Size)

            #currentOffset += 16 - (currentOffset % 16)

            self.boneIndexTranslateTable_Offset = currentOffset
            #self.boneIndexTranslateTable = c_boneIndexTranslateTable(self.bones, collectionName)
            self.boneIndexTranslateTable_Size = self.boneIndexTranslateTable.boneIndexTranslateTable_StructSize
            currentOffset += self.boneIndexTranslateTable_Size
            print('boneIndexTranslateTable_Size: ', self.boneIndexTranslateTable_Size)

            # psyche, this one is padded
            if (currentOffset % 16) > 0:
            #if True: # ??? ok not that
                currentOffset += 16 - (currentOffset % 16)
        else:
            self.bones_Offset = 0
            self.bones = None
            self.numBones = 0
            self.bones_Size = 0
            self.boneIndexTranslateTable_Offset = 0
            self.boneIndexTranslateTable_Size = 0

        self.boneMap = None
        self.numBoneMap = 0

        self.lods = None

        self.colTreeNodes = None
        self.colTreeNodes_Offset = 0
        self.colTreeNodesCount = 0

        if hasArmature:
            self.boneSets_Offset = currentOffset
            self.boneSet = c_boneSet(self.boneMap, self.boneSets_Offset, collectionName)
            self.boneSet_Size = self.boneSet.boneSet_StructSize
            currentOffset += self.boneSet_Size
            print('boneSet_Size: ', self.boneSet_Size)

            #currentOffset += 16 - (currentOffset % 16)
        else:
            self.boneMap_Offset = 0
            self.boneSets_Offset = 0

        self.materials_Offset = currentOffset
        self.materials = c_materials(self.materials_Offset, True, collectionName)
        self.materials_Size = self.materials.materials_StructSize
        currentOffset += self.materials_Size
        print('materials_Size: ', self.materials_Size)
        
        currentOffset += 16 - (currentOffset % 16)
        
        self.textures_Offset = currentOffset
        self.textures = c_textures(self.textures_Offset, self.materials.materials)
        self.textures_Size = self.textures.textures_StructSize
        # TODO fuck, this doesn't parse in the normal order... now I need to track every pointer # huh?
        currentOffset += self.textures_Size
        print('textures_Size: ', self.textures_Size)
        
        if currentOffset % 16 > 0:
            currentOffset += 16 - (currentOffset % 16)
        
        self.meshes_Offset = currentOffset
        self.meshes = c_meshes(self.meshes_Offset, collectionName, self.batchDescriptions)
        self.meshes_Size = self.meshes.meshes_StructSize
        currentOffset += self.meshes_Size
        print('meshes_Size: ', self.meshes_Size)
        
        if not hasArmature:
            for mesh in self.meshes.meshes:
                mesh.numBones = 0
        
        if "mystery" in bpy.data.collections['WMB'] and bpy.data.collections['WMB']["mystery"]:
            self.mystery_Offset = currentOffset #0xf32a2 for Sundowner testing
            self.mystery = c_mystery(self.mystery_Offset)
            currentOffset += self.mystery.mystery_StructSize
        else:
            self.mystery_Offset = 0
            self.mystery = None
