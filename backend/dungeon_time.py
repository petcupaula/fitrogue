from ruamel.yaml import YAML
import random
import ruamel.yaml
import math

available_attributes = ["attack", "attack_max", "health", "armor", "stamina", "effect"]
monster_attributes = [""]
global combat_log
combat_log = []
tribes = ["👺", "👻", "💀", "🤖", "👽"]
food = ["🥗", "🥙", "🥦", "🥬", "🥙", "🍲", "🍛", "🧆"]
friend = ["🥺", "🤩", "🧐", "🤪", "😚", "🥰", "😇", "😬"]

yaml = YAML(typ='safe')  # default, if not specfied, is 'rt' (round-trip)
with open("backend/monsters.yaml", "r") as monster_file:
    monster_list = yaml.load(monster_file)
with open("backend/equipment.yaml", "r") as equipment_file:
    equipment_list = yaml.load(equipment_file)

global hero_attributes
global max_stamina
max_stamina = 15
stamina_per_attack = 10
hero_attributes = {
    "isHero": True,
    "icon": "😀",
    "name": "Hero",
    "attack": 10,
    "attack_max": 20,
    "health": 150,
    "armor": 0,
    "stamina": 50,
    "effect": []
}


class Character():
    def __init__(self, attributes: dict):
        self.is_alive = True
        self.attributes = attributes

    def equip(self, equipment_name: str):
        if equipment_name in equipment_list:
            equipment = equipment_list[equipment_name]
            for attribute in available_attributes:
                if attribute in equipment:
                    self.attributes[attribute] = self.attributes[attribute] + equipment[attribute]

    def attack(self, opponent):
        self.attributes["stamina"] = self.attributes["stamina"] - stamina_per_attack
        if self.attributes["stamina"] <= 0:
            if(self.attributes.get('isHero', False)):
                self.attributes["stamina"] = max_stamina
                combat_log.append(["😴", opponent.attributes["icon"], f"Stamina recovered {random.choice(food)}!", self.see_stats()])
            else:
                combat_log.append([opponent.attributes["icon"], f"{self.attributes['icon']}", f"{self.attributes['name']} is too tired to fight more", opponent.see_stats()])
            # print(combat_log[-1])
            return 0
        bonus_damage = 0
        if(self.attributes.get('isHero', False)):
            if opponent.attributes["icon"] == "👺" and "Goblin Smasher" in self.attributes.get("effect", []):
                bonus_damage = 2
            if opponent.attributes["icon"] == "👻" and "Dream Warden" in self.attributes.get("effect", []):
                bonus_damage = 2
            if opponent.attributes["icon"] == "🤖" and "Short Circuit" in self.attributes.get("effect", []):
                bonus_damage = 2
            if opponent.attributes["icon"] == "👽" and "Probe Protector" in self.attributes.get("effect", []):
                bonus_damage = 2
        damage = random.randint(self.attributes["attack"], self.attributes["attack_max"]) + bonus_damage
        opponent.get_hurt(damage, self)

    def get_hurt(self, raw_damage, opponent):
        raw_damage = round(raw_damage, 2)
        damage = round(raw_damage - self.attributes["armor"], 2)
        if damage < 0:
            damage = 0
        blocked = round(raw_damage - damage, 2)
        self.attributes["health"] = round(self.attributes["health"] - damage, 2)
        if self.attributes.get('isHero', False):
            combat_log.append([f"{self.attributes['icon']}🛡", f"{opponent.attributes['icon']}⚔️", f"{self.attributes['name']} blocked {blocked} and took {damage}.", self.see_stats()])
        else:
            combat_log.append([f"{opponent.attributes['icon']}⚔️", f"{self.attributes['icon']}🛡", f"{opponent.attributes['name']} attacks for {raw_damage}, {self.attributes['name']} blocked {blocked} and took {damage}.", opponent.see_stats()])
        # print(combat_log[-1])
        if self.attributes["health"] > 0:
            if self.attributes.get('isHero', False):
                if self.attributes["health"] <= 50:
                    self.attributes['icon'] = "😟"
                if self.attributes["health"] <= 20:
                    self.attributes['icon'] = "🥵"
            return self.attributes["health"]
        else:
            if not self.attributes.get('isHero', False):
                combat_log.append([f"🥳", f"{self.attributes['icon']}☠️", f"{self.attributes['name']} has been defeated", opponent.see_stats()])
            self.is_alive = False
            # print(combat_log[-1])
            return 0

    def see_stats(self):
        return f"ATK:{self.attributes['attack']}-{self.attributes['attack_max']} DEF:{self.attributes['armor']} LIFE:{self.attributes['health']} STAM:{self.attributes['stamina']}\nPERKS: {','.join(self.attributes['effect'])}"
        return self.attributes.items()


