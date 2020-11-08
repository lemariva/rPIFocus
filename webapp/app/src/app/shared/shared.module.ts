 
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