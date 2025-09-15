

import pygame
import math
import random
import util
import copy

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Florr.io Clone - Player Movement")

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)

# Clock for FPS control
clock = pygame.time.Clock()
FPS = 60

# Map variables
MAP_WIDTH = 2000
MAP_HEIGHT = 2000
TILE_SIZE = 50

# Inventory variables

INVENTORY_ROWS = 5
INVENTORY_COLS = 4
SLOT_SIZE = 50





# Player settings
player_pos = [MAP_WIDTH // 2, MAP_HEIGHT // 2]  # Starting in the center
player_speed = 5
player_radius = 20

# Petal settings
PETAL_COUNT = 8
PETAL_RADIUS = 50       # Distance from player
PETAL_SIZE = 10
PETAL_COLOR = (255, 0, 0)
PETAL_SPEED = 2         # Degrees per frame



petal_offset = 0

camera_x = 0
camera_y = 0

bee_image = pygame.image.load('bee.png')



class Petal:
    def __init__(self, angle, reload = 20, color = PETAL_COLOR, shootable = False, pollen = False, ret_time = 60, damage = 10,
                  name = ""):
        self.angle = angle      # Angle in degrees
        self.state = "orbiting" # "orbiting" or "shot"
        self.shootable = shootable   # Shootable?
        self.x = 0
        self.y = 0
        self.speed = 10         # Speed when shot
        self.radius = 10        # Draw size
        self.return_timer = 0   # Frames before returning
        self.reload_timer = 0  # Frames before it can reappear
        self.reload = reload
        self.pollen = pollen
        self.color = color
        self.return_time = ret_time
        self.damage = damage
        self.name = name

    def update(self, player_pos):
        # Rotate
        self.angle = (self.angle + PETAL_SPEED) % 360
        if self.state == "orbiting":
            # Orbit around player
            rad = math.radians(self.angle)
            self.x = player_pos[0] + PETAL_RADIUS * math.cos(rad)
            self.y = player_pos[1] + PETAL_RADIUS * math.sin(rad)
        elif self.state == "shot":
            # Move outward in the set direction
            if self.pollen:
                self.dx *= 0.9
                self.dy *= 0.9
            self.x += self.dx
            self.y += self.dy
            self.return_timer -= 1
            if self.return_timer <= 0:
                self.state = "orbiting"
        elif self.state == "reloading":
            rad = math.radians(self.angle)
            self.x = player_pos[0] + PETAL_RADIUS * math.cos(rad)
            self.y = player_pos[1] + PETAL_RADIUS * math.sin(rad)
            self.reload_timer -= 1
            if self.reload_timer <= 0:
                self.state = "orbiting"

    def shoot(self, out_x, out_y):
        if self.state == "orbiting":
            self.state = "shot"
            # Calculate direction outwards from player
            angle = math.atan2(self.y - player_pos[1], self.x - player_pos[0])
            self.dx = math.cos(angle) * self.speed
            self.dy = math.sin(angle) * self.speed
            self.return_timer = self.return_time  # Frames before returning to orbit

    def hit_mob(self):
        self.state = "reloading"
        self.reload_timer = self.reload  # Number of frames petal disappears

    def draw(self, surface):
        if self.state != "reloading":  # Don't draw while reloading
            pygame.draw.circle(surface, self.color, (int(self.x - camera_x), int(self.y - camera_y)), self.radius)

class Mob:
    def __init__(self, x, y, size=15, texture=bee_image, health=15, drops=[]):
        self.x = x
        self.y = y
        self.dx = 0
        self.dy = 0
        self.speed = 5
        self.radius = size
        self.texture = texture
        self.health = health
        self.drops = drops
        self.angry = False

    def update(self, player_pos):
        self.x += self.dx
        self.y += self.dy
        self.dx = min(max(self.dx, -self.speed), self.speed)
        self.dy = min(max(self.dy, -self.speed), self.speed)
        
        # self.x = min(max(self.x, self.radius), MAP_WIDTH - self.radius)
        # self.y = min(max(self.y, self.radius), MAP_HEIGHT - self.radius)
        if self.x < self.radius:
            self.x = self.radius
            self.dx *= -1
        if self.x > MAP_WIDTH - self.radius:
            self.x = MAP_WIDTH - self.radius
            self.dx *= -1
        if self.y < self.radius:
            self.y = self.radius
            self.dy *= -1
        if self.y > MAP_WIDTH - self.radius:
            self.y = MAP_WIDTH - self.radius
            self.dy *= -1
        if self.angry:
            # Move toward the player
            dx = player_pos[0] - self.x
            dy = player_pos[1] - self.y
            dist = max(1, (dx**2 + dy**2)**0.5)  # Avoid division by 0
            self.dx += dx / dist * self.speed / 5
            self.dy += dy / dist * self.speed / 5
        else:
            # Move randomly
            self.dx += (random.random()-0.5) * self.speed/5
            self.dy += (random.random()-0.5) * self.speed/5

    def draw(self, surface):
        # pygame.draw.circle(surface, self.color, (int(self.x - camera_x), int(self.y - camera_y)), self.radius)
        util.blitRotate2(surface, self.texture, (int(self.x - camera_x) - self.texture.get_width() // 2, 
                          int(self.y - camera_y) - self.texture.get_height() // 2), -math.atan2(self.dy, self.dx))
        

class Drop:
    def __init__(self, x, y, petal):
        self.x = x
        self.y = y
        self.radius = 8
        self.petal = petal
        self.timer = 600

    def draw(self, surface):
        pygame.draw.circle(surface, self.petal.color, (int(self.x - camera_x), int(self.y - camera_y)), self.radius)


pollen = Petal(0, 30, (255, 216, 0), True, True, 150, 19, "Pollen")
stinger = Petal(0, 300, (0, 0, 0), damage = 100, name = "Stinger")
basic = Petal(0, 75, (216, 216, 216), name="Basic")
missile = Petal(0, 45, (64, 64, 64), True, damage = 75, name = "Missile")


gen_basic = lambda i: Petal(i * (360 // PETAL_COUNT), 75, (216, 216, 216), name="Basic")

inventory = [None] * (INVENTORY_ROWS * INVENTORY_COLS)
loadout = [gen_basic(i) for i in range(PETAL_COUNT)]

def update_camera(player_pos):
    global camera_x, camera_y
    camera_x = player_pos[0] - WIDTH // 2
    camera_y = player_pos[1] - HEIGHT // 2

     # Clamp so camera never shows outside map bounds
    if camera_x < 0:
        camera_x = 0
    if camera_y < 0:
        camera_y = 0
    if camera_x > MAP_WIDTH - WIDTH:
        camera_x = MAP_WIDTH - WIDTH
    if camera_y > MAP_HEIGHT - HEIGHT:
        camera_y = MAP_HEIGHT - HEIGHT

def draw_map(surface):
    # Draw grid lines for reference
    for x in range(0, MAP_WIDTH, TILE_SIZE):
        pygame.draw.line(surface, (200, 200, 200), (x - camera_x, 0 - camera_y), (x - camera_x, MAP_HEIGHT - camera_y))
    for y in range(0, MAP_HEIGHT, TILE_SIZE):
        pygame.draw.line(surface, (200, 200, 200), (0 - camera_x, y - camera_y), (MAP_WIDTH - camera_x, y - camera_y))

def ask_yes_no(screen, question):
    font = pygame.font.SysFont(None, 32)
    question_surf = font.render(question, True, (255, 255, 255))

    # Buttons
    yes_rect = pygame.Rect(150, 300, 100, 50)
    no_rect = pygame.Rect(350, 300, 100, 50)

    while True:
        screen.fill((30, 30, 30))
        screen.blit(question_surf, (100, 150))

        pygame.draw.rect(screen, (0, 200, 0), yes_rect)
        pygame.draw.rect(screen, (200, 0, 0), no_rect)

        yes_text = font.render("Yes", True, (255, 255, 255))
        no_text = font.render("No", True, (255, 255, 255))
        screen.blit(yes_text, (yes_rect.x + 25, yes_rect.y + 10))
        screen.blit(no_text, (no_rect.x + 30, no_rect.y + 10))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if yes_rect.collidepoint(event.pos):
                    return True
                elif no_rect.collidepoint(event.pos):
                    return False

def draw_inventory(screen):
    font = pygame.font.SysFont(None, 24)
    for row in range(INVENTORY_ROWS):
        for col in range(INVENTORY_COLS):
            idx = row * INVENTORY_COLS + col
            rect = pygame.Rect(20 + col * (SLOT_SIZE + 5), 
                               20 + row * (SLOT_SIZE + 5), 
                               SLOT_SIZE, SLOT_SIZE)
            pygame.draw.rect(screen, (200, 200, 200), rect, 2)


            if inventory[idx]:
                # text = font.render(inventory[idx][0].name[0], True, inventory[idx][0].color)
                # screen.blit(text, (rect.x + 10, rect.y + 10))
                pygame.draw.circle(screen, inventory[idx][0].color, (rect.x + SLOT_SIZE // 2, rect.y + SLOT_SIZE // 2), 10)
                text = font.render(str(inventory[idx][1]), True, inventory[idx][0].color)
                screen.blit(text, (rect.x + SLOT_SIZE - 10, rect.y + SLOT_SIZE - 10))

def draw_loadout(screen):
    font = pygame.font.SysFont(None, 24)
    y = screen.get_height() - SLOT_SIZE - 20
    for i in range(len(loadout)):
        rect = pygame.Rect(100 + i * (SLOT_SIZE + 5), y, SLOT_SIZE, SLOT_SIZE)
        pygame.draw.rect(screen, (150, 150, 255), rect, 2)

        if loadout[i]:
            # text = font.render(loadout[i].name[0], True, loadout[i].color)
            pygame.draw.circle(screen, loadout[i].color, (rect.x + SLOT_SIZE // 2, rect.y + SLOT_SIZE // 2), 10)
            # screen.blit(text, (rect.x + 10, rect.y + 10))


dragging_item = None
dragging_from = None

def handle_mouse_events(event, screen_height):
    global dragging_item, dragging_from

    if event.type == pygame.MOUSEBUTTONDOWN:
        # print("Mouse down.")
        pos = event.pos
        # Check inventory slots
        for row in range(INVENTORY_ROWS):
            for col in range(INVENTORY_COLS):
                idx = row * INVENTORY_COLS + col
                rect = pygame.Rect(20 + col * (SLOT_SIZE + 5),
                                   20 + row * (SLOT_SIZE + 5),
                                   SLOT_SIZE, SLOT_SIZE)
                if rect.collidepoint(pos) and inventory[idx][0]:
                    dragging_item = inventory[idx][0]
                    dragging_from = ("inventory", idx)
                    if inventory[idx][1] == 1:
                        inventory[idx] = None
                    else:
                        inventory[idx] = (inventory[idx][0], inventory[idx][1]-1)

        # Check loadout slots
        y = screen_height - SLOT_SIZE - 20
        for i in range(len(loadout)):
            rect = pygame.Rect(100 + i * (SLOT_SIZE + 5), y, SLOT_SIZE, SLOT_SIZE)
            if rect.collidepoint(pos) and loadout[i]:
                dragging_item = loadout[i]
                dragging_from = ("loadout", i)
                loadout[i] = None

    elif event.type == pygame.MOUSEBUTTONUP and dragging_item:
        # print("Mouse up.")
        pos = event.pos
        placed = False

        # Drop into inventory
        for row in range(INVENTORY_ROWS):
            for col in range(INVENTORY_COLS):
                idx = row * INVENTORY_COLS + col
                rect = pygame.Rect(20 + col * (SLOT_SIZE + 5),
                                   20 + row * (SLOT_SIZE + 5),
                                   SLOT_SIZE, SLOT_SIZE)
                
                if rect.collidepoint(pos) and (not inventory[idx] or inventory[idx][0].name == dragging_item.name):
                    if not inventory[idx]:
                        inventory[idx] = (dragging_item, 1)
                    else:
                        inventory[idx] = (inventory[idx][0], inventory[idx][1]+1)
                    placed = True

        # Drop into loadout
        y = screen_height - SLOT_SIZE - 20
        for i in range(len(loadout)):
            rect = pygame.Rect(100 + i * (SLOT_SIZE + 5), y, SLOT_SIZE, SLOT_SIZE)
            if rect.collidepoint(pos) and not loadout[i]:
                dragging_item.angle = i * (360 // PETAL_COUNT) + petal_offset
                item = Petal(
                    i * (360 // PETAL_COUNT) + petal_offset,
                    dragging_item.reload,
                    dragging_item.color,
                    dragging_item.shootable,
                    dragging_item.pollen,
                    dragging_item.return_time,
                    dragging_item.damage,
                    dragging_item.name,
                )
                loadout[i] = item
                placed = True

        # If not placed, return to original spot
        if not placed and dragging_from:
            if dragging_from[0] == "inventory":
                if not inventory[idx]:
                    inventory[dragging_from[1]] = (dragging_item, 1)
                else:
                    inventory[dragging_from[1]] = (inventory[dragging_from[1]][0], inventory[dragging_from[1]][1]+1)
            elif dragging_from[0] == "loadout":
                loadout[dragging_from[1]] = dragging_item

        dragging_item = None
        dragging_from = None



# Create petals evenly spaced
# petals = [basic for i in range(PETAL_COUNT)]
drops = []
mobs = []
NUM_MOBS = 10

# i * (360 // PETAL_COUNT) notTODO notIMPORTANT


for _ in range(NUM_MOBS):
    x = random.randint(0, MAP_WIDTH)
    y = random.randint(0, MAP_HEIGHT)
    mobs.append(Mob(x, y, drops = [Drop(0, 0, pollen), Drop(0, 0, stinger), Drop(0, 0, missile)], size=40, health=37))


running = True
while running:
    clock.tick(FPS)
    screen.fill(WHITE)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        handle_mouse_events(event, HEIGHT)

    # Movement keys
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        player_pos[1] -= player_speed
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        player_pos[1] += player_speed
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        player_pos[0] -= player_speed
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        player_pos[0] += player_speed
    if keys[pygame.K_SPACE]:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        for petal in loadout:
            if petal:
                if petal.shootable:
                    if petal.state == "orbiting":
                        petal.shoot(mouse_x, mouse_y)
                
    if keys[pygame.K_LSHIFT]:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        for petal in loadout:
            if petal.shootable:
                if petal.state == "shot":
                    petal.return_timer = 0






    # Keep player inside screen boundaries
    player_pos[0] = max(player_radius, min(MAP_WIDTH - player_radius, player_pos[0]))
    player_pos[1] = max(player_radius, min(MAP_HEIGHT - player_radius, player_pos[1]))

    # Draw map

    draw_map(screen)

    # Draw player
    pygame.draw.circle(screen, GREEN, (int(player_pos[0] - camera_x), int(player_pos[1] - camera_y)), player_radius)

    # Update and draw petals
    petal_offset += 2
    for petal in loadout:
        if petal:
            petal.update(player_pos)
            petal.draw(screen)

    update_camera(player_pos)

    # Draw loadout and inventory

    draw_inventory(screen)
    draw_loadout(screen)

    if dragging_item:
        font = pygame.font.SysFont(None, 24)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        # text = font.render(dragging_item.name[0], True, dragging_item.color)
        pygame.draw.circle(screen, dragging_item.color, (mouse_x, mouse_y), 10)
        # screen.blit(text, (mouse_x, mouse_y))
        


    # Spawn and draw mobs

    if random.random() < 0.01:
        mob = Mob(500, 500, drops = [Drop(0, 0, pollen), Drop(0, 0, stinger), Drop(0, 0, missile)], size=40, health=37)
        mobs.append(mob)

    for mob in mobs[:]:
        mob.update(player_pos)
        mob.draw(screen)
        for petal in loadout:
            if not petal:
                continue
            # Simple circle collision
            dx = mob.x - petal.x
            dy = mob.y - petal.y
            dist = (dx**2 + dy**2)**0.5
            if dist < mob.radius + petal.radius:
                if petal.state != "reloading":
                    mob.health -= petal.damage  # Petal damages mob
                    # print(f"{petal.name}: {petal.damage}")
                    mob.angry = True
                    petal.hit_mob()
                    if petal.state == "shot":  # Only shot petals reset timer
                        petal.return_timer = 0
                        petal.state = "orbiting"
                    if mob.health <= 0:
                        drop = random.choice(mob.drops)
                        drop.x = mob.x + 40 * (random.random() - 0.5)
                        drop.y = mob.y + 40 * (random.random() - 0.5)
                        # Spawn the drop
                        drops.append(drop)
                        try:
                            mobs.remove(mob)  # Mob dies
                        except:
                            pass

    # Handle collisions between mobs
    for i in range(len(mobs)):
        for j in range(i + 1, len(mobs)):
            mob1 = mobs[i]
            mob2 = mobs[j]

            dx = mob2.x - mob1.x
            dy = mob2.y - mob1.y
            dist = math.hypot(dx, dy)

            if dist < mob1.radius + mob2.radius and dist > 0:
                # How much overlap there is
                overlap = (mob1.radius + mob2.radius) - dist

                # Normalize direction vector
                nx = dx / dist
                ny = dy / dist

                # Push each mob away from the other
                mob1.x -= nx * overlap / 2
                mob1.y -= ny * overlap / 2
                mob2.x += nx * overlap / 2
                mob2.y += ny * overlap / 2

                # Optional: add a little bounce to their velocities
                mob1.dx -= nx * 0.5
                mob1.dy -= ny * 0.5
                mob2.dx += nx * 0.5
                mob2.dy += ny * 0.5



    # Draw drops
    for drop in drops[:]:
        drop.timer -= 1
        if drop.timer < 0:
            drops.remove(drop)
            continue
        drop.draw(screen)
        dx = drop.x - player_pos[0]
        dy = drop.y - player_pos[1]
        dist = (dx**2 + dy**2)**0.5
        if dist < player_radius + drop.radius:
            
            # Collect the drop
            drops.remove(drop)
            # print(f"Collected {drop.item}!")
            """
            petal = drop.petal
            petal.angle = petals.pop(0).angle
            petals.append(petal)
            """

            

            new_petal = Petal(
                angle = 0,
                reload = drop.petal.reload,
                color = drop.petal.color,
                shootable = drop.petal.shootable,
                pollen = drop.petal.pollen,
                ret_time = drop.petal.return_time,
                damage = drop.petal.damage,
                name = drop.petal.name
            )
            # petals.append(new_petal)  # keep the drop
            
            # inventory.append((new_petal, 1))  # keep the drop
            for idx in range(INVENTORY_COLS * INVENTORY_ROWS):
                if (not inventory[idx] or inventory[idx][0].name == new_petal.name):
                    if not inventory[idx]:
                        inventory[idx] = (new_petal, 1)
                    else:
                        inventory[idx] = (inventory[idx][0], inventory[idx][1]+1)
                    break
            
            break

    

    pygame.display.flip()

pygame.quit()
