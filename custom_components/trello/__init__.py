"""The Trello integration."""
from __future__ import annotations

from trello import Member, TrelloClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_API_TOKEN, Platform
from homeassistant.core import HomeAssistant, ServiceCall
import voluptuous as vol

from custom_components.trello.const import DOMAIN
from .const import CONF_BOARD_IDS, DOMAIN
from .coordinator import TrelloDataUpdateCoordinator

PLATFORMS: list[str] = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await register_services(hass)

    return True


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


async def register_services(hass):
    async def add_card(call: ServiceCall) -> None:
        """Service call to add a card to a list."""
        adapter = await get_trello_adapter(hass.config_entries.async_get_entry(call.data['account']))

        list_id = hass.states.get(call.data['list_entity_id']).attributes['list_id']
        card_name = call.data['name']

        await hass.async_add_executor_job(adapter.add_card, list_id, card_name)

    async def update_card(call: ServiceCall) -> None:
        """Service call to add a card to a list."""
        adapter = await get_trello_adapter(hass.config_entries.async_get_entry(call.data['account']))

        list_id = hass.states.get(call.data['list_entity_id']).attributes['list_id']
        card_name = call.data['name']

        target_list_id = None
        if target_list_entity_id := call.data.get('target_list_entity_id'):
            target_list_id = hass.states.get(target_list_entity_id).attributes['list_id']
        target_card_name = call.data.get('target_name')

        await hass.async_add_executor_job(adapter.update_card, list_id, card_name, target_list_id, target_card_name)

    async def delete_card(call: ServiceCall) -> None:
        """Service call to delete a card in a list."""
        adapter = await get_trello_adapter(hass.config_entries.async_get_entry(call.data['account']))

        list_id = hass.states.get(call.data['list_entity_id']).attributes['list_id']
        card_name = call.data['name']

        await hass.async_add_executor_job(adapter.delete_card, list_id, card_name)

    hass.services.async_register(
        DOMAIN, 'add_card', add_card, schema=vol.Schema(
            {
                vol.Required('account'): str,
                vol.Required('name'): str,
                vol.Required('list_entity_id'): str
            }
        )
    )
    hass.services.async_register(
        DOMAIN, 'update_card', update_card, schema=vol.Schema(
            {
                vol.Required('account'): str,
                vol.Required('name'): str,
                vol.Required('list_entity_id'): str,
                vol.Optional('target_list_entity_id'): str,
                vol.Optional('target_name'): str,
            }
        )
    )
    hass.services.async_register(
        DOMAIN, 'delete_card', delete_card, schema=vol.Schema(
            {
                vol.Required('account'): str,
                vol.Required('name'): str,
                vol.Required('list_entity_id'): str
            }
        )
    )


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

    def add_card(self, list_id, name):
        self.client.get_list(list_id).add_card(name)

    def update_card(self, list_id, name, target_list_id, target_name):
        for card in self.client.get_list(list_id).list_cards():
            if card.name == name:
                if target_list_id:
                    card.change_list(target_list_id)
                if target_name:
                    card.set_name(target_name)
                return

    def delete_card(self, list_id, card_name):
        for card in self.client.get_list(list_id).list_cards():
            if card.name == card_name:
                card.delete()
                return


async def get_trello_adapter(account_config_entry):
    config_data = account_config_entry.data
    trello_client = TrelloClient(
        api_key=config_data["api_key"], api_secret=config_data["api_token"]
    )
    return TrelloAdapter(trello_client)


def _is_success(response: dict) -> bool:
    return "200" in response
