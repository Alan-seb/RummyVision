import SwiftUI
import AVFoundation

/// Main view for the Rummy Assistant app
/// Shows camera preview, detected cards, and discard suggestions
struct ContentView: View {
    @StateObject var camera = CameraManager()
    @StateObject var network = NetworkManager()
    
    var body: some View {
        NavigationView {
            VStack {
                // Camera Preview Section
                ZStack {
                    if let layer = camera.previewLayer {
                        // Show live camera preview
                        CameraPreview(layer: layer)
                            .frame(height: 400)
                            .cornerRadius(12)
                    } else {
                        // Show placeholder while camera loads
                        Rectangle()
                            .fill(Color.gray)
                            .frame(height: 400)
                            .overlay(
                                VStack {
                                    if let error = camera.errorMessage {
                                        Text(error)
                                            .foregroundColor(.red)
                                            .padding()
                                    } else {
                                        Text("Camera Loading...")
                                    }
                                }
                            )
                    }
                    
                    // Capture button overlay
                    VStack {
                        Spacer()
                        Button(action: captureAndAnalyze) {
                            // Large circular capture button (like camera app)
                            Circle()
                                .fill(Color.white)
                                .frame(width: 70, height: 70)
                                .overlay(Circle().stroke(Color.black, lineWidth: 2))
                                .shadow(radius: 4)
                        }
                        .disabled(camera.previewLayer == nil || network.isLoading)
                        .opacity(camera.previewLayer == nil || network.isLoading ? 0.5 : 1.0)
                        .padding(.bottom, 20)
                    }
                }
                .padding()
                
                // Results Area - Shows detected cards and suggestions
                ScrollView {
                    // Loading indicator
                    if network.isLoading {
                        ProgressView("Processing...")
                    } else if let error = network.errorMessage {
                        // Show errors in red
                        Text(error)
                            .foregroundColor(.red)
                            .padding()
                    }
                    
                    // Detected Cards Section
                    if !network.detectedCards.isEmpty {
                        VStack(alignment: .leading) {
                            Text("Detected Cards:")
                                .font(.headline)
                            
                            // Horizontal scrollable list of detected cards
                            ScrollView(.horizontal) {
                                HStack {
                                    ForEach(network.detectedCards) { card in
                                        VStack {
                                            Text(card.rank)
                                                .font(.title)
                                                .bold()
                                            Text(card.suit)
                                                .font(.caption)
                                        }
                                        .padding()
                                        .background(Color.gray.opacity(0.1))
                                        .cornerRadius(8)
                                    }
                                }
                            }
                            
                            // Button to get discard suggestions
                            Button("Get Suggestion") {
                                // Convert detected cards to hand format (Rank-Suit)
                                let hand = network.detectedCards.map { "\($0.rank)-\($0.suit)" }
                                network.getSuggestion(hand: hand)
                            }
                            .padding(.top)
                            .buttonStyle(.borderedProminent)
                            .disabled(network.detectedCards.isEmpty || network.isLoading)
                        }
                        .padding()
                    }
                    
                    // Suggestions Section
                    if !network.suggestions.isEmpty {
                        VStack(alignment: .leading) {
                            Text("Recommended Discard:")
                                .font(.headline)
                                .padding(.top)
                            
                            // Show current deadwood score
                            if let currentDeadwood = network.currentDeadwood {
                                Text("Current Deadwood: \(String(format: "%.1f", currentDeadwood))")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                    .padding(.bottom, 4)
                            }
                            
                            // List of suggestions (ranked by win probability)
                            ForEach(network.suggestions) { suggestion in
                                HStack {
                                    // Card info
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text("Discard \(suggestion.card)")
                                            .bold()
                                        if let confidence = suggestion.confidence {
                                            Text("Confidence: \(confidence.capitalized)")
                                                .font(.caption)
                                                .foregroundColor(.secondary)
                                        }
                                    }
                                    Spacer()
                                    // Win probability and expected deadwood
                                    VStack(alignment: .trailing, spacing: 4) {
                                        Text("\(String(format: "%.1f", suggestion.win_probability * 100))%")
                                            .foregroundColor(.green)
                                            .bold()
                                        if let deadwood = suggestion.expected_deadwood {
                                            Text("Deadwood: \(String(format: "%.1f", deadwood))")
                                                .font(.caption)
                                                .foregroundColor(.secondary)
                                        }
                                    }
                                }
                                .padding(.vertical, 4)
                                Divider()
                            }
                        }
                        .padding()
                    }
                }
            }
            .navigationTitle("Rummy Assistant")
            .onAppear {
                // Check camera permissions when view appears
                camera.checkPermissions()
            }
        }
    }
    
    /// Captures a photo and sends it to the server for card recognition
    func captureAndAnalyze() {
        camera.capturePhoto { data in
            guard let data = data else { return }
            // Upload image to CV server for recognition
            network.uploadImage(imageData: data)
        }
    }
}

/// Wrapper to display AVCaptureVideoPreviewLayer in SwiftUI
/// SwiftUI doesn't have native support for AVFoundation preview layers
struct CameraPreview: UIViewRepresentable {
    var layer: AVCaptureVideoPreviewLayer
    
    func makeUIView(context: Context) -> UIView {
        let view = UIView()
        view.backgroundColor = .black
        layer.videoGravity = .resizeAspectFill
        view.layer.addSublayer(layer)
        return view
    }
    
    func updateUIView(_ uiView: UIView, context: Context) {
        // Update layer frame when view bounds change
        // Disable animations for smooth updates
        CATransaction.begin()
        CATransaction.setDisableActions(true)
        layer.frame = uiView.bounds
        CATransaction.commit()
    }
}
