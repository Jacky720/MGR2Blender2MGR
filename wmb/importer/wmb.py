# load from .wmb into Python object
import os
import json
import bpy
import struct # even for only two lines
from time import time

from ...utils.util import print_class, create_dir
from ...utils.ioUtils import SmartIO, read_uint8_x4, to_string, read_float, read_float16, read_uint16, read_uint8, read_uint64, read_int16, read_int32, read_string
from ...wta_wtp.importer.wta import *

DEBUG_HEADER_PRINT = True
DEBUG_VERTEXGROUP_PRINT = False
#DEBUG_VERTEX_PRINT = # Don't even *think* about it.
DEBUG_BATCHES_PRINT = False # broken
DEBUG_BATCHSUPPLEMENT_PRINT = False
DEBUG_BONE_PRINT = False # do not recommend, there can be lots of bones
DEBUG_BITT_PRINT = False # nothing at all
DEBUG_BONESET_PRINT = False
DEBUG_MATERIAL_PRINT = True
DEBUG_TEXTURE_PRINT = True# pretty short, pretty worthwhile
DEBUG_MESH_PRINT = True
DEBUG_MYSTERY_PRINT = True

class WMB_Header(object):
    """ fucking header    """
    size = 112 + 16 # apparently padding, can't be too safe
    def __init__(self, wmb_fp):
        super(WMB_Header, self).__init__()
        if wmb_fp is None:
            return
        self.magicNumber = wmb_fp.read(4)                               # ID
        assert(self.magicNumber == b'WMB4') # Invalid file or wrong WMB version
        self.version = "%08x" % (read_uint32(wmb_fp))
        self.vertexFormat = read_uint32(wmb_fp)             # Vertex data format, ex. 0x137
        self.flags = read_uint16(wmb_fp)
        self.referenceBone = read_int16(wmb_fp)             # flags & referenceBone
        
        self.bounding_box1 = read_float(wmb_fp)             # bounding_box pos 1
        self.bounding_box2 = read_float(wmb_fp)                     
        self.bounding_box3 = read_float(wmb_fp)
        self.bounding_box4 = read_float(wmb_fp)             # bounding_box pos 2
        
        self.bounding_box5 = read_float(wmb_fp)
        self.bounding_box6 = read_float(wmb_fp)
        self.vertexGroupPointer = read_uint32(wmb_fp)
        self.vertexGroupCount = read_uint32(wmb_fp)
        
        self.batchPointer = read_uint32(wmb_fp)
        self.batchCount = read_uint32(wmb_fp)
        self.batchDescriptionPointer = read_uint32(wmb_fp)  # No count on this one
        self.bonePointer = read_uint32(wmb_fp)
        
        self.boneCount = read_uint32(wmb_fp)
        self.boneTranslateTablePointer = read_uint32(wmb_fp)
        self.boneTranslateTableSize = read_uint32(wmb_fp)   # This one isn't count, but size.
        self.boneSetPointer = read_uint32(wmb_fp)
        
        self.boneSetCount = read_uint32(wmb_fp)
        self.materialPointer = read_uint32(wmb_fp)
        self.materialCount = read_uint32(wmb_fp)
        self.texturePointer = read_uint32(wmb_fp)
        
        self.textureCount = read_uint32(wmb_fp)
        self.meshPointer = read_uint32(wmb_fp)
        self.meshCount = read_uint32(wmb_fp)
        self.unknownPointer = read_uint32(wmb_fp)
        
        if DEBUG_HEADER_PRINT:
            print("WMB4 header information")
            print(" version       %s" % self.version)
            print(" vertexFormat  %s" % hex(self.vertexFormat))
            print(" referenceBone %d" % self.referenceBone)
            print(" flags         %s" % hex(self.flags))
            print(" bounding_box1 %d" % self.bounding_box1)
            print(" bounding_box2 %d" % self.bounding_box2)
            print(" bounding_box3 %d" % self.bounding_box3)
            print(" bounding_box4 %d" % self.bounding_box4)
            print(" bounding_box5 %d" % self.bounding_box5)
            print(" bounding_box6 %d" % self.bounding_box6)
            print()
            print(" Name               Pointer Count")
            print(" vertexGroup       ", hex(self.vertexGroupPointer).rjust(7, " "), str(self.vertexGroupCount).rjust(6, " "))
            print(" batch             ", hex(self.batchPointer).rjust(7, " "), str(self.batchCount).rjust(6, " "))
            print(" batchDescription  ", hex(self.batchDescriptionPointer).rjust(7, " "))
            print(" bone              ", hex(self.bonePointer).rjust(7, " "), str(self.boneCount).rjust(6, " "))
            print(" boneTranslateTable", hex(self.boneTranslateTablePointer).rjust(7, " "), str(self.boneTranslateTableSize).rjust(6, " "))
            print(" boneSet           ", hex(self.boneSetPointer).rjust(7, " "), str(self.boneSetCount).rjust(6, " "))
            print(" material          ", hex(self.materialPointer).rjust(7, " "), str(self.materialCount).rjust(6, " "))
            print(" texture           ", hex(self.texturePointer).rjust(7, " "), str(self.textureCount).rjust(6, " "))
            print(" mesh              ", hex(self.meshPointer).rjust(7, " "), str(self.meshCount).rjust(6, " "))
            print(" slicing           ", hex(self.unknownPointer).rjust(7, " "))

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
              "%9d" % self.vertexGroupIndex,
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
        
        self.parameters = load_data_array(wmb_fp, self.parametersPointer, int(self.parametersCount/4), vector4)
        
        self.effectName = load_data(wmb_fp, self.shaderNamePointer, filestring)
        self.uniformArray = {}
        self.textureArray = {}
        self.textureFlagArray = []
        for i, texture in enumerate(texturesArray):
            if i % 2 == 0:
                self.textureFlagArray.append(texture)
            else:
                trueI = int((i - 1) / 2) # bad method, don't care tonight  
                self.textureArray[self.textureFlagArray[trueI]] = texture

        if DEBUG_MATERIAL_PRINT:
            print("Count:", self.trueTexturesCount*2, "Data:", texturesArray)
            print("Shader params:", [(a.x, a.y, a.z, a.w) for a in self.parameters])
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
        if DEBUG_MESH_PRINT:
            print("Materials:", self.materialsCount, self.materials)
        # if self.name == "lowerLeg_dam1_LBODY_DEC":
        #     self.materials = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]

