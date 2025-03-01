import pygame
import sys
from word_ladder_game import WordLadderGame
from typing import Optional, Tuple, List
import time
import math
import threading
from collections import deque
import random
import networkx as nx
import numpy as np

class WordLadderGUI:
    # Modern color scheme with blue and white
    PRIMARY = (63, 81, 181)       # Material Indigo
    PRIMARY_LIGHT = (92, 107, 192)
    PRIMARY_DARK = (48, 63, 159)
    SECONDARY = PRIMARY           # Changed to primary blue
    SECONDARY_LIGHT = PRIMARY_LIGHT
    ACCENT = PRIMARY             # Changed to primary blue
    SUCCESS = PRIMARY            # Changed to primary blue
    ERROR = PRIMARY_DARK         # Changed to darker blue
    WARNING = PRIMARY            # Changed to primary blue
    WHITE = (255, 255, 255)
    BLACK = (33, 33, 33)
    GRAY = (158, 158, 158)
    LIGHT_GRAY = (238, 238, 238)
    BACKGROUND = WHITE           # Changed to white
    
    # Button states
    BUTTON_NORMAL = PRIMARY
    BUTTON_HOVER = PRIMARY_LIGHT
    BUTTON_SELECTED = PRIMARY_DARK
    
    # Loading animation settings
    LOADING_DOTS = 12
    LOADING_RADIUS = 25
    LOADING_DOT_RADIUS = 3
    LOADING_SPEED = 0.1
    LOADING_TEXT = ["Finding words", "Finding words.", "Finding words..", "Finding words..."]
    
    def __init__(self, width=800, height=600):
        """Initialize the GUI with the given width and height."""
        # Initialize pygame
        pygame.init()
        pygame.display.set_caption("Word Ladder Game")
        
        # Set up the screen
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        
        # Set up the clock
        self.clock = pygame.time.Clock()
        
        # Set up fonts
        self.title_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.medium_font = pygame.font.SysFont("Arial", 32, bold=True)
        self.large_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.font = pygame.font.SysFont("Arial", 24)
        self.small_font = pygame.font.SysFont("Arial", 18)
        self.tiny_font = pygame.font.SysFont("Arial", 14)
        
        # Set up the game
        self.game = WordLadderGame()
        
        # Set up the current screen
        self.current_screen = "difficulty_select"
        
        # Set up the input box
        self.input_box = pygame.Rect(0, 0, 0, 0)  # Will be positioned later
        self.input_text = ""
        self.input_active = False
        
        # Set up the message
        self.message = ""
        self.message_timer = 0
        self.message_duration = 3000  # 3 seconds
        
        # Set up the difficulty buttons
        self.difficulty_buttons = {}
        self.selected_difficulty = "beginner"
        
        # Set up the word list
        self.word_list = []
        self.word_list_rects = []
        self.suggested_words = []
        
        # Set up the hint buttons
        self.hint_buttons = {}
        self.hint_button_rect = pygame.Rect(0, 0, 0, 0)  # Will be positioned later
        self.selected_algorithm = "a_star"
        
        # Set up the loading animation
        self.loading_angle = 0
        self.loading_text_index = 0
        self.loading_text_timer = 0
        self.is_loading = False
        self.loading_thread = None
        
        # Set up the graph view
        self.graph_nodes = set()
        self.graph_edges = set()
        self.node_positions = {}
        self.node_colors = {}
        self.edge_colors = {}
        self.edge_widths = {}
        self.edge_paths = {}
        self.selected_node = None
        self.graph_paths = {"a_star": [], "greedy": [], "uniform": [], "user": []}
        self.graph_zoom = 1.0
        self.graph_offset = [0, 0]
        self.dragging = False
        self.dragging_node = None
        self.drag_start = None
        self.drag_offset = (0, 0)
        self.heuristic_values = {}
        self.show_node_labels = True
        self.show_heuristic_values = True
        
        # Set up scrolling for paths screen
        self.scroll_y = 0
        self.max_scroll = 0
        self.scroll_speed = 30
        self.scrollbar_active = False
        self.scroll_start_y = 0
        self.scroll_start_value = 0
        
        # Store the final score when game ends
        self.final_score = 0
    
    def draw_text(self, text: str, pos: Tuple[int, int], font=None, color=None, align="center") -> None:
        """Draw text on the screen with alignment options."""
        if font is None:
            font = self.font
        if color is None:
            color = self.BLACK
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        
        if align == "center":
            text_rect.center = pos
        elif align == "left":
            text_rect.midleft = pos
        elif align == "right":
            text_rect.midright = pos
            
        self.screen.blit(text_surface, text_rect)
    
    def draw_gradient_rect(self, surface: pygame.Surface, color_start: tuple, 
                           color_end: tuple, rect: pygame.Rect) -> None:
        """Draw a rectangle with a vertical gradient from color_start to color_end."""
        # Create a surface for the gradient
        gradient_surface = pygame.Surface((rect.width, rect.height))
        
        # Calculate color steps
        steps = rect.height
        for y in range(steps):
            # Calculate the color for this line
            ratio = y / float(steps)
            color = (
                int(color_start[0] * (1 - ratio) + color_end[0] * ratio),
                int(color_start[1] * (1 - ratio) + color_end[1] * ratio),
                int(color_start[2] * (1 - ratio) + color_end[2] * ratio)
            )
            # Draw the line
            pygame.draw.line(gradient_surface, color, (0, y), (rect.width, y))
        
        # Set alpha if colors have alpha channel
        if len(color_start) > 3 and len(color_end) > 3:
            gradient_surface.set_alpha(
                int(color_start[3] * (1 - 0.5) + color_end[3] * 0.5))
        
        # Draw the gradient surface
        surface.blit(gradient_surface, rect)
        
        # Draw rounded corners if specified
        if hasattr(rect, 'border_radius'):
            pygame.draw.rect(surface, color_end, rect, 
                           border_radius=rect.border_radius)
    
    def draw_rounded_rect(self, surface, color, rect, radius=15, border=0, gradient=False, gradient_color=None):
        """Draw a rounded rectangle with optional gradient."""
        rect = pygame.Rect(rect)
        
        if gradient and gradient_color:
            # Draw gradient background
            self.draw_gradient_rect(surface, color, gradient_color, rect)
        else:
            # Draw solid background
            pygame.draw.rect(surface, color, rect, border_radius=radius)
        
        if border > 0:
            pygame.draw.rect(surface, color, rect, border, border_radius=radius)
    
    def draw_button(self, text: str, rect: pygame.Rect, color: Tuple[int, int, int], selected: bool = False, disabled: bool = False) -> None:
        """Draw a modern button with gradient and hover effects."""
        mouse_pos = pygame.mouse.get_pos()
        
        # Determine button colors
        if disabled:
            main_color = self.GRAY
            gradient_color = self.LIGHT_GRAY
        elif selected:
            main_color = self.PRIMARY_DARK
            gradient_color = self.PRIMARY
        elif rect.collidepoint(mouse_pos):
            main_color = self.PRIMARY
            gradient_color = self.PRIMARY_LIGHT
        else:
            main_color = color
            gradient_color = self.PRIMARY_LIGHT
        
        # Draw button shadow
        shadow_rect = rect.copy()
        shadow_rect.y += 2
        pygame.draw.rect(self.screen, (0, 0, 0, 50), shadow_rect, border_radius=15)
        
        # Draw button with gradient
        self.draw_rounded_rect(self.screen, main_color, rect, radius=15, gradient=True, gradient_color=gradient_color)
        
        # Draw selection indicator
        if selected:
            self.draw_rounded_rect(self.screen, self.ACCENT, rect, border=2, radius=15)
        
        # Draw text with shadow
        shadow_surface = self.font.render(text, True, (0, 0, 0, 128))
        text_surface = self.font.render(text, True, self.WHITE)
        
        # Position text and shadow
        text_rect = text_surface.get_rect(center=rect.center)
        shadow_rect = shadow_surface.get_rect(center=(rect.centerx + 1, rect.centery + 1))
        
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(text_surface, text_rect)
    
    def draw_input_box(self, rect: pygame.Rect, text: str, active: bool) -> None:
        """Draw a modern input box with shadow and glow effects."""
        # Draw shadow
        shadow_rect = rect.copy()
        shadow_rect.y += 2
        pygame.draw.rect(self.screen, (0, 0, 0, 30), shadow_rect, border_radius=15)
        
        # Draw background
        pygame.draw.rect(self.screen, self.WHITE, rect, border_radius=15)
        
        # Draw glow effect when active
        if active:
            glow_rect = rect.copy()
            glow_rect.inflate_ip(4, 4)
            pygame.draw.rect(self.screen, (*self.PRIMARY, 50), glow_rect, border_radius=15)
        
        # Draw border
        border_color = self.PRIMARY if active else self.GRAY
        pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=15)
        
        # Draw text
        if text:
            text_surface = self.font.render(text, True, self.BLACK)
            text_rect = text_surface.get_rect(midleft=(rect.left + 15, rect.centery))
            self.screen.blit(text_surface, text_rect)
        
        # Draw cursor if active
        if active and time.time() % 1 > 0.5:
            cursor_x = rect.left + 15 + (self.font.size(text)[0] if text else 0)
            cursor_y = rect.centery - 12
            pygame.draw.line(self.screen, self.PRIMARY,
                            (cursor_x, cursor_y),
                            (cursor_x, cursor_y + 24), 2)
    
    def draw_difficulty_select_screen(self) -> None:
        """Draw the difficulty selection screen with modern UI."""
        # Draw background with subtle gradient
        self.screen.fill(self.WHITE)
        header_rect = pygame.Rect(0, 0, self.width, 150)
        self.draw_gradient_rect(self.screen, self.PRIMARY, self.PRIMARY_LIGHT, header_rect)
        
        # Draw title with shadow
        title = "Word Ladder Game"
        title_y = 75
        
        # Draw title shadow
        shadow_surface = self.title_font.render(title, True, (0, 0, 0, 60))
        shadow_rect = shadow_surface.get_rect(center=(self.width // 2 + 2, title_y + 2))
        self.screen.blit(shadow_surface, shadow_rect)
        
        # Draw main title
        title_surface = self.title_font.render(title, True, self.WHITE)
        title_rect = title_surface.get_rect(center=(self.width // 2, title_y))
        self.screen.blit(title_surface, title_rect)
        
        # Draw subtitle with modern styling
        subtitle_y = 180
        subtitle = "Select Difficulty"
        subtitle_surface = self.font.render(subtitle, True, self.PRIMARY)
        subtitle_rect = subtitle_surface.get_rect(center=(self.width // 2, subtitle_y))
        self.screen.blit(subtitle_surface, subtitle_rect)
        
        # Draw difficulty buttons with modern styling
        button_width = 250  # Increased width
        button_height = 50  # Reduced height for better spacing
        button_spacing = 20  # Reduced spacing
        start_y = subtitle_y + 40  # Moved buttons up
        
        # Update button positions
        self.difficulty_buttons = {
            "beginner": pygame.Rect((self.width - button_width) // 2, start_y, 
                                  button_width, button_height),
            "advanced": pygame.Rect((self.width - button_width) // 2, 
                                  start_y + button_height + button_spacing, 
                                  button_width, button_height),
            "challenge": pygame.Rect((self.width - button_width) // 2, 
                                   start_y + 2 * (button_height + button_spacing), 
                                   button_width, button_height)
        }
        
        button_icons = {
            "beginner": "🎯",
            "advanced": "⚡",
            "challenge": "🔥"
        }
        
        for difficulty, rect in self.difficulty_buttons.items():
            mouse_pos = pygame.mouse.get_pos()
            is_hovered = rect.collidepoint(mouse_pos)
            is_selected = difficulty == self.selected_difficulty
            
            # Draw button shadow
            shadow_rect = rect.copy()
            shadow_rect.y += 4
            pygame.draw.rect(self.screen, (0, 0, 0, 30), shadow_rect, border_radius=15)
            
            # Draw button background with gradient
            if is_selected:
                self.draw_rounded_rect(self.screen, self.PRIMARY_DARK, rect, radius=15, 
                                     gradient=True, gradient_color=self.PRIMARY)
                pygame.draw.rect(self.screen, self.PRIMARY_LIGHT, rect, 3, border_radius=15)
            elif is_hovered:
                self.draw_rounded_rect(self.screen, self.PRIMARY, rect, radius=15, 
                                     gradient=True, gradient_color=self.PRIMARY_LIGHT)
            else:
                self.draw_rounded_rect(self.screen, self.PRIMARY_LIGHT, rect, radius=15)
            
            # Draw button text with icon
            text = f"{button_icons[difficulty]} {difficulty.capitalize()}"
            text_surface = self.font.render(text, True, self.WHITE)
            text_rect = text_surface.get_rect(center=rect.center)
            
            # Add slight vertical offset when hovered
            if is_hovered and not is_selected:
                text_rect.y -= 2
            
            # Draw text shadow
            shadow_surface = self.font.render(text, True, (0, 0, 0, 50))
            shadow_rect = shadow_surface.get_rect(center=(text_rect.centerx + 1, text_rect.centery + 1))
            self.screen.blit(shadow_surface, shadow_rect)
            self.screen.blit(text_surface, text_rect)
        
        # Draw message box if there's a message
        if self.message:
            message_rect = pygame.Rect(50, self.height - 60, self.width - 100, 40)
            self.draw_gradient_rect(self.screen, self.WHITE, (245, 245, 255), message_rect)
            pygame.draw.rect(self.screen, self.PRIMARY, message_rect, 2, border_radius=10)
            self.draw_text(self.message, message_rect.center, color=self.PRIMARY)
    
    def handle_difficulty_select_input(self, event: pygame.event.Event) -> None:
        """Handle input on the difficulty selection screen."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check if any difficulty button was clicked
            for difficulty, rect in self.difficulty_buttons.items():
                if rect.collidepoint(event.pos):
                    self.selected_difficulty = difficulty
                    
                    # If the user clicks the same difficulty again, proceed to setup
                    if difficulty == self.selected_difficulty:
                        self.current_screen = "setup"
                        self.input_text = ""
                        self.message = ""
                        self.start_word = ""
                        self.target_word = ""
                        
                        # Play button sound if available
                        if hasattr(self, 'button_sound') and self.button_sound:
                            self.button_sound.play()
                    
                    return
    
    def draw_loading_animation(self, center_pos: Tuple[int, int]) -> None:
        """Draw an improved loading animation with dots."""
        current_time = time.time()
        
        # Update loading text
        if current_time - self.loading_text_timer >= 0.5:
            self.loading_text_index = (self.loading_text_index + 1) % len(self.LOADING_TEXT)
            self.loading_text_timer = current_time
        
        # Draw loading text
        loading_text = self.LOADING_TEXT[self.loading_text_index]
        text_surface = self.font.render(loading_text, True, self.PRIMARY)
        text_rect = text_surface.get_rect(center=(center_pos[0], center_pos[1] - 40))
        self.screen.blit(text_surface, text_rect)
        
        # Draw spinning dots
        for i in range(self.LOADING_DOTS):
            angle = self.loading_angle + (i * 360 / self.LOADING_DOTS)
            rad = math.radians(angle)
            
            # Calculate position
            x = center_pos[0] + math.cos(rad) * self.LOADING_RADIUS
            y = center_pos[1] + math.sin(rad) * self.LOADING_RADIUS
            
            # Calculate color alpha (fade effect)
            alpha = int(255 * (1 - (i / self.LOADING_DOTS)))
            dot_color = (*self.PRIMARY[:3], alpha)
            
            # Draw dot
            pygame.draw.circle(self.screen, dot_color, (int(x), int(y)), self.LOADING_DOT_RADIUS)
        
        # Update rotation
        self.loading_angle = (self.loading_angle + 5) % 360
        
        # Draw search progress message
        progress_text = "Searching through word combinations..."
        progress_surface = self.small_font.render(progress_text, True, self.GRAY)
        progress_rect = progress_surface.get_rect(center=(center_pos[0], center_pos[1] + 40))
        self.screen.blit(progress_surface, progress_rect)

    def suggest_words_async(self) -> None:
        """Asynchronously get word suggestions."""
        def worker():
            try:
                if not self.start_word:
                    # Get a random start word
                    word_length = (3 if self.selected_difficulty == "beginner" 
                                 else 5 if self.selected_difficulty == "advanced" 
                                 else 6)
                    start_word = self.game.get_random_word(word_length)
                    if start_word:
                        # Don't set self.start_word yet, just show it in the input box
                        # The user will need to press Enter to confirm
                        self.input_text = start_word  # Show the word in input box
                        self.message = f"Suggested start word: '{start_word}'. Press Enter to confirm or type a different word."
                    else:
                        self.message = "Could not find a valid start word. Try a different difficulty."
                else:
                    # Find a valid target word
                    start_word, target_word = self.game.suggest_word_pair(self.selected_difficulty)
                    if target_word and target_word != self.start_word:
                        self.input_text = target_word  # Show the word in input box
                        self.message = f"Suggested target word: '{target_word}'. Press Enter to confirm or type a different word."
                    else:
                        self.message = "Could not find a valid target word. Try suggesting again."
            except Exception as e:
                self.message = "Error finding word. Please try again."
            finally:
                self.is_loading = False

        # Create and start a new thread
        self.loading_thread = threading.Thread(target=worker, daemon=True)
        self.loading_thread.start()
    
    def draw_setup_screen(self) -> None:
        """Draw the game setup screen with modern UI."""
        # Draw background with gradient
        self.screen.fill(self.WHITE)
        
        # Draw header with gradient
        header_height = 120
        header_rect = pygame.Rect(0, 0, self.width, header_height)
        self.draw_gradient_rect(self.screen, self.PRIMARY, self.PRIMARY_LIGHT, header_rect)
        
        # Draw title with shadow
        title = "Word Ladder Game"
        shadow_surface = self.title_font.render(title, True, (0, 0, 0, 50))
        text_surface = self.title_font.render(title, True, self.WHITE)
        
        title_rect = text_surface.get_rect(center=(self.width // 2, 50))
        shadow_rect = shadow_surface.get_rect(center=(self.width // 2 + 2, 52))
        
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(text_surface, title_rect)
        
        # Draw difficulty indicator with modern styling
        diff_text = f"Difficulty: {self.selected_difficulty.capitalize()}"
        diff_rect = pygame.Rect((self.width - 300) // 2, header_height - 50, 300, 40)
        self.draw_rounded_rect(self.screen, self.WHITE, diff_rect, radius=20)
        self.draw_text(diff_text, diff_rect.center, color=self.PRIMARY)
        
        # Draw input section
        input_y = 200  # Moved up for better spacing
        
        # Draw clear instructions for the user - INCREASED WIDTH AND IMPROVED SPACING
        instructions_y = input_y - 60
        instructions_text = "Enter your own words or click 'Suggest Words'"
        instructions_rect = pygame.Rect(30, instructions_y, self.width - 60, 40)
        self.draw_gradient_rect(self.screen, self.PRIMARY_LIGHT, self.WHITE, instructions_rect)
        pygame.draw.rect(self.screen, self.PRIMARY, instructions_rect, 2, border_radius=10)
        self.draw_text(instructions_text, instructions_rect.center, color=self.PRIMARY)
        
        # Add more vertical space between instructions and prompt
        prompt_text = "Enter start word:" if not self.start_word else "Enter target word:"
        self.draw_text(prompt_text, (self.width // 2, input_y - 20), color=self.PRIMARY)
        
        # Update input box position and draw it
        self.input_box = pygame.Rect((self.width - 400) // 2, input_y, 400, 50)
        self.draw_input_box(self.input_box, self.input_text, self.input_active)
        
        # Draw suggestion button or loading animation
        button_y = input_y + 80  # Adjusted for better spacing
        center_pos = (self.width // 2, button_y)
        
        if self.is_loading:
            self.draw_loading_animation(center_pos)
        else:
            suggest_button = pygame.Rect((self.width - 250) // 2, button_y - 20, 250, 50)
            self.draw_button("Suggest Words", suggest_button, self.PRIMARY)
            
            # Draw Start Game button if both words are set
            if self.start_word and self.target_word:
                start_game_button = pygame.Rect((self.width - 250) // 2, button_y + 50, 250, 50)
                self.draw_button("Start Game", start_game_button, self.SUCCESS)
        
        # Draw current word selections with enhanced styling
        if self.start_word or self.target_word:
            words_y = button_y + (120 if self.start_word and self.target_word else 70)
            words_rect = pygame.Rect(50, words_y, self.width - 100, 80)
            self.draw_gradient_rect(self.screen, self.WHITE, self.LIGHT_GRAY, words_rect)
            pygame.draw.rect(self.screen, self.PRIMARY, words_rect, 2, border_radius=15)
            
            # Draw title
            self.draw_text("Selected Words", (self.width // 2, words_y + 20), color=self.PRIMARY)
            
            # Draw words with more horizontal spacing
            if self.start_word:
                start_text = f"Start: {self.start_word}"
                # Position start word more to the left
                start_x = self.width // 4 - 50
                self.draw_text(start_text, (start_x, words_y + 50), color=self.PRIMARY_DARK)
            
            if self.target_word:
                target_text = f"Target: {self.target_word}"
                # Position target word more to the right
                target_x = 3 * self.width // 4 + 50
                self.draw_text(target_text, (target_x, words_y + 50), color=self.PRIMARY_DARK)
        
        # Draw message with enhanced styling
        if self.message:
            message_y = self.height - 100  # Fixed position at bottom
            message_rect = pygame.Rect(50, message_y, self.width - 100, 60)
            
            # Draw message box with shadow and gradient
            shadow_rect = message_rect.copy()
            shadow_rect.y += 2
            pygame.draw.rect(self.screen, (0, 0, 0, 30), shadow_rect, border_radius=10)
            
            self.draw_gradient_rect(self.screen, self.PRIMARY_LIGHT, self.WHITE, message_rect)
            pygame.draw.rect(self.screen, self.PRIMARY, message_rect, 2, border_radius=10)
            
            # Use smaller font for longer messages
            font_to_use = self.small_font if len(self.message) > 80 else self.font
            self.draw_text(self.message, message_rect.center, font=font_to_use, color=self.PRIMARY)
    
    def handle_setup_input(self, event: pygame.event.Event) -> None:
        """Handle input on the setup screen."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if input box was clicked
            if self.input_box.collidepoint(event.pos):
                self.input_active = True
            else:
                self.input_active = False
            
            # Check if suggest button was clicked
            button_y = self.input_box.y + 80  # Match the position in draw_setup_screen
            suggest_button = pygame.Rect((self.width - 250) // 2, button_y - 20, 250, 50)
            if suggest_button.collidepoint(event.pos) and not self.is_loading:
                self.is_loading = True
                self.suggest_words_async()
                return
            
            # Check if Start Game button was clicked when both words are set
            if self.start_word and self.target_word:
                start_game_button = pygame.Rect((self.width - 250) // 2, button_y + 50, 250, 50)
                if start_game_button.collidepoint(event.pos):
                    if self.game.start_game(self.start_word, self.target_word, self.selected_difficulty):
                        self.current_screen = "game"
                        self.message = ""
                    else:
                        self.message = "Invalid word combination for selected difficulty."
                        self.target_word = ""
        
        elif event.type == pygame.KEYDOWN and self.input_active:
            if event.key == pygame.K_RETURN:
                if self.input_text:
                    if not self.start_word:
                        # Validating start word
                        if self.game.is_valid_word(self.input_text.lower()):
                            self.start_word = self.input_text.lower()
                            self.input_text = ""  # Clear input text after setting start word
                            self.message = "Start word set. Enter target word or click Suggest for a suggestion."
                        else:
                            self.message = f"'{self.input_text}' is not a valid word in our dictionary. Try again or click Suggest."
                    else:
                        # Validating target word - ensure it's different from start word
                        potential_target = self.input_text.lower()
                        if potential_target == self.start_word:
                            self.message = "Target word must be different from start word."
                            self.input_text = ""  # Clear input text
                        elif self.game.is_valid_word(potential_target):
                            # First check if a path exists using A* search
                            path = self.game.a_star_search(self.start_word, potential_target)
                            if path:
                                self.target_word = potential_target
                                self.message = f"Target word set to '{potential_target}'. Click Start Game to begin!"
                            else:
                                self.message = f"No valid path exists between '{self.start_word}' and '{potential_target}'. Try a different target word."
                                self.input_text = ""  # Clear input text
                        else:
                            self.message = f"'{self.input_text}' is not a valid word in our dictionary. Try again or click Suggest."
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.unicode.isalpha():
                # Only add character if it's a letter
                if len(self.input_text) < 8:  # Limit word length to 8
                    self.input_text += event.unicode.lower()

    def draw_game_screen(self) -> None:
        """Draw the game screen with modern UI."""
        # Draw background
        self.screen.fill(self.WHITE)
        
        # Draw header with gradient
        header_height = 80
        header_rect = pygame.Rect(0, 0, self.width, header_height)
        self.draw_gradient_rect(self.screen, self.PRIMARY, self.PRIMARY_LIGHT, header_rect)
        
        # Draw title with shadow
        title = "Word Ladder Game"
        shadow_surface = self.medium_font.render(title, True, (0, 0, 0, 50))
        text_surface = self.medium_font.render(title, True, self.WHITE)
        
        title_rect = text_surface.get_rect(center=(self.width // 2, header_height // 2))
        shadow_rect = shadow_surface.get_rect(center=(self.width // 2 + 2, header_height // 2 + 2))
        
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(text_surface, title_rect)
        
        # Draw game info panel
        info_panel_width = 300
        info_panel_height = 180
        info_panel_x = (self.width - info_panel_width) // 2
        info_panel_y = header_height + 20
        
        info_panel = pygame.Rect(info_panel_x, info_panel_y, info_panel_width, info_panel_height)
        self.draw_rounded_rect(self.screen, self.WHITE, info_panel, radius=15)
        pygame.draw.rect(self.screen, self.PRIMARY, info_panel, 2, border_radius=15)
        
        # Draw current word
        current_word_y = info_panel_y + 30
        self.draw_text("Current Word:", (info_panel_x + info_panel_width // 2, current_word_y), 
                     self.font, self.BLACK)
        
        current_word_display_y = current_word_y + 40
        self.draw_text(self.game.current_word, 
                     (info_panel_x + info_panel_width // 2, current_word_display_y), 
                     self.medium_font, self.PRIMARY)
        
        # Draw target word
        target_word_y = current_word_display_y + 50
        self.draw_text("Target Word:", (info_panel_x + info_panel_width // 2, target_word_y), 
                     self.font, self.BLACK)
        
        target_word_display_y = target_word_y + 40
        self.draw_text(self.game.target_word, 
                     (info_panel_x + info_panel_width // 2, target_word_display_y), 
                     self.medium_font, self.PRIMARY)
        
        # Draw input section
        input_section_y = info_panel_y + info_panel_height + 30
        input_width = 300
        input_height = 50
        
        # Position the input box
        self.input_box = pygame.Rect((self.width - input_width) // 2, 
                                   input_section_y, 
                                   input_width, 
                                   input_height)
        
        # Draw input box
        self.draw_input_box(self.input_box, self.input_text, self.input_active)
        
        # Draw input label
        input_label_y = input_section_y - 25
        self.draw_text("Enter your next word:", 
                     (self.width // 2, input_label_y), 
                     self.font, self.BLACK)
        
        # Draw hint button
        hint_button_width = 120
        hint_button_height = 50
        hint_button_x = (self.width - hint_button_width) // 2
        hint_button_y = input_section_y + input_height + 30
        
        self.hint_button_rect = pygame.Rect(hint_button_x, hint_button_y, 
                                         hint_button_width, hint_button_height)
        
        # Draw hint button with gradient
        self.draw_gradient_rect(self.screen, self.PRIMARY, self.PRIMARY_LIGHT, self.hint_button_rect)
        pygame.draw.rect(self.screen, self.PRIMARY_DARK, self.hint_button_rect, 2, border_radius=15)
        
        # Draw hint button text
        hint_text = f"Hint ({self.game.hints_remaining})"
        self.draw_text(hint_text, 
                     (hint_button_x + hint_button_width // 2, hint_button_y + hint_button_height // 2), 
                     self.font, self.WHITE)
        
        # Draw algorithm selection buttons
        algo_button_width = 100
        algo_button_height = 40
        algo_button_spacing = 20
        algo_buttons_y = hint_button_y + hint_button_height + 30
        
        algorithms = ["a_star", "greedy", "uniform"]
        algo_labels = ["A*", "Greedy", "Uniform"]
        
        # Calculate total width of all buttons
        total_width = len(algorithms) * algo_button_width + (len(algorithms) - 1) * algo_button_spacing
        
        # Calculate starting x position
        start_x = (self.width - total_width) // 2
        
        # Draw algorithm buttons
        self.hint_buttons = {}
        for i, (algo, label) in enumerate(zip(algorithms, algo_labels)):
            button_x = start_x + i * (algo_button_width + algo_button_spacing)
            button_rect = pygame.Rect(button_x, algo_buttons_y, 
                                    algo_button_width, algo_button_height)
            
            # Store button rect
            self.hint_buttons[algo] = button_rect
            
            # Draw button
            selected = (algo == self.selected_algorithm)
            self.draw_button(label, button_rect, 
                           self.BUTTON_SELECTED if selected else self.BUTTON_NORMAL, 
                           selected=selected)
        
        # Draw game stats
        stats_panel_width = 250
        stats_panel_height = 180
        stats_panel_x = 20
        stats_panel_y = header_height + 20
        
        stats_panel = pygame.Rect(stats_panel_x, stats_panel_y, stats_panel_width, stats_panel_height)
        self.draw_rounded_rect(self.screen, self.WHITE, stats_panel, radius=15)
        pygame.draw.rect(self.screen, self.PRIMARY, stats_panel, 2, border_radius=15)
        
        # Draw stats title
        stats_title_y = stats_panel_y + 20
        self.draw_text("Game Stats", (stats_panel_x + stats_panel_width // 2, stats_title_y), 
                     self.font, self.PRIMARY)
        
        # Draw moves
        moves_y = stats_title_y + 40
        moves_count = len(self.game.path_history) - 1
        self.draw_text(f"Moves: {moves_count}", 
                     (stats_panel_x + stats_panel_width // 2, moves_y), 
                     self.font, self.BLACK)
        
        # Draw hints
        hints_y = moves_y + 30
        self.draw_text(f"Hints: {self.game.hints_used} used, {self.game.hints_remaining} left", 
                     (stats_panel_x + stats_panel_width // 2, hints_y), 
                     self.font, self.BLACK)
        
        # Draw time
        time_y = hints_y + 30
        if self.game.time_limit != float('inf'):
            time_remaining = self.game.get_time_remaining()
            minutes = int(time_remaining // 60)
            seconds = int(time_remaining % 60)
            time_text = f"Time: {minutes}:{seconds:02d}"
        else:
            elapsed = time.time() - self.game.start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            time_text = f"Time: {minutes}:{seconds:02d}"
            
        self.draw_text(time_text, 
                     (stats_panel_x + stats_panel_width // 2, time_y), 
                     self.font, self.BLACK)
        
        # Draw score
        score_y = time_y + 30
        score = self.game.calculate_score()
        self.draw_text(f"Score: {score}", 
                     (stats_panel_x + stats_panel_width // 2, score_y), 
                     self.font, self.BLACK)
        
        # Draw path history
        path_panel_width = 250
        path_panel_height = 180
        path_panel_x = self.width - path_panel_width - 20
        path_panel_y = header_height + 20
        
        path_panel = pygame.Rect(path_panel_x, path_panel_y, path_panel_width, path_panel_height)
        self.draw_rounded_rect(self.screen, self.WHITE, path_panel, radius=15)
        pygame.draw.rect(self.screen, self.PRIMARY, path_panel, 2, border_radius=15)
        
        # Draw path title
        path_title_y = path_panel_y + 20
        self.draw_text("Your Path", (path_panel_x + path_panel_width // 2, path_title_y), 
                     self.font, self.PRIMARY)
        
        # Draw path history
        path_history_y = path_title_y + 40
        path_history_height = 120
        path_history_rect = pygame.Rect(path_panel_x + 20, path_history_y, 
                                      path_panel_width - 40, path_history_height)
        
        # Draw path history background
        pygame.draw.rect(self.screen, self.LIGHT_GRAY, path_history_rect, border_radius=10)
        
        # Draw path history text
        if self.game.path_history:
            # Create a formatted path string with arrows
            path_text = " → ".join(self.game.path_history)
            
            # Check if text is too long for the rect
            text_surface = self.small_font.render(path_text, True, self.BLACK)
            if text_surface.get_width() <= path_history_rect.width - 20:
                # Text fits, draw it normally
                text_rect = text_surface.get_rect(center=path_history_rect.center)
                self.screen.blit(text_surface, text_rect)
            else:
                # Text is too long, draw with word wrapping
                words = self.game.path_history
                lines = []
                current_line = []
                current_width = 0
                
                for word in words:
                    word_width = self.small_font.size(word)[0]
                    arrow_width = self.small_font.size(" → ")[0]
                    
                    # Check if adding this word would exceed the width
                    if current_line and current_width + word_width + arrow_width > path_history_rect.width - 20:
                        # Start a new line
                        lines.append(current_line)
                        current_line = [word]
                        current_width = word_width
                    else:
                        # Add to current line
                        current_line.append(word)
                        current_width += word_width + (arrow_width if current_line else 0)
                
                # Add the last line
                if current_line:
                    lines.append(current_line)
                
                # Draw each line
                for i, line in enumerate(lines):
                    line_text = " → ".join(line)
                    line_y = path_history_y + 20 + i * 25
                    
                    if line_y + 25 <= path_history_rect.bottom - 10:
                        self.draw_text(line_text, 
                                     (path_panel_x + path_panel_width // 2, line_y), 
                                     self.small_font, self.BLACK)
        
        # Draw message if there is one
        if self.message:
            message_y = self.height - 50
            self.draw_text(self.message, (self.width // 2, message_y), 
                         self.font, self.PRIMARY)
    
    def handle_game_over_input(self, event: pygame.event.Event) -> None:
        """Handle input on the game over screen."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if view paths button was clicked
            button_y = self.height - 150
            button_width = 200
            button_height = 50
            
            paths_button = pygame.Rect((self.width - button_width) // 2, 
                                     button_y, button_width, button_height)
            
            if paths_button.collidepoint(event.pos):
                self.current_screen = "paths"
                return
                
            # Check if view graph button was clicked
            graph_button_y = self.height - 80
            graph_button = pygame.Rect((self.width - button_width) // 2, 
                                     graph_button_y, button_width, button_height)
            
            if graph_button.collidepoint(event.pos):
                # Make sure we have algorithm paths prepared
                self.prepare_algorithm_paths()
                
                # Prepare graph data for visualization
                self.prepare_graph_data()
                
                # Reset graph view settings
                self.reset_graph_view()
                
                # Switch to graph view screen
                self.current_screen = "graph_view"
                print("Switching to graph view screen")
                return
                
            # Check if play again button was clicked
            play_again_y = self.height - 220
            play_again_button = pygame.Rect((self.width - button_width) // 2, 
                                          play_again_y, button_width, button_height)
            
            if play_again_button.collidepoint(event.pos):
                self.current_screen = "difficulty_select"
                return
    
    def handle_game_input(self, event: pygame.event.Event) -> None:
        """Handle input on the game screen."""
        if self.game.is_game_over():
            # Store the final score when the game ends
            self.final_score = self.game.calculate_score()
            self.current_screen = "game_over"
            
            # Prepare algorithm paths for comparison
            self.prepare_algorithm_paths()
            
            # Prepare graph data for visualization
            self.prepare_graph_data()
            return
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if input box was clicked
            if self.input_box.collidepoint(event.pos):
                self.input_active = True
            else:
                self.input_active = False
                
            # Check if hint button was clicked
            if hasattr(self, 'hint_button_rect') and self.hint_button_rect.collidepoint(event.pos):
                # Get hint based on selected algorithm
                hint = self.game.get_hint(self.selected_algorithm)
                if hint:
                    self.input_text = hint
                    self.message = f"Hint: Try '{hint}'"
                else:
                    self.message = "No hints available"
                    
            # Check if algorithm selection buttons were clicked
            for algo, rect in self.hint_buttons.items():
                if rect.collidepoint(event.pos):
                    self.selected_algorithm = algo
                    break
                    
        elif event.type == pygame.KEYDOWN:
            if self.input_active:
                if event.key == pygame.K_RETURN:
                    # Try to make a move with the input text
                    if self.game.make_move(self.input_text):
                        self.message = "Valid move!"
                        self.input_text = ""
                    else:
                        self.message = "Invalid move. Try again."
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                else:
                    # Add character if it's a letter
                    if event.unicode.isalpha() and len(self.input_text) < 10:
                        self.input_text += event.unicode.lower()

    def draw_game_over_screen(self) -> None:
        """Draw the game over screen with modern UI."""
        # Draw background
        self.screen.fill(self.WHITE)
        
        # Draw header with gradient
        header_height = 80
        header_rect = pygame.Rect(0, 0, self.width, header_height)
        
        # Choose header color based on win/loss
        if self.game.current_word == self.game.target_word:
            header_color = (63, 150, 81)  # Green for win
            header_color_light = (92, 180, 107)
            result_text = "You Won!"
        else:
            header_color = (181, 63, 63)  # Red for loss
            header_color_light = (192, 92, 92)
            result_text = "Time's Up!"
            
        self.draw_gradient_rect(self.screen, header_color, header_color_light, header_rect)
        
        # Draw title with shadow
        shadow_surface = self.medium_font.render(result_text, True, (0, 0, 0, 50))
        text_surface = self.medium_font.render(result_text, True, self.WHITE)
        
        title_rect = text_surface.get_rect(center=(self.width // 2, header_height // 2))
        shadow_rect = shadow_surface.get_rect(center=(self.width // 2 + 2, header_height // 2 + 2))
        
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(text_surface, title_rect)
        
        # Draw statistics card
        stats_width = 400
        stats_height = 300
        stats_x = (self.width - stats_width) // 2
        stats_y = header_height + 50
        
        stats_rect = pygame.Rect(stats_x, stats_y, stats_width, stats_height)
        self.draw_rounded_rect(self.screen, self.WHITE, stats_rect, radius=15)
        pygame.draw.rect(self.screen, self.PRIMARY, stats_rect, 2, border_radius=15)
        
        # Draw stats title
        stats_title_y = stats_y + 30
        self.draw_text("Game Statistics", (self.width // 2, stats_title_y), 
                     self.large_font, self.PRIMARY)
        
        # Draw final score
        score_y = stats_title_y + 60
        self.draw_text(f"Final Score: {self.final_score}", 
                     (self.width // 2, score_y), 
                     self.medium_font, self.PRIMARY)
        
        # Draw other stats
        stats_items = [
            ("Start Word", self.game.path_history[0]),
            ("Target Word", self.game.target_word),
            ("Moves Taken", len(self.game.path_history) - 1),
            ("Hints Used", self.game.hints_used),
            ("Time Taken", self.format_time(time.time() - self.game.start_time))
        ]
        
        for i, (label, value) in enumerate(stats_items):
            y_pos = score_y + 50 + i * 30
            
            # Draw label
            label_x = stats_x + 100
            self.draw_text(f"{label}:", (label_x, y_pos), 
                         self.font, self.BLACK, align="right")
            
            # Draw value
            value_x = stats_x + 120
            self.draw_text(str(value), (value_x, y_pos), 
                         self.font, self.PRIMARY_DARK, align="left")
        
        # Draw buttons
        button_width = 200
        button_height = 50
        
        # Play Again button
        play_again_y = self.height - 220
        play_again_rect = pygame.Rect((self.width - button_width) // 2, 
                                    play_again_y, button_width, button_height)
        
        self.draw_gradient_rect(self.screen, self.PRIMARY, self.PRIMARY_LIGHT, play_again_rect)
        pygame.draw.rect(self.screen, self.PRIMARY_DARK, play_again_rect, 2, border_radius=15)
        
        self.draw_text("Play Again", 
                     (play_again_rect.centerx, play_again_rect.centery), 
                     self.font, self.WHITE)
        
        # View Paths button
        paths_button_y = self.height - 150
        paths_button_rect = pygame.Rect((self.width - button_width) // 2, 
                                      paths_button_y, button_width, button_height)
        
        self.draw_gradient_rect(self.screen, self.PRIMARY, self.PRIMARY_LIGHT, paths_button_rect)
        pygame.draw.rect(self.screen, self.PRIMARY_DARK, paths_button_rect, 2, border_radius=15)
        
        self.draw_text("View Paths", 
                     (paths_button_rect.centerx, paths_button_rect.centery), 
                     self.font, self.WHITE)
        
        # View Graph button
        graph_button_y = self.height - 80
        graph_button_rect = pygame.Rect((self.width - button_width) // 2, 
                                      graph_button_y, button_width, button_height)
        
        self.draw_gradient_rect(self.screen, self.PRIMARY, self.PRIMARY_LIGHT, graph_button_rect)
        pygame.draw.rect(self.screen, self.PRIMARY_DARK, graph_button_rect, 2, border_radius=15)
        
        self.draw_text("View Graph", 
                     (graph_button_rect.centerx, graph_button_rect.centery), 
                     self.font, self.WHITE)
    
    def format_time(self, seconds):
        """Format time in seconds to MM:SS format."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"

    def draw_paths_screen(self) -> None:
        """Draw the paths comparison screen with a simple, clean UI."""
        # Draw background
        self.screen.fill(self.WHITE)
        
        # Draw header with gradient
        header_height = 80
        header_rect = pygame.Rect(0, 0, self.width, header_height)
        self.draw_gradient_rect(self.screen, self.PRIMARY, self.PRIMARY_LIGHT, header_rect)
        
        # Draw title with shadow
        title = "Path Comparison"
        shadow_surface = self.title_font.render(title, True, (0, 0, 0, 50))
        text_surface = self.title_font.render(title, True, self.WHITE)
        
        title_rect = text_surface.get_rect(center=(self.width // 2, header_height // 2))
        shadow_rect = shadow_surface.get_rect(center=(self.width // 2 + 2, header_height // 2 + 2))
        
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(text_surface, title_rect)
        
        # Display path length in the header
        if self.game.path_history:
            path_len = len(self.game.path_history) - 1
            length_text = f"Length: {path_len}"
            length_surface = self.medium_font.render(length_text, True, self.WHITE)
            length_rect = length_surface.get_rect(midright=(self.width - 20, header_height // 2))
            self.screen.blit(length_surface, length_rect)
        
        # Calculate content height to determine if scrolling is needed
        path_box_height = 80  # Height for each path box
        path_spacing = 20     # Spacing between path boxes
        
        # Count all algorithm paths (including empty ones to ensure all algorithms are shown)
        algo_count = len([algo for algo in self.graph_paths.keys() if algo != "user"])
        
        # Calculate content height based on number of algorithms + user path
        content_height = path_box_height * (1 + algo_count) + path_spacing * (algo_count + 2)
        
        # Set maximum scroll based on content height
        visible_height = self.height - header_height - 80  # Subtract header and button area
        self.max_scroll = max(0, content_height - visible_height)
        
        # Create a surface for scrollable content
        content_surface = pygame.Surface((self.width, content_height), pygame.SRCALPHA)
        content_surface.fill((0, 0, 0, 0))  # Transparent background
        
        # Draw paths on content surface
        path_y = 20
        
        # Define algorithm info
        algo_colors = {
            "user": (63, 81, 181),     # PRIMARY
            "a_star": (200, 80, 80),   # Red
            "greedy": (80, 180, 80),   # Green
            "uniform": (80, 80, 200)   # Blue
        }
        
        algo_names = {
            "user": "Your Path",
            "a_star": "A* Algorithm",
            "greedy": "Greedy Best-First Search",
            "uniform": "Uniform Cost Search (BFS)"
        }
        
        # First draw your path
        user_path_rect = pygame.Rect(30, path_y, self.width - 60, path_box_height)
        
        # Draw simple background rectangle
        pygame.draw.rect(content_surface, (230, 235, 250), user_path_rect, border_radius=10)
        pygame.draw.rect(content_surface, algo_colors["user"], user_path_rect, 2, border_radius=10)
        
        # Draw path header
        header_text = algo_names["user"]
        header_surface = self.font.render(header_text, True, algo_colors["user"])
        header_rect = header_surface.get_rect(midleft=(user_path_rect.left + 15, user_path_rect.top + 25))
        content_surface.blit(header_surface, header_rect)
        
        # Draw user path
        if self.game.path_history:
            path_rect = pygame.Rect(user_path_rect.left + 15, user_path_rect.top + 45, 
                                  user_path_rect.width - 30, 20)
            self.draw_path_with_spacing_on_surface(self.game.path_history, path_rect, 
                                                algo_colors["user"], content_surface)
        
        path_y += path_box_height + path_spacing
        
        # Define the order of algorithms to display
        algorithm_order = ["a_star", "greedy", "uniform"]
        
        # Draw algorithm paths in specific order
        for algo in algorithm_order:
            path = self.graph_paths.get(algo, [])
            
            algo_rect = pygame.Rect(30, path_y, self.width - 60, path_box_height)
            
            # Draw simple background rectangle
            bg_color = (250, 230, 230) if algo == "a_star" else (230, 250, 230) if algo == "greedy" else (230, 230, 250)
            pygame.draw.rect(content_surface, bg_color, algo_rect, border_radius=10)
            pygame.draw.rect(content_surface, algo_colors.get(algo, self.PRIMARY), algo_rect, 2, border_radius=10)
            
            # Draw algorithm name
            header_text = algo_names.get(algo, algo.capitalize())
            header_surface = self.font.render(header_text, True, algo_colors.get(algo, self.PRIMARY))
            header_rect = header_surface.get_rect(midleft=(algo_rect.left + 15, algo_rect.top + 25))
            content_surface.blit(header_surface, header_rect)
            
            # Draw path length
            if path:
                path_len = len(path) - 1
                path_len_text = f"Length: {path_len}"
                len_surface = self.small_font.render(path_len_text, True, algo_colors.get(algo, self.PRIMARY))
                len_rect = len_surface.get_rect(midright=(algo_rect.right - 15, algo_rect.top + 25))
                content_surface.blit(len_surface, len_rect)
                
                # Draw algorithm path
                path_rect = pygame.Rect(algo_rect.left + 15, algo_rect.top + 45, 
                                      algo_rect.width - 30, 20)
                self.draw_path_with_spacing_on_surface(path, path_rect, 
                                                    algo_colors.get(algo, self.PRIMARY), content_surface)
            else:
                # Draw "No path found" message
                no_path_text = "No path found"
                no_path_surface = self.font.render(no_path_text, True, algo_colors.get(algo, self.PRIMARY))
                no_path_rect = no_path_surface.get_rect(center=(algo_rect.centerx, algo_rect.top + 45))
                content_surface.blit(no_path_surface, no_path_rect)
            
            path_y += path_box_height + path_spacing
        
        # Draw scrollable content
        visible_rect = pygame.Rect(0, self.scroll_y, self.width, visible_height)
        self.screen.blit(content_surface, (0, header_height), visible_rect)
        
        # Draw scrollbar if needed
        if self.max_scroll > 0:
            # Draw scrollbar track
            track_rect = pygame.Rect(self.width - 15, header_height, 10, visible_height)
            pygame.draw.rect(self.screen, self.LIGHT_GRAY, track_rect, border_radius=5)
            
            # Calculate scrollbar thumb size and position
            thumb_height = max(30, visible_height * (visible_height / content_height))
            thumb_pos = header_height + (self.scroll_y / self.max_scroll) * (visible_height - thumb_height)
            thumb_rect = pygame.Rect(self.width - 15, thumb_pos, 10, thumb_height)
            
            # Draw scrollbar thumb
            pygame.draw.rect(self.screen, self.PRIMARY, thumb_rect, border_radius=5)
            
            # Draw scroll indicators if needed
            if self.scroll_y > 0:
                # Up arrow indicator
                pygame.draw.polygon(self.screen, self.PRIMARY, [
                    (self.width - 20, header_height + 15),
                    (self.width - 10, header_height + 15),
                    (self.width - 15, header_height + 5)
                ])
            
            if self.scroll_y < self.max_scroll:
                # Down arrow indicator
                pygame.draw.polygon(self.screen, self.PRIMARY, [
                    (self.width - 20, self.height - 90),
                    (self.width - 10, self.height - 90),
                    (self.width - 15, self.height - 80)
                ])
        
        # Draw back button
        button_y = self.height - 70
        button_width = 200
        button_height = 50
        
        back_button = pygame.Rect((self.width - button_width) // 2, 
                                button_y, button_width, button_height)
        
        # Draw button with simple style
        pygame.draw.rect(self.screen, self.PRIMARY, back_button, border_radius=10)
        
        # Draw button text
        text = "Back to Game Over"
        text_surface = self.font.render(text, True, self.WHITE)
        text_rect = text_surface.get_rect(center=back_button.center)
        self.screen.blit(text_surface, text_rect)

    def draw_graph_view_screen(self):
        # Draw background
        self.screen.fill((240, 240, 245))
        
        # Draw title with shadow
        title_text = "Word Ladder Graph Visualization"
        title_font = pygame.font.Font(None, 48)
        
        # Draw shadow
        shadow_surface = title_font.render(title_text, True, (100, 100, 100))
        shadow_rect = shadow_surface.get_rect(center=(self.width // 2 + 3, 50 + 3))
        self.screen.blit(shadow_surface, shadow_rect)
        
        # Draw title text
        title_surface = title_font.render(title_text, True, (50, 50, 50))
        title_rect = title_surface.get_rect(center=(self.width // 2, 50))
        self.screen.blit(title_surface, title_rect)
        
        # Draw edges first (so they appear behind nodes)
        for edge in self.graph_edges:
            word1, word2 = edge
            pos1 = self.node_positions[word1]
            pos2 = self.node_positions[word2]
            
            # Apply zoom and offset
            screen_pos1 = (pos1[0] * self.zoom_level + self.graph_offset[0] + self.width // 2,
                          pos1[1] * self.zoom_level + self.graph_offset[1] + self.height // 2)
            screen_pos2 = (pos2[0] * self.zoom_level + self.graph_offset[0] + self.width // 2,
                          pos2[1] * self.zoom_level + self.graph_offset[1] + self.height // 2)
            
            # Draw edges with their colors
            edge_colors = self.edge_colors.get(edge, [(200, 200, 200)])
            edge_width = self.edge_widths.get(edge, 1)
            
            # If edge is in multiple paths, draw multiple lines with slight offsets
            if len(edge_colors) > 1:
                offsets = [(-2, -2), (2, 2), (-2, 2), (2, -2)]
                for i, color in enumerate(edge_colors[:4]):  # Limit to 4 paths max
                    offset = offsets[i % len(offsets)]
                    offset_pos1 = (screen_pos1[0] + offset[0], screen_pos1[1] + offset[1])
                    offset_pos2 = (screen_pos2[0] + offset[0], screen_pos2[1] + offset[1])
                    pygame.draw.line(self.screen, color, offset_pos1, offset_pos2, edge_width)
            else:
                # Single color edge
                pygame.draw.line(self.screen, edge_colors[0], screen_pos1, screen_pos2, edge_width)
        
        # Draw nodes
        for node in self.graph_nodes:
            if node in self.node_positions:
                pos = self.node_positions[node]
                
                # Apply zoom and offset
                screen_pos = (pos[0] * self.zoom_level + self.graph_offset[0] + self.width // 2,
                              pos[1] * self.zoom_level + self.graph_offset[1] + self.height // 2)
                
                color = self.node_colors.get(node, self.LIGHT_GRAY)
                
                # Determine node size based on importance
                node_size = 15
                if node == self.game.path_history[0] or node == self.game.target_word:
                    node_size = 20
                elif node in self.game.path_history:
                    node_size = 18
                
                # Draw node shadow (use solid color)
                shadow_pos = (int(screen_pos[0] + 3), int(screen_pos[1] + 3))
                pygame.draw.circle(self.screen, (100, 100, 100), shadow_pos, node_size)
                
                # Draw node circle
                pygame.draw.circle(self.screen, color, (int(screen_pos[0]), int(screen_pos[1])), node_size)
                
                # Draw node interior (white or light color)
                interior_color = self.WHITE
                pygame.draw.circle(self.screen, interior_color, (int(screen_pos[0]), int(screen_pos[1])), node_size - 3)
                
                # Draw node text (word)
                text_surface = self.small_font.render(node, True, self.BLACK)
                text_rect = text_surface.get_rect(center=screen_pos)
                self.screen.blit(text_surface, text_rect)
                
                # Draw heuristic value below the node
                if node in self.heuristic_values:
                    h_value = self.heuristic_values[node]
                    h_text = f"h={h_value}"
                    h_surface = self.tiny_font.render(h_text, True, self.PRIMARY_DARK)
                    h_rect = h_surface.get_rect(midtop=(screen_pos[0], screen_pos[1] + node_size + 2))
                    self.screen.blit(h_surface, h_rect)
        
        # Draw legend
        legend_font = pygame.font.Font(None, 24)
        legend_items = [
            ("Start Word", (255, 0, 0)),
            ("Target Word", (0, 255, 0)),
            ("User Path", (128, 0, 255)),
            ("A* Path", (255, 100, 100)),
            ("Greedy Path", (100, 255, 100)),
            ("Uniform Path", (100, 100, 255))
        ]
        
        legend_y = 100
        for text, color in legend_items:
            # Draw color box
            pygame.draw.rect(self.screen, color, (20, legend_y, 20, 20))
            pygame.draw.rect(self.screen, (0, 0, 0), (20, legend_y, 20, 20), 1)
            
            # Draw text
            text_surface = legend_font.render(text, True, (0, 0, 0))
            self.screen.blit(text_surface, (50, legend_y))
            legend_y += 30
        
        # Draw instructions
        instructions = [
            "Drag to move the graph",
            "Scroll to zoom in/out",
            "Click on a node to see details",
            "Press ESC to return to game over screen"
        ]
        
        instruction_font = pygame.font.Font(None, 24)
        instruction_y = self.height - 120
        for instruction in instructions:
            text_surface = instruction_font.render(instruction, True, (80, 80, 80))
            text_rect = text_surface.get_rect(right=self.width - 20, y=instruction_y)
            self.screen.blit(text_surface, text_rect)
            instruction_y += 30
        
        # Draw selected node info if any
        if self.selected_node:
            info_font = pygame.font.Font(None, 28)
            info_text = f"Selected: {self.selected_node}"
            info_surface = info_font.render(info_text, True, (0, 0, 0))
            info_rect = info_surface.get_rect(center=(self.width // 2, self.height - 50))
            self.screen.blit(info_surface, info_rect)
            
            # Draw additional info about the node
            if self.selected_node in self.heuristic_values:
                h_value = self.heuristic_values[self.selected_node]
                h_text = f"Heuristic value: {h_value}"
                h_surface = info_font.render(h_text, True, (0, 0, 0))
                h_rect = h_surface.get_rect(center=(self.width // 2, self.height - 20))
                self.screen.blit(h_surface, h_rect)

    def draw_node_info_panel(self, node):
        """Draw information panel for the selected node."""
        if not node:
            return
            
        # Panel position and size
        panel_width = 280
        panel_height = 250
        panel_x = self.width - panel_width - 20
        panel_y = 100
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        
        # Draw panel background with gradient
        self.draw_gradient_rect(self.screen, (245, 245, 255), self.WHITE, panel_rect)
        pygame.draw.rect(self.screen, self.PRIMARY, panel_rect, 2, border_radius=10)
        
        # Draw node word as title
        title_y = panel_y + 20
        self.draw_text(node, (panel_x + panel_width // 2, title_y), 
                     self.medium_font, self.PRIMARY_DARK)
        
        # Draw letter differences from start and target
        start_word = self.game.path_history[0]
        target_word = self.game.target_word
        
        diff_y = title_y + 35
        
        # Calculate differences
        start_diff = sum(1 for a, b in zip(node, start_word) if a != b)
        target_diff = sum(1 for a, b in zip(node, target_word) if a != b)
        
        # Draw difference information
        diff_text = f"Differences: {start_diff} from start, {target_diff} from target"
        self.draw_text(diff_text, (panel_x + panel_width // 2, diff_y), 
                     self.small_font, self.BLACK)
        
        # Draw heuristic value with explanation
        h_value = self.heuristic_values.get(node, 0)
        h_text = f"Heuristic value: {h_value}"
        h_y = diff_y + 30
        self.draw_text(h_text, (panel_x + panel_width // 2, h_y), 
                     self.font, self.PRIMARY_DARK)
        
        h_explain_y = h_y + 20
        h_explain = "(Sum of letter positions in alphabet: A=1, B=2, ...)"
        self.draw_text(h_explain, (panel_x + panel_width // 2, h_explain_y), 
                     self.tiny_font, self.GRAY)
        
        # Draw which paths this node is part of
        paths_y = h_explain_y + 30
        self.draw_text("Part of paths:", (panel_x + panel_width // 2, paths_y), 
                     self.font, self.BLACK)
        
        # Check which paths this node is in
        in_paths = []
        if node in self.game.path_history:
            in_paths.append(("User Path", (100, 100, 200)))
        if node in self.graph_paths.get("a_star", []):
            in_paths.append(("A* Path", (200, 150, 50)))
        if node in self.graph_paths.get("greedy", []):
            in_paths.append(("Greedy Path", (150, 50, 150)))
        if node in self.graph_paths.get("uniform", []):
            in_paths.append(("Uniform Path", (50, 150, 150)))
        
        # Display paths
        for i, (path_name, color) in enumerate(in_paths):
            path_y = paths_y + 25 + i * 20
            
            # Draw color indicator
            pygame.draw.circle(self.screen, color, (panel_x + 30, path_y), 6)
            
            # Draw path name
            self.draw_text(path_name, (panel_x + 40, path_y), 
                         self.small_font, self.BLACK, align="left")
        
        # If not in any path
        if not in_paths:
            self.draw_text("Not in any path", (panel_x + panel_width // 2, paths_y + 25), 
                         self.small_font, self.GRAY)
            
        # Draw neighbors information
        neighbors_y = paths_y + 25 + max(len(in_paths), 1) * 20 + 10
        neighbors = self.game.get_neighbors(node)
        neighbors_in_graph = [n for n in neighbors if n in self.graph_nodes]
        
        if neighbors_in_graph:
            self.draw_text(f"Neighbors: {len(neighbors_in_graph)}", 
                         (panel_x + panel_width // 2, neighbors_y), 
                         self.small_font, self.BLACK)
                         
            # Show up to 3 neighbors with their heuristic values
            max_display = min(3, len(neighbors_in_graph))
            sorted_neighbors = sorted(neighbors_in_graph, 
                                    key=lambda n: self.heuristic_values.get(n, 0))[:max_display]
            
            for i, neighbor in enumerate(sorted_neighbors):
                n_y = neighbors_y + 20 + i * 20
                n_h = self.heuristic_values.get(neighbor, 0)
                n_text = f"{neighbor} (h={n_h})"
                self.draw_text(n_text, (panel_x + panel_width // 2, n_y), 
                             self.tiny_font, self.PRIMARY)
        else:
            self.draw_text("No neighbors in graph", 
                         (panel_x + panel_width // 2, neighbors_y), 
                         self.small_font, self.GRAY)

    def run(self) -> None:
        """Run the game loop."""
        running = True
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                # Handle input based on current screen
                if self.current_screen == "difficulty_select":
                    self.handle_difficulty_select_input(event)
                elif self.current_screen == "setup":
                    self.handle_setup_input(event)
                elif self.current_screen == "game":
                    self.handle_game_input(event)
                elif self.current_screen == "game_over":
                    self.handle_game_over_input(event)
                elif self.current_screen == "paths":
                    self.handle_paths_screen_input(event)
                elif self.current_screen == "graph_view":
                    self.handle_graph_view_input(event)
            
            # Check for word suggestion results
            if self.is_loading and not self.loading_thread.is_alive():
                self.check_suggestion_result()
            
            # Draw current screen
            if self.current_screen == "difficulty_select":
                self.draw_difficulty_select_screen()
            elif self.current_screen == "setup":
                self.draw_setup_screen()
            elif self.current_screen == "game":
                self.draw_game_screen()
            elif self.current_screen == "game_over":
                self.draw_game_over_screen()
            elif self.current_screen == "paths":
                self.draw_paths_screen()
            elif self.current_screen == "graph_view":
                self.draw_graph_view_screen()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()

    def handle_graph_view_input(self, event: pygame.event.Event) -> None:
        """Handle input on the graph view screen."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            
            # Check if a node was clicked
            for node in self.graph_nodes:
                if node in self.node_positions:
                    pos = self.node_positions[node]
                    
                    # Apply zoom and offset to get screen position
                    screen_pos = (pos[0] * self.zoom_level + self.graph_offset[0] + self.width // 2,
                                 pos[1] * self.zoom_level + self.graph_offset[1] + self.height // 2)
                    
                    # Determine node size based on importance
                    node_size = 15
                    if node == self.game.path_history[0] or node == self.game.target_word:
                        node_size = 20
                    elif node in self.game.path_history:
                        node_size = 18
                        
                    # Check if click is within node radius
                    distance = ((mouse_pos[0] - screen_pos[0]) ** 2 + 
                              (mouse_pos[1] - screen_pos[1]) ** 2) ** 0.5
                    if distance <= node_size:
                        if event.button == 1:  # Left click
                            # Toggle selection if clicking the same node
                            if self.selected_node == node:
                                self.selected_node = None
                            else:
                                self.selected_node = node
                            return
            
            # If clicked outside any node, deselect and start dragging the view
            if event.button == 1:  # Left click
                self.selected_node = None
                self.dragging = True
                self.drag_start = mouse_pos
            
            # Handle zoom with mouse wheel
            elif event.button == 4:  # Scroll up
                self.zoom_level *= 1.1
                self.zoom_level = min(self.zoom_level, 3.0)  # Max zoom
            elif event.button == 5:  # Scroll down
                self.zoom_level *= 0.9
                self.zoom_level = max(self.zoom_level, 0.3)  # Min zoom
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left button released
                self.dragging = False
                
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                # Calculate the movement delta
                dx = event.pos[0] - self.drag_start[0]
                dy = event.pos[1] - self.drag_start[1]
                
                # Update the graph offset
                self.graph_offset = (self.graph_offset[0] + dx, self.graph_offset[1] + dy)
                
                # Update drag start position
                self.drag_start = event.pos
                
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Return to game over screen
                self.current_screen = "game_over"
            elif event.key == pygame.K_r:
                # Reset view
                self.reset_graph_view()
    
    def adjust_node_positions_for_zoom(self, zoom_factor):
        """Adjust node positions when zooming."""
        if not self.node_positions:
            return
            
        # Calculate center of view
        center_x = self.width // 2
        center_y = self.height // 2
        
        # Scale all node positions relative to center
        for node in self.node_positions:
            pos = self.node_positions[node]
            # Vector from center to node
            dx = pos[0] - center_x
            dy = pos[1] - center_y
            # Scale vector
            new_dx = dx * zoom_factor
            new_dy = dy * zoom_factor
            # New position
            self.node_positions[node] = (center_x + new_dx, center_y + new_dy)

    def prepare_algorithm_paths(self) -> None:
        """Prepare paths for all search algorithms."""
        if not self.game.path_history:
            return
            
        # Get start and target words
        start_word = self.game.path_history[0]
        target_word = self.game.target_word
        
        # Initialize graph paths dictionary if it doesn't exist
        if not hasattr(self, 'graph_paths'):
            self.graph_paths = {}
        
        # Store user path
        self.graph_paths["user"] = self.game.path_history
        
        # Get A* path
        a_star_path = self.game.a_star_search(start_word, target_word)
        self.graph_paths["a_star"] = a_star_path if a_star_path else []
        
        # Get Greedy Best-First Search path
        greedy_path = self.game.greedy_best_first_search(start_word, target_word)
        self.graph_paths["greedy"] = greedy_path if greedy_path else []
        
        # Get Uniform Cost Search path
        uniform_path = self.game.uniform_cost_search(start_word, target_word)
        self.graph_paths["uniform"] = uniform_path if uniform_path else []
        
        # Print path lengths for debugging
        print(f"User path: {len(self.graph_paths['user']) - 1} steps")
        print(f"A* path: {len(self.graph_paths['a_star']) - 1 if self.graph_paths['a_star'] else 'No path'}")
        print(f"Greedy path: {len(self.graph_paths['greedy']) - 1 if self.graph_paths['greedy'] else 'No path'}")
        print(f"Uniform path: {len(self.graph_paths['uniform']) - 1 if self.graph_paths['uniform'] else 'No path'}")

    def handle_paths_screen_input(self, event: pygame.event.Event) -> None:
        """Handle input on the paths comparison screen."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if back button was clicked
            button_y = self.height - 70
            button_width = 200
            button_height = 50
            
            back_button = pygame.Rect((self.width - button_width) // 2, 
                                    button_y, button_width, button_height)
            
            if back_button.collidepoint(event.pos):
                self.current_screen = "game_over"
                return
            
            # Handle scrolling with mouse wheel
            if event.button == 4:  # Scroll up
                self.scroll_y = max(0, self.scroll_y - self.scroll_speed)
            elif event.button == 5:  # Scroll down
                self.scroll_y = min(self.max_scroll, self.scroll_y + self.scroll_speed)
            
            # Check if scrollbar was clicked
            header_height = 80
            visible_height = self.height - header_height - 80
            
            if self.max_scroll > 0:
                # Calculate scrollbar thumb size and position
                thumb_height = max(30, visible_height * (visible_height / (visible_height + self.max_scroll)))
                thumb_pos = header_height + (self.scroll_y / self.max_scroll) * (visible_height - thumb_height)
                thumb_rect = pygame.Rect(self.width - 15, thumb_pos, 10, thumb_height)
                
                if thumb_rect.collidepoint(event.pos):
                    self.scrollbar_active = True
                    self.scroll_start_y = event.pos[1]
                    self.scroll_start_value = self.scroll_y
        
        elif event.type == pygame.MOUSEBUTTONUP:
            # Stop scrollbar dragging
            self.scrollbar_active = False
        
        elif event.type == pygame.MOUSEMOTION:
            # Handle scrollbar dragging
            if self.scrollbar_active and self.max_scroll > 0:
                header_height = 80
                visible_height = self.height - header_height - 80
                
                # Calculate how much to scroll based on mouse movement
                delta_y = event.pos[1] - self.scroll_start_y
                delta_scroll = delta_y * (self.max_scroll / (visible_height - 30))  # 30 is min thumb height
                
                # Update scroll position
                self.scroll_y = max(0, min(self.max_scroll, self.scroll_start_value + delta_scroll))

    def draw_path_with_spacing_on_surface(self, path, rect, color, surface):
        """Draw a path with proper spacing on the given surface."""
        if not path:
            return
            
        # Calculate spacing between words
        path_width = rect.width
        word_count = len(path)
        
        if word_count <= 1:
            return
            
        # Draw path with arrows
        arrow_text = " -> "
        full_text = arrow_text.join(path)
        
        # Check if text is too long for rect
        text_surface = self.small_font.render(full_text, True, color)
        if text_surface.get_width() <= path_width:
            # Text fits, draw it normally
            text_rect = text_surface.get_rect(midleft=(rect.left, rect.centery))
            surface.blit(text_surface, text_rect)
        else:
            # Text is too long, draw with ellipsis
            visible_words = []
            current_width = 0
            arrow_width = self.small_font.size(arrow_text)[0]
            
            # Always include first and last words
            first_word = path[0]
            last_word = path[-1]
            first_width = self.small_font.size(first_word)[0]
            last_width = self.small_font.size(last_word)[0]
            
            # Reserve space for first word, ellipsis, and last word
            ellipsis_width = self.small_font.size(" ... ")[0]
            available_width = path_width - first_width - ellipsis_width - last_width
            
            if available_width > 0:
                # Add as many middle words as possible
                middle_words = []
                for i in range(1, word_count - 1):
                    word = path[i]
                    word_width = self.small_font.size(word)[0] + arrow_width
                    if current_width + word_width <= available_width:
                        middle_words.append(word)
                        current_width += word_width
                    else:
                        break
                
                # Construct visible text
                if middle_words:
                    visible_text = first_word + arrow_text + arrow_text.join(middle_words) + arrow_text + "..." + arrow_text + last_word
                else:
                    visible_text = first_word + arrow_text + "..." + arrow_text + last_word
            else:
                # Not enough space for middle words
                visible_text = first_word + arrow_text + "..." + arrow_text + last_word
            
            # Draw the visible text
            text_surface = self.small_font.render(visible_text, True, color)
            text_rect = text_surface.get_rect(midleft=(rect.left, rect.centery))
            surface.blit(text_surface, text_rect)

    def check_suggestion_result(self) -> None:
        """Check the result of the word suggestion thread."""
        self.is_loading = False
        # The result is already stored in self.input_text by the worker thread

    def prepare_graph_data(self) -> None:
        """Prepare graph data for visualization."""
        # Get start and target words
        start_word = self.game.path_history[0]
        target_word = self.game.target_word
        
        # Collect all words from path histories
        all_words = set([start_word, target_word])
        
        # Add user path
        for word in self.game.path_history:
            all_words.add(word)
            
        # Add algorithm paths
        for path_name, path in self.graph_paths.items():
            if path:
                for word in path:
                    all_words.add(word)
        
        # Expand graph with limited neighbors
        expanded_words = set(all_words)
        MAX_NEIGHBORS_PER_WORD = 5  # Limit to 5 neighbors per word for readability
        
        for word in all_words:
            neighbors = self.game.get_neighbors(word)
            
            # Sort neighbors by heuristic value (distance to target)
            # This prioritizes neighbors that are closer to the target word
            sorted_neighbors = sorted(
                neighbors, 
                key=lambda w: self.game.heuristic(w, target_word)
            )[:MAX_NEIGHBORS_PER_WORD]  # Take only the top neighbors
            
            expanded_words.update(sorted_neighbors)
        
        # Calculate heuristic values
        self.heuristic_values = {}
        for word in expanded_words:
            self.heuristic_values[word] = self.game.heuristic(word, target_word)
        
        # Set up nodes and edges
        self.graph_nodes = list(expanded_words)
        self.graph_edges = []
        
        # Create edges
        for word in expanded_words:
            neighbors = self.game.get_neighbors(word)
            
            # Again, limit and sort neighbors for edge creation
            sorted_neighbors = sorted(
                [n for n in neighbors if n in expanded_words],
                key=lambda w: self.game.heuristic(w, target_word)
            )[:MAX_NEIGHBORS_PER_WORD]
            
            for neighbor in sorted_neighbors:
                # Sort to ensure consistent edge representation
                edge = tuple(sorted([word, neighbor]))
                if edge not in self.graph_edges:
                    self.graph_edges.append(edge)
        
        # Position nodes using spring layout
        G = nx.Graph()
        G.add_nodes_from(self.graph_nodes)
        G.add_edges_from(self.graph_edges)
        
        # Use spring layout with better parameters for readability
        pos = nx.spring_layout(
            G, 
            k=1.5/math.sqrt(len(self.graph_nodes)),  # Optimal distance between nodes
            iterations=100,  # More iterations for better layout
            seed=42
        )
        
        # Adjust positions to center start and target horizontally
        pos[start_word] = np.array([-1.0, 0.0])
        pos[target_word] = np.array([1.0, 0.0])
        
        # Recompute layout with fixed positions
        fixed_nodes = [start_word, target_word]
        fixed_pos = {start_word: pos[start_word], target_word: pos[target_word]}
        pos = nx.spring_layout(
            G, 
            pos=pos, 
            fixed=fixed_nodes, 
            k=1.5/math.sqrt(len(self.graph_nodes)),
            iterations=50,
            seed=42
        )
        
        # Scale positions
        scale_factor = 200
        self.node_positions = {word: (pos[word][0] * scale_factor, pos[word][1] * scale_factor) 
                              for word in self.graph_nodes}
        
        # Set node colors
        self.node_colors = {}
        
        # Start and target words
        self.node_colors[start_word] = (50, 150, 50)  # Green for start
        self.node_colors[target_word] = (150, 50, 50)  # Red for target
        
        # User path
        for word in self.game.path_history:
            if word != start_word and word != target_word:
                self.node_colors[word] = (100, 100, 200)  # Blue for user path
        
        # Algorithm paths
        for word in self.graph_nodes:
            # Check if node is in A* path
            if word in self.graph_paths.get('a_star', []) and word != start_word and word != target_word:
                self.node_colors[word] = (200, 150, 50)  # Orange for A*
                
            # Check if node is in Greedy path
            if word in self.graph_paths.get('greedy', []) and word != start_word and word != target_word:
                self.node_colors[word] = (150, 50, 150)  # Purple for Greedy
                
            # Check if node is in Uniform path
            if word in self.graph_paths.get('uniform', []) and word != start_word and word != target_word:
                self.node_colors[word] = (50, 150, 150)  # Teal for Uniform
        
        # Set edge colors
        self.edge_colors = {}
        self.edge_widths = {}
        
        # Define colors for different paths
        user_color = (100, 100, 200)  # Blue for user path
        a_star_color = (200, 150, 50)  # Orange for A*
        greedy_color = (150, 50, 150)  # Purple for Greedy
        uniform_color = (50, 150, 150)  # Teal for Uniform
        
        # Process user path
        for i in range(len(self.game.path_history) - 1):
            word1 = self.game.path_history[i]
            word2 = self.game.path_history[i + 1]
            edge = tuple(sorted([word1, word2]))
            
            if edge not in self.edge_colors:
                self.edge_colors[edge] = []
            self.edge_colors[edge].append(user_color)
        
        # Process algorithm paths
        for path_name, path in self.graph_paths.items():
            if not path:
                continue
                
            color = a_star_color if path_name == 'a_star' else \
                    greedy_color if path_name == 'greedy' else \
                    uniform_color
                    
            for i in range(len(path) - 1):
                word1 = path[i]
                word2 = path[i + 1]
                edge = tuple(sorted([word1, word2]))
                
                if edge not in self.edge_colors:
                    self.edge_colors[edge] = []
                self.edge_colors[edge].append(color)
        
        # Set default color for edges not in any path
        for edge in self.graph_edges:
            if edge not in self.edge_colors:
                self.edge_colors[edge] = [(220, 220, 220)]  # Light gray
            
            # Set edge width based on number of paths it belongs to
            self.edge_widths[edge] = min(1 + len(self.edge_colors[edge]), 4)
            
        print(f"Graph prepared: {len(self.graph_nodes)} nodes, {len(self.graph_edges)} edges")

    def reset_graph_view(self):
        """Reset the graph view to default settings."""
        # Reset zoom and position
        self.zoom_level = 1.0
        self.graph_offset = (0, 0)
        
        # Reset selection and dragging state
        self.selected_node = None
        self.dragging = False
        self.drag_start = None
        
        # Make sure we have algorithm paths prepared
        if not any(self.graph_paths.values()):
            self.prepare_algorithm_paths()
            
        # Make sure we have graph data prepared
        if not self.graph_nodes:
            self.prepare_graph_data()
            
        print(f"Graph reset: {len(self.graph_nodes)} nodes, {len(self.graph_edges)} edges")

if __name__ == "__main__":
    try:
        gui = WordLadderGUI()
        gui.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1) 