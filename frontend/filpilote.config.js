/**
 * Filpilote config component
 * Handle filpilote application configuration
 * If your application doesn't need configuration page, delete this file and its references into desc.json
 */
angular
.module('Cleep')
.directive('filpiloteConfigComponent', ['$rootScope', 'cleepService', 'toastService', 'filpiloteService', '$mdDialog',
function($rootScope, cleepService, toastService, filpiloteService, $mdDialog) {

    var filpiloteConfigController = function() {
        var self = this;
        self.areas = [];
        self.areaName = undefined;
        self.selectedGpios = [
            { gpio: undefined, label: 'gpio1' },
            { gpio: undefined, label: 'gpio2' },
        ];
        self.selectedArea = undefined;
        self.MODES = [
            { label: 'Frost-free', value: 'FROSTFREE'},
            { label: 'Comfort', value: 'COMFORT'},
            { label: 'Eco', value: 'ECO'},
            { label: 'Stop', value: 'STOP'},
        ]
        self.selectedMode = self.MODES[0].value;

        self.$onInit = function() {
            self.resetForm();
            cleepService.getModuleDevices('filpilote');
        };

        $rootScope.$watch(
            () => cleepService.devices,
            () => {
                const devices = cleepService.getModuleDevices('filpilote');
                self.setAreas(devices);
            }
        );

        self.resetForm = function () {
            self.areaName = undefined;
        };

        self.setAreas = function (devices) {
            const areas = [];
            for (const area of devices) {
                areas.push({
                    title: area.name,
                    subtitle: 'Current mode: ' + self.getModeLabel(area.mode),
                    clicks: [
                        {
                            icon: 'pencil',
                            tooltip: 'Set mode',
                            click: self.openModeDialog,
                            meta: { area }
                        },
                        {
                            icon: 'delete',
                            style: 'md-accent',
                            click: self.deleteArea,
                            meta: { area },
                        }
                    ]
                });
            }
            self.areas = areas;
        };

        self.getModeLabel = function (mode) {
            for (const item of self.MODES) {
                if (mode === item.value) {
                    return item.label;
                }
            }
        };

        self.addArea = function () {
            const gpio1 = self.selectedGpios.filter((gpio) => gpio.label === 'gpio1')[0];
            const gpio2 = self.selectedGpios.filter((gpio) => gpio.label === 'gpio2')[0];
            filpiloteService.addArea(self.areaName, gpio1.gpio, gpio2.gpio)
                .then((response) => {
                    if (!response.error) {
                        cleepService.reloadDevices();
                        self.resetForm();
                        toastService.success('Area added');
                    }
                });
        };

        self.deleteArea = function (area) {
            filpiloteService.deleteArea(area.name)
                .then((response) => {
                    if (!response.error) {
                        cleepService.reloadDevices();
                        toastService.success('Area deleted');
                    }
                });
        };

        self.setMode = function(area, mode) {
            filpiloteService.setMode(area.name, mode)
                .then((response) => {
                    if (!response.error) {
                        cleepService.reloadDevices();
                        toastService.success('Mode "' + mode + '" applied');
                    }
                });
        };

        self.openModeDialog = function (area) {
            self.selectedArea = area;
            self.selectedMode = area.mode;
            
            return $mdDialog.show({
                controller: function() { return self },
                controllerAs: '$ctrl',
                templateUrl : 'mode.dialog.html',
                clickOutsideToClose: true,
            }).then(() => {
                self.setMode(self.selectedArea, self.selectedMode);
            });
        };

        self.closeDialog = function (cancel) {
            if (cancel === true) {
                $mdDialog.cancel();
                return;
            }
            $mdDialog.hide();
        }
    };

    return {
        templateUrl: 'filpilote.config.html',
        replace: true,
        scope: true,
        controller: filpiloteConfigController,
        controllerAs: '$ctrl',
    };
}]);
