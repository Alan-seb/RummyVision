import Foundation

// MARK: - API Models
// These models match the JSON structure returned by the backend servers

/// Represents a detected card with confidence scores
struct CardResult: Codable, Identifiable {
    var id = UUID()  // For SwiftUI list identification
    let rank: String  // Card rank (A, K, Q, J, 10, 9, etc.)
    let rank_score: Double  // Confidence score for rank recognition (0-1)
    let suit: String  // Card suit (hearts, spades, diamonds, clubs)
    let suit_score: Double  // Confidence score for suit recognition (0-1)
    
    enum CodingKeys: String, CodingKey {
        case rank, rank_score, suit, suit_score
    }
}

/// Response from card recognition endpoint
struct RecognitionResponse: Codable {
    let cards: [CardResult]  // List of detected cards
    let count: Int  // Number of cards detected
    let message: String?  // Optional informational message
    
    enum CodingKeys: String, CodingKey {
        case cards, count, message
    }
}

/// A single discard suggestion with probability and expected outcome
struct DiscardSuggestion: Codable, Identifiable {
    var id = UUID()  // For SwiftUI list identification
    let card: String  // Card to discard (format: "Rank-Suit")
    let win_probability: Double  // Probability of winning after this discard (0-1)
    let expected_deadwood: Double?  // Expected deadwood score after discard
    let confidence: String?  // Confidence level: "high", "medium", or "low"
    
    enum CodingKeys: String, CodingKey {
        case card, win_probability, expected_deadwood, confidence
    }
}

/// Response from suggestion endpoint
struct SuggestResponse: Codable {
    let suggestions: [DiscardSuggestion]  // Ranked list of discard suggestions
    let current_deadwood: Double?  // Current hand's deadwood score
    let message: String?  // Optional informational message
    
    enum CodingKeys: String, CodingKey {
        case suggestions, current_deadwood, message
    }
}

/// Request payload for suggestion endpoint
struct SuggestRequest: Codable {
    let my_hand: [String]  // Cards in hand (format: ["A-hearts", "K-spades", ...])
    let visible: [String]  // Known cards (discard pile, etc.)
    let trials: Int  // Number of Monte Carlo trials (more = more accurate but slower)
    let max_draws: Int?  // Maximum draws to simulate ahead
    
    enum CodingKeys: String, CodingKey {
        case my_hand, visible, trials, max_draws
    }
    
    init(my_hand: [String], visible: [String] = [], trials: Int = 200, max_draws: Int = 5) {
        self.my_hand = my_hand
        self.visible = visible
        self.trials = trials
        self.max_draws = max_draws
    }
}
