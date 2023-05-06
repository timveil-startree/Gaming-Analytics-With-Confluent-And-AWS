#!/usr/bin/env python3
from random import randint
import pygame as pg
import numpy as np
from confluent_kafka import Producer, Consumer
import json
import uuid
import time
'''
PyNBoids - a Boids simulation - github.com/Nikorasu/PyNBoids
Uses numpy array math instead of math lib, more efficient.
Copyright (c) 2021  Nikolaus Stromberg  nikorasu85@gmail.com
'''
FLLSCRN = True          # True for Fullscreen, or False for Window
BOIDZ = 100           # How many boids to spawn, too many may slow fps
WRAP = False            # False avoids edges, True wraps to other side
FISH = False            # True to turn boids into fish
SPEED = 100             # Movement speed 170
WIDTH = 1200            # Window Width (1200)
HEIGHT = 800            # Window Height (800)
BGCOLOR = (0, 0, 0)     # Background color in RGB
FPS = 60                # 30-90
SHOWFPS = True         # show frame rate
NUMBER_OF_CHEATERS = 5  # 
BOID_SIZE = 25
GAME_ID = 13
PRODUCE = True



def read_ccloud_config(config_file):
    conf = {}
    with open(config_file) as fh:
        for line in fh:
            line = line.strip()
            if len(line) != 0 and line[0] != "#":
                parameter, value = line.strip().split('=', 1)
                conf[parameter] = value.strip()
    return conf
def produce_interaction(producer, gameTime, collides):
    print("Collision for Tick " + str(pg.time.get_ticks()))
    #id=str(uuid.uuid4())
    for boid in collides:
        id=str(uuid.uuid4())
        interaction_data = {
            "interactionId" : id,
            "gameId" : GAME_ID,
            "gameTime" : gameTime,
            "playerId" : str(boid.bnum)
        }
        print(interaction_data)
        interaction_data_json = json.dumps(interaction_data)  
        producer.produce("interactions", key=id, value=str(interaction_data_json))
    
