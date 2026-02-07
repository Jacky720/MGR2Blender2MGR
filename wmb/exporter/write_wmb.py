# write data from Python object to .wmb
from ...utils.ioUtils import write_Int32, write_uInt32, write_Int16, write_xyz, write_float, write_char, write_string, write_uInt16, SmartIO, write_byte, write_float16
from ...utils.util import *
from time import time
import bpy

def create_wmb_batches(wmb_file, data):
    wmb_file.seek(data.batches_Offset)

    for batch in data.batches.batches:
        write_uInt32(wmb_file, batch.vertexGroupIndex)                  # vertexGroupIndex
        write_uInt32(wmb_file, batch.vertexStart)                       # vertexStart
        write_uInt32(wmb_file, batch.indexStart)                        # indexStart
        write_uInt32(wmb_file, batch.numVertexes)                       # numVertexes
        write_uInt32(wmb_file, batch.numIndexes)                        # numIndexes

def create_wmb_batch_supplement(wmb_file, data):
    wmb_file.seek(data.batchDescPointer)
    
    for index, offset in enumerate(data.batchDescriptions.batchOffsets):
        if offset == -1:
            write_uInt32(wmb_file, 0)
        else:
            write_uInt32(wmb_file, offset)   # batch data group pointer
        
        write_uInt32(wmb_file, len(data.batchDescriptions.batchData[index])) # batch data group count
    
    for index, group in enumerate(data.batchDescriptions.batchData):
        if len(group) == 0:
            continue
        wmb_file.seek(data.batchDescriptions.batchOffsets[index])
        for batch in group:
            #print(batch)
            write_uInt32(wmb_file, batch[0]) # batchIndex
            write_uInt32(wmb_file, batch[1]) # meshIndex
            write_uInt16(wmb_file, batch[2]) # materialIndex
            write_Int16(wmb_file, batch[3]) # boneSetsIndex
            write_uInt32(wmb_file, 0x100)    # unknown10, hopefully just padding
            # TODO fuck it wasn't padding, sometimes 0x100 sometimes not

def create_wmb_boneIndexTranslateTable(wmb_file, data):
    wmb_file.seek(data.boneIndexTranslateTable_Offset)

    for entry in data.boneIndexTranslateTable.firstLevel:    # firstLevel
        write_Int16(wmb_file, entry)

    for entry in data.boneIndexTranslateTable.secondLevel:   # secondLevel
        write_Int16(wmb_file, entry)

    for entry in data.boneIndexTranslateTable.thirdLevel:    # thirdLevel
        write_Int16(wmb_file, entry)

def create_wmb_boneSet(wmb_file, data):
    wmb_file.seek(data.boneSets_Offset)

    for boneSet in data.boneSet.boneSet:
        write_uInt32(wmb_file, boneSet[0])
        write_uInt32(wmb_file, boneSet[1])
    
    for boneSet in data.boneSet.boneSet:
        wmb_file.seek(boneSet[0])
        for entry in boneSet[2]:
            write_byte(wmb_file, entry)

def create_wmb_bones(wmb_file, data):
    wmb_file.seek(data.bones_Offset)

    for index, bone in enumerate(data.bones.bones):               # [ID, parentIndex, localPosition.xyz, localRotation.xyz, localScale.xyz, position.xyz, rotation.xyz, scale.xyz, tPosition.xyz]
        write_Int16(wmb_file, bone[0])          # ID
        write_Int16(wmb_file, index)       # wrong order probably fine todo
        write_Int16(wmb_file, bone[1])   # parentIndex
        write_Int16(wmb_file, 0)       # rotationOrder or something
        write_xyz(wmb_file, bone[2])    # localPosition.xyz
        write_xyz(wmb_file, bone[5])    # position.xyz

