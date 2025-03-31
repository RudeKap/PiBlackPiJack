import pygame
import sys
import math
import random

# Initialize Pygame
pygame.init()
# pygame.key.set_repeat(0)  # Disable key repeat so that one key press is processed only once
pygame.key.set_repeat(250, 50) # Enable key repeat: wait 250ms, repeat every 50ms

# Constants
WIDTH, HEIGHT = 1200, 600
FPS = 60
TITLE = "PiBlackPiJack"
THRESHOLD = math.pi * 7  # Bust threshold is now π*7
ANIMATION_DURATION = 0.5  # Duration for card and chip animations
STARTING_COINS = 100 # Define starting coins constant
WINNING_COIN_TARGET = 314

# Colors
DARK_GREEN = (10, 50, 10)
YELLOW = (255, 215, 0)
PURPLE = (128, 0, 128)
NEON_BLUE = (0, 255, 255)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
PINK = (255, 105, 180)
CYAN = (0, 255, 255)
RED = (255, 0, 0)
OVERLAY_COLOR = (0, 0, 0, 180) # Semi-transparent overlay
GAMEOVER_OVERLAY_COLOR = (0, 0, 0, 220) # More opaque for game over

# Fonts
pygame.font.init()
font_large = pygame.font.SysFont("consolas", 40)
font_medium = pygame.font.SysFont("consolas", 32) # Added for button text maybe
font_small = pygame.font.SysFont("consolas", 24)

# Setup display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()

# Betting variables
player_coins = STARTING_COINS       # Starting coins
current_bet = 0          # Current bet amount
bet_confirmed = False    # Flag to indicate bet confirmation

# Global game state and related variables
menu_overlay_active = False
restart_confirmation = False
# Added "game_over" state
game_state = "betting"   # "betting", "dealing", "idle", "dealer_turn", "round_end", "game_over"
animation_queue = []     # Queue for card animations
active_animation = None
chip_animations = []     # Queue for chip animations
round_result = None      # Round result text
player_pi_input = ""     # Player's input for a PI card

# Lists to hold dealt cards
player_cards = []  # Each element: {"pos": pos, "card": card}
dealer_cards = []  # Each element: (pos, card)

# Deck starting position for animations
deck_pos = (100, 100)

