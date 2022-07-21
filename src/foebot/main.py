"""Python Starter Template

"""

import requests
from os import environ
import re
import hashlib
import json
import time
from .queue import Queue
from datetime import datetime

def login():
    '''Login to forge of empires and retrieve mid cookie

    '''
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
    login_url = response.text[len("<script>window.top.location.href = \""):-len("\";</script>")]

    # login
    response = session.get(login_url)

    # return mid cookie
    return session.cookies.get_dict()['mid']

def sig(payload, user_key):
    data = user_key + environ.get("FOE_SECRET") + payload
    signature = hashlib.md5(data.encode('utf-8')).hexdigest()[1:11]
    return signature

def req(body):
    gateway_url = environ.get('GATEWAY_URL')
    user_key = gateway_url.split('?h=')[1]
    payload = json.dumps(body).replace(' ', '')
    response = requests.post(gateway_url,headers={
        'cookie': f'sid={environ.get("TEST_SID")}',
        'signature': sig(payload, user_key),
    }, data=payload).json()
    return response

def start_production(prod_id, request_id):
    body = [{
        "__class__": "ServerRequest",
        "requestData": [
            prod_id,
            1
        ],
        "requestClass": "CityProductionService",
        "requestMethod": "startProduction",
        "requestId": 0
    }
    ]

    response = req(body)
    try:
        resources = [data['responseData']['resources'] for data in response if data['requestMethod'] == 'getPlayerResources'][0]
    except:
        print(prod_id)
        print(json.dumps(response, indent=2))
        resources = {
            'money': 0,
            'supplies': 0,
            'population': 0,
            'total_population': 0,
        }
        #raise Exception('Start Production Error')
    updated_entities = [data['responseData']['updatedEntities'] for data in response if data['requestMethod'] == 'startProduction'][0]
    # return game state and also queue items
    return {
        'state': {
            'request_id': request_id + 1,
            'money': resources['money'],
            'supplies': resources['supplies'],
            'population': resources['population'],
            'total_population': resources['total_population'],
        },
        'queue_items': [
            {
                'type': 'pickupProduction',
                'id': entity['id'],
                'entity': entity,
                'time': entity['state']['next_state_transition_at']
            } for entity in updated_entities
        ]
    }

def pickup_production(entity_ids, request_id):
    body = [{
            "__class__": "ServerRequest",
            "requestData": [
                entity_ids
            ],
            "requestClass": "CityProductionService",
            "requestMethod": "pickupProduction",
            "requestId": request_id
        }
    ]

    response = req(body)
    try:
        resources = [data['responseData']['resources'] for data in response if data['requestMethod'] == 'getPlayerResources'][0]
    except:
        print(entity_ids)
        print(json.dumps(response, indent=2))
        resources = {
            'money': 0,
            'supplies': 0,
            'population': 0,
            'total_population': 0,
        }

    updated_entities = [data['responseData']['updatedEntities'] for data in response if data['requestMethod'] == 'pickupProduction'][0]
    # return game state and also queue items
    return {
        'state': {
            'request_id': request_id + 1,
            'money': resources['money'],
            'supplies': resources['supplies'],
            'population': resources['population'],
            'total_population': resources['total_population'],
        },
        'queue_items': [
            {
                'type': 'pickupProduction' if entity['type'] == 'residential' else 'startProduction',
                'id': entity['id'],
                'entity': entity,
                'time': 0 if entity['state']['__class__'] == 'IdleState' else entity['state']['next_state_transition_at']
            } for entity in updated_entities
        ]
    }



def init_game(mid_token):
    '''
    worlds = requests.post('https://en0.forgeofempires.com/start/index?action=fetch_worlds_for_login_page', headers={
        'cookie': f'mid={mid_token}',
        'x-requested-with': 'XMLHttpRequest'
    }).json()
    world = list(worlds['player_worlds'].keys())[0]

    play_now = requests.post('https://en0.forgeofempires.com/start/index?action=play_now_login', headers={
        'cookie': f'mid={mid_token}',
        'x-requested-with': 'XMLHttpRequest'
    }, data={"json": f"%7B%22world_id%22%3A%22{world}%22%7D"}).json()

    session = requests.Session()
    response = session.get(play_now['login_url'])
    '''
    #gateway_url = re.findall(r'gatewayUrl: \'([\S]*)\',' , response.text)[0]

    body = [
        {
            "__class__": "ServerRequest",
            "requestData": [],
            "requestClass": "StartupService",
            "requestMethod": "getData",
            "requestId": 1
        }
    ]
    response = req(body)
    init_data = [d for d in response if d['requestClass'] == 'StartupService' and d['requestMethod'] == 'getData'][0]
    resources = [data['responseData']['resources'] for data in response if data['requestMethod'] == 'getPlayerResources'][0]
    state = {
        'request_id': 2,
        'money': resources['money'],
        'supplies': resources['supplies'],
        'population': resources['population'],
        'total_population': resources['total_population'],
    }
    print(state)

    queue = Queue()

    entity_types = set(['residential', 'main_building', 'production'])
    entities = [ent for ent in init_data['responseData']['city_map']['entities'] if ent['type'] in entity_types]

    # initialise queue
    for entity in entities:
        if entity['state']['__class__'] == 'ProducingState':
            queue.insert([{
                'type': 'pickupProduction',
                'id': entity['id'],
                'entity': entity,
                'time': entity['state']['next_state_transition_at']
            }])
        if entity['state']['__class__'] == 'ProductionFinishedState':
            queue.insert([{
                'type': 'pickupProduction',
                'id': entity['id'],
                'entity': entity,
                'time': 0
            }])
        if entity['state']['__class__'] == 'IdleState' and entity['type'] == 'production':
            queue.insert([{
                'type': 'startProduction',
                'id': entity['id'],
                'entity': entity,
                'time': 0
            }])

    current = queue.pop()
    while True:
        time.sleep(2)
        now = int(datetime.now().timestamp())
        print(current['type'], current['id'], current['entity']['cityentity_id'], current['time'], now)
        if current['time'] >= now:
            continue
        try:
            if current['type'] == 'pickupProduction':
                response = pickup_production([current['id']], state['request_id'])
                state = response['state']
                queue.insert(response['queue_items'])
            if current['type'] == 'startProduction':
                response = start_production(current['id'], state['request_id'])
                state = response['state']
                queue.insert(response['queue_items'])
            print(state)
            current = queue.pop()
        except Exception as e:
            print(f'ERROR: {e} \n RETRYING')


    return {}