class wmb4_texture(object):
    """The WMB4 texture is delightfully simple."""
    def read(self, wmb_fp):
        super(wmb4_texture, self).__init__()
        self.flags = read_uint32(wmb_fp)
        self.id = str(read_uint32(wmb_fp))

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
        SmartIO.uint32,  # normals (11+11+10 bits)
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
        SmartIO.uint32,  # normals (11+11+10 bits)
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
        SmartIO.uint32,  # normals (11+11+10 bits)
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
        SmartIO.uint32,  # normals (11+11+10 bits)
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
            normal, \
            self.tangentX, self.tangentY, self.tangentZ, self.tangentD, \
            boneIndex[0], boneIndex[1], boneIndex[2], boneIndex[3], \
            boneWeight[0], boneWeight[1], boneWeight[2], boneWeight[3] \
            = wmb4_vertex.smartRead10337.read(wmb_fp)
            self.boneIndices = boneIndex
            self.boneWeights = [weight/255 for weight in boneWeight]
            # All these values are discarded??
            # self.tangentX *= 2/255
            # self.tangentY *= 2/255
            # self.tangentZ *= 2/255
            # self.tangentD *= 2/255
            self.tangentX = (self.tangentX - 127) / 127
            self.tangentY = (self.tangentY - 127) / 127
            self.tangentZ = (self.tangentZ - 127) / 127
            self.tangentD = (self.tangentD - 127) / 127
        
        elif vertexFormat == 0x10307:
            self.positionX, self.positionY, self.positionZ, \
            self.textureU, self.textureV, \
            normal, \
            self.tangentX, self.tangentY, self.tangentZ, self.tangentD, \
            self.color, \
            self.textureU2, self.textureV2 \
            = wmb4_vertex.smartRead10307.read(wmb_fp)
            
            self.color = list(struct.unpack("<BBBB", struct.pack("<I", self.color))) # byte me
            
        elif vertexFormat == 0x10107:
            self.positionX, self.positionY, self.positionZ, \
            self.textureU, self.textureV, \
            normal, \
            self.tangentX, self.tangentY, self.tangentZ, self.tangentD, \
            self.color \
            = wmb4_vertex.smartRead10107.read(wmb_fp)
            
            self.color = list(struct.unpack("<BBBB", struct.pack("<I", self.color))) # byte me
            
        elif vertexFormat == 0x00107:
            self.positionX, self.positionY, self.positionZ, \
            self.textureU, self.textureV, \
            normal, \
            self.tangentX, self.tangentY, self.tangentZ, self.tangentD \
            = wmb4_vertex.smartRead00107.read(wmb_fp)
            
        else:
            print("God fucking DAMMIT Kris, the vertex format is %s." % hex(vertexFormat))
            return

        # split normal to self.normalX, Y, Z
        self.normalX = normal & ((1 << 11) - 1)
        self.normalY = (normal >> 11) & ((1 << 11) - 1)
        self.normalZ = (normal >> 22)
        if self.normalX & (1 << 10):
            self.normalX &= ~(1 << 10)
            self.normalX -= 1 << 10
        if self.normalY & (1 << 10):
            self.normalY &= ~(1 << 10)
            self.normalY -= 1 << 10
        if self.normalZ & (1 << 9):
            self.normalZ &= ~(1 << 9)
            self.normalZ -= 1 << 9
        # normalize
        self.normalX /= (1<<10)-1
        self.normalY /= (1<<10)-1
        self.normalZ /= (1<<9)-1

class wmb4_vertexExData(object):
    """docstring for wmb4_vertexExData"""
    def read(self, wmb_fp, vertexFormat):
        if (vertexFormat & 0x337) == 0x337: # both 10337 and 00337
            self.color = list(read_uint8_x4(wmb_fp))
            self.textureU2 = read_float16(wmb_fp)
            self.textureV2 = read_float16(wmb_fp)
            return
            
        elif vertexFormat == 0x10137:
            self.color = list(read_uint8_x4(wmb_fp))
            return
        
        else:
            print("How the FUCK did you get here, the function call is *directly* inside a check for vertexFormat matching... Somehow, it's", hex(vertexFormat))
            return


def read_vector3(wmb_fp):
    X = read_float(wmb_fp)
    Y = read_float(wmb_fp)
    Z = read_float(wmb_fp)
    return [X, Y, Z]

