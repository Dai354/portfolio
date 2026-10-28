import pygame
import random

pygame.init()

# Constants
WIDTH, HEIGHT = 1200, 800
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rocket 2025 Internship Game")

# Colors
WHITE = (255, 255, 255)
RED = (200, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

# Game settings
FPS = 60
IMMUNE_DURATION = int(6.5 * FPS) # frames, so it stops counting down while paused
HIGH_SCORE_FILE = "high_score.txt"

# Platform layout. A full jump covers ~300px sideways, less when jumping upward,
# so the widest possible gap (including both platforms drifting apart) stays below that.
MIN_GAP = 40
MAX_GAP = 200
PLATFORM_MIN_RANGE = 30
PLATFORM_MAX_RANGE = 80
MAX_STEP_UP = 150 # how much higher the next platform can be

# Difficulty: falling objects spawn more often and fall faster as the score rises
START_SPAWN_FRAMES = 120 # 2 seconds
MIN_SPAWN_FRAMES = 40
SPAWN_SPEEDUP_EVERY = 500 # score points per step
SPAWN_SPEEDUP_STEP = 10 # frames removed per step
FALL_SPEEDUP_EVERY = 1000 # score points per +1 fall speed

ROTATE_SPEED = 6 # degrees per frame while the screen spins into/out of inverted mode
# The 180° rotation already makes LEFT/RIGHT feel backwards on screen.
# Set this to True to also swap the keys (which cancels that out and feels "normal" again).
SWAP_KEYS_WHEN_INVERTED = False

# Fonts
FONT = pygame.font.SysFont(None, 30)
LARGE_FONT = pygame.font.SysFont(None, 60, bold=True)

# Load images helper
def load_image(path, size=None):
    try:
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.scale(img, size)
        return img
    except (pygame.error, FileNotFoundError):
        print(f"Missing image: {path}, using placeholder.")
        surf = pygame.Surface(size or (60, 60))
        surf.fill((150, 150, 150))
        return surf

# Load images (use your actual paths)
player_imgs = [
    load_image("Breyona Sprite.png"),
    load_image("AnimationSheet_Character-1.png.png"),
    load_image("Z_Character.png"),
    load_image("Jeremiah_Character.png")
]

rock_img = load_image("Moon_rock.png", (140, 140))
bomb_img = load_image("Trap2.png", (200, 200))
platform_img = load_image("Idle.png", (200, 40))
trap_platform_img = load_image("BLOCK5.png", (200, 40))
background_img = load_image("Day_Background.png", (WIDTH, HEIGHT))
inverted_background_img = load_image("Game_ Background.png", (WIDTH, HEIGHT))
heal_img = load_image("751.png", (40, 40))
immunity_img = load_image("8794823.png", (40, 40))

# The game world is drawn onto this surface first, then rotated onto WIN in inverted mode
world_surface = pygame.Surface((WIDTH, HEIGHT))

try:
    pygame.mixer.music.load("Roa - Pixel Story.mp3")
    pygame.mixer.music.play(-1)
except Exception as e:
    print("Could not load music:", e)

# Player scales per character index
player_scales = [3.0, 2.0, 0.6, 1.7]

# Classes
class Player(pygame.sprite.Sprite):
    def __init__(self, start_pos, image, scale_factor=1):
        super().__init__()
        self.original_image = image
        self.image = pygame.transform.scale_by(self.original_image, scale_factor)
        self.rect = self.image.get_rect(midbottom=start_pos)
        self.speed = 5
        self.health = 200
        self.y_velocity = 0
        self.on_ground = False
        self.immune = False
        self.collision_rect = pygame.Rect(0, 0, self.rect.width * 0.4, self.rect.height * 0.8)
        self.collision_rect.midbottom = self.rect.midbottom
        self.facing_left = False
        
    def update(self, keys, swap_keys=False):
        left_key, right_key = pygame.K_LEFT, pygame.K_RIGHT
        if swap_keys:
            left_key, right_key = right_key, left_key

        if keys[left_key]:
            self.rect.x -= self.speed
            self.facing_left = True
        if keys[right_key]:
            self.rect.x += self.speed
            self.facing_left = False
        
        gravity = 0.5
        jump_force = -15

        self.y_velocity += gravity

        prev_bottom = self.rect.bottom
        self.rect.y += self.y_velocity
        self.collision_rect.midbottom = self.rect.midbottom

        on_ground_this_frame = False
        for plat in platforms:
            if self.collision_rect.colliderect(plat['rect']):
                # Only land if we were above the platform last frame, not when hitting it from the side or below
                if self.y_velocity > 0 and prev_bottom <= plat['rect'].top:
                    self.rect.bottom = plat['rect'].top
                    self.y_velocity = 0
                    on_ground_this_frame = True
                    if plat.get('has_trap', False) and not self.immune:
                        self.health -= 1
        
        self.on_ground = on_ground_this_frame
        self.collision_rect.midbottom = self.rect.midbottom

        # Death if off-screen vertically
        if self.rect.top > HEIGHT:
            self.health = 0

        if keys[pygame.K_SPACE] and self.on_ground:
            self.y_velocity = jump_force

        self.health = max(0, min(self.health, 200))
        
    def set_character(self, new_image, scale_factor):
        old_bottom = self.rect.midbottom
        self.original_image = new_image
        self.image = pygame.transform.scale_by(self.original_image, scale_factor)
        self.rect = self.image.get_rect(midbottom=old_bottom)
        self.collision_rect = pygame.Rect(0, 0, self.rect.width * 0.4, self.rect.height * 0.8)
        self.collision_rect.midbottom = self.rect.midbottom

class FallingObject(pygame.sprite.Sprite):
    def __init__(self, image, damage, camera_x, speed_bonus=0):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        # Spawn within the currently visible area (world coords = screen + camera_x)
        self.rect.x = random.randint(camera_x, camera_x + WIDTH - self.rect.width)
        self.speed = random.randint(3, 6) + speed_bonus
        self.damage = damage
        self.rect.y = -self.rect.height

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()

class SpecialItem(pygame.sprite.Sprite):
    def __init__(self, image, platform, item_type):
        super().__init__()
        self.image = image
        self.platform = platform
        self.rect = self.image.get_rect()
        self.item_type = item_type
        self.update()

    def update(self):
        # Ride along on top of the (moving) platform
        self.rect.midbottom = self.platform['rect'].midtop

def draw_health_bar(surface, x, y, health):
    ratio = max(0, min(health, 200)) / 200
    pygame.draw.rect(surface, RED, (x, y, 100, 15))
    pygame.draw.rect(surface, GREEN, (x, y, 100 * ratio, 15))

def load_high_score():
    try:
        with open(HIGH_SCORE_FILE) as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return 0

def save_high_score(value):
    try:
        with open(HIGH_SCORE_FILE, "w") as f:
            f.write(str(value))
    except OSError as e:
        print("Could not save high score:", e)

def spawn_interval(score):
    return max(MIN_SPAWN_FRAMES, START_SPAWN_FRAMES - (score // SPAWN_SPEEDUP_EVERY) * SPAWN_SPEEDUP_STEP)

def generate_platforms(count=8):
    # Each new platform continues from the last one so batches never overlap
    for _ in range(count):
        move_range = random.randint(PLATFORM_MIN_RANGE, PLATFORM_MAX_RANGE)
        if platforms:
            prev = platforms[-1]
            prev_right = prev['start_x'] + prev['rect'].width
            # Worst case both platforms drift apart by their full range, so leave room for that
            gap = random.randint(MIN_GAP, MAX_GAP - prev['range'] - move_range)
            x = prev_right + gap
            y = random.randint(max(400, prev['rect'].y - MAX_STEP_UP), 600)
        else:
            x = random.randint(50, 200)
            y = 500
        has_trap = random.random() < 0.25 and bool(platforms)  # never start on a trap
        img = trap_platform_img if has_trap else platform_img
        w, h = img.get_size()
        platform = {
            'rect': pygame.Rect(x, y, w, h),
            'image': img,
            'has_trap': has_trap,
            'dx': 0
        }
        platform['speed'] = random.choice([1, 2])
        platform['direction'] = random.choice([-1, 1])
        platform['range'] = move_range
        platform['start_x'] = x
        platforms.append(platform)

def reset_game():
    global platforms, special_items, falling_objects, camera_x
    global score, last_special_spawn_score, paused, game_over
    global immune_frames_left, player, all_sprites
    global screen_angle, spawn_timer, new_record

    platforms.clear()
    special_items.empty()
    falling_objects.empty()
    generate_platforms(8)

    first_platform = platforms[0]
    start_x = first_platform['rect'].centerx
    start_y = first_platform['rect'].top

    player = Player((start_x, start_y), player_imgs[current_char_index], scale_factor=player_scales[current_char_index])
    player.rect.bottom = start_y
    player.collision_rect.midbottom = player.rect.midbottom

    all_sprites = pygame.sprite.Group(player)

    camera_x = score = last_special_spawn_score = 0
    paused = game_over = new_record = False
    immune_frames_left = 0
    screen_angle = 0
    spawn_timer = START_SPAWN_FRAMES

# Initialize
platforms = []
special_items = pygame.sprite.Group()
falling_objects = pygame.sprite.Group()
current_char_index = 0
high_score = load_high_score()

reset_game()

clock = pygame.time.Clock()

while True:
    clock.tick(FPS)
    current_inverted_mode = 1500 <= score < 3000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p and not game_over:
                paused = not paused
            elif event.key == pygame.K_r and game_over:
                reset_game()
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                new_char_index = event.key - pygame.K_1
                if 0 <= new_char_index < len(player_imgs):
                    current_char_index = new_char_index
                    player.set_character(player_imgs[new_char_index], player_scales[new_char_index])

    if not paused and not game_over:
        keys = pygame.key.get_pressed()
        player.update(keys, swap_keys=current_inverted_mode and SWAP_KEYS_WHEN_INVERTED)

        spawn_timer -= 1
        if spawn_timer <= 0:
            obj = FallingObject(random.choice([rock_img, bomb_img]), damage=random.choice([10, 20]),
                                camera_x=camera_x, speed_bonus=score // FALL_SPEEDUP_EVERY)
            falling_objects.add(obj)
            all_sprites.add(obj)
            spawn_timer = spawn_interval(score)

        for obj in falling_objects:
            obj.update()

        if player.immune:
            immune_frames_left -= 1
            if immune_frames_left <= 0:
                player.immune = False

        camera_x = player.rect.centerx - WIDTH // 2

        for plat in platforms:
            dx = plat['speed'] * plat['direction']
            plat['rect'].x += dx
            plat['dx'] = dx
            if abs(plat['rect'].x - plat['start_x']) > plat['range']:
                plat['direction'] *= -1
            
            # Make the player move with the platform
            if player.on_ground and player.collision_rect.colliderect(plat['rect']):
                player.rect.x += dx

        if platforms[-1]['rect'].x < player.rect.centerx + WIDTH * 1.5:
            generate_platforms(8)

        platforms[:] = [plat for plat in platforms if plat['rect'].right > camera_x - 500]

        if score - last_special_spawn_score >= 300:
            last_special_spawn_score = score
            # Prefer platforms ahead of the player that are on screen, then any ahead
            ahead = [p for p in platforms if p['rect'].left > player.rect.centerx + 150]
            on_screen = [p for p in ahead if p['rect'].right < camera_x + WIDTH]
            candidates = on_screen or ahead
            if candidates:
                plat = random.choice(candidates)
                item_type = random.choice(["immunity", "heal"])
                item_img = immunity_img if item_type == "immunity" else heal_img
                special_items.add(SpecialItem(item_img, plat, item_type))

        for item in special_items:
            item.update()
            if item.rect.right < camera_x - 500:
                item.kill()  # its platform was removed behind the player

        for item in special_items:
            if player.collision_rect.colliderect(item.rect):
                if item.item_type == "immunity":
                    player.immune = True
                    immune_frames_left = IMMUNE_DURATION
                elif item.item_type == "heal":
                    player.health = min(player.health + 33, 200)
                item.kill()

        for obj in falling_objects:
            if player.collision_rect.colliderect(obj.rect):
                if not player.immune:
                    player.health -= obj.damage
                obj.kill()

        if player.health <= 0:
            game_over = True
            if score > high_score:
                high_score = score
                new_record = True
                save_high_score(high_score)

        score += 1

    # --- Drawing section ---
    
    # Use the appropriate background based on the game mode
    # The whole world goes onto world_surface; the screen rotation turns it upside down,
    # so the inverted background no longer needs to be pre-flipped
    bg_scroll = camera_x * 0.5
    if current_inverted_mode:
        bg_to_draw = inverted_background_img
    else:
        bg_to_draw = background_img

    world_surface.blit(bg_to_draw, (-(bg_scroll % bg_to_draw.get_width()), 0))
    world_surface.blit(bg_to_draw, (-(bg_scroll % bg_to_draw.get_width()) + bg_to_draw.get_width(), 0))

    # 2. Game objects (platforms, sprites, items)
    for plat in platforms:
        world_surface.blit(plat['image'], (plat['rect'].x - camera_x, plat['rect'].y))
    
    for sprite in all_sprites:
        img_to_draw = sprite.image
        sprite_rect = sprite.rect.copy()
        
        if isinstance(sprite, Player):
            # Only flip horizontally based on direction, not vertically for inverted mode
            if sprite.facing_left:
                img_to_draw = pygame.transform.flip(img_to_draw, True, False)
                
        world_surface.blit(img_to_draw, (sprite_rect.x - camera_x, sprite_rect.y))

    for item in special_items:
        world_surface.blit(item.image, (item.rect.x - camera_x, item.rect.y))

    # Spin the screen toward 180° in inverted mode, back to 0° otherwise
    target_angle = 180 if current_inverted_mode else 0
    if screen_angle < target_angle:
        screen_angle = min(screen_angle + ROTATE_SPEED, target_angle)
    elif screen_angle > target_angle:
        screen_angle = max(screen_angle - ROTATE_SPEED, target_angle)

    if screen_angle == 0:
        WIN.blit(world_surface, (0, 0))
    elif screen_angle == 180:
        # Flipping both axes is the same as a 180° rotation, and much faster
        WIN.blit(pygame.transform.flip(world_surface, True, True), (0, 0))
    else:
        WIN.fill(BLACK)
        rotated = pygame.transform.rotate(world_surface, screen_angle)
        WIN.blit(rotated, rotated.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

    # 3. UI elements (always drawn last)
    draw_health_bar(WIN, WIDTH - 110, HEIGHT - 30, player.health)
    WIN.blit(FONT.render(f"Score: {score}", True, WHITE), (10, 10))
    WIN.blit(FONT.render(f"Best: {max(score, high_score)}", True, WHITE), (10, 35))

    if current_inverted_mode:
        WIN.blit(FONT.render("Inverted Mode", True, RED), (WIDTH - 200, 10))

    if paused:
        pause_surf = FONT.render("Paused", True, RED)
        WIN.blit(pause_surf, (WIDTH // 2 - pause_surf.get_width() // 2, HEIGHT // 2 - 20))
    
    if game_over:
        game_over_text = "GAME OVER"
        restart_text = "Press R to Restart"
        
        game_over_surf = LARGE_FONT.render(game_over_text, True, RED)
        restart_surf = FONT.render(restart_text, True, WHITE)
        
        WIN.blit(game_over_surf, (WIDTH // 2 - game_over_surf.get_width() // 2, HEIGHT // 2 - game_over_surf.get_height() // 2 - 30))
        WIN.blit(restart_surf, (WIDTH // 2 - restart_surf.get_width() // 2, HEIGHT // 2 + restart_surf.get_height() // 2 + 10))

        if new_record:
            record_surf = FONT.render("New best score!", True, GREEN)
            WIN.blit(record_surf, (WIDTH // 2 - record_surf.get_width() // 2, HEIGHT // 2 + 60))
    
    pygame.display.update()