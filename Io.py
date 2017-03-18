"""
Authors: Alex French, Samuel Gass, Margaret Yim
"""

import json
from watson_developer_cloud import ToneAnalyzerV3
import fileinput
from pprint import pprint
import argparse
from slackclient import SlackClient
import time


topic_limit = 5
bot_name = 'io'
AT_BOT = ""


def talkAboutTopic(tone_analyzer,
                   slack_client,
                   command,
                   channel,
                   filename="",
                   debug=False):
    emotions = dict(anger=0, disgust=0, fear=0, joy=0, sadness=0)

    if debug:
        with open(filename) as resp_file:
            resp_obj = json.load(resp_file)
        topic = resp_obj["topic"]
    else:
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text="What would you like to talk about?",
            as_user=True)
        while True:
            topic, channel = parse_slack_output(slack_client.rtm_read())
            if topic and channel:
                break

    for i in range(topic_limit):
        if debug:
            resp = resp_obj["responses"][i]
        else:
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text="Tell me more",
                as_user=True)
            while True:
                resp, channel = parse_slack_output(slack_client.rtm_read())
                if resp and channel:
                    break

        analysis = tone_analyzer.tone(text=resp)
        for category in analysis["document_tone"]["tone_categories"]:
            if category["category_id"] == "emotion_tone":
                for tone in category["tones"]:
                    if tone["tone_id"] == "anger":
                        emotions['anger'] = (
                            emotions['anger'] * i + tone["score"]) / (i + 1)
                    if tone["tone_id"] == "disgust":
                        emotions['disgust'] = (
                            emotions['disgust'] * i + tone["score"]) / (i + 1)
                    if tone["tone_id"] == "fear":
                        emotions['fear'] = (
                            emotions['fear'] * i + tone["score"]) / (i + 1)
                    if tone["tone_id"] == "joy":
                        emotions['joy'] = (
                            emotions['joy'] * i + tone["score"]) / (i + 1)
                    if tone["tone_id"] == "sadness":
                        emotions['sadness'] = (
                            emotions['sadness'] * i + tone["score"]) / (i + 1)

    max_key = max(emotions, key=emotions.get)
    if emotions[max_key] < 0.5:
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text="I'm not sure how you feel about this. Let's try another topic.",
            as_user=True)
    else:
        if max_key == "anger":
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text="You seem angry about this. I'm sorry. Let's talk about something else.",
                as_user=True)
        if max_key == "disgust":
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text="You seem disgusted by this. I'm sorry. Let's talk about something else.",
                as_user=True)
        if max_key == "fear":
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text="You seem scared by this. Everything will be okay. Let's talk about something else.",
                as_user=True)
        if max_key == "joy":
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text="You seem happy about this! I'm glad for you. Let's talk about something else.",
                as_user=True)
        if max_key == "sadness":
            slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text="You seem sad about this. I'm sorry. Let's talk about something else.",
                as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                    output['channel']
    return None, None


def main():
    with open('creds.json') as cred_file:
        cred_obj = json.load(cred_file)

    slack_client = SlackClient(cred_obj["slack_token"])
    global AT_BOT
    AT_BOT = "<@" + cred_obj["bot_id"] + ">"

    tone_analyzer = ToneAnalyzerV3(
        username=cred_obj["username"],
        password=cred_obj["password"],
        version='2016-05-19')

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--debug",
        help="Read input from debug file instead of user input",
        type=str)
    args = parser.parse_args()

    READ_WEBSOCKET_DELAY = 1  # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                if args.debug:
                    talkAboutTopic(tone_analyzer, slack_client, command,
                                   channel, args.debug, True)
                else:
                    talkAboutTopic(tone_analyzer, slack_client, command,
                                   channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")


if __name__ == "__main__":
    main()
