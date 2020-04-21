#
# Nature Remo Smart TV easy Control program called from Alexa Smart Home Skill
#
# The following TVs can be operated with this program.
# ・ Power ON / OFF
# ・ Volume increase / decrease (default value: ± 2, direct value: ± 1 to 4)
# ・ Channel change (up / down, direct value: 1 ~ 12)
#
# This program handles the following Alexa interface to operate
# the TV and calls the Nature Remo Cloud API.
#
# ・Alexa.Speaker Inferface
# ・Alexa.PowerController Inferface
# ・Alexa.ChannelController Inferface
#
# more information https://ameblo.jp/nabezou3/entry-12590144194.html
#
# 2020.04.21 Copyright by Hiroyasu Watanabe
#

# -*- coding: utf-8 -*-
# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License"). You may not use this file except in
# compliance with the License. A copy of the License is located at
#
#    http://aws.amazon.com/asl/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific
# language governing permissions and limitations under the License.

"""Alexa Smart Home Lambda Function Sample Code.

This file demonstrates some key concepts when migrating an existing Smart Home skill Lambda to
v3, including recommendations on how to transfer endpoint/appliance objects, how v2 and vNext
handlers can be used together, and how to validate your v3 responses using the new Validation
Schema.

Note that this example does not deal with user authentication, only uses virtual devices, omits
a lot of implementation and error handling to keep the code simple and focused.
"""

import logging
import time
import json
import uuid
import requests

# Imports for v3 validation
from validation import validate_message

# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# To simplify this sample Lambda, we omit validation of access tokens and retrieval of a specific
# user's appliances. Instead, this array includes a variety of virtual appliances in v2 API syntax,
# and will be used to demonstrate transformation between v2 appliances and v3 endpoints.
SAMPLE_APPLIANCES = [
    {
        "applianceId": "endpoint-001",
        "manufacturerName": "Sample Manufacturer",
        "modelName": "Smart Switch",
        "version": "1",
        "friendlyName": "Switch",
        "friendlyDescription": "001 Switch that can only be turned on/off",
        "isReachable": True,
        "actions": [
            "turnOn",
            "turnOff"
        ],
        "additionalApplianceDetails": {
            "detail1": "For simplicity, this is the only appliance",
            "detail2": "that has some values in the additionalApplianceDetails"
        }
    },
    {
        "applianceId": "endpoint-002",
        "manufacturerName": "Sample Manufacturer",
        "modelName": "Smart Light",
        "version": "1",
        "friendlyName": "Light",
        "friendlyDescription": "002 Light that is dimmable and can change color and color temperature",
        "isReachable": True,
        "actions": [
            "turnOn",
            "turnOff",
            "setPercentage",
            "incrementPercentage",
            "decrementPercentage",
            "setColor",
            "setColorTemperature",
            "incrementColorTemperature",
            "decrementColorTemperature"
        ],
        "additionalApplianceDetails": {}
    },
    {
        "applianceId": "endpoint-003",
        "manufacturerName": "Sample Manufacturer",
        "modelName": "Smart White Light",
        "version": "1",
        "friendlyName": "White Light",
        "friendlyDescription": "003 Light that is dimmable and can change color temperature only",
        "isReachable": True,
        "actions": [
            "turnOn",
            "turnOff",
            "setPercentage",
            "incrementPercentage",
            "decrementPercentage",
            "setColorTemperature",
            "incrementColorTemperature",
            "decrementColorTemperature"
        ],
        "additionalApplianceDetails": {}
    },
    {
        "applianceId": "endpoint-004",
        "manufacturerName": "Sample Manufacturer",
        "modelName": "Smart Thermostat",
        "version": "1",
        "friendlyName": "Thermostat",
        "friendlyDescription": "004 Thermostat that can change and query temperatures",
        "isReachable": True,
        "actions": [
            "setTargetTemperature",
            "incrementTargetTemperature",
            "decrementTargetTemperature",
            "getTargetTemperature",
            "getTemperatureReading"
        ],
        "additionalApplianceDetails": {}
    },
    {
        "applianceId": "endpoint-004-1",
        "manufacturerName": "Sample Manufacturer",
        "modelName": "Smart Thermostat Dual",
        "version": "1",
        "friendlyName": "Living Room Thermostat",
        "friendlyDescription": "004-1 Thermostat that can change and query temperatures, supports dual setpoints",
        "isReachable": True,
        "actions": [
            "setTargetTemperature",
            "incrementTargetTemperature",
            "decrementTargetTemperature",
            "getTargetTemperature",
            "getTemperatureReading"
        ],
        "additionalApplianceDetails": {}
    },
    {
        "applianceId": "endpoint-005",
        "manufacturerName": "Sample Manufacturer",
        "modelName": "Smart Lock",
        "version": "1",
        "friendlyName": "Lock",
        "friendlyDescription": "005 Lock that can be locked and can query lock state",
        "isReachable": True,
        "actions": [
            "setLockState",
            "getLockState"
        ],
        "additionalApplianceDetails": {}
    },
    {
        "applianceId": "endpoint-006",
        "manufacturerName": "Sample Manufacturer",
        "modelName": "Smart Scene",
        "version": "1",
        "friendlyName": "Good Night Scene",
        "friendlyDescription": "006 Scene that can only be turned on",
        "isReachable": True,
        "actions": [
            "turnOn"
        ],
        "additionalApplianceDetails": {}
    },
    {
        "applianceId": "endpoint-007",
        "manufacturerName": "Sample Manufacturer",
        "modelName": "Smart Activity",
        "version": "1",
        "friendlyName": "Watch TV",
        "friendlyDescription": "007 Activity that runs sequentially that can be turned on and off",
        "isReachable": True,
        "actions": [
            "turnOn",
            "turnOff"
            ],
        "additionalApplianceDetails": {}
    },
    {
        "applianceId": "endpoint-008",
        "manufacturerName": "Sample Manufacturer",
        "modelName": "Smart Camera",
        "version": "1",
        "friendlyName": "Baby Camera",
        "friendlyDescription": "008 Camera that streams from an RSTP source",
        "isReachable": True,
        "actions": [
            "retrieveCameraStreamUri"
            ],
        "additionalApplianceDetails": {}
    },
    {
        "applianceId": "endpoint-009",
        "manufacturerName": "Sample Manufacturer",
        "modelName": "Smart TV",
        "version": "1",
        "friendlyName": "テレビ",
        "friendlyDescription": "009 TV that can be turned on/off and ajust volume up/down and change channel",
        "isReachable": True,
        "actions": [
            "AdjustVolume",
            "turnOn",
            "turnOff",
            "ChangeChannel",
            "SkipChannels"
            ],
        "additionalApplianceDetails": {}
    }
]

