
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

from GameComponent import GameComponent



class Player:

    # A list of all the actions the player can perform

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

        self.map = {f'{x},{y}':GameComponent(x, y) for x in range(0,400,8) for y in range(0,400,8)}

        self.playername = playername
        self.y = None
        self.x = None
        self.health = 0
        self.ammo = 0

        self.serverx = None
        self.servery = None
        self.seen_items = set()
        self.seen_floors = set()
        self.seen_walls = set()
        self.seen_walls_dict = {}
        self.seen_players = {}
        self.inventory_dict = {}

        self.floors_dict = {}
        self.predecessors = {}

        self.serverDetails = serverDetails
        self.socket = socket
        self.bufferSize = 1024

        self.startx = None
        self.starty = None

        self.exit = None

        self.last_moved = time.time()

        self.lock = False

        self.seen_key = False

        self.key = None

        self.has_key = False

        self.join()



    def join(self):
        join_command = "requestjoin: " +self.playername
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


    def move_to(self, x: int, y: int, mapping=True):


        print('Trying to move to', x, y, 'from', self.x, self.y, 'server says', self.serverx, self.servery )

        # if self.servery == self.y and self.serverx == self.x:
        #
        #     requestmovemessage = f"moveto:{x},{y}"
        #     self.SendMessage(requestmovemessage)
        #
        #     self.x = x
        #     self.y = y
        #
        # else:
        #     print('Move denied')
        #     print('server', self.serverx, self.servery)
        #     print('self', self.x, self.y)


        requestmovemessage = f"moveto:{x},{y}"
        self.SendMessage(requestmovemessage)

        self.x = x
        self.y = y
        self.last_moved = time.time()


    def fire(self):
        fireMessage = "fire:"
        self.SendMessage(fireMessage)


    def stop(self):
        stopMessage = "stop:"
        self.SendMessage(stopMessage)


    def move_direction(self, direction):
        directionMoveMessage = f"movedirection:{direction}"
        self.SendMessage(directionMoveMessage)


    def face_direction(self, direction):
        directionFaceMessage = f"facedirection:{direction}"
        self.SendMessage(directionFaceMessage)


    def update(self, update):

        if not self.lock:
            components = update.split(':')
            dtype = components[0]
            data = components[1].split(',')

            if dtype == 'playerupdate':
                # self.x = int(float(data[0]))
                # self.y = int(float(data[1]))
                self.serverx = 8 * math.ceil(int(float(data[0])) / 8)
                self.servery = 8 * math.ceil(int(float(data[1])) / 8)
                self.health = int(data[2])
                self.ammo = int(data[3])
                self.has_key = data[4] == 'True'


            elif dtype == 'nearbyitem':

                keymappings = {
                    'elf': 'greenkey',
                    'wizard': 'yellowkey',
                    'valkyrie': 'bluekey',
                    'warrior': 'redkey'
                }

                if len(data):
                    n_groups = (len(data) - 1) // 3
                    for i in range(n_groups):
                        itemtype, x, y = data[i * 3:(i + 1) * 3]
                        i = Item(itemtype, int(x), int(y))
                        self.seen_items.add(i)

                        if self.key is None:
                            if itemtype in keymappings.values():
                                if itemtype == keymappings[self.playertype]:
                                    self.key = i

            elif dtype == 'nearbyfloors':
                # Each floor tile comes in the format x1,y1,x2,y2,...
                if len(data):
                    n_groups = (len(data) - 1) // 2

                    for i in range(n_groups):
                        x, y = data[i * 2:(i + 1) * 2]
                        ft = FloorTile(int(x), int(y), False)

                        if ft not in self.seen_floors:
                            self.map[f'{x},{y}'] = ft
                            # if f'{x},{y}' not in self.floors_dict:
                            #     self.floors_dict[f'{x},{y}'] = ft
                            self.seen_floors.add(ft)

            elif dtype == 'playerjoined':
                print('joined with data', data)
                self.playertype = data[0]

                self.x = 8 * math.ceil(int(float(data[2])) / 8)
                self.y = 8 * math.ceil(int(float(data[3])) / 8)
                self.serverx = self.x
                self.servery = self.y
                self.startx = self.x
                self.starty = self.y

            elif dtype == 'nearbywalls':
                if len(data):
                    n_groups = (len(data) - 1) // 2

                    for i in range(n_groups):
                        x, y = data[i * 2:(i + 1) * 2]
                        ft = Wall(int(x), int(y))

                        self.map[f'{x},{y}'] = ft
                        # self.seen_walls.add(ft)
                        # self.seen_walls_dict[(x, y)] = True

            elif dtype == 'nearbyplayer':
                if len(data):
                    # print(data)
                    character_class, player_name, x, y = data[:4]
                    self.seen_players[(character_class, player_name)] = [x, y]

            elif dtype == 'exit':
                if len(data):
                    self.exit = Exit(int(float(data[0])), int(float(data[1])))
                    # print("Exit is at", self.exit)

            else:
                print('ERR: unhandled update item', update)


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