# Predefined dealer target positions for initial deal
dealer_targets = [(WIDTH // 2 - 150, 130), (WIDTH // 2 - 70, 130)]

# --- Function Definitions (create_deck, calculate_*, CardAnimation, ChipAnimation, etc. - Keep as they are) ---
def create_deck():
    deck = []
    suits = ["♠", "♥", "♦", "♣"]
    ranks = list(map(str, range(2, 11))) + ["J", "Q", "K", "A"]
    for suit in suits:
        for rank in ranks:
            # Pi value for face cards
            if rank in ["J", "Q", "K"]:
                value = math.pi
            elif rank == "A":
                # Ace can be 1 or 11 - handle later during calculation if needed, start as 11
                # For simplicity in this structure, let's keep Ace as 11. Pi Blackjack might not need 1/11 rule.
                # Revisit if standard Ace rules are desired. For now, fixed value.
                value = 11 # Or maybe math.e? Let's stick to 11 for now unless Pi theme dictates otherwise.
            else:
                value = int(rank)
            deck.append({"rank": rank, "suit": suit, "value": value, "face_down": False})

    # Add the special PI card (joker) twice. Value is None until assigned.
    deck.append({"rank": "PI", "suit": "", "value": None, "face_down": False, "joker": True})
    deck.append({"rank": "PI", "suit": "", "value": None, "face_down": False, "joker": True})
    random.shuffle(deck)
    return deck

deck = create_deck()

def calculate_player_targets(num_cards):
    card_width = 60
    # Adjust spacing based on number of cards to prevent overlap
    spacing = 15 if num_cards <= 5 else 10 if num_cards <= 7 else 5
    total_width = num_cards * card_width + (num_cards - 1) * spacing
    start_x = (WIDTH - total_width) // 2
    y = HEIGHT - 200 # Player card Y position
    targets = []
    for i in range(num_cards):
        x = start_x + i * (card_width + spacing)
        targets.append((x, y))
    return targets

def calculate_dealer_target(num_cards_already_present):
    card_width = 60
    spacing = 15 # Spacing between dealer cards
    # Start placing additional cards relative to the last initial card position
    base_x, base_y = dealer_targets[1] # Position of the second (initially hidden) card
    # Calculate offset based on how many cards *beyond the initial two* are being added
    # The first *new* card (index 2) goes one space right, index 3 goes two spaces right etc.
    card_index = num_cards_already_present # e.g., if 2 cards exist, next is index 2
    offset_index = card_index - 1 # The first new card (index 2) adds 1 spacing unit offset
    new_x = base_x + offset_index * (card_width + spacing)
    return (new_x, base_y)

class CardAnimation:
    def __init__(self, start_pos, end_pos, duration, destination, card, face_down_override=None):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.duration = duration
        self.elapsed = 0
        self.destination = destination  # "player" or "dealer"
        self.card = card.copy()
        if face_down_override is not None:
            self.card["face_down"] = face_down_override

    def update(self, dt):
        self.elapsed += dt
        progress = min(self.elapsed / self.duration, 1.0)
        # Simple linear interpolation
        current_x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * progress
        current_y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * progress
        return (current_x, current_y), progress >= 1.0

class ChipAnimation:
    def __init__(self, start_pos, end_pos, duration, amount):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.duration = duration
        self.elapsed = 0
        self.amount = amount # Store amount if needed later (e.g., displaying value during anim)
    def update(self, dt):
        self.elapsed += dt
        progress = min(self.elapsed / self.duration, 1.0)
        # Simple linear interpolation
        current_x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * progress
        current_y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * progress
        return (current_x, current_y), progress >= 1.0


# Function to fully reset the game (e.g., after Game Over)
def reset_game():
    global player_coins, current_bet, bet_confirmed, game_state
    player_coins = STARTING_COINS
    current_bet = 0
    bet_confirmed = False
    reset_round() # Also resets cards, deck, etc.
    game_state = "betting" # Start back at betting

# Reset round function (keeps player coins as they are)
def reset_round():
    global deck, player_cards, dealer_cards, animation_queue, active_animation, game_state, round_result, player_pi_input, current_bet, bet_confirmed
    # Only reset round-specific variables
    deck = create_deck()
    player_cards.clear()
    dealer_cards.clear()
    # animation_queue.clear() # Clearing here might cancel animations needed for round transition visual? No, needed.
    animation_queue = []
    active_animation = None
    chip_animations.clear() # Clear any leftover chip anims
    round_result = None
    player_pi_input = ""
    current_bet = 0       # Reset bet amount for the new round
    bet_confirmed = False # Need to confirm bet again
    game_state = "betting" # Go back to betting state
    # DO NOT add initial deal animations here. They are added when the bet is confirmed.


def add_initial_deal_animations():
    global animation_queue, deck
    # Ensure the queue is clear before adding new ones
    animation_queue.clear()
    if len(deck) < 4: # Check if enough cards exist
        print("Error: Not enough cards in deck to deal.")
        # Handle this - maybe reshuffle or end game? For now, just print.
        deck = create_deck() # Simple fix: reset deck if too low

    initial_player_targets = calculate_player_targets(2)
    # Player Card 1
    card1 = deck.pop()
    animation_queue.append(CardAnimation(deck_pos, initial_player_targets[0], ANIMATION_DURATION, "player", card1, face_down_override=False))
    # Dealer Card 1 (Face Up)
    card2 = deck.pop()
    animation_queue.append(CardAnimation(deck_pos, dealer_targets[0], ANIMATION_DURATION, "dealer", card2, face_down_override=False))
    # Player Card 2
    card3 = deck.pop()
    animation_queue.append(CardAnimation(deck_pos, initial_player_targets[1], ANIMATION_DURATION, "player", card3, face_down_override=False))
    # Dealer Card 2 (Face Down)
    card4 = deck.pop()
    animation_queue.append(CardAnimation(deck_pos, dealer_targets[1], ANIMATION_DURATION, "dealer", card4, face_down_override=True))


# Auto-assign value to dealer's PI cards to maximize score without busting if possible
def auto_assign_dealer_pi():
    # First pass: calculate total excluding unassigned PI cards
    current_total = 0
    pi_card_indices = []
    for i in range(len(dealer_cards)):
        pos, card = dealer_cards[i]
        if card.get("joker", False) and card["value"] is None and not card.get("face_down", False):
            pi_card_indices.append(i)
        elif not card.get("face_down", False):
            current_total += card["value"] if card["value"] is not None else 0

    # Assign values to PI cards
    for index in pi_card_indices:
        pos, card = dealer_cards[index]
        # Try to get as close to THRESHOLD as possible without busting
        needed = THRESHOLD - current_total
        # Choose a value: simple strategy - aim for threshold, default to 1 if that busts or is <= 0
        # More complex logic could go here (e.g., based on player's hand)
        assign_val = needed
        if assign_val <= 0 or current_total + assign_val > THRESHOLD:
             assign_val = 1 # Assign a minimal value if aiming for threshold busts or is non-positive

        # Check if assigning 1 still busts (only possible if current_total is already >= THRESHOLD)
        if current_total + 1 > THRESHOLD:
             assign_val = 1 # Or perhaps assign 0? Let's stick to 1 for simplicity.

        card["value"] = assign_val
        print(f"Dealer auto-assigned PI card value: {assign_val}")
        current_total += assign_val

# --- Drawing Functions (Keep most as they are) ---
def draw_background():
    screen.fill(DARK_GREEN)
    # Optional: Draw subtle background pattern if desired
    # pi_font = pygame.font.SysFont("consolas", 28)
    # for i in range(10):
    #     for j in range(6):
    #         pi_text = pi_font.render("π", True, (0, 100 + i * 5, 0)) # Darker green
    #         screen.blit(pi_text, (100 + i * 100, 80 + j * 100))

def draw_menu_icon():
    menu_rect = pygame.Rect(30, 30, 40, 30)
    pygame.draw.rect(screen, PURPLE, menu_rect, border_radius=4)
    for i in range(3):
        pygame.draw.line(screen, WHITE, (35, 38 + i * 8), (65, 38 + i * 8), 4)
    return menu_rect

def draw_dealer_cards_placeholders():
    # Only draw if no cards are present or being animated for dealer yet?
    # Or always draw behind? Let's draw if len(dealer_cards) < 2
    if len(dealer_cards) < 2 and not any(anim.destination == 'dealer' for anim in animation_queue + ([active_animation] if active_animation else [])):
        for pos in dealer_targets:
            bg_rect = pygame.Rect(pos[0], pos[1], 60, 90)
            pygame.draw.rect(screen, (0, 80, 0), bg_rect, border_radius=5) # Darker placeholder

def draw_player_cards_placeholders():
     # Draw if player has no cards and none are animating towards player
    if not player_cards and not any(anim.destination == 'player' for anim in animation_queue + ([active_animation] if active_animation else [])):
        targets = calculate_player_targets(2)
        for pos in targets:
            bg_rect = pygame.Rect(pos[0], pos[1], 60, 90)
            pygame.draw.rect(screen, (50, 50, 50), bg_rect, 2, border_radius=5) # Outline placeholder

def draw_totals(player_total, dealer_total):
    # Player's total.
    player_label = font_large.render("YOUR TOTAL:", True, YELLOW)
    screen.blit(player_label, (50, HEIGHT // 2 - 120))
    player_circle_center = (200, HEIGHT // 2 - 20)
    pygame.draw.circle(screen, PINK, player_circle_center, 40)
    pygame.draw.circle(screen, NEON_BLUE, player_circle_center, 44, 4)
    player_total_text = font_large.render(f"{player_total:.2f}", True, BLACK) # Format to 2 decimals
    player_rect = player_total_text.get_rect(center=player_circle_center)
    screen.blit(player_total_text, player_rect)
    # Show player's PI input if needed.
    if is_pi_input_required(): # Check if input is currently needed
        input_prompt_y = player_circle_center[1] + 60
        input_text = font_small.render("Enter PI value: " + player_pi_input, True, WHITE)
        input_rect = input_text.get_rect(center=(player_circle_center[0], input_prompt_y))
        # Draw a small background box for the input prompt
        prompt_bg_rect = input_rect.inflate(10, 5)
        prompt_bg_rect.center = input_rect.center
        pygame.draw.rect(screen, BLACK, prompt_bg_rect, border_radius=4)
        pygame.draw.rect(screen, NEON_BLUE, prompt_bg_rect, 1, border_radius=4)
        screen.blit(input_text, input_rect)


    # Dealer's total.
    dealer_label = font_large.render("DEALER TOTAL:", True, YELLOW)
    screen.blit(dealer_label, (WIDTH - 350, HEIGHT // 2 - 120))
    dealer_circle_center = (WIDTH - 200, HEIGHT // 2 - 20)
    pygame.draw.circle(screen, PINK, dealer_circle_center, 40)
    pygame.draw.circle(screen, NEON_BLUE, dealer_circle_center, 44, 4)
    # Format to 2 decimals
    dealer_total_text = font_large.render(f"{dealer_total:.2f}", True, BLACK)
    dealer_rect = dealer_total_text.get_rect(center=dealer_circle_center)
    screen.blit(dealer_total_text, dealer_rect)


def draw_betting_overlay(mouse_pos):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill(OVERLAY_COLOR)
    screen.blit(overlay, (0, 0))

    bet_text = font_large.render("Place Your Bet", True, YELLOW)
    text_rect = bet_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 180)) # Moved up slightly
    screen.blit(bet_text, text_rect)

    # Display Winning Condition
    win_condition_text = font_small.render(f"Reach {WINNING_COIN_TARGET} π coins to Win!", True, CYAN)
    win_rect = win_condition_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 130)) # Below title
    screen.blit(win_condition_text, win_rect)

    coins_text = font_small.render(f"Coins: {player_coins}", True, WHITE)
    coins_rect = coins_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 80)) # Adjusted Y
    screen.blit(coins_text, coins_rect)

    current_bet_text = font_small.render(f"Current Bet: {current_bet}", True, WHITE)
    bet_rect = current_bet_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 40)) # Adjusted Y
    screen.blit(current_bet_text, bet_rect)

    instructions = font_small.render("UP/DOWN arrows to adjust bet, ENTER to confirm", True, WHITE)
    inst_rect = instructions.get_rect(center=(WIDTH//2, HEIGHT//2 + 10)) # Adjusted Y
    screen.blit(instructions, inst_rect)

    # All-In Button
    all_in_rect = pygame.Rect(WIDTH // 2 - 90, HEIGHT // 2 + 60, 180, 50) # Adjusted Y
    all_in_color = RED if all_in_rect.collidepoint(mouse_pos) else (200, 0, 0)
    if player_coins <= 0: all_in_color = (100, 100, 100) # Greyed out
    pygame.draw.rect(screen, all_in_color, all_in_rect, border_radius=10)
    all_in_text = font_medium.render("ALL IN", True, WHITE)
    all_in_text_rect = all_in_text.get_rect(center=all_in_rect.center)
    screen.blit(all_in_text, all_in_text_rect)

    return all_in_rect # Return the rect for click detection

def draw_game_won_screen():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 100, 0, 220)) # Greenish overlay for winning
    screen.blit(overlay, (0, 0))

    title_text = font_large.render("YOU WIN!", True, YELLOW)
    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80))
    screen.blit(title_text, title_rect)

    congrats_text = font_medium.render("Congratulations!", True, WHITE)
    congrats_rect = congrats_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
    screen.blit(congrats_text, congrats_rect)

    reason_text = font_small.render(f"You reached {player_coins} π coins!", True, WHITE)
    reason_rect = reason_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
    screen.blit(reason_text, reason_rect)

    restart_text = font_medium.render("Press R to Play Again", True, YELLOW)
    restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80))
    screen.blit(restart_text, restart_rect)



