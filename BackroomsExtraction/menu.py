import pygame
import logging
import random
import math
from settings import *
from survivor import SurvivorManager

class Button:
    def __init__(self, x, y, width, height, text, font_size=FONT_SIZE_MEDIUM):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font_size = font_size
        self.is_hovered = False
        self.alpha = 0  # Per l'effetto di fade
        self.hover_effect = 0  # Per l'effetto di pulsazione
        
        # Colori con valori RGB per permettere la manipolazione dell'alpha
        self.normal_color = (*DARK_GRAY, 255)
        self.hover_color = (*LIGHT_GRAY, 255)
        self.text_color = (*WHITE, 255)
        
        try:
            self.font = pygame.font.Font(None, self.font_size)
        except Exception as e:
            logging.error(f"Failed to load font: {str(e)}")
            self.font = pygame.font.SysFont('arial', self.font_size)

    def update(self, mouse_pos):
        """Update button state based on mouse position"""
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        # Aggiorna effetto hover
        if self.is_hovered:
            self.hover_effect = min(1.0, self.hover_effect + 0.1)
        else:
            self.hover_effect = max(0.0, self.hover_effect - 0.1)
            
        # Aggiorna fade
        self.alpha = min(255, self.alpha + 10)

    def draw(self, screen):
        """Draw the button with effects"""
        try:
            # Crea superficie per il bottone con alpha
            button_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            
            # Calcola colore corrente basato su hover
            current_color = [
                int(self.normal_color[i] + (self.hover_color[i] - self.normal_color[i]) * self.hover_effect)
                for i in range(3)
            ]
            current_color.append(self.alpha)  # Aggiungi alpha
            
            # Disegna il bottone con effetto pulsante quando hover
            hover_expansion = math.sin(pygame.time.get_ticks() * 0.005) * 5 * self.hover_effect
            hover_rect = self.rect.inflate(hover_expansion, hover_expansion)
            
            # Disegna il bordo del bottone
            pygame.draw.rect(button_surface, current_color, 
                           (0, 0, self.rect.width, self.rect.height), 
                           border_radius=10)
            
            # Aggiungi effetto gradiente
            gradient_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            for i in range(self.rect.height):
                alpha = int(128 + (i / self.rect.height) * 127)
                pygame.draw.line(gradient_surface, (*WHITE, alpha), 
                               (0, i), (self.rect.width, i))
            button_surface.blit(gradient_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            
            # Renderizza il testo
            text_surface = self.font.render(self.text, True, self.text_color)
            text_rect = text_surface.get_rect(center=button_surface.get_rect().center)
            button_surface.blit(text_surface, text_rect)
            
            # Disegna il bottone sullo schermo
            screen.blit(button_surface, self.rect)
            
        except Exception as e:
            logging.error(f"Error drawing button: {str(e)}")

class Menu:
    def __init__(self):
        self.state = "main"  # main, class_select, level_select, credits
        self.buttons = {}
        self.background_alpha = 0
        self.title_alpha = 0
        
        # Survivor manager per la selezione della classe
        self.survivor_manager = SurvivorManager()
        self.selected_class = None
        self.selected_level = None
        
        # Effetti particellari per lo sfondo
        self.particles = []
        
        try:
            self.title_font = pygame.font.Font(None, FONT_SIZE_LARGE * 2)
            self.subtitle_font = pygame.font.Font(None, FONT_SIZE_MEDIUM)
            self.description_font = pygame.font.Font(None, FONT_SIZE_SMALL)
        except Exception as e:
            logging.error(f"Failed to load fonts: {str(e)}")
            self.title_font = pygame.font.SysFont('arial', FONT_SIZE_LARGE * 2)
            self.subtitle_font = pygame.font.SysFont('arial', FONT_SIZE_MEDIUM)
            self.description_font = pygame.font.SysFont('arial', FONT_SIZE_SMALL)
            
        self.setup_menu()
        self.generate_particles()

    def setup_menu(self):
        """Setup menu buttons for different states"""
        button_width = 200
        button_height = 50
        start_y = SCREEN_HEIGHT // 2
        
        # Main Menu
        self.buttons["main"] = [
            Button(SCREEN_WIDTH//2 - button_width//2, start_y, 
                  button_width, button_height, "Start Game"),
            Button(SCREEN_WIDTH//2 - button_width//2, start_y + 70, 
                  button_width, button_height, "Credits"),
            Button(SCREEN_WIDTH//2 - button_width//2, start_y + 140, 
                  button_width, button_height, "Exit")
        ]
        
        # Class Selection Menu
        class_y = SCREEN_HEIGHT // 3
        self.buttons["class_select"] = []
        for i, class_name in enumerate(self.survivor_manager.classes.keys()):
            self.buttons["class_select"].append(
                Button(SCREEN_WIDTH//2 - button_width//2, class_y + i * 70,
                      button_width, button_height, class_name)
            )
        # Add back button
        self.buttons["class_select"].append(
            Button(SCREEN_WIDTH//2 - button_width//2, SCREEN_HEIGHT - 100,
                  button_width, button_height, "Back")
        )
        
        # Level Selection Menu
        level_y = SCREEN_HEIGHT // 3
        self.buttons["level_select"] = []
        for level_id, level_data in BACKROOMS_LEVELS.items():
            self.buttons["level_select"].append(
                Button(SCREEN_WIDTH//2 - button_width//2, 
                      level_y + level_id * 70,
                      button_width, button_height, 
                      f"Level {level_id}")
            )
        # Add back button
        self.buttons["level_select"].append(
            Button(SCREEN_WIDTH//2 - button_width//2, SCREEN_HEIGHT - 100,
                  button_width, button_height, "Back")
        )
        
        # Credits Menu
        self.buttons["credits"] = [
            Button(SCREEN_WIDTH//2 - button_width//2, SCREEN_HEIGHT - 100,
                  button_width, button_height, "Back")
        ]

    def draw_class_info(self, screen, class_name):
        """Draw class information"""
        if class_name in self.survivor_manager.classes:
            stats = self.survivor_manager.classes[class_name]
            desc = stats['description']
            
            # Draw description
            desc_surface = self.description_font.render(desc, True, WHITE)
            desc_rect = desc_surface.get_rect(
                center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 150))
            screen.blit(desc_surface, desc_rect)
            
            # Draw stats
            stat_y = SCREEN_HEIGHT - 120
            for stat, value in stats.items():
                if stat != 'description':
                    stat_text = f"{stat.capitalize()}: {value}"
                    stat_surface = self.description_font.render(stat_text, 
                                                              True, LIGHT_GRAY)
                    stat_rect = stat_surface.get_rect(
                        center=(SCREEN_WIDTH//2, stat_y))
                    screen.blit(stat_surface, stat_rect)
                    stat_y += 20

    def draw_level_info(self, screen, level_id):
        """Draw level information"""
        if level_id in BACKROOMS_LEVELS:
            level_data = BACKROOMS_LEVELS[level_id]
            
            # Draw description
            desc_surface = self.description_font.render(
                level_data['description'], True, WHITE)
            desc_rect = desc_surface.get_rect(
                center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 150))
            screen.blit(desc_surface, desc_rect)
            
            # Draw difficulty
            diff_surface = self.description_font.render(
                f"Difficulty: {level_data['difficulty']}", True, 
                GREEN if level_data['difficulty'] == 'Normal' else RED)
            diff_rect = diff_surface.get_rect(
                center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 120))
            screen.blit(diff_surface, diff_rect)

    def generate_particles(self):
        """Generate background particles"""
        for _ in range(50):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            speed = random.uniform(0.5, 2.0)
            size = random.randint(1, 3)
            self.particles.append({
                'pos': [x, y],
                'speed': speed,
                'size': size,
                'alpha': random.randint(50, 200)
            })

    def update_particles(self):
        """Update particle positions and properties"""
        for particle in self.particles:
            particle['pos'][1] += particle['speed']
            if particle['pos'][1] > SCREEN_HEIGHT:
                particle['pos'][1] = 0
                particle['pos'][0] = random.randint(0, SCREEN_WIDTH)

    def draw_particles(self, screen):
        """Draw background particles"""
        particle_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for particle in self.particles:
            pygame.draw.circle(particle_surface, 
                             (255, 255, 255, particle['alpha']),
                             (int(particle['pos'][0]), int(particle['pos'][1])),
                             particle['size'])
        screen.blit(particle_surface, (0, 0))

    def update(self, mouse_pos):
        """Update menu state"""
        # Aggiorna fade degli elementi
        self.background_alpha = min(200, self.background_alpha + 5)
        self.title_alpha = min(255, self.title_alpha + 5)
        
        # Aggiorna particelle
        self.update_particles()
        
        # Aggiorna bottoni dello stato corrente
        for button in self.buttons[self.state]:
            button.update(mouse_pos)

    def handle_event(self, event):
        """Handle menu events"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                for button in self.buttons[self.state]:
                    if button.rect.collidepoint(event.pos):
                        if self.state == "main":
                            if button.text == "Start Game":
                                self.state = "class_select"
                            elif button.text == "Credits":
                                self.state = "credits"
                            elif button.text == "Exit":
                                return "exit"
                        elif self.state == "class_select":
                            if button.text == "Back":
                                self.state = "main"
                            else:
                                self.selected_class = button.text
                                self.survivor_manager.create_survivor(button.text)
                                self.state = "level_select"
                        elif self.state == "level_select":
                            if button.text == "Back":
                                self.state = "class_select"
                            else:
                                level_num = int(button.text.split()[-1])
                                self.selected_level = level_num
                                return "start_game"
                        elif self.state == "credits":
                            if button.text == "Back":
                                self.state = "main"
        return None

    def draw(self, screen):
        """Draw the menu"""
        try:
            # Disegna sfondo scuro con fade
            background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            background.fill(BLACK)
            background.set_alpha(self.background_alpha)
            screen.blit(background, (0, 0))
            
            # Disegna particelle
            self.draw_particles(screen)
            
            # Disegna titolo con effetto fade
            title_text = self.title_font.render("Backrooms Extraction", True, WHITE)
            title_text.set_alpha(self.title_alpha)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 150))
            screen.blit(title_text, title_rect)
            
            # Disegna sottotitolo specifico per ogni stato
            if self.state == "main":
                subtitle_text = self.subtitle_font.render(
                    "Survive. Extract. Escape.", True, LIGHT_GRAY)
                subtitle_rect = subtitle_text.get_rect(
                    center=(SCREEN_WIDTH//2, 220))
                screen.blit(subtitle_text, subtitle_rect)
            elif self.state == "class_select":
                subtitle_text = self.subtitle_font.render(
                    "Choose Your Class", True, LIGHT_GRAY)
                subtitle_rect = subtitle_text.get_rect(
                    center=(SCREEN_WIDTH//2, 220))
                screen.blit(subtitle_text, subtitle_rect)
            elif self.state == "level_select":
                subtitle_text = self.subtitle_font.render(
                    "Select Backrooms Level", True, LIGHT_GRAY)
                subtitle_rect = subtitle_text.get_rect(
                    center=(SCREEN_WIDTH//2, 220))
                screen.blit(subtitle_text, subtitle_rect)
            
            # Disegna i bottoni dello stato corrente
            for button in self.buttons[self.state]:
                button.draw(screen)
                if self.state == "class_select" and button.is_hovered:
                    self.draw_class_info(screen, button.text)
                elif self.state == "level_select" and button.is_hovered:
                    try:
                        level_num = int(button.text.split()[-1])
                        self.draw_level_info(screen, level_num)
                    except ValueError:
                        pass
            
            # Disegna i credits se necessario
            if self.state == "credits":
                credits_text = [
                    "Backrooms Extraction",
                    "A Horror Extraction Game",
                    "",
                    "Created by: Your Name",
                    "Graphics: Procedurally Generated",
                    "",
                    "Thanks for playing!"
                ]
                
                y = 150
                for line in credits_text:
                    text = self.subtitle_font.render(line, True, WHITE)
                    rect = text.get_rect(center=(SCREEN_WIDTH//2, y))
                    screen.blit(text, rect)
                    y += 40
                    
        except Exception as e:
            logging.error(f"Error drawing menu: {str(e)}")
