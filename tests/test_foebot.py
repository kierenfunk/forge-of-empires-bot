
from src.foebot.main import *
import json

MID_TOKEN = login()
SID_TOKEN, GATEWAY_URL = start_game(MID_TOKEN)

def test_login():
    """Login to forge of empires

    """
    assert len(MID_TOKEN) == 40

def test_start_game():
    '''Initiate game

    '''
    assert isinstance(SID_TOKEN, str)
    assert len(SID_TOKEN) == 40
    assert isinstance(GATEWAY_URL, str)

def test_sig():
    '''Tests the signature
    If this fails, the FOE_SECRET needs to be updated

    '''
    body = [
        {
            "__class__": "ServerRequest",
            "requestData": [
                {
                    "__class__": "ViewportMetrics",
                    "stageWidth": 950,
                    "stageHeight": 767,
                    "bufferWidth": 1140,
                    "bufferHeight": 920,
                    "displayWidth": 1537,
                    "displayHeight": 865,
                    "contentsScaleFactor": 1.2
                }
            ],
            "requestClass": "LogService",
            "requestMethod": "logViewportMetrics",
            "requestId": 1
        },
        {
            "__class__": "ServerRequest",
            "requestData": [],
            "requestClass": "StartupService",
            "requestMethod": "getData",
            "requestId": 2
        }
    ]
    body = json.dumps(body).replace(' ', '')
    result = sig(body, 'Jdal3Q4X33xkRVJHe5XG-0jw')
    assert result == '4cb8c704f6'

def test_startup_service():
    state, queue_items = execute_task(
        create_queue_item("StartupService", "getData"), {
            'sid_token': SID_TOKEN, 'gateway_url': GATEWAY_URL}
    )
    assert 'money' in state
    assert state['money'] > 0
    assert 'player_id' in state
