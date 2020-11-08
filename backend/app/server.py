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

import os
import sys
import argparse
import logging
import cv2
import socket
import time
import threading
import requests
import pickle
import struct
import numpy as np
from flask import Flask, render_template, Response, request, jsonify
from imutils.video import WebcamVideoStream
from imutils.video import FPS
from datetime import datetime

from os import listdir, makedirs, replace, remove
from os.path import isfile, join

from blur_detection import dwt
from blur_detection import estimate_blur

m5stack_host = None

app = Flask(__name__)
vc = WebcamVideoStream(src=0).start()
fps = FPS().start()

frame = vc.read()
frame_cut = frame

_, frame_jpg = cv2.imencode(".JPEG", frame)
frame_tmp = frame_jpg

focus_phase = 0
focus_break = True
focus_mode = 0
score_history = []

tpu_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
photo_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

obj_detector = []
object_selected = []
tpu_api_detected = False
take_photo_detected = False

streaming = []

focus_config = {
    "focus_type": "box",
    "frame_x": 0,
    "frame_y": 0,
    "frame_w": len(frame[0]),
    "frame_h": len(frame),
}

color_selected = (109, 41, 3)
color_normal = (239, 218, 195)

thread = threading.Thread()
encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

# ############################################
# FOCUS SEARCH
# Some parts from this section were taken from:
# https://github.com/sourtin/igem15-sw/blob/master/img_processing/identificationTesting/autofocus.py
# ############################################


def getfocus(frame_focus):
    if frame_focus.ndim == 3:
        frame_focus = cv2.cvtColor(frame_focus, cv2.COLOR_BGR2GRAY)

    score = dwt.low_res_score(frame_focus)
    # _, score, _ = estimate_blur(frame_focus, threshold=100)
    return score


def gaussian_fitting(z, f):
    """
    Fit the autofocus function data according to the equation 16.5 in the
    textbook : 'Microscope Image Processing' by Q.Wu et al'
    z_max = gaussian_fitting((z1, z2, z3), (f1, f2 f3))
    where z1, z2 , z3 are points where the autofocus functions
    values f1, f2, f3 are measured
    """
    z1 = z[0]
    z2 = z[1]
    z3 = z[2]
    f1 = f[0]
    f2 = f[1]
    f3 = f[2]

    B = (np.log(f2) - np.log(f1)) / (np.log(f3) - np.log(f2))

    if (z3 - z2) == (z2 - z1):
        return 0.5 * (B * (z3 + z2) - (z2 + z1)) / (B - 1)
    else:
        return (
            0.5
            * (B * (z3 ** 2 - z2 ** 2) - (z2 ** 2 - z1 ** 2))
            / (B * (z3 - z2) - (z2 - z1))
        )


def parabola_fitting(z, f):
    """
    Fit the autofocus function data according to the equation 16.5 in the
    textbook : 'Microscope Image Processing' by Q.Wu et al'
    parabola_fitting((z1, z2, z3), (f1, f2 f3))
    where z1, z2 , z3 are points where the autofocus functions
    values f1, f2, f3 are measured
    """
    z1 = z[0]
    z2 = z[1]
    z3 = z[2]
    f1 = f[0]
    f2 = f[1]
    f3 = f[2]

    E = (f2 - f1) / (f3 - f2)

    if (z3 - z2) == (z2 - z1):
        return 0.5 * (E * (z3 + z2) - (z2 + z1)) / (E - 1)
    else:
        return (
            0.5
            * (E * (z3 ** 2 - z2 ** 2) - (z2 ** 2 - z1 ** 2))
            / (E * (z3 - z2) - (z2 - z1))
        )


def hill_climbing(step_size=300):
    """Climb to a higher place, find a smaller interval containing focus position
    (z1, z2, z3), (f1, f2, f3) = hill_climbing(f)
    """
    global frame_cut
    mtype = "focus"

    f1 = getfocus(frame_cut)
    z1 = 0
    f2 = move_focus_motor(step_size, True)
    z2 = step_size
    score_history.append(f1)
    score_history.append(f2)
    iterations = 0

    while True:

        if f2 > f1:
            f0 = f1
            f1 = f2
            f2 = move_focus_motor(step_size, True)
            score_history.append(f2)
            z2 += step_size
            iterations += 1

        elif iterations <= 1:
            logging.info("Found a dip, assuming it is wrong and continuing")
            f0 = f1
            f1 = f2
            f2 = move_focus_motor(step_size, True)
            score_history.append(f2)
            z2 += step_size
            iterations += 1

        elif iterations <= 2:
            logging.info("Changing search direction")
            return hill_climbing(-step_size / 2)

        else:
            logging.info("Finised hill climbing")
            return ((z2 - 2 * step_size - 2, z2 - step_size, z2), (f0, f1, f2))


