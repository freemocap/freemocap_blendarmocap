from dataclasses import dataclass
from math import radians

from .driver_interface import DriverProperties, DriverContainer, DriverType, ObjectType
from ..mapping import Slope, CustomProps


@dataclass(repr=True)
class CustomAngleMultiplier(DriverProperties):
    target_object: str
    provider_obj = str
    functions: list

    def __init__(self,
                 driver_target: str,
                 provider_obj: str,
                 x_slope: Slope,
                 z_slope: Slope):
        """ Provides eye driver properties to animate the lids.
            :param provider_obj: object providing rotation values.
            :param slope: factor to multiply and offset the rotation
            :param offset: offsets the base input value
        """
        prop_name = "fac"
        self.target_object = driver_target
        self.target_type = ObjectType.OBJECT
        self.custom_target_props = CustomProps(prop_name, x_slope.slope)
        self.provider_obj = provider_obj
        self.provider_type = ObjectType.BONE
        self.target_rig = "something"
        self.driver_type = DriverType.CUSTOM   # ? or single prop ?

        self.overwrite = True
        self.property_type = "rotation_euler"
        self.property_name = "fac"
        self.data_paths = [f'pose.bones["{provider_obj}"]["{prop_name}"]']*3
        # self.data_paths = ["rotation_euler[0]", "rotation_euler[1]", "rotation_euler[2]"]
        self.functions = ["", "", ""]


@dataclass(repr=True)
class FingerAngleDriver(DriverProperties):
    target_object: str
    functions: list

    def __init__(self,
                 driver_target: str,
                 provider_obj: object,
                 x_slope: Slope,
                 z_slope: Slope):
        """ Provides eye driver properties to animate the lids.
            :param provider_obj: object providing rotation values.
            :param slope: factor to multiply and offset the rotation
            :param offset: offsets the base input value
        """

        self.target_object = driver_target
        self.driver_type = DriverType.SINGLE
        self.provider_obj = provider_obj
        self.property_type = "rotation_euler"
        self.property_name = "rotation"
        self.overwrite = True
        self.data_paths = ["rotation_euler[0]", "rotation_euler[1]", "rotation_euler[2]"]
        self.functions = [
            # f"{x_slope.min_out}+{x_slope.slope}*({-x_slope.min_in}+(rotation))",
            f"{x_slope.min_out}+fac*({-x_slope.min_in}+(rotation))",
            "",
            f"{z_slope.min_out}+{z_slope.slope}*({-z_slope.min_in}+(rotation))"]


@dataclass(repr=True)
class FingerDriverContainer(DriverContainer):
    # shifting avgs for L / R hand z-angles
    # thumb / index / middle / ring / pinky
    z_inputs = [
        [20, 60],
        [-25, 60],
        [-35, 40],
        [-25, 40],
        [-40, 50],
    ]

    z_outputs = [
        [-25, 25.],
        [25., -40],
        [35., -25],
        [10., -30],
        [20., -30],
    ]

    x_inputs = [
        [0.011, 0.630], [0.010, 0.536], [0.008, 1.035],
        [0.105, 1.331], [0.014, 1.858], [0.340, 1.523],
        [0.046, 1.326], [0.330, 1.803], [0.007, 1.911],
        [0.012, 1.477], [0.244, 1.674], [0.021, 1.614],
        [0.120, 1.322], [0.213, 1.584], [0.018, 1.937]
    ]

    x_outputs = [
        [-.60, 0.63], [-.30, 0.54], [-.15, 1.03],
        [-.50, 1.33], [-.20, 1.86], [-.55, 1.52],
        [-.50, 1.33], [-.30, 1.80], [-.15, 1.91],
        [-.60, 1.48], [-.30, 1.67], [-.30, 1.61],
        [-.80, 1.32], [-.50, 1.58], [-.30, 1.94]
    ]

    def __init__(self, driver_targets: list, provider_objs: list, orientation: str, bone_names: list):
        print(bone_names)
        x_slopes = [
            Slope(self.x_inputs[idx][0], self.x_inputs[idx][1], self.x_outputs[idx][0], self.x_outputs[idx][1])
            for idx in range(0, 15)
        ]

        self.z_inputs_r = [[radians(v[0]), radians(v[1])] for v in self.z_inputs]
        self.z_inputs_l = [[radians(v[0]), radians(v[1])] for v in self.z_inputs]
        self.z_outputs = [[radians(v[0]), radians(v[1])] for v in self.z_outputs]

        z_slopes_r = [
            Slope(self.z_inputs_r[idx][0], self.z_inputs_r[idx][1], self.z_outputs[idx][0], self.z_outputs[idx][1])
            for idx in range(0, 5)
        ]

        # values have to be mirrored to fit angles
        self.z_outputs = [[i[0] * -1, i[1] * -1] for idx, i in enumerate(self.z_outputs)]
        z_slopes_l = [
            Slope(self.z_inputs_l[idx][0], self.z_inputs_l[idx][1], self.z_outputs[idx][0], self.z_outputs[idx][1])
            for idx in range(0, 5)
        ]

        def get_z_slope(idx):
            if idx not in range(0, 15, 3):
                return Slope(0, 1, 0, 1)

            if orientation == "right":
                return z_slopes_r[int(idx / 3)]
            else:
                return z_slopes_l[int(idx / 3)]
        # todo: set slope properly
        self.pose_drivers = [
            CustomAngleMultiplier(
                driver_targets[idx],
                bone_names[idx],
                x_slopes[idx],
                get_z_slope(idx)
            ) for idx, _ in enumerate(driver_targets)]
        self.pose_drivers += [
            FingerAngleDriver(
                driver_targets[idx],
                provider_objs[idx],
                x_slopes[idx],
                get_z_slope(idx)
            ) for idx, _ in enumerate(driver_targets)]
