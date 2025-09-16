

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
PETAL_SIZE = 10
PETAL_COLOR = (255, 0, 0)
PETAL_SPEED = 2         # Degrees per frame



petal_offset = 0
petal_radius = 50       # Distance from player


camera_x = 0
camera_y = 0

player_health = 1000
player_max_health = 1000
knockback_dx = 0
knockback_dy = 0
knockback_timer = 0


basic_image_not_scaled = pygame.image.load('assets/basic.png')
pollen_image_not_scaled = pygame.image.load('assets/pollen.png')
stinger_image_not_scaled = pygame.image.load('assets/stinger.png')
missile_image_not_scaled = pygame.image.load('assets/missile.png')

basic_image = pygame.transform.scale(basic_image_not_scaled, (PETAL_SIZE*2, PETAL_SIZE*2))
pollen_image = pygame.transform.scale(pollen_image_not_scaled, (PETAL_SIZE*2, PETAL_SIZE*2))
stinger_image = pygame.transform.scale(stinger_image_not_scaled, (PETAL_SIZE*2, PETAL_SIZE*2))
missile_image = pygame.transform.scale(missile_image_not_scaled, (PETAL_SIZE*4, PETAL_SIZE*2))


common_bee_image = pygame.image.load('assets/bee.png')
unusual_bee_image = pygame.transform.scale_by(common_bee_image, 1.5)