def fibonacci_search(interval):
    """Carry out the fibonacci search method according* to the paper:
    'Autofocusing for tissue microscopy' by T.T.E.Yeo et al

    (a,b,x) = fibonacci_search(interval)
    interval = (a, b)
    f is the microscope control class
    """
    global frame_cut
    phi = 0.5 * (1 + 5 ** 0.5)  # Golden ratio

    def fibs(n=None):
        """ A generator, (thanks to W.J.Earley) that returns the fibonacci series """
        a, b = 0, 1
        yield 0
        yield 1
        if n is not None:
            for _ in range(1, n):
                b = b + a
                a = b - a
                yield (b)
        else:
            while True:
                b = b + a
                a = b - a
                yield (b)

    def smallfib(m):
        """ Return N such that fib(N) >= m """
        n = 0
        for fib in fibs(m):
            if fib >= m:
                return n
            n = n + 1

    def fib(n):
        """ Evaluate the n'th fibonacci number """
        return (phi ** n - (-phi) ** (-n)) / (5 ** 0.5)

    a = interval[0]
    b = interval[1]
    c = np.mean((a, b))  # current position of z is inbetween the interval
    N = smallfib(int(b - a))
    delta = (fib(N - 2) / fib(N)) * (b - a)

    x1 = a + delta
    x2 = b - delta

    y1 = move_focus_motor(x1 - c, True)
    y2 = move_focus_motor(x2 - x1, True)

    score_history.append(y1)
    score_history.append(y2)

    older_pos = 0
    old_pos = x1
    curr_pos = x2
    iterations = 1

    for n in range(N - 1, 1, -1):
        if iterations > 10:  # Only 5 iterations for speed
            break
        elif y1 < y2:
            a = x1
            x1 = x2
            y1 = y2
            x2 = b - (fib(n - 2) / fib(n)) * (b - a)
            y2 = move_focus_motor(x2 - curr_pos, True)
            score_history.append(y2)

            older_pos = old_pos
            old_pose = curr_pos
            curr_pos = x2
        else:
            b = x2
            x2 = x1
            y2 = y1
            x1 = a + (fib(n - 2) / fib(n)) * (b - a)
            y1 = move_focus_motor(x1 - curr_pos, True)
            score_history.append(y1)
            older_pos = old_pos
            old_pos = curr_pos
            curr_pos = x1
        iterations += 1

    if y1 > y2:
        return (a, b, x1, older_pos, old_pos, curr_pos)

    else:
        return (a, b, x2, older_pos, old_pos, curr_pos)


# ############################################
# FOCUS TYPE
# ############################################


def autofocus():
    global frame_cut, focus_phase, focus_break, score_history
    score_history = []

    motor_status = get_motor_status("focus")
    max_steps = motor_status["max_steps"]
    actual_position = motor_status["position"]

    # focus_phase 0 -> away from corners
    if actual_position < 200 or actual_position > max_steps - 200:
        logging.info("focus_phase 0")
        step_size = max_steps / 2 - actual_position
        logging.info(
            f"max_steps: {max_steps} actual_position: {actual_position} move: {step_size}"
        )
        move_focus_motor(max_steps / 2 - actual_position)

    logging.info("Starting hill_climbing search")
    pos, scores = hill_climbing()
    if focus_break:
        return

    logging.info("Gaussian Fitting")
    mu = gaussian_fitting(pos, scores)
    interval = (mu - 400, mu + 400)
    step_size = -pos[2] + mu
    logging.info(
        f"interval: {interval} actual_position: {actual_position} move: {step_size}"
    )
    move_focus_motor(step_size)
    if focus_break:
        return

    logging.info("Starting fibonacci_search search")
    (a, b, x, z1, z3, z2) = fibonacci_search(interval)
    if focus_break:
        return

    logging.info("Starting parabola_fitting search")
    mu = parabola_fitting(
        (z1, z2, z3), (-score_history[-2], -score_history[-1], -score_history[-3])
    )
    step_size = -x + mu
    move_focus_motor(step_size)
    logging.info(
        f"max_steps: {max_steps} actual_position: {actual_position} move: {step_size}"
    )

    score_history.append(getfocus(frame_cut))
    logging.info(f"score_x: {score_history[-1]}")


