'''Runs the Slack RPG Helper bot.'''
import os
import argparse

import slack

from rpg_helper import RPGHelper


@slack.RTMClient.run_on(event="message")
def respond_to_messages(**payload):
    '''Responds to messages on every channel if needed.'''
    if any(key not in payload
           for key in ("data", "web_client")):
        return
    data = payload["data"]
    web_client = payload["web_client"]

    if any(key not in data
           for key in ("text", "channel", "user")):
        return

    resp = RPGHELPER.handle_command(data["user"], data["text"])
    if resp:
        web_client.chat_postMessage(
            channel=data["channel"],
            text=resp
        )


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument(
        "-l", "--load",
        default="minatoris",
        help="Load a game by default on start")
    ARGS = PARSER.parse_args()
    RPGHELPER = RPGHelper(ARGS.load)
    slack.RTMClient(token=os.environ["slack_token"]).start()
