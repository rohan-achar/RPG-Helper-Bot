import os
import regex as re
import time
import json
from random import randint

class Stats(dict):
    def __init__(self, from_dict):
        super().__init__()
        for key, value in from_dict.items():
            self[key] = value

    def __setitem__(self, key, value):
        if key in set(["str", "dex", "con", "int", "wis", "cha"]):
            super().__setitem__(key + "mod", self.get_modifier(value))
        return super().__setitem__(key, value)

    def get_modifier(self, value):
        mod = int(value/2) - 5
        return str(mod) if mod < 0 else f"+{mod}"


class DNDHelper(object):
    def __init__(self, game):
        self.macros = dict()
        self.uuid_map = dict()
        self.pc_stats = dict()
        self.game = None
        if game:
            self.load_game(game)
    
    def handle_command(self, user, message):
        parse = re.match(r"!([a-zA-Z0-9_\-]+?)\s+(.*)$", message)
        
        if not parse:
            return
        command, args = parse.groups()
        if command == "load":
            return self.load_game(args)
        if command == "roll":
            if not self.game:
                return (
                    "No game has been loaded. "
                    "Load using command `!load <game>`")
            return self.handle_roll(user, args)

    def load_game(self, game):
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
        return self.roll(user, self.resolve_command(user, roll_command))

    def roll(self, user, roll_command):
        parse = re.match(
            r"([0-9]*)d([0-9]+)\s*([+\-]\s*[0-9]+)*(\s+[A|D])?",
            roll_command.strip())
        if not parse:
            return f"<@{user}> Unknown command: Eg: !roll 4d6+2"

        number, sides, _, adv = parse.groups()
        constants = parse.captures(3)
        
        number = int(number) if number else 1
        rolls = [randint(1, int(sides)) for i in range(int(number))]
        rerolls = [randint(1, int(sides)) for i in range(int(number))]
        if adv:
            adv = adv.strip()
        if adv == "A" and sum(rerolls) > sum(rolls):
            true_rolls = rerolls
        elif adv == "D" and sum(rerolls) < sum(rolls):
            true_rolls = rerolls
        else:
            true_rolls = rolls
        total = sum(
            true_rolls + [
                int(re.sub(r"\s+", "", constant))
                for constant in constants
                if constant
            ]
        )
        if adv:
            adv_text = "ADV" if adv == "A" else "DISADV"
            return (
                f"<@{user}> rolled `{roll_command}`\n"
                f"```"
                f"{repr(rolls)}, {repr(rerolls)}\n"
                f"Total ({adv_text}): {total}"
                f"```")
        else:
            return (f"<@{user}> rolled `{roll_command}`\n"
                    f"```"
                    f"{repr(rolls)}\n"
                    f"Total: {total}"
                    f"```")
        
    def get_proficiency_by_level(self, level):
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

    def resolve_command(self, user, roll_command):
        user = str(user)
        if (user not in self.uuid_map 
                or self.uuid_map[user] not in self.pc_stats):
            print (user, list(self.pc_stats.keys()))
            return roll_command
        stats = self.pc_stats[self.uuid_map[user]]
        prof = self.get_proficiency_by_level(stats["level"])
        parse = re.match(r"(.*?)(\s+[A|D])?$", roll_command)
        if not parse:
            return roll_command
        command, adv_or_disadv = parse.groups()
        if command in self.macros:
            return self.macros[command].format(
                **stats,
                proficiency=(
                    prof if command in stats["proficient_rolls"] else ""),
                adv_or_disadv=adv_or_disadv if adv_or_disadv else "")
        return roll_command
