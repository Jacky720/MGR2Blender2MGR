import os
import json
import bpy
import struct # even for only two lines
from time import time

from ...utils.util import print_class, create_dir
from ...utils.ioUtils import SmartIO, read_uint8_x4, to_string, read_float, read_float16, read_uint16, read_uint8, read_uint64, read_int16, read_int32, read_string
from ...wta_wtp.importer.wta import *


class wmb4_batch(object):
    """docstring for wmb4_batch"""
    def read(self, wmb_fp):
        self.batchGroup = -1 # overwritten later
        self.vertexGroupIndex = read_uint32(wmb_fp)
        self.vertexStart = read_int32(wmb_fp)
        self.indexStart = read_int32(wmb_fp)
        self.numVertexes = read_uint32(wmb_fp)
        self.numIndexes = read_uint32(wmb_fp)
        if DEBUG_BATCHES_PRINT:
            print(" ",
              self.vertexGroupIndex.ljust(10, " "),
              ("%d-%d" % (self.vertexStart, self.vertexStart + self.numVertexes)).ljust(11, " "),
              ("%d-%d" % (self.indexStart, self.indexStart + self.numIndexes))
            )

class wmb4_batchDescription(object):
    """docstring for wmb4_batchDescription"""
    def read(self, wmb_fp):
        self.batchDataPointers = []
        self.batchDataCounts = []
        self.batchData = []
        #print("Iterating over 4, length %d" % 4)
        for dataNum in range(4):
            if DEBUG_BATCHSUPPLEMENT_PRINT:
                print("Batch supplement for group", dataNum)
            self.batchDataPointers.append(read_uint32(wmb_fp))
            self.batchDataCounts.append(read_uint32(wmb_fp))
            self.batchData.append(load_data_array(wmb_fp, self.batchDataPointers[-1], self.batchDataCounts[-1], wmb4_batchData))
        #print("Batch data pointers:", [hex(f) for f in self.batchDataPointers])

class wmb4_batchData(object):
    """docstring for wmb4_batchData"""
    def read(self, wmb_fp):
        self.batchIndex = read_uint32(wmb_fp)
        self.meshIndex = read_uint32(wmb_fp)
        self.materialIndex = read_uint16(wmb_fp)
        self.boneSetsIndex = read_int16(wmb_fp)
        self.unknown10 = read_uint32(wmb_fp) # again, maybe just padding
        
        if DEBUG_BATCHSUPPLEMENT_PRINT:
            print(" Batch: %s;   Mesh: %s;   Material: %s;   Bone set: %s" % (str(self.batchIndex).rjust(3, " "), str(self.meshIndex).rjust(3, " "), str(self.materialIndex).rjust(3, " "), str(self.boneSetsIndex).rjust(3, " ")))

class wmb4_bone(object):
    """docstring for wmb4_bone"""
    def read(self, wmb_fp, index):
        super(wmb4_bone, self).__init__()
        self.boneIndex = index
        self.boneNumber = read_int16(wmb_fp)
        self.unknown02 = read_int16(wmb_fp) # one is global index
        self.parentIndex = read_int16(wmb_fp)
        self.unknownRotation = read_int16(wmb_fp) # rotation order or smth

        relativePositionX = read_float(wmb_fp)
        relativePositionY = read_float(wmb_fp)
        relativePositionZ = read_float(wmb_fp)
        
        positionX = read_float(wmb_fp)
        positionY = read_float(wmb_fp)
        positionZ = read_float(wmb_fp)

        self.local_position = (relativePositionX, relativePositionY, relativePositionZ)
        self.local_rotation = (0, 0, 0)
        
        self.world_position = (positionX, positionY, positionZ)
        self.world_rotation = (relativePositionX, relativePositionY, relativePositionZ)
        #self.boneNumber = self.boneIndex
        # self... wait, why is world_rotation used twice?
        self.world_position_tpose = (0, 0, 0)
        
        if DEBUG_BONE_PRINT:
            # there are lots of bones, so this should be compressed better
            print()
            print("index:      ", index)
            print("ID:         ", self.boneNumber)
            print("Unknown:    ", self.unknown02)
            print("Parent:     ", self.parentIndex)
            print("Rotation(?):", self.unknownRotation)
            print("Position A: ", "(%s, %s, %s)" % self.local_position)
            print("Position B: ", "(%s, %s, %s)" % self.world_position)

class wmb4_boneSet(object):
    """docstring for wmb4_boneSet"""
    def read(self, wmb_fp):
        super(wmb4_boneSet, self).__init__()
        self.pointer = read_uint32(wmb_fp)
        self.count = read_uint32(wmb_fp)
        self.boneSet = load_data_array(wmb_fp, self.pointer, self.count, uint8)
        if DEBUG_BONESET_PRINT:
            print("Count:", self.count, "Data:", self.boneSet)

