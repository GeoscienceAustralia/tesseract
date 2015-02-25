// Code goes here

var myApp = angular.module('myApp', []);

myApp.controller('MainCtrl', function($scope, $http){

    $scope.data = null;
    $scope.dato = null;

    $http({
        method: 'GET',
        url: "/pixel_drill/23/23/23/23/",
        headers: {'Content-Type': 'application/x-www-form-urlencoded'}
    }).success(function(response){
        $scope.data = response;
        console.log("response data: " + $scope.data)

    }).error(function(){
        alert("Error ");
    });

    $http({
        method: 'GET',
        url: "/pixel_drull/23/23/23/23/",
        headers: {'Content-Type': 'application/x-www-form-urlencoded'}
    }).success(function(response){
        var parseDate = d3.time.format("%y-%b-%d").parse
        response.forEach(function(d) {
            d.date = parseDate(d.date);
        });
        $scope.dato = response;
        console.log("response dato: " + $scope.dato)

    }).error(function(){
        alert("Error ");
    });

});


myApp.directive('areaChart', function(){

  function link(scope, el, attr){

    var margin = {top: 20, right: 20, bottom: 30, left: 50},
    width = 960 - margin.left - margin.right,
    height = 500 - margin.top - margin.bottom;

    var formatPercent = d3.format(".0%");

    var x = d3.time.scale()
        .range([0, width]);

    var y = d3.scale.linear()
        .range([height, 0]);

    var color = d3.scale.category20();

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

    var stack = d3.layout.stack()
        .values(function(d) { return d.values; });

    var svg = d3.select("body").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
      .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


    scope.$watch('data', function(data){
      console.log('changed dato: ' + data)
      if(!data){
        return;
      }
      var browsers = stack(color.domain().map(function(name) {
        return {
          name: name,
          values: data.map(function(d) {
            return {date: d.date, y: d[name] / 100};
          })
        };
        console.log(browsers)
      }));

      x.domain(d3.extent(data, function(d) { return d.date; }));

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

myApp.directive('donutChart', function(){
  function link(scope, el, attr){
    var color = d3.scale.category10();
    var width = 300;
    var height = 300;
    var min = Math.min(width, height);
    var svg = d3.select(el[0]).append('svg');
    var pie = d3.layout.pie().sort(null);
    var arc = d3.svg.arc()
      .outerRadius(min / 2 * 0.9)
      .innerRadius(min / 2 * 0.5);

    svg.attr({width: width, height: height});
    // center the donut chart
    var g = svg.append('g')
      .attr('transform', 'translate(' + width / 2 + ',' + height / 2 + ')');

    // add the <path>s for each arc slice
    var arcs = g.selectAll('path');

    scope.$watch('data', function(data){
      console.log("changed data: " + data)
      if(!data){ return; }
      arcs = arcs.data(pie(data));
      arcs.exit().remove();
      arcs.enter().append('path')
        .style('stroke', 'white')
        .attr('fill', function(d, i){ return color(i) });
      // update all the arcs (not just the ones that might have been added)
      arcs.attr('d', arc);
    }, true);

  }
  return {
    link: link,
    restrict: 'E',
    scope: { data: '=' }
  };
});