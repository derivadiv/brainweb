var app = angular.module("brainwebapp",['ngRoute']);
app.config(function($routeProvider){
	$routeProvider
		.when('/hippovol', {
			templateUrl: 'hippovol.html'
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
	$http.post('/hippovol').success(function(res) {
		$scope.data = res['data'];
	});
}

app.controller('BrainCtrl', ['$scope','$http',BrainCtrl]);