class wmb4_boneTranslateTable(object):
    """docstring for wmb4_boneTranslateTable"""
    def read(self, wmb_fp):
        self.firstLevel = []
        self.secondLevel = []
        self.thirdLevel = []
        for entry in range(16):
            self.firstLevel.append(read_int16(wmb_fp))

        firstLevel_Entry_Count = 0
        for entry in self.firstLevel:
            if entry != -1:
                firstLevel_Entry_Count += 1

        #print("Iterating over firstLevel_Entry_Count * 16, length %d" % firstLevel_Entry_Count * 16)
        for entry in range(firstLevel_Entry_Count * 16):
            self.secondLevel.append(read_int16(wmb_fp))

        secondLevel_Entry_Count = 0
        for entry in self.secondLevel:
            if entry != -1:
                secondLevel_Entry_Count += 1

        #print("Iterating over secondLevel_Entry_Count * 16, length %d" % secondLevel_Entry_Count * 16)
        for entry in range(secondLevel_Entry_Count * 16):
            self.thirdLevel.append(read_int16(wmb_fp))

class wmb4_material(object):
    """docstring for wmb4_material"""
    class paramFunc(object):
        def read(self, wmb_fp):
            self.x = read_float(wmb_fp)
            self.y = read_float(wmb_fp)
            self.z = read_float(wmb_fp)
            self.w = read_float(wmb_fp)
    
    def read(self, wmb_fp):
        super(wmb4_material, self).__init__()
        self.shaderNamePointer = read_uint32(wmb_fp)
        self.texturesPointer = read_uint32(wmb_fp)
        # by context, probably another offset.
        # check for unread data in the file.
        self.unknown08 = read_uint32(wmb_fp)
        self.parametersPointer = read_uint32(wmb_fp)
        
        self.texturesCount = read_uint16(wmb_fp) # wait so what's this
        self.trueTexturesCount = read_uint16(wmb_fp) # texture count, 4 or 5
        self.unknown14 = read_uint16(wmb_fp) # and the mystery count.
        self.parametersCount = read_uint16(wmb_fp)
        
        texturesArray = load_data_array(wmb_fp, self.texturesPointer, self.trueTexturesCount*2, uint32)
        
        if self.parametersCount/4 % 1 != 0:
            print("Hey, idiot, you have incomplete parameters in your materials. It's gonna read some garbage data, since each one should have exactly four attributes: xyzw. Actually, I'm not sure if it'll read garbage or stop early. Idiot.")
        
        self.parameters = load_data_array(wmb_fp, self.parametersPointer, int(self.parametersCount/4), self.paramFunc)
        
        self.effectName = load_data(wmb_fp, self.shaderNamePointer, filestring)
        self.techniqueName = "NoTechnique"
        self.uniformArray = {}
        self.textureArray = {}
        for i, texture in enumerate(texturesArray):
            if i in {1, 3}:
                self.textureArray["albedoMap" + str(i)] = texture
            elif i == 7:
                self.textureArray["normalMap" + str(i)] = texture
            else:
                self.textureArray["tex" + str(i)] = texture
        
        if DEBUG_MATERIAL_PRINT:
            print("Count:", self.trueTexturesCount*2, "Data:", texturesArray)
        self.parameterGroups = self.parameters
        self.materialName = "UnusedMaterial" # mesh name overrides
        self.wmb4 = True

class wmb4_mesh(object):
    """docstring for wmb4_mesh"""
    def read(self, wmb_fp, scr_mode=None):
        super(wmb4_mesh, self).__init__()
        self.namePointer = read_uint32(wmb_fp)
        self.boundingBox = []
        #print("Iterating over 6, length %d" % 6)
        for i in range(6):
            self.boundingBox.append(read_float(wmb_fp))
        
        self.batch0Pointer = read_uint32(wmb_fp)
        self.batch0Count = read_uint32(wmb_fp)
        self.batch1Pointer = read_uint32(wmb_fp)
        self.batch1Count = read_uint32(wmb_fp)
        self.batch2Pointer = read_uint32(wmb_fp)
        self.batch2Count = read_uint32(wmb_fp)
        self.batch3Pointer = read_uint32(wmb_fp)
        self.batch3Count = read_uint32(wmb_fp)
        
        self.materialsPointer = read_uint32(wmb_fp)
        self.materialsCount = read_uint32(wmb_fp)
        
        self.name = load_data(wmb_fp, self.namePointer, filestring)
        if scr_mode is not None and scr_mode[0]:
            if self.name != "SCR_MESH":
                print()
                print("Hey, very interesting. A map file with custom mesh names.")
            else:
                self.name = scr_mode[1]
        if DEBUG_MESH_PRINT:
            print("\nMesh name: %s" % self.name)
        
        self.batches0 = load_data_array(wmb_fp, self.batch0Pointer, self.batch0Count, uint16)
        self.batches1 = load_data_array(wmb_fp, self.batch1Pointer, self.batch1Count, uint16)
        self.batches2 = load_data_array(wmb_fp, self.batch2Pointer, self.batch2Count, uint16)
        self.batches3 = load_data_array(wmb_fp, self.batch3Pointer, self.batch3Count, uint16)
        if DEBUG_MESH_PRINT:
            print("Batches:", self.batches0, self.batches1, self.batches2, self.batches3)
        
        self.materials = load_data_array(wmb_fp, self.materialsPointer, self.materialsCount, uint16)

