"""
Rummy Game Engine for RummyVision

This server handles the game logic and strategy suggestions. Uses Monte Carlo
simulation to evaluate different discard options and suggest the best move.

The algorithm simulates random draws from the remaining deck and tracks how
each potential discard affects the hand's deadwood score. Not perfect, but
it works pretty well in practice - good enough to give useful advice.

TODO: Could add more sophisticated heuristics, like considering opponent's
likely discards or tracking card probabilities more carefully
TODO: Maybe add support for different Rummy variants (Gin Rummy, etc.)
"""

import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Tuple, Set, Optional
import collections
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Rummy Game Engine",
    description="Monte Carlo simulation engine for Rummy game strategy",
    version="1.0.0"
)

# Add CORS middleware for iOS app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Rummy Logic ---
# Standard 52-card deck configuration
# These constants define the card system we're working with

SUITS = ['hearts', 'diamonds', 'clubs', 'spades']
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
RANK_VALUES = {r: i+1 for i, r in enumerate(RANKS)}  # For ordering/sequencing (A=1, K=13)

# Deadwood scoring - face cards and 10s are worth 10, Ace is 1, others are face value
# This is standard Rummy scoring - lower deadwood is better
# Deadwood = sum of unmatched card values
DEADWOOD_VALUES = {r: min(i+1, 10) for i, r in enumerate(RANKS)}
DEADWOOD_VALUES['J'] = 10  # Face cards are worth 10
DEADWOOD_VALUES['Q'] = 10
DEADWOOD_VALUES['K'] = 10
DEADWOOD_VALUES['A'] = 1  # Ace is always 1 in deadwood (lowest value)

class SuggestRequest(BaseModel):
    my_hand: List[str] = Field(..., min_length=1, description="List of cards in format 'Rank-Suit'")
    visible: List[str] = Field(default_factory=list, description="Known cards (discard pile, etc.)")
    trials: int = Field(default=200, ge=50, le=2000, description="Number of Monte Carlo trials")
    max_draws: int = Field(default=5, ge=1, le=10, description="Maximum number of draws to simulate")
    
    @field_validator('my_hand')
    @classmethod
    def validate_hand(cls, v):
        if len(v) > 13:
            raise ValueError("Hand cannot have more than 13 cards")
        if len(v) < 1:
            raise ValueError("Hand must have at least 1 card")
        return v

class DiscardSuggestion(BaseModel):
    card: str
    win_probability: float = Field(ge=0.0, le=1.0, description="Probability of winning after discarding this card")
    expected_deadwood: float = Field(description="Expected deadwood score after discarding")
    confidence: str = Field(description="Confidence level: high, medium, or low")

class SuggestResponse(BaseModel):
    suggestions: List[DiscardSuggestion]
    current_deadwood: float
    message: Optional[str] = None

def parse_card(card_str: str) -> Optional[Tuple[int, str]]:
    """
    Parses 'Rank-Suit' string into (rank_val, suit).
    
    Expected format: "A-hearts", "K-spades", "10-diamonds", etc.
    Returns None if format is invalid (wrong format, unknown rank/suit).
    
    This is used throughout to convert string representations to internal format.
    """
    try:
        parts = card_str.split('-')
        if len(parts) != 2:
            return None
        rank, suit = parts[0].strip(), parts[1].strip()
        rank_val = RANK_VALUES.get(rank, 0)
        if rank_val == 0 or suit not in SUITS:
            return None
        return (rank_val, suit)
    except Exception as e:
        logger.debug(f"Error parsing card '{card_str}': {e}")
        return None

def build_deck() -> List[str]:
    """
    Builds a standard 52-card deck.
    
    Returns list of card strings in format "Rank-Suit".
    Simple function but useful for building the full deck when we need to
    figure out what cards are still unknown.
    """
    deck = []
    for s in SUITS:
        for r in RANKS:
            deck.append(f"{r}-{s}")
    return deck