class wmb4_mystery(object):
    """Probably for some form of cut info. Present on Sundowner."""
    class mystery1Template(object):
        def read(self, wmb_fp):
            self.namePointer = read_uint32(wmb_fp)
            self.parent = read_int16(wmb_fp)
            self.mysteryB = read_int16(wmb_fp)
            self.name = load_data(wmb_fp, self.namePointer, filestring)
    
    class mystery2Template(object):
        def read(self, wmb_fp):
            self.posA = read_vector3(wmb_fp)
            flagA1 = read_int16(wmb_fp)
            flagA2 = read_int16(wmb_fp)
            self.flagA = [flagA1, flagA2]
            
            self.posB = read_vector3(wmb_fp)
            flagB1 = read_int16(wmb_fp)
            flagB2 = read_int16(wmb_fp)
            self.flagB = [flagB1, flagB2]
            
            self.posC = read_vector3(wmb_fp)
            flagC1 = read_int16(wmb_fp)
            flagC2 = read_int16(wmb_fp)
            self.flagC = [flagC1, flagC2]
            
            self.posD = read_vector3(wmb_fp)
    
    class mystery3Template(object):
        class vectorsTemplate(object):
            def read(self, wmb_fp):
                # vectors, but lists are easier to use
                self.mysteryA = read_vector3(wmb_fp)
                self.mysteryB = read_vector3(wmb_fp)
                self.mysteryC = read_vector3(wmb_fp)
                self.mysteryD = read_vector3(wmb_fp)
                self.mysteryE = read_vector3(wmb_fp)
                
                self.mysteryF = read_uint32(wmb_fp)
                
        
        def read(self, wmb_fp):
            self.vectorsPointer = read_uint32(wmb_fp)
            self.vectorsCount = read_uint32(wmb_fp)
            self.vectors = load_data_array(wmb_fp, self.vectorsPointer, self.vectorsCount, self.vectorsTemplate)
    
    class mystery4Template(object):
        
        def read(self, wmb_fp):
            self.posA = read_vector3(wmb_fp)
            self.posB = read_vector3(wmb_fp)
            self.mysteryC = read_uint32(wmb_fp)
            self.mysteryD = read_uint32(wmb_fp)
            self.mysteryE = read_uint16(wmb_fp)
            self.mysteryE2 = read_uint16(wmb_fp)
            self.mysteryF = read_uint32(wmb_fp) # always 0 or 1?
            
            self.twentyElementsPointer = read_uint32(wmb_fp)
            self.startVertex = read_uint32(wmb_fp)
            self.vertexCount = read_uint32(wmb_fp)
            self.startIndex = read_uint32(wmb_fp)
            self.indexCount = read_uint32(wmb_fp)
            
            self.twentyElements = load_data_array(wmb_fp, self.twentyElementsPointer, 20, uint32)
    
    class mystery5Template(object):
        class mysteryDTemplate(object):
            def read(self, wmb_fp):
                self.contentPointer = read_uint32(wmb_fp)
                self.contentCount = read_uint32(wmb_fp)
                self.content = load_data_array(wmb_fp, self.contentPointer, self.contentCount, int16)
    
        def read(self, wmb_fp):
            self.mysteryA = read_uint32(wmb_fp)
            self.mysteryB = read_int16(wmb_fp)
            self.mysteryB2 = read_int16(wmb_fp)
            self.mysteryC = read_int16(wmb_fp)
            self.mysteryC2 = read_int16(wmb_fp)
            self.mysteryDPointer = read_uint32(wmb_fp)
            self.mysteryDCount = read_uint32(wmb_fp)
            
            self.mysteryD = load_data_array(wmb_fp, self.mysteryDPointer, self.mysteryDCount, self.mysteryDTemplate)
    
    class mystery6Template(object):
        def read(self, wmb_fp):
            self.mysteryAPointer = read_uint32(wmb_fp)
            self.mysteryBPointer = read_uint32(wmb_fp)
            self.mysteryACount = read_uint32(wmb_fp)
            self.mysteryBCount = read_uint32(wmb_fp)
            
            # immediately after those headers everything gets out of order.
            # next subchunk is 9, then 8, then 7, before getting back to this content.
            # not gonna bother to reproduce that unless i have to
            
            self.mysteryA = load_data_array(wmb_fp, self.mysteryAPointer, self.mysteryACount, vector4)
            self.mysteryB = load_data_array(wmb_fp, self.mysteryBPointer, self.mysteryBCount, int16)
    
    class mystery7Template(object):
        def read(self, wmb_fp):
            self.unknownA = read_vector3(wmb_fp)
            self.unknownB = read_vector3(wmb_fp)
            self.unknownC = read_uint32(wmb_fp)
            self.unknownD = read_float(wmb_fp)
            
            self.startVertex = read_uint32(wmb_fp)
            self.vertexCount = read_uint32(wmb_fp)
            self.startIndex = read_uint32(wmb_fp)
            self.indexCount = read_uint32(wmb_fp)
    
    class mystery8Template(object):
        def read(self, wmb_fp):
            self.vectors = []
            for i in range(5):
                self.vectors.append(read_vector3(wmb_fp))
            self.mysteryA = read_uint32(wmb_fp) # so close to being more vector
            mysteryBX = read_float(wmb_fp)
            mysteryBY = read_float(wmb_fp)
            self.mysteryB = [mysteryBX, mysteryBY]
            self.mysteryC = read_int16(wmb_fp)
            self.mysteryD = read_int16(wmb_fp)
            self.mysteryE = read_uint32(wmb_fp)
            self.mysteryF = read_uint32(wmb_fp)
            self.mysteryG = read_uint32(wmb_fp)
    
    class mystery9Template(object):
        def read(self, wmb_fp):
            self.mysteryA = read_int16(wmb_fp)
            self.mysteryParent = read_int16(wmb_fp)
            self.mysteryC = read_int16(wmb_fp)
            self.mysteryD = read_int16(wmb_fp)
            self.mysteryE = read_uint32(wmb_fp)
    
    def read(self, wmb_fp):
        self.mystery1Pointer = read_uint32(wmb_fp)
        self.mystery1Count = read_uint32(wmb_fp)
        self.mystery2Pointer = read_uint32(wmb_fp)
        self.mystery2Count = read_uint32(wmb_fp)
        self.mystery3Pointer = read_uint32(wmb_fp)
        self.mystery3Count = read_uint32(wmb_fp)
        self.mystery4Pointer = read_uint32(wmb_fp)
        self.mystery4Count = read_uint32(wmb_fp)
        self.mystery5Pointer = read_uint32(wmb_fp)
        self.mystery5Count = read_uint32(wmb_fp)
        self.mystery6Pointer = read_uint32(wmb_fp)
        self.mystery6Count = read_uint32(wmb_fp)
        self.mystery7Pointer = read_uint32(wmb_fp)
        self.mystery7Count = read_uint32(wmb_fp)
        self.mystery8Pointer = read_uint32(wmb_fp)
        self.mystery8Count = read_uint32(wmb_fp)
        self.mystery9Pointer = read_uint32(wmb_fp)
        self.mystery9Count = read_uint32(wmb_fp)
        
        self.mystery1 = load_data_array(wmb_fp, self.mystery1Pointer, self.mystery1Count, self.mystery1Template)
        self.mystery2 = load_data_array(wmb_fp, self.mystery2Pointer, self.mystery2Count, self.mystery2Template)
        self.mystery3 = load_data_array(wmb_fp, self.mystery3Pointer, self.mystery3Count, self.mystery3Template)
        self.mystery4 = load_data_array(wmb_fp, self.mystery4Pointer, self.mystery4Count, self.mystery4Template)
        self.mystery5 = load_data_array(wmb_fp, self.mystery5Pointer, self.mystery5Count, self.mystery5Template)
        self.mystery6 = load_data_array(wmb_fp, self.mystery6Pointer, self.mystery6Count, self.mystery6Template)
        self.mystery7 = load_data_array(wmb_fp, self.mystery7Pointer, self.mystery7Count, self.mystery7Template)
        self.mystery8 = load_data_array(wmb_fp, self.mystery8Pointer, self.mystery8Count, self.mystery8Template)
        self.mystery9 = load_data_array(wmb_fp, self.mystery9Pointer, self.mystery9Count, self.mystery9Template)

