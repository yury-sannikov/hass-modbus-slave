"""The tests for the Modbus sensor component."""
from datetime import timedelta
import logging
from unittest import mock

from homeassistant.components.modbus.const import DEFAULT_HUB
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_TYPE,
)
from homeassistant.setup import async_setup_component
import homeassistant.util.dt as dt_util
import pytest
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.modbus_slave.const import MODBUS_DOMAIN as DOMAIN

_LOGGER = logging.getLogger(__name__)


class ReadResult:
    """Storage class for register read results."""

    def __init__(self, register_words):
        """Init."""
        self.registers = register_words
        self.bits = register_words


async def base_test(
    hass,
    config_device,
    device_name,
    entity_domain,
    array_name_discovery,
    array_name_old_config,
    register_words_or_exception,
    expected,
    method_discovery=False,
    check_config_only=False,
    config_modbus=None,
    scan_interval=None,
    expect_init_to_fail=False,
):
    """Run test on device for given config."""

    if config_modbus is None:
        config_modbus = {
            DOMAIN: {
                CONF_NAME: DEFAULT_HUB,
                CONF_TYPE: "tcp",
                CONF_HOST: "modbusTest",
                CONF_PORT: 5001,
            },
        }

    mock_sync = mock.MagicMock()
    # Setup inputs for the sensor
    with mock.patch(
        "custom_components.modbus_slave.modbus.ModbusTcpClient",
        return_value=mock_sync,
    ), mock.patch(
        "custom_components.modbus_slave.modbus.ModbusSerialClient",
        return_value=mock_sync,
    ), mock.patch(
        "custom_components.modbus_slave.modbus.ModbusUdpClient",
        return_value=mock_sync,
    ):

        read_result = (
            register_words_or_exception
            if isinstance(register_words_or_exception, Exception)
            else ReadResult(register_words_or_exception)
        )
        mock_sync.read_coils.return_value = read_result
        mock_sync.read_discrete_inputs.return_value = read_result
        mock_sync.read_input_registers.return_value = read_result
        mock_sync.read_holding_registers.return_value = read_result

        # mock timer and add old/new config
        now = dt_util.utcnow()
        with mock.patch("homeassistant.helpers.event.dt_util.utcnow", return_value=now):
            if method_discovery and config_device is not None:
                # setup modbus which in turn does setup for the devices
                config_modbus[DOMAIN].update(
                    {array_name_discovery: [{**config_device}]}
                )
                config_device = None
            assert await async_setup_component(hass, DOMAIN, config_modbus)
            await hass.async_block_till_done()

            # setup platform old style
            if config_device is not None:
                config_device = {
                    entity_domain: {
                        CONF_PLATFORM: DOMAIN,
                        array_name_old_config: [
                            {
                                **config_device,
                            }
                        ],
                    }
                }
                if scan_interval is not None:
                    config_device[entity_domain][CONF_SCAN_INTERVAL] = scan_interval
                assert await async_setup_component(hass, entity_domain, config_device)
                await hass.async_block_till_done()

        assert DOMAIN in hass.data
        if config_device is not None:
            entity_id = f"{entity_domain}.{device_name}"
            device = hass.states.get(entity_id)

            if expect_init_to_fail:
                assert device is None
            elif device is None:
                pytest.fail("CONFIG failed, see output")
        if check_config_only:
            return

        # Trigger update call with time_changed event
        now = now + timedelta(seconds=scan_interval + 60)
        with mock.patch("homeassistant.helpers.event.dt_util.utcnow", return_value=now):
            async_fire_time_changed(hass, now)
            await hass.async_block_till_done()

        entity_id = f"{entity_domain}.{device_name}"
        return hass.states.get(entity_id).state


async def base_config_test(
    hass,
    config_device,
    device_name,
    entity_domain,
    array_name_discovery,
    array_name_old_config,
    method_discovery=False,
    config_modbus=None,
    expect_init_to_fail=False,
):
    """Check config of device for given config."""

    await base_test(
        hass,
        config_device,
        device_name,
        entity_domain,
        array_name_discovery,
        array_name_old_config,
        None,
        None,
        method_discovery=method_discovery,
        check_config_only=True,
        config_modbus=config_modbus,
        expect_init_to_fail=expect_init_to_fail,
    )