def create_wmb_header(wmb_file, data, collectionName="WMB"):

    print('Writing header:')
    for char in 'WMB4':               # id
        write_char(wmb_file, char)                                 
    write_uInt32(wmb_file, 0)     # version
    write_uInt32(wmb_file, data.vertexFormat)
    
    if data.numBones > 0 or data.vertexFormat == 0x10307: # melon has referencebone?
        write_Int16(wmb_file, 0)
    elif collectionName != "WMB": # TODO a better check for SCR-ness
        write_Int16(wmb_file, 0)
    else:
        write_Int16(wmb_file, -1)
    
    if data.vertexFormat > 0x107: # TODO more precise
        write_Int16(wmb_file, -1)
    else:
        write_Int16(wmb_file, data.vertexGroups.vertexGroups[0].vertexes[0][4][0]) # bone index
    
    boundingBoxXYZ, boundingBoxUVW = getGlobalBoundingBox()
    write_xyz(wmb_file, boundingBoxXYZ) # boundingBox: x y z 
    write_xyz(wmb_file, boundingBoxUVW) #              u v w
    
    offsetVertexGroups = data.vertexGroups_Offset
    write_uInt32(wmb_file, offsetVertexGroups)                  # offsetVertexGroups
    print(' + offsetVertexGroups:           ', hex(offsetVertexGroups))

    numVertexGroups = len(data.vertexGroups.vertexGroups)
    write_uInt32(wmb_file, numVertexGroups)                     # numVertexGroups
    print(' + numVertexGroups:              ', numVertexGroups)
    
    offsetBatches = data.batches_Offset
    write_uInt32(wmb_file, offsetBatches)                       # offsetBatches
    print(' + offsetBatches:                ', hex(offsetBatches))

    numBatches = len(data.batches.batches)
    write_uInt32(wmb_file, numBatches)                          # numBatches
    print(' + numBatches:                   ', numBatches)
    
    batchDescPointer = data.batchDescPointer
    write_uInt32(wmb_file, batchDescPointer)
    print(' + batchDescPointer:             ', hex(batchDescPointer))
    
    offsetBones = data.bones_Offset
    write_uInt32(wmb_file, offsetBones)                          # offsetBones
    print(' + offsetBones:                  ', hex(offsetBones))

    numBones = data.numBones
    write_uInt32(wmb_file, numBones)                            # numBones
    print(' + numBones:                     ', numBones)
    
    offsetBoneIndexTranslateTable = data.boneIndexTranslateTable_Offset
    write_uInt32(wmb_file, offsetBoneIndexTranslateTable)       # offsetBoneIndexTranslateTable
    print(' + offsetBoneIndexTranslateTable:', hex(offsetBoneIndexTranslateTable))

    if hasattr(data, 'boneIndexTranslateTable'):
        boneTranslateTableSize = data.boneIndexTranslateTable.boneIndexTranslateTable_StructSize
    else:
        boneTranslateTableSize = 0
    write_uInt32(wmb_file, boneTranslateTableSize)              # boneTranslateTableSize
    print(' + boneTranslateTableSize:       ', boneTranslateTableSize)
    
    offsetBoneSets = data.boneSets_Offset                
    write_uInt32(wmb_file, offsetBoneSets)                      # offsetBoneSets
    print(' + offsetBoneSets:               ', hex(offsetBoneSets))

    if hasattr(data, 'boneSet'):
        numBoneSets = len(data.boneSet.boneSet)   
    else:
        numBoneSets = 0                          
    write_uInt32(wmb_file, numBoneSets)                         # numBoneSets
    print(' + numBoneSets:                  ', numBoneSets)
    
    offsetMaterials = data.materials_Offset
    write_uInt32(wmb_file, offsetMaterials)                     # offsetMaterials
    print(' + offsetMaterials:              ', hex(offsetMaterials))

    numMaterials = len(data.materials.materials)
    write_uInt32(wmb_file, numMaterials)                        # numMaterials
    print(' + numMaterials:                 ', numMaterials)
    
    offsetTextures = data.textures_Offset
    write_uInt32(wmb_file, offsetTextures)                     # offsetMaterials
    print(' + offsetTextures:               ', hex(offsetTextures))

    numTextures = len(data.textures.textures)
    write_uInt32(wmb_file, numTextures)                        # numMaterials
    print(' + numTextures:                  ', numTextures)
    
    offsetMeshes = data.meshes_Offset
    write_uInt32(wmb_file, offsetMeshes)                        # offsetMeshes
    print(' + offsetMeshes:                 ', hex(offsetMeshes))

    numMeshes = len(data.meshes.meshes)
    write_uInt32(wmb_file, numMeshes)                           # numMeshes
    print(' + numMeshes:                    ', numMeshes)
    
    offsetMystery = data.mystery_Offset
    write_uInt32(wmb_file, offsetMystery)
    print(' + offsetMystery:                ', offsetMystery)

