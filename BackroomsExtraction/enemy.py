import pygame
import math
import random
import logging
from settings import *

class Enemy:
    def __init__(self, x, y, patrol_points=None):
        """Initialize the enemy"""
        self.x = x
        self.y = y
        self.width = ENEMY_SIZE
        self.height = ENEMY_SIZE
        self.speed = ENEMY_SPEED
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.detection_range = ENEMY_DETECTION_RANGE
        
        # AI States
        self.PATROL = "patrol"
        self.CHASE = "chase"
        self.SEARCH = "search"
        self.IDLE = "idle"
        self.current_state = self.PATROL
        
        # Patrol behavior
        self.patrol_points = patrol_points or self.generate_patrol_points()
        self.current_patrol_index = 0
        self.wait_time = 0
        self.max_wait_time = 2 * FPS  # 2 seconds in frames
        
        # Chase behavior
        self.last_known_player_pos = None
        self.chase_timer = 0
        self.max_chase_time = 10 * FPS  # 10 seconds in frames
        
        # Search behavior
        self.search_points = []
        self.current_search_point = None
        self.search_timer = 0
        self.max_search_time = 15 * FPS  # 15 seconds in frames
        
        self.load_assets()

    def load_assets(self):
        """Load enemy assets"""
        try:
            # Placeholder for enemy sprite/animation loading
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill(BLOOD_RED)
        except Exception as e:
            logging.error(f"Failed to load enemy assets: {str(e)}")
            # Fallback appearance
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill(RED)

    def generate_patrol_points(self):
        """Generate random patrol points"""
        points = []
        num_points = random.randint(3, 6)
        for _ in range(num_points):
            x = random.randint(0, SCREEN_WIDTH - self.width)
            y = random.randint(0, SCREEN_HEIGHT - self.height)
            points.append((x, y))
        return points

    def generate_search_points(self, last_known_pos):
        """Generate points to search around the last known player position"""
        points = []
        radius = ENEMY_DETECTION_RANGE
        num_points = 8
        
        for i in range(num_points):
            angle = (2 * math.pi * i) / num_points
            x = last_known_pos[0] + radius * math.cos(angle)
            y = last_known_pos[1] + radius * math.sin(angle)
            # Ensure points are within screen bounds
            x = max(0, min(x, SCREEN_WIDTH - self.width))
            y = max(0, min(y, SCREEN_HEIGHT - self.height))
            points.append((x, y))
        
        return points

    def move_towards(self, target_x, target_y):
        """Move enemy towards a target position"""
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            dx = dx / distance * self.speed
            dy = dy / distance * self.speed
            
            self.x += dx
            self.y += dy
            self.rect.x = self.x
            self.rect.y = self.y

    def can_see_player(self, player_pos, player_noise_level):
        """Check if the enemy can detect the player based on position and noise"""
        dx = player_pos[0] - self.x
        dy = player_pos[1] - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        # Base detection range increased by player noise
        current_detection_range = self.detection_range * (1 + player_noise_level / 100)
        
        return distance <= current_detection_range

    def update_patrol(self):
        """Update patrol behavior"""
        if self.wait_time > 0:
            self.wait_time -= 1
            return
            
        target = self.patrol_points[self.current_patrol_index]
        self.move_towards(target[0], target[1])
        
        # Check if reached patrol point
        distance = math.sqrt((self.x - target[0])**2 + (self.y - target[1])**2)
        if distance < self.speed:
            self.wait_time = self.max_wait_time
            self.current_patrol_index = (self.current_patrol_index + 1) % len(self.patrol_points)

    def update_chase(self, player_pos):
        """Update chase behavior"""
        if self.last_known_player_pos:
            self.move_towards(player_pos[0], player_pos[1])
            self.last_known_player_pos = player_pos
            self.chase_timer = 0
        else:
            self.chase_timer += 1
            if self.chase_timer >= self.max_chase_time:
                self.current_state = self.SEARCH
                self.search_points = self.generate_search_points(self.last_known_player_pos)
                self.current_search_point = 0

    def update_search(self):
        """Update search behavior"""
        if not self.search_points:
            self.current_state = self.PATROL
            return
            
        current_point = self.search_points[self.current_search_point]
        self.move_towards(current_point[0], current_point[1])
        
        # Check if reached search point
        distance = math.sqrt((self.x - current_point[0])**2 + (self.y - current_point[1])**2)
        if distance < self.speed:
            self.current_search_point = (self.current_search_point + 1) % len(self.search_points)
            self.search_timer += 1
            
            if self.search_timer >= self.max_search_time:
                self.current_state = self.PATROL
                self.search_timer = 0

    def update(self, player_pos, player_noise_level):
        """Update enemy state and position"""
        # Check for player detection
        if self.can_see_player(player_pos, player_noise_level):
            self.current_state = self.CHASE
            self.last_known_player_pos = player_pos
            
        # Update based on current state
        if self.current_state == self.PATROL:
            self.update_patrol()
        elif self.current_state == self.CHASE:
            self.update_chase(player_pos)
        elif self.current_state == self.SEARCH:
            self.update_search()

    def draw(self, screen):
        """Draw the enemy"""
        try:
            screen.blit(self.image, self.rect)
            
            # Draw detection radius (for debugging)
            # pygame.draw.circle(screen, RED, (int(self.x + self.width/2), int(self.y + self.height/2)), 
            #                   self.detection_range, 1)
            
        except Exception as e:
            logging.error(f"Error drawing enemy: {str(e)}")

    def get_position(self):
        """Get current enemy position"""
        return (self.x, self.y)

    def get_collision_rect(self):
        """Get enemy collision rectangle"""
        return self.rect
