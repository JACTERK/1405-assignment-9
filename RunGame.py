# Assignment 09 - COMP 1405 - Friday, November 17th, 2023
# Jacob Terkuc - 101196620
# Owen Pearson -

# Pair Programming Questions
# Jacob Terkuc
# 1: Github and Voice Chat
# 2: I wrote a lot of my code myself, but we collaborated on coming up with the best way to implement the functions we
#    independently wrote as well as brainstormed.
# 3: The biggest one I ran into was figuring out the best way to format the settings.txt file.
# 4: We each rotated once, so Owen started the rotation as the driver, and I ended it as the driver.
# 5: Using live coding would definitely be an easier way to work more collaboratively on coding assignments, although
#    GitHub proved to be fairly useful.


import Duty
import random
import json


# Function to parse settings.txt file, returns a dictionary.
# Jacob Terkuc
def parse_settings() -> dict:
    # Attempt to load settings.txt file
    try:
        # Reads the file and converts the json data into a usable dictionary to be returned. Ignores lines
        # starting with '#'.
        with open("settings.txt", "r") as file:
            json_data = '\n'.join(line for line in file if not line.startswith('#'))

    # Exception if the file settings.txt is not found
    except FileNotFoundError:
        print("Error: No 'settings.txt' file found. Making one now... Please fill in the file with settings and rerun "
              "the program.")

        # This code block creates a new file settings.txt and fills it with comments and the default values. Uses json
        # formatting.
        # Creates a json file with the default settings in it on first run.
        with open('settings.txt', 'w') as file:
            file.write("# Debug (bool): Enables/disables debug output in terminal.\n")
            file.write("# Timescale (int): Multiplier used to determine the timescale.\n")
            file.write("# Probability (int): Used to determine the likelihood of an anomaly appearing.\n")
            file.write("# min_seconds_between_anomalies (int): Self explanatory, value is in seconds.\n")
            file.write("{\n")
            file.write('"debug": "False",\n')
            file.write('"timescale": 60,\n')
            file.write('"probability": 0.1,\n')
            file.write('"min_seconds_between_anomalies": 10\n')
            file.write('}')
        exit()

    # Return the json_data variable to be usable in the main function.
    return json.loads(json_data)


def main():
    # Loads settings using the parse_settings function.
    # Jacob Terkuc
    args = parse_settings()

    """
    The main function is mostly just here to setup the game and keep it running in a loop.
    It has a specific order of events that it follows.
    There are a lot of comments in here to help you understand what is going on, but 
    feel free to remove them if they impede your reading of the code.
    """

    # First, we set up all of the game data. 
    # This could have been done using the init() function's optional parameters,
    # but this should make it easier for you to modify it later.

    # These 'helper functions' just clean up the main function and make it more readable.
    # We need to add rooms to the game and we\ need to register what  anomalies are possible.

    add_rooms()
    register_anomalies()

    # Code block modified to use the variables from the args dict. - Jacob Terkuc
    # It might be cleaner to put all of these into their own helper function. Feel free to do that if you think it would be better!
    Duty.set_setting("debug", args["debug"])  # Setting this to True will show additional information to help you debug new anomalies
    Duty.set_setting("timescale", args["timescale"])
    Duty.set_setting("probability", args["probability"])
    Duty.set_setting("min_seconds_between_anomalies", args["min_seconds_between_anomalies"] * 60)

    # Initialize the game with all of the data we've just set up.
    Duty.init()

    # This is the main game loop. It will run until the game_running variable is set to False.
    game_running = True
    while game_running:
        # The game keeps track of time while the player is idle, so it is possible we will need
        # to create multiple anomalies at a time the next time the player types a command.
        # `number_of_anomalies_to_create` also takes our probability setting into account.
        n_anomalies = Duty.number_of_anomalies_to_create()

        # We create one anomaly at a time, and we'll write a small helper function to clean up the main function.
        for _ in range(n_anomalies):
            # Keep looping until we can create the anomaly, just in case one of them fails
            anomaly_created = False
            while not anomaly_created:
                anomaly_created = create_anomaly()

        # This will update the game status to check if we've lost the game or reached the end.
        # Update returns True if the game should keep going or False if it should end after this loop.
        game_running = Duty.update()

        # Display shows all of the game data. If update() determined the game should end, display() will show the end screen.
        Duty.display()

        # This will pause the loop and wait for the user to type something, running the appropriate commands
        # to handle their actions.
        Duty.handle_input()


def add_rooms():
    """
    Adds all of the rooms to the game. 
    Duty.add_room() takes a string for the name of a room and a list of strings for the items in the room.
    """
    Duty.add_room("Living Room", ["42\" TV Playing Golf", "Black Leather Sofa", "Circular Metal Coffee Table",
                                  "Wooden Bookshelf with 3 Shelves"])
    Duty.add_room("Kitchen", ["Gas Stove", "Retro Red Metal Refrigerator", "Oak Wooden Table", "4 Wooden Chairs"])
    Duty.add_room("Bedroom", ["Queen Size Bed", "Oak Wooden Nightstand", "Oak Wooden Dresser", "Oak Wooden Desk",
                              "Oak Wooden Chair"])
    Duty.add_room("Bathroom", ["4 Toilets with Oak Seats", "Chrome Sink", "Shower with Blue Tiles", "Medicine Cabinet"])


