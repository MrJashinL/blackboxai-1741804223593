import pygame
import logging
import random
from settings import *
from player import Player
from enemy import Enemy
from environment import Environment

class GameState:
    def __init__(self, selected_class=None, selected_level=0):
        self.running = True
        self.paused = False
        self.game_over = False
        self.extraction_successful = False
        
        # Level setup
        self.current_level = selected_level
        self.level_data = BACKROOMS_LEVELS[selected_level]
        
        # Game components
        self.environment = Environment()
        self.environment.generate_level(
            self.level_data['map_size'],
            self.level_data['min_rooms'],
            self.level_data['max_rooms'],
            self.level_data['extraction_points'],
            self.level_data['ambient_light']
        )
        
        # Player setup
        starting_room = random.choice(self.environment.rooms)
        start_x = starting_room.rect.centerx
        start_y = starting_room.rect.centery
        self.survivor_manager = SurvivorManager()
        self.player = Player(start_x, start_y, selected_class, self.survivor_manager)
        
        # Enemy spawning
        self.enemies = []
        self.spawn_enemies(self.level_data['enemy_count'])
        
        # Camera
        self.camera_x = 0
        self.camera_y = 0
        
        # UI elements
        self.setup_ui()
        
        # Game stats
        self.time_survived = 0
        self.items_collected = 0
        self.enemies_avoided = 0
        self.rooms_explored = set()  # Per tracciare le stanze esplorate

    def setup_ui(self):
        """Setup UI elements"""
        try:
            self.font = pygame.font.Font(None, FONT_SIZE_MEDIUM)
            self.large_font = pygame.font.Font(None, FONT_SIZE_LARGE)
        except Exception as e:
            logging.error(f"Failed to load fonts: {str(e)}")
            self.font = pygame.font.SysFont('arial', FONT_SIZE_MEDIUM)
            self.large_font = pygame.font.SysFont('arial', FONT_SIZE_LARGE)

    def load_sounds(self):
        """Load game sound effects"""
        self.sounds = {}
        try:
            # Placeholder for sound loading
            # self.sounds['footstep'] = pygame.mixer.Sound('assets/sounds/footstep.wav')
            # self.sounds['enemy_detect'] = pygame.mixer.Sound('assets/sounds/enemy_detect.wav')
            # self.sounds['extraction'] = pygame.mixer.Sound('assets/sounds/extraction.wav')
            pass
        except Exception as e:
            logging.error(f"Failed to load sounds: {str(e)}")

    def spawn_enemies(self, enemy_count):
        """Spawn enemies in random rooms"""
        self.enemies.clear()
        available_rooms = [room for room in self.environment.rooms 
                         if not room.has_extraction_point]
        
        num_enemies = min(len(available_rooms), enemy_count)
        spawn_rooms = random.sample(available_rooms, num_enemies)
        
        for room in spawn_rooms:
            patrol_points = [
                (random.randint(room.rect.left + 50, room.rect.right - 50),
                 random.randint(room.rect.top + 50, room.rect.bottom - 50))
                for _ in range(3)
            ]
            enemy = Enemy(room.rect.centerx, room.rect.centery, patrol_points)
            self.enemies.append(enemy)

    def check_room_exploration(self):
        """Check if player has entered a new room and award experience"""
        current_room = self.environment.get_room_at_position(self.player.get_position())
        if current_room and current_room not in self.rooms_explored:
            self.rooms_explored.add(current_room)
            self.player.add_experience(XP_EXPLORE)
            logging.info(f"Explored new room! Total rooms: {len(self.rooms_explored)}")

    def check_enemy_avoidance(self):
        """Check if player successfully avoided nearby enemies"""
        player_pos = self.player.get_position()
        for enemy in self.enemies:
            enemy_pos = enemy.get_position()
            distance = math.sqrt((player_pos[0] - enemy_pos[0])**2 + 
                               (player_pos[1] - enemy_pos[1])**2)
            if distance < ENEMY_DETECTION_RANGE * 1.5:  # Se il giocatore è vicino ma non viene rilevato
                if enemy.current_state != enemy.CHASE:
                    self.enemies_avoided += 1
                    self.player.add_experience(XP_AVOID_ENEMY)
                    logging.info("Successfully avoided enemy!")

    def check_extraction(self):
        """Check if player has reached an extraction point"""
        if self.environment.is_extraction_point(self.player.get_position()):
            self.extraction_successful = True
            self.game_over = True
            self.player.add_experience(XP_EXTRACTION)
            logging.info("Extraction successful!")

    def update_camera(self):
        """Update camera position to follow player"""
        target_x = self.player.x - SCREEN_WIDTH // 2
        target_y = self.player.y - SCREEN_HEIGHT // 2
        
        # Smooth camera movement
        self.camera_x += (target_x - self.camera_x) * 0.1
        self.camera_y += (target_y - self.camera_y) * 0.1
        
        # Keep camera within map bounds
        self.camera_x = max(0, min(self.camera_x, MAP_WIDTH * TILE_SIZE - SCREEN_WIDTH))
        self.camera_y = max(0, min(self.camera_y, MAP_HEIGHT * TILE_SIZE - SCREEN_HEIGHT))

    def handle_collisions(self):
        """Handle collisions between game objects"""
        # Player-Enemy collisions
        player_rect = self.player.rect
        for enemy in self.enemies:
            if player_rect.colliderect(enemy.rect):
                self.player.take_damage(10)
                if not self.player.is_alive():
                    self.game_over = True
                    return
        
        # Player-Extraction point collisions
        player_pos = self.player.get_position()
        if self.environment.is_extraction_point(player_pos):
            self.extraction_successful = True
            self.game_over = True

    def update(self):
        """Update game state"""
        if self.paused or self.game_over:
            return

        # Update time survived
        self.time_survived += 1/FPS

        # Handle input
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        
        # Update player
        self.player.update()
        
        # Update enemies
        player_pos = self.player.get_position()
        player_noise = self.player.get_noise_level()
        for enemy in self.enemies:
            enemy.update(player_pos, player_noise)
        
        # Update environment
        self.environment.update_lighting()
        
        # Update camera
        self.update_camera()
        
        # Check various game conditions
        self.check_room_exploration()
        self.check_enemy_avoidance()
        self.check_extraction()
        
        # Handle collisions
        self.handle_collisions()

    def draw_hud(self, screen):
        """Draw heads-up display"""
        try:
            # Health bar
            health_text = f"Health: {self.player.health}/{self.player.max_health}"
            health_surface = self.font.render(health_text, True, WHITE)
            screen.blit(health_surface, (20, 20))
            
            # Stamina bar
            stamina_text = f"Stamina: {int(self.player.stamina)}/{self.player.max_stamina}"
            stamina_surface = self.font.render(stamina_text, True, WHITE)
            screen.blit(stamina_surface, (20, 50))
            
            # Level info
            level_text = f"Level {self.current_level}: {BACKROOMS_LEVELS[self.current_level]['name']}"
            level_surface = self.font.render(level_text, True, WHITE)
            screen.blit(level_surface, (20, 80))
            
            # Experience
            exp_text = f"XP: {self.player.experience_gained}"
            exp_surface = self.font.render(exp_text, True, WHITE)
            screen.blit(exp_surface, (20, 110))
            
            # Stats
            stats_text = f"Rooms: {len(self.rooms_explored)} | Avoided: {self.enemies_avoided}"
            stats_surface = self.font.render(stats_text, True, WHITE)
            screen.blit(stats_surface, (20, 140))
            
            # Noise level indicator
            noise_level = self.player.get_noise_level()
            noise_text = f"Noise: {'!' * (noise_level // 20)}"
            noise_color = (
                min(255, noise_level * 2),
                max(0, 255 - noise_level * 2),
                0
            )
            noise_surface = self.font.render(noise_text, True, noise_color)
            screen.blit(noise_surface, (20, 170))
            
        except Exception as e:
            logging.error(f"Error drawing HUD: {str(e)}")

    def draw_game_over_screen(self, screen):
        """Draw game over screen overlay"""
        try:
            # Semi-transparent overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill(BLACK)
            overlay.set_alpha(192)
            screen.blit(overlay, (0, 0))
            
            # Game over message
            if self.extraction_successful:
                title_text = "EXTRACTION SUCCESSFUL"
                title_color = GREEN
            else:
                title_text = "GAME OVER"
                title_color = RED
            
            title_surface = self.large_font.render(title_text, True, title_color)
            title_rect = title_surface.get_rect(center=(SCREEN_WIDTH//2, 
                                                      SCREEN_HEIGHT//2 - 50))
            screen.blit(title_surface, title_rect)
            
            # Stats
            stats_text = [
                f"Time Survived: {int(self.time_survived)}s",
                f"Rooms Explored: {len(self.rooms_explored)}",
                f"Enemies Avoided: {self.enemies_avoided}",
                f"Experience Gained: {self.player.experience_gained}"
            ]
            
            y_offset = 20
            for text in stats_text:
                surface = self.font.render(text, True, WHITE)
                rect = surface.get_rect(center=(SCREEN_WIDTH//2, 
                                              SCREEN_HEIGHT//2 + y_offset))
                screen.blit(surface, rect)
                y_offset += 30
            
            # Instructions
            instructions = self.font.render("Press SPACE to restart", True, WHITE)
            inst_rect = instructions.get_rect(center=(SCREEN_WIDTH//2, 
                                                    SCREEN_HEIGHT//2 + 100))
            screen.blit(instructions, inst_rect)
            
        except Exception as e:
            logging.error(f"Error drawing game over screen: {str(e)}")

    def draw(self, screen):
        """Draw game state"""
        try:
            # Clear screen
            screen.fill(BLACK)
            
            # Draw environment
            self.environment.draw(screen, (self.camera_x, self.camera_y))
            
            # Draw enemies
            for enemy in self.enemies:
                enemy.draw(screen)
            
            # Draw player
            self.player.draw(screen)
            
            # Draw HUD
            self.draw_hud(screen)
            
            # Draw pause/game over screen if necessary
            if self.paused:
                self.draw_pause_screen(screen)
            elif self.game_over:
                self.draw_game_over_screen(screen)
                
        except Exception as e:
            logging.error(f"Error drawing game state: {str(e)}")

    def draw_hud(self, screen):
        """Draw heads-up display"""
        try:
            # Health bar
            health_text = f"Health: {self.player.health}"
            health_surface = self.font.render(health_text, True, WHITE)
            screen.blit(health_surface, (20, 20))
            
            # Time survived
            time_text = f"Time: {int(self.time_survived)}s"
            time_surface = self.font.render(time_text, True, WHITE)
            screen.blit(time_surface, (20, 50))
            
            # Noise level indicator
            noise_level = self.player.get_noise_level()
            noise_text = f"Noise: {'!' * (noise_level // 20)}"
            noise_surface = self.font.render(noise_text, True, 
                                           (255, min(255, noise_level * 2), 0))
            screen.blit(noise_surface, (20, 80))
            
        except Exception as e:
            logging.error(f"Error drawing HUD: {str(e)}")

    def draw_pause_screen(self, screen):
        """Draw pause screen overlay"""
        try:
            # Semi-transparent overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill(BLACK)
            overlay.set_alpha(128)
            screen.blit(overlay, (0, 0))
            
            # Pause text
            pause_text = self.large_font.render("PAUSED", True, WHITE)
            text_rect = pause_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(pause_text, text_rect)
            
            # Instructions
            instructions = self.font.render("Press ESC to resume", True, WHITE)
            inst_rect = instructions.get_rect(center=(SCREEN_WIDTH//2, 
                                                    SCREEN_HEIGHT//2 + 50))
            screen.blit(instructions, inst_rect)
            
        except Exception as e:
            logging.error(f"Error drawing pause screen: {str(e)}")

    def draw_game_over_screen(self, screen):
        """Draw game over screen overlay"""
        try:
            # Semi-transparent overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill(BLACK)
            overlay.set_alpha(192)
            screen.blit(overlay, (0, 0))
            
            # Game over message
            if self.extraction_successful:
                title_text = "EXTRACTION SUCCESSFUL"
                title_color = (0, 255, 0)
            else:
                title_text = "GAME OVER"
                title_color = (255, 0, 0)
            
            title_surface = self.large_font.render(title_text, True, title_color)
            title_rect = title_surface.get_rect(center=(SCREEN_WIDTH//2, 
                                                      SCREEN_HEIGHT//2 - 50))
            screen.blit(title_surface, title_rect)
            
            # Stats
            stats_text = [
                f"Time Survived: {int(self.time_survived)}s",
                f"Items Collected: {self.items_collected}",
                f"Enemies Avoided: {self.enemies_avoided}"
            ]
            
            y_offset = 20
            for text in stats_text:
                surface = self.font.render(text, True, WHITE)
                rect = surface.get_rect(center=(SCREEN_WIDTH//2, 
                                              SCREEN_HEIGHT//2 + y_offset))
                screen.blit(surface, rect)
                y_offset += 30
            
            # Instructions
            instructions = self.font.render("Press SPACE to restart", True, WHITE)
            inst_rect = instructions.get_rect(center=(SCREEN_WIDTH//2, 
                                                    SCREEN_HEIGHT//2 + 100))
            screen.blit(instructions, inst_rect)
            
        except Exception as e:
            logging.error(f"Error drawing game over screen: {str(e)}")

    def handle_event(self, event):
        """Handle game events"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.paused = not self.paused
            elif event.key == pygame.K_SPACE and self.game_over:
                return "restart"
        return None

    def reset(self):
        """Reset game state"""
        self.__init__()
