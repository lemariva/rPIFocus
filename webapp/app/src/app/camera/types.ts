export class CamStatus {
    ma_pos: number = 0;
    ma_calibrated: boolean = false;
    ma_max_steps: number = 0;
    mf_pos: number = 0;
    mf_calibrated: boolean = false;
    mf_max_steps: number = 0;
    tpu_api: boolean = false;
}

export class MotorStatus {
    mtype: string = "";
    position: number = 0;
    status: boolean = true;
    clockwise: number = 0;
    steps: number = 0;
}

export class FocusConfig {
    type: string = "";
    frame_x: number = 0;
    frame_y: number = 0;
    frame_w: number = 0;
    frame_h: number = 0;
}

export class ObjectConfig {
    objects: string = "";
}

export class PhotoConfig {
    ev: number = 0;
    aeb: number = 0;
    exposure: string = "auto";
    iso: number = 200;
}

export class PhotoStatus {
    filename: string = "";
}

export class FocusStatus {
    mode: number = 0;
    focus_phase: number = 0;
    started: boolean = true;
    autotype: string = "autofocus"; 
    thread_name: string = "Thread-XX"
}

export enum FocusType {
    stop = 0,
    manual = 1,
    auto = 2,
    live = 3,
}