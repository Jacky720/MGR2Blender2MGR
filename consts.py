
ADDON_NAME = __package__
DAT_EXTENSIONS = (".dat", ".dtt", ".eft", ".evn", ".eff")

parameterIDs = {

}



textureFlagDictonary = {
    0 : "Albedo 0",
    1 : "Albedo 1",
    2 : "Light Map",
    3 : "Normal",
    10 : "Tension Map"
}

def getTextureFlagFromDict(id):
    value = textureFlagDictonary.get(id)
    if value is not None:
        return value
    else:
        return str(id)