#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import paho.mqtt.client as mqtt
import paho.mqtt.publish as mqttPublish
import pixels

_INTENT_ADD_TO_LIST 	= 'hermes/intent/Psychokiller1888:demoAddToList'
_USER_RANDOM_ANSWER 	= 'hermes/intent/Psychokiller1888:userRandomAnswer'

mqttClient = None
leds = None
sessions = {}

def onConnect(client, userData, flags, rc):
	mqttClient.subscribe(_INTENT_ADD_TO_LIST)
	mqttClient.subscribe(_USER_RANDOM_ANSWER)


def onMessage(client, userData, message):
	data = json.loads(message.payload)
	sessionId = data['sessionId']

	if message.topic == _INTENT_ADD_TO_LIST:
		ask(text='What do you want to add to the shopping list?', customData=json.dumps({
			'wasIntent': _INTENT_ADD_TO_LIST
		}))

	elif message.topic == 'userRandomAnswer':
		customData = parseCustomData(message)
		print(customData['userInput'])


def onSessionStarted(client, data, msg):
	sessionId = parseSessionId(msg)
	sessions[sessionId] = msg


def onSessionEnded(client, data, msg):
	sessionId = parseSessionId(msg)
	if sessionId in sessions:
		del sessions[sessionId]


def onIntentNotRecognized(client, data, msg):
	payload = json.loads(msg.payload)
	sessionId = parseSessionId(msg)

	wasMessage = sessions[sessionId]
	customData = parseCustomData(wasMessage)

	# This is not a continued session as there's no custom data
	if customData is None:
		return

	siteId = parseSiteId(wasMessage)

	customData['userInput'] = payload['input']
	payload['customData'] = customData

	payload['siteId'] = siteId
	wasMessage.payload = json.dumps(payload)
	wasMessage.topic = 'userRandomAnswer'

	onMessage(None, None, wasMessage)


def endTalk(sessionId, text):
	mqttClient.publish('hermes/dialogueManager/endSession', json.dumps({
		'sessionId': sessionId,
		'text': text
	}))


def say(text):
	mqttClient.publish('hermes/dialogueManager/startSession', json.dumps({
		'init': {
			'type': 'notification',
			'text': text
		}
	}))


def ask(text, client='default', intentFilter=None, customData=''):
	mqttClient.publish('hermes/dialogueManager/startSession', json.dumps({
		'siteId': client,
		'customData': customData,
		'init': {
			'type': 'action',
			'text': text,
			'canBeEnqueued': True
		}
	}))


def parseSessionId(message):
	data = json.loads(message.payload)
	if 'sessionId' in data:
		return data['sessionId']
	else:
		return False


def parseCustomData(message):
	data = json.loads(message.payload)
	if 'customData' in data and data['customData'] is not None:
		return json.loads(data['customData'])
	else:
		return None


def parseSiteId(message):
	data = json.loads(message.payload)
	if 'siteId' in data:
		return data['siteId']
	else:
		return 'default'


if __name__ == '__main__':
	print('Loading arbitrary text capture demo')

	leds = pixels.Pixels()
	leds.off()

	mqttClient = mqtt.Client()
	mqttClient.on_connect = onConnect
	mqttClient.on_message = onMessage
	mqttClient.message_callback_add("hermes/nlu/intentNotRecognized", onIntentNotRecognized)
	mqttClient.message_callback_add('hermes/dialogueManager/sessionEnded', onSessionEnded)
	mqttClient.message_callback_add('hermes/dialogueManager/sessionStarted', onSessionStarted)
	mqttClient.connect('localhost', 1883)
	print('Demo loaded')
	mqttClient.loop_forever()