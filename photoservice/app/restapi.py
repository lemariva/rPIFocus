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
import struct
import cv2
import exifread
import time
import subprocess
import numpy as np
import logging
from flask import Flask, render_template, Response, request, jsonify, url_for
from celery import Celery
from celery.result import AsyncResult
from os import listdir, makedirs, replace, remove
from os.path import isfile, join
import shutil 

app = Flask(__name__)
app.config["CELERY_broker_url"] = "redis://{0}:6379/0".format(os.environ["HOST_REDIS"])
app.config["result_backend"] = "redis://{0}:6379/0".format(os.environ["HOST_REDIS"])

celery = Celery(app.name, broker=app.config["CELERY_broker_url"])
celery.conf.update(app.config)

tmp_photo_folder = None
save_photo_folder = None

hdr_b = np.array([30, 25, 20, 15, 13, 10, 8, 6, 5, 4, 3.2, 2.5, 2, 1.6, 1.3, 1, 0.8, 0.6,
                  0.5, 0.4, 0.3, 1/4, 1/5, 1/6, 1/8, 1/10, 1/20, 1/25, 1/30, 1/40, 1/50, 1/60,
                  1/80, 1/100, 1/125, 1/160, 1/200, 1/250, 1/320, 1/400, 1/500, 1/640, 1/800,
                  1/1000, 1/1250, 1/1600, 1/2000, 1/2500, 1/3200, 1/4000, 1/5000, 1/6400, 1/8000])

# celery --app=restapi.celery worker -l INFO

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx

@celery.task()
def process_photos(folders):
    psave = folders["psave"]
    ptmp = folders["ptmp"]
    pgal = folders["pgal"]

    foldername = folders["foldername"]

    save_folder = psave + "/" + foldername
    makedirs(save_folder)

    onlyfiles = [f for f in listdir(ptmp) if isfile(join(ptmp, f))]

    images = []
    times = np.array([], dtype=np.float32)
    logging.info("Loading images for HDR")
    for filename in onlyfiles:
        filesrc = ptmp + "/" + filename
        filedest = save_folder + "/" + filename
        shutil.move(filesrc, filedest)

        file_data = open(filedest, 'rb')
        tags = exifread.process_file(file_data)
        exposure = float(tags['EXIF ExposureTime'].values[0])

        im = cv2.imread(filedest)
        images.append(im)
        times = np.append(times, np.float32(exposure))

    logging.info("Align input images")
    align_MTB = cv2.createAlignMTB()
    align_MTB.process(images, images)

    logging.info('Obtain Camera Response Function (CRF)')
    calibrate_debevec = cv2.createCalibrateDebevec()
    response_debevec = calibrate_debevec.process(images, times)

    logging.info('Merge images into an HDR linear image')
    merge_debevec = cv2.createMergeDebevec()
    hdr_debevec = merge_debevec.process(images, times, response_debevec)

    logging.info('Save HDR image')
    save_file = pgal + "/" + foldername 
    cv2.imwrite(save_file + ".hdr", hdr_debevec)

    logging.info("Tonemaping using Drago's method ... ")
    tonemap_drago = cv2.createTonemapDrago(1.0, 0.7)
    ldr_drago = tonemap_drago.process(hdr_debevec)
    ldr_drago = 3 * ldr_drago
    cv2.imwrite(save_file + "_drago.jpg", ldr_drago * 255)
    
    logging.info("Tonemaping using Reinhard's method ... ")
    tonemap_reinhard = cv2.createTonemapReinhard(1.5, 0,0,0)
    ldr_reinhard = tonemap_reinhard.process(hdr_debevec)
    cv2.imwrite(save_file + "_reinhard.jpg", ldr_reinhard * 255)
    
    logging.info("Tonemaping using Mantiuk's method ... ")
    tonemap_mantiuk = cv2.createTonemapMantiuk(2.2,0.85, 1.2)
    ldr_mantiuk = tonemap_mantiuk.process(hdr_debevec)
    ldr_mantiuk = 3 * ldr_mantiuk
    cv2.imwrite(save_file + "_mantiuk.jpg", ldr_mantiuk * 255)


