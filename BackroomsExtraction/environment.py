import pygame
import random
import logging
from settings import *

class Room:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.connected_rooms = []
        self.doors = []  # (x, y, width, height) for each door
        self.lights = []  # [(x, y, intensity, flicker_rate)]
        self.has_extraction_point = False
        
    def intersects(self, other_room):
        """Check if this room intersects with another room"""
        return self.rect.inflate(20, 20).colliderect(other_room.rect)
        
    def connect_room(self, other_room):
        """Create a connection (door) between two rooms"""
        if other_room not in self.connected_rooms:
            self.connected_rooms.append(other_room)
            other_room.connected_rooms.append(self)
            
            # Create door
            if self.rect.x < other_room.rect.x:  # Rooms are side by side
                door_x = other_room.rect.x
                door_y = max(self.rect.y, other_room.rect.y) + min(self.rect.height, other_room.rect.height) // 2
                door = pygame.Rect(door_x - 5, door_y - 15, 10, 30)
            else:  # Rooms are top and bottom
                door_x = max(self.rect.x, other_room.rect.x) + min(self.rect.width, other_room.rect.width) // 2
                door_y = other_room.rect.y
                door = pygame.Rect(door_x - 15, door_y - 5, 30, 10)
                
            self.doors.append(door)
            other_room.doors.append(door)

