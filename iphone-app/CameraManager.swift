import SwiftUI
import AVFoundation

/// Manages camera access and photo capture
/// Handles permissions, session setup, and photo capture
class CameraManager: NSObject, ObservableObject {
    // Published properties for SwiftUI
    @Published var session = AVCaptureSession()
    @Published var output = AVCapturePhotoOutput()
    @Published var previewLayer: AVCaptureVideoPreviewLayer?
    @Published var isAuthorized = false
    @Published var errorMessage: String?
    
    // Serial queue for all camera operations to ensure thread safety
    // Camera operations must happen on a single queue to avoid conflicts
    private let sessionQueue = DispatchQueue(label: "camera.session.queue")
    
    override init() {
        super.init()
        checkPermissions()
    }
    
    /// Checks camera permissions and requests access if needed
    /// iOS requires explicit permission for camera access
    func checkPermissions() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            // Already have permission, set up camera
            isAuthorized = true
            setupCamera()
        case .notDetermined:
            // Haven't asked yet - request permission
            AVCaptureDevice.requestAccess(for: .video) { granted in
                DispatchQueue.main.async {
                    self.isAuthorized = granted
                    if granted {
                        self.setupCamera()
                    } else {
                        self.errorMessage = "Camera access denied. Please enable camera access in Settings."
                    }
                }
            }
        case .denied, .restricted:
            // User denied or restricted - show error
            isAuthorized = false
            errorMessage = "Camera access denied. Please enable camera access in Settings."
        @unknown default:
            // Handle future cases
            isAuthorized = false
            errorMessage = "Unknown camera authorization status."
        }
    }
    
    /// Sets up the camera session with proper configuration
    /// This is a bit complex because AVFoundation requires careful session management
    func setupCamera() {
        // Use serial queue for all camera operations (required by AVFoundation)
        sessionQueue.async {
            do {
                // Stop session if running (need to reconfigure)
                if self.session.isRunning {
                    self.session.stopRunning()
                }
                
                // Wait for session to fully stop before reconfiguring
                // This prevents conflicts during configuration
                let semaphore = DispatchSemaphore(value: 0)
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
                    semaphore.signal()
                }
                semaphore.wait()
                
                // Begin configuration - all changes happen atomically
                self.session.beginConfiguration()
                
                // Set session preset before adding inputs
                // Photo preset gives us good quality for card recognition
                if self.session.canSetSessionPreset(.photo) {
                    self.session.sessionPreset = .photo
                }
                
                // Remove existing inputs and outputs (clean slate)
                // This prevents conflicts if setupCamera is called multiple times
                for input in self.session.inputs {
                    self.session.removeInput(input)
                }
                for output in self.session.outputs {
                    self.session.removeOutput(output)
                }
                
                // Get the back camera (better quality than front camera)
                guard let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back) else {
                    self.session.commitConfiguration()
                    DispatchQueue.main.async {
                        self.errorMessage = "Camera device not available."
                    }
                    return
                }
                
                // Lock device for configuration (required by AVFoundation)
                try device.lockForConfiguration()
                defer { device.unlockForConfiguration() }  // Always unlock, even on error
                
                // Create input from device
                let input = try AVCaptureDeviceInput(device: device)
                
                if self.session.canAddInput(input) {
                    self.session.addInput(input)
                } else {
                    self.session.commitConfiguration()
                    throw NSError(domain: "CameraManager", code: 1, userInfo: [NSLocalizedDescriptionKey: "Cannot add camera input"])
                }
                
                // Add photo output for capturing images
                if self.session.canAddOutput(self.output) {
                    self.session.addOutput(self.output)
                } else {
                    self.session.commitConfiguration()
                    throw NSError(domain: "CameraManager", code: 2, userInfo: [NSLocalizedDescriptionKey: "Cannot add photo output"])
                }
                
                // Commit all configuration changes atomically
                self.session.commitConfiguration()
                
                // Create and configure preview layer on main thread (UI must be on main thread)
                DispatchQueue.main.async {
                    let preview = AVCaptureVideoPreviewLayer(session: self.session)
                    preview.videoGravity = .resizeAspectFill  // Fill the preview area
                    self.previewLayer = preview
                    
                    // Start session on serial queue after preview is set
                    self.sessionQueue.async {
                        if !self.session.isRunning {
                            self.session.startRunning()
                        }
                    }
                }
            } catch { 
                // Always try to commit configuration to clean up
                // Prevents leaving session in bad state
                if self.session.inputs.isEmpty || !self.session.isRunning {
                    self.session.commitConfiguration()
                }
                
                DispatchQueue.main.async {
                    self.errorMessage = "Camera setup failed: \(error.localizedDescription)"
                }
            }
        }
    }
    
    /// Captures a photo from the camera
    /// Completion handler receives the image data (or nil on error)
    func capturePhoto(completion: @escaping (Data?) -> Void) {
        sessionQueue.async {
            let settings = AVCapturePhotoSettings()
            self.photoCompletion = completion
            // Capture photo - delegate method will be called when done
            self.output.capturePhoto(with: settings, delegate: self)
        }
    }
    
    // Store completion handler for when photo is captured
    private var photoCompletion: ((Data?) -> Void)?
}

// MARK: - AVCapturePhotoCaptureDelegate
extension CameraManager: AVCapturePhotoCaptureDelegate {
    /// Called when photo capture completes
    /// Converts the photo to Data format for network upload
    func photoOutput(_ output: AVCapturePhotoOutput, didFinishProcessingPhoto photo: AVCapturePhoto, error: Error?) {
        if let error = error {
            DispatchQueue.main.async {
                self.errorMessage = "Photo capture failed: \(error.localizedDescription)"
            }
            photoCompletion?(nil)
            return
        }
        
        // Get JPEG data representation for upload
        guard let data = photo.fileDataRepresentation() else {
            DispatchQueue.main.async {
                self.errorMessage = "Failed to get photo data representation."
            }
            photoCompletion?(nil)
            return
        }
        photoCompletion?(data)
    }
}