def livefocus():
    global focus_break
    motor_status = get_motor_status("focus")
    max_steps = motor_status["max_steps"]

    autofocus()

    mem = 2
    margin = 50
    score_old = np.zeros(mem)
    step_size = 50

    mem_count = mem
    mdir = 1

    while mem_count > 0 and not focus_break:  # fill buffer
        mem_count = mem_count - 1
        score_x = move_focus_motor(15, True)
        score_old = np.append(score_old, score_x)
        score_old = np.delete(score_old, 0)
        logging.info(f"score_x: {score_x}")

    mdir_old = mdir
    swing = 0

    while not focus_break:
        motor_status = get_motor_status("focus")
        max_steps = motor_status["max_steps"]
        actual_position = motor_status["position"]

        score_x = move_focus_motor(mdir * step_size, True)

        logging.info(f"score_x: {score_x}")

        score_old = np.append(score_old, score_x)
        score_old = np.delete(score_old, 0)

        gradient = np.sum(np.gradient(score_old, 1)) / mem
        mdir = 1 if gradient < 0 else -1

        # avoid swing on maximal
        if mdir != mdir_old:
            swing = swing + 1
        else:
            swing = 0

        logging.info(
            f"gradient: {gradient} score_old: {score_old} swing: {swing} actual_position: {actual_position} max_steps {max_steps}"
        )

        mdir_old = mdir
        # reset position limit reached
        if max_steps - actual_position < margin:
            break
        if actual_position < margin:
            break


# ############################################
# LIVE PREVIEW
# ############################################


def gen():
    """Video streaming generator function."""
    global frame_jpg
    while True:
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_jpg.tobytes() + b"\r\n"
        )


def restart_live_preview(task_id):
    global streaming, vc
    request_check = args.photo + task_id
    state = requests.get(request_check).json()["state"]
    while state != "SUCCESS":
        state = requests.get(request_check).json()["state"]
        time.sleep(0.1)

    logging.info("Starting live view after taking photos!")
    time.sleep(0.5)
    vc = WebcamVideoStream(src=0).start()
    streaming = threading.Thread(target=video_streaming)
    streaming.start()


def video_streaming():
    global frame, frame_cut, frame_jpg, frame_tmp, focus_config, obj_detector, streaming_stop
    t = threading.currentThread()

    while getattr(t, "do_run", True):
        frame = vc.read()

        if focus_config["focus_type"] == "image":
            _, frame_jpg = cv2.imencode(".jpg", frame, encode_param)

            frame_cut = frame

        elif focus_config["focus_type"] == "box":
            start_point = (focus_config["frame_x"], focus_config["frame_y"])
            end_point = (
                focus_config["frame_x"] + focus_config["frame_w"],
                focus_config["frame_y"] + focus_config["frame_h"],
            )

            color = color_selected
            thickness = 2

            frame_cut = frame[
                focus_config["frame_y"] : focus_config["frame_y"]
                + focus_config["frame_h"],
                focus_config["frame_x"] : focus_config["frame_x"]
                + focus_config["frame_w"],
            ]

            frame_draw = cv2.rectangle(frame, start_point, end_point, color, thickness)
            _, frame_jpg = cv2.imencode(".jpg", frame_draw, encode_param)

        elif focus_config["focus_type"] == "object":
            _, frame_tmp = cv2.imencode(".jpg", frame, encode_param)

            if focus_break:
                classify_objects()

            cut_size = [len(frame), 0, len(frame[0]), 0]

            for obj in obj_detector:
                thickness = 2
                if obj["selected"]:
                    color = color_selected
                else:
                    color = color_normal

                frame_draw = cv2.rectangle(
                    frame,
                    (obj["x0"], obj["y0"]),
                    (obj["x1"], obj["y1"]),
                    color,
                    thickness,
                )

                if obj["x0"] < cut_size[0]:
                    cut_size[0] = obj["x0"]
                if obj["x1"] > cut_size[1]:
                    cut_size[1] = obj["x1"]
                if obj["y0"] < cut_size[2]:
                    cut_size[2] = obj["y0"]
                if obj["y1"] > cut_size[3]:
                    cut_size[3] = obj["y1"]

            if len(obj_detector) == 0:
                frame_draw = frame
                frame_cut = frame
            else:
                frame_cut = frame[cut_size[2] : cut_size[3], cut_size[0] : cut_size[1]]

            _, frame_jpg = cv2.imencode(".jpg", frame_draw, encode_param)

        fps.update()