class Boid(pg.sprite.Sprite):
    def __init__(self, boidNum, data, drawSurf, color, isFish=False, cHSV=None):
        super().__init__()
        self.data = data
        self.bnum = boidNum
        self.drawSurf = drawSurf
        self.image = pg.Surface((15, 15)).convert()
        self.image.set_colorkey(0)
        self.color = pg.Color(color)
        #self.color = pg.Color(0)  # preps color so we can use hsva
        #self.color.hsva = (randint(0,360), 90, 90) if cHSV is None else cHSV # randint(5,55) #4goldfish
        if isFish:  # (randint(120,300) + 180) % 360  #4noblues
            pg.draw.polygon(self.image, self.color, ((7,0),(12,5),(3,14),(11,14),(2,5),(7,0)), width=3)
            self.image = pg.transform.scale(self.image, (16, 24))
        else : 
            pg.draw.polygon(self.image, self.color, ((7,0), (13,14), (7,11), (1,14), (7,0)))
            #pg.draw.polygon(self.image, self.color, ((20,0), (13,14), (7,11)))
        self.bSize = 22 if isFish else 50
        self.orig_image = pg.transform.rotate(self.image.copy(), -90)
        self.dir = pg.Vector2(1, 0)  # sets up forward direction
        maxW, maxH = self.drawSurf.get_size()
        self.rect = self.image.get_rect(center=(randint(50, maxW - 50), randint(50, maxH - 50)))
        self.ang = randint(0, 360)  # random start angle, & position ^
        self.pos = pg.Vector2(self.rect.center)
    def update(self, dt, speed, ejWrap=False):
        maxW, maxH = self.drawSurf.get_size()
        turnDir = xvt = yvt = yat = xat = 0
        turnRate = 120 * dt  # about 120 seems ok
        margin = 42
        # Make list of nearby boids, sorted by distance
        otherBoids = np.delete(self.data.array, self.bnum, 0)
        array_dists = (self.pos.x - otherBoids[:,0])**2 + (self.pos.y - otherBoids[:,1])**2
        closeBoidIs = np.argsort(array_dists)[:7]
        neiboids = otherBoids[closeBoidIs]
        neiboids[:,3] = np.sqrt(array_dists[closeBoidIs])
        neiboids = neiboids[neiboids[:,3] < self.bSize*12]
        if neiboids.size > 1:  # if has neighborS, do math and sim rules
            yat = np.sum(np.sin(np.deg2rad(neiboids[:,2])))
            xat = np.sum(np.cos(np.deg2rad(neiboids[:,2])))
            # averages the positions and angles of neighbors
            tAvejAng = np.rad2deg(np.arctan2(yat, xat))
            targetV = (np.mean(neiboids[:,0]), np.mean(neiboids[:,1]))
            # if too close, move away from closest neighbor
            if neiboids[0,3] < self.bSize : targetV = (neiboids[0,0], neiboids[0,1])
            # get angle differences for steering
            tDiff = pg.Vector2(targetV) - self.pos
            tDistance, tAngle = pg.math.Vector2.as_polar(tDiff)
            # if boid is close enough to neighbors, match their average angle
            if tDistance < self.bSize*6 : tAngle = tAvejAng
            # computes the difference to reach target angle, for smooth steering
            angleDiff = (tAngle - self.ang) + 180
            if abs(tAngle - self.ang) > 1.2: turnDir = (angleDiff / 360 - (angleDiff // 360)) * 360 - 180
            # if boid gets too close to target, steer away
            if tDistance < self.bSize and targetV == (neiboids[0,0], neiboids[0,1]) : turnDir = -turnDir
        # Avoid edges of screen by turning toward the edge normal-angle
        if not ejWrap and min(self.pos.x, self.pos.y, maxW - self.pos.x, maxH - self.pos.y) < margin:
            if self.pos.x < margin : tAngle = 0
            elif self.pos.x > maxW - margin : tAngle = 180
            if self.pos.y < margin : tAngle = 90
            elif self.pos.y > maxH - margin : tAngle = 270
            angleDiff = (tAngle - self.ang) + 180  # if in margin, increase turnRate to ensure stays on screen
            turnDir = (angleDiff / 360 - (angleDiff // 360)) * 360 - 180
            edgeDist = min(self.pos.x, self.pos.y, maxW - self.pos.x, maxH - self.pos.y)
            turnRate = turnRate + (1 - edgeDist / margin) * (20 - turnRate) #minRate+(1-dist/margin)*(maxRate-minRate)
        if turnDir != 0:  # steers based on turnDir, handles left or right
            self.ang += turnRate * abs(turnDir) / turnDir
            self.ang %= 360  # ensures that the angle stays within 0-360
        # Adjusts angle of boid image to match heading
        self.image = pg.transform.rotate(self.orig_image, -self.ang)
        self.rect = self.image.get_rect(center=self.rect.center)  # recentering fix
        self.dir = pg.Vector2(1, 0).rotate(self.ang).normalize()
        self.pos += self.dir * dt * (speed + (7 - neiboids.size) * 2)  # movement speed
        # Optional screen wrap
        if ejWrap and not self.drawSurf.get_rect().contains(self.rect):
            if self.rect.bottom < 0 : self.pos.y = maxH
            elif self.rect.top > maxH : self.pos.y = 0
            if self.rect.right < 0 : self.pos.x = maxW
            elif self.rect.left > maxW : self.pos.x = 0
        # Actually update position of boid
        self.rect.center = self.pos
        # Finally, output pos/ang to array
        self.data.array[self.bnum,:3] = [self.pos[0], self.pos[1], self.ang]
    
    def cheat(self, dt, speed, ejWrap=False):   

        cheatSpeed = speed * 3
        maxW, maxH = self.drawSurf.get_size()

        turnDir = xvt = yvt = yat = xat = 0
        turnRate = 120 * dt  # about 120 seems ok
        margin = 42
        # Make list of nearby boids, sorted by distance
        otherBoids = np.delete(self.data.array, self.bnum, 0)
        array_dists = (self.pos.x - otherBoids[:,0])**2 + (self.pos.y - otherBoids[:,1])**2
        closeBoidIs = np.argsort(array_dists)[:7]
        neiboids = otherBoids[closeBoidIs]
        neiboids[:,3] = np.sqrt(array_dists[closeBoidIs])
        neiboids = neiboids[neiboids[:,3] < self.bSize*12]
        if neiboids.size > 1:  # if has neighborS, do math and sim rules
            yat = np.sum(np.sin(np.deg2rad(neiboids[:,2])))
            xat = np.sum(np.cos(np.deg2rad(neiboids[:,2])))
            # averages the positions and angles of neighbors
            tAvejAng = np.rad2deg(np.arctan2(yat, xat))
            targetV = (np.mean(neiboids[:,0]), np.mean(neiboids[:,1]))
            # if too close, move away from closest neighbor
            if neiboids[0,3] < self.bSize : targetV = (neiboids[0,0], neiboids[0,1])
            # get angle differences for steering
            tDiff = pg.Vector2(targetV) - self.pos
            tDistance, tAngle = pg.math.Vector2.as_polar(tDiff)
            # if boid is close enough to neighbors, match their average angle
            if tDistance < self.bSize*6 : tAngle = tAvejAng
            # computes the difference to reach target angle, for smooth steering
            angleDiff = (tAngle - self.ang) + 180
            if abs(tAngle - self.ang) > 1.2: turnDir = (angleDiff / 360 - (angleDiff // 360)) * 360 - 180
            # if boid gets too close to target, steer away
            if tDistance < self.bSize and targetV == (neiboids[0,0], neiboids[0,1]) : turnDir = -turnDir
        # Avoid edges of screen by turning toward the edge normal-angle
        if not ejWrap and min(self.pos.x, self.pos.y, maxW - self.pos.x, maxH - self.pos.y) < margin:
            if self.pos.x < margin : tAngle = 0
            elif self.pos.x > maxW - margin : tAngle = 180
            if self.pos.y < margin : tAngle = 90
            elif self.pos.y > maxH - margin : tAngle = 270
            angleDiff = (tAngle - self.ang) + 180  # if in margin, increase turnRate to ensure stays on screen
            turnDir = (angleDiff / 360 - (angleDiff // 360)) * 360 - 180
            edgeDist = min(self.pos.x, self.pos.y, maxW - self.pos.x, maxH - self.pos.y)
            turnRate = turnRate + (1 - edgeDist / margin) * (20 - turnRate) #minRate+(1-dist/margin)*(maxRate-minRate)
        if turnDir != 0:  # steers based on turnDir, handles left or right
            self.ang += turnRate * abs(turnDir) / turnDir
            self.ang %= 360  # ensures that the angle stays within 0-360
        # Adjusts angle of boid image to match heading
        self.image = pg.transform.rotate(self.orig_image, -self.ang)
        self.rect = self.image.get_rect(center=self.rect.center)  # recentering fix
        self.dir = pg.Vector2(1, 0).rotate(self.ang).normalize()
        self.pos += self.dir * dt * (cheatSpeed+ (7 - neiboids.size) * 2)  # movement speed
        # Optional screen wrap
        if ejWrap and not self.drawSurf.get_rect().contains(self.rect):
            if self.rect.bottom < 0 : self.pos.y = maxH
            elif self.rect.top > maxH : self.pos.y = 0
            if self.rect.right < 0 : self.pos.x = maxW
            elif self.rect.left > maxW : self.pos.x = 0
        # Actually update position of boid
        self.rect.center = self.pos
        # Finally, output pos/ang to array
        self.data.array[self.bnum,:3] = [self.pos[0], self.pos[1], self.ang]

    def stopCheating(self):
        self.color = pg.Color('green')
class BoidArray():  # Holds array to store positions and angles
    def __init__(self):
        self.array = np.zeros((BOIDZ, 4), dtype=float)

def main():
    pg.init()  # prepare window
    window = pg.display.set_caption("Demo Game")
    try: 
        BOID_ICON = pg.image.load("assets/nboids.png")
        SCALED_BOID_ICON = pg.transform.scale(BOID_ICON, (BOID_SIZE, BOID_SIZE))
        
        pg.display.set_icon(SCALED_BOID_ICON)

    except: 
        print("FYI: nboids.png icon not found, skipping..")

    # setup fullscreen or window mode
    if FLLSCRN:
        currentRez = (pg.display.Info().current_w, pg.display.Info().current_h)
        screen = pg.display.set_mode(currentRez, pg.SCALED)
        pg.mouse.set_visible(False)

    else: screen = pg.display.set_mode((WIDTH, HEIGHT), pg.RESIZABLE)


    nBoids = pg.sprite.Group()
    dataArray = BoidArray()
    for n in range(BOIDZ):
        if n == 0:
            color = "red"
            nBoids.add(Boid(n, dataArray, screen, color, FISH))
        else:
            color="blue"
            nBoids.add(Boid(n, dataArray, screen, color, FISH))  # spawns desired # of boidz

    clock = pg.time.Clock()
    
    if SHOWFPS : font = pg.font.Font(None, 30)

    #Create Producer for Kakfa
    producer = Producer(read_ccloud_config("client.properties"))
    props = read_ccloud_config("client.properties")
    props["group.id"] = "python-group-1"
    props["auto.offset.reset"] = "earliest"
    consumer = Consumer(props)
    #consumer.subscribe(["my-topic"])

    recordId = 0
    collision = 0
    # main loop
    while True:
        for e in pg.event.get():
            if e.type == pg.QUIT or e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE:
                return
        
        dt = clock.tick(FPS) / 1000
        screen.fill(BGCOLOR)
        nBoids.update(dt, SPEED, WRAP)

        background = pg.image.load("assets/map.png")
        background.set_alpha(225)

        screen.blit(background,(0,0))
        color = (255,0,0)

        #The Bridge
        #pg.draw.rect(screen, color,  pg.Rect(75, 375, 250, 75))

        #Downtown
        #pg.draw.rect(screen, color,  pg.Rect(400, 100, 450, 300))

        #Business District  
        #pg.draw.rect(screen, color,  pg.Rect(425, 500, 500, 300))

        #Amiko Greens
        #pg.draw.rect(screen, color,  pg.Rect(1000, 350, 200, 500))

        #Glen Falls Division
        #pg.draw.rect(screen, color,  pg.Rect(1300, 0, 500, 500))

        #Kasama District
        #pg.draw.rect(screen, color,  pg.Rect(1300, 600, 500, 500))
        #pg.display.flip()
        nBoids.draw(screen)
        nBoids.sprites()[0].cheat(dt, SPEED, WRAP)

        if(pg.time.get_ticks() % 3 == 0 or pg.time.get_ticks() % 4 == 0):
            for entity in nBoids:
                #print(entity.bnum)
                collides = pg.sprite.spritecollide(entity, nBoids, False)
                
                if len(collides) >= 2:
                    #print(str(collides[0].bnum) + "collided with " + str(collides[1].bnum) + ": originating from " + str(entity.bnum))
                    id=str(uuid.uuid4())
                    gameTime = pg.time.get_ticks()
                    interaction_data = {
                        "interactionId" : id,
                        "gameId" : GAME_ID,
                        "gameTime" : gameTime,
                        "sourcePlayerId" : str(entity.bnum),
                        "player1Id": str(collides[0].bnum),
                        "player2Id": str(collides[1].bnum)
                    }
                    #print(interaction_data)
                    interaction_data_json = json.dumps(interaction_data)  
                    if PRODUCE == True:
                        producer.produce("interactions", key=id, value=str(interaction_data_json))
                        

                gameTime = pg.time.get_ticks()

                player_data = {
                    "recordId" : recordId,
                    "gameId" : GAME_ID,
                    "playerId": entity.bnum,
                    "gameTime" : gameTime,
                    "topCoordinate": entity.rect.top,
                    "leftCoordinate": entity.rect.left,
                }
                player_data_json = json.dumps(player_data)

                #print(player_data_json)
                recordId = recordId + 1
                if PRODUCE == True:
                    producer.produce("player-position", key=str(entity.bnum), value=str(player_data_json))
            
        
        if SHOWFPS : screen.blit(font.render(str(int(clock.get_fps())), True, [0,200,0]), (8, 8))
        
        pg.display.update()

if __name__ == '__main__':
    main() 
    pg.quit()
