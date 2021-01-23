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

import socket
import sys
import cv2
import pickle
import numpy as np
import argparse
import struct
import zlib

from pycoral.adapters.common import input_size
from pycoral.adapters.detect import get_objects
from pycoral.utils.dataset import read_label_file
from pycoral.utils.edgetpu import make_interpreter
from pycoral.utils.edgetpu import run_inference

HOST = ""

if __name__ == "__main__":
    assert sys.version_info >= (3, 6), sys.version_info

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", help="File path of Tflite model.", required=True)
    parser.add_argument("--labels", help="File path of label file.", required=True)
    parser.add_argument(
        "--top_k",
        type=int,
        default=3,
        help="number of classes with highest score to display",
    )
    parser.add_argument(
        "--threshold", type=float, default=0.4, help="class score threshold"
    )
    parser.add_argument("--port", type=int, default=8010, help="server port for images")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="set logging level to debug"
    )

    args = parser.parse_args()

    interpreter = make_interpreter(args.model)
    interpreter.allocate_tensors()
    labels = read_label_file(args.labels)
    inference_size = input_size(interpreter)

    labels = read_label_file(args.labels)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, args.port))
    s.listen(10)
    conn, addr = s.accept()
    data = b""
    payload_size = struct.calcsize(">L")

    while True:
        while len(data) < payload_size:
            data += conn.recv(4096)

        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack(">L", packed_msg_size)[0]

        while len(data) < msg_size:
            data += conn.recv(4096)

        frame_data = data[:msg_size]
        data = data[msg_size:]

        frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
        frame = cv2.imdecode(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = frame.shape

        frame = cv2.resize(frame, inference_size)
        run_inference(interpreter, frame.tobytes())
        objs = get_objects(interpreter, args.threshold)[: args.top_k]

        scale_x, scale_y = width / inference_size[0], height / inference_size[1]

        ret_array = []
        for obj in objs:
            ret = {}

            bbox = obj.bbox.scale(scale_x, scale_y)
            x0, y0 = int(bbox.xmin), int(bbox.ymin)
            x1, y1 = int(bbox.xmax), int(bbox.ymax)

            percent = int(100 * obj.score)
            ret["label"] = labels.get(obj.id, obj.id)
            ret["percent"] = percent
            ret["x0"] = x0
            ret["x1"] = x1
            ret["y0"] = y0
            ret["y1"] = y1
            ret_array.append(ret)

        data_udp = pickle.dumps(ret_array, 0)
        size_udp = len(data_udp)
        conn.sendall(struct.pack(">L", size_udp) + data_udp)
