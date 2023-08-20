"""The Trello integration."""
from typing import Any

from trello import Member, TrelloClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
import voluptuous as vol

from custom_components.trello_ext.const import DOMAIN
from .const import LOGGER

PLATFORMS: list[str] = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await register_services(hass)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
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

    def get_board_lists(
            self, id_boards: dict[str, dict[str, str]], selected_board_ids: list[str]
    ) -> dict[str, dict[str, Any]]:
        """Fetch lists for selected boards.

        :param id_boards: All boards
        :param selected_board_ids: Board IDs the user has selected
        :return: Selected boards populated with the IDs of their lists
        """
        sub_query_params = "fields=name"
        urls = ",".join(
            f"/boards/{board_id}/lists?{sub_query_params}"
            for board_id in selected_board_ids
        )

        batch_response = (
            self.client.fetch_json("batch", query_params={"urls": urls}) if urls else []
        )
        user_selected_boards = {}
        for i, board_lists_response in enumerate(batch_response):
            board = dict(id_boards[selected_board_ids[i]])
            if _is_success(board_lists_response):
                board["lists"] = board_lists_response["200"]
            else:
                LOGGER.error(
                    "Unable to fetch lists for board named '%s' with ID '%s'. Response was: %s)",
                    board["name"],
                    board["id"],
                    board_lists_response,
                )
                continue

            user_selected_boards[board["id"]] = board

        return user_selected_boards


async def get_trello_adapter(account_config_entry):
    config_data = account_config_entry.data
    trello_client = TrelloClient(
        api_key=config_data["api_key"], api_secret=config_data["api_token"]
    )
    return TrelloAdapter(trello_client)


def _is_success(response: dict) -> bool:
    return "200" in response
