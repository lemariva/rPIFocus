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