# ############################################
# MOTORS
# ############################################


def set_move_motor(mtype, step, mdir):
    try:
        url = f"http://{m5stack_host}/move/{mtype}/{step}/{mdir}"
        r = requests.get(url)
        done = True if r.json()["status"] == "true" else False
        position = r.json()["position"]
    except:
        done = False
        position = 0

    return done, position


def move_focus_motor(step_size, take_photo=False):
    global frame_cut
    mtype = "focus"
    mdir = 0 if step_size < 0 else 1

    while not set_move_motor(mtype, abs(int(step_size)), mdir):
        pass

    if take_photo:
        time.sleep(0.1)
        return getfocus(frame_cut)


def get_motor_status(mtype):
    url = f"http://{m5stack_host}/status/{mtype}"
    status = requests.get(url).json()
    return status


# ############################################
# OBJECT DETECTION
# ############################################


def classify_objects():
    global frame_tmp, obj_detector

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


def check_object_selected():
    global obj_detector
    for idx, obj in enumerate(obj_detector):
        if (
            obj["x0"] < focus_config["frame_x"]
            and obj["x1"] > focus_config["frame_x"]
            and obj["y0"] < focus_config["frame_y"]
            and obj["y1"] > focus_config["frame_y"]
        ):

            obj_detector[idx]["selected"] = not obj_detector[idx]["selected"]


# ############################################
# REST API
# ############################################


@app.route("/")
def index():
    """Video streaming ."""
    return render_template("index.html")


@app.route("/api/video_feed")
def api_video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/api/frame")
def api_focus_frame():
    global focus_config
    if (
        request.args.get("x") is not None
        and request.args.get("y") is not None
        and request.args.get("w") is not None
        and request.args.get("h") is not None
        and request.args.get("type") is not None
    ):
        focus_config["focus_type"] = request.args.get("type")
        focus_config["frame_x"] = int(request.args.get("x"))
        focus_config["frame_y"] = int(request.args.get("y"))
        focus_config["frame_w"] = int(request.args.get("w"))
        focus_config["frame_h"] = int(request.args.get("h"))

    data = {
        "type": focus_config["focus_type"],
        "frame_x": focus_config["frame_x"],
        "frame_y": focus_config["frame_y"],
        "frame_w": focus_config["frame_w"],
        "frame_h": focus_config["frame_h"],
    }

    return jsonify(data), 200


@app.route("/api/object")
def api_focus_object():
    global focus_config, obj_detector

    if (
        request.args.get("x") is not None
        and request.args.get("y") is not None
        and request.args.get("type") is not None
    ):
        focus_config["focus_type"] = request.args.get("type")
        focus_config["frame_x"] = int(request.args.get("x"))
        focus_config["frame_y"] = int(request.args.get("y"))

    check_object_selected()

    objects = ""
    for obj in obj_detector:
        if obj["selected"]:
            objects = objects + obj["label"] + ", "

    data = {
        "objects": objects,
    }

    return jsonify(data), 200


@app.route("/api/autofocus")
def api_autofocus():
    global thread, focus_mode, focus_phase, focus_break
    autotype = ""
    if request.args.get("mode") is not None:
        if focus_phase != 0 and focus_mode != int(request.args.get("mode")):
            focus_break = True

        if focus_mode == 0:  # stop focusing
            focus_break = True

        focus_mode = int(request.args.get("mode"))
        if focus_mode == 2:  # autofocus
            if not thread.is_alive():
                focus_break = False
                autotype = "autofocus"
                thread = threading.Thread(target=autofocus)
                thread.daemon = True
                thread.start()
        elif focus_mode == 3:  # livefocus
            if not thread.is_alive():
                focus_break = False
                autotype = "livefocus"
                thread = threading.Thread(target=livefocus)
                thread.daemon = True
                thread.start()

    data = {
        "mode": focus_mode,
        "thread_name": str(thread.name),
        "autotype": autotype,
        "focus_phase": focus_phase,
        "started": True,
    }

    return jsonify(data), 200


