import { Component } from '@angular/core';

@Component({
  selector: 'app',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {

  views:Object[] = [
    {
      name: "Camera",
      description: "Take photos using the camera",
      icon: "camera",
      link: "/home"
    },
    {
      name: "Gallery",
      description: "Check the photos taken with the camera",
      icon: "image_search",
      link: "/gallery"
    }
  ];
  
  title = 'raspi-camera';
}
