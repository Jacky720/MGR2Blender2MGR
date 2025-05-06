
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

reflectiveBlacklist = ["skn03_xbXxX","siv00_sxmxb", "siv00_sxmvx", "siv00_sxmvb", "sis20_xxmvb", "siv20_sxxvx", "sis20_xxxfb", "siv00_sxmfb", # These shaders will never have reflection
"sis20_sxxvX", "sis00_sxmxX", "sis00_sxmxb", "siv00_sxwxx", "siv00_sxmxx", "siv00_sxmex", "sis00_sxmvX", "siv20_sxxfb"] # These I'm not so sure about but seem too reflective currently
transparentShaders = ["siv01_sxmxx", "ois02_sbxeX", "cnm10_SxwXX", "siv23_sbxex", "siv21_sxxxx", "siv01_sxxvx", "siv01_sxmxx", "sis03_sxxxX", "siv21_sxxvx", "cnm10_SxXXX", "siv02_sxcxx", "cnm20_SxvXX", "siv23_sxcxx", "siv22_sxwxx", "siv22_sxcvx"] # These shaders will be given a cardboard cutout effect

def getTextureFlagFromDict(id):
    value = textureFlagDictonary.get(id)
    if value is not None:
        return value
    else:
        return str(id)