@app.route("/api/status")
def api_app_status():

    aperture_status = get_motor_status("aperture")

    ma_pos = aperture_status["position"]
    ma_calibrated = aperture_status["calibrated"]
    ma_max_steps = aperture_status["max_steps"]

    focus_status = get_motor_status("focus")

    mf_pos = focus_status["position"]
    mf_calibrated = focus_status["calibrated"]
    mf_max_steps = focus_status["max_steps"]

    data = {
        "ma_pos": ma_pos,
        "ma_calibrated": ma_calibrated,
        "ma_max_steps": ma_max_steps,
        "mf_pos": mf_pos,
        "mf_calibrated": mf_calibrated,
        "mf_max_steps": mf_max_steps,
        "tpu_api": tpu_api_detected,
    }

    return jsonify(data), 200


@app.route("/api/move")
def api_set_move_motor():
    if (
        request.args.get("mtype") is not None
        and request.args.get("position") is not None
    ):
        mtype = request.args.get("mtype")
        position = int(request.args.get("position"))

        motor_status = get_motor_status(mtype)
        max_steps = motor_status["max_steps"]
        actual_position = motor_status["position"]

        if position < 0:
            position = 0
        if position > max_steps:
            position = max_steps

        step_size = int(position - actual_position)
        mdir = 0 if step_size < 0 else 1

        logging.info(f"mtype: {mtype} step_size: {step_size} mdir: {mdir}")

        motor_status = set_move_motor(mtype, abs(step_size), mdir)

        return jsonify(motor_status), 200


@app.route("/api/takephoto")
def api_take_photo():
    global streaming, vc
    now = datetime.now()
    hash = now.strftime("%Y%m%d_%H%M%S")
    data = {"filename": hash + "_image"}
    if (
        request.args.get("ev") is not None
        and request.args.get("ex") is not None
        and request.args.get("aeb") is not None
        and request.args.get("iso") is not None
    ):
        # stop live view
        logging.info("Stopping live view to take photos!")
        streaming.do_run = False
        streaming.join()
        time.sleep(0.5)
        vc.stream.release()
        time.sleep(0.5)

        request_link = (
            args.photo
            + "/api/takephoto?foldername={0}&aeb={1}&ev={2}&ex={3}&iso={4}".format(
                hash + "_image",
                request.args.get("aeb"),
                request.args.get("ev"),
                request.args.get("ex"),
                request.args.get("iso"),
            )
        )


        data = requests.get(request_link)
        task_id = data.json()["task_id"]

        photo_check = threading.Thread(target=restart_live_preview, args=(task_id,))
        photo_check.start()

    return jsonify(data.json()), 200

@app.route("/api/getphotos")
def api_get_photos():
    pgal = args.pgallery
    onlyfiles = [f for f in listdir(pgal) if isfile(join(pgal, f))]

    data = []
    for file in onlyfiles:
        if file.endswith('.jpg'):
            data.append( {
                "filename": file
            })

    return jsonify(data), 200


if __name__ == "__main__":
    assert sys.version_info >= (3, 6), sys.version_info
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--motor", default="192.168.178.71", help="IP from the ESP32 controlling the steppers"
    )
    parser.add_argument(
        "--htpu", default="obj-detector", help="client host for object detector"
    )
    parser.add_argument(
        "--ptpu", type=int, default=8010, help="client port for object detector"
    )
    parser.add_argument(
        "--photo", default="http://photo-service:8005", help="client restapi address for photo service"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="set logging level to debug"
    )

    parser.add_argument(
        "--pgallery", default="/mnt/gallery", help="folder to save gallery photos"
    )

    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level)

    m5stack_host = args.motor

    try:
        tpu_socket.connect((args.htpu, args.ptpu))
        connection = tpu_socket.makefile("wb")
        tpu_api_detected = True
    except:
        tpu_api_detected = False

    streaming = threading.Thread(target=video_streaming)
    streaming.start()

    app.run(host="0.0.0.0", debug=True, threaded=True, use_reloader=False)
