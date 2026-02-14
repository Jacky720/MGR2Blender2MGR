from __future__ import annotations
import bpy
from idprop.types import IDPropertyArray
from io import BufferedReader, BufferedWriter

from ..utils.ioUtils import read_uint32, write_float, write_uInt32

# TODO: Better exception classes
# TODO: check all "tentative" matches (somehow)


"""
General sectioning and parenting info.
Referenced by Slice5Data (tentative), Slice8Data (tentative)
"""
class Slice1Data:
    name: str
    parent_ind: int  # short, -1 accepted
    unk_6: int  # short
    
    def __init__(self, name: str = "CG_DEFAULT", parent_ind: int = -1, unk_6: int = -1):
        self.name = name
        self.parent_ind = parent_ind
        self.unk_6 = unk_6
    
    def from_collection(self, entry_index: int, collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        i: str = f"{entry_index:2d}"
        self.name = collection[f"1-{i}-name"]
        self.parent_ind = collection[f"1-{i}-parent"]
        self.unk_6 = collection[f"1-{i}-short_6"]
        return self
    
    def to_collection(self, entry_index: int, collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        i: str = f"{entry_index:2d}"
        collection[f"1-{i}-name"] = self.name
        collection[f"1-{i}-parent"] = self.parent_ind
        collection[f"1-{i}-short_6"] = self.unk_6
    
    @staticmethod
    def store_section(entries: list[Slice1Data], collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        for k in list(collection.keys()):
            if k.startswith("1-"):
                del collection[k]
        
        for i, entry in enumerate(entries):
            entry.to_collection(i, collection)
    
    @staticmethod
    def fetch_section(collection: bpy.types.Collection = None) -> list[Slice1Data]:
        if collection is None:
            collection = bpy.data.collections['WMB']
        out = []
        i = 0
        while any(k.startswith(f"1-{i:2d}-") for k in list(collection.keys())):
            out.append(Slice1Data().from_collection(i, collection))
            i += 1
        return out


"""
Unknown. Absent from sample generation model.
"""
class Slice2Data:
    unk_0: SVector3
    unk_C: int  # short
    unk_E: int  # short
    unk_10: SVector3
    unk_1C: int  # short
    unk_1E: int  # short
    unk_20: SVector3
    unk_2C: int  # short
    unk_2E: int  # short
    unk_30: SVector3
    
    def __init__(self, unk_0: SVector3 = None, unk_C: int = 0, unk_E: int = 0,
                 unk_10: SVector3 = None, unk_1C: int = 0, unk_1E: int = 0,
                 unk_20: SVector3 = None, unk_2C: int = 0, unk_2E: int = 0,
                 unk_30: SVector3 = None):
        if unk_0 is None:
            unk_0 = SVector3()
        if unk_10 is None:
            unk_10 = SVector3()
        if unk_20 is None:
            unk_20 = SVector3()
        if unk_30 is None:
            unk_30 = SVector3()
        self.unk_0 = unk_0
        self.unk_C = unk_C
        self.unk_E = unk_E
        self.unk_10 = unk_10
        self.unk_1C = unk_1C
        self.unk_1E = unk_1E
        self.unk_20 = unk_20
        self.unk_2C = unk_2C
        self.unk_2E = unk_2E
        self.unk_30 = unk_30
    
    def from_collection(self, entry_index: int, collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        i: str = f"{entry_index:2d}"
        self.unk_0.from_collection(collection[f"2-{i}-vec_0"])
        self.unk_C = collection[f"2-{i}-flag_C"][0]
        self.unk_E = collection[f"2-{i}-flag_C"][1]
        self.unk_10.from_collection(collection[f"2-{i}-vec_10"])
        self.unk_1C = collection[f"2-{i}-flag_1C"][0]
        self.unk_1E = collection[f"2-{i}-flag_1C"][1]
        self.unk_20.from_collection(collection[f"2-{i}-vec_20"])
        self.unk_2C = collection[f"2-{i}-flag_2C"][0]
        self.unk_2E = collection[f"2-{i}-flag_2C"][1]
        self.unk_30.from_collection(collection[f"2-{i}-vec_30"])
        return self
    
    def to_collection(self, entry_index: int, collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        i: str = f"{entry_index:2d}"
        self.unk_0.to_collection(collection, f"2-{i}-vec_0")
        collection[f"2-{i}-flag_C"] = [self.unk_C, self.unk_E]
        self.unk_10.to_collection(collection, f"2-{i}-vec_10")
        collection[f"2-{i}-flag_1C"] = [self.unk_1C, self.unk_1E]
        self.unk_20.to_collection(collection, f"2-{i}-vec_20")
        collection[f"2-{i}-flag_2C"] = [self.unk_2C, self.unk_2E]
        self.unk_30.to_collection(collection, f"2-{i}-vec_30")
    
    @staticmethod
    def store_section(entries: list[Slice2Data], collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        for k in list(collection.keys()):
            if k.startswith("2-"):
                del collection[k]
        
        for i, entry in enumerate(entries):
            entry.to_collection(i, collection)
    
    @staticmethod
    def fetch_section(collection: bpy.types.Collection = None) -> list[Slice2Data]:
        if collection is None:
            collection = bpy.data.collections['WMB']
        out = []
        i = 0
        while any(k.startswith(f"2-{i:2d}-") for k in list(collection.keys())):
            out.append(Slice2Data().from_collection(i, collection))
            i += 1
        return out


"""
Suspected materials.
Referenced by Slice5Data (tentative)
References model materials (tentative)
"""
class Slice3Data:
    entries: list[Slice3Data.Slice3DataData]
    
    def __init__(self, entries: list[Slice3Data.Slice3DataData] = None):
        if entries is None:
            entries = []
        self.entries = entries
    
    def from_collection(self, entry_index: int, collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        self.entries = []
        j = 0
        while any(k.startswith(f"3-{entry_index:2d}-{j:2d}-") for k in list(collection.keys())):
            self.entries.append(self.Slice3DataData().from_collection(collection, entry_index, j))
            j += 1
        return self
    
    def to_collection(self, entry_index: int, collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        for sub_index, entry in enumerate(self.entries):
            entry.to_collection(collection, entry_index, sub_index)
    
    @staticmethod
    def store_section(entries: list[Slice3Data], collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        for k in list(collection.keys()):
            if k.startswith("3-"):
                del collection[k]
        
        for i, entry in enumerate(entries):
            entry.to_collection(i, collection)
    
    @staticmethod
    def fetch_section(collection: bpy.types.Collection = None) -> list[Slice3Data]:
        if collection is None:
            collection = bpy.data.collections['WMB']
        out = []
        i = 0
        while any(k.startswith(f"3-{i:2d}-") for k in list(collection.keys())):
            out.append(Slice3Data().from_collection(i, collection))
            i += 1
        return out
    
    class Slice3DataData:
        unk_0: SVector3
        unk_C: SVector3
        unk_18: SVector3
        unk_24: SVector3
        unk_30: SVector3
        mat_index: int
        
        def __init__(self, unk_0: SVector3 = None, unk_C: SVector3 = None,
                     unk_18: SVector3 = None, unk_24: SVector3 = None,
                     unk_30: SVector3 = None, mat_index: int = 0):
            if unk_0 is None:
                unk_0 = SVector3()
            if unk_C is None:
                unk_C = SVector3()
            if unk_18 is None:
                unk_18 = SVector3()
            if unk_24 is None:
                unk_24 = SVector3()
            if unk_30 is None:
                unk_30 = SVector3()
            self.unk_0 = unk_0
            self.unk_C = unk_C
            self.unk_18 = unk_18
            self.unk_24 = unk_24
            self.unk_30 = unk_30
            self.mat_index = mat_index
        
        def from_collection(self, collection: bpy.types.Collection,
                            entry_index: int, sub_index: int):
            # col may not be None here, assume handled by parent
            index: str = f"{entry_index:2d}-{sub_index:2d}"
            self.unk_0.from_collection(collection[f"3-{index}-A"])
            self.unk_C.from_collection(collection[f"3-{index}-B"])
            self.unk_18.from_collection(collection[f"3-{index}-C"])
            self.unk_24.from_collection(collection[f"3-{index}-D"])
            self.unk_30.from_collection(collection[f"3-{index}-E"])
            self.mat_index = collection[f"3-{index}-material"]
            
            return self
        
        def to_collection(self, collection: bpy.types.Collection,
                          entry_index: int, sub_index: int):
            # col may not be None here, assume handled by parent
            index: str = f"{entry_index:2d}-{sub_index:2d}"
            self.unk_0.to_collection(collection, f"3-{index}-A")
            self.unk_C.to_collection(collection, f"3-{index}-B")
            self.unk_18.to_collection(collection, f"3-{index}-C")
            self.unk_24.to_collection(collection, f"3-{index}-D")
            self.unk_30.to_collection(collection, f"3-{index}-E")
            collection[f"3-{index}-material"] = self.mat_index


"""
First set of face indices. Primary segment? Approximate correspondence with batches.
References Slice5Data (tentative)
"""
class Slice4Data:
    unk_0: SVector3
    unk_C: SVector3
    chunk5_ind: int
    batch_ind: int
    unk_20: int  # short
    unk_22: int  # short, tentatively material index? That can't be right.
    unk_24: int
    unk_array: list[int]  # 20 elements, or 0.
    faces: SFaceSet
    
    def __init__(self, unk_0: SVector3 = None, unk_C: SVector3 = None, chunk5_ind: int = 0,
                 batch_ind: int = 0, unk_20: int = 0, unk_22: int = 0, unk_24: int = 0,
                 unk_array: list[int] = None, faces: SFaceSet = None):
        if unk_0 is None:
            unk_0 = SVector3()
        if unk_C is None:
            unk_C = SVector3()
        if unk_array is None:
            unk_array = [0] * 20
        if faces is None:
            faces = SFaceSet()
        self.unk_0 = unk_0
        self.unk_C = unk_C
        self.chunk5_ind = chunk5_ind
        self.batch_ind = batch_ind
        self.unk_20 = unk_20
        self.unk_22 = unk_22
        self.unk_24 = unk_24
        self.unk_array = unk_array
        self.faces = faces
    
    def from_collection(self, entry_index: int, collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        i: str = f"{entry_index:2d}"
        self.unk_0.from_collection(collection[f"4-{i}-vec_0"])
        self.unk_C.from_collection(collection[f"4-{i}-vec_C"])
        self.chunk5_ind = collection[f"4-{i}-ref5"]
        self.batch_ind = collection[f"4-{i}-refBatch"]
        self.unk_20 = collection[f"4-{i}-short_20"]
        self.unk_22 = collection[f"4-{i}-short_22"]
        self.unk_24 = collection[f"4-{i}-int_24"]
        self.unk_array = list(collection[f"4-{i}-array"])
        self.faces.from_collection(collection, f"4-{i}")
        
        return self
    
    def to_collection(self, entry_index: int, collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        i: str = f"{entry_index:2d}"
        self.unk_0.to_collection(collection, f"4-{i}-vec_0")
        self.unk_C.to_collection(collection, f"4-{i}-vec_C")
        collection[f"4-{i}-ref5"] = self.chunk5_ind
        collection[f"4-{i}-refBatch"] = self.batch_ind
        collection[f"4-{i}-short_20"] = self.unk_20
        collection[f"4-{i}-short_22"] = self.unk_22
        collection[f"4-{i}-int_24"] = self.unk_24
        collection[f"4-{i}-array"] = self.unk_array
        self.faces.to_collection(collection, f"4-{i}")
    
    @staticmethod
    def store_section(entries: list[Slice4Data], collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        for k in list(collection.keys()):
            if k.startswith("4-"):
                del collection[k]
        
        for i, entry in enumerate(entries):
            entry.to_collection(i, collection)
    
    @staticmethod
    def fetch_section(collection: bpy.types.Collection = None) -> list[Slice4Data]:
        if collection is None:
            collection = bpy.data.collections['WMB']
        out = []
        i = 0
        while any(k.startswith(f"4-{i:2d}-") for k in list(collection.keys())):
            out.append(Slice4Data().from_collection(i, collection))
            i += 1
        return out


"""
Confusing meta-reference.
Referenced by Slice4Data (tentative)
References Slice1Data (tentative), Slice3Data (tentative)
"""
class Slice5Data:
    vertgroup_ind: int
    chunk1_ind: int  # short
    unk_6: int  # short
    chunk3_ind: int  # short, -1 accepted
    unk_A: int  # short
    unk_array: list[list[int]]  # 2D short array
    
    def __init__(self, vertgroup_ind: int = 0, chunk1_ind: int = 0, unk_6: int = 0,
                 chunk3_ind: int = -1, unk_A: int = 0, unk_array: list[list[int]] = None):
        if unk_array is None:
            unk_array = []
        self.vertgroup_ind = vertgroup_ind
        self.chunk1_ind = chunk1_ind
        self.unk_6 = unk_6
        self.chunk3_ind = chunk3_ind
        self.unk_A = unk_A
        self.unk_array = unk_array
        
    def from_collection(self, entry_index: int, collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        i: str = f"{entry_index:2d}"
        self.vertgroup_ind = collection[f"5-{i}-refVertexGroup"]
        self.chunk1_ind = collection[f"5-{i}-ref1"]
        self.unk_6 = collection[f"5-{i}-short_6"]
        self.chunk3_ind = collection[f"5-{i}-ref3"]
        self.unk_A = collection[f"5-{i}-short_A"]
        self.unk_array = []
        j = 0
        while f"5-{i}-array-{j:2d}" in collection:
            self.unk_array.append(list(collection[f"5-{i}-array-{j:2d}"]))
            j += 1
        
        return self
    
    def to_collection(self, entry_index: int, collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        i: str = f"{entry_index:2d}"
        collection[f"5-{i}-refVertexGroup"] = self.vertgroup_ind
        collection[f"5-{i}-ref1"] = self.chunk1_ind
        collection[f"5-{i}-short_6"] = self.unk_6
        collection[f"5-{i}-ref3"] = self.chunk3_ind
        collection[f"5-{i}-short_A"] = self.unk_A
        for j, sublist in enumerate(self.unk_array):
            collection[f"5-{i}-array-{j:2d}"] = sublist
    
    @staticmethod
    def store_section(entries: list[Slice5Data], collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        for k in list(collection.keys()):
            if k.startswith("5-"):
                del collection[k]
        
        for i, entry in enumerate(entries):
            entry.to_collection(i, collection)
    
    @staticmethod
    def fetch_section(collection: bpy.types.Collection = None) -> list[Slice5Data]:
        if collection is None:
            collection = bpy.data.collections['WMB']
        out = []
        i = 0
        while any(k.startswith(f"5-{i:2d}-") for k in list(collection.keys())):
            out.append(Slice5Data().from_collection(i, collection))
            i += 1
        return out

    @staticmethod
    def sort(collection: bpy.types.Collection = None) -> None:
        if collection is None:
            collection = bpy.data.collections["WMB"]
        section = Slice5Data.fetch_section(collection)
        section = sorted(section, key=lambda x: x.vertgroup_ind)
        Slice5Data.store_section(section, collection)


"""
Base vertex/face data for later sections
Referenced by Slice7Data (tentative), Slice8Data (tentative), Slice9Data (tentative)
"""
class Slice6Data:
    data: SGeometry
    
    def __init__(self, data: SGeometry = None):
        if data is None:
            data = SGeometry()
        self.data = data
        
    def from_collection(self, entry_index: int, collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        i: str = f"{entry_index:2d}"
        self.data.from_collection(collection, f"6-{i}")
        
        return self
    
    def to_collection(self, entry_index: int, collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        i: str = f"{entry_index:2d}"
        self.data.to_collection(collection, f"6-{i}")
    
    @staticmethod
    def store_section(entries: list[Slice6Data], collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        for k in list(collection.keys()):
            if k.startswith("6-"):
                del collection[k]
        
        for i, entry in enumerate(entries):
            entry.to_collection(i, collection)
    
    @staticmethod
    def fetch_section(collection: bpy.types.Collection = None) -> list[Slice6Data]:
        if collection is None:
            collection = bpy.data.collections['WMB']
        out = []
        i = 0
        while any(k.startswith(f"6-{i:2d}-") for k in list(collection.keys())):
            out.append(Slice6Data().from_collection(i, collection))
            i += 1
        return out


"""
Subgroups of Slice6 vertex data
References Slice6Data (tentative)
"""
class Slice7Data:
    unk_0: SVector3
    unk_C: SVector3
    chunk6_ind: int
    unk_1C: float
    faces: SFaceSet
    
    def __init__(self, unk_0: SVector3 = None, unk_C: SVector3 = None, chunk6_ind: int = 0,
                 unk_1C: float = 0.0, faces: SFaceSet = None):
        if unk_0 is None:
            unk_0 = SVector3()
        if unk_C is None:
            unk_C = SVector3()
        if faces is None:
            faces = SFaceSet()
        self.unk_0 = unk_0
        self.unk_C = unk_C
        self.chunk6_ind = chunk6_ind
        self.unk_1C = unk_1C
        self.faces = faces
        
    def from_collection(self, entry_index: int, collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        i: str = f"{entry_index:2d}"
        self.unk_0.from_collection(collection[f"7-{i}-vec_0"])
        self.unk_C.from_collection(collection[f"7-{i}-vec_C"])
        self.chunk6_ind = collection[f"7-{i}-ref6"]
        self.unk_1C = collection[f"7-{i}-float_1C"]
        self.faces.from_collection(collection, f"7-{i}")
        
        return self
    
    def to_collection(self, entry_index: int, collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        i: str = f"{entry_index:2d}"
        self.unk_0.to_collection(collection, f"7-{i}-vec_0")
        self.unk_C.to_collection(collection, f"7-{i}-vec_C")
        collection[f"7-{i}-ref6"] = self.chunk6_ind
        collection[f"7-{i}-float_1C"] = self.unk_1C
        self.faces.to_collection(collection, f"7-{i}")
    
    @staticmethod
    def store_section(entries: list[Slice7Data], collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        for k in list(collection.keys()):
            if k.startswith("7-"):
                del collection[k]
        
        for i, entry in enumerate(entries):
            entry.to_collection(i, collection)
    
    @staticmethod
    def fetch_section(collection: bpy.types.Collection = None) -> list[Slice7Data]:
        if collection is None:
            collection = bpy.data.collections['WMB']
        out = []
        i = 0
        while any(k.startswith(f"7-{i:2d}-") for k in list(collection.keys())):
            out.append(Slice7Data().from_collection(i, collection))
            i += 1
        return out


"""
Additional metadata?
References Slice1Data (tentative), Slice7Data (tentative)
"""
class Slice8Data:
    unk_0: SVector4
    unk_10: SVector4
    unk_20: SVector4
    unk_30: SVector3
    chunk1_ind: int
    unk_40: float
    unk_44: float
    unk_48: int  # short
    unk_4A: int  # short
    unk_4C: int
    chunk7_ind: int
    unk_54: int
    
    def __init__(self, unk_0: SVector4 = None, unk_10: SVector4 = None,
                 unk_20: SVector4 = None, unk_30: SVector3 = None,
                 chunk1_ind: int = 0, unk_40: float = 0.0, unk_44: int = 0.0, unk_48: int = 1,
                 unk_4A: int = 0, unk_4C: int = 0, chunk7_ind: int = 0, unk_54: int = 1):
        if unk_0 is None:
            unk_0 = SVector4()
        if unk_10 is None:
            unk_10 = SVector4()
        if unk_20 is None:
            unk_20 = SVector4()
        if unk_30 is None:
            unk_30 = SVector3()
        self.unk_0 = unk_0
        self.unk_10 = unk_10
        self.unk_20 = unk_20
        self.unk_30 = unk_30
        self.chunk1_ind = chunk1_ind
        self.unk_40 = unk_40
        self.unk_44 = unk_44
        self.unk_48 = unk_48
        self.unk_4A = unk_4A
        self.unk_4C = unk_4C
        self.chunk7_ind = chunk7_ind
        self.unk_54 = unk_54
        
    def from_collection(self, entry_index: int, collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        i: str = f"{entry_index:2d}"
        flatVecs = list(collection[f"8-{i}-vectors"])
        self.unk_0 = SVector4(flatVecs[0], flatVecs[1], flatVecs[2], flatVecs[3])
        self.unk_10 = SVector4(flatVecs[4], flatVecs[5], flatVecs[6], flatVecs[7])
        self.unk_20 = SVector4(flatVecs[8], flatVecs[9], flatVecs[10], flatVecs[11])
        self.unk_30 = SVector3(flatVecs[12], flatVecs[13], flatVecs[14])
        self.chunk1_ind = collection[f"8-{i}-ref1"]
        self.unk_40 = collection[f"8-{i}-vec_40"][0]
        self.unk_44 = collection[f"8-{i}-vec_40"][1]
        self.unk_48 = collection[f"8-{i}-short_48"]
        self.unk_4A = collection[f"8-{i}-short_4A"]
        self.unk_4C = collection[f"8-{i}-int_4C"]
        self.chunk7_ind = collection[f"8-{i}-ref7"]
        self.unk_54 = collection[f"8-{i}-int_54"]
        
        return self
    
    def to_collection(self, entry_index: int, collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        i: str = f"{entry_index:2d}"
        collection[f"8-{i}-vectors"] = [
            self.unk_0.x, self.unk_0.y, self.unk_0.z, self.unk_0.w,
            self.unk_10.x, self.unk_10.y, self.unk_10.z, self.unk_10.w,
            self.unk_20.x, self.unk_20.y, self.unk_20.z, self.unk_20.w,
            self.unk_30.x, self.unk_30.y, self.unk_30.z
        ]
        collection[f"8-{i}-ref1"] = self.chunk1_ind
        collection[f"8-{i}-vec_40"] = [self.unk_40, self.unk_44]
        collection[f"8-{i}-short_48"] = self.unk_48
        collection[f"8-{i}-short_4A"] = self.unk_4A
        collection[f"8-{i}-int_4C"] = self.unk_4C
        collection[f"8-{i}-ref7"] = self.chunk7_ind
        collection[f"8-{i}-int_54"] = self.unk_54
    
    @staticmethod
    def store_section(entries: list[Slice8Data], collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        for k in list(collection.keys()):
            if k.startswith("8-"):
                del collection[k]
        
        for i, entry in enumerate(entries):
            entry.to_collection(i, collection)
    
    @staticmethod
    def fetch_section(collection: bpy.types.Collection = None) -> list[Slice8Data]:
        if collection is None:
            collection = bpy.data.collections['WMB']
        out = []
        i = 0
        while any(k.startswith(f"8-{i:2d}-") for k in list(collection.keys())):
            out.append(Slice8Data().from_collection(i, collection))
            i += 1
        return out


"""
Final metadata, oddly 'incomplete'
References Slice8Data (tentative)
"""
class Slice9Data:
    unk_0: int  # short
    parent: int  # short, -1 accepted
    chunk8_ind: int  # short
    unk_6: int  # short, tentatively suspect number of Slice8Data entries
    unk_8: int
    
    def __init__(self, unk_0: int = 0, parent: int = -1, chunk8_ind: int = 0,
                 unk_6: int = 1, unk_8: int = 1):
        self.unk_0 = unk_0
        self.parent = parent
        self.chunk8_ind = chunk8_ind
        self.unk_6 = unk_6
        self.unk_8 = unk_8
        
    def from_collection(self, entry_index: int, collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        i: str = f"{entry_index:2d}"
        self.unk_0 = collection[f"9-{i}-short_0"]
        self.parent = collection[f"9-{i}-parent"]
        self.chunk8_ind = collection[f"9-{i}-ref8"]
        self.unk_6 = collection[f"9-{i}-short_6"]
        self.unk_8 = collection[f"9-{i}-int_8"]
        
        return self
    
    def to_collection(self, entry_index: int, collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        i: str = f"{entry_index:2d}"
        collection[f"9-{i}-short_0"] = self.unk_0
        collection[f"9-{i}-parent"] = self.parent
        collection[f"9-{i}-ref8"] = self.chunk8_ind
        collection[f"9-{i}-short_6"] = self.unk_6
        collection[f"9-{i}-int_8"] = self.unk_8
    
    @staticmethod
    def store_section(entries: list[Slice9Data], collection: bpy.types.Collection = None):
        if collection is None:
            collection = bpy.data.collections['WMB']
        for k in list(collection.keys()):
            if k.startswith("9-"):
                del collection[k]
        
        for i, entry in enumerate(entries):
            entry.to_collection(i, collection)
    
    @staticmethod
    def fetch_section(collection: bpy.types.Collection = None) -> list[Slice9Data]:
        if collection is None:
            collection = bpy.data.collections['WMB']
        out = []
        i = 0
        while any(k.startswith(f"9-{i:2d}-") for k in list(collection.keys())):
            out.append(Slice9Data().from_collection(i, collection))
            i += 1
        return out


"""Helper"""
class SVector3:
    x: float
    y: float
    z: float
    
    def __init__(self, x: float | list[float] = 0.0, y: float = 0.0, z: float = 0.0):
        if type(x) is list:
            self.x = x[0]
            self.y = x[1]
            self.z = x[2]
        else:
            self.x = x
            self.y = y
            self.z = z
    
    def from_collection(self, col_tuple: IDPropertyArray):
        if len(col_tuple) != 3:
            raise Exception("Invalid tuple to read Vector3")
        self.x = col_tuple[0]
        self.y = col_tuple[1]
        self.z = col_tuple[2]
        return self
    
    def to_collection(self, col: bpy.types.Collection, write_key: str):
        # col may not be None here, assume handled by parent
        col[write_key] = [self.x, self.y, self.z]
    
    def to_wmb(self, wmb_fp: BufferedWriter):
        write_float(wmb_fp, self.x)
        write_float(wmb_fp, self.y)
        write_float(wmb_fp, self.z)

"""Helper"""
class SVector4:
    x: float
    y: float
    z: float
    w: float
    
    def __init__(self, x: float | list[float] = 0.0, y: float = 0.0, z: float = 0.0, w: float = 1.0):
        if type(x) is list:
            self.x = x[0]
            self.y = x[1]
            self.z = x[2]
            self.w = x[3]
        else:
            self.x = x
            self.y = y
            self.z = z
            self.w = w
    
    def from_collection(self, col_tuple: idprop.types.IDPropertyArray):
        if len(col_tuple) != 3:
            raise Exception("Invalid tuple to read Vector3")
        self.x = col_tuple[0]
        self.y = col_tuple[1]
        self.z = col_tuple[2]
        self.w = col_tuple[3]
        return self
    
    def to_collection(self, col: bpy.types.Collection, write_key: str):
        # col may not be None here, assume handled by parent
        col[write_key] = [self.x, self.y, self.z, self.w]
    
    def to_wmb(self, wmb_fp: BufferedWriter):
        write_float(wmb_fp, self.x)
        write_float(wmb_fp, self.y)
        write_float(wmb_fp, self.z)
        write_float(wmb_fp, self.w)

"""Helper"""
class SFaceSet:
    vertexStart: int
    vertexCount: int
    faceStart: int
    faceCount: int
    
    def __init__(self, vertexStart: int = 0, vertexCount: int = 0, faceStart: int = 0, faceCount: int = 0):
        self.vertexStart = vertexStart
        self.vertexCount = vertexCount
        self.faceStart = faceStart
        self.faceCount = faceCount
    
    def from_collection(self, col: bpy.types.Collection, prefix: str):
        self.vertexStart = col[f"{prefix}-startVertex"]
        self.vertexCount = col[f"{prefix}-vertexCount"]
        self.faceStart = col[f"{prefix}-startIndex"]
        self.faceCount = col[f"{prefix}-indexCount"]
        
        return self
    
    def to_collection(self, col: bpy.types.Collection, prefix: str):
        col[f"{prefix}-startVertex"] = self.vertexStart
        col[f"{prefix}-vertexCount"] = self.vertexCount
        col[f"{prefix}-startIndex"] = self.faceStart
        col[f"{prefix}-indexCount"] = self.faceCount
    
    def from_wmb(self, wmb_fp: BufferedReader):
        self.vertexStart = read_uint32(wmb_fp)
        self.vertexCount = read_uint32(wmb_fp)
        self.faceStart = read_uint32(wmb_fp)
        self.faceCount = read_uint32(wmb_fp)
        
        return self
    
    def to_wmb(self, wmb_fp: BufferedWriter):
        write_uInt32(wmb_fp, self.vertexStart)
        write_uInt32(wmb_fp, self.vertexCount)
        write_uInt32(wmb_fp, self.faceStart)
        write_uInt32(wmb_fp, self.faceCount)
    
    def __str__(self):
        return f"v: {self.vertexStart}-{self.vertexStart + self.vertexCount}; f: {self.faceStart}-{self.faceStart + self.faceCount}"

"""Helper"""
class SGeometry:
    vertexes: list[SVector4]
    faces: list[int]  # list of int16
    
    def __init__(self, vertexes: list[SVector4] = None, faces: list[int] = None):
        if vertexes is None:
            vertexes = []
        if faces is None:
            faces = []
        self.vertexes = vertexes
        self.faces = faces
    
    def from_collection(self, col: bpy.types.Collection, prefix: str):
        vFlat = col[f"{prefix}-vertexes"]
        self.vertexes = []
        for j in range(0, len(vFlat), 4):
            self.vertexes.append(SVector4(vFlat[j], vFlat[j+1], vFlat[j+2], vFlat[j+3]))
        self.faces = list(col[f"{prefix}-faces"])
        
        return self
    
    def to_collection(self, col: bpy.types.Collection, prefix: str):
        vFlat = []
        for vector in self.vertexes:
            vFlat += [vector.x, vector.y, vector.z, vector.w]
        col[f"{prefix}-vertexes"] = vFlat
        col[f"{prefix}-faces"] = self.faces
