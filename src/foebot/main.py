"""Foebot module

"""

from os import environ
import re
import hashlib
import json
import time
from datetime import datetime
import requests
from .queue import Queue


class FoeBotReload(Exception):
    """Raised when an invalid OLX refresh token is provided

    """

    def __init__(self, message):
        super().__init__(message)


class FoeBotExpiredSession(Exception):
    """Raised when sid or gateway url has expired

    """

    def __init__(self, message):
        super().__init__(message)


class FoeBotRewardNotAvailable(Exception):
    """Raised when reward is not available yet

    """

    def __init__(self, message):
        super().__init__(message)


def login():
    '''Login to forge of empires and retrieve mid cookie

    returns: mid token
    '''
    if 'SID' in environ and 'GATEWAY_URL' in environ:
        # MID token is not necessary if these environment variables are present
        return environ.get('MID', '')
    if "MID" in environ:
        return environ.get('MID')

    session = requests.Session()
    # necessary to get xsrf token
    session.get('https://en.forgeofempires.com/glps/iframe-login')

    # complete login check
    response = session.post('https://en.forgeofempires.com/glps/login_check', headers={
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'x-requested-with': 'XMLHttpRequest',
        'x-xsrf-token': session.cookies.get_dict()['XSRF-TOKEN'],
    },
        data={
        'login[userid]': environ.get("USERNAME"),
        'login[password]': environ.get("PASSWORD"),
        'login[remember_me]': 'false'
    })

    # get login url with token
    response = session.get('https://en.forgeofempires.com/glps/iframe-login')
    login_url = response.text[len(
        "<script>window.top.location.href = \""):-len("\";</script>")]

    # login
    response = session.get(login_url)

    # return mid cookie
    return session.cookies.get_dict()['mid']


def start_game(mid_token):
    '''Choose world, get sid cookie and gateway url

    returns: sid token, gateway url
    '''

    if 'SID' in environ and 'GATEWAY_URL' in environ:
        return environ.get('SID'), environ.get('GATEWAY_URL')

    # get all worlds
    worlds = requests.post('https://en0.forgeofempires.com/start/index?action=fetch_worlds_for_login_page', headers={
        'cookie': f'mid={mid_token}',
        'x-requested-with': 'XMLHttpRequest'
    }).json()

    # currently only chooses the first world
    world = list(worlds['player_worlds'].keys())[0]

    # init
    play_now = requests.post('https://en0.forgeofempires.com/start/index?action=play_now_login', headers={
        'cookie': f'mid={mid_token}',
        'x-requested-with': 'XMLHttpRequest'
    }, data={"json": f"%7B%22world_id%22%3A%22{world}%22%7D"}).json()

    # get sid token
    session = requests.Session()
    response = session.get(play_now['login_url'])
    print(response.text)

    # get gateway url from response
    gateway_url = re.findall(r'gatewayUrl: \'([\S]*)\',', response.text)[0]

    return session.cookies.get_dict()['sid'], gateway_url


def get_secret():
    '''Retrieve FOE Secret from game source code

    '''
    response = requests.get('https://foeen.innogamescdn.com/cache/ForgeHX-3a368f34.js')
    print(response)
    secrets = re.findall(r'this\.\_signatureHash\+\"[A-Z\=0-9a-z]{88}\"', response.text)
    if len(secrets) > 0:
        secret = secrets[0]
    else:
        raise Exception('No secret found')
    return secret[24:-1]

def sig(payload, user_key, foe_secret):
    '''Generate sigature required for FOE requests signature header
    CONCEPT FROM: https://github.com/m3talstorm/foe-decryption

    payload: request payload
    user_key: parameter key from gateway url

    returns: signature
    '''

    data = user_key + foe_secret + payload
    signature = hashlib.md5(data.encode('utf-8')).hexdigest()[1:11]
    return signature


def req(body, state):
    '''Request wrapper, handles all requests to FOE

    body: Request body generated by make_request_body()
    state: contains gateway_url and sid_token

    returns: requests response body in json format
    '''
    gateway_url = state['gateway_url']
    user_key = gateway_url.split('?h=')[1]
    payload = json.dumps(body).replace(' ', '')
    response = requests.post(gateway_url, headers={
        'cookie': f"sid={state['sid_token']}",
        'signature': sig(payload, user_key, state['foe_secret']),
    }, data=payload).json()
    return response


