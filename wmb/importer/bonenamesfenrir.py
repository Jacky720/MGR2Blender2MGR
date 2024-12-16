wmb4_bonenames = {
    0: "HIP",
    1: "spine_1",
    2: "spine_2",
    3: "spine_3",
    4: "neck",
    5: "neck_2",
    6: "head",
    
    7: "jaw",
    8: "tongue_1",
    9: "tongue_2",
    10: "tongue_3",
    11: "tongue_4",
    
    17: "shoulder_R",
    18: "upper_leg_FR",
    19: "lower_leg_FR",
    20: "paw_FR",
    22: "shoulder_L",
    23: "upper_leg_FL",
    24: "lower_leg_FL",
    25: "paw_FL",
    
    27: "thigh_R",
    28: "upper_leg_BR",
    29: "lower_leg_BR",
    30: "paw_BR",
    32: "thigh_L",
    33: "upper_leg_BL",
    34: "lower_leg_BL",
    35: "paw_BL",
    
    37: "tail_1",
    38: "tail_2",
    39: "tail_3",
    40: "tail_4",
    41: "tail_5",
    42: "tail_6",
    43: "tail_7",
    44: "tail_8",
    45: "tail_9",
    46: "tail_10",
    47: "tail_11",
    
    48: "tentacle_a_1",
    49: "tentacle_a_2",
    50: "tentacle_a_3",
    51: "tentacle_b_1",
    52: "tentacle_b_2",
    53: "tentacle_b_3",
    54: "tentacle_c_1",
    55: "tentacle_c_2",
    56: "tentacle_c_3",
    
    63: "tail_alt_11", # yes, it overlaps
    64: "tail_alt_12",
    65: "tail_alt_13",
    
    72: "mask_R",
    73: "mask_L",
    
    74: "upper_leg_armor_FR",
    75: "lower_leg_armor_FR",
    76: "foot_knife_FR",
    85: "upper_leg_armor_FL",
    86: "lower_leg_armor_FL",
    87: "foot_knife_FL",
    96: "upper_leg_armor_BR",
    98: "lower_leg_armor_BR",
    99: "foot_knife_BR_or_rack_1", # they actually reused an ID
    107: "upper_leg_armor_BL",
    109: "lower_leg_armor_BL",
    110: "foot_knife_BL",
    
    100: "rack_2",
    101: "rack_3",
    102: "rack_mount_point",
    
    1280: "neck_armor_1_A",
    1281: "neck_armor_1_B",
    1282: "neck_armor_2",
    1283: "neck_armor_3_A",
    1284: "neck_armor_3_B",
    1285: "neck_armor_4_A",
    1286: "neck_armor_4_B",
    1287: "neck_armor_5_A",
    1288: "neck_armor_5_B",
    
    #1792: "tail_mount_point"
}
# not gonna duplicate this for both hands
fingers = {
    256: "claw_1A_F",
    257: "claw_1B_F",
    258: "claw_2A_F",
    259: "claw_2B_F",
    260: "claw_3A_F",
    261: "claw_3B_F",
    262: "claw_1A_B",
    263: "claw_1B_B",
    264: "claw_2A_B",
    265: "claw_2B_B",
    266: "claw_3A_B",
    267: "claw_3B_B",
}
for ind in fingers.keys():
    name = fingers[ind]
    wmb4_bonenames[ind] = name + "R"
    wmb4_bonenames[ind + 256] = name + "L"
