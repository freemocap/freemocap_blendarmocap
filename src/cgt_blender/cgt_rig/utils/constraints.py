
def copy_rotation(constraint, target, *args):
    constraint.target = target
    constraint.euler_order = 'XYZ'
    constraint.influence = 1
    constraint.mix_mode = 'ADD'
    constraint.owner_space = 'LOCAL'


def copy_rotation_world_space(bone, target, *args):
    constraint = bone.constraints.new(
        type="COPY_ROTATION"
    )
    constraint.target = target
    constraint.euler_order = 'XYZ'
    constraint.influence = 1
    constraint.mix_mode = 'ADD'
    constraint.owner_space = 'WORLD'


def copy_location(constraint, target, *args):
    constraint.target = target
    constraint.influence = 1
    constraint.owner_space = 'POSE'


def copy_location_offset(bone, target, *args):
    constraint = bone.constraints.new(
        type="COPY_LOCATION"
    )
    constraint.target = target
    constraint.influence = 1
    constraint.use_offset = True
    constraint.owner_space = 'POSE'


def copy_location_world(bone, target, *args):
    constraint = bone.constraints.new(
        type="COPY_LOCATION"
    )
    constraint.target = target
    constraint.influence = 1
    constraint.owner_space = 'WORLD'


def damped_track(constraint, target, *args):
    constraint.target = target
    constraint.influence = 1
    constraint.track_axis = 'TRACK_Y'
    constraint.owner_space = 'POSE'


def track_to(constraint, target, *args):
    constraint.target = target
    constraint.influence = 1


constraint_mapping = {
        "CAMERA_SOLVER":        0,
        "FOLLOW_TRACK":         1,
        "OBJECT_SOLVER":        2,
        "COPY_LOCATION":        copy_location,
        "COPY_LOCATION_OFFSET": copy_location_offset,
        "COPY_LOCATION_WORLD":  copy_location_world,
        "COPY_ROTATION":        copy_rotation,
        "COPY_ROTATION_WORLD":  copy_rotation_world_space,
        "COPY_SCALE":           5,
        "COPY_TRANSFORMS":      6,
        "LIMIT_DISTANCE":       7,
        "LIMIT_LOCATION":       8,
        "LIMIT_ROTATION":       9,
        "LIMIT_SCALE":          10,
        "MAINTAIN_VOLUME":      11,
        "TRANSFORM":            12,
        "TRANSFORM_CACHE":      13,
        "CLAMP_TO":             14,
        "DAMPED_TRACK":         damped_track,
        "IK":                   16,
        "LOCKED_TRACK":         17,
        "SPLINE_IK":            18,
        "STRETCH_TO":           19,
        "TRACK_TO":             20,
        "ACTION":               21,
        "ARMATURE":             22,
        "CHILD_OF":             23,
        "FLOOR":                24,
        "FOLLOW_PATH":          25,
        "PIVOT":                26,
        "SHRINKWRAP":           27,
    }


def add_constraint(bone, target, constraint):
    m_constraints = [c for c in bone.constraints]
    # overwriting constraint by
    # removing previously added constraints if types match
    for c in m_constraints:
        # setup correct syntax for comparison
        constraint_name = c.name
        if "_WORLD" in constraint_name:
            constraint_name.remove("_WORLD")
        elif "_OFFSET" in constraint_name:
            constraint_name.remove("_OFFSET", constraint_name)
        constraint_name = constraint_name.replace(" ", "_")
        constraint_name = constraint_name.upper()
        # remove match
        if constraint_name == constraint:
            bone.constraints.remove(c)
    try:
        # adding a new constraint
        m_constraint = bone.constraints.new(
            type=constraint
        )
        constraint_mapping[constraint](m_constraint, target)
    except TypeError or KeyError:
        # call custom method with bone
        constraint_mapping[constraint](bone, target)