def create_wmb_materials(wmb_file, data):
    wmb_file.seek(data.materials_Offset)

    for material in data.materials.materials:
        write_uInt32(wmb_file, material.offsetShaderName) # offsetShaderName
        write_uInt32(wmb_file, material.offsetTextures)
        write_uInt32(wmb_file, 0) # unknown08. pointer?
        write_uInt32(wmb_file, material.offsetParameterGroups)
        write_uInt16(wmb_file, 8) # what even
        write_uInt16(wmb_file, material.numTextures) # 5 or 4, usually
        write_uInt16(wmb_file, 0) # mystery value
        write_uInt16(wmb_file, material.numParameterGroups*4)
    for material in data.materials.materials:
        wmb_file.seek(material.offsetShaderName)
        write_string(wmb_file, material.shaderName)             # shaderName
        wmb_file.seek(material.offsetTextures)
        for i, texture in enumerate(material.textures):                       # [offsetName, texture, name]
            worked = False
            for key, value in enumerate(data.textures.textures):
                print(f"{value[1]} : {texture[1]}")
                if value[1] == texture[1]:
                    write_uInt32(wmb_file, material.textures[i][2])
                    write_uInt32(wmb_file, key)
                    worked = True
                    break
            if not worked:
                print("WARNING! Could not find texture", texture[1])
        
        wmb_file.seek(material.offsetParameterGroups)
        for parameterGroup in material.parameterGroups:
            for value in parameterGroup[3]:
                write_float(wmb_file, value)

def create_wmb_meshes(wmb_file, data):
    wmb_file.seek(data.meshes_Offset)

    for mesh in data.meshes.meshes:
        write_uInt32(wmb_file, mesh.nameOffset)             # nameOffset
        for val in mesh.boundingBox:                        # boundingBox [x, y, z, u, v, m]
            write_float(wmb_file, val)
        
        write_uInt32(wmb_file, mesh.batch0Pointer)
        write_uInt32(wmb_file, len(mesh.batches0))
        write_uInt32(wmb_file, mesh.batch1Pointer)
        write_uInt32(wmb_file, len(mesh.batches1))
        write_uInt32(wmb_file, mesh.batch2Pointer)
        write_uInt32(wmb_file, len(mesh.batches2))
        write_uInt32(wmb_file, mesh.batch3Pointer)
        write_uInt32(wmb_file, len(mesh.batches3))
        write_uInt32(wmb_file, mesh.offsetMaterials)        # offsetMaterials
        write_uInt32(wmb_file, mesh.numMaterials)           # numMaterials

    for mesh in data.meshes.meshes:
        wmb_file.seek(mesh.nameOffset)
        #print(wmb_file.tell(), mesh.name)
        write_string(wmb_file, mesh.name)                   # name
        wmb_file.seek(mesh.batch0Pointer)
        for batch in mesh.batches0:
            write_uInt16(wmb_file, batch)
        wmb_file.seek(mesh.batch1Pointer)
        for batch in mesh.batches1:
            write_uInt16(wmb_file, batch)
        wmb_file.seek(mesh.batch2Pointer)
        for batch in mesh.batches2:
            write_uInt16(wmb_file, batch)
        wmb_file.seek(mesh.batch3Pointer)
        for batch in mesh.batches3:
            write_uInt16(wmb_file, batch)
        wmb_file.seek(mesh.offsetMaterials)
        for material in mesh.materials:
            write_uInt16(wmb_file, material)                # materials
        if mesh.numBones != 0:
            for bone in mesh.bones:
                write_uInt16(wmb_file, bone)                    # bones

