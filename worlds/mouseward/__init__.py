import json
import os
from BaseClasses import Item, ItemClassification, Location, Tutorial
from worlds.AutoWorld import WebWorld, World

from .Options import MousewardOptions
from .Regions import create_dynamic_regions

# Load the JSON file at the module level
world_data_path = os.path.join(os.path.dirname(__file__), 'world_data.json')
try:
    with open(world_data_path, 'r') as f:
        world_data = json.load(f)
except FileNotFoundError:
    world_data = {"regions": [], "locations": [], "items": []}

# Dynamically populate the ID maps directly from the Unity export
item_name_to_id = {item["code_name"]: item["id"] for item in world_data.get("items", [])}
location_name_to_id = {loc["code_name"]: loc["id"] for loc in world_data.get("locations", [])}

# Reverse lookup for parsing rules
id_to_item_name = {item["id"]: item["code_name"] for item in world_data.get("items", [])}


class MousewardWeb(WebWorld):
    theme = "party"
    setup = Tutorial(
        "Multiworld Setup Guide",
        "A guide to setting up Mouseward for Archipelago.",
        "English",
        "setup_en.md",
        "setup/en",
        ["Cookie966507"]
    )
    tutorials = [setup]


class MousewardItem(Item):
    game: str = "Mouseward"


class MousewardLocation(Location):
    game: str = "Mouseward"


class MousewardWorld(World):
    """Mouseward is a soulslike collectathon RPG."""

    game = "Mouseward"
    web = MousewardWeb()

    options_dataclass = MousewardOptions
    options: MousewardOptions

    item_name_to_id = item_name_to_id
    location_name_to_id = location_name_to_id

    def create_item(self, name: str) -> MousewardItem:
        # Find the item data from the JSON to get its classification
        item_data = next((i for i in world_data["items"] if i["code_name"] == name), None)

        classification = ItemClassification.filler
        if item_data:
            class_str = item_data.get("classification", "filler").lower()
            if class_str == "progression":
                classification = ItemClassification.progression
            elif class_str == "useful":
                classification = ItemClassification.useful
            elif class_str == "trap":
                classification = ItemClassification.trap

        return MousewardItem(name, classification, self.item_name_to_id[name], self.player)

    def create_regions(self):
        """
        Creates all regions and locations based on the user's options.
        """
        self.multiworld.get_region("Menu", self.player)  # Ensure Menu exists early

        # Iterate through the JSON and only instantiate active locations
        for loc in world_data.get("locations", []):
            loc_name = loc["code_name"]
            sanity_req = loc.get("sanity_requirement", 0)

            # Check the sanity requirement against the player's chosen options
            is_active = False
            if sanity_req == 0:
                is_active = True
            elif sanity_req == 1 and self.options.code_1_sanity:
                is_active = True
            elif sanity_req == 2 and self.options.code_2_sanity:
                is_active = True

            # If the location is valid for this seed, create it!
            if is_active:
                loc_obj = MousewardLocation(self.player, loc_name, self.location_name_to_id[loc_name])
                self.multiworld.clear_location_cache()

        # Connect the regions and apply the lambda rules
        create_dynamic_regions(self, world_data, id_to_item_name)

    def create_items(self):
        """
        Fills the item pool.
        """
        itempool = []
        for item_name in self.item_name_to_id.keys():
            #TODO
            # In the full implementation, we will compare total locations to total items
            # and pad with junk/stardust if there's a discrepancy.
            itempool.append(self.create_item(item_name))

        self.multiworld.itempool += itempool

    def set_rules(self):
        """
        Rules are dynamically attached to locations/regions during create_regions,
        but global completion conditions go here.
        """
        self.multiworld.completion_condition[self.player] = lambda state: state.has("Victory", self.player)
        pass

    def fill_slot_data(self) -> dict:
        """
        Data passed back to the Unity client upon connection.
        """
        return {
            "code_1_sanity": self.options.code_1_sanity.value,
            "code_2_sanity": self.options.code_2_sanity.value,
            "death_link": self.options.death_link.value,
            # Pass the seed to ensure local randomizer elements match
            "game_seed": self.multiworld.seed
        }