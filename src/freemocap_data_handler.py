from pathlib import Path
from typing import Union
import numpy as np 

from mediapipe.python.solutions import holistic as mp_holistic



class FreeMoCapDataHandler:
    def __init__(self, session_path:Union[str,Path],  detection_type:str):
        self._session_path = session_path
        self._detection_type = detection_type


        if self._detection_type == 'POSE':
            self.body_frame_landmark_dimension = np.load(self._get_body_npy_path(self._session_path)) / 1000 #convert to meters 
        else:
            raise NotImplementedError(
                f'Only POSE detection type is supported at this time. You provided {self._detection_type}')

        self.mediapipe_body_landmark_names = [
            landmark.name.lower() for landmark in mp_holistic.PoseLandmark
        ]

    @property
    def number_of_frames(self):
        return self.body_frame_landmark_dimension.shape[0]

    def get_frame_data(self, frame_number:int)->list:
        """ Get the data for a specific frame number in the BlendARMocap format - [landmark_index_number, [x, y, z]. """

        landmark_xyz_data = []
        for landmark_number in range(self.body_frame_landmark_dimension.shape[1]):
            landmark_xyz_data.append([landmark_number, self.body_frame_landmark_dimension[frame_number, landmark_number, :]])

        return landmark_xyz_data
    def load_freemocap_data(self)->dict:
        """ Load the data from a freemocap session. """

        freemocap_data_dict = {}
        freemocap_data_dict[self._detection_type] = self._build_freemocap_body_data_dictionary(self.body_frame_landmark_dimension,
                                                              self.mediapipe_body_landmark_names)
        return freemocap_data_dict

    def _build_freemocap_body_data_dictionary(self, body_frame_landmark_dimension, mediapipe_body_landmark_names):
        """
        Build a dictionary of freemocap data where each key is a landmark name containing a dicationary with keys x,y, and z
        """
        body_data_dict = {}

        for landmark_number, landmark_name in enumerate(mediapipe_body_landmark_names):
            body_data_dict[landmark_name] = {}
            body_data_dict[landmark_name]['x'] = body_frame_landmark_dimension[:, landmark_number, 0]
            body_data_dict[landmark_name]['y'] = body_frame_landmark_dimension[:, landmark_number, 1]
            body_data_dict[landmark_name]['z'] = body_frame_landmark_dimension[:, landmark_number, 2]

        return body_data_dict

    def _get_body_npy_path(self, session_path:Union[str,Path]):
        """ Get the path to the body npy file. """
        # TODO - make this work with `alpha` paths and whatnot
        body_npy_path = Path(session_path) / 'DataArrays' / 'mediapipe_body_3d_xyz.npy'

        if not body_npy_path.exists():
            raise FileNotFoundError(f'Could not find body npy file at {body_npy_path}')

        return body_npy_path