def draw_coin_total():
    coin_text = font_small.render(f"Coins: {player_coins}", True, WHITE)
    # Position bottom-left
    screen.blit(coin_text, (10, HEIGHT - 30))
    # Also show current bet if > 0 and not in betting phase explicitly
    if current_bet > 0 and game_state != "betting":
        bet_display_text = font_small.render(f"Bet: {current_bet}", True, YELLOW)
        screen.blit(bet_display_text, (150, HEIGHT - 30))

def draw_chip(pos):
    pygame.draw.circle(screen, YELLOW, pos, 15) # Outer circle
    pygame.draw.circle(screen, BLACK, pos, 13) # Inner circle
    chip_text = font_small.render("π", True, YELLOW) # Pi symbol
    chip_rect = chip_text.get_rect(center=pos)
    screen.blit(chip_text, chip_rect)

# No longer needed - incorporated into draw_totals
# def draw_pi_input_box():
    # ...

def is_pi_input_required():
    # Check if any player card is a Joker PI and has value None
    for item in player_cards:
        card = item["card"]
        if card.get("joker", False) and card.get("value") is None:
            return True
    return False

# --- Menu/Overlay Functions (Keep draw_menu_overlay, draw_restart_confirmation_overlay, draw_round_result) ---
def draw_menu_overlay():
    overlay_width, overlay_height = 400, 300
    overlay_x, overlay_y = 50, 50 # Position from top-left
    overlay = pygame.Surface((overlay_width, overlay_height), pygame.SRCALPHA)
    overlay.fill((50, 50, 50, 240)) # Dark semi-transparent background
    screen.blit(overlay, (overlay_x, overlay_y))

    # Simple Title
    title_text = font_medium.render("Menu", True, WHITE)
    title_rect = title_text.get_rect(center=(overlay_x + overlay_width // 2, overlay_y + 40))
    screen.blit(title_text, title_rect)

    # Options (adjust positions relative to overlay_x, overlay_y)
    home_text = font_large.render("Home", True, WHITE) # Home might quit or go to title screen TBD
    restart_text = font_large.render("Restart", True, WHITE)
    # Options might control sound, speed, etc. TBD
    options_text = font_large.render("Options", True, WHITE)

    base_y = overlay_y + 90
    spacing = 70
    home_rect = home_text.get_rect(topleft=(overlay_x + 50, base_y))
    restart_rect = restart_text.get_rect(topleft=(overlay_x + 50, base_y + spacing))
    options_rect = options_text.get_rect(topleft=(overlay_x + 50, base_y + 2 * spacing))

    # Basic Hover Effect (Optional)
    mouse_pos = pygame.mouse.get_pos()
    if home_rect.collidepoint(mouse_pos): pygame.draw.rect(screen, PURPLE, home_rect.inflate(10, 2), 1)
    if restart_rect.collidepoint(mouse_pos): pygame.draw.rect(screen, PURPLE, restart_rect.inflate(10, 2), 1)
    if options_rect.collidepoint(mouse_pos): pygame.draw.rect(screen, PURPLE, options_rect.inflate(10, 2), 1)

    screen.blit(home_text, home_rect)
    screen.blit(restart_text, restart_rect)
    screen.blit(options_text, options_rect)

    return {"home": home_rect, "restart": restart_rect, "options": options_rect}


def draw_restart_confirmation_overlay():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill(OVERLAY_COLOR) # Use semi-transparent overlay
    screen.blit(overlay, (0, 0))
    confirm_text = font_large.render("Confirm Restart? (Y / N)", True, WHITE)
    text_rect = confirm_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(confirm_text, text_rect)


def draw_round_result(result_text):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200)) # Darker overlay for results
    screen.blit(overlay, (0, 0))

    result_render = font_large.render(result_text, True, YELLOW)
    result_rect = result_render.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
    screen.blit(result_render, result_rect)

    # Check if game is over due to coins
    if player_coins <= 0:
        prompt = font_small.render("Game Over! Press R to Restart", True, WHITE)
    else:
        prompt = font_small.render("Press SPACE to start next round", True, WHITE)

    prompt_rect = prompt.get_rect(center=(WIDTH//2, HEIGHT//2 + 20))
    screen.blit(prompt, prompt_rect)

# New Game Over Screen function
def draw_game_over_screen():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill(GAMEOVER_OVERLAY_COLOR) # Use the more opaque overlay
    screen.blit(overlay, (0, 0))

    title_text = font_large.render("GAME OVER", True, RED)
    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
    screen.blit(title_text, title_rect)

    reason_text = font_small.render("You ran out of π coins!", True, WHITE)
    reason_rect = reason_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(reason_text, reason_rect)

    restart_text = font_medium.render("Press R to Restart", True, YELLOW)
    restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))
    screen.blit(restart_text, restart_rect)


