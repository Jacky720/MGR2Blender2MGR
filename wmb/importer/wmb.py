# load from .wmb into Python object
import os
import json
import bpy
import struct # even for only two lines
from time import time

from ...utils.util import print_class, create_dir
from ...utils.ioUtils import SmartIO, read_uint8_x4, to_string, read_float, read_float16, read_uint16, read_uint8, read_uint64, read_int16, read_int32, read_string
from ...wta_wtp.importer.wta import *
from .load_data_funcs import *

from .wmb3classes import *
from .wmb4classes import *
from .wmb2classes import *

DEBUG_HEADER_PRINT = True
DEBUG_VERTEXGROUP_PRINT = False
#DEBUG_VERTEX_PRINT = # Don't even *think* about it.
DEBUG_BATCHES_PRINT = False
DEBUG_BATCHSUPPLEMENT_PRINT = False
DEBUG_BONE_PRINT = False # do not recommend, there can be lots of bones
DEBUG_BITT_PRINT = False # nothing at all
DEBUG_BONESET_PRINT = False
DEBUG_MATERIAL_PRINT = False
DEBUG_TEXTURE_PRINT = False # basically nothing at the moment
DEBUG_MESH_PRINT = False

class WMB_Header(object):
    """ fucking header    """
    size = 112 + 16 # apparently padding, can't be too safe
    def __init__(self, wmb_fp):
        super(WMB_Header, self).__init__()
        if wmb_fp is None:
            return
        self.magicNumber = wmb_fp.read(4)                               # ID
        if self.magicNumber == b'WMB3':
            self.version = "%08x" % (read_uint32(wmb_fp))               # Version
            self.unknown08 = read_uint32(wmb_fp)                        # UnknownA
            self.flags = read_uint32(wmb_fp)                            # flags & referenceBone
            
            self.bounding_box1 = read_float(wmb_fp)                     # bounding_box
            self.bounding_box2 = read_float(wmb_fp)                     
            self.bounding_box3 = read_float(wmb_fp)
            self.bounding_box4 = read_float(wmb_fp)
            
            self.bounding_box5 = read_float(wmb_fp)
            self.bounding_box6 = read_float(wmb_fp)
            self.bonePointer = read_uint32(wmb_fp)
            self.boneCount = read_uint32(wmb_fp)
            
            self.boneTranslateTablePointer = read_uint32(wmb_fp)
            self.boneTranslateTableSize = read_uint32(wmb_fp) # Wait, size? Not count? Check this.
            self.vertexGroupPointer = read_uint32(wmb_fp)
            self.vertexGroupCount = read_uint32(wmb_fp)
            
            self.meshPointer = read_uint32(wmb_fp)
            self.meshCount = read_uint32(wmb_fp)
            self.meshGroupInfoPointer = read_uint32(wmb_fp)
            self.meshGroupInfoCount = read_uint32(wmb_fp)
            
            self.colTreeNodesPointer = read_uint32(wmb_fp)
            self.colTreeNodesCount = read_uint32(wmb_fp)
            self.boneMapPointer = read_uint32(wmb_fp)
            self.boneMapCount = read_uint32(wmb_fp)
            
            self.boneSetPointer = read_uint32(wmb_fp)
            self.boneSetCount = read_uint32(wmb_fp)
            self.materialPointer = read_uint32(wmb_fp)
            self.materialCount = read_uint32(wmb_fp)
            
            self.meshGroupPointer = read_uint32(wmb_fp)
            self.meshGroupCount = read_uint32(wmb_fp)
            self.meshMaterialsPointer = read_uint32(wmb_fp) # Unaccessed??
            self.meshMaterialsCount = read_uint32(wmb_fp)
            
            self.unknownWorldDataPointer = read_uint32(wmb_fp)      # World Model Stuff
            self.unknownWorldDataCount = read_uint32(wmb_fp)        # World Model Stuff
            self.unknown8C = read_uint32(wmb_fp)                    # Maybe just padding lol
        
        elif self.magicNumber == b'WMB4':
            self.version = "%08x" % (read_uint32(wmb_fp))
            self.vertexFormat = read_uint32(wmb_fp)             # Vertex data format, ex. 0x137
            self.referenceBone = read_uint16(wmb_fp)
            self.flags = read_int16(wmb_fp)                     # flags & referenceBone
            
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
                print(" ??????            ", hex(self.unknownPointer).rjust(7, " "))
        
        elif self.magicNumber == b'WMB2':
            print('oh god')
            self.minusone = read_int32(wmb_fp)
            self.version = "%08x" % (read_uint32(wmb_fp)) # 0
            #self.vertexFormat = 0x137#read_uint32(wmb_fp)             # Vertex data format, ex. 0x137
            #self.referenceBone = 0#read_uint16(wmb_fp)
            #self.flags = 0#read_int16(wmb_fp)                     # flags & referenceBone
            self.bounding_box1 = read_float(wmb_fp)             # bounding_box pos 1
            
            self.bounding_box2 = read_float(wmb_fp)                     
            self.bounding_box3 = read_float(wmb_fp)
            self.bounding_box4 = read_float(wmb_fp)             # bounding_box pos 2
            self.bounding_box5 = read_float(wmb_fp)
            
            self.bounding_box6 = read_float(wmb_fp)
            self.vertexGroupPointer = read_uint32(wmb_fp)
            self.vertexGroupCount = 1#read_uint32(wmb_fp)
            self.batchPointer = read_uint32(wmb_fp)
            self.batchCount = read_uint32(wmb_fp)
            
            #self.batchDescriptionPointer = read_uint32(wmb_fp)  # No count on this one
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
            
            self.unknownPointer = read_uint32(wmb_fp) # going back in time didn't get rid of it
            
            if DEBUG_HEADER_PRINT:
                print("WMB2 header information")
                print(" Should be -1: %d" % self.minusone)
                print(" version       %s" % self.version)
                print(" bounding_box1 %f" % self.bounding_box1)
                print(" bounding_box2 %f" % self.bounding_box2)
                print(" bounding_box3 %f" % self.bounding_box3)
                print(" bounding_box4 %f" % self.bounding_box4)
                print(" bounding_box5 %f" % self.bounding_box5)
                print(" bounding_box6 %f" % self.bounding_box6)
                print()
                print(" Name               Pointer Count")
                print(" vertexGroup       ", hex(self.vertexGroupPointer).rjust(7, " "), str(self.vertexGroupCount).rjust(6, " "))
                print(" batch             ", hex(self.batchPointer).rjust(7, " "), str(self.batchCount).rjust(6, " "))
                print(" bone              ", hex(self.bonePointer).rjust(7, " "), str(self.boneCount).rjust(6, " "))
                print(" boneTranslateTable", hex(self.boneTranslateTablePointer).rjust(7, " "), str(self.boneTranslateTableSize).rjust(6, " "))
                print(" boneSet           ", hex(self.boneSetPointer).rjust(7, " "), str(self.boneSetCount).rjust(6, " "))
                print(" material          ", hex(self.materialPointer).rjust(7, " "), str(self.materialCount).rjust(6, " "))
                print(" texture           ", hex(self.texturePointer).rjust(7, " "), str(self.textureCount).rjust(6, " "))
                print(" mesh              ", hex(self.meshPointer).rjust(7, " "), str(self.meshCount).rjust(6, " "))
                print(" ??????            ", hex(self.unknownPointer).rjust(7, " "))


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
            split_path = wmb_file.replace("/", "\\").split("\\")
            wmbinscr_name = split_path.pop()[:-4] # wmb name
            split_path.pop() # "extracted_scr"
            datdttname = split_path.pop()[:-4] # e.g. "ra01"
            # wtb is both wtp and wta
            wtp_path = "\\".join(split_path) + "\\%s.dtt\\%sscr.wtb" % (datdttname, datdttname)
            wta_path = "\\".join(split_path) + "\\%s.dtt\\%sscr.wtb" % (datdttname, datdttname)
            if os.path.exists(wtp_path.replace('scr.wtb', 'cmn.wtb')):
                # common files, jackpot!
                pass # todo: load this somewhere other files can get it
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
            wmb_fp = open(wmb_path, "rb")
        else:
            print("DTT/DAT does not contain WMB file.")
            print("Last attempted path:", wmb_path)
            return
        
        
        
        self.wmb_header = WMB_Header(wmb_fp)
        if self.wmb_header.magicNumber == b'WMB3':
            self.hasBone = False
            if self.wmb_header.boneCount > 0:
                self.hasBone = True

            wmb_fp.seek(self.wmb_header.bonePointer)
            #print("Seeking to self.wmb_header.bonePointer: %s" % hex(self.wmb_header.bonePointer))
            self.boneArray = []
            #print("Iterating over self.wmb_header.boneCount, length %d" % self.wmb_header.boneCount)
            for boneIndex in range(self.wmb_header.boneCount):
                self.boneArray.append(wmb3_bone(wmb_fp,boneIndex))
            
            # indexBoneTranslateTable
            self.firstLevel = []
            self.secondLevel = []
            self.thirdLevel = []
            if self.wmb_header.boneTranslateTablePointer > 0:
                wmb_fp.seek(self.wmb_header.boneTranslateTablePointer)
                #print("Seeking to self.wmb_header.boneTranslateTablePointer: %s" % hex(self.wmb_header.boneTranslateTablePointer))
                #print("Iterating over 16, length %d" % 16)
                for entry in range(16):
                    self.firstLevel.append(read_uint16(wmb_fp))
                    if self.firstLevel[-1] == 65535:
                        self.firstLevel[-1] = -1

                firstLevel_Entry_Count = 0
                for entry in self.firstLevel:
                    if entry != -1:
                        firstLevel_Entry_Count += 1

                #print("Iterating over firstLevel_Entry_Count * 16, length %d" % firstLevel_Entry_Count * 16)
                for entry in range(firstLevel_Entry_Count * 16):
                    self.secondLevel.append(read_uint16(wmb_fp))
                    if self.secondLevel[-1] == 65535:
                        self.secondLevel[-1] = -1

                secondLevel_Entry_Count = 0
                for entry in self.secondLevel:
                    if entry != -1:
                        secondLevel_Entry_Count += 1

                #print("Iterating over secondLevel_Entry_Count * 16, length %d" % secondLevel_Entry_Count * 16)
                for entry in range(secondLevel_Entry_Count * 16):
                    self.thirdLevel.append(read_uint16(wmb_fp))
                    if self.thirdLevel[-1] == 65535:
                        self.thirdLevel[-1] = -1


                wmb_fp.seek(self.wmb_header.boneTranslateTablePointer)
                #print("Seeking to self.wmb_header.boneTranslateTablePointer: %s" % hex(self.wmb_header.boneTranslateTablePointer))
                unknownData1Array = []
                #print("Iterating over self.wmb_header.boneTranslateTableSize, length %d" % self.wmb_header.boneTranslateTableSize)
                for i in range(self.wmb_header.boneTranslateTableSize):
                    unknownData1Array.append(read_uint8(wmb_fp))

            self.materialArray = []
            #print("Iterating over self.wmb_header.materialCount, length %d" % self.wmb_header.materialCount)
            for materialIndex in range(self.wmb_header.materialCount):
                wmb_fp.seek(self.wmb_header.materialPointer + materialIndex * 0x30)
                #print("Seeking to self.wmb_header.materialPointer + materialIndex * 0x30: %s" % hex(self.wmb_header.materialPointer + materialIndex * 0x30))
                material = wmb3_material(wmb_fp)
                self.materialArray.append(material)

            if only_extract:
                return

            self.vertexGroupArray = []
            #print("Iterating over self.wmb_header.vertexGroupCount, length %d" % self.wmb_header.vertexGroupCount)
            for vertexGroupIndex in range(self.wmb_header.vertexGroupCount):
                wmb_fp.seek(self.wmb_header.vertexGroupPointer + 0x30 * vertexGroupIndex)
                #print("Seeking to self.wmb_header.vertexGroupPointer + 0x30 * vertexGroupIndex: %s" % hex(self.wmb_header.vertexGroupPointer + 0x30 * vertexGroupIndex))

                vertexGroup = wmb3_vertexGroup(wmb_fp,((self.wmb_header.flags & 0x8) and 4 or 2))
                self.vertexGroupArray.append(vertexGroup)

            self.meshArray = []
            wmb_fp.seek(self.wmb_header.meshPointer)
            #print("Seeking to self.wmb_header.meshPointer: %s" % hex(self.wmb_header.meshPointer))
            #print("Iterating over self.wmb_header.meshCount, length %d" % self.wmb_header.meshCount)
            for meshIndex in range(self.wmb_header.meshCount):
                mesh = wmb3_mesh(wmb_fp)
                self.meshArray.append(mesh)

            self.meshGroupInfoArray = []
            #print("Iterating over self.wmb_header.meshGroupInfoCount, length %d" % self.wmb_header.meshGroupInfoCount)
            for meshGroupInfoArrayIndex in range(self.wmb_header.meshGroupInfoCount):
                wmb_fp.seek(self.wmb_header.meshGroupInfoPointer + meshGroupInfoArrayIndex * 0x14)
                #print("Seeking to self.wmb_header.meshGroupInfoPointer + meshGroupInfoArrayIndex * 0x14: %s" % hex(self.wmb_header.meshGroupInfoPointer + meshGroupInfoArrayIndex * 0x14))
                meshGroupInfo= wmb3_meshGroupInfo(wmb_fp)
                self.meshGroupInfoArray.append(meshGroupInfo)

            self.meshGroupArray = []
            #print("Iterating over self.wmb_header.meshGroupCount, length %d" % self.wmb_header.meshGroupCount)
            for meshGroupIndex in range(self.wmb_header.meshGroupCount):
                wmb_fp.seek(self.wmb_header.meshGroupPointer + meshGroupIndex * 0x2c)
                #print("Seeking to self.wmb_header.meshGroupPointer + meshGroupIndex * 0x2c: %s" % hex(self.wmb_header.meshGroupPointer + meshGroupIndex * 0x2c))
                meshGroup = wmb3_meshGroup(wmb_fp)
                
                self.meshGroupArray.append(meshGroup)

            wmb_fp.seek(self.wmb_header.boneMapPointer)
            #print("Seeking to self.wmb_header.boneMapPointer: %s" % hex(self.wmb_header.boneMapPointer))
            self.boneMap = []
            #print("Iterating over self.wmb_header.boneMapCount, length %d" % self.wmb_header.boneMapCount)
            for index in range(self.wmb_header.boneMapCount):
                self.boneMap.append(read_uint32(wmb_fp))
            wmb_fp.seek(self.wmb_header.boneSetPointer)
            #print("Seeking to self.wmb_header.boneSetPointer: %s" % hex(self.wmb_header.boneSetPointer))
            self.boneSetArray = wmb3_boneSet(wmb_fp, self.wmb_header.boneSetCount).boneSetArray

            # colTreeNode
            self.hasColTreeNodes = False
            if self.wmb_header.colTreeNodesPointer > 0:
                self.hasColTreeNodes = True
                self.colTreeNodes = []
                wmb_fp.seek(self.wmb_header.colTreeNodesPointer)
                #print("Seeking to self.wmb_header.colTreeNodesPointer: %s" % hex(self.wmb_header.colTreeNodesPointer))
                #print("Iterating over self.wmb_header.colTreeNodesCount, length %d" % self.wmb_header.colTreeNodesCount)
                for index in range(self.wmb_header.colTreeNodesCount):
                    self.colTreeNodes.append(wmb3_colTreeNode(wmb_fp))
            
            # World Model Data
            self.hasUnknownWorldData = False
            if self.wmb_header.unknownWorldDataPointer > 0:
                self.hasUnknownWorldData = True
                self.unknownWorldDataArray = []
                wmb_fp.seek(self.wmb_header.unknownWorldDataPointer)
                #print("Seeking to self.wmb_header.unknownWorldDataPointer: %s" % hex(self.wmb_header.unknownWorldDataPointer))
                #print("Iterating over self.wmb_header.unknownWorldDataCount, length %d" % self.wmb_header.unknownWorldDataCount)
                for index in range(self.wmb_header.unknownWorldDataCount):
                    self.unknownWorldDataArray.append(wmb3_worldData(wmb_fp))
        
        elif self.wmb_header.magicNumber == b'WMB4':
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
                print("Material info (specifically textures, not shaders; not yet):")
            self.materialArray = load_data_array(wmb_fp, self.wmb_header.materialPointer, self.wmb_header.materialCount, wmb4_material)
            
            if DEBUG_TEXTURE_PRINT:
                print()
                print("Just have the textures array if you care so bad")
            self.textureArray = load_data_array(wmb_fp, self.wmb_header.texturePointer, self.wmb_header.textureCount, wmb4_texture)
            if DEBUG_TEXTURE_PRINT:
                print([item.id for item in self.textureArray])
            
            if DEBUG_MESH_PRINT:
                print()
                print("Meshes (batches separated by batchGroup, naturally):")
            self.meshArray = load_data_array(wmb_fp, self.wmb_header.meshPointer, self.wmb_header.meshCount, wmb4_mesh, [scr_mode, wmbinscr_name])
            
            for mesh in self.meshArray:
                for materialIndex, material in enumerate(mesh.materials):
                    self.materialArray[material].materialName = mesh.name + "-%d" % materialIndex
            
            self.boneMap = None # <trollface>
            self.hasColTreeNodes = False # maybe this could be before the version check
            self.hasUnknownWorldData = False
        
        elif self.wmb_header.magicNumber == b'WMB2':
            self.vertexGroupArray = [load_data(wmb_fp, self.wmb_header.vertexGroupPointer, wmb2_vertexGroup)]
            self.wmb_header.vertexFormat = self.vertexGroupArray[0].vertexFormat
            
            if DEBUG_BATCHES_PRINT:
                print()
                print("Batches:")
                print("vertexGroup vertexRange indexRange")
            self.batchArray = load_data_array(wmb_fp, self.wmb_header.batchPointer, self.wmb_header.batchCount, wmb2_batch)
            curFaceIndex = 0
            for batch in self.batchArray:
                self.vertexGroupArray[0].faceRawArray.extend(batch.faces)
                batch.indexStart = curFaceIndex
                curFaceIndex += batch.numIndexes
            
            self.hasBone = self.wmb_header.boneCount > 0
            if DEBUG_BONE_PRINT:
                print()
                print("Bones?", self.hasBone)
                if self.hasBone:
                    print("Enjoy the debug bone data:")
            self.boneArray = load_data_array(wmb_fp, self.wmb_header.bonePointer, self.wmb_header.boneCount, wmb2_bone, None, True)
            
            if DEBUG_BITT_PRINT:
                print()
                print("The boneIndexTranslateTable? I got no debug info besides what's in the header.")
            boneTranslateTable = load_data(wmb_fp, self.wmb_header.boneTranslateTablePointer, wmb2_boneTranslateTable)
            if boneTranslateTable is not None:
                self.firstLevel = boneTranslateTable.firstLevel
                self.secondLevel = boneTranslateTable.secondLevel
                self.thirdLevel = boneTranslateTable.thirdLevel
            
            if DEBUG_BONESET_PRINT:
                print()
                print("Bonesets:")
            boneSetArrayTrue = load_data_array(wmb_fp, self.wmb_header.boneSetPointer, self.wmb_header.boneSetCount, wmb2_boneSet)
            # is this cheating
            self.boneSetArray = [item.boneSet for item in boneSetArrayTrue]
            #print(self.boneSetArray)
            
            if DEBUG_MATERIAL_PRINT:
                print()
                print("Material info (specifically textures, not shaders; not yet):")
            self.materialArray = load_data_array(wmb_fp, self.wmb_header.materialPointer, self.wmb_header.materialCount, wmb2_material)
            
            if DEBUG_TEXTURE_PRINT:
                print()
                print("Just have the textures array if you care so bad")
            self.textureArray = load_data_array(wmb_fp, self.wmb_header.texturePointer, self.wmb_header.textureCount, wmb2_texture)
            if DEBUG_TEXTURE_PRINT:
                print([item.id for item in self.textureArray])
            
            if DEBUG_MESH_PRINT:
                print()
                print("Meshes (batches separated by batchGroup, naturally):")
            self.meshArray = load_data_array(wmb_fp, self.wmb_header.meshPointer, self.wmb_header.meshCount, wmb2_mesh, [scr_mode, wmbinscr_name])
            
            for mesh in self.meshArray:
                for materialIndex, material in enumerate(mesh.materials):
                    self.materialArray[material].materialName = mesh.name + "-%d" % materialIndex
            
            self.boneMap = None # <trollface>
            self.hasColTreeNodes = False # maybe this could be before the version check
            self.hasUnknownWorldData = False
            
            self.wmb_header.magicNumber = b'WMB4' # I'm lying to every part of the program and myself
        else:
            print("You madman! This isn't WMB2, 3 or 4, but %s!" % self.wmb_header.magicNumber.decode("ascii"))
    
        print("\n\n")
        print("Continuing to wmb_importer.py...\n")
        
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
        
        if wmb4 and (-1 in facesRaw): # actually wmb2 but worry about that later
            # they compressed the faces... somehow. Something about edges.
            # I guess the -1's are split points, and otherwise it continues using the last edge.
            chain = []
            newFaceList = []
            reverse = True
            for vert in facesRaw:
                if vert == -1:
                    chain = []
                    reverse = True
                    continue
                chain.append(vert)
                if len(chain) > 3:
                    chain.pop(0)
                if len(chain) == 3:
                    reverse = not reverse
                    if reverse:
                        chain.reverse()
                    newFaceList.extend(chain)
                    if reverse:
                        chain.reverse()
            
            """
            # okay, that didn't work
            # only got like half the faces
            # maybe I can detect all triangles and generate faces from those...
            # fuck performance, btw. this only has to run once. ever.
            """
            # so that's also false, turns out these sickos put backfaces in in the first place.
            # gotta read the normals...
            """
            edges = []
            faceEdgePairs = []
            for i in range(0, len(newFaceList), 3):
                face = [newFaceList[i], newFaceList[i+1], newFaceList[i+2]]
                edges.append([face[0], face[1]])
                edges.append([face[1], face[2]])
                edges.append([face[2], face[0]])
                faceEdgePairs.append(sorted([edges[-3], edges[-2]]))
                faceEdgePairs.append(sorted([edges[-2], edges[-1]]))
                faceEdgePairs.append(sorted([edges[-1], edges[-3]]))
            edgeFirstVerts = [edge[0] for edge in edges]
            edgeSecondVerts = [edge[1] for edge in edges]
            #edgePairs = []
            for i, firstVert in enumerate(edgeFirstVerts):
                for j, matchVert in enumerate([x for x in edgeSecondVerts if x == firstVert]):
                    # lol don't even need matchVert
                    edgePair = sorted([edges[i], edges[j]])
                    thirdEdge = [edges[j][0], edges[i][1]]
                    if thirdEdge not in edges:
                        thirdEdge.reverse()
                    if edgePair not in faceEdgePairs and thirdEdge in edges:
                        newFace = []
                        newFace.append(edges[i][0]) # firstVert == matchVert
                        newFace.append(edges[j][0])
                        newFace.append(edges[i][1])
                        newFaceList.extend(newFace)
            """
            facesRaw = newFaceList
            faceRawCount = len(facesRaw)
            print(len(facesRaw), max(facesRaw))
        
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
        faces = [0] * int(faceRawCount / 3)
        usedVertices = [0] * len(usedVertexIndexArray)
        boneWeightInfos = [[],[]]
        #print("Iterating over 0, faceRawCount, 3, length %d" % 0, faceRawCount, 3)
        for i in range(0, faceRawCount, 3):
            faces[int(i/3)] = ( facesRaw[i], facesRaw[i + 1], facesRaw[i + 2] )
        meshVertices = vertexGroup.vertexArray[vertexStart : vertexStart + vertexCount]

        if self.hasBone:
            boneWeightInfos = [0] * len(usedVertexIndexArray)
        for newIndex, i in enumerate(usedVertexIndexArray):
            usedVertices[newIndex] = (meshVertices[i].positionX, meshVertices[i].positionY, meshVertices[i].positionZ)

            # Vertex_Colors are stored in VertexData
            if vertexGroup.vertexFlags in {4, 5, 12, 14} or (wmb4 and self.wmb_header.vertexFormat in {0x10307, 0x10107}):
                vertex_colors.append(meshVertices[i].color)
            # Vertex_Colors are stored in VertexExData
            if vertexGroup.vertexFlags in {10, 11} or (wmb4 and self.wmb_header.vertexFormat in {0x10337, 0x10137, 0x00337}):
                vertex_colors.append(vertexesExData[i].color)

            if self.hasBone:
                bonesetIndex = mesh.bonesetIndex
                if bonesetIndex in range(len(self.boneSetArray)):
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
                            print("How terrible! Time to crash.")
                            assert False
                    boneWeightInfos[newIndex] = [boneIndices, meshVertices[i].boneWeights]
                    s = sum(meshVertices[i].boneWeights)
                    if s > 1.000000001 or s < 0.999999:
                        print('[-] error weight detect %f' % s)
                        print(meshVertices[i].boneWeights) 
                else:
                    self.hasBone = False
        return usedVertices, faces, usedVertexIndexArray, boneWeightInfos, vertex_colors, vertexStart


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
