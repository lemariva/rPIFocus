
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

// external modules
import {BrowserModule} from '@angular/platform-browser';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import {NgModule} from '@angular/core';
import {PreloadAllModules, RouterModule} from "@angular/router";

// own modules and components
import {appRoutingModule} from "./app.routes";
import {AppComponent} from './app.component';
import {SharedModule} from "./shared/shared.module";
import {MaterialModule} from "./shared/material/material.module";
import {CameraComponent} from "./camera/camera.component";
import {GalleryComponent} from "./gallery/gallery.component";
import {GalleryService} from './gallery/gallery.service'
import {CameraService} from "./camera/camera.service";
import {SharingService} from './camera/storage'

@NgModule({
    declarations: [
        AppComponent,
        CameraComponent,
        GalleryComponent
    ],
    imports: [
        BrowserModule,
        BrowserAnimationsModule,
        SharedModule,
        MaterialModule,
        appRoutingModule
    ],
    providers: [
        CameraService,
        SharingService,
        GalleryService
    ],
    bootstrap: [AppComponent]
})
export class AppModule {
}