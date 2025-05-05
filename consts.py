
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

reflectiveBlacklist = ["skn03_xbXxX","siv00_sxmxb", "siv00_sxmvx", "siv00_sxmvb", "sis20_xxmvb", "siv20_sxxvx", "sis20_xxxfb", "siv00_sxmfb"] # These shaders will never have reflection
transparentShaders = ["ois02_sbxeX", "cnm10_SxwXX", "siv23_sbxex", "siv01_sxxvx"] # These shaders will be given a cardboard cutout effect

def getTextureFlagFromDict(id):
    value = textureFlagDictonary.get(id)
    if value is not None:
        return value
    else:
        return str(id)