# --- Calculation Functions (Keep as they are) ---
def calculate_player_total():
    total = 0
    num_aces = 0 # Not used currently as Ace=11 fixed, but structure is here if needed
    for item in player_cards:
        card = item["card"]
        if not card.get("face_down", False):
            value = card.get("value")
            if value is not None:
                total += value
                # if card["rank"] == "A": num_aces += 1 # For Ace 1/11 logic

    # Basic Ace 1/11 logic (if implemented)
    # while total > THRESHOLD and num_aces > 0:
    #     total -= 10 # Change an Ace from 11 to 1
    #     num_aces -= 1
    return total

def calculate_dealer_total(reveal_all=False):
    total = 0
    num_aces = 0 # Not used currently
    for pos, card in dealer_cards:
        # Only count visible cards unless reveal_all is True (for end of round)
        if not card.get("face_down", False) or reveal_all:
            value = card.get("value")
            if value is not None:
                total += value
                # if card["rank"] == "A": num_aces += 1

    # Ace logic (if implemented)
    # while total > THRESHOLD and num_aces > 0:
    #     total -= 10
    #     num_aces -= 1
    return total

# --- Card Drawing (Keep as is) ---
def draw_card(card, pos):
    card_width, card_height = 60, 90
    card_rect = pygame.Rect(pos[0], pos[1], card_width, card_height)
    border_radius = 5

    if card.get("face_down", False):
        # Draw face down card (e.g., purple with outline)
        pygame.draw.rect(screen, PURPLE, card_rect, border_radius=border_radius)
        pygame.draw.rect(screen, NEON_BLUE, card_rect, 2, border_radius=border_radius)
        # Optional: Add a symbol like π to the back
        pi_text = font_large.render("π", True, WHITE)
        pi_rect = pi_text.get_rect(center=card_rect.center)
        screen.blit(pi_text, pi_rect)
    else:
        # Draw face up card
        pygame.draw.rect(screen, WHITE, card_rect, border_radius=border_radius) # White background
        pygame.draw.rect(screen, BLACK, card_rect, 1, border_radius=border_radius) # Thin black border

        rank = card["rank"]
        suit = card["suit"]
        value = card["value"] # Get assigned value for display?

        # Determine text color (Red for Hearts/Diamonds, Black otherwise)
        text_color = RED if suit in ["♥", "♦"] else BLACK

        # Special display for Joker PI card
        if card.get("joker", False):
            display_text = "PI"
            # Maybe show assigned value if it exists?
            # if value is not None: display_text += f"({value:.1f})" # Example: PI(3.1)
            text_color = PURPLE # Make PI card purple text
        else:
            display_text = rank # Just show rank J, Q, K, A, 2-10

        # Render Rank/Suit
        rank_font = font_small # Font for rank/suit
        rank_surf = rank_font.render(display_text, True, text_color)
        suit_surf = rank_font.render(suit, True, text_color)

        # Position rank/suit (top-left and bottom-right corners)
        screen.blit(rank_surf, (card_rect.left + 5, card_rect.top + 5))
        screen.blit(suit_surf, (card_rect.left + 5, card_rect.top + 20))

        # Optional: Draw rotated text on bottom right? More complex. Stick to top-left.

        # Optional: Draw simple representation in center (e.g., just rank for number cards)
        # center_font = font_large
        # center_surf = center_font.render(rank, True, text_color)
        # center_rect = center_surf.get_rect(center=card_rect.center)
        # screen.blit(center_surf, center_rect)