def create_queue_item(request_class, request_method, request_data=None, task_time=0):
    '''Wrapper for creating queue items

    '''

    return {
        "requestClass": request_class,
        "requestMethod": request_method,
        "requestData": [] if request_data is None else request_data,
        "time": task_time,
    }


def handle_entities(entities):
    '''Handles all producing buildings and creates appropriate queue tasks for each case

    '''
    queue_items = []
    for entity in entities:
        state_class = entity['state']['__class__']
        if state_class == 'ProducingState':
            # pickup resources after certain time period
            queue_items.append(create_queue_item("CityProductionService", "pickupProduction", [
                               [entity['id']]], entity['state']['next_state_transition_at'] + 1))
        elif state_class == 'ProductionFinishedState':
            # pickup resources immediately
            queue_items.append(create_queue_item(
                "CityProductionService", "pickupProduction", [[entity['id']]]))
        elif state_class == 'IdleState' and entity['type'] in set(['production', 'goods', 'cultural_goods_production', 'diplomacy']):
            if entity['type'] == 'diplomacy' and entity['cityentity_id'] != 'J_Vikings_Diplomacy4':
                # only certain types of diplomacy buildings in cultural settings can be production
                continue
            # start production immediately
            queue_items.append(create_queue_item(
                "CityProductionService", "startProduction", [entity['id'], 1]))
        elif state_class == 'IdleState' and entity['type'] in set(['military']):
            # train new military units
            units = [unit for unit in entity['unitSlots']
                     if 'unlocked' in unit and unit['unlocked'] and unit['unit_id'] == -1]
            if len(units) > 0:
                queue_items.append(create_queue_item("CityProductionService", "startProduction", [
                                   entity['id'], units[0]['nr'] if 'nr' in units[0] else 0], 0))
        elif state_class == 'ConstructionState' and entity['type'] in set(['production', 'goods', 'cultural_goods_production', 'diplomacy']):
            # start production after building has finished production
            queue_items.append(create_queue_item("CityProductionService", "startProduction", [
                               entity['id'], 1], entity['state']['next_state_transition_at'] + 1))
    return queue_items


def execute_task(task, state):
    '''Task executor
    makes the request, handles the response and returns the state and new queue items

    '''
    body = make_request_body(
        task["requestClass"], task["requestMethod"], task['requestData'])
    response = req(body, state)
    return handle_response(response, state, task)


def update_state(response, prev_state):
    '''Wrapper for handling state updates

    '''
    # new state instance
    new_state = dict(prev_state.items())

    for data in response:
        # refresh state
        if data['requestMethod'] == 'getPlayerResources' and data['requestClass'] == 'ResourceService':
            # get resources
            resources = data['responseData']['resources']
            new_state = {
                **new_state,
                'money': resources['money'],
                'forge_points': resources['strategy_points'],
                'supplies': resources['supplies'],
                'population': resources['population'],
                'total_population': resources['total_population'],
            }
        elif data['requestMethod'] == 'getData' and data['requestClass'] == 'StartupService':
            # get user data
            new_state = {**new_state, 'player_id': data['responseData']['user_data']['player_id']}

    return new_state


def check_response_errors(response, request):
    '''Check response body for possible errors and raise appropriate exceptions

    '''
    for data in response:
        # check for errors and raise Exceptions if necessary
        if '__class__' in data and data['__class__'] == 'Redirect':
            # session most probably has expired
            raise FoeBotExpiredSession(data['message'])

        if data['requestMethod'] == request['requestMethod'] and data['requestClass'] == request['requestClass']:
            if "__class__" in data['responseData'] and data['responseData']['__class__'] == "Error":
                # reload if service returns an Error
                raise FoeBotReload(data['responseData']['message'])
        elif data['requestMethod'] == 'collectReward' and data['requestClass'] == 'HiddenRewardService':
            if data['responseData']['__class__'] == "Error":
                if data['responseData']['message'] == 'This reward is not available anymore':
                    raise FoeBotRewardNotAvailable(
                        data['responseData']['message'])
                raise FoeBotReload(data['responseData']['message'])