def register_anomalies():
    """
    Each anomaly we want to add to the game must be "Registered". 
    This is so the game knows what anomalies are possible.
    They will all be stored in UPPERCASE to make it easier to compare them later.
    """
    Duty.register_anomaly("CAMERA MALFUNCTION")
    Duty.register_anomaly("MISSING ITEM")
    Duty.register_anomaly("ITEM MOVEMENT")


def create_anomaly() -> bool:
    """
    This little helper function handles the control flow for three steps:
    1. Choose a random room that does not have an anomaly, because rooms can only have one anomaly.
    2. Choose a random anomaly from the list of registered anomalies.
    3. Create the anomaly in the room.

    Return True if an anomaly was created, False if no anomaly was created.
    """

    # Choose a random room that does not have an anomaly
    room = Duty.get_random_unchanged_room()

    # Pick a random anomaly from the list of registered anomalies
    # Note: It is possible that some anomalies you create can't work in every room.
    # Maybe you will need additional logic to make sure the anomaly makes sense in the room.
    anomaly = Duty.get_random_anomaly()

    # Camera Malfunction is actually a special one.
    # It will not show this camera when clicking through if 
    # It sees CAMERA MALFUNCTION as the anomaly name
    if anomaly == "CAMERA MALFUNCTION":
        # All anomalies are stores as all uppercase
        # Since a camera malfunction means no items are shown, we pass an empty list
        return Duty.add_anomaly("CAMERA MALFUNCTION", room, [])
    elif anomaly == "MISSING ITEM":
        # We pass the name of the room to these functions to separate out the logic
        return missing_item(room)
    elif anomaly == "ITEM MOVEMENT":
        return item_movement(room)
    # Owen Pearson
    elif anomaly == "NUMBER CHANGE":  # if anomaly "NUMBER CHANGE" is choose then call number_change() which handles modifying list and adding anomaly
        return number_change(room)
    else:
        print(f"ERROR: Anomaly {anomaly} not found")
        return False


def missing_item(room: str) -> bool:
    """
    Removes a random item from the room. This is a pretty straightforward one.
    1. Get the list of items in the room. (Duty.get_room_items())
    2. Choose a random item to remove. (random.randint())
    3. Make a copy of the list of items and remove the item from the copy. (list slicing)
    4. Create the anomaly with the new list of items. (Duty.add_anomaly())
    """
    items = Duty.get_room_items(room)
    item_index_to_remove = random.randint(0, len(items) - 1)
    new_items = items[:]
    new_items.pop(item_index_to_remove)

    # add_anomaly returns True if the anomaly was created, False if it was not.
    return Duty.add_anomaly("MISSING ITEM", room, new_items)


def item_movement(room: str) -> bool:
    """
    Re-arranges two items in a room. This one is a little more complicated.
    1. Get the list of items in the room. (Duty.get_room_items())
    2. Choose two random items to swap. (random.randint())
    3. Make a copy of the list of items and swap the two items. (list slicing)
    4. Create the anomaly with the new list of items. (Duty.add_anomaly())
    """

    items = Duty.get_room_items(room)

    # If there is only one item in the room, we can't move anything!
    if len(items) < 2:
        return False

    # Find two random items to swap
    item_to_move = random.randint(0, len(items) - 1)
    item_to_move_to = random.randint(0, len(items) - 1)

    # Make sure the two items are not the same
    while item_to_move == item_to_move_to:
        item_to_move_to = random.randint(0, len(items) - 1)

    # Make a copy to avoid accidentally modifying the original item list
    new_items = items[:]

    # The below swap is also possible with the line: new_items[item_to_move], new_items[item_to_move_to] = new_items[item_to_move_to], new_items[item_to_move]
    item_a = new_items[item_to_move]
    item_b = new_items[item_to_move_to]
    new_items[item_to_move] = item_b
    new_items[item_to_move_to] = item_a

    return Duty.add_anomaly("ITEM MOVEMENT", room, new_items)


# Owen Pearson
def change_number_in_string(item: str) -> str:

    number = '' #initialize empty string which we will hold the number(s) from string

    for index, char in enumerate(item): #loop through char in item

        if char.isdigit():
            number += char

            index_of_last_number = item.index(char)

    index_first_number = index_of_last_number - len(number) + 1


    new_number = int(number) + random.choice([-1,1]) #randomly add either 1 or -1

    #use string splitting to concatenate and form new string
    modified_string = item[:index_first_number] + str(new_number) + item[index_first_number + len(str(new_number)):]

    return modified_string


# Owen Pearson
def number_change(room: str) -> bool:

    items = Duty.get_room_items(room) #get items from room

    items_from_room = items[:] #create deep copy of items from room

    items_with_numbers = get_list_strings_with_numbers(items_from_room) #returns a list of items from room which contain numbers

    item_to_be_modified = random.choice(items_with_numbers) #randomly select item from list of items that only contain strings with numbers

    modified_item = change_number_in_string(item_to_be_modified) #call to function which handles manipulating string and returns string with modiified number

    #update list, find index of the "orginal" item
    index = items_from_room.index(item_to_be_modified)

    items_from_room[index] = modified_item #modify list so that it contains the modified string

    return Duty.add_anomaly("NUMBER CHANGE", room, items_from_room)


main()
