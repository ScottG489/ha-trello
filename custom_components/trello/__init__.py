"""The Trello integration."""
from __future__ import annotations

from trello import Member, TrelloClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_API_TOKEN, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_BOARD_IDS, DOMAIN
from .coordinator import TrelloDataUpdateCoordinator

PLATFORMS: list[str] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    config_boards = entry.options[CONF_BOARD_IDS]
    config_data = entry.data
    trello_client = TrelloClient(
        api_key=config_data[CONF_API_KEY],
        api_secret=config_data[CONF_API_TOKEN],
    )
    trello_coordinator = TrelloDataUpdateCoordinator(hass, trello_client, config_boards)
    await trello_coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = trello_coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_entry))

    return True


async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update a given config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of an entry."""
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


class TrelloAdapter:
    """Adapter for Trello lib's client."""

    def __init__(self, client: TrelloClient) -> None:
        """Initialize with Trello lib client."""
        self.client = client

    @classmethod
    def from_creds(cls, api_key: str, api_token: str) -> TrelloAdapter:
        """Initialize with API Key and API Token."""
        return cls(TrelloClient(api_key=api_key, api_secret=api_token))

    def get_member(self) -> Member:
        """Get member information."""
        return self.client.get_member("me")

    def get_boards(self) -> dict[str, dict[str, str]]:
        """Get all user's boards."""
        return {
            board.id: {"id": board.id, "name": board.name}
            for board in self.client.list_boards(board_filter="open")
        }
