"""Configure tests for the Trello integration."""
from collections.abc import Awaitable, Callable, Coroutine
import json
from typing import Any
from unittest.mock import patch

import pytest

from custom_components.trello.const import DOMAIN
from homeassistant.const import CONF_API_KEY, CONF_API_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import MockConfigEntry, load_fixture


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


ComponentSetup = Callable[[], Awaitable[None]]

CONF_USER_ID = "user_id"
CONF_USER_EMAIL = "user_email"
CONF_BOARD_IDS = "board_ids"


def mock_fetch_json(path="batch.json"):
    """Mock response from Trello client."""
    return json.loads(load_fixture(path))


@pytest.fixture(name="setup_integration")
async def mock_setup_integration(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> Callable[[], Coroutine[Any, Any, None]]:
    """Mock a config entry then set up the component."""
    config_entry.add_to_hass(hass)

    async def func() -> None:
        with patch(
            "custom_components.trello.TrelloClient.fetch_json",
            return_value=mock_fetch_json("batch.json"),
        ):
            assert await async_setup_component(hass, DOMAIN, {})
            await hass.async_block_till_done()

    return func


@pytest.fixture(name="config_entry")
def mock_config_entry() -> MockConfigEntry:
    """Fixture to set the oauth token expiration time."""
    return MockConfigEntry(
        domain="trello",
        title="foo@example.com",
        data={
            CONF_API_KEY: "abc123",
            CONF_API_TOKEN: "123abc",
            CONF_USER_ID: "12345",
            CONF_USER_EMAIL: "foo@example.com",
        },
        options={
            CONF_BOARD_IDS: [
                "3a634d47a4cb1e9a9886a2e3",
                "bea542e091bc1bfe5e780c8f",
                "0c6646739c3a12b1bf3dfd3a",
            ]
        },
    )