# "friendlyName": "アクオス" or "テレビ"
        
def lambda_handler(request, context):
    """Main Lambda handler.

    Since you can expect both v2 and v3 directives for a period of time during the migration
    and transition of your existing users, this main Lambda handler must be modified to support
    both v2 and v3 requests.
    """

    try:
        logger.info("Directive:")
        logger.info(json.dumps(request, indent=4, sort_keys=True))

        version = get_directive_version(request)

        if version == "3":
            logger.info("Received v3 directive!")
            if request["directive"]["header"]["name"] == "Discover":
                response = handle_discovery_v3(request)
            else:
                response = handle_non_discovery_v3(request)

        else:
            logger.info("Received v2 directive!")
            if request["header"]["namespace"] == "Alexa.ConnectedHome.Discovery":
                response = handle_discovery()
            else:
                response = handle_non_discovery(request)

        logger.info("Response:")
        logger.info(json.dumps(response, indent=4, sort_keys=True))

        #if version == "3":
            #logger.info("Validate v3 response")
            #validate_message(request, response)

        return response
    except ValueError as error:
        logger.error(error)
        raise

# v2 handlers
def handle_discovery():
    header = {
        "namespace": "Alexa.ConnectedHome.Discovery",
        "name": "DiscoverAppliancesResponse",
        "payloadVersion": "2",
        "messageId": get_uuid()
    }
    payload = {
        "discoveredAppliances": SAMPLE_APPLIANCES
    }
    response = {
        "header": header,
        "payload": payload
    }
    return response

def handle_non_discovery(request):
    request_name = request["header"]["name"]

    if request_name == "TurnOnRequest":
        header = {
            "namespace": "Alexa.ConnectedHome.Control",
            "name": "TurnOnConfirmation",
            "payloadVersion": "2",
            "messageId": get_uuid()
        }
        payload = {}
    elif request_name == "TurnOffRequest":
        header = {
            "namespace": "Alexa.ConnectedHome.Control",
            "name": "TurnOffConfirmation",
            "payloadVersion": "2",
            "messageId": get_uuid()
        }
    # other handlers omitted in this example
    payload = {}
    response = {
        "header": header,
        "payload": payload
    }
    return response

