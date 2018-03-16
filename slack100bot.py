#!/usr/bin/env python3
"""
Authors: Evan Bluhm, Alex French, Samuel Gass, Margaret Yim
"""

import json
import os
import argparse
import logging
import random
import requests
import sys
import time
import operator
from requests.auth import HTTPBasicAuth
from slackclient import SlackClient

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

WATSON_API_ENDPOINT = 'https://gateway.watsonplatform.net/tone-analyzer/api/v3'


class EmojiBot(object):
    """
    Wow wow such EmojiBot

    Hard-coding the bot ID for now, but will pass those in to the constructor
    later
    """

    def __init__(self, bx_username, bx_password, slack_token):

        self._bot_id = "U4M6Z42JK"
        # 1 second delay between reading from firehose
        self._READ_WEBSOCKET_DELAY = 1
        self.sc = SlackClient(slack_token)
        self.bxauth = HTTPBasicAuth(username=bx_username, password=bx_password)

    def listen(self):
        slack_client = self.sc
        if slack_client.rtm_connect():
            logging.info("StarterBot connected and running!")
            while True:
                event = parse_slack_output(slack_client.rtm_read())
                if event:
                    logging.info("event received from slack: %s",
                                 event.get('text'))
                    psychoAnalyze(
                        event=event,
                        slack_client=slack_client,
                        bxauth=self.bxauth)
                time.sleep(self._READ_WEBSOCKET_DELAY)
        else:
            logging.error("Connection failed. Invalid Slack token or bot ID?")


def psychoAnalyze(event, slack_client, bxauth):
    EMOTIONAL_THRESHOLD = 0.6
    payload = {
        'text': event.get('text'),
        'version': '2016-05-19',
        'Content-Type': 'text/plain;charset=utf-8'
    }
    resp = requests.get(
        WATSON_API_ENDPOINT + '/tone', params=payload, auth=bxauth)
    if resp.status_code != 200:
        logging.error(
            "Failed request for tone data from Watson: %s" % resp.text)
        return False
    analysis = json.loads(resp.text)
    emotions = dict(anger=0, disgust=0, fear=0, joy=0, sadness=0)

    for category in analysis['document_tone']['tone_categories']:
        if category['category_id'] == 'emotion_tone':
            for tone in category['tones']:
                if tone['tone_id'] == 'anger':
                    emotions['anger'] = tone['score']
                if tone['tone_id'] == 'disgust':
                    emotions['disgust'] = tone['score']
                if tone['tone_id'] == 'fear':
                    emotions['fear'] = tone['score']
                if tone['tone_id'] == 'joy':
                    emotions['joy'] = tone['score']
                if tone['tone_id'] == 'sadness':
                    emotions['sadness'] = tone['score']
    logging.info("Emotional parsing for statement \"%s\" complete: %s",
                 event.get('text'), emotions)

    sorted_emotions = sorted(
        emotions.items(), key=operator.itemgetter(1), reverse=True)
    (top_emotion, top_score) = sorted_emotions[0]
    if top_score > EMOTIONAL_THRESHOLD:
        logging.debug("This event merits an emoji response: %s", event)
        rewardEmotion(
            slack_client=slack_client,
            emotion=top_emotion,
            statement=event.get('text'),
            channel=event.get('channel'),
            timestamp=event.get('ts'))
    else:
        logging.debug(
            "Decided this event only got a %s score of %f, so no response: %s",
            max(emotions), top_score, event)


def rewardEmotion(slack_client, emotion, statement, channel, timestamp):
    the_database = {
        'anger': [
            'hummus', 'rage', 'upside_down_face', 'pouting_cat',
            'dove_of_peace', 'wind_blowing_face', 'dealwithitparrot'
        ],
        'disgust': [
            'pizza', 'dizzy_face', 'boredparrot', 'no_mouth', 'neutral_face',
            'disappointed', 'hankey', 'shit', 'pouting_cat', 'thumbsdown'
        ],
        'fear': [
            'scream_cat', 'scream', 'confusedparrot', 'runner',
            'slightly_smiling_face', 'no_mouth', 'flushed', 'ghost',
            'thumbsdown', 'jack_o_lantern', 'sweat_drops'
        ],
        'joy': [
            'partyparrot', '100', 'blue_heart', 'pancakes', 'beers',
            'sparkles', 'heart_eyes_cat', 'raised_hands', 'clap', 'fire',
            'beers', 'fish_cake'
        ],
        'sadness': [
            'sadparrot', 'pouting_cat', 'thumbsdown', 'wind_blowing_face',
            'broken_heart', 'greyhound'
        ]
    }
    # Pick a random emoji matching the appropriate emotion
    perfect_choice = random.choice(the_database[emotion])
    logging.info("We have selected the wonderful %s for this event",
                 perfect_choice)
    # Add it as a reaction to the message
    slack_client.api_call(
        "reactions.add",
        channel=channel,
        name=perfect_choice,
        timestamp=timestamp)


def parse_slack_output(slack_rtm_output):
    """
    The Slack Real Time Messaging API is an events firehose. This parsing
    function returns the last-seen message if there is one, otherwise returns
    None
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            # We are a creepy bot, we listen to everything you say
            if output and 'text' in output:
                return output
    return None


def try_load_env_var(var_name):
    """Read environment variables into a configuration object

    Args:
        var_name (str): Environment variable name to attempt to read
    """
    value = None
    if var_name in os.environ:
        value = os.environ[var_name]
    else:
        logging.info(
            "Environment variable %s is not set. Will try to read from command-line",
            var_name)
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--debug",
        dest="debug",
        help="Read input from debug file instead of user input",
        type=str,
        required=False)
    parser.add_argument(
        "--bx-username",
        dest="bx_username",
        help="Bluemix Tone Analyzer username",
        type=str,
        required=False,
        default=try_load_env_var("BX_USERNAME"))
    parser.add_argument(
        "--bx-password",
        dest="bx_password",
        help="Bluemix Tone Analyzer password",
        type=str,
        required=False,
        default=try_load_env_var("BX_PASSWORD"))
    parser.add_argument(
        "--slack-token",
        dest="slack_token",
        help="Slack client token",
        type=str,
        required=False,
        default=try_load_env_var("SLACK_TOKEN"))
    args = parser.parse_args()
    if not (args.bx_username and args.bx_password and args.slack_token):
        parser.print_help()
        sys.exit(1)

    eb = EmojiBot(
        bx_username=args.bx_username,
        bx_password=args.bx_password,
        slack_token=args.slack_token)
    eb.listen()


if __name__ == "__main__":
    main()