def choose_random_monster(type: str = "basic", tribe: str = None):
    if tribe is not None:
        monsters_in_tribe = monster_list[type][tribe]
    else:
        random_tribe = random.sample(list(monster_list[type]), 1)[0]
        monsters_in_tribe = monster_list[type][random_tribe]

    attributes = random.sample(monsters_in_tribe, 1)[0]
    return attributes


def enter_the_dungeon(hero: Character):
    monsters = []
    number_of_monsters = 16
    for i in range(0, number_of_monsters):
        if i == 9:
            monster_attributes = choose_random_monster(type="boss", tribe="first")
        elif i == 15:
            monster_attributes = choose_random_monster(type="boss", tribe="second")
        else:
            monster_attributes = choose_random_monster()
        monsters.append(Character(monster_attributes.copy()))
    # for monster in monsters:
    #     monster.see_stats()

    while (hero.is_alive > 0 and len(monsters) > 0):
        monster = monsters.pop(0)
        combat_log.append([f"{hero.attributes['icon']}", f"{monster.attributes['icon']}", f"You've encountered a {monster.attributes['name']}.", hero.see_stats()])
        # hero.attributes["stamina"] = max_stamina
        while (monster.is_alive and hero.is_alive):
            raw_damage = hero.attack(monster)
            if monster.is_alive:
                raw_damage = monster.attack(hero)

    if hero.is_alive:
        combat_log.append([f"😀            ", f"", f"", hero.see_stats()])
        combat_log.append([f"😁            ", f"", f"", hero.see_stats()])
        combat_log.append([f"🥳   😎🤩", f"", f"", hero.see_stats()])
        combat_log.append([f"🥳🎊 🎉😎🤩🎉", f"", f"CONGRATULATIONS! You have completed the game!", hero.see_stats()])
    else:
        combat_log.append([f"☠️ ", f"", f"You died on level {number_of_monsters- len(monsters)}", hero.see_stats()])
        combat_log.append([f"☠️ 😢", f"", f"", hero.see_stats()])
        combat_log.append([f"☠️ 😢😭", f"", f"", hero.see_stats()])
        combat_log.append([f"☠️ 😢😭😱", f"", f"Your friends miss you", hero.see_stats()])


def character_creation(equipment_names):
    combat_log.append(["😔", "", "", ""])
    combat_log.append(["😏", "", "", ""])
    combat_log.append(["😁", "", "Welcome adventurer", ""])
    combat_log.append(["😀", "", "", ""])
    hero = Character(hero_attributes)
    hero = hero_equip_items(equipment_names, hero)
    return hero


def hero_equip_items(equipment_names: list, hero: Character):
    for item in equipment_names:
        if item in equipment_list:
            hero.equip(item)
            item_icon = equipment_list[item]["icon"]
            combat_log.append([f"{hero.attributes['icon']}{item_icon}", "", f"{equipment_list[item]['display_name']} obtained from {random.choice(friend)}", ""])
    hero_attributes = hero.attributes.copy()
    max_stamina = hero_attributes["stamina"]
    return hero


def run_dungeon(items):
    global combat_log
    combat_log = []
    hero = character_creation(items)
    enter_the_dungeon(hero)
    return combat_log


if __name__ == "__main__":
    hero = character_creation(["boxing_gloves", "fish", "rose_hat", "the_armored_blouse"])
    hero.see_stats()
    enter_the_dungeon(hero)
    for line in combat_log:
        print("\t".join(line))