def find_melds(parsed_hand: List[Tuple[int, str]]) -> Tuple[Set[int], List[List[Tuple[int, str]]]]:
    """
    Finds all possible melds (sets and runs) in the hand.
    
    Returns (matched_indices, list_of_melds).
    
    A "meld" is either:
    - Set: 3+ cards of same rank, different suits (e.g., 3 Kings of different suits)
    - Run: 3+ consecutive cards of same suit (e.g., 5-6-7 of hearts)
    
    This uses a greedy approach - finds sets first, then runs from remaining cards.
    Not optimal (could find better combinations), but fast and works well enough for
    our purposes. The optimal solution would require more complex algorithms.
    
    TODO: Could implement optimal melding using dynamic programming or backtracking
    TODO: Handle edge cases like A-2-3 runs (Ace can be low or high)
    """
    if not parsed_hand:
        return set(), []
    
    # Sort by rank for easier processing
    sorted_hand = sorted(enumerate(parsed_hand), key=lambda x: (x[1][0], x[1][1]))
    
    matched_indices = set()  # Track which cards are already in melds
    melds = []
    
    # 1. Find Sets (3 or 4 of same rank, different suits)
    # Group cards by rank first - makes it easier to find sets
    rank_groups = collections.defaultdict(list)
    for idx, (rank, suit) in sorted_hand:
        rank_groups[rank].append((idx, suit))
    
    for rank, cards in rank_groups.items():
        if len(cards) >= 3:
            # Check for valid set (must have different suits)
            # Can't have a set with duplicate suits
            suits_in_set = set(suit for _, suit in cards)
            if len(suits_in_set) >= 3:
                # Take up to 4 cards of different suits (max set size)
                # We want the best set possible, so we take different suits
                used_suits = set()
                set_cards = []
                for idx, suit in cards:
                    if suit not in used_suits:
                        set_cards.append((idx, (rank, suit)))
                        used_suits.add(suit)
                        if len(set_cards) >= 4:  # Max 4 cards in a set (one per suit)
                            break
                if len(set_cards) >= 3:  # Minimum 3 for a valid set
                    melds.append([card for _, card in set_cards])
                    for idx, _ in set_cards:
                        matched_indices.add(idx)
    
    # 2. Find Runs (3+ consecutive same suit)
    # Only look at cards not already in sets (can't use same card twice)
    suit_groups = collections.defaultdict(list)
    for idx, (rank, suit) in sorted_hand:
        if idx not in matched_indices:
            suit_groups[suit].append((idx, rank))
    
    for suit, cards in suit_groups.items():
        if len(cards) < 3:  # Need at least 3 cards for a run
            continue
        
        # Sort by rank to find sequences - makes it easier to spot consecutive cards
        cards.sort(key=lambda x: x[1])
        
        # Find consecutive sequences - walk through sorted cards and group consecutive ones
        sequences = []
        current_seq = [cards[0]]
        
        for i in range(1, len(cards)):
            if cards[i][1] == cards[i-1][1] + 1:  # Consecutive rank (e.g., 5 then 6)
                current_seq.append(cards[i])
            else:
                # End of current sequence, save if long enough
                if len(current_seq) >= 3:
                    sequences.append(current_seq)
                current_seq = [cards[i]]  # Start new sequence
        
        # Don't forget the last sequence (edge case)
        if len(current_seq) >= 3:
            sequences.append(current_seq)
        
        # Add sequences to melds
        for seq in sequences:
            run_cards = [(idx, (rank, suit)) for idx, rank in seq]
            melds.append([card for _, card in run_cards])
            for idx, _ in run_cards:
                matched_indices.add(idx)
    
    return matched_indices, melds

def calculate_deadwood(hand: List[str]) -> float:
    """
    Calculates deadwood points (unmatched cards) using optimal melding.
    
    Deadwood = sum of point values of cards not in any meld.
    Lower is better - goal is to minimize deadwood. A hand with 0 deadwood
    means all cards are in melds (you can go out).
    
    This is the core metric we use to evaluate hand quality.
    """
    parsed_hand = [parse_card(c) for c in hand if parse_card(c)]
    if not parsed_hand:
        return 0.0
    
    # Find all melds to determine which cards are "matched"
    # Cards in melds don't count toward deadwood
    matched_indices, _ = find_melds(parsed_hand)
    
    # Sum up points for unmatched cards
    # These are the cards that count against you
    score = 0.0
    for i, (rank, suit) in enumerate(parsed_hand):
        if i not in matched_indices:
            rank_str = RANKS[rank - 1]  # Convert rank value back to rank string
            score += DEADWOOD_VALUES.get(rank_str, 10)  # Default to 10 if something goes wrong
    
    return score

