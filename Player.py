import socket
import time
import random
import sys
import math
from FloorTile import FloorTile
from Item import Item
from math import sqrt
from Wall import Wall
from Exit import Exit


from pygame.locals import (
    K_UP,
    K_DOWN,
    K_LEFT,
    K_RIGHT,
    K_ESCAPE,
    KEYDOWN,
    QUIT,
)



class Player:

    # A list of all the actions the player can perform
    actions = ["join", "move_to", "fire", "stop", "move_direction", "face_direction"]

    @classmethod
    def spawn(cls, serverDetails, playerName):
        try:
            UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        except socket.error as e:

            print("Error creating socket: ", e)
            sys.exit(1)
        
        return Player(playerName, serverDetails, UDPClientSocket)

    def __init__(self, playername: str, serverDetails: tuple[str, int], socket):

        # This dictionary controls which actions are logged (displayed in the output)

        self.logging_actions = {action: False for action in self.actions}

        self.playername = playername
        self.y = None
        self.x = None
        self.logging_actions = {action: False for action in self.actions}
        self.health = 0
        self.ammo = 0

        self.seen_items = set()
        self.seen_floors = set()
        self.seen_walls = set()
        self.seen_walls_dict = {}
        self.seen_players = {}
        self.inventory_dict = {}
        self.position_graph={}

        self.floors_dict = {}
        self.predecessors = {}

        self.serverDetails = serverDetails
        self.socket = socket
        self.bufferSize = 1024

        self.exit = None

        self.last_moved = time.time()

        self.lock = False

        self.join()

    def get_player_actions(self, action):
        return self.actions

    def set_logging_for_action(self, action):
        if action in self.actions:
            self.logging_actions[action] = True

    def set_logging_for_action(self, action):
        if action in self.actions:
            self.log_actions[action] = True
        else:
            print(f"{action} is not a valid action, so cannot be logged - ignoring...")

    def join(self):
        join_command = "requestjoin:"+self.playername
        join_bytes = str.encode(join_command)

        self.socket.sendto(join_bytes, self.serverDetails)

        try:
            update = self.socket.recvfrom(self.bufferSize)[0].decode('ascii')
        except TimeoutError:
            self.joined_server = False
            print(f"Failed to join server with player: {self.playername}")
        else:
            self.joined_server = True
            self.update(update)

    def SendMessage(self, requestmovemessage):
        bytesToSend = str.encode(requestmovemessage)
        self.socket.sendto(bytesToSend, self.serverDetails)

    def update_position_graph(self, position_as_tuple, recursion_layer=0):

        if self.position_graph.get(position_as_tuple) is None:
            if recursion_layer < 2:

                self.position_graph[position_as_tuple] = []

                x,y = position_as_tuple
                adj_positions_queue = []

                for x_offset in [-8,0,8]:
                    for y_offset in [-8,0,8]:
                        if self.seen_walls_dict.get((x+x_offset, y+y_offset)) is None:
                            adj_pos = (x+x_offset,y+y_offset)
                            self.position_graph[position_as_tuple].append(adj_pos)
                            adj_positions_queue.append(adj_pos)

                for pos in adj_positions_queue:
                    self.update_position_graph(pos, recursion_layer+1)



    def move_to(self, x: int, y: int, mapping=True):
        self.x = x
        self.y = y


        print('Trying to move to', x, y)




        requestmovemessage = f"moveto:{x},{y}"
        self.SendMessage(requestmovemessage)

        self.last_moved = time.time()



        if self.logging_actions["move_to"]:
            print(requestmovemessage)

        # if f'{x},{y}' not in self.predecessors:
        #     self.predecessors[f'{x},{y}'] = f'{self.x},{self.y}'

        # if mapping:
        #
        #     adjacent_positions = self.position_graph.get((x,y))
        #
        #     if adjacent_positions is None:
        #         self.update_position_graph((x,y))

    def fire(self):
        fireMessage = "fire:"
        self.SendMessage(fireMessage)
        if self.logging_actions["fire"]:
            print(fireMessage)

    def stop(self):
        stopMessage = "stop:"
        self.SendMessage(stopMessage)
        if self.logging_actions["stop"]:
            print(stopMessage)

    def move_direction(self, direction):
        directionMoveMessage = f"movedirection:{direction}"
        self.SendMessage(directionMoveMessage)
        if self.logging_actions["move_direction"]:
            print(directionMoveMessage)

    def face_direction(self, direction):
        directionFaceMessage = f"facedirection:{direction}"
        self.SendMessage(directionFaceMessage)
        if self.logging_actions["face_direction"]:
            print(directionFaceMessage)

    def update(self, update):

        if not self.lock:
            components = update.split(':')
            dtype = components[0]
            data = components[1].split(',')
            #
            # print(dtype, data)

            if dtype == 'playerupdate':
                # self.x = int(float(data[0]))
                # self.y = int(float(data[1]))
                # self.x = 8 * math.ceil(int(float(data[0])) / 8)
                # self.y = 8 * math.ceil(int(float(data[1])) / 8)
                self.health = int(data[2])
                self.ammo = int(data[3])


            elif dtype == 'nearbyitem':
                # self.nearby_items.append(data)

                if len(data):
                    n_groups = (len(data) - 1) // 3
                    for i in range(n_groups):
                        itemtype, x, y = data[i * 3:(i + 1) * 3]
                        i = Item(itemtype, x, y)
                        self.seen_items.add(i)





                        # if self.playertype == 'elf' and itemtype == 'greenkey':
                        #     # print('Key found', i)
                        #     if self.inventory_dict.get((i.x, i.y)) is None:
                        #         self.get_item(i.x, i.y)
                        # elif self.playertype == 'warrior' and itemtype == 'redkey':
                        #     if self.inventory_dict.get((i.x, i.y)) is None:
                        #         self.get_item(i.x, i.y)
                        #     # print('Key found', i)
                        # elif self.playertype == 'valkyrie' and itemtype == 'bluekey':
                        #     if self.inventory_dict.get((i.x, i.y)) is None:
                        #         self.get_item(i.x, i.y)
                        #     # print('Key found', i)
                        # elif self.playertype == 'wizard' and itemtype == 'yellowkey':
                        #     if self.inventory_dict.get((i.x, i.y)) is None:
                        #         self.get_item(i.x, i.y)
                            # print('Key found', i)

            elif dtype == 'nearbyfloors':
                # Each floor tile comes in the format x1,y1,x2,y2,...
                if len(data):
                    n_groups = (len(data) - 1) // 2

                    for i in range(n_groups):
                        x, y = data[i * 2:(i + 1) * 2]
                        ft = FloorTile(int(x), int(y), False)

                        if f'{x},{y}' not in self.floors_dict:
                            self.floors_dict[f'{x},{y}'] = ft
                        self.seen_floors.add(ft)

            elif dtype == 'playerjoined':
                print('joined with data', data)
                self.playertype = data[0]

                self.x = 8 * math.ceil(int(float(data[2])) / 8)
                self.y = 8 * math.ceil(int(float(data[3])) / 8)

            elif dtype == 'nearbywalls':
                if len(data):
                    n_groups = (len(data) - 1) // 2

                    for i in range(n_groups):
                        x, y = data[i * 2:(i + 1) * 2]
                        ft = Wall(int(x), int(y))

                        self.seen_walls.add(ft)
                        self.seen_walls_dict[(x,y)] = True

            elif dtype == 'nearbyplayer':
                if len(data):
                    # print(data)
                    character_class, player_name, x, y = data[:4]
                    self.seen_players[(character_class, player_name)] = [x,y]

            elif dtype == 'exit':
                if len(data):

                    self.exit = Exit(int(float(data[0])), int(float(data[1])))
                    # print("Exit is at", self.exit)

            else:
                print('ERR: unhandled update item', update)

    def nearest_floors(self, k):

        def distance(floor: FloorTile):
            return sqrt(
                (self.x - floor.x) ** 2 + (self.y - floor.y) ** 2
            )

        k_nearest_floors = sorted(self.seen_floors, key=distance)[:k]

        return k_nearest_floors

    def nearest_walls(self, k):

        def distance(wall: Wall):
            return sqrt(
                (self.x - wall.x) ** 2 + (self.y - wall.y) ** 2
            )

        k_nearest_walls = sorted(self.seen_walls, key=distance)[:k]

        return k_nearest_walls

    def nearest_items(self, k):

        def distance(item: Item):
            return sqrt(
                (self.x - item.x) ** 2 + (self.y - item.y) ** 2
            )

        k_nearest_items = sorted(self.seen_items, key=distance)[:k]

        return k_nearest_items


    def k_nearest_unvisited(self, k):

        def distance(floor: FloorTile):
            return sqrt(
                (self.x - floor.x) ** 2 + (self.y - floor.y) ** 2
            )

        nearest = sorted(self.seen_floors, key=distance)
        unv = list(filter(lambda f: not f.visited, nearest))
        return unv[:k]

    def k_nearest_players(self, k):

        def distance(x2, y2):
            return sqrt(
                (self.x - player.x) ** 2 + (self.y - player.y) ** 2
            )

        player_distances = []
        nearest = []

        for player, player_pos in self.seen_players.items():
            player_distance = distance(player_pos[0], player_pos[1])
            player_distances.append([player, player_pos, player_distance])

        player_distances.sort(key=lambda player_data: player_data[2])
        nearest = [player[:2] for player in player_distances]

        return nearest[:k]

    def shortest_path_to_pos(self, source_x,source_y, dest_x,dest_y):

        visited = {pos:False for pos in self.position_graph.keys()}
        predecessors = {pos:-1 for pos in self.position_graph.keys()}
        distances_to_positions = {pos:math.inf for pos in self.position_graph.keys()}
        position_queue = []

        source_pos = (source_x, source_y)
        dest_pos = (dest_x, dest_y)

        dest_pos_found = False
        visited[source_pos] = True
        distances_to_positions[source_pos] = 0
        position_queue.append(source_pos)

        while len(position_queue) != 0:
            curr_pos = position_queue.pop(0)
            for adj_pos in self.position_graph.get(curr_pos, []):
                if visited.get(adj_pos) is not None and not visited[adj_pos]:
                    visited[adj_pos] = True
                    distances_to_positions[adj_pos] = 1+distances_to_positions[curr_pos]
                    predecessors[adj_pos] = curr_pos
                    position_queue.append(adj_pos)

                    if adj_pos == dest_pos:
                        dest_pos_found = True
                        break

        path_to_position = []
        if dest_pos_found:

            path_pos = dest_pos

            while (predecessors[path_pos] != -1):
                path_to_position.append(path_pos)
                path_pos=predecessors[path_pos]

            path_to_position = path_to_position[::-1]

        return path_to_position

    def move_to_via_shortest_path(self, destination_x,destination_y):

        path_to_pos = self.shortest_path_to_pos(self.x, self.y, destination_x, destination_y)

        if path_to_pos:

            for pos in path_to_pos:
                x_pos, y_pos = pos
                self.move_to(x_pos, y_pos)

    def guard_current_pos(self):

        pass

    def get_item(self, item_x_pos, item_y_pos):

        # if item_y_pos == self.y:
        #     if item_x_pos > self.x:
        #         for i in range(0, item_x_pos, 8):
        #             if self.seen_walls(self.x+)



        if True == False:

            path_to_item = self.shortest_path_to_pos(self.x, self.y, item_x_pos, item_y_pos)

            if path_to_item:


                for pos in path_to_item:
                    x_pos, y_pos = pos
                    self.move_to(x_pos, y_pos, False)

                for pos in path_to_item[1::-1]:
                    x_pos, y_pos = pos
                    self.move_to(x_pos, y_pos, False)

                self.move_to(self.x, self.y)

                self.inventory_dict[(item_x_pos, item_y_pos)] = True


    def execute_keys(self, key_updates):

        # print('called')
        if key_updates[K_UP]:
            print('up')
            self.move_to(self.x, self.y - 8)

        elif key_updates[K_DOWN]:
            print('down')
            self.move_to(self.x, self.y + 8)

        elif key_updates[K_RIGHT]:
            print('right')
            self.move_to(self.x + 8, self.y)

        elif key_updates[K_LEFT]:
            print('left')
            self.move_to(self.x - 8, self.y)








