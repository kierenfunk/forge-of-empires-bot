# Forge of Empires Bot
> Bot written in Python for automating various tasks in Forge of Empires

## Features

- Automatic login
- Collects and starts production buildings (supplies)
- Collects and starts good buildings (goods)
- Collects residential buildings (coins)
- Collects the silver from your tavern
- Sits in your friends tavern
- Collects hidden rewards
- Collects daily castle points and rewards
- Trains military units
- Polishes your friends / guild members / neighbours buildings

## To do

- Daily reward starting
- Automate Tavern Upgrades
- Allocate forge points over 5 to research
- Friends algorithm (Add and remove friends based on activity and goods produced)
- Trading algorithm (Balance inventory by trading)
- A guild expedition negotiation algorithm based on entropy and probability
- A path finding algorithm for research & progress in the game
- City builder/optimiser

## Get Started

### Requirements

- Python 3
- `pipenv`

### Installation

With `pipenv`
```bash
pipenv install --dev
pipenv shell
```

## Usage

First add username and password to `.env`
```bash
USERNAME=your-username
PASSWORD=your-password
```

### *Optional

If you want to run the bot and play the game at the same time, you will need to copy the sid cookie and gateway url into an environment variable.
```bash
GATEWAY_URL=https://en15.forgeofempires.com/game/json?h=xxxxxxxxxxxxxxxxxxxxxxxx
SID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Testing

For linting:
```bash
pipenv run lint
```

To run all tests
```bash
pytest --cov
```
