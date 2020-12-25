
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

import { Component, OnInit, AfterViewInit } from '@angular/core'; 
import { MatSliderChange } from '@angular/material/slider';
import { MatButtonToggleChange } from '@angular/material/button-toggle';
import { CameraService} from "./camera.service";
import { FormBuilder, FormGroup, FormControl, FormsModule} from '@angular/forms';
import { CamStatus, MotorStatus, FocusConfig, FocusStatus, FocusType, ObjectConfig, PhotoConfig, PhotoStatus} from "./types";
import { SharingService } from './storage';

import 'rxjs/add/operator/map'
import 'rxjs/add/operator/catch';

import * as _ from 'lodash';

@Component({ 
  selector: 'app-camera', 
  templateUrl: './camera.component.html', 
  styleUrls: ['./camera.component.css'] 
}) 

export class CameraComponent implements OnInit { 
    CAM_WIDTH: number = 640;
    CAM_HEIGHT: number = 480;

    private ImagePath: string; 
    private motAperture: MotorStatus[];
    private showFocusBox: Boolean = true;
    private showFocusObject: Boolean = true;
    private focusType = FocusType.auto;
    private showFocusType: number = 0; 
    private showTpuEdge: Boolean = false;
    private takePhotoConfig;

    private focusBoxSize = 100;
    private photoConfig: PhotoConfig[] = [
      {
        ev: 0,
        aeb: 2,
        exposure: "auto",
        iso: 200
      }
    ]
    private focusConfig: FocusConfig[] = [
      {
        type: "image",
        frame_x: 0,
        frame_y: 0,
        frame_w: this.CAM_WIDTH,
        frame_h: this.CAM_HEIGHT,
      }
    ];
    private focusObject: ObjectConfig[] = [
      {
        objects: "",
      }
    ];

    private camStatus: CamStatus[] = [
        {
          ma_pos: 0,
          ma_calibrated: false,
          ma_max_steps: 0,
          mf_pos: 0,
          mf_calibrated: false,
          mf_max_steps: 0,
          tpu_api: false,
        }
    ];
    private focusStatus: FocusStatus[] = [
      {
        mode: 0,
        focus_phase: 0,
        started: true,
        autotype: "autofocus",
        thread_name: "Thread-XX"
      }
    ];

    constructor(
      private cameraService: CameraService, 
      private formBuilder: FormBuilder,
      private storageService: SharingService
      ) {
        this.ImagePath = "http://" + location.hostname  + ":5000/api/video_feed";
        this.takePhotoConfig = this.formBuilder.group({
          ev: this.photoConfig[0].ev,
          aeb: this.photoConfig[0].aeb,
          iso: this.photoConfig[0].iso,
          exposure: this.photoConfig[0].exposure,
        });
    }

    ngOnInit() {
      this.getCamStatus();
      this.getFocusStatus();
    }

    public updateGui() {
      this.showFocusBox = (this.focusConfig['type'] == "box") ? false : true;
      this.showFocusObject = (this.focusConfig['type'] == "object") ? false : true;
      this.showFocusType = this.focusStatus['mode'];
      this.showTpuEdge = this.camStatus['tpu_api'];
    }

    /* update status functions */
    public getCamStatus() {
      this.cameraService.getCamStatus().subscribe((camera) => {
          this.camStatus = camera;
          this.updateGui()
      });

      this.cameraService.getAutoFocus().subscribe((focusMode) => {
        this.focusStatus = focusMode;
        this.updateGui()
    });
    }

    public getFocusStatus() {
      this.cameraService.getFocusStatus().subscribe((focusConfig) => {
        this.focusConfig = focusConfig;
        this.updateGui()
      });
    }

    /* set motor positions */
    public setMotorPosition(mType: string, mStep: number) {
      this.cameraService.setMotorPosition(mType, mStep).subscribe((motAperture) => {
        this.motAperture = motAperture;
        this.updateGui()
      });
    }
    // aperture
    onApertureChange(event: MatSliderChange) {
      var step, position, requestUrl;
      position = event.value;
      step = parseInt(position);
      this.setMotorPosition("aperture", step)
    }
    // focus
    onFocusSliderChange(event: MatSliderChange) {
      var step, position, requestUrl;
      position = event.value;
      step = parseInt(position);
      this.setMotorPosition("focus", step)
    }

    /* autofocus functions */

    // image, box, object
    onFocusElementChange(event: MatButtonToggleChange) {
      this.focusConfig['type'] = event.value;
      var focusTmp: FocusConfig[] = [{
        "type": event.value,
        "frame_x": 0,
        "frame_y": 0,
        "frame_w": this.CAM_WIDTH,
        "frame_h": this.CAM_HEIGHT,
      }];
      this.setFocusFrameCamera(focusTmp)
    }

    // frame
    public setFocusFrameCamera(focusTmp: FocusConfig[]) {
      this.cameraService.setFocusFrame(focusTmp).subscribe((focusConfig) => {
        this.focusConfig = focusConfig;
        this.updateGui()
      });
    }
    public setFocusObjectCamera(focusTmp: FocusConfig[]) {
      this.cameraService.setFocusObject(focusTmp).subscribe((focusObject) => {
        this.focusObject = focusObject;
        this.updateGui()
      });
    }

    onClickBoxImage(event){
      let mousePosition= (<any>window).mousePosition;
      let positionX = Math.floor(mousePosition.x * this.CAM_WIDTH);
      let positionY = Math.floor(mousePosition.y * this.CAM_HEIGHT);
      if (this.focusConfig['type'] == "box"){
        var focusTmp: FocusConfig[] = [ {
          "type": "box",
          "frame_x": positionX - Math.round(this.focusBoxSize/2),
          "frame_y": positionY - Math.round(this.focusBoxSize/2),
          "frame_w": this.focusBoxSize,
          "frame_h": this.focusBoxSize,
        }];
        this.setFocusFrameCamera(focusTmp)
      } else if (this.focusConfig['type'] == "object"){
        var focusTmp: FocusConfig[] = [ {
          "type": "object",
          "frame_x": positionX,
          "frame_y": positionY,
          "frame_w": 0,
          "frame_h": 0,
        }];
        this.setFocusObjectCamera(focusTmp);
      };  
    }

    onFocusBoxSizeChange(event: MatSliderChange) {
      this.focusBoxSize = event.value;
    }

    public setAutoFocus(focusType: number) {
      this.cameraService.setAutoFocus(focusType).subscribe((focusStatus) => {
        this.focusStatus = focusStatus;
        this.updateGui()
      });
    }

    onFocusModeClick(event) {
      var eventId = event.target.textContent;
      
      switch(eventId){
        case "Manual":
          this.setAutoFocus(FocusType.manual);
          break;
        case "Auto":
          this.setAutoFocus(FocusType.auto);
          break;
        case "Live":
          this.setAutoFocus(FocusType.live);
          break;
        default:
          this.setAutoFocus(FocusType.stop)
      }
    }

    onSubmit(photoData) {
      //this.takePhotoConfig.reset();
      this.photoConfig[0].ev = photoData.ev;
      this.photoConfig[0].aeb = photoData.aeb;
      this.photoConfig[0].exposure = photoData.exposure;
      this.photoConfig[0].iso = photoData.iso;

      this.cameraService.takePhoto(this.photoConfig).subscribe((photoStatus) => {
        console.info('Photo filename:', photoStatus);
        this.updateGui()
      });
    }

}