def handle_tavern_response(data, player_id):
    '''Handle response after checking tavern for new rewards

    '''
    result = []
    if data[0] == player_id:
        # if tavern is own tavern

        # log
        print(
            datetime.now(),
            f"Tavern Status: {data[2]} seats filled out of a possible {data[1]}"
        )
        if data[1] == data[2]:
            # if chairs taken matches number of total chairs, collect reward
            result.append(create_queue_item("FriendsTavernService", "collectReward", 0))
        # check again in 5 minutes
        result.append(create_queue_item(
            'FriendsTavernService',
            'getSittingPlayersCount',
            task_time=int(datetime.now().timestamp()) + 5 * 60
        ))
    return result


def handle_social_list(data):
    '''Create queue tasks from list of friends, neighbours and guild members

    '''
    players = data['friends'] + data['neighbours'] + data['guildMembers']
    players = [player for player in players
               if 'is_self' not in player and ('is_friend' in player or 'is_guild_member' in player or 'is_neighbor' in player)]

    # filter duplicate players
    player_id_set = set()
    unique_players = []
    for player in players:
        if player['player_id'] not in player_id_set:
            player_id_set.add(player['player_id'])
            unique_players.append(player)

    result = [create_queue_item(
        "OtherPlayerService",
        "polivateRandomBuilding",
        [player['player_id']],
        int(datetime.now().timestamp(
        )) + player['next_interaction_in'] + 1 if 'next_interaction_in' in player else 0
    ) for player in unique_players]

    return result


def handle_response(response, state, request):
    '''Response handler, handles everything returned from FOE

    '''
    check_response_errors(response, request)

    # first update state
    state = update_state(response, state)

    # parse two, create queue items
    queue_items = []
    for data in response:

        if data['requestMethod'] == 'getSittingPlayersCount' and data['requestClass'] == 'FriendsTavernService':
            # Check tavern for rewards
            queue_items.extend(
                handle_tavern_response(data['responseData'], state['player_id'])
            )

        elif data['requestMethod'] == "getCityMap" and data['requestClass'] == "CityMapService" and 'gridId' in data['responseData'] and data['responseData']['gridId'] == 'cultural_outpost':
            queue_items.extend(handle_entities(data['responseData']['entities']))
        elif data['requestMethod'] == 'getOverview' and data['requestClass'] == 'CastleSystemService':
            # collect castle rewards
            queue_items.append(create_queue_item("CastleSystemService", "collectDailyReward",
                               task_time=data['responseData']['dailyRewardCollectionAvailableAt']))
            queue_items.append(create_queue_item("CastleSystemService", "collectDailyPoints",
                               task_time=data['responseData']['dailyPointsCollectionAvailableAt']))

        elif data['requestMethod'] in set(['startProduction', "pickupProduction"]) and data['requestClass'] == "CityProductionService":
            # handle city buildings collection and production
            queue_items.extend(handle_entities(data['responseData']['updatedEntities']))

        elif data['requestMethod'] == 'getData' and data['requestClass'] == 'StartupService':
            # handle city buildings collection and production at startup
            entity_types = set(['residential', 'main_building',
                               'production', 'goods', 'greatbuilding', 'military'])
            queue_items.extend(handle_entities(
                [ent for ent in data['responseData']['city_map']
                    ['entities'] if ent['type'] in entity_types]
            ))

        elif data['requestMethod'] == "updatePlayer" and data['requestClass'] == "OtherPlayerService":
            # update player, after aid
            queue_items.extend([create_queue_item(
                "OtherPlayerService",
                "polivateRandomBuilding",
                [player['player_id']],
                int(datetime.now().timestamp()) + player['next_interaction_in'] + 1 if 'next_interaction_in' in player else 0
            ) for player in data['responseData']])

        elif data['requestMethod'] == "getSocialList" and data['requestClass'] == "OtherPlayerService":
            # auto aid friends, neighbours and guild members
            queue_items.extend(handle_social_list(data['responseData']))

        elif data['requestMethod'] == "getOtherTavernStates" and data['requestClass'] == "FriendsTavernService":
            # visit other players taverns

            # Players must satisfy the following condition:
            #   1. must be friend (notFriend)
            #   2. must have a chair available in their tavern (noChair)
            #   3. Must not already be sitting in their tavern (isSitting)
            #   4. Must have a tavern (notUnlocked)
            excluded_players = set(['notFriend', 'noChair', 'isSitting', 'notUnlocked'])
            players = [player for player in data['responseData'] if not ('state' in player and player['state'] in excluded_players)]

            queue_items.extend([
                create_queue_item(
                    "FriendsTavernService",
                    "getOtherTavern",
                    [player['ownerId']],
                    player['nextVisitTime'] + 1 if 'nextVisitTime' in player else 0
                ) for player in players])

        elif data['requestMethod'] == 'collectReward' and data['requestClass'] == 'RewardService':
            response_data = data['responseData'][0][0]
            print(datetime.now(), 'REWARD: ',
                  response_data['description'], 'Collected:', response_data['name'])

        elif data['requestMethod'] == 'getOverview' and data['requestClass'] == 'HiddenRewardService':
            # find new rewards

            # filter expired rewards
            rewards = [reward for reward in data['responseData']['hiddenRewards'] if reward['expireTime'] > int(datetime.now().timestamp())]

            # collect reward tasks
            queue_items.extend([
                create_queue_item("HiddenRewardService", "collectReward", [reward['hiddenRewardId']], reward['startTime'])
                for reward in rewards
            ])
            # check for new rewards in one hour
            queue_items.append(create_queue_item("HiddenRewardService", "getOverview", task_time=int(datetime.now().timestamp()) + (60 * 60)))

    return state, queue_items