def create_wmb_mystery(wmb_file, data):
    def write_vector3(wmb_file, vec):
        write_float(wmb_file, vec[0])
        write_float(wmb_file, vec[1])
        write_float(wmb_file, vec[2])
    
    def write_vector4(wmb_file, vec):
        write_vector3(wmb_file, vec) # :)
        write_float(wmb_file, vec[3])
    
    # General offsets
    wmb_file.seek(data.mystery_Offset)
    for i, offset in enumerate(data.mystery.mysteryOffsets):
        write_uInt32(wmb_file, offset)
        write_uInt32(wmb_file, data.mystery.mysteryCounts[i])
    
    # Slice1Data
    subchunk = data.mystery.mystery[0]["content"]
    wmb_file.seek(data.mystery.mysteryOffsets[0])
    for mystery1 in subchunk:
        write_uInt32(wmb_file, mystery1["offsetName"])
        write_Int16(wmb_file, mystery1["parent"])
        write_Int16(wmb_file, mystery1["short_6"])
        pos = wmb_file.tell()
        wmb_file.seek(mystery1["offsetName"])
        write_string(wmb_file, mystery1["name"])
        wmb_file.seek(pos)
    
    # Slice2Data
    subchunk = data.mystery.mystery[1]["content"]
    wmb_file.seek(data.mystery.mysteryOffsets[1])
    for mystery2 in subchunk:
        mystery2["vec_0"].to_wmb(wmb_file)
        write_Int16(wmb_file, mystery2["flag_C"][0])
        write_Int16(wmb_file, mystery2["flag_C"][1])
        mystery2["vec_10"].to_wmb(wmb_file)
        write_Int16(wmb_file, mystery2["flag_1C"][0])
        write_Int16(wmb_file, mystery2["flag_1C"][1])
        mystery2["vec_20"].to_wmb(wmb_file)
        write_Int16(wmb_file, mystery2["flag_2C"][0])
        write_Int16(wmb_file, mystery2["flag_2C"][1])
        mystery2["vec_30"].to_wmb(wmb_file)
    
    # Slice3Data
    subchunk = data.mystery.mystery[2]["content"]
    wmb_file.seek(data.mystery.mysteryOffsets[2])
    for mystery3 in subchunk:
        write_uInt32(wmb_file, mystery3["offset"])
        write_uInt32(wmb_file, len(mystery3["content"])) # count
        pos = wmb_file.tell()
        wmb_file.seek(mystery3["offset"])
        for entry in mystery3["content"]:
            for vec in entry["vecs"]:
                write_vector3(wmb_file, vec)
            write_uInt32(wmb_file, entry["material"])
        wmb_file.seek(pos)
    
    # Slice4Data
    subchunk = data.mystery.mystery[3]["content"]
    wmb_file.seek(data.mystery.mysteryOffsets[3])
    for mystery4 in subchunk:
        mystery4["vec_0"].to_wmb(wmb_file)
        mystery4["vec_C"].to_wmb(wmb_file)
        write_uInt32(wmb_file, mystery4["ref5"])
        write_uInt32(wmb_file, mystery4["int_1C"])
        write_uInt16(wmb_file, mystery4["short_20"])
        write_uInt16(wmb_file, mystery4["short_22"])
        write_uInt32(wmb_file, mystery4["int_24"])
        write_uInt32(wmb_file, mystery4["offset"])
        mystery4["faces"].to_wmb(wmb_file)
        pos = wmb_file.tell()
        wmb_file.seek(mystery4["offset"])
        for val in mystery4["array"]: # 20
            write_uInt32(wmb_file, val)
        wmb_file.seek(pos)
    
    # Slice5Data
    subchunk = data.mystery.mystery[4]["content"]
    wmb_file.seek(data.mystery.mysteryOffsets[4])
    for mystery5 in subchunk:
        write_uInt32(wmb_file, mystery5["int_0"])
        write_Int16(wmb_file, mystery5["ref1"])
        write_Int16(wmb_file, mystery5["short_6"])
        write_Int16(wmb_file, mystery5["ref3"])
        write_Int16(wmb_file, mystery5["short_A"])
        write_uInt32(wmb_file, mystery5["offset"])
        write_uInt32(wmb_file, len(mystery5["array"]))
        pos1 = wmb_file.tell()
        wmb_file.seek(mystery5["offset"])
        for i, content in enumerate(mystery5["array"]):
            write_uInt32(wmb_file, mystery5["offsetTwo"][i]) # pointer 2
            write_uInt32(wmb_file, len(content))
            pos2 = wmb_file.tell()
            wmb_file.seek(mystery5["offsetTwo"][i])
            for num in content:
                write_Int16(wmb_file, num)
            wmb_file.seek(pos2)
        
        wmb_file.seek(pos1)
    
    # Slice6Data
    subchunk = data.mystery.mystery[5]["content"]
    wmb_file.seek(data.mystery.mysteryOffsets[5])
    for mystery6 in subchunk:
        write_uInt32(wmb_file, mystery6["offsetVert"])
        write_uInt32(wmb_file, mystery6["offsetFace"])
        write_uInt32(wmb_file, len(mystery6["vertexes"])) # vector4 count
        write_uInt32(wmb_file, len(mystery6["faces"]))
        pos = wmb_file.tell()
        wmb_file.seek(mystery6["offsetVert"])
        for vec in mystery6["vertexes"]:
            vec.to_wmb(wmb_file)
        wmb_file.seek(mystery6["offsetFace"])
        for num in mystery6["faces"]:
            write_Int16(wmb_file, num)
        
        wmb_file.seek(pos)
    
    # Slice7Data
    subchunk = data.mystery.mystery[6]["content"]
    wmb_file.seek(data.mystery.mysteryOffsets[6])
    for mystery7 in subchunk:
        mystery7["vec_0"].to_wmb(wmb_file)
        mystery7["vec_C"].to_wmb(wmb_file)
        write_uInt32(wmb_file, mystery7["ref6"])
        write_float(wmb_file, mystery7["float_1C"])
        mystery7["faces"].to_wmb(wmb_file)
    
    # Slice8Data
    subchunk = data.mystery.mystery[7]["content"]
    wmb_file.seek(data.mystery.mysteryOffsets[7])
    for mystery8 in subchunk:
        mystery8["vec_0"].to_wmb(wmb_file)
        mystery8["vec_10"].to_wmb(wmb_file)
        mystery8["vec_20"].to_wmb(wmb_file)
        mystery8["vec_30"].to_wmb(wmb_file)
        write_uInt32(wmb_file, mystery8["ref1"])
        write_float(wmb_file, mystery8["float_40"])
        write_float(wmb_file, mystery8["float_44"])
        write_Int16(wmb_file, mystery8["short_48"])
        write_Int16(wmb_file, mystery8["short_4A"])
        write_uInt32(wmb_file, mystery8["int_4C"])
        write_uInt32(wmb_file, mystery8["ref7"])
        write_uInt32(wmb_file, mystery8["int_54"])
    
    # Slice9Data
    subchunk = data.mystery.mystery[8]["content"]
    wmb_file.seek(data.mystery.mysteryOffsets[8])
    for mystery9 in subchunk:
        write_Int16(wmb_file, mystery9["short_0"])
        write_Int16(wmb_file, mystery9["parent"])
        write_Int16(wmb_file, mystery9["ref8"])
        write_Int16(wmb_file, mystery9["short_6"])
        write_uInt32(wmb_file, mystery9["int_8"])

