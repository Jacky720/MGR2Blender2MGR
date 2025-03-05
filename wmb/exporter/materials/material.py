from ....utils.util import ShowMessageBox

class c_material(object):
    def __init__(self, offsetMaterialName, material, wmb4=False):
        self.offsetMaterial = offsetMaterialName
        self.b_material = material

        def get_textures(self, material, offsetTextures):
            offset = offsetTextures
            numTextures = 0
            textures = []
            
            for texture in material.mgr_data.textures:
                print(f"{texture.flag} : {texture.id}")
                numTextures += 1

            offsetName = offset + numTextures * 8

            for texobj in material.mgr_data.textures:
                texture = texobj.id
                flag = texobj.flag

                textures.append([offsetName, texture, flag])
            
            # proper sorting
            sortedTextures = []
            for tex in textures:
                flag = tex[2]
                sortedTextures.append([tex, flag])
            
            # I'm using "tex" really loosely here, since it's become:
            # [[offsetName, id, flag], flag]
            sortedTextures = sorted(sortedTextures, key=lambda tex: tex[1])
            return [tex[0] for tex in sortedTextures]

        def get_textures_StructSize(self, textures):
            textures_StructSize = 0
            for texture in textures:
                #print(texture[1])
                textures_StructSize += 8 # if not wmb4 else 4 # the other 4 are flags and now considered such
            #print(textures_StructSize)
            return textures_StructSize

        def get_numParameterGroups(self, material):
            return len(material.mgr_data.parameters)

        def get_parameterGroups(self, material, offsetParameterGroups, numParameterGroups):
            parameterGroups = []
            offsetParameters = offsetParameterGroups + numParameterGroups * 12

            for i in range(numParameterGroups):
                index = i

                if index == 1:
                    index = -1

                parameters = []
                parameters.append(material.mgr_data.parameters[i].value[0])
                parameters.append(material.mgr_data.parameters[i].value[0])
                parameters.append(material.mgr_data.parameters[i].value[0])
                parameters.append(material.mgr_data.parameters[i].value[0])
                        
                numParameters = len(parameters)

                parameterGroups.append([index, offsetParameters, numParameters, parameters])

                offsetParameters += numParameters * 4

            return parameterGroups

        def get_parameterGroups_StructSize(self, parameterGroups):
            parameterGroups_StructSize = 0
            for parameterGroup in parameterGroups:
                parameterGroups_StructSize += 16
            return parameterGroups_StructSize

        def get_variables(self, material, offsetVariables):
            numVariables = 0
            for key, val in material.items():
                if (isinstance(val, float)) and (key[0] not in ('0', '1')):
                    numVariables += 1
            
            variables = []
            offset = offsetVariables + numVariables * 8
            for key, val in material.items():
                if (isinstance(val, float)) and (key[0] not in ('0', '1')):
                    offsetName = offset
                    value = val
                    name = key
                    variables.append([offsetName, value, name])
                    offset += len(name) + 1
            return variables

        def get_variables_StructSize(self, variables):
            return 0

        self.unknown0 = [] if wmb4 else [2016, 7, 5, 15] # This is probably always the same as far as I know?

        self.offsetName = self.offsetMaterial

        self.offsetShaderName = self.offsetName + len(self.b_material.name) + 1

        self.offsetShaderName = self.offsetName

        '''if not 'Shader_Name' in self.b_material:
            ShowMessageBox('Shader_Name not found. The exporter just tried converting a material that does not have all the required data. Check system console for details.', 'Invalid Material', 'ERROR')
            print('[ERROR] Invalid Material: Shader_Name not found.')
            print(' - If you know all materials used are valid, try ticking "Purge Materials" at export, this will clear all unused materials from your Blender file that might still be lingering.')
            print(' - WARNING: THIS WILL PERMANENTLY REMOVE ALL UNUSED MATERIALS.')'''
        # TODO Reimplement  

        wmbShaderName = self.b_material.mgr_data.shader_name
    
        self.unknown1 = 1                           # This probably also the same mostly

        self.offsetTextures = self.offsetShaderName + len(wmbShaderName)
        self.offsetTextures += 16 - (self.offsetTextures % 16)

        self.textures = get_textures(self, self.b_material, self.offsetTextures)

        self.numTextures = len(self.textures)

        self.offsetParameterGroups = self.offsetTextures + get_textures_StructSize(self, self.textures)
        #print(hex(self.offsetParameterGroups))
        if wmb4 and (self.offsetParameterGroups % 16 > 0):
            self.offsetParameterGroups += 16 - (self.offsetParameterGroups % 16)

        self.numParameterGroups = get_numParameterGroups(self, self.b_material)  

        self.parameterGroups = get_parameterGroups(self, self.b_material, self.offsetParameterGroups, self.numParameterGroups)

        self.offsetVariables = self.offsetParameterGroups + get_parameterGroups_StructSize(self, self.parameterGroups)

        self.variables = get_variables(self, self.b_material, self.offsetVariables)

        self.numVariables = len(self.variables)

        self.name = self.b_material.name

        self.shaderName = wmbShaderName
        
        self.materialNames_StructSize = self.offsetVariables + get_variables_StructSize(self, self.variables) - self.offsetName
        print(self.offsetShaderName, self.offsetTextures, self.offsetParameterGroups, self.materialNames_StructSize)