# v2 utility functions
def get_appliance_by_appliance_id(appliance_id):
    for appliance in SAMPLE_APPLIANCES:
        if appliance["applianceId"] == appliance_id:
            return appliance
    return None

def get_utc_timestamp(seconds=None):
    return time.strftime("%Y-%m-%dT%H:%M:%S.00Z", time.gmtime(seconds))

def get_uuid():
    return str(uuid.uuid4())

# v3 handlers
def handle_discovery_v3(request):
    endpoints = []
    for appliance in SAMPLE_APPLIANCES:
        endpoints.append(get_endpoint_from_v2_appliance(appliance))

    response = {
        "event": {
            "header": {
                "namespace": "Alexa.Discovery",
                "name": "Discover.Response",
                "payloadVersion": "3",
                "messageId": get_uuid()
            },
            "payload": {
                "endpoints": endpoints
            }
        }
    }
    return response


def send_command_to_nature_remo(payload):

    # Set Nature Remo API Key
    # [Nature Remo Access Token] は https://home.nature.global/ から取得してください。
    KEY_IN_HEADERS = {
        'accept': 'application/json',
        'Authorization': 'Bearer [Nature Remo Access Token]'
    }

    # Nature Remo grobal API for TV control
    # [id] は下記コマンドでNatue Remo Cloudから、デバイス情報を取得してください。
    # $ curl -X GET "https://api.nature.global/1/appliances" -H "accept: application/json" \
    #        -k --header "Authorization: Bearer [Nature Remo Access Token] "
    URL_OF_GROBAL_API = 'https://api.nature.global/1/appliances/[id]/tv'

    result = requests.post(URL_OF_GROBAL_API, headers=KEY_IN_HEADERS, data=payload)

    return result