def draw_all_cards():
    # Draw dealer cards first (so player cards are on top if overlapping slightly)
    for pos, card in dealer_cards:
        draw_card(card, pos)
    # Draw player cards
    for item in player_cards:
        draw_card(item["card"], item["pos"])

# --- Game Logic Functions ---
def dealer_turn():
    global game_state, round_result, player_coins, deck # Added player_coins
    print("Dealer's turn begins.")

    # Reveal the hidden card first
    revealed_card = False
    for i in range(len(dealer_cards)):
        pos, card = dealer_cards[i]
        if card.get("face_down", False):
            card["face_down"] = False
            revealed_card = True
            # Optional: Add a brief pause or animation for reveal?
            # For now, just flip instantly.
            print(f"Dealer reveals: {card['rank']}{card['suit']}")
            break

    # Auto-assign any PI cards *after* revealing
    auto_assign_dealer_pi()
    dealer_total = calculate_dealer_total(reveal_all=True) # Calculate total with all cards visible
    print(f"Dealer initial total (after reveal/PI): {dealer_total:.2f}")

    if not deck: # Now accesses the global deck correctly
        print("Error: Deck empty during dealer turn. Reshuffling.")
        deck = create_deck() # Assigns to the global deck correctly
        
    # Dealer hits based on rules (e.g., hit on soft 17, stand on hard 17+)
    # Using simple rule: hit if total < 17
    while dealer_total < 17:
        print("Dealer hits.")
        if not deck:
            print("Error: Deck empty during dealer turn.")
            deck = create_deck() # Reshuffle if empty mid-turn

        new_card = deck.pop()
        # Calculate target position for the new card
        new_target = calculate_dealer_target(len(dealer_cards))

        # Add animation for the new card deal
        animation_queue.append(CardAnimation(deck_pos, new_target, ANIMATION_DURATION, "dealer", new_card, face_down_override=False))

        # Important: Add the card to dealer_cards *immediately* conceptually,
        # but the animation will handle drawing it moving.
        # The state needs to know the card exists for future calculations or turn logic.
        # However, adding it here means calculate_dealer_total needs care during animation.
        # Let's add it *after* the animation finishes in the main loop instead.
        # For the loop condition, we need to predict the total *if* the card is drawn.
        # This is tricky. Let's stick to adding the animation and letting the main loop handle state updates.
        # The dealer_turn function will be called again *after* the animation finishes if needed.
        game_state = "dealing" # Set state to dealing to process the animation
        return # Exit function, let animation play out

    # If dealer stands (total >= 17)
    print(f"Dealer stands with total: {dealer_total:.2f}")
    game_state = "round_end"
    determine_winner() # Determine winner now that dealer's turn is complete


