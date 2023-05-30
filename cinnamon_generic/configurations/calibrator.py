from __future__ import annotations

import multiprocessing as mp
from typing import Dict, Any, Optional

from cinnamon_core.core.configuration import supports_variants, Configuration, C
from cinnamon_core.core.registry import RegistrationKey, Registry, register

from cinnamon_generic.components.calibrator import ValidateCondition, HyperOptCalibrator, GridSearchCalibrator


class UnsetCalibrationConfigurationException(Exception):

    def __init__(self, calibration_config):
        super().__init__(f'Cannot get search space if calibration config is not set! Got {calibration_config}')


class NonTunableConfigurationException(Exception):

    def __init__(self, class_type):
        super().__init__(f'Expected an instance of TunableConfiguration but got {class_type}')


@supports_variants
class TunableConfiguration(Configuration):

    @classmethod
    def get_default(
            cls: type[C]
    ) -> C:
        config = super().get_default()
        config.add_short(name='calibration_config',
                         type_hint=RegistrationKey,
                         build_type_hint=Configuration,
                         is_registration=True,
                         build_from_registration=False,
                         is_calibration=True,
                         description="Calibration configuration that specifies")
        return config

    @classmethod
    def get_search_space(
            cls,
            buffer: Optional[Dict[str, Any]] = None,
            parent_key: Optional[str] = None
    ) -> Dict[str, Any]:
        buffer = buffer if buffer is not None else dict()

        default_config = cls.get_default()
        if default_config.calibration_config is None:
            raise UnsetCalibrationConfigurationException(calibration_config=default_config.calibration_config)

        # Apply to children as well
        children = {param_key: param for param_key, param in default_config.items() if
                    param.is_registration and not param.is_calibration}
        for child_key, child in children.items():
            child_config_class = Registry.retrieve_configurations_from_key(config_registration_key=child.value,
                                                                           exact_match=True).class_type
            if not issubclass(child_config_class, TunableConfiguration):
                raise NonTunableConfigurationException(class_type=child_config_class)

            buffer = child_config_class.get_search_space(buffer=buffer,
                                                         parent_key=f'{parent_key}.{child.name}'
                                                         if parent_key is not None else f'{child.name}')

        # Merge search space
        calibration_config_class = Registry.retrieve_configurations_from_key(
            config_registration_key=default_config.calibration_config,
            exact_match=True).class_type
        search_space = {f'{parent_key}.{key}' if parent_key is not None else key: value
                        for key, value in calibration_config_class.get_default().search_space.items()}
        buffer = {**buffer, **search_space}

        return buffer


# TODO: add RandomSearchCalibratorConfig, OptunaCalibratorConfig
class CalibratorConfig(Configuration):

    @classmethod
    def get_default(
            cls
    ) -> CalibratorConfig:
        config = super().get_default()

        config.add_short(name='validate_on',
                         type_hint=str,
                         description="metric name to monitor for calibration",
                         is_required=True)
        config.add_short(name='validate_condition',
                         type_hint=ValidateCondition,
                         description="whether the ``validate_on`` monitor value should be maximized or minimized",
                         is_required=True)

        return config


class HyperoptCalibratorConfig(CalibratorConfig):

    @classmethod
    def get_default(
            cls
    ) -> HyperoptCalibratorConfig:
        config = super().get_default()

        config.add_short(name='file_manager_registration_key',
                         type_hint=RegistrationKey,
                         value=RegistrationKey(name='file_manager',
                                               tags={'default'},
                                               namespace='generic'),
                         description="registration info of built FileManager component."
                                     " Used for filesystem interfacing")
        config.add_short(name='max_evaluations',
                         value=-1,
                         type_hint=int,
                         description="number of evaluations to perform for calibration."
                                     " -1 allows search space grid search.")
        config.add_short(name='mongo_directory',
                         value='mongodb',
                         description="directory name where mongoDB is located and running",
                         is_required=True)
        config.add_short(name='mongo_workers_directory',
                         value='mongo_workers',
                         description="directory name where mongo workers stored their execution metadata")
        config.add_short(name='hyperopt_additional_info',
                         type_hint=Optional[Dict[str, Any]],
                         description="additional arguments for hyperopt calibrator")
        config.add_short(name='use_mongo',
                         value=False,
                         allowed_range=lambda value: value in [False, True],
                         type_hint=bool,
                         description="if enabled, it uses hyperopt mongoDB support for calibration")
        config.add_short(name='mongo_address',
                         value='localhost',
                         type_hint=str,
                         description="the address of running mongoDB instance")
        config.add_short(name='mongo_port',
                         value=4000,
                         type_hint=int,
                         description="the port of running mongoDB instance")
        config.add_short(name='workers',
                         value=2,
                         allowed_range=lambda value: 1 <= value <= mp.cpu_count(),
                         type_hint=int,
                         description="number of mongo workers to run")
        config.add_short(name='reserve_timeout',
                         value=10.0,
                         type_hint=float,
                         description="Wait time (in seconds) for reserving a calibration "
                                     "instance from mongo workers pool")
        config.add_short(name='max_consecutive_failures',
                         value=2,
                         type_hint=int,
                         description="Maximum number of tentatives before mongo worker is shutdown")
        config.add_short(name='poll_interval',
                         value=5.0,
                         type_hint=float,
                         description="Wait time for poll request.")
        config.add_short(name='use_subprocesses',
                         value=False,
                         allowed_range=lambda value: value in [False, True],
                         type_hint=bool,
                         description="If enabled, mongo workers are executed with the"
                                     " capability of running subprocesses")
        config.add_short(name='worker_sleep_interval',
                         value=2.0,
                         type_hint=float,
                         description="Interval time between each mongo worker execution")

        config.add_condition_short(name='worker_sleep_interval_minimum',
                                   condition=lambda parameters: parameters.worker_sleep_interval.value >= 0.5)
        config.add_condition_short(name="max_evaluations_minimum",
                                   condition=lambda parameters: parameters.max_evaluations > 0)

        return config


@register
def register_calibrators():
    Registry.register_and_bind(configuration_class=HyperoptCalibratorConfig,
                               component_class=HyperOptCalibrator,
                               name='calibrator',
                               tags={'hyperopt'},
                               namespace='generic',
                               is_default=True)
    Registry.register_and_bind(configuration_class=Configuration,
                               component_class=GridSearchCalibrator,
                               name='calibrator',
                               tags={'gridsearch'},
                               namespace='generic',
                               is_default=True)