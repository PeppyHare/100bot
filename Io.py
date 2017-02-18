import json
from watson_developer_cloud import ToneAnalyzerV3
import fileinput
from pprint import pprint
import argparse

#Authors: Alex French, Samuel Gass, Margaret Yim

topic_limit = 5

def talkAboutTopic(tone_analyzer, filename="", debug=False):
	emotions = dict(anger=0, disgust=0, fear=0, joy=0, sadness=0)

	if debug:
		with open(filename) as resp_file:    
			resp_obj = json.load(resp_file)
		topic = resp_obj["topic"]
	else:
		topic = input("What would you like to talk about?\n")
	
	for i in range(topic_limit):	
		if debug:
			resp = resp_obj["responses"][i]
		else:
			resp = input("Tell me more about this.\n")

		analysis = tone_analyzer.tone(text=resp)
		for category in analysis["document_tone"]["tone_categories"]:
			if category["category_id"] == "emotion_tone":
				for tone in category["tones"]:
					if tone["tone_id"] == "anger":
						emotions['anger'] = (emotions['anger']*i + tone["score"])/(i+1)
					if tone["tone_id"] == "disgust":
						emotions['disgust'] = (emotions['disgust']*i + tone["score"])/(i+1)
					if tone["tone_id"] == "fear":
						emotions['fear'] = (emotions['fear']*i + tone["score"])/(i+1)
					if tone["tone_id"] == "joy":
						emotions['joy'] = (emotions['joy']*i + tone["score"])/(i+1)
					if tone["tone_id"] == "sadness":
						emotions['sadness'] = (emotions['sadness']*i + tone["score"])/(i+1)

	max_key = max(emotions, key=emotions.get)
	if emotions[max_key] < 0.5:
		print("I'm not sure how you feel about this. Let's try another topic.\n")
	else:
		if max_key == "anger":
			print("You seem angry about this. I'm sorry. Let's talk about something else.\n")
		if max_key == "disgust":
			print("You seem disgusted by this. I'm sorry. Let's talk about something else.\n")
		if max_key == "fear":
			print("You seem scared by this. Everything will be okay. Let's talk about something else.\n")
		if max_key == "joy":
			print("You seem happy about this! I'm glad for you. Let's talk about something else.\n")
		if max_key == "sadness":
			print("You seem sad about this. I'm sorry. Let's talk about something else.\n")

def main():
	with open('creds.json') as cred_file:    
		cred_obj = json.load(cred_file)

	tone_analyzer = ToneAnalyzerV3(
	   username=cred_obj["username"],
	   password=cred_obj["password"],
	   version='2016-05-19')

	parser = argparse.ArgumentParser()
	parser.add_argument("--debug", help="Read input from debug file instead of user input", type=str)
	args = parser.parse_args()

	if args.debug:
		talkAboutTopic(tone_analyzer, args.debug, True)
	else:
		name=input("Hello, my name is Io. What is your name?\n")
		print("Hello, " + name)
		while(1):
			talkAboutTopic(tone_analyzer)

if __name__ == "__main__":
	main()