class Environment:
    def __init__(self):
        self.rooms = []
        self.corridors = []  # [(start_pos, end_pos, width)]
        self.extraction_points = []  # [(x, y, active)]
        self.current_level = 1
        
        # Lighting
        self.ambient_light = 0.2  # Base ambient light level (0-1)
        self.light_surfaces = {}  # Cache for light surfaces
        self.flickering_lights = []  # [(x, y, intensity, time)]
        
        # Environment effects
        self.particles = []  # [(pos, velocity, lifetime)] for dust/atmosphere
        self.wall_texture = None
        self.floor_texture = None
        
        self.load_assets()
        self.generate_level()

    def load_assets(self):
        """Load environment textures and assets"""
        try:
            # Create basic textures for walls and floor
            self.wall_texture = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.wall_texture.fill(DARK_GRAY)
            # Add some noise to the wall texture
            for _ in range(100):
                x = random.randint(0, TILE_SIZE-1)
                y = random.randint(0, TILE_SIZE-1)
                color = random.randint(15, 25)
                pygame.draw.circle(self.wall_texture, (color, color, color), (x, y), 1)
                
            self.floor_texture = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.floor_texture.fill((30, 30, 30))
            # Add some noise to the floor texture
            for _ in range(50):
                x = random.randint(0, TILE_SIZE-1)
                y = random.randint(0, TILE_SIZE-1)
                color = random.randint(25, 35)
                pygame.draw.circle(self.floor_texture, (color, color, color), (x, y), 1)
                
        except Exception as e:
            logging.error(f"Failed to load environment assets: {str(e)}")
            # Create fallback textures
            self.wall_texture = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.wall_texture.fill(DARK_GRAY)
            self.floor_texture = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.floor_texture.fill((30, 30, 30))

    def generate_level(self, map_size, min_rooms, max_rooms, num_extraction_points, ambient_light):
        """Generate a new level with rooms and corridors"""
        self.rooms = []
        self.corridors = []
        self.extraction_points = []
        self.ambient_light = ambient_light
        
        map_width, map_height = map_size
        
        # Generate rooms
        attempts = 0
        num_rooms = random.randint(min_rooms, max_rooms)
        
        while len(self.rooms) < num_rooms and attempts < 100:
            # Generate room with random size
            width = random.randint(5, 10) * TILE_SIZE
            height = random.randint(5, 10) * TILE_SIZE
            x = random.randint(0, map_width * TILE_SIZE - width)
            y = random.randint(0, map_height * TILE_SIZE - height)
            
            new_room = Room(x, y, width, height)
            
            # Check if room overlaps with existing rooms
            can_place = True
            for room in self.rooms:
                if new_room.intersects(room):
                    can_place = False
                    break
                    
            if can_place:
                # Add random lights to the room
                num_lights = random.randint(1, 3)
                for _ in range(num_lights):
                    light_x = random.randint(new_room.rect.left + 50, new_room.rect.right - 50)
                    light_y = random.randint(new_room.rect.top + 50, new_room.rect.bottom - 50)
                    intensity = random.uniform(0.5, 1.0)
                    # Più buio = più flickering
                    flicker_rate = random.uniform(0.1, 0.4) * (1 - ambient_light)
                    new_room.lights.append((light_x, light_y, intensity, flicker_rate))
                
                self.rooms.append(new_room)
                
            attempts += 1
            
        # Connect rooms
        for i, room in enumerate(self.rooms):
            if i > 0:
                closest_room = min([r for r in self.rooms[:i]], 
                                 key=lambda r: abs(r.rect.centerx - room.rect.centerx) + 
                                             abs(r.rect.centery - room.rect.centery))
                room.connect_room(closest_room)
                
                # Create corridor
                start_pos = (room.rect.centerx, room.rect.centery)
                end_pos = (closest_room.rect.centerx, closest_room.rect.centery)
                self.corridors.append((start_pos, end_pos, TILE_SIZE))
                
        # Add extraction points
        possible_rooms = self.rooms.copy()
        random.shuffle(possible_rooms)
        
        for i in range(num_extraction_points):
            if possible_rooms:
                room = possible_rooms.pop()
                x = random.randint(room.rect.left + 50, room.rect.right - 50)
                y = random.randint(room.rect.top + 50, room.rect.bottom - 50)
                self.extraction_points.append((x, y, True))
                room.has_extraction_point = True
                
        logging.info(f"Generated level with {len(self.rooms)} rooms and {num_extraction_points} extraction points")

    def update_lighting(self):
        """Update dynamic lighting effects"""
        # Update flickering lights
        for room in self.rooms:
            for i, (x, y, intensity, flicker_rate) in enumerate(room.lights):
                if random.random() < flicker_rate:
                    room.lights[i] = (x, y, intensity * random.uniform(0.5, 1.0), flicker_rate)

    def create_light_surface(self, radius, intensity):
        """Create a light surface with falloff"""
        key = (radius, intensity)
        if key in self.light_surfaces:
            return self.light_surfaces[key]
            
        surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for x in range(radius * 2):
            for y in range(radius * 2):
                distance = math.sqrt((x - radius) ** 2 + (y - radius) ** 2)
                if distance < radius:
                    alpha = int(255 * (1 - distance/radius) * intensity)
                    surface.set_at((x, y), (255, 255, 255, alpha))
                    
        self.light_surfaces[key] = surface
        return surface

    def draw(self, screen, camera_pos=(0, 0)):
        """Draw the environment"""
        try:
            # Create base surface for the level
            level_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            level_surface.fill(BLACK)
            
            # Draw rooms
            for room in self.rooms:
                # Draw floor
                for x in range(room.rect.left, room.rect.right, TILE_SIZE):
                    for y in range(room.rect.top, room.rect.bottom, TILE_SIZE):
                        level_surface.blit(self.floor_texture, 
                                       (x - camera_pos[0], y - camera_pos[1]))
                
                # Draw walls with texture
                wall_rect = room.rect.move(-camera_pos[0], -camera_pos[1])
                pygame.draw.rect(level_surface, DARK_GRAY, wall_rect, 2)
                
                # Draw doors with depth effect
                for door in room.doors:
                    door_rect = door.move(-camera_pos[0], -camera_pos[1])
                    pygame.draw.rect(level_surface, (40, 40, 40), door_rect)
                    # Aggiunge ombra alla porta
                    pygame.draw.rect(level_surface, (20, 20, 20), door_rect, 2)
                    
            # Draw corridors with depth effect
            for start, end, width in self.corridors:
                start_pos = (start[0] - camera_pos[0], start[1] - camera_pos[1])
                end_pos = (end[0] - camera_pos[0], end[1] - camera_pos[1])
                # Corridoio principale
                pygame.draw.line(level_surface, (25, 25, 25),
                               start_pos, end_pos, width)
                # Bordi del corridoio per effetto profondità
                pygame.draw.line(level_surface, (35, 35, 35),
                               start_pos, end_pos, width-2)
                
            # Draw extraction points with glow effect
            for x, y, active in self.extraction_points:
                pos = (x - camera_pos[0], y - camera_pos[1])
                if active:
                    # Glow effect
                    for radius in range(25, 15, -5):
                        alpha = int(100 * (radius/25))
                        glow_surface = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                        pygame.draw.circle(glow_surface, (*GREEN, alpha), 
                                        (radius, radius), radius)
                        level_surface.blit(glow_surface, 
                                       (pos[0]-radius, pos[1]-radius))
                    # Central point
                    pygame.draw.circle(level_surface, GREEN, pos, 15)
                else:
                    pygame.draw.circle(level_surface, (150, 0, 0), pos, 15)
                
            # Apply ambient lighting and fog
            light_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            fog_alpha = int(255 * (1 - self.ambient_light))
            light_surface.fill((0, 0, 0, fog_alpha))
            
            # Draw room lights with flickering
            for room in self.rooms:
                for x, y, intensity, flicker_rate in room.lights:
                    # Applica flickering
                    current_intensity = intensity * (1 - random.uniform(0, flicker_rate))
                    light = self.create_light_surface(LIGHT_RADIUS, current_intensity)
                    pos = (x - camera_pos[0] - LIGHT_RADIUS,
                          y - camera_pos[1] - LIGHT_RADIUS)
                    light_surface.blit(light, pos, special_flags=pygame.BLEND_RGBA_SUB)
            
            # Combine surfaces
            screen.blit(level_surface, (0, 0))
            screen.blit(light_surface, (0, 0))
            
        except Exception as e:
            logging.error(f"Error drawing environment: {str(e)}")

    def get_room_at_position(self, pos):
        """Get the room at a given position"""
        for room in self.rooms:
            if room.rect.collidepoint(pos):
                return room
        return None

    def check_collision(self, rect):
        """Check if a rectangle collides with walls"""
        # Check room walls
        for room in self.rooms:
            if rect.colliderect(room.rect):
                return True
        return False

    def is_extraction_point(self, pos):
        """Check if a position is an extraction point"""
        for x, y, active in self.extraction_points:
            if active and math.sqrt((pos[0] - x)**2 + (pos[1] - y)**2) < 20:
                return True
        return False