class vector4(object):
    """originally used only for paramFunc, moved for mystery chunk"""
    def read(self, wmb_fp):
        self.x = read_float(wmb_fp)
        self.y = read_float(wmb_fp)
        self.z = read_float(wmb_fp)
        self.w = read_float(wmb_fp)

class int16(object):
    """
    int16 class for reading data and
    returning to original location via load_data
    """
    type = "int"
    def __init__(self):
        self.val = 0
    def read(self, wmb_fp):
        self.val = read_int16(wmb_fp)

class uint16(object):
    """
    uint16 class for reading data and
    returning to original location via load_data
    """
    type = "int"
    def __init__(self):
        self.val = 0
    def read(self, wmb_fp):
        self.val = read_uint16(wmb_fp)

class uint8(object):
    """
    uint8 class for reading data and
    returning to original location via load_data
    """
    type = "int"
    def __init__(self):
        self.val = 0
    def read(self, wmb_fp):
        self.val = read_uint8(wmb_fp)

class uint32(object):
    """
    uint32 class for reading data and
    returning to original location via load_data
    """
    type = "int"
    def __init__(self):
        self.val = 0
    def read(self, wmb_fp):
        self.val = read_uint32(wmb_fp)

class filestring(object):
    """
    filestring class for reading data and
    returning to original location via load_data
    """
    type = "string"
    def __init__(self):
        self.val = ""
    def read(self, wmb_fp):
        self.val = read_string(wmb_fp)

