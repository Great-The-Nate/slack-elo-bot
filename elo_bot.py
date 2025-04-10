import os
import requests
import re
import json
from flask import Flask, request, jsonify
from slackeventsapi import SlackEventAdapter

from elo_system import ELO_System

app = Flask(__name__)

SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
VERIFICATION_TOKEN = os.environ["VERIFICATION_TOKEN"]
ELO_BOT_CHANNEL_ID = "C08LY4U1H63" # #elo-bot channel ID
slack_events_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, "/slack/events", app)

elo_system = None

SLACK_ID_REGEX = r"<(@[A-Z0-9]*)(?:\|[a-z0-9._-]*)?>"

@app.route('/leaderboard', methods=['POST'])
def leaderboard():
    data = request.form
    if not data.get('token') == VERIFICATION_TOKEN:
        # This is not ideal but better than nothing
        return

    text = data.get('text')

    event_pattern = r"((?i:air|sport|standard))"
    match = re.match(event_pattern, text)
    event = match.groups()[0] if match else None
    
    by_elo_list, by_best_list, by_avg_list = elo_system.get_leaderboard(event)

    response_text = ""
    if not event:
        response_text = f"*ELO Leaderboard:*\n{by_elo_list}"
    else:
        response_text = f"*Leaderboard by Best in {event.lower().capitalize()}:*\n{by_best_list}\n*Leaderboard by Average in {event.lower().capitalize()}:*\n{by_avg_list}"

    # Acknowledge the request immediately (important for Slack)
    response = {
        "response_type": "ephemeral",  # "in_channel" for public, "ephemeral" for private
        "text": response_text
    }
    return jsonify(response)


@app.route('/record', methods=['POST'])
def record():
    data = request.form
    if not data.get('token') == VERIFICATION_TOKEN:
        return

    text = data.get('text')
    result = handle_score_list(text)

    response_text = ""
    if result:
        event, scores = result
        if len(scores) == 0:
            response_text = f"No scores listed :("
        else:
            scores = sorted(scores, key=lambda x: x[1], reverse=True)
            response_text = f"*Recorded {event.lower().capitalize()} Scores:*\n"+"\n".join([f"{i+1}. {s[0]} - {s[1]}" for i, s in enumerate(scores)])
    else:
        response_text = f"Invalid format, please write as: Event @User1 Score1 @User2 Score2 ..."
    
    response = {
        "response_type": "in_channel",
        "text": response_text
    }
    return jsonify(response)


@app.route('/duel', methods=['POST'])
def challenge_match():
    data = request.form
    if not data.get('token') == VERIFICATION_TOKEN:
        return

    text = data.get('text')
    result = handle_challenge_match(text)

    response_text = ""
    if not result is None:
        playerA, scoreA, playerB, scoreB, eloA, eloB, elo_delta = result
        eloA = round(eloA, 2)
        eloB = round(eloB, 2)
        elo_delta = round(elo_delta, 2)
        response_text = f"*{playerA}: {eloA - elo_delta} -> {eloA}*\n*{playerB}: {eloB + elo_delta} -> {eloB}*"
    else:
        response_text = f"Invalid format, please write as: @User1 Score1 - Score2 @User2"
    
    response = {
        "response_type": "in_channel",
        "text": response_text
    }
    return jsonify(response)


@slack_events_adapter.on("app_mention")
def app_mention(event_data):
    print(json.dumps(event_data, indent=2))
    text = event_data['event']['text']

    score_list_pattern = r"<@[A-Z0-9]*>\s*(?i:air|sport|standard)(?i:\s*pistol)?(\s*(<@[A-Z0-9]*>)\s*(\d{3}))+"
    challenge_match_pattern = r"<@[A-Z0-9]*>\s*<@[A-Z0-9]*>\s*\d+\s*-\s*\d+\s*<@[A-Z0-9]*>"

    result = None
    if re.match(score_list_pattern, text):
        result = handle_score_list(text)
    elif re.match(challenge_match_pattern, text):
        result = handle_challenge_match(text)
    
    if result:
        add_reaction("thumbsup", event_data['event']['ts'])
    else:
        add_reaction("thumbsdown", event_data['event']['ts'])
    return


def handle_score_list(text):
    event_pattern = r"((?i:air|sport|standard))(?i:\s*pistol)?\s*"
    scores_pattern = rf"{SLACK_ID_REGEX}\s*(\d+)"

    match = re.search(event_pattern, text)
    if not match:
        return None

    event = match.groups()[0]
    scores = re.findall(scores_pattern, text)
    scores = list(map(lambda s: (f"<{s[0]}>", s[1]), scores))
    
    result = elo_system.record_scores(event, scores)
    elo_system.save_to_json()
    return result


def handle_challenge_match(text):
    challenge_match_pattern = rf"(?:<@[A-Z0-9]*>)?\s*{SLACK_ID_REGEX}\s*(\d+)\s*-\s*(\d+)\s*{SLACK_ID_REGEX}"

    match = re.match(challenge_match_pattern, text)
    if not match:
        return None
    groups = match.groups()
    if not len(groups) == 4:
        return None

    playerA = f"<{groups[0]}>"
    scoreA = groups[1]
    scoreB = groups[2]
    playerB = f"<{groups[3]}>"

    eloA, eloB, elo_delta = elo_system.update_elo(playerA, scoreA, playerB, scoreB)
    elo_system.save_to_json()
    return playerA, scoreA, playerB, scoreB, eloA, eloB, elo_delta


def send_message(msg, channel=ELO_BOT_CHANNEL_ID):
    # set thread_ts to send as thread
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "channel": channel,
        "text": msg
    }
    r = requests.post("https://slack.com/api/chat.postMessage", headers=headers, data=json.dumps(payload))
    print("Send Message POST Response:", r.text)


def add_reaction(emoji_name, msg_timestamp, channel=ELO_BOT_CHANNEL_ID):
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "channel": channel,
        "name": emoji_name,
        "timestamp": msg_timestamp
    }
    r = requests.post("https://slack.com/api/reactions.add", headers=headers, data=json.dumps(payload))
    print("Add Reaction POST Response:", r.text)


if __name__ == "__main__":
    elo_system = ELO_System.from_json("scores.json")
    app.run(port=3000)

'''
TODO:
- List scores for a person
- modify elo based on match scores?
- more games with elo
- season system / tournament bracket
- fun messages for duel results
- better UI / message response formatting
'''