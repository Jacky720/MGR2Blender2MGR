
from ..utils.ioUtils import SmartIO, readBe_uint32, readBe_int16, readBe_float, writeBe_int32, writeBe_uint32, writeBe_uint16, writeBe_float
import bmesh
import bpy

class PATH_Header:
    def __init__(self, path_fp):
        self.type = readBe_uint32(path_fp)
        self.nodeCount = readBe_uint32(path_fp)
        self.unk1 = readBe_uint32(path_fp)
        self.indiceCount = readBe_uint32(path_fp)
        self.unk2 = readBe_uint32(path_fp)

class PATH_NodeInfo:
    def __init__(self, path_fp):
        self.index = readBe_uint32(path_fp)
        self.x = readBe_float(path_fp)
        self.y = readBe_float(path_fp)
        self.z = readBe_float(path_fp)
        self.w = readBe_float(path_fp)
        self.flags = readBe_uint32(path_fp)
        self.unk2 = readBe_int16(path_fp)
        self.groupNo = readBe_int16(path_fp)
        self.shortCount = readBe_uint32(path_fp)
        self.parameters = []
        
        print("-- Nav Node Info --")
        print("Index: " + str(self.index))
        print("Flags: " + str(self.flags))
        print("Parameter Count: " + str(self.shortCount)) 
        
        for x in range(self.shortCount):
            self.parameters.append(readBe_int16(path_fp))
            


class PATH_Indice:
    def __init__(self, path_fp):
        self.index = readBe_uint32(path_fp)
        self.pad1 = readBe_uint32(path_fp)
        self.pad2 = readBe_uint32(path_fp)
        self.priority = readBe_float(path_fp)
    
def export(filepath):
    
    navmesh_collection = bpy.data.collections.get('NAVMESH')
    if navmesh_collection:
        print(f"Found the NAVMESH collection: {navmesh_collection.name}")
    else:
        return
    
    file = open(filepath, "wb")
    
    writeBe_uint32(file, 537989654)
    writeBe_uint32(file, len(navmesh_collection.objects))
    writeBe_uint32(file, navmesh_collection["param1"])
    writeBe_uint32(file, len(navmesh_collection["IndexIndexs"]))
    writeBe_uint32(file, navmesh_collection["param2"])
    
    for obj in navmesh_collection.objects:
        writeBe_uint32(file, int(obj.name))
        writeBe_float(file, float(obj.location.x))
        writeBe_float(file, float(obj.location.z))
        writeBe_float(file, float(-obj.location.y))
        writeBe_float(file, obj["w"])
        writeBe_int32(file, obj["flags"])
        writeBe_uint32(file, obj["unk2"])
        writeBe_int32(file, obj["groupNo"])
        writeBe_uint32(file, len(obj["parameters"]))
        for x in obj["parameters"]:
            writeBe_uint16(file, x)
    
    for ind in navmesh_collection["IndexIndexs"]:
        writeBe_uint32(file, ind)
        writeBe_uint32(file, 0)
        writeBe_uint32(file, 0)
        writeBe_float(file, navmesh_collection["IndexWeights"][ind])
    
    writeBe_uint32(file, 0)
    writeBe_uint32(file, 0)
    writeBe_uint32(file, 131071)
    writeBe_uint16(file, 65535)
    
    file.close()

def main(filepath):
    print("Importing navigation data...")
    file = open(filepath, "rb")
    
    pathdata = bpy.data.collections.new('NAVMESH')
    bpy.context.scene.collection.children.link(pathdata)
    
    header = PATH_Header(file)
    nodes = []
    indices = []
    
    print("-- Nav Mesh Info --")
    print("Node Count: " + str(header.nodeCount))
    print("Index Count: " + str(header.indiceCount))
    
    for x in range(header.nodeCount):
        node = PATH_NodeInfo(file)
        nodes.append(node)
        

    for x in range(header.indiceCount):
        index = PATH_Indice(file)
        indices.append(index)
    
    pathdata["param1"] = header.unk1
    pathdata["param2"] = header.unk2
    
    indexWeightList = []
    indexIndexList = []
    for x in indices:
        indexWeightList.append(x.priority)
        indexIndexList.append(x.index)
        
    pathdata["IndexIndexs"] = indexIndexList
    pathdata["IndexWeights"] = indexWeightList 
    
    
    
    for x in nodes:
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(x.x, -x.z, x.y))
        empty = bpy.context.object
        if empty:
            empty.name = str(x.index)
            empty["w"] = x.w
            empty["flags"] = x.flags
            empty["unk2"] = x.unk2
            empty["groupNo"] = x.groupNo
            empty["parameters"] = x.parameters
            
            pathdata.objects.link(empty)

            default_collection = bpy.context.view_layer.active_layer_collection.collection
            if empty.name in default_collection.objects:
                default_collection.objects.unlink(empty)
    
    file.close()
    
    