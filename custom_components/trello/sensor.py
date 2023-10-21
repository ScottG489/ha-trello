"""Platform for sensor integration."""
from __future__ import annotations

from trello import TrelloClient

from homeassistant.components import webhook
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from aiohttp import web

from .const import DOMAIN
from .const import DOMAIN, LOGGER, Board, List
from .coordinator import TrelloDataUpdateCoordinator


class TrelloSensor(CoordinatorEntity[TrelloDataUpdateCoordinator], SensorEntity):
    """Representation of a TrelloSensor."""

    _attr_native_unit_of_measurement = "Cards"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True

    def __init__(
        self,
        board: Board,
        list_: List,
        coordinator: TrelloDataUpdateCoordinator,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self.board = board
        self.list_id = list_.id
        self._attr_unique_id = f"list_{list_.id}".lower()
        self._attr_name = list_.name

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, board.id)},
            name=board.name,
            entry_type=DeviceEntryType.SERVICE,
            manufacturer="Trello",
            model="Board",
        )

    @property
    def available(self) -> bool:
        """Determine if sensor is available."""
        board = self.coordinator.data[self.board.id]
        list_id = board.lists.get(self.list_id)
        return bool(board.lists and list_id)

    @property
    def native_value(self) -> int | None:
        """Return the card count of the sensor's list."""
        return self.coordinator.data[self.board.id].lists[self.list_id].card_count

    @property
    def extra_state_attributes(self):
        """Return state attributes."""
        return {
            "list_id": self.list_id
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        if self.available:
            board = self.coordinator.data[self.board.id]
            self._attr_name = board.lists[self.list_id].name
            self.async_write_ha_state()
        super()._handle_coordinator_update()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up trello sensors for config entries."""
    trello_coordinator: TrelloDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    trello_client = TrelloClient(
        api_key=config_entry.data["api_key"], api_secret=config_entry.data["api_token"]
    )
    boards = trello_coordinator.data.values()

    # webhook_id = webhook.async_generate_id()
    # webhook_callback_url = webhook.async_generate_url(hass, webhook_id)
    # await hass.async_add_executor_job(create_trello_webhooks, webhook_callback_url, boards, trello_client)

    # webhook.async_register(
    #     hass, DOMAIN, "Trello", webhook_id, async_handle_webhook
    # )

    async_add_entities(
        [
            TrelloSensor(board, list_, trello_coordinator)
            for board in boards
            for list_ in board.lists.values()
        ],
        True,
    )


async def async_handle_webhook(hass: HomeAssistant, webhook_id: str, request: web.Request):
    body = await request.json()
    return web.Response(status=web.HTTPNoContent.status_code)


def create_trello_webhooks(webhook_url, boards, trello_client):
    for board in boards.values():
        try:
            trello_client.create_hook(callback_url=webhook_url, id_model=board['id'], desc=f"Webhook for '{board['name']}' board.")
        except Exception as ex:
            LOGGER.error(ex)
