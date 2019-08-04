import slack
import os
import argparse

from dnd_helper import DNDHelper


@slack.RTMClient.run_on(event="message")
def handle_rolls(**payload):
    if any(key not in payload
           for key in ("data", "web_client")):
        return
    data = payload["data"]
    web_client = payload["web_client"]
    
    if any(key not in data
           for key in ("text", "channel", "user")):
        return
    
    resp = dnd_helper.handle_command(data["user"], data["text"])
    if resp:
        web_client.chat_postMessage(
            channel=data["channel"],
            text=resp
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l", "--load",
        default="minatoris",
        help="Load a game by default on start")
    args = parser.parse_args()
    dnd_helper = DNDHelper(args.load)
    slack_token = os.environ["slack_token"]
    rtm_client = slack.RTMClient(token=slack_token)
    rtm_client.start()