class Petal:
    def __init__(self, angle, reload = 20, color = basic_image, shootable = False, pollen = False, ret_time = 60, damage = 10,
                  name = "", rarity_color = (0, 255, 0)):
        self.angle = angle           # Angle in degrees
        self.state = "orbiting"      # "orbiting" or "shot"
        self.shootable = shootable   # Shootable?
        self.x = 0
        self.y = 0
        self.speed = 10              # Speed when shot
        self.radius = PETAL_SIZE     # Hitbox size
        self.return_timer = 0        # Frames before returning
        self.reload_timer = 0        # Frames before it can reappear
        self.reload = reload
        self.pollen = pollen
        self.color = color
        self.return_time = ret_time
        self.damage = damage
        self.name = name
        self.rarity_color = rarity_color

    def update(self, player_pos):
        # Rotate
        self.angle = (self.angle + PETAL_SPEED) % 360
        if self.state == "orbiting":
            # Orbit around player
            rad = math.radians(self.angle)
            self.x = player_pos[0] + petal_radius * math.cos(rad)
            self.y = player_pos[1] + petal_radius * math.sin(rad)
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
            self.x = player_pos[0] + petal_radius * math.cos(rad)
            self.y = player_pos[1] + petal_radius * math.sin(rad)
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
            if self.state == "orbiting":
                # pygame.draw.circle(surface, self.color, (int(self.x - camera_x), int(self.y - camera_y)), self.radius)
                util.blitRotate2(surface, self.color, (int(self.x - camera_x)-self.color.get_width() // 2, 
                            int(self.y - camera_y)-self.color.get_height() // 2), -self.angle)
            else:
                util.blitRotate2(surface, self.color, (int(self.x - camera_x)-self.color.get_width() // 2, 
                            int(self.y - camera_y)-self.color.get_height() // 2), -math.atan2(self.dy, self.dx)/math.pi*180)


class Mob:
    def __init__(self, x, y, size=15, texture=common_bee_image, health=15, drops=[], damage = 1):
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
        self.damage = damage

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
            self.dx += dx / dist * self.speed / 10
            self.dy += dy / dist * self.speed / 10
        else:
            # Move randomly
            self.dx += (random.random()-0.5) * self.speed/10
            self.dy += (random.random()-0.5) * self.speed/10

    def draw(self, surface):
        # pygame.draw.circle(surface, self.color, (int(self.x - camera_x), int(self.y - camera_y)), self.radius)
        util.blitRotate2(surface, self.texture, (int(self.x - camera_x) - self.texture.get_width() // 2, 
                          int(self.y - camera_y) - self.texture.get_height() // 2), -math.atan2(self.dy, self.dx)/math.pi*180)
        

class Drop:
    def __init__(self, x, y, petal):
        self.x = x
        self.y = y
        self.radius = 10
        self.petal = petal
        self.timer = 600

    def draw(self, surface):
        # pygame.draw.circle(surface, self.petal.color, (int(self.x - camera_x), int(self.y - camera_y)), self.radius)
        screen.blit(self.petal.color, (int(self.x - camera_x)-self.radius, int(self.y - camera_y)-self.radius))
        # util.blitRotate2(surface, basic_image, (int(self.x - camera_x)-self.radius, 
        #                     int(self.y - camera_y)-self.radius), 0)


# Petals


basic = Petal(0, 75, basic_image, name="Basic")

cpollen = Petal(0, 30, pollen_image, True, True, 150, 19, "Pollen")
cstinger = Petal(0, 300, stinger_image, damage = 100, name = "Stinger")
cmissile = Petal(0, 45, missile_image, True, damage = 25, name = "Missile")


upollen = Petal(0, 30, pollen_image, True, True, 150, 57, "Pollen", (255, 216, 0))
ustinger = Petal(0, 300, stinger_image, damage = 300, name = "Stinger", rarity_color=(255, 216, 0))
umissile = Petal(0, 45, missile_image, True, damage = 75, name = "Missile", rarity_color=(255, 216, 0))

cbee = Mob(500, 500, 40, drops = [Drop(0, 0, cpollen), Drop(0, 0, cstinger), Drop(0, 0, cmissile)], health=37, damage = 50)
ubee = Mob(1500, 1500, 60, unusual_bee_image, 140, [Drop(0, 0, upollen), Drop(0, 0, ustinger), Drop(0, 0, umissile)], damage = 150)


gen_basic = lambda i: Petal(i * (360 // PETAL_COUNT), 75, basic_image, name="Basic")

inventory = [None] * (INVENTORY_ROWS * INVENTORY_COLS)
loadout = [gen_basic(i) for i in range(PETAL_COUNT)]

def stack(stack, petal):
    if (not stack or (stack[0].name == petal.name and
                        stack[0].rarity_color == petal.rarity_color)):
        if not stack:
            return (petal, 1)
        else:
            return (stack[0], stack[1]+1)
    return None

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
            
            try:
                pygame.draw.rect(screen, inventory[idx][0].rarity_color, rect)
            except:
                pygame.draw.rect(screen, (255, 255, 255), rect)

            pygame.draw.rect(screen, (0, 0, 0), rect, 2)
            

            if inventory[idx]:
                # text = font.render(inventory[idx][0].name[0], True, inventory[idx][0].color)
                # screen.blit(text, (rect.x + 10, rect.y + 10))
                # pygame.draw.circle(screen, inventory[idx][0].color, (rect.x + SLOT_SIZE // 2, rect.y + SLOT_SIZE // 2), 10)

                screen.blit(inventory[idx][0].color, (rect.x + SLOT_SIZE // 2 - inventory[idx][0].color.get_width() // 2, 
                                                      rect.y + SLOT_SIZE // 2 - inventory[idx][0].color.get_height() // 2))
                
                text = font.render(str(inventory[idx][1]), True, (0, 0, 0))
                screen.blit(text, (rect.x + SLOT_SIZE - 10, rect.y + SLOT_SIZE - 10))

def draw_loadout(screen):
    font = pygame.font.SysFont(None, 24)
    y = screen.get_height() - SLOT_SIZE - 20
    for i in range(len(loadout)):
        rect = pygame.Rect(100 + i * (SLOT_SIZE + 5), y, SLOT_SIZE, SLOT_SIZE)
        # pygame.draw.rect(screen, loadout[i].rarity_color, rect, 2)

        try:
            pygame.draw.rect(screen, loadout[i].rarity_color, rect)
        except:
            pygame.draw.rect(screen, (255, 255, 255), rect)
            # pygame.draw.rect(screen, loadout[i][0].rarity_color, rect)

        pygame.draw.rect(screen, (0, 0, 0), rect, 2)
       

        if loadout[i]:
            # text = font.render(loadout[i].name[0], True, loadout[i].color)
            # pygame.draw.circle(screen, loadout[i].color, (rect.x + SLOT_SIZE // 2, rect.y + SLOT_SIZE // 2), 10)
            screen.blit(loadout[i].color, (rect.x + SLOT_SIZE // 2 - loadout[i].color.get_width() // 2, 
                                           rect.y + SLOT_SIZE // 2 - loadout[i].color.get_height() // 2))
            # screen.blit(text, (rect.x + 10, rect.y + 10))

def draw_health_bar(surface, x, y, health, max_health, width=player_radius*4, height=20):
    # Background
    pygame.draw.rect(surface, (100, 100, 100), (x, y, width, height))
    # Foreground (scaled to health)
    health_width = int(width * (health / max_health))
    pygame.draw.rect(surface, (0, 255, 0), (x, y, health_width, height))
    # Border
    pygame.draw.rect(surface, (255, 255, 255), (x, y, width, height), 2)


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
                    dragging_item.rarity_color,
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
spawns = [cbee, ubee]
MAX_MOBS = 100

# i * (360 // PETAL_COUNT) notTODO notIMPORTANT


# for _ in range(NUM_MOBS):
#     x = random.randint(0, MAP_WIDTH)
#     y = random.randint(0, MAP_HEIGHT)
#     mobs.append(Mob(x, y, drops = [Drop(0, 0, pollen), Drop(0, 0, stinger), Drop(0, 0, missile)], size=40, health=37))


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
    if knockback_timer > 0:
        player_pos[0] += knockback_dx
        player_pos[1] += knockback_dy
        knockback_timer -= 1
    else:
        # Normal WASD movement
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
        petal_radius = 100
        for petal in loadout:
            if petal:
                if petal.shootable:
                    if petal.state == "orbiting":
                        petal.shoot(mouse_x, mouse_y)
    else:
        petal_radius = 50
                
                
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

    # Draw health bar

    draw_health_bar(screen, int(player_pos[0] - camera_x) - 2 * player_radius,
                    int(player_pos[1] - camera_y) + player_radius + 10, player_health, player_max_health)

    
        


    # (De)Spawn and draw mobs
    for spawn in spawns:
        if random.random() < 0.005:
            mob = Mob(
                x = spawn.x,
                y = spawn.y,
                size = spawn.radius,
                texture = spawn.texture,
                health = spawn.health,
                drops = spawn.drops
            )
            mobs.append(mob)

    while len(mobs) > MAX_MOBS:
        mobs.pop()

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

            dx = mob.x - player_pos[0]
            dy = mob.y - player_pos[1]
            dist = max(1, (dx**2 + dy**2)**0.5)
            if dist < mob.radius + player_radius:
                player_health -= mob.damage  # Damage player
                if player_health <= 0:
                    print("Game Over!")
                    running = False
                knockback_dx = -(dx / dist) * 10  # strength of knockback
                knockback_dy = -(dy / dist) * 10
                knockback_timer = 15  # frames of knockback

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

    # Draw loadout and inventory

    draw_inventory(screen)
    draw_loadout(screen)

    if dragging_item:
        font = pygame.font.SysFont(None, 24)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        # text = font.render(dragging_item.name[0], True, dragging_item.color)
        # pygame.draw.circle(screen, dragging_item.color, (mouse_x, mouse_y), 10)
        screen.blit(dragging_item.color, (mouse_x-dragging_item.radius, mouse_y-dragging_item.radius))
        # screen.blit(text, (mouse_x, mouse_y))



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
                name = drop.petal.name,
                rarity_color = drop.petal.rarity_color
            )
            # petals.append(new_petal)  # keep the drop
            
            # inventory.append((new_petal, 1))  # keep the drop
            for idx in range(INVENTORY_COLS * INVENTORY_ROWS):
                # if (not inventory[idx] or (inventory[idx][0].name == new_petal.name and
                #                            inventory[idx][0].rarity_color == new_petal.rarity_color)):
                #     if not inventory[idx]:
                #         inventory[idx] = (new_petal, 1)
                #     else:
                #         inventory[idx] = (inventory[idx][0], inventory[idx][1]+1)
                #     break
                new_stack = stack(inventory[idx], new_petal)
                if new_stack:
                    inventory[idx] = new_stack
                    break

            
            
            

    

    pygame.display.flip()

pygame.quit()