class wmb4_texture(object):
    """The WMB4 texture is delightfully simple."""
    def read(self, wmb_fp):
        super(wmb4_texture, self).__init__()
        self.flags = read_uint32(wmb_fp)
        self.id = "%08x" % read_uint32(wmb_fp)

class wmb4_vertexGroup(object):
    """docstring for wmb4_vertexGroup"""
    def size(a):
        return 28 + 0
    def read(self, wmb_fp, vertexFormat):
        self.vertexesDataPointer = read_uint32(wmb_fp)
        self.extraVertexesDataPointer = read_uint32(wmb_fp)
        self.unknownPointer = read_uint32(wmb_fp)
        self.unknownCount = read_uint32(wmb_fp) # might actually be another pointer lol idk
        # or what if it's just padding?
        self.vertexesCount = read_uint32(wmb_fp)
        self.faceIndexesPointer = read_uint32(wmb_fp)
        self.faceIndexesCount = read_uint32(wmb_fp)
        
        
        if DEBUG_VERTEXGROUP_PRINT:
            print()
            print("Vertex group information    Pointer Count")
            print(" vertexesData            " + hex(self.vertexesDataPointer).rjust(10, " ") + str(self.vertexesCount).rjust(6, " "))
            print(" extraVertexesData       " + hex(self.extraVertexesDataPointer).rjust(10, " "))
            print(" unknown                 " + hex(self.unknownPointer).rjust(10, " ") + str(self.unknownCount).rjust(6, " "))
            print(" faceIndexes             " + hex(self.faceIndexesPointer).rjust(10, " ") + str(self.faceIndexesCount).rjust(6, " "))
        
        
        self.vertexArray = load_data_array(wmb_fp, self.vertexesDataPointer, self.vertexesCount, wmb4_vertex, vertexFormat)
        
        if vertexFormat in {0x10337, 0x10137, 0x00337}:
            self.vertexesExDataArray = load_data_array(wmb_fp, self.extraVertexesDataPointer, self.vertexesCount, wmb4_vertexExData, vertexFormat)
        else:
            self.vertexesExDataArray = [None] * self.vertexesCount
        
        self.unknownArray = load_data_array(wmb_fp, self.unknownPointer, self.unknownCount, uint32)
        # mercifully empty
        
        self.faceRawArray = load_data_array(wmb_fp, self.faceIndexesPointer, self.faceIndexesCount, uint16)
        
        self.vertexFlags = None # <trollface>

