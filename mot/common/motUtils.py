from __future__ import annotations
from dataclasses import dataclass
from math import atan, tan
from typing import Callable
import bpy
from mathutils import Vector

cameraId = 0x7000
camTargetId = 0x7001

class KeyFrame:
	interpolationType: str
	frame: int
	value: float
	m0: float|None
	m1: float|None
	applyInterpolation: Callable[[KeyFrameCombo|None, KeyFrameCombo], None]
	
	def __init__(self):
		self.interpolationType = ""
		self.frame = 0
		self.value = 0
		self.m0 = None
		self.m1 = None
		self.applyInterpolation = lambda kfData, kf: None

	def toString(self) -> str:
		return f"({self.frame}, {round(self.value, 2)})"
@dataclass
class KeyFrameCombo:
	mot: KeyFrame
	blend: bpy.types.Keyframe

class Spline:
	frame: int
	value: float
	m0: float
	m1: float

	def __init__(self, frame: int = None, value: float = None, m0: float = None, m1: float = None):
		self.frame = frame
		self.value = value
		self.m0 = m0
		self.m1 = m1

def getArmatureObject() -> bpy.types.Object:
	activeObj = bpy.context.active_object
	if activeObj is not None and activeObj.type == "ARMATURE":
		return activeObj
	allArmatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
	if len(allArmatures) == 0:
		return None
	wmbColl = bpy.data.collections.get("WMB")
	if wmbColl is None:
		return allArmatures[0]
	armaturesInWmbColl = [obj for obj in wmbColl.all_objects if obj.type == "ARMATURE"]
	if len(armaturesInWmbColl) == 0:
		return allArmatures[0]
	return armaturesInWmbColl[0]

def getCameraObject(constructIfMissing: bool) -> bpy.types.Object|None:
	activeObj = bpy.context.active_object
	if activeObj is not None and activeObj.type == "CAMERA" and activeObj.name.startswith("MOT Camera"):
		return activeObj
	collection: bpy.types.Collection = bpy.data.collections.get("MOT")
	if collection:
		cameras = [
			obj
			for obj in collection.all_objects
			if obj.type == "CAMERA" and obj.name.startswith("MOT Camera")
		]
		if len(cameras) > 0:
			return cameras[0]
	elif constructIfMissing:
		collection = bpy.data.collections.new("MOT")
		bpy.context.scene.collection.children.link(collection)
	if not constructIfMissing:
		return None
	cam = bpy.data.objects.new("MOT Camera", bpy.data.cameras.new("Camera"))
	trackingConstraint = cam.constraints.new("TRACK_TO")
	trackingConstraint.target = getCameraTarget(True)
	collection.objects.link(cam)
	return cam

def getCameraTarget(constructIfMissing: bool) -> bpy.types.Object|None:
	activeObj = bpy.context.active_object
	if activeObj is not None and activeObj.type == "EMPTY" and activeObj.name.startswith("MOT Camera Target"):
		return activeObj
	collection: bpy.types.Collection = bpy.data.collections.get("MOT")
	if collection:
		target = [
			obj
			for obj in collection.all_objects
			if obj.type == "EMPTY" and obj.name.startswith("MOT Camera Target")
		]
		if len(target) > 0:
			return target[0]
	elif constructIfMissing:
		collection = bpy.data.collections.new("MOT")
		bpy.context.scene.collection.children.link(collection)
	if not constructIfMissing:
		return None
	target = bpy.data.objects.new("MOT Camera Target", None)
	target.empty_display_size = 0.15
	collection.objects.link(target)
	return target

def getBoneFCurve(armatureObj: bpy.types.Object, bone: bpy.types.PoseBone, property: str, index: int) -> bpy.types.FCurve:
	for fCurve in armatureObj.animation_data.action.fcurves:
		if fCurve.data_path == f"pose.bones[\"{bone.name}\"].{property}" and fCurve.array_index == index:
			return fCurve
	return None

def getObjFCurve(obj: bpy.types.Object, property: str, index: int) -> bpy.types.FCurve:
	for fCurve in obj.animation_data.action.fcurves:
		if fCurve.data_path == property and fCurve.array_index == index:
			return fCurve
	return None

def interpolateLinearVal(p0: KeyFrame, p1: KeyFrame, frame: int) -> float:
	return \
		(1 - (frame - p0.frame) / (p1.frame - p0.frame)) * p0.value + \
		(frame - p0.frame) / (p1.frame - p0.frame) * p1.value

def interpolateSplineVal(p0: KeyFrame, p1: KeyFrame, frame: int) -> Spline:
	# float t = (float)(index - keys[i].index)/(keys[i+1].index - keys[i].index)
	# float val = (2*t^3 - 3*t^2 + 1)*p0 + (t^3 - 2*t^2 + t)*m0 + (-2*t^3 + 3*t^2)*p1 + (t^3 - t^2)*m1;
	
	t = (frame - p0.frame) / (p1.frame - p0.frame)
	val = (2 * t ** 3 - 3 * t ** 2 + 1) * p0.value + (t ** 3 - 2 * t ** 2 + t) * p0.m1 + (-2 * t ** 3 + 3 * t ** 2) * p1.value + (t ** 3 - t ** 2) * p1.m1
	spline = Spline()
	spline.frame = frame
	spline.value = val
	spline.m0 = p0.m1 * (1 - t) + p1.m0 * t
	spline.m1 = spline.m0
	return spline

def slopeToVec2D(slope: float) -> Vector:
	v = Vector((1, slope))
	v.normalize()
	return v

def hermitVecToBezierVec(vec: Vector) -> Vector:
	return vec / 3

def alignTo4(num: int) -> int:
	return (num + 3) & ~3

def fovToFocalLength(camData, fovRad: float) -> float:
	fovRad *=  16 / 9
	sensorSize = max(camData.sensor_width, camData.sensor_height)
	return sensorSize / (2 * tan(fovRad / 2))

def focalLengthToFov(camData, focalLength: float) -> float:
	sensorSize = max(camData.sensor_width, camData.sensor_height)
	fovRad = 2 * atan(sensorSize / (2 * focalLength))
	return fovRad / 16 * 9
