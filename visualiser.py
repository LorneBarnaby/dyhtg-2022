import threading

from FloorTile import FloorTile
from PlayerT import Player

import pygame
from pygame.locals import (
    K_UP,
    K_DOWN,
    K_LEFT,
    K_RIGHT,
    K_ESCAPE,
    KEYDOWN,
    QUIT,
)

import time

global running


def get_updates(player):
    while running:
        update = player.socket.recvfrom(player.bufferSize)[0].decode('ascii')
        player.update(update)


def go_walkabout(player):

    def reconstruct_path(cameFrom, current):
        total_path = [current]

        while f'{current.x},{current.y}' in cameFrom:
            current = cameFrom[f'{current.x},{current.y}']
            total_path.append(current)

        return total_path[::-1]





    def A_star(start, goal, h):
        openSet = {start}
        cameFrom = dict()

        gScore = {f'{x},{y}':float('inf') for x in range(0,400,8) for y in range(0,400,8)}
        gScore[f'{start.x},{start.y}'] = 0

        fScore = {f'{x},{y}': float('inf') for x in range(0, 400, 8) for y in range(0, 400, 8)}
        fScore[f'{start.x},{start.y}'] = h(start)

        while len(openSet):

            #current := the node in openSet having the lowest fScore[] value
            current = sorted(openSet, key= lambda n: fScore[f'{n.x},{n.y}'])[0]

            if current.x == goal.x and current.y == goal.y:
                return reconstruct_path(cameFrom, current)

            openSet.remove(current)

            #For each neighbour of current
            can_go_to = []
            for xdiff in range(-8, 9, 8):
                for ydiff in range(-8, 9, 8):
                    if not (xdiff == 0 and ydiff == 0):
                        x, y = current.x + xdiff, current.y + ydiff
                        map_at = player.map[f'{x},{y}']

                        if isinstance(map_at, FloorTile):
                            can_go_to.append(map_at)

            for neighbour in can_go_to:
                tentative_gScore = gScore[f'{current.x},{current.y}'] + 1

                if tentative_gScore < gScore[f'{neighbour.x},{neighbour.y}']:
                    cameFrom[f'{neighbour.x},{neighbour.y}'] = current
                    gScore[f'{neighbour.x},{neighbour.y}'] = tentative_gScore
                    fScore[f'{neighbour.x},{neighbour.y}'] = tentative_gScore + h(neighbour)

                    if neighbour not in openSet:
                        openSet.add(neighbour)
        return None




    def neighbours(point):
        can_go_to = []
        for xdiff in range(-8, 9, 8):
            for ydiff in range(-8, 9, 8):
                if not (xdiff == 0 and ydiff == 0):
                    x, y = point.x + xdiff, point.y + ydiff
                    map_at = player.map[f'{x},{y}']

                    if isinstance(map_at, FloorTile):
                        can_go_to.append(map_at)

        return can_go_to



    def dfs():
        can_go_to = neighbours(FloorTile(player.x, player.y, True))

        print(can_go_to)
        # break
        unvisited = list(filter(lambda t: not t.visited, can_go_to))

        def d(p):
            if player.key is None:
                return -1 * (((p.x - player.startx) ** 2 + (p.y - player.starty) ** 2) ** 0.5)

            elif player.has_key and player.exit is not None:
                return ((p.x - player.exit.x) ** 2 + (p.y - player.exit.y) ** 2) ** 0.5

            elif player.has_key:
                return -1 * (((p.x - player.startx) ** 2 + (p.y - player.starty) ** 2) ** 0.5)
            else:
                return ((p.x - player.key.x) ** 2 + (p.y - player.key.y) ** 2) ** 0.5

        unvisited = sorted(unvisited, key=d)

        if len(unvisited):
            newx, newy = unvisited[0].x, unvisited[0].y

            unvisited[0].visited = True
            been_to.append(unvisited[0])
            player.map[f'{newx},{newy}'] = FloorTile(newx, newy, True)

            player.move_to(newx, newy)

        else:
            print('backtracking')


            for p in been_to[::-1]:
                been_to.pop()
                can_go_to = neighbours(FloorTile(p.x, p.y, True))
                unvisited = list(filter(lambda t: not t.visited, can_go_to))

                if len(unvisited):

                    def h(point):
                        return ((point.x - p.x)**2 + (p.y - point.y)**2) ** 0.5

                    path = A_star(FloorTile(player.x, player.y, True), p, h)

                    for i in path:
                        player.move_to(i.x, i.y)

                        time.sleep(0.3)

                    break




            # player.move_to(last.x, last.y)


    print('going walkabout')
    been_to = [FloorTile(player.x, player.y, True)]
    player.map[f'{player.x},{player.y}'] = FloorTile(player.x, player.y, True)

    while running:

        if len(player.seen_floors):

            if player.key is not None:

                if not player.has_key:
                    print('trying to find route to key')

                    def h(point):
                        return ((point.x - player.key.x) ** 2 + (point.y - player.key.y) ** 2) ** 0.5

                    path_to_key = A_star(FloorTile(player.x, player.y, False), player.key, h)
                    if path_to_key is None:
                        dfs()
                    else:
                        print('Found path to key')
                        for point in path_to_key:
                            player.move_to(point.x, point.y)
                            time.sleep(0.3)
                else:
                    if player.exit is not None:
                        #Find exit
                        def h(point):
                            return ((point.x - player.exit.x) ** 2 + (point.y - player.exit.y) ** 2) ** 0.5

                        path_to_exit = A_star(FloorTile(player.x, player.y, False), player.exit, h)

                        if path_to_exit is None:
                            dfs()
                        else:
                            print('Found exit path', path_to_exit)
                            for point in path_to_exit:
                                player.move_to(point.x, point.y)
                                time.sleep(0.3)
                            break

                    else:
                        dfs()
            else:
                dfs()


        time.sleep(0.3)


if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((600, 800))
    pygame.display.set_caption("First Game")

    clock = pygame.time.Clock()

    x, y, width, height = 50, 50, 40, 60
    vel = 5

    running = True

    player = Player.spawn(("10.211.55.4", 11000), 'lorne')

    update_loop = threading.Thread(target=lambda: get_updates(player))
    update_loop.start()

    time.sleep(2)

    player_traverse = threading.Thread(target=lambda: go_walkabout(player))
    player_traverse.start()

    while running:
        # screen.fill((0, 0, 0))
        # clock.tick(2)

        for event in pygame.event.get():

            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False

            elif event.type == QUIT:
                running = False

        # seen_walls = player.seen_walls.copy()
        # player.lock = True
        # print('drawing walls')

        # for i in range(len(player.seen_walls)):
        #     pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(player.seen_walls[i].x, player.seen_walls[i].y, 8, 8))
        #     pygame.display.flip()

        # print(len(player.map.keys()))
        for i in player.map.values():
            if i.draw(screen):
                pygame.display.flip()

        pygame.draw.rect(screen, (0, 255, 0), pygame.Rect(player.x, player.y, 8, 8))
        pygame.display.flip()

        if player.key is not None:
            pygame.draw.rect(screen, (205, 127, 50), pygame.Rect(player.key.x, player.key.y, 8, 8))
            pygame.display.flip()

        if player.exit is not None:
            pygame.draw.rect(screen, (0, 0, 200), pygame.Rect(player.exit.x, player.exit.y, 8, 8))
            pygame.display.flip()

        pressed_keys = pygame.key.get_pressed()
        player.execute_keys(pressed_keys)