def simulate_game(hand: List[str], unknown_deck: List[str], trials: int = 100, max_draws: int = 5) -> Tuple[float, float]:
    """
    Simulates random draws to see how hand improves.
    
    Uses Monte Carlo simulation - randomly draws cards and tries different
    discard strategies to see which works best. The idea is to simulate many
    possible futures and see what happens on average.
    
    Returns (average_deadwood, improvement_probability).
    
    Args:
        hand: Current hand (list of card strings)
        unknown_deck: Cards we haven't seen yet (what's left in the deck)
        trials: Number of simulation runs (more = more accurate but slower)
        max_draws: Max cards to draw in each simulation (how far ahead to look)
    
    TODO: Could make this smarter by tracking card probabilities instead of
    pure random draws, but random works surprisingly well for this use case.
    TODO: Maybe add opponent modeling - simulate what they might discard
    """
    if not unknown_deck:
        # No unknown cards, can't improve
        current_deadwood = calculate_deadwood(hand)
        return current_deadwood, 0.0
    
    total_deadwood = 0.0
    improvements = 0  # Count how many trials resulted in improvement
    initial_deadwood = calculate_deadwood(hand)
    
    # Run multiple trials to get average outcome
    # More trials = more accurate, but slower
    for _ in range(trials):
        # Shuffle remaining deck for this trial - simulate random draws
        deck_copy = unknown_deck.copy()
        random.shuffle(deck_copy)
        
        # Simulate drawing and discarding cards
        current_hand = hand.copy()
        best_deadwood = initial_deadwood
        
        # Try drawing up to max_draws cards
        # This simulates looking ahead a few turns
        for draw_num in range(min(max_draws, len(deck_copy))):
            # Draw a card from the shuffled deck
            drawn = deck_copy[draw_num]
            current_hand.append(drawn)
            
            # Try discarding each card to find the best resulting hand
            # Greedy approach - always discard what gives best immediate result
            # Could be smarter, but this is fast and works reasonably well
            best_after_draw = float('inf')
            best_discard_card = None
            
            for card_to_try_discarding in current_hand:
                test_hand = [c for c in current_hand if c != card_to_try_discarding]
                dw = calculate_deadwood(test_hand)
                if dw < best_after_draw:
                    best_after_draw = dw
                    best_discard_card = card_to_try_discarding
            
            # If we found an improvement, keep that hand
            # Otherwise, discard the card we just drew (didn't help)
            if best_after_draw < best_deadwood and best_discard_card:
                best_deadwood = best_after_draw
                current_hand = [c for c in current_hand if c != best_discard_card]
                # Track if we improved from initial state
                if best_after_draw < initial_deadwood:
                    improvements += 1
            else:
                # No improvement, discard the drawn card (keep original hand)
                current_hand.remove(drawn)
        
        total_deadwood += best_deadwood
    
    # Calculate averages across all trials
    avg_deadwood = total_deadwood / trials
    improvement_prob = improvements / trials  # What fraction of trials improved?
    
    return avg_deadwood, improvement_prob

def get_confidence_level(prob: float, trials: int) -> str:
    """
    Determines confidence level based on probability and number of trials.
    
    More trials = more reliable results, so we can be confident with lower
    probabilities. Fewer trials need higher probabilities to be confident.
    
    These thresholds are somewhat arbitrary but work reasonably well in practice.
    Could tune these based on user feedback or more rigorous testing.
    
    Returns "high", "medium", or "low" confidence.
    """
    if trials >= 500:
        # Lots of trials, can trust lower probabilities
        if prob >= 0.7:
            return "high"
        elif prob >= 0.4:
            return "medium"
        else:
            return "low"
    elif trials >= 200:
        # Moderate trials
        if prob >= 0.75:
            return "high"
        elif prob >= 0.45:
            return "medium"
        else:
            return "low"
    else:
        # Few trials, need high probability to be confident
        if prob >= 0.8:
            return "high"
        elif prob >= 0.5:
            return "medium"
        else:
            return "low"

