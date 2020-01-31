'''Runs the Discord RPG Helper bot.'''
import argparse
import os

import discord

from rpg_helper import RPGHelper


class DiscordClient(discord.Client):
    '''Client that handles discord messages.'''

    def __init__(self, helper):
        super().__init__()
        self.rpg_helper = helper

    async def on_ready(self):
        '''Logging the bot login.'''
        print("Logged on as", self.user)

    async def on_message(self, message):
        '''Observing each message and responding if needed.'''
        if message.author == self.user:
            return
        userid = message.author.id
        resp = self.rpg_helper.handle_command(userid, message.content)
        if resp:
            await message.channel.send(resp)

if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument(
        "-l", "--load",
        default="seonstra",
        help="Load a game by default on start")
    ARGS = PARSER.parse_args()
    while True:
        try:
            DiscordClient(RPGHelper(ARGS.load)).run(os.environ["discord_token"])
        except Exception:
            print ("Exception was caught")