class wmb4_vertex(object):
    smartRead10337 = SmartIO.makeFormat( # 10137, 00337, 00137 same
        SmartIO.float,   # x
        SmartIO.float,   # y
        SmartIO.float,   # z
        SmartIO.float16, # texture u
        SmartIO.float16, # texture v
        SmartIO.uint8,   # normal x
        SmartIO.uint8,   # normal y
        SmartIO.uint8,   # normal z
        SmartIO.uint8,   # normal padding
        SmartIO.uint8,   # tangent x
        SmartIO.uint8,   # tangent y
        SmartIO.uint8,   # tangent z
        SmartIO.uint8,   # tangent d
        SmartIO.uint8, SmartIO.uint8, SmartIO.uint8, SmartIO.uint8, # boneIndexes
        SmartIO.uint8, SmartIO.uint8, SmartIO.uint8, SmartIO.uint8  # boneWeights
    )
    smartRead10307 = SmartIO.makeFormat(
        SmartIO.float,   # x
        SmartIO.float,   # y
        SmartIO.float,   # z
        SmartIO.float16, # texture u
        SmartIO.float16, # texture v
        SmartIO.uint8,   # normal x
        SmartIO.uint8,   # normal y
        SmartIO.uint8,   # normal z
        SmartIO.uint8,   # normal padding
        SmartIO.uint8,   # tangent x
        SmartIO.uint8,   # tangent y
        SmartIO.uint8,   # tangent z
        SmartIO.uint8,   # tangent d
        SmartIO.uint32,  # color
        SmartIO.float16, # texture2 u
        SmartIO.float16  # texture2 v
    )
    smartRead10107 = SmartIO.makeFormat(
        SmartIO.float,   # x
        SmartIO.float,   # y
        SmartIO.float,   # z
        SmartIO.float16, # texture u
        SmartIO.float16, # texture v
        SmartIO.uint8,   # normal x
        SmartIO.uint8,   # normal y
        SmartIO.uint8,   # normal z
        SmartIO.uint8,   # normal padding
        SmartIO.uint8,   # tangent x
        SmartIO.uint8,   # tangent y
        SmartIO.uint8,   # tangent z
        SmartIO.uint8,   # tangent d
        SmartIO.uint32   # color
    )
    smartRead00107 = SmartIO.makeFormat(
        SmartIO.float,   # x
        SmartIO.float,   # y
        SmartIO.float,   # z
        SmartIO.float16, # texture u
        SmartIO.float16, # texture v
        SmartIO.uint8,   # normal x
        SmartIO.uint8,   # normal y
        SmartIO.uint8,   # normal z
        SmartIO.uint8,   # normal padding
        SmartIO.uint8,   # tangent x
        SmartIO.uint8,   # tangent y
        SmartIO.uint8,   # tangent z
        SmartIO.uint8,   # tangent d
    )
    
    """docstring for wmb4_vertex"""
    def read(self, wmb_fp, vertexFormat):
        if (vertexFormat & 0x137) == 0x137: # 10337, 10137, 00337, 00137, all match this
            # everything I did with the indexes is horrible here todo fix
            boneIndex = [0] * 4
            boneWeight = [0] * 4
            self.positionX, self.positionY, self.positionZ, \
            self.textureU, self.textureV, \
            self.normalX, self.normalY, self.normalZ, _, \
            self.tangentX, self.tangentY, self.tangentZ, self.tangentD, \
            boneIndex[0], boneIndex[1], boneIndex[2], boneIndex[3], \
            boneWeight[0], boneWeight[1], boneWeight[2], boneWeight[3] \
            = wmb4_vertex.smartRead10337.read(wmb_fp)
            self.boneIndices = boneIndex
            self.boneWeights = [weight/255 for weight in boneWeight]
            # All these values are discarded??
            self.normalX *= 2/255
            self.normalY *= 2/255
            self.normalZ *= 2/255
            self.tangentX *= 2/255
            self.tangentY *= 2/255
            self.tangentZ *= 2/255
            self.tangentD *= 2/255
            return
        
        elif vertexFormat == 0x10307:
            self.positionX, self.positionY, self.positionZ, \
            self.textureU, self.textureV, \
            self.normalX, self.normalY, self.normalZ, _, \
            self.tangentX, self.tangentY, self.tangentZ, self.tangentD, \
            self.color, \
            self.textureU2, self.textureV2 \
            = wmb4_vertex.smartRead10307.read(wmb_fp)
            
            self.color = list(struct.unpack("<BBBB", struct.pack("<I", self.color))) # byte me
            return
            
        elif vertexFormat == 0x10107:
            self.positionX, self.positionY, self.positionZ, \
            self.textureU, self.textureV, \
            self.normalX, self.normalY, self.normalZ, _, \
            self.tangentX, self.tangentY, self.tangentZ, self.tangentD, \
            self.color \
            = wmb4_vertex.smartRead10107.read(wmb_fp)
            
            self.color = list(struct.unpack("<BBBB", struct.pack("<I", self.color))) # byte me
            return
            
        elif vertexFormat == 0x00107:
            self.positionX, self.positionY, self.positionZ, \
            self.textureU, self.textureV, \
            self.normalX, self.normalY, self.normalZ, _, \
            self.tangentX, self.tangentY, self.tangentZ, self.tangentD \
            = wmb4_vertex.smartRead00107.read(wmb_fp)
            return
            
        else:
            print("God fucking DAMMIT Kris, the vertex format is %s." % hex(vertexFormat))
            return

class wmb4_vertexExData(object):
    """docstring for wmb4_vertexExData"""
    def read(self, wmb_fp, vertexFormat):
        if (vertexFormat & 0x337) == 0x337: # both 10337 and 00337
            self.color = list(read_uint8_x4(wmb_fp))
            self.textureU2 = read_float16(wmb_fp)
            self.textureV2 = read_float16(wmb_fp)
            return
            
        elif vertexFormat == 0x10137:
            self.color = read_uint32(wmb_fp)
            return
        
        else:
            print("How the FUCK did you get here, the function call is *directly* inside a check for vertexFormat matching... Somehow, it's", hex(vertexFormat))
            return
