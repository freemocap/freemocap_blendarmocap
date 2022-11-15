'''
Copyright (C) cgtinker, cgtinker.com, hello@cgtinker.com

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import bpy
from pathlib import Path
from ..utils import objects
from ...cgt_naming import COLLECTIONS
from ...freemocap_data_handler import FreeMoCapDataHandler


class UI_CGT_transfer_anim_button(bpy.types.Operator):
    bl_label = "Transfer Animation"
    bl_idname = "button.cgt_transfer_animation_button"
    bl_description = "Transfer driver animation to cgt_rig"

    @classmethod
    def poll(cls, context):
        return context.mode in {'OBJECT'}

    def execute(self, context):
        from ..cgt_rig import rigify_pose, rigify_face, rigify_fingers

        col_mapping = {
            COLLECTIONS.hands: rigify_fingers.RigifyHands,
            COLLECTIONS.face:  rigify_face.RigifyFace,
            COLLECTIONS.pose:  rigify_pose.RigifyPose
        }

        user = bpy.context.scene.m_cgtinker_mediapipe

        selected_driver_collection = user.selected_driver_collection
        selected_armature = user.selected_rig.name_full

        print(f"TRYING TO TRANSFER ANIMATION DATA FROM {selected_driver_collection} TO {selected_armature}")

        driver_collections = objects.get_child_collections(selected_driver_collection)
        for col in driver_collections:
            armature = objects.get_armature(selected_armature)
            driver_objects = objects.get_objects_from_collection(col)
            if driver_objects is not None:
                col_mapping[col](armature, driver_objects)

        # input_manager.transfer_animation()
        return {'FINISHED'}


class UI_CGT_toggle_drivers_button(bpy.types.Operator):
    bl_label = "Toggle Drivers"
    bl_idname = "button.cgt_toggle_drivers_button"
    bl_description = "Toggle drivers to improve performance while motion capturing"
    # TODO: IMPLEMENT PROPER WAY TO TOGGLE

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        user = bpy.context.scene.m_cgtinker_mediapipe  # noqa
        user.toggle_drivers_bool = not user.toggle_drivers_bool
        print("toggled", user.toggle_drivers_bool)

        driver_collections = objects.get_child_collections('CGT_DRIVERS')
        objs = objects.get_objects_from_collection('CGT_DRIVERS')
        print(objs)
        return {'FINISHED'}


class WM_CGT_modal_detection_operator(bpy.types.Operator):
    bl_label = "Feature Detection Operator"
    bl_idname = "wm.cgt_feature_detection_operator"
    bl_description = "Detect solution in Stream."

    _timer = None
    detection_handler = None
    user = None

    def execute(self, context):
        """ Runs movie or stream detection depending on user input. """
        self.user = context.scene.m_cgtinker_mediapipe  # noqa
        print('Executing - WM_CGT_modal_detection_operator')

        # hacky way to check if operator is running
        if self.user.detection_operator_running is True:
            self.user.detection_operator_running = False
            return {'FINISHED'}
        else:
            self.user.detection_operator_running = True

        # create a detection handler
        from ...main import DetectionHandler
        detection_type = self.user.enum_detection_type
        self.detection_handler = DetectionHandler(detection_type, "BPY")

        # initialize detector using user inputs
        frame_start = bpy.context.scene.frame_start
        if self.user.detection_input_type == 'movie':
            mov_path = bpy.path.abspath(self.user.mov_data_path)
            print("Path to mov:", mov_path)
            if not Path(mov_path).is_file():
                print("GIVEN PATH IS NOT VALID")
                self.user.detection_operator_running = False
                return {'FINISHED'}
            self.detection_handler.init_detector(str(mov_path), "sd", 0, frame_start, 1, 1)
        elif self.user.detection_input_type == 'stream':
            camera_index = self.user.webcam_input_device
            dimensions = self.user.enum_stream_dim
            backend = int(self.user.enum_stream_type)
            key_step = self.user.key_frame_step
            self.detection_handler.init_detector(camera_index, dimensions, backend, frame_start, key_step, 0)
        elif self.user.detection_input_type == 'freemocap':
            freemocap_session_path = Path(bpy.path.abspath(self.user.freemocap_session_path))
            if not Path(freemocap_session_path).is_dir():
                print(f"No directory found at: {freemocap_session_path}")
                self.user.detection_operator_running = False
                return {'FINISHED'}
            self.freemocap_data_handler = FreeMoCapDataHandler(session_path = freemocap_session_path, detection_type=detection_type)

            self.detection_handler.init_detector(input_type=2)

        # initialize the bridge from the detector to blender
        self.detection_handler.init_bridge()

        # add a timer property and start running
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.001, window=context.window)
        context.window_manager.modal_handler_add(self)

        print(f"RUNNING {detection_type} DETECTION AS MODAL")
        return {'RUNNING_MODAL'}

    @classmethod
    def poll(cls, context):
        return context.mode in {'OBJECT', 'POSE'}

    def modal(self, context, event):
        """ Run detection as modal operation, finish with 'Q', 'ESC' or 'RIGHT MOUSE'. """
        if event.type == "TIMER":
            if self.user.detection_input_type == 'freemocap':
                # spoofing `BlendAR`'s frame-loop based loading methods.
                #  Prolly slower than loading the `empty` data directly,
                #  but easier to interface with the existing machinery
                # that @cgtinker put together this way :D

                current_frame_number = self.detection_handler.detector.frame
                print(f"Loading `freemocap` data for frame {current_frame_number} of {self.freemocap_data_handler.number_of_frames}")
                current_frame_number = self.detection_handler.detector.frame

                landmark_xyz_data_for_this_frame = self.freemocap_data_handler.get_frame_data(current_frame_number)
                self.detection_handler.detector.listener.data = landmark_xyz_data_for_this_frame
                self.detection_handler.detector.update_listeners()

                self.detection_handler.detector.frame += self.detection_handler.detector.key_step

                running = not(self.detection_handler.detector.frame >= self.freemocap_data_handler.number_of_frames)



            else:
                running = self.detection_handler.detector.image_detection()

            if running:
                return {'PASS_THROUGH'}
            else:
                return self.cancel(context)

        if event.type in {'Q', 'ESC', 'RIGHT_MOUSE'} or self.user.detection_operator_running is False:
            return self.cancel(context)

        return {'PASS_THROUGH'}

    def cancel(self, context):
        """ Upon finishing detection clear the handlers. """
        bpy.context.scene.m_cgtinker_mediapipe.detection_operator_running = False # noqa
        del self.detection_handler
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        print("FINISHED DETECTION")
        return {'FINISHED'}


## FreeMoCap Stuff

class WM_FMC_bind_freemocap_data_to_skeleton(bpy.types.Operator):
    bl_label = "Bind `freemocap` to skeleton    "
    bl_idname = "wm.fmc_bind_freemocap_data_to_skeleton"
    bl_description = "Bind freemocap animation data to a rigify skeleton (rig)"

    _timer = None
    detection_handler = None
    user = None

    def execute(self, context):
        print("Executing `bind freemocap data to skeleton` operator")
        # load rigify human metarig
        #%% create metarig
        bpy.ops.object.armature_human_metarig_add()
        
        # generate rig
        bpy.ops.pose.rigify_generate()
        rigify_rig = bpy.context.active_object

        # bind Hands drivers
        bpy.context.scene.m_cgtinker_mediapipe.selected_driver_collection = "cgt_HANDS"
        bpy.context.scene.m_cgtinker_mediapipe.selected_rig = rigify_rig               
        bpy.ops.button.cgt_transfer_animation_button() #press button "Transfer Animation"

        # bind Face drivers
        bpy.context.scene.m_cgtinker_mediapipe.selected_driver_collection = "cgt_FACE"        
        bpy.ops.button.cgt_transfer_animation_button() #press button "Transfer Animation"

        # bind Body drivers (bind legs)
        bpy.context.scene.m_cgtinker_mediapipe.selected_driver_collection = "cgt_POSE"        
        bpy.context.scene.m_cgtinker_mediapipe.experimental_feature_bool = True # 'transfer animation to legs'
        bpy.ops.button.cgt_transfer_animation_button() #press button "Transfer Animation"
        bpy.context.object.data.layers[31] = True

        # #copy location - rig & hips_center
        # constraint = rigify_rig.constraints.new(type="COPY_LOCATION")
        # constraint.target = bpy.data.objects['cgt_hip_center']

        # # hands - disable copy rotations on IK rig
        # bpy.context.object.pose.bones["hand_ik.R"].constraints["Copy Rotation"].enabled = False
        # bpy.context.object.pose.bones["hand_ik.L"].constraints["Copy Rotation"].enabled = False


        return {'FINISHED'}




class WM_FMC_load_synchronized_videos(bpy.types.Operator):
    
    bl_label = "load synchronized freemocap videos"
    bl_idname = "wm.fmc_load_synchronized_videos"
    bl_description = "Load synchronized freemocap videos using 'Images as Planes' addon"

    user=None
    def execute(self, context):
        print("Running `WM_FMC_load_synchronized_videos` operator")
        self.user = context.scene.m_cgtinker_mediapipe  # noqa
        freemocap_session_path = Path(self.user.freemocap_session_path)

        addon_utils.enable("io_import_images_as_planes")

        try:
            print('loading videos as planes...')
            vidFolderPath = freemocap_session_path / 'SyncedVideos'
            #%% create world origin

            bpy.ops.object.empty_add(type='ARROWS')
            world_origin_axes = bpy.context.active_object
            world_origin_axes.name = 'world_origin' #will stay at origin

            world_origin = bpy.data.objects['world_origin']

            number_of_videos = len(list(vidFolderPath.glob('*.mp4')))

            vid_location_scale = 4


            for vid_number, thisVidPath, in enumerate(vidFolderPath.glob('*.mp4')):
                print(thisVidPath)
                # use 'images as planes' add on to load in the video files as planes
                bpy.ops.import_image.to_plane(files=[{"name":thisVidPath.name}], directory=str(thisVidPath.parent), shader='EMISSION', )
                this_vid_as_plane = bpy.context.active_object
                this_vid_as_plane.name = 'vid_' + str(vid_number)
                
                
                vid_x = (vid_number - number_of_videos/2) * vid_location_scale
                
                this_vid_as_plane.location = [vid_x, vid_location_scale, vid_location_scale]
                this_vid_as_plane.rotation_euler = [np.pi/2, 0, 0]
                this_vid_as_plane.scale = [vid_location_scale*1.5]*3
                this_vid_as_plane.parent = world_origin 
                # create a light
                # bpy.ops.object.light_add(type='POINT', radius=1, align='WORLD')
        except Exception as e:
            print('Failed to load videos to Blender scene')
            print(e)

    
        return {'FINISHED'}
