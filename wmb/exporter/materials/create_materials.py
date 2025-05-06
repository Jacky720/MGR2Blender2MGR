from .material import c_material
from ....utils.util import getUsedMaterials


class c_materials(object):
    def __init__(self, materialsStart, wmb4=False, collectionName='WMB'):
        
        def get_materials(self):
            materials = []
            offsetMaterialName = materialsStart

            # Material Headers
            offsetMaterialName += 24 * len(getUsedMaterials(collectionName))
            
            if (offsetMaterialName%16>0):
                offsetMaterialName += 16 - (offsetMaterialName%16)

            for mat in getUsedMaterials(collectionName):
                print('[+] Generating Material', mat.name)
                material = c_material(offsetMaterialName, mat, wmb4)
                materials.append(material)

                offsetMaterialName += material.materialNames_StructSize

            return materials
        
        def get_materials_StructSize(self, materials):
            materials_StructSize = 0
            for material in materials:
                materials_StructSize += (48 if not wmb4 else 24) + material.materialNames_StructSize
                #if wmb4 and (materials_StructSize%16>0):
                #    materials_StructSize += 16 - (materials_StructSize%16)
                    
            return materials_StructSize

        self.materials = get_materials(self)
        self.materials_StructSize = get_materials_StructSize(self, self.materials)