# Modified determine_winner to check for win condition
def determine_winner():
    global round_result, player_coins, current_bet, game_state # Added game_state
    player_total = calculate_player_total()
    dealer_total = calculate_dealer_total(reveal_all=True)

    print(f"Determining winner: Player={player_total:.2f}, Dealer={dealer_total:.2f}")
    payout_multiplier = 0 # 0 for loss, 1 for push, 2 for win

    if player_total > THRESHOLD:
        round_result = "Player Busts! Dealer Wins!"
        payout_multiplier = 0
    elif dealer_total > THRESHOLD:
        round_result = "Dealer Busts! Player Wins!"
        payout_multiplier = 2
    elif player_total > dealer_total:
        round_result = "Player Wins!"
        payout_multiplier = 2
    elif dealer_total > player_total:
        round_result = "Dealer Wins!"
        payout_multiplier = 0
    else: # Tie (Push)
        round_result = "Push! It's a Tie!"
        payout_multiplier = 1

    # Calculate new coin total
    player_coins += current_bet * payout_multiplier
    print(f"Round Result: {round_result}. Player Coins: {player_coins}")

    # --- Check for Win/Loss Conditions AFTER payout ---
    # Prioritize checking for the win condition
    if player_coins >= WINNING_COIN_TARGET:
        print(f"Player reached {player_coins} coins! Game Won!")
        # Set state to game_won, the round_result overlay will show briefly,
        # then the main loop will switch to drawing the game_won screen.
        game_state = "game_won"
        # Optionally override round_result here if you want the win screen immediately
        # round_result = None # Or set a specific "Game Won!" result?
    # If not won, check if player is out of coins
    elif player_coins <= 0:
         print("Player has run out of coins.")
         # The state change to game_over will be handled by the key press logic
         # in the round_end state, ensuring the result is displayed first.

def draw_buttons(mouse_pos, mouse_click, buttons_active):
    global game_state, player_cards, deck # Added globals

    button_width, button_height = 180, 60
    button_y = HEIGHT - 100 # Y position for both buttons
    hit_x = WIDTH // 4 - button_width // 2 # Position Hit button left-center
    stand_x = 3 * WIDTH // 4 - button_width // 2 # Position Stand button right-center

    hit_rect = pygame.Rect(hit_x, button_y, button_width, button_height)
    stand_rect = pygame.Rect(stand_x, button_y, button_width, button_height)

    # Define colors based on active state and hover
    hit_base_color = PINK
    hit_hover_color = (255, 150, 200) # Lighter pink
    hit_inactive_color = (150, 50, 150) # Darker/greyed pink

    stand_base_color = PURPLE
    stand_hover_color = (180, 0, 180) # Lighter purple
    stand_inactive_color = (70, 0, 70) # Darker/greyed purple

    # Determine current colors
    if buttons_active:
        hit_color = hit_hover_color if hit_rect.collidepoint(mouse_pos) else hit_base_color
        stand_color = stand_hover_color if stand_rect.collidepoint(mouse_pos) else stand_base_color
    else:
        hit_color = hit_inactive_color
        stand_color = stand_inactive_color

    # Draw Hit Button
    pygame.draw.rect(screen, hit_color, hit_rect, border_radius=12)
    hit_text = font_large.render("HIT", True, BLACK)
    hit_text_rect = hit_text.get_rect(center=hit_rect.center)
    screen.blit(hit_text, hit_text_rect)

    # Draw Stand Button
    pygame.draw.rect(screen, stand_color, stand_rect, border_radius=12)
    stand_text = font_large.render("STAND", True, YELLOW)
    stand_text_rect = stand_text.get_rect(center=stand_rect.center)
    screen.blit(stand_text, stand_text_rect)

    # Process clicks ONLY if buttons are active
    if buttons_active and mouse_click:
        if hit_rect.collidepoint(mouse_pos):
            print("HIT button clicked")
            if game_state == "idle": # Double check state just in case
                # --- Hit Logic ---
                if not deck:
                    print("Error: Deck empty when hitting.")
                    deck = create_deck() # Reshuffle

                new_card = deck.pop()
                # Recalculate targets to potentially make space
                new_targets = calculate_player_targets(len(player_cards) + 1)
                # Update existing card positions smoothly? Or just snap? Let's snap for simplicity.
                for i in range(len(player_cards)):
                    player_cards[i]["pos"] = new_targets[i]

                # Add animation for the new card
                animation_queue.append(CardAnimation(deck_pos, new_targets[-1], ANIMATION_DURATION, "player", new_card, face_down_override=False))
                game_state = "dealing" # Process the card animation
                print("Player hits, dealing card.")

        elif stand_rect.collidepoint(mouse_pos):
            print("STAND button clicked")
            if game_state == "idle":
                # --- Stand Logic ---
                game_state = "dealer_turn" # Transition to dealer's turn
                dealer_turn() # Start the dealer's logic (reveal card, then potentially hit)
                print("Player stands. Dealer's turn.")

    # Return rects if needed elsewhere, otherwise not necessary
    # return hit_rect, stand_rect

