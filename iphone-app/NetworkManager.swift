import Foundation
import UIKit

/// Handles all network communication with the backend servers
/// Manages card recognition requests and strategy suggestions
class NetworkManager: ObservableObject {
    // Configuration: Set your server IP address here or use environment variable
    // You can also set this via UserDefaults or a settings screen
    // TODO: Add a proper settings UI for this
    private var baseURL: String {
        // Check UserDefaults first (for runtime configuration)
        // This allows users to change the server URL without rebuilding
        if let savedURL = UserDefaults.standard.string(forKey: "serverBaseURL"), !savedURL.isEmpty {
            return savedURL
        }
        // Fallback to environment variable or default
        // In production, you might want to use a config file or settings screen
        // Default IP is just a placeholder - update this to your Mac's IP
        return ProcessInfo.processInfo.environment["RUMMY_SERVER_URL"] ?? "192.168.1.4"
    }
    
    // Published properties for SwiftUI - these trigger UI updates when changed
    @Published var detectedCards: [CardResult] = []
    @Published var suggestions: [DiscardSuggestion] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var currentDeadwood: Double?
    
    // Allow runtime configuration - useful for testing or switching servers
    func setServerURL(_ url: String) {
        UserDefaults.standard.set(url, forKey: "serverBaseURL")
    }
    
    func getServerURL() -> String {
        return baseURL
    }
    
    /// Uploads an image to the CV server for card recognition
    /// The server will detect and identify cards in the image
    func uploadImage(imageData: Data) {
        guard !imageData.isEmpty else {
            errorMessage = "Image data is empty"
            return
        }
        
        // Build the recognition endpoint URL
        guard let url = URL(string: "\(baseURL):8000/recognize") else {
            errorMessage = "Invalid server URL. Please configure the server address."
            return
        }
        
        isLoading = true
        errorMessage = nil
        
        // Set up the multipart form request
        // This is the standard way to upload files via HTTP
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = 30.0  // 30 second timeout - CV processing can take a moment
        
        // Create multipart form boundary
        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        // Build the multipart form body
        // This is a bit verbose but necessary for file uploads
        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"capture.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(imageData)
        body.append("\r\n".data(using: .utf8)!)
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        
        request.httpBody = body
        
        // Perform the network request asynchronously
        // Using weak self to avoid retain cycles
        URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            DispatchQueue.main.async {
                guard let self = self else { return }
                self.isLoading = false
                
                // Handle network errors
                if let error = error {
                    self.errorMessage = "Network error: \(error.localizedDescription)"
                    return
                }
                
                // Validate HTTP response
                guard let httpResponse = response as? HTTPURLResponse else {
                    self.errorMessage = "Invalid server response"
                    return
                }
                
                // Check for HTTP errors (non-2xx status codes)
                guard (200...299).contains(httpResponse.statusCode) else {
                    self.errorMessage = "Server error: HTTP \(httpResponse.statusCode)"
                    // Try to get error details from response body
                    if let data = data, let errorString = String(data: data, encoding: .utf8) {
                        self.errorMessage = "Server error: \(errorString)"
                    }
                    return
                }
                
                guard let data = data else {
                    self.errorMessage = "No data received from server"
                    return
                }
                
                // Parse JSON response
                do {
                    let result = try JSONDecoder().decode(RecognitionResponse.self, from: data)
                    // Filter out cards with very low confidence scores
                    // Better to show fewer cards than wrong ones
                    self.detectedCards = result.cards.filter { card in
                        card.rank_score > 0.3 && card.suit_score > 0.3 && card.rank != "Unknown"
                    }
                    if self.detectedCards.isEmpty && result.count > 0 {
                        self.errorMessage = result.message ?? "No cards detected with sufficient confidence. Try better lighting or angle."
                    } else if let message = result.message, !message.isEmpty {
                        // Show informational message but don't treat as error
                        print("Recognition message: \(message)")
                    }
                } catch {
                    self.errorMessage = "Failed to parse server response: \(error.localizedDescription)"
                }
            }
        }.resume()
    }
    
    /// Requests discard suggestions from the game engine server
    /// Takes the current hand and returns ranked suggestions with win probabilities
    func getSuggestion(hand: [String], visible: [String] = [], trials: Int = 200) {
        guard !hand.isEmpty else {
            errorMessage = "Cannot get suggestion for empty hand"
            return
        }
        
        // Build the suggestion endpoint URL (different port from CV server)
        guard let url = URL(string: "\(baseURL):8001/suggest") else {
            errorMessage = "Invalid server URL. Please configure the server address."
            return
        }
        
        isLoading = true
        errorMessage = nil
        
        // Set up JSON POST request
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 30.0  // Monte Carlo simulation can take a moment
        
        // Clamp trials to reasonable range (100-1000)
        // Too few = inaccurate, too many = slow
        let payload = SuggestRequest(
            my_hand: hand,
            visible: visible,  // Known cards (discard pile, etc.)
            trials: max(100, min(trials, 1000)),
            max_draws: 5  // Look ahead 5 draws
        )
        
        do {
            request.httpBody = try JSONEncoder().encode(payload)
        } catch {
            self.errorMessage = "Failed to encode request: \(error.localizedDescription)"
            return
        }
        
        // Perform the network request
        URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            DispatchQueue.main.async {
                guard let self = self else { return }
                self.isLoading = false
                
                // Handle network errors
                if let error = error {
                    self.errorMessage = "Network error: \(error.localizedDescription)"
                    return
                }
                
                // Validate HTTP response
                guard let httpResponse = response as? HTTPURLResponse else {
                    self.errorMessage = "Invalid server response"
                    return
                }
                
                // Check for HTTP errors
                guard (200...299).contains(httpResponse.statusCode) else {
                    self.errorMessage = "Server error: HTTP \(httpResponse.statusCode)"
                    if let data = data, let errorString = String(data: data, encoding: .utf8) {
                        self.errorMessage = "Server error: \(errorString)"
                    }
                    return
                }
                
                guard let data = data else {
                    self.errorMessage = "No data received from server"
                    return
                }
                
                // Parse JSON response
                do {
                    let result = try JSONDecoder().decode(SuggestResponse.self, from: data)
                    self.suggestions = result.suggestions  // Ranked list of discard options
                    self.currentDeadwood = result.current_deadwood  // Current hand score
                    if self.suggestions.isEmpty {
                        self.errorMessage = result.message ?? "No suggestions returned from server"
                    } else if let message = result.message, !message.isEmpty {
                        // Show informational message (not an error)
                        print("Suggestion message: \(message)")
                    }
                } catch {
                    self.errorMessage = "Failed to parse server response: \(error.localizedDescription)"
                }
            }
        }.resume()
    }
}