def make_request_body(request_class, request_method, request_data=None):
    '''Wrapper for request payloads to FOE

    '''
    return [
        {
            "__class__": "ServerRequest",
            "requestData": [] if request_data is None else request_data,
            "requestClass": request_class,
            "requestMethod": request_method,
            "requestId": 0
        }
    ]


def init_game(sid_token, gateway_url):
    '''Wrapper for calling the FOE startup service

    Future: get metadata like research
    '''
    # research = requests.get('https://foeen.innogamescdn.com/start/metadata?id=research-82aa3cecc98e43f0ffde0e908e53fb5656164d72').json()
    # for i in [x for x in research if ('level' in x and x['level'] < 3) or 'level' not in x]:
    # print(json.dumps(i, indent=2))
    # print(i['level'] if 'level' in i else '')
    # print(research.keys())
    # print(json.dumps(research,indent=2))

    foe_secret = get_secret()
    print(foe_secret)

    state, queue_items = execute_task(
        create_queue_item("StartupService", "getData"), {
            'sid_token': sid_token, 
            'gateway_url': gateway_url, 
            'foe_secret': environ.get('FOE_SECRET') 
        }
    )

    _, tasks = execute_task(create_queue_item("CityMapService", "getCityMap", ["cultural_outpost"]), state)
    return state, queue_items + tasks


def main():
    '''Main event loop

    '''

    # initialise game
    mid_token = login()
    sid_token, gateway_url = start_game(mid_token)

    queue = Queue()  # initialise queue
    state, queue_items = init_game(sid_token, gateway_url)
    queue.insert(queue_items)

    # group queue items for efficiency
    queue.group()
    current = queue.pop()

    while True:
        # get time
        now = int(datetime.now().timestamp())

        # log next task
        print(datetime.now(), current['requestClass'], current['requestMethod'],
              current['requestData'], current['time'], now, 'Wait: ', max(current['time'] - now, 0))

        # wait until next task should be executed
        time.sleep(max(current['time'] - now, 0))

        # updated time
        now = int(datetime.now().timestamp())

        try:
            # execute task
            state, queue_items = execute_task(current, state)
        except FoeBotReload as error:
            print(error, 'reloading...')
            queue.clear()
            state, queue_items = init_game(
                state['sid_token'], state['gateway_url'])
        except FoeBotRewardNotAvailable as error:
            # if reward not available, just move on to next task
            print(error, 'skipping...')
        except requests.exceptions.RequestException as error:
            # handle disconnection error
            print('CANNOT CONNECT: ', error)
            print('Trying again in 10 seconds...')
            # wait 10 seconds, then reset the game
            time.sleep(10)
            print('reloading...')
            queue_items = [create_queue_item("StartupService", "getData")]
        finally:
            # insert new tasks
            queue.insert(queue_items)

            # log state
            print(datetime.now(
            ), f"Money: {state['money']}, Supplies: {state['supplies']}, Forge Points: {state['forge_points']}")

            # group production collection together
            queue.group()

            # set new task
            current = queue.pop()
            time.sleep(0.5)
