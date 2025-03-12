import pygame
import logging
from settings import *
from survivor import SurvivorManager

class Player:
    def __init__(self, x, y, survivor_class=None, survivor_manager=None):
        """Initialize the player with class-specific stats"""
        self.x = x
        self.y = y
        self.width = PLAYER_SIZE
        self.height = PLAYER_SIZE
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.direction = pygame.math.Vector2()
        
        # Base stats (modificati dalle statistiche della classe)
        self.base_speed = 5
        self.base_health = 100
        self.base_stamina = 100
        self.base_stealth = 1.0
        self.base_strength = 1.0
        
        # Applica modificatori della classe se specificata
        if survivor_class and survivor_manager and survivor_class in survivor_manager.classes:
            class_stats = survivor_manager.classes[survivor_class]
            self.speed = self.base_speed * class_stats['speed']
            self.health = int(self.base_health * class_stats['health'] / 100)
            self.max_health = self.health
            self.stamina = int(self.base_stamina * class_stats['stamina'] / 100)
            self.max_stamina = self.stamina
            self.stealth = self.base_stealth * class_stats['stealth']
            self.strength = self.base_strength * class_stats['strength']
        else:
            self.speed = self.base_speed
            self.health = self.base_health
            self.max_health = self.health
            self.stamina = self.base_stamina
            self.max_stamina = self.stamina
            self.stealth = self.base_stealth
            self.strength = self.base_strength
        
        # Stati del movimento
        self.is_moving = False
        self.stamina_recovery_rate = 0.5 * self.stealth  # Più furtivo = recupero stamina più veloce
        self.running = False
        self.run_speed_multiplier = 1.6
        self.run_stamina_cost = 1 / self.stealth  # Più furtivo = meno costo stamina
        
        # Inventory
        self.inventory = []
        self.selected_item = None
        
        # Combat and interaction
        self.is_crouching = False
        self.crouch_speed_multiplier = 0.5
        self.noise_level = 0  # 0 = silent, 100 = very noisy
        
        # Experience
        self.experience_gained = 0
        
        self.load_assets()

    def load_assets(self):
        """Load player assets"""
        try:
            # Placeholder for player sprite/animation loading
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill(WHITE)
        except Exception as e:
            logging.error(f"Failed to load player assets: {str(e)}")
            # Use fallback appearance
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill(RED)

    def handle_input(self, keys):
        """Handle player input"""
        # Reset direction
        self.direction.x = 0
        self.direction.y = 0
        
        # Movement
        if keys[pygame.K_w]:
            self.direction.y = -1
        if keys[pygame.K_s]:
            self.direction.y = 1
        if keys[pygame.K_a]:
            self.direction.x = -1
        if keys[pygame.K_d]:
            self.direction.x = 1
            
        # Normalize diagonal movement
        if self.direction.magnitude() > 0:
            self.direction = self.direction.normalize()
            self.is_moving = True
        else:
            self.is_moving = False

        # Running
        self.running = keys[pygame.K_LSHIFT] and self.stamina > 0 and self.is_moving
        
        # Crouching
        self.is_crouching = keys[pygame.K_LCTRL]

    def update(self):
        """Update player state"""
        # Calculate current speed
        current_speed = self.speed
        
        if self.running:
            current_speed *= self.run_speed_multiplier
            self.stamina = max(0, self.stamina - self.run_stamina_cost)
            self.noise_level = int(80 / self.stealth)  # Più furtivo = meno rumore
        elif self.is_crouching:
            current_speed *= self.crouch_speed_multiplier
            self.noise_level = int(20 / self.stealth)
        else:
            self.noise_level = int(40 / self.stealth) if self.is_moving else 0
            
        # Update position
        self.x += self.direction.x * current_speed
        self.y += self.direction.y * current_speed
        
        # Update rectangle position
        self.rect.x = self.x
        self.rect.y = self.y
        
        # Stamina recovery when not running
        if not self.running:
            self.stamina = min(self.max_stamina, 
                             self.stamina + self.stamina_recovery_rate)

        # Keep player in bounds
        self.x = max(0, min(self.x, SCREEN_WIDTH - self.width))
        self.y = max(0, min(self.y, SCREEN_HEIGHT - self.height))

    def take_damage(self, amount):
        """Handle player taking damage"""
        actual_damage = int(amount / self.strength)  # Più forte = meno danno
        self.health = max(0, self.health - actual_damage)
        logging.info(f"Player took {actual_damage} damage. Health: {self.health}")
        return self.health <= 0

    def heal(self, amount):
        """Handle player healing"""
        self.health = min(self.max_health, self.health + amount)
        logging.info(f"Player healed {amount}. Health: {self.health}")

    def add_to_inventory(self, item):
        """Add item to inventory if there's space"""
        if len(self.inventory) < INVENTORY_CAPACITY:
            self.inventory.append(item)
            logging.info(f"Added {item} to inventory")
            return True
        logging.info("Inventory full")
        return False

    def remove_from_inventory(self, item):
        """Remove item from inventory"""
        if item in self.inventory:
            self.inventory.remove(item)
            logging.info(f"Removed {item} from inventory")
            return True
        return False

    def draw(self, screen):
        """Draw the player"""
        try:
            screen.blit(self.image, self.rect)
            
            # Draw health bar
            health_bar_width = 50
            health_bar_height = 5
            health_ratio = self.health / self.max_health
            pygame.draw.rect(screen, RED, (self.rect.x, self.rect.y - 10,
                                         health_bar_width, health_bar_height))
            pygame.draw.rect(screen, (0, 255, 0),
                           (self.rect.x, self.rect.y - 10,
                            health_bar_width * health_ratio, health_bar_height))
            
            # Draw stamina bar
            stamina_bar_width = 50
            stamina_bar_height = 5
            stamina_ratio = self.stamina / self.max_stamina
            pygame.draw.rect(screen, LIGHT_GRAY,
                           (self.rect.x, self.rect.y - 20,
                            stamina_bar_width, stamina_bar_height))
            pygame.draw.rect(screen, (0, 0, 255),
                           (self.rect.x, self.rect.y - 20,
                            stamina_bar_width * stamina_ratio, stamina_bar_height))
            
        except Exception as e:
            logging.error(f"Error drawing player: {str(e)}")

    def get_position(self):
        """Get current player position"""
        return (self.x, self.y)

    def get_noise_level(self):
        """Get current noise level"""
        return self.noise_level

    def is_alive(self):
        """Check if player is alive"""
        return self.health > 0

    def add_experience(self, amount):
        """Add experience points"""
        self.experience_gained += amount
        logging.info(f"Gained {amount} experience points. Total: {self.experience_gained}")
