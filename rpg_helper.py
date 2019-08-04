'''The main RPG helper logic. Receives commands, and returns responses.'''
import json
import os
from random import randint

import regex as re

class Stats(dict):
    '''Special dictionary to parse stats and create modifiers automatically.'''
    def __init__(self, from_dict):
        super().__init__()
        for key, value in from_dict.items():
            self[key] = value

    def __setitem__(self, key, value):
        '''If special attribute is set, create the mod version of it.'''
        if key in set(["str", "dex", "con", "int", "wis", "cha"]):
            super().__setitem__(key + "mod", Stats.get_modifier(value))
        return super().__setitem__(key, value)

    @staticmethod
    def get_modifier(value):
        '''Generate the attribute mod (as string).'''
        mod = int(value/2) - 5
        return str(mod) if mod < 0 else f"+{mod}"


class RPGHelper():
    '''Main RPG helper class.'''
    def __init__(self, game):
        # All the macros for the game.
        self.macros = dict()
        # All the slack/discord uuids are mapped to characters.
        self.uuid_map = dict()
        # The stats of each character.
        self.pc_stats = dict()
        # The game being played.
        self.game = None
        if game:
            self.load_game(game)

    def handle_command(self, user, message):
        '''Parse and execute slack/discord message and respond if needed.'''
        parse = re.match(r"!([a-zA-Z0-9_\-]+?)\s+(.*)$", message)

        if parse:
            # Not a message that the bot needs to respond to.
            return None
        command, args = parse.groups()
        if command == "load":
            # Loads a new game with new characters and macros.
            return self.load_game(args)
        if command == "roll":
            # Rolls a particular stat. parameter user is the initiator.
            if not self.game:
                return (
                    "No game has been loaded. "
                    "Load using command `!load <game>`")
            return self.handle_roll(user, args)
        return None

    def load_game(self, game):
        '''Loads a new game from the folder with name {game}'''
        was_loaded = self.game
        if not os.path.exists(f"{game}"):
            return f"Game path {game} does not exist"
        self.macros = json.load(open(f"{game}/macros.json"))
        self.uuid_map = json.load(open(f"{game}/uuid_map.json"))
        self.pc_stats = {
            fname[:-5]: Stats(json.load(open(f"{game}/PC_files/{fname}")))
            for fname in os.listdir(f"{game}/PC_files")
            if fname.endswith(".json")
        }
        self.game = game

        if was_loaded:
            return f"Game {was_loaded} was replaced with game {game}"
        return f"New game {game} loaded"

    def handle_roll(self, user, roll_command):
        '''Responds to a roll command by {user}.'''
        return self.roll(user, self.resolve_command(user, roll_command))

    def resolve_command(self, user, roll_command):
        '''Resolves a macro, if a macro is detected.'''
        user = str(user)
        if (user not in self.uuid_map
                or self.uuid_map[user] not in self.pc_stats):
            print(user, list(self.pc_stats.keys()))
            # The user is not in the list, and does not have
            # stats to roll from. Hopefully this command does
            # not need to be resolved.
            return roll_command
        stats = self.pc_stats[self.uuid_map[user]]
        prof = RPGHelper.get_proficiency_by_level(stats["level"])
        parse = re.match(r"(.*?)(\s+[A|D])?$", roll_command)
        if not parse:
            # Unknown command, the roll function will deal with it.
            return roll_command
        command, adv_or_disadv = parse.groups()
        if command in self.macros:
            # Resolve the macro format with the key values
            # in the stats dictionary.
            return self.macros[command].format(
                **stats,
                proficiency=(
                    prof if command in stats["proficient_rolls"] else ""),
                adv_or_disadv=adv_or_disadv if adv_or_disadv else "")
        # It is not a known macro.
        return roll_command

    @staticmethod
    def get_proficiency_by_level(level):
        '''Gets the proficiency modifier based on level of character.'''
        if level in range(5):
            return "+2"
        if level in range(5, 9):
            return "+3"
        if level in range(9, 13):
            return "+4"
        if level in range(13, 17):
            return "+5"
        if level in range(17, 21):
            return "+6"
        return ""

    @staticmethod
    def roll(user, roll_command):
        '''Rolls a command resolved to the base form EG. d20+2 A'''
        parse = re.match(
            r"([0-9]*)d([0-9]+)\s*([+\-]\s*[0-9]+)*(\s+[A|D])?",
            roll_command.strip())
        if not parse:
            return f"<@{user}> Unknown command: Eg: !roll 4d6+2"

        # Forget the third group as by default only the last capture of it
        # is read and returned
        number, sides, _, adv = parse.groups()
        # Here we actually read all the captures. (Regex is the best!)
        constants = parse.captures(3)

        # Default number is 1. Eg. d20 resolves to 1d20.
        number = int(number) if number else 1
        # Pray to RNGesus.
        rolls = [randint(1, int(sides)) for i in range(int(number))]
        # Needed if Adv or Disadv is required.
        rerolls = [randint(1, int(sides)) for i in range(int(number))]
        if adv:
            adv = adv.strip()
        if adv == "A" and sum(rerolls) > sum(rolls):
            true_rolls = rerolls
        elif adv == "D" and sum(rerolls) < sum(rolls):
            true_rolls = rerolls
        else:
            true_rolls = rolls
        # Adding true_rolls and all constants parsed.
        total = sum(
            true_rolls + [
                int(re.sub(r"\s+", "", constant))
                for constant in constants
                if constant
            ]
        )
        if adv:
            # The format of the response when A or D was set.
            adv_text = "ADV" if adv == "A" else "DISADV"
            return (
                f"<@{user}> rolled `{roll_command}`\n"
                f"```"
                f"{repr(rolls)}, {repr(rerolls)}\n"
                f"Total ({adv_text}): {total}"
                f"```")
        # The format of the response when A or D was not set.
        return (f"<@{user}> rolled `{roll_command}`\n"
                f"```"
                f"{repr(rolls)}\n"
                f"Total: {total}"
                f"```")