@celery.task()
def take_photo(parameters):
    global hdr_b
    # foto parameters
    aeb = parameters["aeb"]
    ev = parameters["ev"]
    ex = parameters["ex"]
    iso = parameters["iso"]
    # paths
    foldername = parameters["foldername"]
    ptmp = parameters["ptmp"]
    psave = parameters["psave"]
    pgal = parameters["pgal"]

    logging.info("Taking a reference photo")
    path_name = ptmp + "/0.jpg"
    cmd = """raspistill -n -bm -r -ev {0} -ex {1} -ISO {2} -o {3} -tl 0 --thumb none""".format(ev, ex, iso, path_name)
    subprocess.call(cmd, shell=True)

    if aeb > 0:
        logging.info("Getting parameters from reference photo")
        file_data = open(path_name, 'rb')
        tags = exifread.process_file(file_data)
        exposure = float(tags['EXIF ExposureTime'].values[0])
        idx = find_nearest(hdr_b, exposure)

        delta_aeb = aeb + 1 # getting aeb from array

        # getting exposure times
        idx_m2 = idx - delta_aeb * 2
        idx_m2 = idx_m2 if idx_m2 > 0 else 0
        idx_m1 = idx - delta_aeb
        idx_m1 = idx_m1 if idx_m1 > 0 else 0

        idx_p2 = idx + delta_aeb * 2
        idx_p2 = idx_p2 if idx_p2 < len(hdr_b) else len(hdr_b)
        idx_p1 = idx + delta_aeb
        idx_p1 = idx_p1 if idx_p1 < len(hdr_b) else len(hdr_b)

        hdr_ss = [hdr_b[idx_m2] * 1e6, hdr_b[idx_m1] * 1e6, hdr_b[idx_p1] * 1e6, hdr_b[idx_p2] * 1e6]

        for pic, hdr in enumerate(hdr_ss):
            path_name = ptmp + "/{0}.jpg".format(pic + 1)
            cmd = """raspistill -n -bm -r -ev {0} -ISO {1} -ss {2} -o {3} -tl 0 --thumb none""".format(ev, iso, hdr, path_name)
            print(cmd)
            subprocess.call(cmd, shell=True)

    folders = {
                "psave": psave, 
                "ptmp": ptmp, 
                "pgal": pgal,
                "foldername": foldername
            }

    process_photos.delay(folders)

@app.route("/api/takephoto")
def api_take_photo():
    foldername = request.args.get("foldername")
    aeb = int(request.args.get("aeb"))
    ev = int(request.args.get("ev"))
    ex = request.args.get("ex")
    iso = request.args.get("iso")

    parameters = {  
                    "foldername": foldername, 
                    "aeb": aeb, 
                    "ev": ev, 
                    "ex": ex, 
                    "iso": iso,
                    "ptmp": tmp_photo_folder,
                    "psave": save_photo_folder,
                    "pgal": gallery_photo_folder
                }

    task = take_photo.delay(parameters)

    data = {"task_id": url_for("taskstatus", task_id=task.id)}

    return jsonify(data), 200


@app.route("/api/hrdphoto")
def api_hrd_photo():
    foldername = request.args.get("foldername")
    ptmp = request.args.get("ptmp")
    psave = request.args.get("psave")

    parameters = {  
                    "foldername": foldername, 
                    "ptmp": ptmp,
                    "psave": psave
                }

    task = process_photos.delay(parameters)

    data = {"task_id": url_for("taskstatus", task_id=task.id)}

    return jsonify(data), 200


@app.route("/status/<task_id>")
def taskstatus(task_id):
    task = celery.AsyncResult(task_id)

    status = task.state
    if task.state != "FAILURE":
        response = {
            "state": task.state,
        }
    else:
        response = {
            "state": task.state,
            "status": str(task.info),  # this is the exception raised
        }
    return jsonify(response)


if __name__ == "__main__":
    assert sys.version_info >= (3, 6), sys.version_info

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8005, help="server port for information")
    parser.add_argument("--ptmp", default="/mnt/ramdisk", help="folder for temp photos")
    parser.add_argument("--praw", default="/mnt/raw", help="folder to save raw photos")
    parser.add_argument("--pgallery", default="/mnt/gallery", help="folder to save gallery photos")
    parser.add_argument("-v", "--verbose", action="store_true", help="set logging level to debug")
    
    args = parser.parse_args()

    tmp_photo_folder = args.ptmp
    save_photo_folder = args.praw
    gallery_photo_folder = args.pgallery

    app.run(
        host="0.0.0.0", debug=True, port=args.port, threaded=True, use_reloader=False
    )
