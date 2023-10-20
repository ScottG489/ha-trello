"""Test the trello config flow."""
from datetime import timedelta
from unittest.mock import patch

from custom_components.trello.sensor import SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from pytest_homeassistant_custom_component.common import async_fire_time_changed
from .conftest import ComponentSetup, mock_fetch_json


async def test_sensor_setup_entry(
    hass: HomeAssistant, setup_integration: ComponentSetup
) -> None:
    """Test sensors are set up and updated as expected."""
    await setup_integration()

    all_states = hass.states.async_all()
    all_devices = hass.data["device_registry"].devices.data.values()

    assert len(all_states) == 3
    assert len(all_devices) == 2

    ideas_board_device = hass.data["device_registry"].async_get_device(
        {("trello", "bea542e091bc1bfe5e780c8f")}
    )
    goals_board_device = hass.data["device_registry"].async_get_device(
        {("trello", "3a634d47a4cb1e9a9886a2e3")}
    )

    assert ideas_board_device.name == "Ideas"
    assert goals_board_device.name == "Goals"

    ideas_planned = hass.states.get("sensor.ideas_planned")
    goals_to_do = hass.states.get("sensor.goals_to_do")
    goals_done = hass.states.get("sensor.goals_done")

    assert ideas_planned.state == "1"
    assert goals_to_do.state == "2"
    assert goals_done.state == "0"

    assert ideas_planned.attributes["friendly_name"] == "Ideas Planned"
    assert goals_to_do.attributes["friendly_name"] == "Goals To Do"
    assert goals_done.attributes["friendly_name"] == "Goals Done"

    for device in all_devices:
        assert device.manufacturer == "Trello"
        assert device.model == "Board"

    for entity in all_states:
        assert entity.attributes["state_class"] == SensorStateClass.MEASUREMENT
        assert entity.attributes["unit_of_measurement"] == "Cards"

    with patch(
        "custom_components.trello.TrelloClient.fetch_json",
        return_value=mock_fetch_json(path="update_batch_with_error.json"),
    ):
        future = dt_util.utcnow() + timedelta(seconds=60)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    ideas_planned = hass.states.get("sensor.ideas_planned")
    goals_to_do = hass.states.get("sensor.goals_to_do")
    goals_done = hass.states.get("sensor.goals_done")

    assert ideas_planned.state == "unavailable"
    assert goals_to_do.state == "1"
    assert goals_done.state == "1"
