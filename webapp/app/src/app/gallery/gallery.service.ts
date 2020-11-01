import {Injectable} from '@angular/core';
import {Http} from "@angular/http";
import {Observable} from "rxjs/Observable";
import 'rxjs/add/operator/map';
import { PhotoFiles } from "./types";

const SERVER_URL: string = 'api/';

@Injectable()
export class GalleryService {

    constructor(private http: Http) {
    }

    public getPhotoFiles(): Observable<PhotoFiles[]> {
        return this.http.get(`${SERVER_URL}getphotos`).map((res) => res.json());
    }
}