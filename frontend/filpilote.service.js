/**
 * Filpilote service.
 * Handle filpilote application requests.
 * Service is the place to store your application content (it is a singleton) and
 * to provide your application functions.
 */
angular
.module('Cleep')
.service('filpiloteService', ['rpcService', function(rpcService) {
    var self = this;

    self.addArea = function (areaName, gpio1, gpio2) {
        const data = {
            area_name: areaName,
            gpio1,
            gpio2,
        }
        return rpcService.sendCommand('add_area', 'filpilote', data);
    };

    self.deleteArea = function (uuid) {
        const data = {
            area_uuid: uuid,
        }
        return rpcService.sendCommand('delete_area', 'filpilote', data);
    };

    self.setMode = function (uuid, mode) {
        const data = {
            area_uuid: uuid,
            mode,
        }
        return rpcService.sendCommand('set_mode', 'filpilote', data);
    };
}]);
