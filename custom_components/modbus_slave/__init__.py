"""Support for Modbus."""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    DEVICE_CLASSES_SCHEMA as BINARY_SENSOR_DEVICE_CLASSES_SCHEMA,
)
from homeassistant.components.cover import (
    DEVICE_CLASSES_SCHEMA as COVER_DEVICE_CLASSES_SCHEMA,
)
from homeassistant.components.modbus import (
    MODBUS_SCHEMA,
    SERIAL_SCHEMA,
    SERVICE_WRITE_COIL_SCHEMA,
    SERVICE_WRITE_REGISTER_SCHEMA,
)
from homeassistant.components.sensor import (
    DEVICE_CLASSES_SCHEMA as SENSOR_DEVICE_CLASSES_SCHEMA,
)
from homeassistant.components.switch import (
    DEVICE_CLASSES_SCHEMA as SWITCH_DEVICE_CLASSES_SCHEMA,
)
from homeassistant.const import (
    CONF_ADDRESS,
    CONF_BINARY_SENSORS,
    CONF_COMMAND_OFF,
    CONF_COMMAND_ON,
    CONF_COUNT,
    CONF_COVERS,
    CONF_DELAY,
    CONF_DEVICE_CLASS,
    CONF_HOST,
    CONF_METHOD,
    CONF_NAME,
    CONF_OFFSET,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SENSORS,
    CONF_SLAVE,
    CONF_STRUCTURE,
    CONF_SWITCHES,
    CONF_TEMPERATURE_UNIT,
    CONF_TIMEOUT,
    CONF_TYPE,
    CONF_UNIT_OF_MEASUREMENT,
)
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import (
    ATTR_ADDRESS,
    ATTR_HUB,
    ATTR_STATE,
    ATTR_UNIT,
    ATTR_VALUE,
    CALL_TYPE_COIL,
    CALL_TYPE_DISCRETE,
    CALL_TYPE_REGISTER_HOLDING,
    CALL_TYPE_REGISTER_INPUT,
    CONF_BAUDRATE,
    CONF_BIT_NUMBER,
    CONF_BIT_SENSORS,
    CONF_BIT_SWITCHES,
    CONF_BYTESIZE,
    CONF_CLIMATES,
    CONF_COMMAND_BIT_NUMBER,
    CONF_CURRENT_TEMP,
    CONF_CURRENT_TEMP_REGISTER_TYPE,
    CONF_DATA_COUNT,
    CONF_DATA_TYPE,
    CONF_INPUT_TYPE,
    CONF_MAX_TEMP,
    CONF_MIN_TEMP,
    CONF_PARITY,
    CONF_PRECISION,
    CONF_REGISTER,
    CONF_REVERSE_ORDER,
    CONF_SCALE,
    CONF_STATE_CLOSED,
    CONF_STATE_CLOSING,
    CONF_STATE_OFF,
    CONF_STATE_ON,
    CONF_STATE_OPEN,
    CONF_STATE_OPENING,
    CONF_STATUS_BIT_NUMBER,
    CONF_STATUS_REGISTER,
    CONF_STATUS_REGISTER_TYPE,
    CONF_STEP,
    CONF_STOPBITS,
    CONF_TARGET_TEMP,
    CONF_VERIFY_REGISTER,
    CONF_VERIFY_STATE,
    DATA_TYPE_CUSTOM,
    DATA_TYPE_FLOAT,
    DATA_TYPE_INT,
    DATA_TYPE_STRING,
    DATA_TYPE_UINT,
    DEFAULT_HUB,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_STRUCTURE_PREFIX,
    DEFAULT_TEMP_UNIT,
    MODBUS_DOMAIN as DOMAIN,
)
from .modbus import modbus_setup

BASE_SCHEMA = vol.Schema({vol.Optional(CONF_NAME, default=DEFAULT_HUB): cv.string})


def number(value: Any) -> int | float:
    """Coerce a value to number without losing precision."""
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value

    try:
        value = int(value)
        return value
    except (TypeError, ValueError):
        pass
    try:
        value = float(value)
        return value
    except (TypeError, ValueError) as err:
        raise vol.Invalid(f"invalid number {value}") from err


BASE_COMPONENT_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_SLAVE): cv.positive_int,
        vol.Optional(
            CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
        ): cv.positive_int,
    }
)


