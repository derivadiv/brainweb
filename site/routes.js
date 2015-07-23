var app = angular.module("brainwebapp",['ngRoute','ngSanitize']);
app.config(function($routeProvider){
	$routeProvider
		.when('/hippovol', {
			templateUrl: 'hippovol.html',
			controller: 'HipCtrl'
		})
		.when('/test', { 
			templateUrl: 'test.html',
			controller: 'BrainCtrl'
		})
		.when('/dbq', {
			templateUrl: 'dbq.html'
		});
});

function BrainCtrl($scope, $http){
	$http.post('/testme').success(function(res) {
		$scope.data = res['data'];
	});
}

function HipCtrl($scope, $http){
	$http.post('/hippovol').success(function(res) {
		$scope.myhtml = arr2tablehtml(res['data']);
	});
}

function arr2tablehtml(data){
	// header
	var head = data.shift();
	var tstr = '<thead><tr><th>'+head.join('</th><th>')+'</th></tr></thead><tbody>';
	// remainder is actual table data
	$.each(data, function(i, row){
		var rowstr = '<tr><td>'+row.join('</td><td>')+'</td></tr>';
		tstr = tstr + rowstr;
	});
	tstr = tstr + '</tbody>';
	return tstr;
}

app.controller('BrainCtrl', ['$scope','$http',BrainCtrl]);
app.controller('HipCtrl', ['$scope','$http',HipCtrl]);
