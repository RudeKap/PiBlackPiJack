
# Pi Blackjack UI

**Pi Blackjack UI** is a Python game built with Pygame that reimagines classic blackjack with a unique twist inspired by π (pi). In this game, cards are imbued with the number π, betting uses a coin system where the win condition is themed around reaching 314 (or any π‑related value), and special mechanics such as PI card input and unique winning conditions (like "PI found!" when specific cards are drawn) add creative flair.

## Overview

This project blends elements of blackjack with innovative, π-themed mechanics. Key aspects include:

- **Card Game with a Twist:**  
  Cards have unique values (e.g., face cards are valued as π) and special PI cards allow the player to input a custom positive integer.

- **Betting System:**  
  Players start with a coin total and place bets using a π-themed betting interface. Poker chip animations simulate chips sliding onto the table.

- **Dynamic Game States:**  
  The game manages several states (betting, dealing, idle, dealer turn, round end) to provide a smooth gameplay experience.

- **Special Winning Conditions:**  
  For example, if the player’s first three cards are 3, A, and 4 (in that order), they instantly win with a "PI found!" message.

## Features

- **PvE Gameplay:**  
  Single-player blackjack with a twist using π-based mechanics.

- **Betting Interface:**  
  A dedicated betting phase where players adjust and confirm bets using keyboard inputs (UP/DOWN arrows and ENTER).

- **Chip Animations:**  
  Visual chip animations slide from the coin display to the table when bets are placed, reinforcing the π theme.

- **PI Card Input:**  
  When a PI card (joker) appears in the player's hand without an assigned value, a prompt appears for the player to enter a custom value.

- **Special Conditions & Quick Wins:**  
  Specific card sequences (e.g., 3, A, 4) trigger instant wins with a unique message.

## How to Play

1. **Betting Phase:**  
   - When the game starts, you’ll see a "Place Your Bet" screen.  
   - Use the UP and DOWN arrow keys to adjust your bet.  
   - Press ENTER to confirm your bet. A chip animation will slide from the coin area to the table.

2. **Gameplay:**  
   - Once betting is complete, the game deals cards with smooth animations.  
   - Use the HIT and STAND buttons (clickable on the screen) to play your hand.
   - If a PI card appears in your hand, an input box will prompt you to enter a positive integer value.
   - Special winning conditions may trigger based on your card sequence or if your total exceeds the threshold.

3. **Winning & Losing:**  
   - Your goal is to beat the dealer while keeping your total below the bust threshold (set to π*7).  
   - Winning rounds add to your coin total, and if you reach 314 coins, you win the game!

## Installation & Setup

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/<your-username>/pi_blackjack.git
   cd pi_blackjack
   ```

2. **Set Up a Virtual Environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

   *If you don't have a requirements.txt, ensure you install at least:*

   ```bash
   pip install pygame
   ```

4. **Run the Project:**

   ```bash
   python main.py
   ```

## Future Enhancements

- **Enhanced Betting Mechanics:**  
  Add multiple chip denominations and more complex betting options.

- **Improved Animations:**  
  More detailed chip and card animations with easing functions and sound effects.

- **Multiplayer Support:**  
  Extend the game to support multiplayer or online play.

- **Advanced Dealer AI:**  
  Refine the dealer’s logic for a more challenging game experience.

## License

*(Include license information here if applicable.)*