class WMB(object):
    """docstring for WMB"""
    def __init__(self, wmb_file, only_extract):
        super(WMB, self).__init__()
        wmb_fp = 0
        wta_fp = 0
        wtp_fp = 0
        self.wta = 0

        wmb_path = wmb_file
        if not os.path.exists(wmb_path):
            wmb_path = wmb_file.replace('.dat','.dtt')
        wtp_path = wmb_file.replace('.dat','.dtt').replace('.wmb','.wtp')
        wta_path = wmb_file.replace('.dtt','.dat').replace('.wmb','.wta')
        scr_mode = False
        wmbinscr_name = ""
        if "extracted_scr" in wmb_path:
            scr_mode = True
            split_path = os.path.split(wmb_file)
            wmbinscr_name = split_path[1][:-4] # wmb name
            split_path = os.path.split(split_path[0]) # discard "extracted_scr"
            split_path = os.path.split(split_path[0]) # separate dat name
            datdttname = split_path[1][:-4] # e.g. "ra01"
            # wtb is both wtp and wta
            wtp_path = os.path.join(split_path[0], "%s.dtt" % datdttname, "%sscr.wtb" % datdttname)
            wta_path = wtp_path
            if os.path.exists(wtp_path.replace('scr.wtb', 'cmn.wtb')):
                print("Loading %s..." % wtp_path.replace('scr.wtb', 'cmn.wtb'))
                wtb_fp = open(wtp_path.replace('scr.wtb', 'cmn.wtb'), 'rb')
                wtb = WTA(wtb_fp)

                wmbname = os.path.split(wmb_file)[-1]
                texture_dir = wmb_file.replace(wmbname, 'textures/common')

                for textureIndex in range(wtb.textureCount):
                    identifier = wtb.wtaTextureIdentifier[textureIndex]
                    texture_file_name = identifier + '.dds'
                    texture_filepath = os.path.join(texture_dir, texture_file_name)
                    try:
                        texture_stream = wtb.getTextureByIdentifier(identifier, wtb_fp)
                        if not texture_stream:
                            print("Texture identifier %s does not exist in WTB, despite being fetched from that WTB's identifier list." % identifier)
                            continue
                        if not os.path.exists(texture_filepath):
                            create_dir(texture_dir)
                            texture_fp = open(texture_filepath, "wb")
                            print('[+] could not find DDS texture, trying to find it in WTB;', texture_file_name)
                            texture_fp.write(texture_stream)
                            texture_fp.close()
                    except:
                        continue

                    if bpy.data.images.get(texture_file_name) is None:
                        bpy.data.images.load(texture_filepath)


        if os.path.exists(wtp_path):
            print('open wtp file')
            self.wtp_fp = open(wtp_path,'rb')
        if os.path.exists(wta_path):
            print('open wta file')
            wta_fp = open(wta_path,'rb')
        
        self.wta = None
        if wta_fp:
            self.wta = WTA(wta_fp)
            wta_fp.close()
        
        if os.path.exists(wmb_path):
            print('open wmb file:', wmb_path)
            wmb_fp = open(wmb_path, "rb")
        else:
            print("DTT/DAT does not contain WMB file.")
            print("Last attempted path:", wmb_path)
            return
        
        
        
        self.wmb_header = WMB_Header(wmb_fp)

        if self.wmb_header.magicNumber == b'WMB4':
            self.vertexGroupArray = load_data_array(wmb_fp, self.wmb_header.vertexGroupPointer, self.wmb_header.vertexGroupCount, wmb4_vertexGroup, self.wmb_header.vertexFormat)
            
            if DEBUG_BATCHES_PRINT:
                print()
                print("Batches:")
                print("vertexGroup vertexRange indexRange")
            self.batchArray = load_data_array(wmb_fp, self.wmb_header.batchPointer, self.wmb_header.batchCount, wmb4_batch)
            
            if DEBUG_BATCHSUPPLEMENT_PRINT:
                print()
                print("Batch supplement data:")
            self.batchDescription = load_data(wmb_fp, self.wmb_header.batchDescriptionPointer, wmb4_batchDescription)
            self.batchDataArray = []
            for batchDataSubgroup in self.batchDescription.batchData:
                self.batchDataArray.extend(batchDataSubgroup)
            
            # hack
            for dataNum, batchDataSubgroup in enumerate(self.batchDescription.batchData):
                for batchData in batchDataSubgroup:
                    self.batchArray[batchData.batchIndex].batchGroup = dataNum
            
            self.hasBone = self.wmb_header.boneCount > 0
            if DEBUG_BONE_PRINT:
                print()
                print("Bones?", self.hasBone)
                if self.hasBone:
                    print("Enjoy the debug bone data:")
            self.boneArray = load_data_array(wmb_fp, self.wmb_header.bonePointer, self.wmb_header.boneCount, wmb4_bone, None, True)
            
            if DEBUG_BITT_PRINT:
                print()
                print("The boneIndexTranslateTable? I got no debug info besides what's in the header.")
            boneTranslateTable = load_data(wmb_fp, self.wmb_header.boneTranslateTablePointer, wmb4_boneTranslateTable)
            if boneTranslateTable is not None:
                self.firstLevel = boneTranslateTable.firstLevel
                self.secondLevel = boneTranslateTable.secondLevel
                self.thirdLevel = boneTranslateTable.thirdLevel
            
            if DEBUG_BONESET_PRINT:
                print()
                print("Bonesets:")
            boneSetArrayTrue = load_data_array(wmb_fp, self.wmb_header.boneSetPointer, self.wmb_header.boneSetCount, wmb4_boneSet)
            # is this cheating
            self.boneSetArray = [item.boneSet for item in boneSetArrayTrue]
            #print(self.boneSetArray)
            
            if DEBUG_MATERIAL_PRINT:
                print()
                print("Material info:")
            self.materialArray = load_data_array(wmb_fp, self.wmb_header.materialPointer, self.wmb_header.materialCount, wmb4_material)
            
            if DEBUG_TEXTURE_PRINT:
                print()
                print("Just have the textures array if you care so bad")
            self.textureArray = load_data_array(wmb_fp, self.wmb_header.texturePointer, self.wmb_header.textureCount, wmb4_texture)
            if DEBUG_TEXTURE_PRINT:
                print("\n".join([str([item.id, hex(item.flags)]) for item in self.textureArray]))
            
            if DEBUG_MESH_PRINT:
                print()
                print("Meshes (batches separated by batchGroup, naturally):")
            self.meshArray = load_data_array(wmb_fp, self.wmb_header.meshPointer, self.wmb_header.meshCount, wmb4_mesh, [scr_mode, wmbinscr_name])
            
            for mesh in self.meshArray:
                for materialIndex, material in enumerate(mesh.materials):
                    self.materialArray[material].materialName = mesh.name + "-%d" % materialIndex
            
            # Hack (index and material used differently than the loop immediately above)
            for materialIndex, material in enumerate(self.materialArray):
                if material.materialName == "UnusedMaterial":
                    self.meshArray[0].materials.append(materialIndex)
                    self.materialArray[materialIndex].materialName = self.meshArray[0].name + "-x-%d" % materialIndex
            
            self.mystery = load_data(wmb_fp, self.wmb_header.unknownPointer, wmb4_mystery)
            
            self.boneMap = None # <trollface>
            self.hasColTreeNodes = False # maybe this could be before the version check
            self.hasUnknownWorldData = False
            
            print("\n\n")
            print("Continuing to wmb_importer.py...\n")
        
        else:
            print("You madman! This isn't WMB4, but %s!" % self.wmb_header.magicNumber.decode("ascii"))

    def clear_unused_vertex(self, meshArrayIndex,vertexGroupIndex, wmb4=False):
        mesh = self.meshArray[meshArrayIndex]
        vertexGroup = self.vertexGroupArray[vertexGroupIndex]
        
        faceRawStart = mesh.faceStart
        faceRawCount = mesh.faceCount
        vertexStart = mesh.vertexStart
        vertexCount = mesh.vertexCount

        vertexesExData = vertexGroup.vertexesExDataArray[vertexStart : vertexStart + vertexCount]

        vertex_colors = []
        
        facesRaw = vertexGroup.faceRawArray[faceRawStart : faceRawStart + faceRawCount ]
        if len(facesRaw) < faceRawCount:
            faceRawCount = len(facesRaw)
            print("\n\n===== ERROR: Insufficient faces found in faceRawArray, reducing faceCount to match =====\n\n")
        if not wmb4:
            facesRaw = [index - 1 for index in facesRaw]
        usedVertexIndexArray = sorted(list(set(facesRaw))) # oneliner to remove duplicates
        
        """
        print("Vertex group index:", vertexGroupIndex, "Face first index:", faceRawStart, "Face last index:", faceRawStart+faceRawCount)
        print("Faces range from %d to %d" % (min(facesRaw), max(facesRaw)))
        print([("[" if i%3==0 else "") + str(face).rjust(3, " ") + ("]" if i%3==2 else "") for i, face in enumerate(facesRaw)])
        """
        # mappingDict is the reverse lookup for usedVertexIndexArray
        mappingDict = {}
        for newIndex, vertid in enumerate(usedVertexIndexArray):
            mappingDict[vertid] = newIndex
        #print(mappingDict)
        # After this loop, facesRaw now points to indexes in usedVertices (below)
        for i, vertex in enumerate(facesRaw):
            facesRaw[i] = mappingDict[vertex]
        faces = [0] * (faceRawCount // 3)
        usedVertices = [None] * len(usedVertexIndexArray)
        usedNormals = [None] * len(usedVertexIndexArray)
        boneWeightInfos = [[],[]]
        #print("Iterating over 0, faceRawCount, 3, length %d" % 0, faceRawCount, 3)
        for i in range(0, faceRawCount, 3):
            faces[i // 3] = ( facesRaw[i + 2], facesRaw[i + 1], facesRaw[i] )
        meshVertices = vertexGroup.vertexArray[vertexStart : vertexStart + vertexCount]

        if self.hasBone:
            boneWeightInfos = [0] * len(usedVertexIndexArray)
        for newIndex, i in enumerate(usedVertexIndexArray):
            usedVertices[newIndex] = (meshVertices[i].positionX, meshVertices[i].positionY, meshVertices[i].positionZ)
            usedNormals[newIndex] = (meshVertices[i].normalX, meshVertices[i].normalY, meshVertices[i].normalZ)

            # Vertex_Colors are stored in VertexData
            if vertexGroup.vertexFlags in {4, 5, 12, 14} or (wmb4 and self.wmb_header.vertexFormat in {0x10307, 0x10107}):
                vertex_colors.append(meshVertices[i].color)
            # Vertex_Colors are stored in VertexExData
            if vertexGroup.vertexFlags in {10, 11} or (wmb4 and self.wmb_header.vertexFormat in {0x10337, 0x10137, 0x00337}):
                vertex_colors.append(vertexesExData[i].color)

            if self.hasBone:
                bonesetIndex = mesh.bonesetIndex
                if bonesetIndex != -1:
                    boneSet = self.boneSetArray[bonesetIndex]
                    if not wmb4:
                        boneIndices = [self.boneMap[boneSet[index]] for index in meshVertices[i].boneIndices]
                    else:
                        #boneIndices = meshVertices[i].boneIndices
                        # this is really rather obvious
                        try:
                            boneIndices = [boneSet[index] for index in meshVertices[i].boneIndices]
                        except:
                            print()
                            print("Hey! Something's wrong with the bone set. The mesh %s has these bone indices:" % mesh.name)
                            #print([vertexes.boneIndices for vertexes in meshVertices])
                            print("...nevermind that's way too much to print")
                            print("(They go up to %d)" % max([max(vertexes.boneIndices) for vertexes in meshVertices]))
                            print("But the bone set (#%d) only has %d bones." % (bonesetIndex, len(boneSet)))
                            print("How terrible! Time to crash.\n")
                            assert False # See console above about missing boneset elements
                    boneWeightInfos[newIndex] = [boneIndices, meshVertices[i].boneWeights]
                    s = sum(meshVertices[i].boneWeights)
                    if s > 1.000000001 or s < 0.999999:
                        print('[-] error weight detect %f' % s)
                        print(meshVertices[i].boneWeights) 
                else:
                    self.hasBone = False
        if wmb4:
            return usedVertices, faces, usedVertexIndexArray, boneWeightInfos, vertex_colors, vertexStart, vertexCount, usedNormals
        return usedVertices, faces, usedVertexIndexArray, boneWeightInfos, vertex_colors, vertexStart

def load_data(wmb_fp, pointer, chunkClass, other=None):
    pos = wmb_fp.tell()
    final = None
    if pointer > 0:
        wmb_fp.seek(pointer)
        #print("Seeking to %sPointer: %s" % (chunkClass.__name__, hex(pointer)))
        final = chunkClass()
        if other is not None:
            final.read(wmb_fp, other)
        else:
            final.read(wmb_fp)
        wmb_fp.seek(pos)
        if "type" in chunkClass.__dict__ and chunkClass.type in {"int", "string"}:
            return final.val
    return final

def load_data_array(wmb_fp, pointer, count, chunkClass, other=None, useIndex=False):
    array = []
    pos = wmb_fp.tell()
    if pointer > 0:
        wmb_fp.seek(pointer)
        #print("Seeking to %sPointer: %s" % (chunkClass.__name__, hex(pointer)))
        
        # putting the for in the if is, uh, maybe optimized idk
        if other is not None:
            #print("Iterating over %sCount, length %d" % (chunkClass.__name__, count))
            for itemIndex in range(count):
                #print("This could be a print. %d" % itemIndex)
                item = chunkClass()
                item.read(wmb_fp, other)
                if "type" in chunkClass.__dict__ and chunkClass.type in {"int", "string"}:
                    item = item.val
                array.append(item)
        elif useIndex:
            #print("Iterating over %sCount, length %d" % (chunkClass.__name__, count))
            for itemIndex in range(count):
                #print("This could be a print. %d" % itemIndex)
                item = chunkClass()
                item.read(wmb_fp, itemIndex)
                if "type" in chunkClass.__dict__ and chunkClass.type in {"int", "string"}:
                    item = item.val
                array.append(item)
        else:
            #print("Iterating over %sCount, length %d" % (chunkClass.__name__, count))
            for itemIndex in range(count):
                #print("This could be a print. %d" % itemIndex)
                item = chunkClass()
                item.read(wmb_fp)
                if "type" in chunkClass.__dict__ and chunkClass.type in {"int", "string"}:
                    item = item.val
                array.append(item)
        wmb_fp.seek(pos)
        #print("Seeking to return position: %s" % hex(pos))
    return array


def export_obj(wmb, wta, wtp_fp, obj_file):
    if not obj_file:
        obj_file = 'test'
    create_dir('out/%s'%obj_file)
    obj_file = 'out/%s/%s'%(obj_file, obj_file)
    textureArray = []
    
    if (wta and wtp_fp):
        #print("Iterating over wmb.wmb_header.materialCount, length %d" % wmb.wmb_header.materialCount)
        for materialIndex in range(wmb.wmb_header.materialCount):
            material = wmb.materialArray[materialIndex]
            materialName = material.materialName
            if 'g_AlbedoMap' in material.textureArray.keys():
                identifier = material.textureArray['g_AlbedoMap']
                textureFile = "%s%s"%('out/texture/',identifier)
                textureArray.append(textureFile)
            if 'g_NormalMap' in material.textureArray.keys():
                identifier = material.textureArray['g_NormalMap']
                textureFile = "%s%s"%('out/texture/',identifier)
                textureArray.append(textureFile)
        """
        for textureFile in textureArray:
            texture = wta.getTextureByIdentifier(textureFile.replace('out/texture/',''), wtp_fp)
            if texture:
                texture_fp = open("%s.dds"%textureFile, "wb")
                #print('dumping %s.dds'%textureFile)
                texture_fp.write(texture)
                texture_fp.close()
        """

    mtl = open("%s.mtl"%obj_file, 'w')
    #print("Iterating over wmb.wmb_header.materialCount, length %d" % wmb.wmb_header.materialCount)
    for materialIndex in range(wmb.wmb_header.materialCount):
        material = wmb.materialArray[materialIndex]
        materialName = material.materialName
        if 'g_AlbedoMap' in material.textureArray.keys():
            identifier = material.textureArray['g_AlbedoMap']
            textureFile = "%s%s"%('out/texture/',identifier)
            mtl.write('newmtl %s\n'%(identifier))
            mtl.write('Ns 96.0784\nNi 1.5000\nd 1.0000\nTr 0.0000\nTf 1.0000 1.0000 1.0000 \nillum 2\nKa 0.0000 0.0000 0.0000\nKd 0.6400 0.6400 0.6400\nKs 0.0873 0.0873 0.0873\nKe 0.0000 0.0000 0.0000\n')
            mtl.write('map_Ka %s.dds\nmap_Kd %s.dds\n'%(textureFile.replace('out','..'),textureFile.replace('out','..')))
        if 'g_NormalMap' in material.textureArray.keys():
            identifier = material.textureArray['g_NormalMap']
            textureFile2 = "%s%s"%('out/texture/',identifier)    
            mtl.write("bump %s.dds\n"%textureFile2.replace('out','..'))
        mtl.write('\n')
    mtl.close()

    
    #print("Iterating over wmb.wmb_header.vertexGroupCount, length %d" % wmb.wmb_header.vertexGroupCount)
    for vertexGroupIndex in range(wmb.wmb_header.vertexGroupCount):
        
        #print("Iterating over wmb.wmb_header.meshGroupCount, length %d" % wmb.wmb_header.meshGroupCount)
        for meshGroupIndex in range(wmb.wmb_header.meshGroupCount):
            meshIndexArray = []
            
            groupedMeshArray = wmb.meshGroupInfoArray[0].groupedMeshArray
            for groupedMeshIndex in range(len(groupedMeshArray)):
                if groupedMeshArray[groupedMeshIndex].meshGroupIndex == meshGroupIndex:
                    meshIndexArray.append(groupedMeshIndex)
            meshGroup = wmb.meshGroupArray[meshGroupIndex]
            for meshArrayIndex in (meshIndexArray):
                meshVertexGroupIndex = wmb.meshArray[meshArrayIndex].vertexGroupIndex
                if meshVertexGroupIndex == vertexGroupIndex:
                    if  not os.path.exists('%s_%s_%d.obj'%(obj_file,meshGroup.meshGroupname,vertexGroupIndex)):
                        obj = open('%s_%s_%d.obj'%(obj_file,meshGroup.meshGroupname,vertexGroupIndex),"w")
                        obj.write('mtllib ./%s.mtl\n'%obj_file.split('/')[-1])
                        #print("Iterating over wmb.vertexGroupArray[vertexGroupIndex].vertexGroupHeader.vertexCount, length %d" % wmb.vertexGroupArray[vertexGroupIndex].vertexGroupHeader.vertexCount)
                        for vertexIndex in range(wmb.vertexGroupArray[vertexGroupIndex].vertexGroupHeader.vertexCount):
                            vertex = wmb.vertexGroupArray[vertexGroupIndex].vertexArray[vertexIndex]
                            obj.write('v %f %f %f\n'%(vertex.positionX,vertex.positionY,vertex.positionZ))
                            obj.write('vt %f %f\n'%(vertex.textureU,1 - vertex.textureV))
                            obj.write('vn %f %f %f\n'%(vertex.normalX, vertex.normalY, vertex.normalZ))
                    else:
                        obj = open('%s_%s_%d.obj'%(obj_file,meshGroup.meshGroupname,vertexGroupIndex),"a+")
                    if 'g_AlbedoMap' in wmb.materialArray[groupedMeshArray[meshArrayIndex].materialIndex].textureArray.keys():
                        textureFile = wmb.materialArray[groupedMeshArray[meshArrayIndex].materialIndex].textureArray["g_AlbedoMap"]
                        obj.write('usemtl %s\n'%textureFile.split('/')[-1])
                    #print('dumping %s_%s_%d.obj'%(obj_file,meshGroup.meshGroupname,vertexGroupIndex))
                    obj.write('g %s%d\n'% (meshGroup.meshGroupname,vertexGroupIndex))
                    faceRawStart = wmb.meshArray[meshArrayIndex].faceStart
                    faceRawNum = wmb.meshArray[meshArrayIndex].faceCount
                    vertexStart = wmb.meshArray[meshArrayIndex].vertexStart
                    vertexNum = wmb.meshArray[meshArrayIndex].vertexCount
                    faceRawArray = wmb.vertexGroupArray[meshVertexGroupIndex].faceRawArray
                    
                    for i in range(int(faceRawNum/3)):
                        obj.write('f %d/%d/%d %d/%d/%d %d/%d/%d\n'%(
                                faceRawArray[faceRawStart + i * 3],faceRawArray[faceRawStart + i * 3],faceRawArray[faceRawStart + i * 3],
                                faceRawArray[faceRawStart + i * 3 + 1],faceRawArray[faceRawStart + i * 3 + 1],faceRawArray[faceRawStart + i * 3 + 1],
                                faceRawArray[faceRawStart + i * 3 + 2],faceRawArray[faceRawStart + i * 3 + 2],faceRawArray[faceRawStart + i * 3 + 2],
                            )
                        )
                    obj.close()

def main(arg, wmb_fp, wta_fp, wtp_fp, dump):
    wmb = WMB(wmb_fp)
    wmb_fp.close()
    wta = 0
    if wta_fp:
        wta = WTA(wta_fp)
        wta_fp.close()
    if dump:
        obj_file = os.path.split(arg)[-1].replace('.wmb','')
        export_obj(wmb, wta, wtp_fp, obj_file)
        if wtp_fp:
            wtp_fp.close()

if __name__ == '__main__':
    pass
