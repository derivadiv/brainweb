// Tutorial from https://codeforgeek.com/2014/12/single-page-web-app-angularjs/ 
var app = angular.module("brainwebapp",['ngRoute']);
app.config(function($routeProvider){
	$routeProvider
		.when('/hippovol', {
			templateUrl: 'hippovol.html'
		});
});
