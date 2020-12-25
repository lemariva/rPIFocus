"""
Copyright (C) 2020 Mauro Riva

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import cv2
import time
import numpy as np
import pickle
import struct

encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]


def classify_objects(tpu_socket, frame, obj_detector):
    """Detect objects on the provided camera frame and
    return its coordinates and label. To do that, it sends
    the frame via UDP to the object detector service.

    Args:
        tpu_socket ([socket.socket]): socket to connect to the service
        frame ([numpy.ndarray]): camera frame
        obj_detector ([list]): list to return the label and coordinates 
                               of detected objects
    """
    # encode the frame in JPEG format
    flag, frame_tmp = cv2.imencode(".jpg", frame, encode_param)

    data = b""
    payload_size = struct.calcsize(">L")

    # send image to classify
    data_udp = pickle.dumps(frame_tmp, 0)
    size_udp = len(data_udp)
    tpu_socket.sendall(struct.pack(">L", size_udp) + data_udp)

    # receive labels and coordinates
    while len(data) < payload_size:
        data += tpu_socket.recv(4096)

    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack(">L", packed_msg_size)[0]

    while len(data) < msg_size:
        data += tpu_socket.recv(4096)

    labels_data = data[:msg_size]
    data = data[msg_size:]

    new_objs = pickle.loads(labels_data, fix_imports=True, encoding="bytes")

    for obj in new_objs:
        obj_temp = next(
            (
                (idx, item)
                for idx, item in enumerate(obj_detector)
                if item["label"] == obj["label"]
            ),
            False,
        )
        if not obj_temp:
            obj["selected"] = False
            obj["added"] = time.time_ns()
            obj_detector.append(obj)
        else:
            obj_detector[obj_temp[0]]["x0"] = obj["x0"]
            obj_detector[obj_temp[0]]["x1"] = obj["x1"]
            obj_detector[obj_temp[0]]["y0"] = obj["y0"]
            obj_detector[obj_temp[0]]["y1"] = obj["y1"]
            obj_detector[obj_temp[0]]["added"] = time.time_ns()

    for idx, obj in enumerate(obj_detector):
        if obj["added"] < time.time_ns() - 2e9:
            obj_detector.pop(idx)


def check_object_selected(focus_config, obj_detector):
    """Mark an object as selected if the coordinates of
    the clic are inside the object rectangle.

    Args:
        focus_config ([json]): coodinates of the clic
        obj_detector ([list]): objects detected using classify_objects(...)
    """
    for idx, obj in enumerate(obj_detector):
        if (
            obj["x0"] < focus_config["frame_x"]
            and obj["x1"] > focus_config["frame_x"]
            and obj["y0"] < focus_config["frame_y"]
            and obj["y1"] > focus_config["frame_y"]
        ):

            obj_detector[idx]["selected"] = not obj_detector[idx]["selected"]