# ==============================================================================
# Main Game Loop
# ==============================================================================
# ==============================================================================
# Main Game Loop
# ==============================================================================
def main():
    global menu_overlay_active, restart_confirmation, active_animation, game_state
    global player_cards, dealer_cards, round_result, player_pi_input
    global player_coins, current_bet, chip_animations, bet_confirmed, deck

    running = True
    all_in_button_rect = None # To store the rect from the drawing function

    while running:
        dt = clock.tick(FPS) / 1000.0 # Delta time in seconds
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False # Reset mouse click status each frame

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left mouse button
                    mouse_click = True

            # --- Keyboard Input Handling based on State ---
            if event.type == pygame.KEYDOWN:
                # Menu / Restart Confirmation Handling (Can happen in most states)
                if restart_confirmation:
                    if event.key == pygame.K_y:
                        print("Restart confirmed")
                        restart_confirmation = False
                        menu_overlay_active = False
                        reset_game() # Full reset
                    elif event.key == pygame.K_n:
                        print("Restart cancelled")
                        restart_confirmation = False
                        # menu_overlay_active = False # Keep menu closed maybe?
                # Game Over Restart
                elif game_state == "game_over":
                    if event.key == pygame.K_r:
                        print("Restarting game from Game Over screen.")
                        reset_game() # Full reset
                # Add handler for Game Won state
                elif game_state == "game_won":
                    if event.key == pygame.K_r:
                        print("Restarting game from Win Screen.")
                        reset_game() # Full reset

                # Betting State Input
                elif game_state == "betting":
                    if event.key == pygame.K_UP:
                        if current_bet < player_coins:
                            current_bet += 1 # Allow holding key due to set_repeat
                    elif event.key == pygame.K_DOWN:
                        if current_bet > 0:
                            current_bet -= 1
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        if current_bet > 0 and current_bet <= player_coins and not bet_confirmed:
                            player_coins -= current_bet
                            # Animate chip from coin total area to bet area
                            coin_area_pos = (60, HEIGHT - 20)
                            bet_area_pos = (WIDTH // 2, HEIGHT // 2 + 80) # Center below bet text
                            chip_animations.append(ChipAnimation(coin_area_pos, bet_area_pos, ANIMATION_DURATION / 2, current_bet))
                            bet_confirmed = True
                            print(f"Bet confirmed: {current_bet}. Waiting for chip animation.")

                # Player Turn (Idle State) - PI Input
                elif game_state == "idle" and is_pi_input_required():
                    if event.unicode.isdigit(): # Use unicode for digits 0-9
                        player_pi_input += event.unicode
                    elif event.key == pygame.K_BACKSPACE:
                        player_pi_input = player_pi_input[:-1]
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        if player_pi_input: # Check if input is not empty
                            try:
                                val = int(player_pi_input)
                                if val > 0:
                                    # Find the first unassigned PI card and assign value
                                    for item in player_cards:
                                        card = item["card"]
                                        if card.get("joker", False) and card.get("value") is None:
                                            card["value"] = val
                                            print(f"Player assigned PI card value: {val}")
                                            player_pi_input = "" # Clear input field

                                            # Check for immediate bust after assignment
                                            player_total = calculate_player_total()
                                            if player_total > THRESHOLD:
                                                print("Player busts after assigning PI value.")
                                                game_state = "round_end"
                                                determine_winner() # This will set result to bust

                                            # If not bust, check if more PI input is needed
                                            elif not is_pi_input_required():
                                                # If no more input needed, game stays idle for Hit/Stand
                                                print("PI input complete. Awaiting player action.")
                                            break # Exit loop after assigning to one card
                                    else:
                                        # This case shouldn't be reachable if is_pi_input_required was true
                                        player_pi_input = ""
                                else:
                                    print("PI value must be positive.")
                                    player_pi_input = "" # Clear invalid input
                            except ValueError:
                                print("Invalid input. Please enter a number.")
                                player_pi_input = "" # Clear invalid input

                # Round End State - Proceed to next round or handle Game Over/Win
                elif game_state == "round_end":
                    # Check Win/Loss status BEFORE checking keys
                    # Note: determine_winner might have already set game_state to game_won/game_over
                    # This check handles the key press *after* the result is shown.
                    if player_coins >= WINNING_COIN_TARGET:
                        # If game is already won, 'R' should restart
                        if event.key == pygame.K_r:
                           print("Restarting game after Win.")
                           reset_game()
                           continue # Skip Space check
                    elif player_coins <= 0:
                        # If game is over (no coins), 'R' should restart
                        if event.key == pygame.K_r:
                            print("Restarting game from Round End (Game Over).")
                            reset_game()
                            continue # Skip Space check
                    # If not won/lost, Space proceeds
                    elif event.key == pygame.K_SPACE:
                        print("Starting new round.")
                        reset_round()

        # --- Handle Mouse Clicks Outside Event Loop (for buttons) ---
        # Menu Icon Click
        menu_rect = draw_menu_icon() # Get rect while drawing
        if mouse_click and menu_rect.collidepoint(mouse_pos) and not restart_confirmation:
            menu_overlay_active = not menu_overlay_active
            if menu_overlay_active: # Reset confirmation if opening menu
                restart_confirmation = False

        # All-In Button Click (Only in Betting state)
        if game_state == "betting" and all_in_button_rect is not None:
             if mouse_click and all_in_button_rect.collidepoint(mouse_pos):
                 if player_coins > 0 and not bet_confirmed:
                     print("All In clicked!")
                     current_bet = player_coins # Bet all coins
                     player_coins = 0 # Coins are now committed to the bet
                     # Animate chip
                     coin_area_pos = (60, HEIGHT - 20)
                     bet_area_pos = (WIDTH // 2, HEIGHT // 2 + 80)
                     chip_animations.append(ChipAnimation(coin_area_pos, bet_area_pos, ANIMATION_DURATION / 2, current_bet))
                     bet_confirmed = True
                     print(f"Bet confirmed (ALL IN): {current_bet}. Waiting for chip animation.")


        # --- Update and Draw Section ---
        draw_background()

        # Update & Draw Chip Animations (Run always if they exist)
        if chip_animations:
            active_chips = []
            for chip in chip_animations:
                pos, done = chip.update(dt)
                draw_chip(pos)
                if not done:
                    active_chips.append(chip)
                # else: print("Chip animation finished.") # Debug
            chip_animations = active_chips

        # --- Game State Specific Drawing & Logic ---
        if game_state == "betting":
            all_in_button_rect = draw_betting_overlay(mouse_pos) # Draw and get rect
            draw_coin_total()
            # Transition to dealing after bet confirmed and chip animation done
            if bet_confirmed and not chip_animations:
                print("Chip animation complete. Transitioning to dealing.")
                add_initial_deal_animations()
                game_state = "dealing"
                # bet_confirmed = False # Resetting bet_confirmed happens in reset_round

        elif game_state == "dealing" or game_state == "idle" or game_state == "dealer_turn":
            player_total = calculate_player_total()
            dealer_total = calculate_dealer_total(reveal_all=False)
            draw_totals(player_total, dealer_total)
            draw_coin_total()

            # Update & Draw Card Animations
            if active_animation is None and animation_queue:
                active_animation = animation_queue.pop(0)

            if active_animation:
                pos, done = active_animation.update(dt)
                draw_card(active_animation.card, pos)
                if done:
                    # Store info before clearing animation
                    card_destination = active_animation.destination
                    card_info = active_animation.card

                    # Add card to the correct hand
                    if card_destination == "player":
                        player_cards.append({"pos": active_animation.end_pos, "card": card_info})
                        # Optional print: print(f"Player receives: {card_info['rank']}{card_info['suit']}")
                    elif card_destination == "dealer":
                        dealer_cards.append((active_animation.end_pos, card_info))
                        # Optional print: print(f"Dealer receives card (hidden: {card_info.get('face_down', False)})")

                    active_animation = None # Animation complete

                    # --- Post-Animation State Checks ---
                    # Only perform checks if the animation queue is NOW empty
                    if not animation_queue:
                        # Capture the state *at the moment the queue became empty*
                        state_when_queue_emptied = game_state

                        # Scenario 1: We were 'dealing' (Initial Deal OR Player Hit finished)
                        if state_when_queue_emptied == "dealing":
                            print("Dealing sequence finished.")
                            player_total = calculate_player_total()
                            # Check for immediate player bust
                            if player_total > THRESHOLD:
                                print("Player busts.")
                                game_state = "round_end"
                                determine_winner()
                            # Check if PI input is now required
                            elif is_pi_input_required():
                                game_state = "idle" # Wait for player PI input
                                print("PI card dealt, waiting for input.")
                            # Otherwise, the initial deal / player hit is complete.
                            # It is NOW the player's turn to Hit or Stand.
                            else:
                                game_state = "idle"
                                print("Player turn (Idle).")

                        # Scenario 2: We were in the 'dealer_turn' (Dealer Hit finished)
                        elif state_when_queue_emptied == "dealer_turn":
                             # The dealer just finished receiving a card they were forced to take.
                             # We MUST re-evaluate the dealer's hand immediately.
                             print("Dealer hit animation finished. Re-evaluating dealer.")
                             dealer_turn() # This function will decide the next step (hit again or stand/end round)

                    # If the animation queue is NOT empty, the loop continues processing.
                    # The game state ('dealing' or 'dealer_turn') remains as it was.

            # Draw static cards (dealer first, then player)
            draw_all_cards()

            # Draw Hit/Stand buttons if applicable
            # Buttons active only in 'idle' state, when no PI input needed, and no overlays active
            buttons_active = (game_state == "idle" and
                              not is_pi_input_required() and
                              not menu_overlay_active and
                              not restart_confirmation)
            draw_buttons(mouse_pos, mouse_click, buttons_active)

        elif game_state == "round_end":
            # Draw the final hands, totals, etc.
            player_total = calculate_player_total()
            dealer_total = calculate_dealer_total(reveal_all=True) # Show final dealer hand
            draw_totals(player_total, dealer_total)
            draw_all_cards()
            draw_coin_total()
            # Draw the result overlay - This will show briefly even if the state changed
            # to game_won/game_over in determine_winner. The *next* frame will draw the final screen.
            if round_result:
                draw_round_result(round_result)

        elif game_state == "game_over":
            draw_game_over_screen()

        # Add drawing for the new game_won state
        elif game_state == "game_won":
            draw_game_won_screen()


        # --- Overlays (Menu, Restart Confirmation) ---
        # These are drawn on top of game states (except maybe game over/won)
        if menu_overlay_active and not restart_confirmation:
            option_rects = draw_menu_overlay()
            if mouse_click: # Handle menu clicks
                if option_rects["home"].collidepoint(mouse_pos):
                    print("Home option clicked - Action TBD (e.g., quit)")
                    # running = False # Example action
                    menu_overlay_active = False
                elif option_rects["restart"].collidepoint(mouse_pos):
                    print("Restart option selected")
                    restart_confirmation = True
                    menu_overlay_active = False 
                elif option_rects["options"].collidepoint(mouse_pos):
                    print("Options option clicked - Action TBD")
                    menu_overlay_active = False

        if restart_confirmation:
            draw_restart_confirmation_overlay()


        pygame.display.flip()

    pygame.quit()
    sys.exit()
    
if __name__ == "__main__":
    main()