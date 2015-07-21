var app = angular.module("brainwebapp",['ngRoute']);
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
		$scope.data = res['data'];
	});
}
app.controller('BrainCtrl', ['$scope','$http',BrainCtrl]);
app.controller('HipCtrl', ['$scope','$http',HipCtrl]);
