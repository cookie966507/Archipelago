from BaseClasses import MultiWorld, Region
from worlds.generic.Rules import add_rule

def create_lambda_rule(world, rules_data, id_to_name_map):
    """
    Translates the JSON logic arrays [ {"or_group": [ID, ID]} ] into an Archipelago lambda rule.
    """
    if not rules_data:
        return lambda state: True

    translated_groups = []
    for group in rules_data:
        or_group = group.get("or_group", [])
        # Translate the global integer IDs back into the string code_names
        translated_or = [id_to_name_map[item_id] for item_id in or_group if item_id in id_to_name_map]

        if translated_or:
            translated_groups.append(translated_or)

    # If the rule ended up empty after translation, default to True
    if not translated_groups:
        return lambda state: True

    # Return the composite logic function: AND( OR(items), OR(items) )
    return lambda state: all(
        any(state.has(item_name, world.player) for item_name in and_group)
        for and_group in translated_groups
    )


def create_dynamic_regions(world, world_data, id_to_name_map):
    """
    Builds the region graph using the hardcoded Menu and the dynamic JSON data.
    """
    multiworld: MultiWorld = world.multiworld
    player: int = world.player

    # 1. Create the Hardcoded Root Region
    menu_region = Region("Menu", player, multiworld)
    multiworld.regions.append(menu_region)

    # Dictionary to track our created regions
    created_regions = {"Menu": menu_region}

    # 2. Generate all Dynamic Regions from the JSON
    for region_data in world_data.get("regions", []):
        region_name = region_data["name"]
        region = Region(region_name, player, multiworld)
        created_regions[region_name] = region
        multiworld.regions.append(region)

    # 3. Add Locations to their respective Regions
    # (We only iterate through the locations that were instantiated in __init__.py based on options)
    for loc_data in world_data.get("locations", []):
        loc_name = loc_data["code_name"]

        try:
            # Check if this location was included in the active pool
            location = world.get_location(loc_name)
            region_name = loc_data["region"]

            if region_name in created_regions:
                region = created_regions[region_name]
                location.parent_region = region
                region.locations.append(location)

                # Apply any location-specific item requirements
                if loc_data.get("requires_ids"):
                    rule_func = create_lambda_rule(world, loc_data["requires_ids"], id_to_name_map)
                    add_rule(location, rule_func)
        except KeyError:
            # Location is disabled by options, safely ignore
            continue

    # 4. Connect the Root to the Starting Zone
    starting_zone_name = "Ivory"
    if starting_zone_name in created_regions:
        menu_region.connect(created_regions[starting_zone_name])

    # 5. Connect all Dynamic Regions
    for region_data in world_data.get("regions", []):
        source_region = created_regions[region_data["name"]]

        for connection in region_data.get("connections", []):
            target_region_name = connection["target"]

            if target_region_name in created_regions:
                target_region = created_regions[target_region_name]
                rule_func = create_lambda_rule(world, connection["rules"], id_to_name_map)
                source_region.connect(target_region, rule=rule_func)