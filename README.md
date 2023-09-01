# ha-trello-ext
![maintenance-status](https://img.shields.io/badge/maintenance-active-brightgreen)

Trello integration for Home Assistant.

## Features
- Sensors to track the number of cards in the lists on any Trello board.

### Planned features
- Services for creating, updating, and deleting cards, lists, and boards.
- OAuth support ([as soon as Trello adds support for OAuth2](https://developer.atlassian.com/cloud/trello/guides/rest-api/authorization/#using-basic-oauth))
- Moving to a push model rather than polling for improved responsiveness.
- [Anything you'd like to request that this integration doesn't do!](https://github.com/ScottG489/ha-trello-ext/issues/new?assignees=&labels=Feature%2BRequest&projects=&template=feature_request.yaml)



## Installation
First add this repository [as a custom repository](https://hacs.xyz/docs/faq/custom_repositories/).

### Setup
#### Prerequisites

Before setting up this integration, you need to get credentials by creating an Integration in Trello's
[Power-Up Admin Portal](https://trello.com/power-ups/admin/).

<details>
<summary><strong>Create Integration and associated API key and Token</strong></summary>

1. Ensure you're logged in to [Trello](https://trello.com/) in your browser.
2. Visit the [Power-Up Admin Portal](https://trello.com/power-ups/admin/) and select **New** near the top right.
3. Fill out all fields except the **Iframe connector URL**.
4. Select **Create** near the bottom right.
5. You should be taken to the **API key** page. Select **Generate a new API key** and select **Generate API key** if a
   dialog pops up.
6. Record the **API key** at the top of the page. *This will be the first of two credentials you'll need.*
7. At the end of the paragraph to the right of your **API key**, select the **Token** link to "... manually generate a Token."
8. You should be taken to a page with text at the top saying **"Would you like to give the following application access to your account?"**.
   Select the **"Allow"** button near the bottom right of the page.
9. On the following page, record your **Token**. *This will be the last credential you'll need.*
</details>

After you have both your **API Key** and **Token** you can start the integration setup.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=trello)

## Development
Run the following to set up your development environment
```shell
python3 -m venv venv
pip3 install -r requirements_test.txt
source venv/bin/activate
```
To run Home Assistant with this integration loaded:
```shell
hass -c config
```
### Testing
To run unit tests with coverage:
```shell
pytest tests --cov=custom_components.trello --cov-report term-missing
```