CLIMATE_SCHEMA = BASE_COMPONENT_SCHEMA.extend(
    {
        vol.Required(CONF_CURRENT_TEMP): cv.positive_int,
        vol.Required(CONF_TARGET_TEMP): cv.positive_int,
        vol.Optional(CONF_DATA_COUNT, default=2): cv.positive_int,
        vol.Optional(
            CONF_CURRENT_TEMP_REGISTER_TYPE, default=CALL_TYPE_REGISTER_HOLDING
        ): vol.In([CALL_TYPE_REGISTER_HOLDING, CALL_TYPE_REGISTER_INPUT]),
        vol.Optional(CONF_DATA_TYPE, default=DATA_TYPE_FLOAT): vol.In(
            [DATA_TYPE_INT, DATA_TYPE_UINT, DATA_TYPE_FLOAT, DATA_TYPE_CUSTOM]
        ),
        vol.Optional(CONF_PRECISION, default=1): cv.positive_int,
        vol.Optional(CONF_SCALE, default=1): vol.Coerce(float),
        vol.Optional(CONF_OFFSET, default=0): vol.Coerce(float),
        vol.Optional(CONF_MAX_TEMP, default=35): cv.positive_int,
        vol.Optional(CONF_MIN_TEMP, default=5): cv.positive_int,
        vol.Optional(CONF_STEP, default=0.5): vol.Coerce(float),
        vol.Optional(CONF_STRUCTURE, default=DEFAULT_STRUCTURE_PREFIX): cv.string,
        vol.Optional(CONF_TEMPERATURE_UNIT, default=DEFAULT_TEMP_UNIT): cv.string,
    }
)

COVERS_SCHEMA = vol.All(
    cv.has_at_least_one_key(CALL_TYPE_COIL, CONF_REGISTER),
    BASE_COMPONENT_SCHEMA.extend(
        {
            vol.Optional(CONF_DEVICE_CLASS): COVER_DEVICE_CLASSES_SCHEMA,
            vol.Optional(CONF_STATE_CLOSED, default=0): cv.positive_int,
            vol.Optional(CONF_STATE_CLOSING, default=3): cv.positive_int,
            vol.Optional(CONF_STATE_OPEN, default=1): cv.positive_int,
            vol.Optional(CONF_STATE_OPENING, default=2): cv.positive_int,
            vol.Optional(CONF_STATUS_REGISTER): cv.positive_int,
            vol.Optional(
                CONF_STATUS_REGISTER_TYPE,
                default=CALL_TYPE_REGISTER_HOLDING,
            ): vol.In([CALL_TYPE_REGISTER_HOLDING, CALL_TYPE_REGISTER_INPUT]),
            vol.Exclusive(CALL_TYPE_COIL, CONF_INPUT_TYPE): cv.positive_int,
            vol.Exclusive(CONF_REGISTER, CONF_INPUT_TYPE): cv.positive_int,
        }
    ),
)

SWITCH_SCHEMA = BASE_COMPONENT_SCHEMA.extend(
    {
        vol.Required(CONF_ADDRESS): cv.positive_int,
        vol.Optional(CONF_DEVICE_CLASS): SWITCH_DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_INPUT_TYPE, default=CALL_TYPE_REGISTER_HOLDING): vol.In(
            [CALL_TYPE_REGISTER_HOLDING, CALL_TYPE_REGISTER_INPUT, CALL_TYPE_COIL]
        ),
        vol.Optional(CONF_COMMAND_OFF, default=0x00): cv.positive_int,
        vol.Optional(CONF_COMMAND_ON, default=0x01): cv.positive_int,
        vol.Optional(CONF_STATE_OFF): cv.positive_int,
        vol.Optional(CONF_STATE_ON): cv.positive_int,
        vol.Optional(CONF_VERIFY_REGISTER): cv.positive_int,
        vol.Optional(CONF_VERIFY_STATE, default=True): cv.boolean,
    }
)

BIT_SWITCH_SCHEMA = BASE_COMPONENT_SCHEMA.extend(
    {
        vol.Required(CONF_ADDRESS): cv.positive_int,
        vol.Required(CONF_COMMAND_BIT_NUMBER): cv.positive_int,
        vol.Optional(CONF_STATUS_BIT_NUMBER): cv.positive_int,
        vol.Optional(CONF_DEVICE_CLASS): SWITCH_DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_INPUT_TYPE, default=CALL_TYPE_REGISTER_HOLDING): vol.In(
            [CALL_TYPE_REGISTER_HOLDING, CALL_TYPE_REGISTER_INPUT]
        ),
        vol.Optional(CONF_VERIFY_REGISTER): cv.positive_int,
        vol.Optional(CONF_VERIFY_STATE, default=True): cv.boolean,
    }
)


