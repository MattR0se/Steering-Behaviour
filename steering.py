import pygame as pg
import traceback
from random import randint, randrange, uniform
import math

vec = pg.math.Vector2

WIDTH = 800
HEIGHT = 800

# simulation mode
# modes = 'wander', 'arrive', 'follow'
MODE = 'follow'


# ----------- custom functions ------------------------------------------------

def limit(vector, lim):
    if vector.length_squared() > (lim * lim):
        vector.scale_to_length(lim)


def remap(n, start1, stop1, start2, stop2):
    # https://p5js.org/reference/#/p5/map
    newval = (n - start1) / (stop1 - start1) * (stop2 - start2) + start2
    if (start2 < stop2):
        return constrain(newval, start2, stop2)
    else:
        return constrain(newval, stop2, start2)


def constrain(n, low, high):
    return max(min(n, high), low)


def rngVec():
    angle = uniform(0, 2.0 * math.pi)
    return vec(math.cos(angle), math.sin(angle))

# ---------- game class -------------------------------------------------------

class Game():
    def __init__(self):
        pg.init()

        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.clock = pg.time.Clock()
        
        self.path = []
        
        self.running = True


    def new(self):
        # start a new game
        self.all_sprites = pg.sprite.LayeredUpdates()

        for i in range(100):
            pos = (randint(0, WIDTH), randint(0, HEIGHT))
            speed = randint(3, 6)
            p = Projectile(self, (12, 14), pos, speed)
            self.all_sprites.add(p)
            
            
        self.flowfield = FlowField(50)
        
        self.run()
        
        
    def run(self):
        # game loop
        self.playing = True
        while self.playing:
            self.clock.tick(60)
            self.events()
            self.update()
            self.draw()
    
    
    def update(self):
        # game loop update
        self.all_sprites.update()
        
        self.flowfield.change()
        
    
    def events(self):
        # game loop events
        for event in pg.event.get():
            if event.type == pg.QUIT:
                if self.playing:
                    self.playing = False
                self.running = False
            if event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:
                    pos = vec(pg.mouse.get_pos())
                    self.path.append(pos)
                
                if event.button == 3:
                    self.path = []
    
    
    def draw(self):
        self.screen.fill((10, 40, 70))
        #self.drawVectors()
        self.drawField()
        
        self.drawPath()
        
        self.all_sprites.draw(self.screen)
    
        
        pg.display.flip()
        
    
    def drawVectors(self):
        for p in self.all_sprites:
            target = p.desired
            target = target.normalize()
            target.scale_to_length(20 * p.vel.length())
            pg.draw.line(self.screen, (0, 255, 0), p.pos, p.pos + p.extent, 1)
            pg.draw.circle(self.screen, (0, 255, 0), 
                           (int(p.pos.x + p.extent.x), 
                            int(p.pos.y + p.extent.y)), 30, 1)
            pg.draw.line(self.screen, (0, 255, 0), p.pos + p.extent, 
                         p.target, 1)

     
    def drawField(self):
        field = self.flowfield.field
        w = len(field)
        h = len(field[0])
        for i in range(h):
            #pg.draw.line(self.screen, (0, 200, 100), (0, HEIGHT / h * i),
                         #(WIDTH, HEIGHT / h * i))
            for j in range(w):
                #pg.draw.line(self.screen, (0, 200, 100), (WIDTH / w * j, 0),
                         #(WIDTH / w * j, HEIGHT))
                
                pos = vec(WIDTH / w * j + (WIDTH / w) / 2, 
                          HEIGHT / h * i + (HEIGHT / h) / 2)
                end = pos + field[j][i] * self.flowfield.resolution / 2
                pg.draw.line(self.screen, (0, 200, 100), pos, end, 1)


    def drawPath(self):
        if len(self.path) > 1:
            for i in range(1, len(self.path)):
                pg.draw.line(self.screen, (0, 255, 0), 
                             self.path[i - 1], self.path[i], 1)
        elif len(self.path) == 1:
            pg.draw.circle(self.screen, (0, 255, 0), 
                           (int(self.path[0].x), int(self.path[0].y)), 1)



class FlowField():
    def __init__(self, resolution):
        self.resolution = resolution
        self.cols = WIDTH // self.resolution
        self.rows = HEIGHT // self.resolution
        self.field = [[None for i in range(self.cols)] 
                      for j in range(self.rows)]
        
        
        self.clock = 0
        self.dir = vec(1, 1)
        
        for i in range(self.rows):
            for j in range(self.cols):
                self.field[i][j] = rngVec()

                
    def lookup(self, vector):
        column = int(constrain(vector.x / self.resolution, 0, self.cols - 1))
        row = int(constrain(vector.y / self.resolution, 0, self.rows- 1))
        return vec(self.field[row][column])
    
    
    def change(self):
        self.clock += 1
        if self.clock > randrange(10, 20):
            for i in range(self.rows):
                for j in range(self.cols):
                    change = 0.8
                    # change the angle by a small random amount 
                    self.field[i][j] += (vec(uniform(-change, change), 
                                         uniform(-change, change)) + self.dir)
                    self.field[i][j] = self.field[i][j].normalize()
            
            # change the general direction
            change2 = 0.5
            
            self.dir.x += uniform(-change2, change2)
            self.dir.y += uniform(-change2, change2)
            
            self.dir = self.dir.normalize()
            
            self.clock = 0
    
    
    