def handle_non_discovery_v3(request):
    
    request_namespace = request["directive"]["header"]["namespace"]
    request_name = request["directive"]["header"]["name"]

    # インターフェースの識別
    if request_namespace == "Alexa.PowerController":

        # 電源ON or OFF
        if request_name == "TurnOn":
            value = "ON"
            payload = {'button': 'power'} # トグル
        else:
            value = "OFF"
            payload = {'button': 'power'} # トグル

        # コマンド送信
        result = send_command_to_nature_remo(payload)

        # 応答パケット作成
        response = {
            "context": {
                "properties": [
                    {
                        "namespace": "Alexa.PowerController",
                        "name": "powerState",
                        "value": value,
                        "timeOfSample": get_utc_timestamp(),
                        "uncertaintyInMilliseconds": 500
                    }
                ]
            },
            "event": {
                "header": {
                    "namespace": "Alexa",
                    "name": "Response",
                    "payloadVersion": "3",
                    "messageId": get_uuid(),
                    "correlationToken": request["directive"]["header"]["correlationToken"]
                },
                "endpoint": {
                    "scope": {
                        "type": "BearerToken",
                        "token": "access-token-from-Amazon"
                    },
                    "endpointId": request["directive"]["endpoint"]["endpointId"]
                },
                "payload": {}
            }
        }
        
        return response

    elif request_namespace == "Alexa.ChannelController":

        if request_name == "ChangeChannel":
            # チャンネル変更
            request_channel_number = request["directive"]["payload"]["channel"]["number"]

            # チャンネル番号セット
            strButton = "ch-" + request_channel_number
            payload = {'button': strButton }
            
            # コマンド送信
            result = send_command_to_nature_remo(payload)
         
            # 応答パケット作成(正常)
            response = {
                "context": {
                    "properties": [
                        {
                            "namespace": "Alexa.ChannelController",
                            "name": "channel",
                            "value": {
                                "number": request_channel_number,
                                "callSign": "",
                                "affiliateCallSign": ""
                            },
                            "timeOfSample": get_utc_timestamp(),
                            "uncertaintyInMilliseconds": 500
                        }
                    ]
                },
                "event": {
                    "header": {
                        "namespace": "Alexa",
                        "name": "Response",
                        "payloadVersion": "3",
                        "messageId": get_uuid(),
                        "correlationToken": request["directive"]["header"]["correlationToken"]
                    },
                    "endpoint": {
                        "scope": {
                            "type": "BearerToken",
                            "token": "access-token-from-Amazon"
                        },
                        "endpointId": request["directive"]["endpoint"]["endpointId"]
                    },
                    "payload": {}
                }
            }
            

        elif request_name == "SkipChannels":
            #チャンネル増減
            request_channel_count = request["directive"]["payload"]["channelCount"]

            # チャンネル増減命令セット
            if request_channel_count > 0 :
                payload = {'button': 'ch-up'}
            else:
                payload = {'button': 'ch-down'}
                    
            # コマンド送信
            result = send_command_to_nature_remo(payload)
         
            # 応答パケット作成(正常)
            response = {
                "context": {
                    "properties": [
                        {
                            "namespace": "Alexa.ChannelController",
                            "name": "channelCount",
                            "value": request_channel_count,
                            "timeOfSample": get_utc_timestamp(),
                            "uncertaintyInMilliseconds": 500
                        }
                    ]
                },
                "event": {
                    "header": {
                        "namespace": "Alexa",
                        "name": "Response",
                        "payloadVersion": "3",
                        "messageId": get_uuid(),
                        "correlationToken": request["directive"]["header"]["correlationToken"]
                    },
                    "endpoint": {
                        "scope": {
                            "type": "BearerToken",
                            "token": "access-token-from-Amazon"
                        },
                        "endpointId": request["directive"]["endpoint"]["endpointId"]
                    },
                    "payload": {}
                }
            }

        else :
            # 応答パケット作成(エラー)
            response = {
                "event": {
                    "header": {
                        "namespace": "Alexa",
                        "name": "ErrorResponse",
                        "messageId": get_uuid(),
                        "payloadVersion": "3"
                    },
                    "endpoint":{
                        "endpointId": request["directive"]["endpoint"]["endpointId"]
                    },
                    "payload": {
                        "type": "INVALID_DIRECTIVE",
                        "message": "サポートされていないコマンドです"
                    }
                }
            }
        
        
        return response


    elif request_namespace == "Alexa.Authorization":
        if request_name == "AcceptGrant":
            response = {
                "event": {
                    "header": {
                        "namespace": "Alexa.Authorization",
                        "name": "AcceptGrant.Response",
                        "payloadVersion": "3",
                        "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4"
                    },
                    "payload": {}
                }
            }
            return response

    elif request_namespace == "Alexa.Speaker":

        #ボリューム調整
        if request_name == "AdjustVolume":
            request_volume = request["directive"]["payload"]["volume"]
            request_volumeDefault = request["directive"]["payload"]["volumeDefault"]

            #ボリューム増減命令セット
            if request_volume < 0 :
                payload = {'button': 'vol-down'}
            else :
                payload = {'button': 'vol-up'}
            
            if request_volumeDefault == True :
                # デフォルト2レベル上下したい
                sendCount = 2
            else:
                # ユーザー指定増減幅を使用、最大値4。
                sendCount = min (abs(request_volume), 4)

            #コマンド送信
            for _ in range(sendCount) :
                result = send_command_to_nature_remo(payload)
                

            # 応答パケット作成
            response = {
                "context": {
                    "properties": [
                        {
                            "namespace": "Alexa.Speaker",
                            "name": "volume",
                            "value": request_volume,
                            "timeOfSample": get_utc_timestamp(),
                            "uncertaintyInMilliseconds": 0
                        },
                        {
                            "namespace": "Alexa.Speaker",
                            "name": "muted",
                            "value": False,
                            "timeOfSample": get_utc_timestamp(),
                            "uncertaintyInMilliseconds": 0
                        }
                    ]
                },
                "event": {
                    "header": {
                        "messageId": get_uuid(),
                        "correlationToken": request["directive"]["header"]["correlationToken"],
                        "namespace": "Alexa",
                        "name": "Response",
                        "payloadVersion": "3"
                    },
                    "endpoint":{
                        "endpointId": request["directive"]["endpoint"]["endpointId"]
                    },
                    
                    "payload": payload
                }
            }
            
            return response

    # other handlers omitted in this example

# v3 utility functions
def get_endpoint_from_v2_appliance(appliance):
    endpoint = {
        "endpointId": appliance["applianceId"],
        "manufacturerName": appliance["manufacturerName"],
        "friendlyName": appliance["friendlyName"],
        "description": appliance["friendlyDescription"],
        "displayCategories": [],
        "cookie": appliance["additionalApplianceDetails"],
        "capabilities": []
    }
    endpoint["displayCategories"] = get_display_categories_from_v2_appliance(appliance)
    endpoint["capabilities"] = get_capabilities_from_v2_appliance(appliance)
    return endpoint

