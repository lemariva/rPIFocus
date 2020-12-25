 

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

import { NgModule } from '@angular/core';
import { CommonModule } from "@angular/common";
import { RouterModule } from "@angular/router";
import { FormsModule, ReactiveFormsModule} from "@angular/forms";
import { HttpModule } from "@angular/http";
import { CdkTableModule } from '@angular/cdk/table';
import { FlexLayoutModule } from "@angular/flex-layout";
import { MainLayoutModule } from "./layouts/main-layout/main-layout.module";
import { GalleryModule } from  'ng-gallery';
import { GALLERY_CONFIG } from 'ng-gallery';


@NgModule({
    imports: [
        // Angular Modules
        CommonModule,
        FormsModule,
        ReactiveFormsModule,
        RouterModule,
        HttpModule,
        FlexLayoutModule,
        CdkTableModule,
        // Chart module
        MainLayoutModule,
        // Gallery
        GalleryModule
    ],
    exports: [
        // Angular Modules
        CommonModule,
        FormsModule,
        ReactiveFormsModule,
        RouterModule,
        HttpModule,
        FlexLayoutModule,
        CdkTableModule,
        // Chart module
        MainLayoutModule,
        GalleryModule
    ],
    declarations: [],
    providers: [
        {
            provide: GALLERY_CONFIG,
            useValue: {
              dots: true,
              imageSize: 'contain',
              thumbMode: 'strict',
              loadingStrategy: 'lazy',
              gestures: 'true',
              autoPlay: 'true'
            }
        }
    ],
    entryComponents: []
})
export class SharedModule {
}