# ------ SPRITES --------------------------------------------------------------

class Projectile(pg.sprite.Sprite):
    def __init__(self, game, size, pos, speed):
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self)
        self.layer = 0
        self.groups.add(self, layer=self.layer)
        self.game = game
        self.size = size
        self.pos = vec(pos)
        self.vel = vec(0, 0)
        self.acc = vec(0, 0)
        self.steer = vec(0, 0)
        self.desired = vec(0, 0)
        self.extent = vec(0, 0)
        self.target = vec(0, 0)
        
        self.maxspeed = speed
        self.maxforce = uniform(0.05, 0.15)
        self.theta = 0
        
        self.clock = 0
        
        self.image = pg.Surface(self.size, pg.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        self.rect = self.image.get_rect()
        pg.draw.polygon(self.image, (255, 255, 255), (self.rect.bottomleft,
                        self.rect.midtop, self.rect.bottomright))

        self.normal_image = self.image
        
        self.layer = 1
        
    
    def update(self):
        self.clock += 1
        
        if MODE == 'wander':
            self.wander()
        elif MODE == 'follow':
            self.follow()
        elif MODE == 'arrive':
            self.arrive(vec(pg.mouse.get_pos()))
        
        self.vel += self.acc
        limit(self.vel, self.maxspeed)
        self.pos += self.vel
        
        self.acc *= 0
            
        
        
       # screen wrap
        if self.pos.x < 0:
            self.pos.x = WIDTH
        elif self.pos.x > WIDTH:
            self.pos.x = 0
        if self.pos.y < 0:
            self.pos.y = HEIGHT
        elif self.pos.y > HEIGHT:
            self.pos.y = 0
        
        # rotate image in the direction of velocity
        angle = self.vel.angle_to(vec(0, -1))
        self.image = pg.transform.rotate(self.normal_image, angle)
        self.rect = self.image.get_rect()
        
        self.rect.center = self.pos
        
        # create some particles for visual appeal
        self.emitParticle()
        
    
    def wander(self):
        self.arrive(self.target)
        
        if self.vel.length_squared() != 0:
            # extent vector as a multiple of the velocity
            self.extent = self.vel.normalize() * 80
            # radius
            r = 30
            # change the angle by a small random amount each frame
            self.theta += randrange(-2, 3) / 16
            self.target = self.pos + self.extent + vec(r * math.cos(self.theta), 
                                                       r * math.sin(self.theta))
        
        
    def seek(self, target):
        # get vector from self to target
        self.desired = target - self.pos
        self.desired = self.desired.normalize()
        
        self.desired *= self.maxspeed
        
        # calculate steering force
        self.steer = self.desired - self.vel
        limit(self.steer, self.maxforce)
        
        self.acc += self.steer
        
        
    def arrive(self, target):
        # get vector from self to target
        self.desired = target - self.pos
        d = self.desired.length()
        self.desired = self.desired.normalize()
        
        radius = 100
        
        if d < radius:
            m = remap(d, 0, radius, 0, self.maxspeed)
            self.desired *= m
            
        else:
            self.desired *= self.maxspeed
        
        # calculate steering force
        self.steer = self.desired - self.vel
        limit(self.steer, self.maxforce)
        
        self.acc += self.steer
        
        
    def follow(self):
        desired = self.game.flowfield.lookup(self.pos)
        desired *= self.maxspeed
        
        steer = desired - self.vel
        limit(steer, self.maxforce)
        self.acc += steer
        
        

    def emitParticle(self):
        if self.clock >= 3:
            self.clock = 0
            Particle(self.game, self.pos, self.size[0] / 4)



class Particle(pg.sprite.Sprite):
    def __init__(self, game, pos, diameter):
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self)
        self.layer = -1
        self.groups.add(self, layer=self.layer)
        self.game = game
        self.pos = vec(pos)
        
        self.image = pg.Surface((diameter, diameter))
        self.image.fill((0, 0, 0))
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        
        
        pg.draw.ellipse(self.image, (255, 100, 0), self.rect)
        self.alpha = 255
        
        self.rect.center = self.pos
        
        
    
    
    def update(self):
        self.rect.center = self.pos
        
        self.image.set_alpha(self.alpha)
        
        self.alpha -= 5
        if self.alpha <= 0:
            self.kill()
        


# ------ MAIN -----------------------------------------------------------------
        
def run():
    g = Game()
    try:
        while g.running:
            g.new()
    except Exception:
        traceback.print_exc()
        pg.quit()
    
    pg.quit()

if __name__ == '__main__':
    run()