SENSOR_SCHEMA = BASE_COMPONENT_SCHEMA.extend(
    {
        vol.Required(CONF_ADDRESS): cv.positive_int,
        vol.Optional(CONF_COUNT, default=1): cv.positive_int,
        vol.Optional(CONF_DATA_TYPE, default=DATA_TYPE_INT): vol.In(
            [
                DATA_TYPE_INT,
                DATA_TYPE_UINT,
                DATA_TYPE_FLOAT,
                DATA_TYPE_STRING,
                DATA_TYPE_CUSTOM,
            ]
        ),
        vol.Optional(CONF_DEVICE_CLASS): SENSOR_DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_OFFSET, default=0): number,
        vol.Optional(CONF_PRECISION, default=0): cv.positive_int,
        vol.Optional(CONF_INPUT_TYPE, default=CALL_TYPE_REGISTER_HOLDING): vol.In(
            [CALL_TYPE_REGISTER_HOLDING, CALL_TYPE_REGISTER_INPUT]
        ),
        vol.Optional(CONF_REVERSE_ORDER, default=False): cv.boolean,
        vol.Optional(CONF_SCALE, default=1): number,
        vol.Optional(CONF_STRUCTURE): cv.string,
        vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
    }
)

BIT_SENSOR_SCHEMA = BASE_COMPONENT_SCHEMA.extend(
    {
        vol.Required(CONF_ADDRESS): cv.positive_int,
        vol.Required(CONF_BIT_NUMBER): cv.positive_int,
        vol.Optional(CONF_COUNT, default=1): cv.positive_int,
        vol.Optional(CONF_DEVICE_CLASS): SENSOR_DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_INPUT_TYPE, default=CALL_TYPE_REGISTER_HOLDING): vol.In(
            [CALL_TYPE_REGISTER_HOLDING, CALL_TYPE_REGISTER_INPUT]
        ),
    }
)

BINARY_SENSOR_SCHEMA = BASE_COMPONENT_SCHEMA.extend(
    {
        vol.Required(CONF_ADDRESS): cv.positive_int,
        vol.Optional(CONF_DEVICE_CLASS): BINARY_SENSOR_DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_INPUT_TYPE, default=CALL_TYPE_COIL): vol.In(
            [CALL_TYPE_COIL, CALL_TYPE_DISCRETE]
        ),
    }
)

MODBUS_SLAVE_SCHEMA = MODBUS_SCHEMA.extend(
    {
        vol.Optional(CONF_BIT_SENSORS): vol.All(cv.ensure_list, [BIT_SENSOR_SCHEMA]),
        vol.Optional(CONF_BIT_SWITCHES): vol.All(cv.ensure_list, [BIT_SWITCH_SCHEMA]),
    }
)

ETHERNET_SCHEMA = MODBUS_SLAVE_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT): cv.port,
        vol.Required(CONF_TYPE): vol.Any("tcp", "udp", "rtuovertcp"),
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            cv.ensure_list,
            [
                vol.Any(SERIAL_SCHEMA, ETHERNET_SCHEMA),
            ],
        ),
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(hass, config):
    """Set up Modbus component."""
    return modbus_setup(
        hass, config, SERVICE_WRITE_REGISTER_SCHEMA, SERVICE_WRITE_COIL_SCHEMA
    )



# 2021-04-28 10:45:37 DEBUG (SyncWorker_7) [custom_components.modbus_slave.modbus] Modbus Error: [Connection] Failed to connect[ModbusTcpClient(192.168.5.222:2020)]
# 2021-04-28 10:45:37 ERROR (MainThread) [homeassistant] Error doing job: Future exception was never retrieved
# Traceback (most recent call last):
#   File "/usr/local/lib/python3.9/concurrent/futures/thread.py", line 52, in run
#     result = self.fn(*self.args, **self.kwargs)
#   File "/config/custom_components/modbus_slave/bit_sensor.py", line 194, in <lambda>
#     self.hass, lambda arg: self._update(), self._scan_interval
#   File "/config/custom_components/modbus_slave/bit_sensor.py", line 220, in _update
#     self._value = bool(result.registers[register_index] & register_bit_mask)
# AttributeError: 'NoneType' object has no attribute 'registers'