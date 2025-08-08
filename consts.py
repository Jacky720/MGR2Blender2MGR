
ADDON_NAME = __package__
DAT_EXTENSIONS = (".dat", ".dtt", ".eft", ".evn", ".eff")

parameterIDs = {

}

textureFlagDictonary = {
    0 : "Albedo 0",
    1 : "Albedo 1",
    2 : "Normal",
    3 : "Blended Normal",
    4 : "Cubemap",
    7 : "Lightmap",
    10 : "Tension Map"
}

reflectiveBlacklist = [
                       # These shaders will never have reflection:
                       "skn03_xbXxX",
                       # "siv00_sxmxb", "siv00_sxmvx", "siv00_sxmvb", "siv00_sxmfb", "siv20_sxxvx",
                       # "sis20_xxmvb", "sis20_xxxfb",
                       # These I'm not so sure about, but seem too reflective currently:
                       # "sis00_sxmxX", "sis00_sxmxb", "sis00_sxmvX",
                       # "siv00_sxwxx", "siv00_sxmxx", "siv00_sxmex",
                       # "sis20_sxxvX", "siv20_sxxfb",
                       "siv", "sis"
                       ]

transparentShaders = [
                      # These shaders will be given a cardboard cutout effect
                      # "siv01_sxmxx", "siv01_sxxvx", "siv01_sxmxx", "siv02_sxcxx",
                      # "siv21_sxxvx", "siv21_sxxxx", "siv22_sxwxx", "siv22_sxcvx", "siv23_sxcxx", "siv23_sbxex",
                      "siv01", "siv02", "siv2",
                      "sis03_sxxxX",
                      "ois01_xbceX", "ois01_sbceX",
                      # "ois02_sbxeX", "ois02_sbxxX", "ois02_xbceX", "ois02_xbxeX",
                      "ois02",
                      "cnm10_SxwXX", "cnm10_SxXXX", "cnm20_SxvXX",
                      # "har00_sbXtX", "har00_sbXxX", "har03_sbXtX",
                      "har",
                      ]

weakLightmapShaders = ["skn", "eye", "ois00_xbceX", "ois00_xbweX"]

def isReflective(shader_name):
    return not any(shader_name.startswith(x) for x in reflectiveBlacklist)

def isTransparent(shader_name):
    return any(shader_name.startswith(x) for x in transparentShaders)

def hasWeakLightmap(shader_name):
    return any(shader_name.startswith(x) for x in weakLightmapShaders)


def getTextureFlagFromDict(id):
    value = textureFlagDictonary.get(id)
    if value is not None:
        return value
    else:
        return str(id)