def get_directive_version(request):
    try:
        return request["directive"]["header"]["payloadVersion"]
    except:
        try:
            return request["header"]["payloadVersion"]
        except:
            return "-1"

def get_endpoint_by_endpoint_id(endpoint_id):
    appliance = get_appliance_by_appliance_id(endpoint_id)
    if appliance:
        return get_endpoint_from_v2_appliance(appliance)
    return None

def get_display_categories_from_v2_appliance(appliance):
    model_name = appliance["modelName"]
    if model_name == "Smart Switch": displayCategories = ["SWITCH"]
    elif model_name == "Smart Light": displayCategories = ["LIGHT"]
    elif model_name == "Smart White Light": displayCategories = ["LIGHT"]
    elif model_name == "Smart Thermostat": displayCategories = ["THERMOSTAT"]
    elif model_name == "Smart Lock": displayCategories = ["SMARTLOCK"]
    elif model_name == "Smart Scene": displayCategories = ["SCENE_TRIGGER"]
    elif model_name == "Smart Activity": displayCategories = ["ACTIVITY_TRIGGER"]
    elif model_name == "Smart Camera": displayCategories = ["CAMERA"]
    else: displayCategories = ["OTHER"]
    return displayCategories

def get_capabilities_from_v2_appliance(appliance):
    model_name = appliance["modelName"]
    if model_name == 'Smart Switch':
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PowerController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "powerState" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            }
        ]
    elif model_name == "Smart Light":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PowerController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "powerState" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.ColorController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "color" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.ColorTemperatureController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "colorTemperatureInKelvin" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.BrightnessController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "brightness" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PowerLevelController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "powerLevel" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PercentageController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "percentage" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            }
        ]
    elif model_name == "Smart White Light":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PowerController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "powerState" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.ColorTemperatureController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "colorTemperatureInKelvin" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.BrightnessController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "brightness" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PowerLevelController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "powerLevel" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PercentageController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "percentage" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            }
        ]
    elif model_name == "Smart Thermostat":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.ThermostatController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "targetSetpoint" },
                        { "name": "thermostatMode" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.TemperatureSensor",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "temperature" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            }
        ]
    elif model_name == "Smart Thermostat Dual":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.ThermostatController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "upperSetpoint" },
                        { "name": "lowerSetpoint" },
                        { "name": "thermostatMode" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.TemperatureSensor",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "temperature" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            }
        ]
    elif model_name == "Smart Lock":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.LockController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "lockState" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            }
        ]
    elif model_name == "Smart Scene":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.SceneController",
                "version": "3",
                "supportsDeactivation": False,
                "proactivelyReported": True
            }
        ]
    elif model_name == "Smart Activity":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.SceneController",
                "version": "3",
                "supportsDeactivation": True,
                "proactivelyReported": True
            }
        ]
    elif model_name == "Smart Camera":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.CameraStreamController",
                "version": "3",
                "cameraStreamConfigurations" : [ {
                    "protocols": ["RTSP"],
                    "resolutions": [{"width":1280, "height":720}],
                    "authorizationTypes": ["NONE"],
                    "videoCodecs": ["H264"],
                    "audioCodecs": ["AAC"]
                } ]
            }
        ]
    elif model_name == "Smart TV":
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.Speaker",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "AdjustVolume" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PowerController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "powerState" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            },
            {
                "type": "AlexaInterface",
                "interface": "Alexa.ChannelController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "channel" },
                        { "name": "channelCount" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            }

        ]
    else:
        # in this example, just return simple on/off capability
        capabilities = [
            {
                "type": "AlexaInterface",
                "interface": "Alexa.PowerController",
                "version": "3",
                "properties": {
                    "supported": [
                        { "name": "powerState" }
                    ],
                    "proactivelyReported": True,
                    "retrievable": True
                }
            }
        ]

    # additional capabilities that are required for each endpoint
    endpoint_health_capability = {
        "type": "AlexaInterface",
        "interface": "Alexa.EndpointHealth",
        "version": "3",
        "properties": {
            "supported":[
                { "name":"connectivity" }
            ],
            "proactivelyReported": True,
            "retrievable": True
        }
    }
    alexa_interface_capability = {
        "type": "AlexaInterface",
        "interface": "Alexa",
        "version": "3"
    }
    capabilities.append(endpoint_health_capability)
    capabilities.append(alexa_interface_capability)
    return capabilities
