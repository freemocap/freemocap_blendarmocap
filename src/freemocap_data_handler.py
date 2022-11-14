from pathlib import Path
from typing import Union
import numpy as np 

from mediapipe.python.solutions import holistic as mp_holistic
mediapipe_body_landmark_names = [
    landmark.name.lower() for landmark in mp_holistic.PoseLandmark
]


class FreeMoCapDataHandler:
    def load_freemocap_data(self, session_path: Union[str, Path], detection_type: str)->dict:
        """ Load the data from a freemocap session. """
        if detection_type == 'POSE':
            body_frame_marker_dimension = np.load(self._get_body_npy_path(session_path))
        else:
            raise NotImplementedError(f'Only POSE detection type is supported at this time. You provided {detection_type}')

        body_data_dict = self._build_freemocap_body_data_dictionary(body_frame_marker_dimension,
                                                              mediapipe_body_landmark_names)
        return body_data_dict

    def _build_freemocap_body_data_dictionary(self, body_frame_marker_dimension, mediapipe_body_landmark_names):
        """
        Build a dictionary of freemocap data where each key is a landmark name containing a dicationary with keys x,y, and z
        """
        body_data_dict = {}

        for landmark_number, landmark_name in enumerate(mediapipe_body_landmark_names):
            body_data_dict[landmark_name] = {}
            body_data_dict[landmark_name]['x'] = body_frame_marker_dimension[:, landmark_number, 0]
            body_data_dict[landmark_name]['y'] = body_frame_marker_dimension[:, landmark_number, 1]
            body_data_dict[landmark_name]['z'] = body_frame_marker_dimension[:, landmark_number, 2]

        return body_data_dict

    def _get_body_npy_path(self, session_path:Union[str,Path]):
        """ Get the path to the body npy file. """
        # TODO - make this work with `alpha` paths and whatnot
        body_npy_path = Path(session_path) / 'DataArrays' / 'mediapipe_body_3d_xyz.npy'

        if not body_npy_path.exists():
            raise FileNotFoundError(f'Could not find body npy file at {body_npy_path}')

        return body_npy_path

