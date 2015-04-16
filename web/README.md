Pixel Drill Web Application
===========================

This web application is used to prove fast timeseries retrieval capacities of the proposed data format and Low Level API. It uses a combination of Python, Go and Javascript. 

Key files in this folder are:

  * server.go: This is the web server engine using standard Go language libraries. This program wraps the pixel drill Python function into a JSON object served through HTTP. 
  * static: This folder contains all the HTML, CSS and Javascript code served by Go. Javascript code has dependencies on AngularJS, Openlayers and D3 libraries.  
