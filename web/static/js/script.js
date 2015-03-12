// Code goes here

var myApp = angular.module('myApp', []);

myApp.controller('MainCtrl', function($scope, $http){

    $scope.ls5 = true;
    $scope.ls7 = true;
    $scope.era = true;

    $scope.sat = "LS5";
    $scope.prod = "FC";
    $scope.start_date = new Date(1987, 1, 1, 0, 0, 0, 0);
    $scope.end_date = new Date(2014, 1, 1, 0, 0, 0, 0);
    $scope.data = null;
    $scope.coords = [null, null];

    $scope.update_coords = function(coords) {
        console.log("update_ts_with_coords: " + coords)
        $http({
            method: 'GET',
            url: "/pixel_drill/" + $scope.start_date.toISOString() + "/" + $scope.end_date.toISOString() + "/" + $scope.coords[0] + "/" + $scope.coords[1] + "/",
            headers: {'Content-Type': 'application/x-www-form-urlencoded'}
        }).success(function(response){
            var parseDate = d3.time.format("%Y-%m-%dT%H:%M:%S.%LZ").parse

            response.forEach(function(d) {
                d.timestamp = parseDate(d.timestamp);
            });

            $scope.data = response;

        }).error(function(){
            alert("Error ");
        });
    };

});



myApp.directive('clickableMap', function(){

  function link(scope, el, attr){

    console.log(scope.coords);


    el.append('<div id="map" class="col-md-9"></div>');

    var mousePositionControl = new ol.control.MousePosition({
      coordinateFormat: ol.coordinate.createStringXY(4),
      projection: 'EPSG:4326',
      // comment the following two lines to have the mouse position
      // be placed within the map.
      className: 'custom-mouse-position',
      target: document.getElementById('mouse-position'),
      undefinedHTML: '&nbsp;'
    });


    // A ring must be closed, that is its last coordinate
    // should be the same as its first coordinate.
    var ring = [
      [147, -31], [152, -31], [152, -25], [147, -25], [147, -31]
    ];

    // A polygon is an array of rings, the first ring is
    // the exterior ring, the others are the interior rings.
    // In your case there is one ring only.
    var polygon = new ol.geom.Polygon([ring]);

    // Create feature with polygon.
    var feature = new ol.Feature(polygon);

    polygon.transform('EPSG:4326', 'EPSG:3857');


    // Create vector source and the feature to it.
    var vectorSource = new ol.source.Vector();
    vectorSource.addFeature(feature);


    var map = new ol.Map({
      target: 'map',
      controls: ol.control.defaults().extend([mousePositionControl]),
      layers: [
        new ol.layer.Tile({
            source: new ol.source.MapQuest({layer: 'sat'})
        }),
        new ol.layer.Vector({
            source: vectorSource
        })
      ],
      //renderer: exampleNS.getRendererFromQueryString(),
      view: new ol.View({
        center: ol.proj.transform([150.0, -28.00], 'EPSG:4326', 'EPSG:3857'),
        zoom: 6
      })
    });

    map.on("click", function(e) {
        clicked_coord = ol.proj.transform(e.coordinate, 'EPSG:3857', 'EPSG:4326');

        if (147 < clicked_coord[0] && clicked_coord[0]< 152 && -31 < clicked_coord[1] && clicked_coord[1] < -25) {
            scope.coords = clicked_coord;
            scope.update_coords(clicked_coord);
        }
    });


  }
  return {
    link: link,
    restrict: 'E',
    scope: false
  };
});


myApp.directive('areaChart', function(){

  function link(scope, el, attr){

    el.append('<div id="chart" class="col-md-12"></div>');

    var margin = {top: 40, right: 60, bottom: 40, left: 60},
    width = d3.select("#chart").node().getBoundingClientRect().width - margin.left - margin.right,
    //width = 960 - margin.left - margin.right,
    height = (width / 2.618) - margin.top - margin.bottom;

    console.log(d3.select("#chart").node().getBoundingClientRect())

    var formatPercent = d3.format(".0%");

    var x = d3.time.scale()
        .range([0, width]);

    var y = d3.scale.linear()
        .range([height, 0]);

    //var color = d3.scale.category20();
    var color = d3.scale.ordinal()
                  .domain(["FC0", "FC2", "FC1"])
                  .range(["#D9A88F", "#F9D3A5", "#AB9C73"]);

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom");

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left")
        .tickFormat(formatPercent);

    var area = d3.svg.area()
        .x(function(d) { return x(d.date); })
        .y0(function(d) { return y(d.y0); })
        .y1(function(d) { return y(d.y0 + d.y); });

    var stack_bak = d3.layout.stack()
        .values(function(d) { return d.values; });
    var stack = d3.layout.stack()
        .values(function(d) {
            console.log(d.values);
            return d.values; 
        });

    // Clean before plotting
    d3.select("svg").remove();

    var svg = d3.select("#chart").append("svg")
        //.attr("class", "col-md-12")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


    scope.$watch('data', function(data){

      if(!data){
        return;
      }

      color.domain(d3.keys(data[0]).filter(function(key) { return key !== "timestamp"; }));

      var browsers = stack(color.domain().map(function(name) {
        return {
          name: name,
          values: data.map(function(d) {
            return {date: d.timestamp, y: d[name] / 10000};
          })
        };

      }));

      x.domain(d3.extent(data, function(d) { return d.timestamp; }));

      var browser = svg.selectAll(".browser")
          .data(browsers)
          .enter().append("g")
          .attr("class", "browser");

      browser.append("path")
          .attr("class", "area")
          .attr("d", function(d) { return area(d.values); })
          .style("fill", function(d) { return color(d.name); });

      browser.append("text")
          .datum(function(d) { return {name: d.name, value: d.values[d.values.length - 1]}; })
          .attr("transform", function(d) { return "translate(" + x(d.value.date) + "," + y(d.value.y0 + d.value.y / 2) + ")"; })
          .attr("x", -6)
          .attr("dy", ".35em")
          .text(function(d) { return d.name; });

      svg.append("g")
          .attr("class", "x axis")
          .attr("transform", "translate(0," + height + ")")
          .call(xAxis);

      svg.append("g")
          .attr("class", "y axis")
          .call(yAxis);

    }, true);

  }
  return {
    link: link,
    restrict: 'E',
    scope: { data: '=' }
  };
});
