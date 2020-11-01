import { Routes, RouterModule } from '@angular/router';
import {CameraComponent} from "./camera/camera.component";
import {GalleryComponent} from "./gallery/gallery.component";

export const ROUTES: Routes = [
    // routes from pages
    { path: 'home', component: CameraComponent, data: {title: 'Home'}},
    { path: 'gallery', component: GalleryComponent, data: {title: 'Gallery'}},
    
    // default redirect
    {path: '**', redirectTo: 'home'}
];

export const appRoutingModule = RouterModule.forRoot(ROUTES);