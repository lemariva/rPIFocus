import {NgModule} from '@angular/core';

import {MainLayoutComponent} from './main-layout.component';
import {CommonModule} from "@angular/common";
import {FlexLayoutModule} from "@angular/flex-layout";
import {NavBarComponent} from "./nav-bar/nav-bar.component";
import {MatButtonModule} from '@angular/material/button';
import {MatIconModule} from '@angular/material/icon';
import {MatMenuModule} from '@angular/material/menu';
import {RouterModule} from "@angular/router";
import {MatToolbarModule} from '@angular/material/toolbar';
import {SideNavComponent} from "./side-nav/side-nav.component";

@NgModule({
    imports: [
        CommonModule,
        RouterModule,
        FlexLayoutModule,
        MatMenuModule,
        MatButtonModule,
        MatIconModule,
        MatToolbarModule
    ],
    exports: [
        MainLayoutComponent,
        NavBarComponent,
        SideNavComponent],
    declarations: [
        MainLayoutComponent,
        NavBarComponent,
        SideNavComponent
    ],
    providers: [],
})
export class MainLayoutModule {
}