def create_wmb_textures(wmb_file, data):
    wmb_file.seek(data.textures_Offset)
    for tex in data.textures.textures:
        write_uInt32(wmb_file, tex[0]) # flags
        write_uInt32(wmb_file, int(tex[1])) # wta index/hash thing

def create_wmb_vertexGroups(wmb_file, data):
    wmb_file.seek(data.vertexGroups_Offset)
    
    for vertexGroup in data.vertexGroups.vertexGroups:
        write_uInt32(wmb_file, vertexGroup.vertexOffset)            # vertexOffset
        write_uInt32(wmb_file, vertexGroup.vertexExDataOffset)      # vertexExDataOffset
        for val in vertexGroup.unknownOffset:                       # unknownOffset
            write_uInt32(wmb_file, val)
        print("NumVertexes:", hex(vertexGroup.numVertexes))
        write_Int32(wmb_file, vertexGroup.numVertexes)              # numVertexes
        write_Int32(wmb_file, vertexGroup.indexBufferOffset)        # indexBufferOffset
        write_Int32(wmb_file, vertexGroup.numIndexes)               # numIndexes
    
    fourbytes = SmartIO.makeFormat(SmartIO.uint8, SmartIO.uint8, SmartIO.uint8, SmartIO.uint8)
    writePos = SmartIO.makeFormat(SmartIO.float, SmartIO.float, SmartIO.float)
    writeTangent = fourbytes
    writeNormal = SmartIO.makeFormat(SmartIO.float16, SmartIO.float16, SmartIO.float16, SmartIO.float16)
    #if wmb4:
    #    writeNormal = SmartIO.makeFormat(SmartIO.uint32)
    writeBoneIndexes = fourbytes
    writeBoneWeights = fourbytes
    writeUV = SmartIO.makeFormat(SmartIO.float16, SmartIO.float16)
    writeColor = fourbytes
    
    for vertexGroup in data.vertexGroups.vertexGroups:
        wmb_file.seek(vertexGroup.vertexOffset)
        print("Vertices:", len(vertexGroup.vertexes))
        for vertex in vertexGroup.vertexes:                         # [position.xyz, tangents, normal, uv_maps, boneIndexes, boneWeights, color]
            writePos.write(wmb_file, vertex[0]) # Position
            writeUV.write(wmb_file, vertex[3][0]) # UVMap 1
            
            write_uInt32(wmb_file, vertex[2]) # Normal
            writeTangent.write(wmb_file, vertex[1]) # Tangent
            
            # bits that change based on flags
            #if data.vertexFormat in {0x10337, 0x10137, 0x00337, 0x00137}:
            if data.vertexFormat & 0x30 == 0x30: # hehe i'm clever
                writeBoneIndexes.write(wmb_file, vertex[4])
                writeBoneWeights.write(wmb_file, vertex[5])
            if data.vertexFormat in {0x10307, 0x10107}:
                writeColor.write(wmb_file, vertex[6])
            if data.vertexFormat == 0x10307:
                try:
                    writeUV.write(wmb_file, vertex[3][1]) # UVMap 2
                except:
                    print("ERROR: Missing UVMap2, export will likely fail")
            
            
        if vertexGroup.vertexExDataOffset > 0:
            wmb_file.seek(vertexGroup.vertexExDataOffset)
        for vertexExData in vertexGroup.vertexesExData:             # [normal, uv_maps, color]
            if vertexGroup.vertexExDataOffset <= 0:
                break
            writeColor.write(wmb_file, vertexExData[2])
            if data.vertexFormat in {0x10337, 0x00337}:
                writeUV.write(wmb_file, vertexExData[1][0])
            elif data.vertexFormat != 0x10137:
                print("How the hell is there vertexExData with a vertexFormat of %s?" % hex(data.vertexFormat))
            
        
        wmb_file.seek(vertexGroup.indexBufferOffset)
        for index in vertexGroup.indexes:                           # indexes
            write_uInt16(wmb_file, index)
        
