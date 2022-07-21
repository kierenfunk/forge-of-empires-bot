"""Python starter template testing

"""

from src.foebot.main import main, init_game, sig
from os import environ
import json

def test_main():
    """A generic test

    """
    init_game(environ.get("TEST_MID"))

def test_sig():
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