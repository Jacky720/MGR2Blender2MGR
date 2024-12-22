wmb4_bonenames = {
    0: "HIP",
    1: "spine_1",
    2: "spine_2",
    3: "spine_3",
    
    4: "neck_1",
    5: "neck_2",
    6: "head",
    7: "mouth_L",
    8: "mouth_R",
    9: "jaw",
    10: "chin",
    11: "mouth_upper_1_L",
    12: "mouth_upper_2_L",
    13: "mouth_upper_3_L",
    14: "mouth_upper_1_R",
    15: "mouth_upper_2_R",
    16: "mouth_upper_3_R",
    
    17: "arm_1_L",
    18: "arm_2_L",
    19: "arm_3_L",
    20: "arm_underarmor_L",
    21: "arm_1_R",
    22: "arm_2_R",
    23: "arm_3_R",
    24: "arm_underarmor_R",
    
    25: "legs",
    26: "leg_1_L",
    27: "leg_2_L",
    28: "leg_3_L",
    29: "leg_4_L",
    30: "leg_5_L",
    31: "foot_1_L",
    32: "foot_2_L",
    33: "toe_flex_L_F",
    34: "toe_flex_L_R",
    35: "toe_flex_L_L",
    36: "toe_flex_L_B",
    37: "leg_1_R",
    38: "leg_2_R",
    39: "leg_3_R",
    40: "leg_4_R",
    41: "leg_5_R",
    42: "foot_1_R",
    43: "foot_2_R",
    44: "toe_flex_R_F",
    45: "toe_flex_R_L",
    46: "toe_flex_R_R",
    47: "toe_flex_R_B",
    
    # tail 48-65
    
    272: "gun_mount_arm_L",
    273: "gun_mount_arm_R",
    274: "gun_mount_leg_L",
    275: "gun_mount_leg_R",
    276: "laser_emitter",
    
    # sword arm 512-541
    512: "sword_armor_3",
    513: "sword_armor_4_F",
    514: "sword_armor_4_B",
    515: "sword_armor_1_F",
    516: "sword_armor_1_B",
    517: "sword_armor_2_F",
    518: "sword_armor_2_B",
    519: "sword_rig",
    520: "sword_1_F",
    521: "sword_2_F",
    522: "sword_3_F",
    523: "sword_4_F",
    524: "sword_5_F",
    525: "sword_6_F",
    526: "sword_7_F",
    527: "blade_1_F",
    528: "blade_2_F",
    529: "blade_3_F",
    530: "blade_4_F",
    531: "sword_1_B",
    532: "sword_2_B",
    533: "sword_3_B",
    534: "sword_4_B",
    535: "sword_5_B",
    536: "sword_6_B",
    537: "sword_7_B",
    538: "blade_1_B",
    539: "blade_2_B",
    540: "blade_3_B",
    541: "blade_4_B",
    
    # missile flaps 768-783
    
    2048: "missile_emitter_back_1_L",
    2049: "missile_emitter_back_2_L",
    2050: "missile_emitter_back_3_L",
    2051: "missile_emitter_back_1_R",
    2052: "missile_emitter_back_2_R",
    2053: "missile_emitter_back_3_R",
    # 16 more ranging 2054-2069
}

# there are 16 flaps
for i in range(16):
    direction = "F" if i % 2 == 0 else "B"
    wmb4_bonenames[768 + i] = f"missile_flap_{(i//2)+1}_{direction}"
    wmb4_bonenames[2054 + i] = f"missile_emitter_arm_{(i//2)+1}_{direction}"

# 18 tail bones
for i in range(18):
    wmb4_bonenames[48 + i] = f"tail_{i+1}"