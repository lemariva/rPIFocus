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

import { Component, OnInit } from '@angular/core';
import { GalleryItem, ImageItem } from 'ng-gallery';
import { GalleryService } from "./gallery.service";
import { PhotoFiles} from "./types";

import 'hammerjs';

const SERVER_URL: string = '/photos/gallery/';

@Component({
  templateUrl: './gallery.component.html', 
  styleUrls: ['./gallery.component.css'] 
})

export class GalleryComponent implements OnInit {

  images: GalleryItem[];
  private photoFiles: PhotoFiles[];
  
  constructor(
    private galleryService: GalleryService
    ) {};

  ngOnInit() {
    
    this.images = [
      new ImageItem({ src: `${SERVER_URL}/icon.png`, thumb: `${SERVER_URL}/icon.png` }),
    ];
    
    //console.log(this.images )
    this.galleryService.getPhotoFiles().subscribe((photoFiles) => {
      this.photoFiles = photoFiles;
      this.photoFiles.forEach(
          element =>
            this.images.push(new ImageItem({ src: `${SERVER_URL}${element["filename"]}`, thumb:`${SERVER_URL}${element["filename"]}`}))
      );

    });
  }
}