@app.post("/suggest", response_model=SuggestResponse)
async def suggest_discard(request: SuggestRequest):
    """
    Suggests the best card to discard based on Monte Carlo simulation.
    
    For each card in the hand, simulates what happens if we discard it.
    Returns ranked list of suggestions with win probabilities.
    
    This is the main endpoint the iOS app calls to get strategy advice.
    The suggestions are sorted by win probability (best first).
    """
    try:
        my_hand = request.my_hand
        visible = set(request.visible)
        
        # Validate hand format
        parsed_hand = [parse_card(c) for c in my_hand]
        invalid_cards = [c for c, p in zip(my_hand, parsed_hand) if p is None]
        if invalid_cards:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid card format(s): {invalid_cards}. Expected format: 'Rank-Suit' (e.g., 'A-hearts')"
            )
        
        # Check for duplicates
        if len(my_hand) != len(set(my_hand)):
            raise HTTPException(status_code=400, detail="Duplicate cards found in hand")
        
        # Build the unknown deck (cards we haven't seen)
        # This is what we simulate drawing from
        full_deck = build_deck()
        my_hand_set = set(my_hand)
        visible_set = set(visible)
        
        # Validate visible cards (discard pile, etc.)
        # These are cards we know about but don't have
        invalid_visible = [c for c in visible if parse_card(c) is None]
        if invalid_visible:
            logger.warning(f"Invalid visible cards: {invalid_visible}")
        
        # Unknown deck = all cards minus hand minus visible cards
        # These are the cards we might draw
        unknown_deck = [c for c in full_deck if c not in my_hand_set and c not in visible_set]
        
        if len(unknown_deck) == 0:
            raise HTTPException(status_code=400, detail="No unknown cards remaining in deck")
        
        current_deadwood = calculate_deadwood(my_hand)
        
        results = []
        
        # For each card in hand, simulate what happens if we discard it
        # This gives us a comparison of all options
        for card_to_discard in my_hand:
            # Remaining hand
            remaining_hand = [c for c in my_hand if c != card_to_discard]
            
            # Run simulation on this remaining hand state
            avg_deadwood, win_prob = simulate_game(
                remaining_hand,
                unknown_deck.copy(),
                trials=request.trials,
                max_draws=request.max_draws
            )
            
            # Convert improvement probability to "win probability"
            # Lower deadwood = better chance of winning
            # Normalize based on how much we can reduce deadwood
            if current_deadwood > 0:
                # If we can significantly reduce deadwood, that's a good sign
                # This formula weights both improvement frequency and magnitude
                normalized_prob = win_prob * (1.0 - min(avg_deadwood / (current_deadwood + 1), 1.0))
            else:
                # Already at 0 deadwood (or very low), just use improvement prob
                normalized_prob = win_prob
            
            confidence = get_confidence_level(normalized_prob, request.trials)
            
            results.append(DiscardSuggestion(
                card=card_to_discard,
                win_probability=min(max(normalized_prob, 0.0), 1.0),
                expected_deadwood=round(avg_deadwood, 2),
                confidence=confidence
            ))
        
        # Sort: We want to discard the card that leaves us with the BEST remaining hand.
        # Sort by win_probability (descending), then by expected_deadwood (ascending)
        # Higher win prob + lower deadwood = better option
        # This gives us the best suggestions first
        results.sort(key=lambda x: (x.win_probability, -x.expected_deadwood), reverse=True)
        
        # Add a helpful message if all options look bad
        message = None
        if len(results) > 0 and results[0].win_probability < 0.3:
            message = "All discard options show low win probability. Consider your current hand carefully."
        
        return SuggestResponse(
            suggestions=results,
            current_deadwood=round(current_deadwood, 2),
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in suggest_discard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/")
def health_check():
    """
    Health check endpoint.
    
    Simple endpoint to verify the server is running.
    """
    return {
        "status": "ok",
        "service": "rummy_engine",
        "version": "1.0.0"
    }

@app.get("/deck/validate")
def validate_card(card: str):
    """
    Validate a card string format.
    
    Useful for debugging - check if a card string is properly formatted.
    Also returns the deadwood value for that card, which can be helpful.
    """
    parsed = parse_card(card)
    if parsed:
        rank_val, suit = parsed
        return {
            "valid": True,
            "rank": RANKS[rank_val - 1],
            "suit": suit,
            "deadwood_value": DEADWOOD_VALUES.get(RANKS[rank_val - 1], 10)
        }
    else:
        return {"valid": False, "message": f"Invalid card format. Expected 'Rank-Suit' (e.g., 'A-hearts')"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", "8001"))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
