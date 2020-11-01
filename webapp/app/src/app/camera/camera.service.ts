
/*
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
*/

import {Injectable} from '@angular/core';
import {Http} from "@angular/http";
import {Observable} from "rxjs/Observable";
import 'rxjs/add/operator/map';
import {
    CamStatus,
    MotorStatus,
    FocusConfig,
    FocusStatus,
    ObjectConfig,
    PhotoConfig
} from "./types";

const SERVER_URL: string = 'api/';

@Injectable()
export class CameraService {
    CAM_WIDTH: number = 640;
    CAM_HEIGHT: number = 480;

    constructor(private http: Http) {
    }

    public getCamStatus(): Observable<CamStatus[]> {
        return this.http.get(`${SERVER_URL}status`).map((res) => res.json());
    }

    public getFocusStatus(): Observable<FocusConfig[]> {
        return this.http.get(`${SERVER_URL}frame`).map((res) => res.json());
    }

    public setMotorPosition(mType: string, mStep: number): Observable<MotorStatus[]> {
        return this.http.get(`${SERVER_URL}move?mtype=${mType}&position=${mStep}`).map((res) => res.json());
    }

    public setAutoFocus(focusType: number): Observable<FocusStatus[]> {
        return this.http.get(`${SERVER_URL}autofocus?mode=${focusType}`).map((res) => res.json());
    }

    public getAutoFocus(): Observable<FocusStatus[]> {
        return this.http.get(`${SERVER_URL}autofocus`).map((res) => res.json());
    }


    public setFocusObject(frame: FocusConfig[]): Observable<ObjectConfig[]> {
        var requestUrl = `${SERVER_URL}object?x=${frame[0].frame_x}&y=${frame[0].frame_y}&type=${frame[0].type}`
        return this.http.get(requestUrl).map((res) => res.json());
    }


    public takePhoto(config: PhotoConfig[]): Observable<String> {
        var requestUrl = `${SERVER_URL}takephoto?ev=${config[0].ev}&ex=${config[0].exposure}&iso=${config[0].iso}&aeb=${config[0].aeb}`
        return this.http.get(requestUrl).map((res) => res.json());
    }

    public setFocusFrame(frame: FocusConfig[]): Observable<FocusConfig[]> {
        if ((frame[0].frame_x + frame[0].frame_w) > this.CAM_WIDTH) {
            frame[0].frame_w = this.CAM_WIDTH - frame[0].frame_x;
        }
        if (frame[0].frame_x  < 0) {
            frame[0].frame_w = frame[0].frame_w + frame[0].frame_x;
            frame[0].frame_x = 0;
        }
        if ((frame[0].frame_y + frame[0].frame_h) > this.CAM_HEIGHT) {
            frame[0].frame_h = this.CAM_HEIGHT - frame[0].frame_y;
        }
        if (frame[0].frame_y < 0) {
            frame[0].frame_h = frame[0].frame_h + frame[0].frame_y;
            frame[0].frame_y = 0;
        }
        var requestUrl = `${SERVER_URL}frame?x=${frame[0].frame_x}&y=${frame[0].frame_y}&w=${frame[0].frame_w}&h=${frame[0].frame_h}&type=${frame[0].type}`
        return this.http.get(requestUrl).map((res) => res.json());
    }
}
