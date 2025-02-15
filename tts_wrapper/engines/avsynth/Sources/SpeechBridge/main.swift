import Foundation
import AVFoundation
import ArgumentParser

func log(_ message: String) {
    fputs("DEBUG: \(message)\n", stderr)
    fflush(stderr)
}

struct SpeechBridge: ParsableCommand {
    static var configuration = CommandConfiguration(
        commandName: "SpeechBridge",
        abstract: "Bridge between Python and AVSpeechSynthesizer",
        subcommands: [ListVoices.self, Synthesize.self, Stream.self]
    )
}

// Command to list available voices
struct ListVoices: ParsableCommand {
    static var configuration = CommandConfiguration(
        commandName: "list-voices",
        abstract: "List available voices"
    )
    
    func run() throws {
        let voices = AVSpeechSynthesisVoice.speechVoices().map { voice in
            [
                "id": voice.identifier,
                "name": voice.name,
                "language_codes": [voice.language],
                "gender": voice.gender == .female ? "female" : "male"
            ]
        }
        
        let jsonData = try JSONSerialization.data(withJSONObject: voices)
        if let jsonString = String(data: jsonData, encoding: .utf8) {
            print(jsonString)
        }
    }
}

// Command to synthesize speech
struct Synthesize: ParsableCommand {
    static var configuration = CommandConfiguration(
        commandName: "synth",
        abstract: "Synthesize text to speech"
    )
    
    @Argument(help: "Text to synthesize")
    var text: String
    
    @Option(name: .long, help: "Voice identifier")
    var voice: String?
    
    @Option(name: .long, help: "Speech rate (0.0 - 1.0)")
    var rate: Float = 0.5
    
    @Option(name: .long, help: "Volume (0.0 - 1.0)")
    var volume: Float = 1.0
    
    @Option(name: .long, help: "Pitch multiplier (0.5 - 2.0)")
    var pitch: Float = 1.0
    
    @Option(name: .long, help: "Whether the text contains SSML markup")
    var isSSML: Bool = false
    
    func run() throws {
        log("Starting synthesis")
        
        let synthesizer = AVSpeechSynthesizer()
        let utterance: AVSpeechUtterance
        
        // Use SSML if available and text contains SSML markup
        if #available(macOS 13.0, *), isSSML {
            log("Using SSML synthesis")
            guard let ssmlUtterance = AVSpeechUtterance(ssmlRepresentation: text) else {
                throw NSError(
                    domain: "SpeechBridge",
                    code: -4,
                    userInfo: [NSLocalizedDescriptionKey: "Invalid SSML markup"]
                )
            }
            utterance = ssmlUtterance
        } else {
            log("Using plain text synthesis")
            utterance = AVSpeechUtterance(string: text)
            
            // Configure utterance (only for non-SSML)
            if let voiceId = voice {
                log("Using voice: \(voiceId)")
                utterance.voice = AVSpeechSynthesisVoice(identifier: voiceId)
            }
            utterance.rate = rate
            utterance.volume = volume
            utterance.pitchMultiplier = pitch
        }
        
        var audioData = Data()
        var wordTimings: [[String: Any]] = []
        var hasError = false
        var isComplete = false
        var bufferCount = 0
        
        // Set up delegate for word boundary events
        class SpeechDelegate: NSObject, AVSpeechSynthesizerDelegate {
            var onWordBoundary: ([String: Any]) -> Void
            var onComplete: () -> Void
            var onError: () -> Void
            var spokenText: String
            
            init(
                spokenText: String,
                onWordBoundary: @escaping ([String: Any]) -> Void,
                onComplete: @escaping () -> Void,
                onError: @escaping () -> Void
            ) {
                self.spokenText = spokenText
                self.onWordBoundary = onWordBoundary
                self.onComplete = onComplete
                self.onError = onError
                super.init()
            }
            
            func speechSynthesizer(
                _ synthesizer: AVSpeechSynthesizer,
                willSpeakRangeOfSpeechString characterRange: NSRange,
                utterance: AVSpeechUtterance
            ) {
                // For SSML, use the actual spoken text length
                let textLength = Double(spokenText.count)
                let start = Double(characterRange.location) / textLength
                let end = Double(characterRange.location + characterRange.length) / textLength
                
                // Get the word being spoken, safely
                let word: String
                if characterRange.location + characterRange.length <= spokenText.count {
                    let startIndex = spokenText.index(spokenText.startIndex, offsetBy: characterRange.location)
                    let endIndex = spokenText.index(startIndex, offsetBy: characterRange.length)
                    word = String(spokenText[startIndex..<endIndex])
                } else {
                    word = ""  // Default to empty if range is invalid
                }
                
                log("Speaking word: \(word)")
                let timing: [String: Any] = [
                    "word": word,
                    "start": start,
                    "end": end
                ]
                onWordBoundary(timing)
            }
            
            func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
                log("Synthesis finished")
                onComplete()
            }
            
            func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didEncounterError error: Error, utterance: AVSpeechUtterance) {
                log("Synthesis error: \(error)")
                onError()
            }
        }
        
        // For SSML, extract the plain text content for word boundary calculations
        let plainText: String
        if isSSML {
            // Simple extraction of text content (you might want to make this more sophisticated)
            plainText = text.replacingOccurrences(of: "<[^>]+>", with: "", options: .regularExpression)
        } else {
            plainText = text
        }
        
        let delegate = SpeechDelegate(
            spokenText: plainText,
            onWordBoundary: { timing in
                wordTimings.append(timing)
            },
            onComplete: {
                log("Synthesis complete")
                isComplete = true
            },
            onError: {
                log("Synthesis error")
                hasError = true
            }
        )
        synthesizer.delegate = delegate
        
        do {
            // Start synthesis and collect buffers
            synthesizer.write(utterance) { buffer in
                if let audioBuffer = buffer as? AVAudioPCMBuffer {
                    bufferCount += 1
                    log("Processing buffer \(bufferCount)")
                    
                    // Convert float samples to 16-bit PCM
                    let frameCount = Int(audioBuffer.frameLength)
                    var pcmData = Data(capacity: frameCount * 2) // 2 bytes per sample
                    
                    if let channelData = audioBuffer.floatChannelData?[0] {
                        for i in 0..<frameCount {
                            // Convert float to 16-bit integer
                            let sample = channelData[i]
                            let intSample = Int16(max(-1.0, min(1.0, sample)) * 32767.0)
                            
                            // Append as little-endian bytes
                            pcmData.append(UInt8(intSample & 0xFF))
                            pcmData.append(UInt8((intSample >> 8) & 0xFF))
                        }
                    }
                    
                    audioData.append(pcmData)
                }
            }
            
            log("Waiting for completion")
            // Run the main loop until completion or timeout
            let startTime = Date()
            while !isComplete && !hasError {
                if Date().timeIntervalSince(startTime) > 30 {
                    log("Synthesis timed out")
                    throw NSError(domain: "SpeechBridge", code: -1, userInfo: [NSLocalizedDescriptionKey: "Synthesis timed out"])
                }
                RunLoop.current.run(mode: .default, before: Date(timeIntervalSinceNow: 0.1))
            }
            
            if hasError {
                log("Synthesis failed")
                throw NSError(domain: "SpeechBridge", code: -2, userInfo: [NSLocalizedDescriptionKey: "Synthesis failed"])
            }
            
            if !isComplete {
                log("Synthesis incomplete")
                throw NSError(domain: "SpeechBridge", code: -3, userInfo: [NSLocalizedDescriptionKey: "Synthesis incomplete"])
            }
            
            // Create response
            let response: [String: Any] = [
                "audio_data": [UInt8](audioData),
                "word_timings": wordTimings
            ]
            
            // Output JSON response
            if let jsonData = try? JSONSerialization.data(withJSONObject: response),
               let jsonString = String(data: jsonData, encoding: .utf8) {
                print(jsonString)
            }
            
            log("Synthesis completed successfully")
            
        } catch {
            log("Error during synthesis: \(error)")
            throw error
        }
    }
}

// Command to stream speech
struct Stream: ParsableCommand {
    static var configuration = CommandConfiguration(
        commandName: "stream",
        abstract: "Stream synthesized speech"
    )
    
    @Argument(help: "Text to synthesize")
    var text: String
    
    @Option(name: .long, help: "Voice identifier")
    var voice: String?
    
    @Option(name: .long, help: "Speech rate (0.0 - 1.0)")
    var rate: Float = 0.5
    
    @Option(name: .long, help: "Volume (0.0 - 1.0)")
    var volume: Float = 1.0
    
    @Option(name: .long, help: "Pitch multiplier (0.5 - 2.0)")
    var pitch: Float = 1.0
    
    @Option(name: .long, help: "Whether the text contains SSML markup")
    var isSSML: Bool = false
    
    func run() throws {
        log("Starting streaming synthesis")
        
        let synthesizer = AVSpeechSynthesizer()
        let utterance: AVSpeechUtterance
        
        // Use SSML if available and text contains SSML markup
        if #available(macOS 13.0, *), isSSML {
            log("Using SSML synthesis")
            guard let ssmlUtterance = AVSpeechUtterance(ssmlRepresentation: text) else {
                throw NSError(
                    domain: "SpeechBridge",
                    code: -4,
                    userInfo: [NSLocalizedDescriptionKey: "Invalid SSML markup"]
                )
            }
            utterance = ssmlUtterance
        } else {
            log("Using plain text synthesis")
            utterance = AVSpeechUtterance(string: text)
            
            // Configure utterance (only for non-SSML)
            if let voiceId = voice {
                log("Using voice: \(voiceId)")
                utterance.voice = AVSpeechSynthesisVoice(identifier: voiceId)
            }
            utterance.rate = rate
            utterance.volume = volume
            utterance.pitchMultiplier = pitch
        }
        
        var wordTimings: [[String: Any]] = []
        let synthesisComplete = DispatchSemaphore(value: 0)
        let audioComplete = DispatchSemaphore(value: 0)
        var hasError = false
        
        // Set up audio engine
        let audioEngine = AVAudioEngine()
        let mainMixer = audioEngine.mainMixerNode
        let format = mainMixer.outputFormat(forBus: 0)
        
        // First, send audio format information
        let formatInfo: [String: Any] = [
            "sample_rate": format.sampleRate,
            "channels": format.channelCount,
            "bits_per_sample": 16,  // We'll convert to 16-bit PCM
            "is_float": false
        ]
        
        if let formatData = try? JSONSerialization.data(withJSONObject: formatInfo),
           let formatString = String(data: formatData, encoding: .utf8) {
            print(formatString)
            print("\n---AUDIO_START---\n")  // Clear delimiter
            fflush(stdout)
        }
        
        // Install tap before starting synthesis
        log("Installing audio tap")
        mainMixer.installTap(onBus: 0, bufferSize: 4096, format: format) { buffer, _ in
            let frameCount = Int(buffer.frameLength)
            var pcmData = Data()
            
            if let channelData = buffer.floatChannelData?[0] {
                // Convert float samples to 16-bit PCM
                for i in 0..<frameCount {
                    let sample = channelData[i]
                    let intSample = Int16(max(-1.0, min(1.0, sample)) * 32767.0)
                    pcmData.append(UInt8(intSample & 0xFF))
                    pcmData.append(UInt8((intSample >> 8) & 0xFF))
                }
                FileHandle.standardOutput.write(pcmData)
                fflush(stdout)
            }
        }
        
        do {
            log("Starting audio engine")
            try audioEngine.start()
            
            // Set up delegate for synthesis events
            class SpeechDelegate: NSObject, AVSpeechSynthesizerDelegate {
                var onWordBoundary: ([String: Any]) -> Void
                var onComplete: () -> Void
                var onError: () -> Void
                var spokenText: String
                
                init(
                    spokenText: String,
                    onWordBoundary: @escaping ([String: Any]) -> Void,
                    onComplete: @escaping () -> Void,
                    onError: @escaping () -> Void
                ) {
                    self.spokenText = spokenText
                    self.onWordBoundary = onWordBoundary
                    self.onComplete = onComplete
                    self.onError = onError
                    super.init()
                }
                
                func speechSynthesizer(
                    _ synthesizer: AVSpeechSynthesizer,
                    willSpeakRangeOfSpeechString characterRange: NSRange,
                    utterance: AVSpeechUtterance
                ) {
                    // For SSML, use the actual spoken text length
                    let textLength = Double(spokenText.count)
                    let start = Double(characterRange.location) / textLength
                    let end = Double(characterRange.location + characterRange.length) / textLength
                    
                    // Get the word being spoken, safely
                    let word: String
                    if characterRange.location + characterRange.length <= spokenText.count {
                        let startIndex = spokenText.index(spokenText.startIndex, offsetBy: characterRange.location)
                        let endIndex = spokenText.index(startIndex, offsetBy: characterRange.length)
                        word = String(spokenText[startIndex..<endIndex])
                    } else {
                        word = ""  // Default to empty if range is invalid
                    }
                    
                    log("Speaking word: \(word)")
                    let timing: [String: Any] = [
                        "word": word,
                        "start": start,
                        "end": end
                    ]
                    onWordBoundary(timing)
                }
                
                func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
                    log("Synthesis finished")
                    onComplete()
                }
                
                func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didEncounterError error: Error, utterance: AVSpeechUtterance) {
                    log("Synthesis error: \(error)")
                    onError()
                }
            }
            
            // For SSML, extract the plain text content for word boundary calculations
            let plainText: String
            if isSSML {
                // Simple extraction of text content (you might want to make this more sophisticated)
                plainText = text.replacingOccurrences(of: "<[^>]+>", with: "", options: .regularExpression)
            } else {
                plainText = text
            }
            
            let delegate = SpeechDelegate(
                spokenText: plainText,
                onWordBoundary: { timing in
                    wordTimings.append(timing)
                    // Send word timing immediately
                    if let timingData = try? JSONSerialization.data(withJSONObject: timing),
                       let timingString = String(data: timingData, encoding: .utf8) {
                        print("\n---WORD_TIMING---\n\(timingString)\n---AUDIO_CONTINUE---\n")
                        fflush(stdout)
                    }
                },
                onComplete: {
                    log("Synthesis complete")
                    synthesisComplete.signal()
                },
                onError: {
                    log("Synthesis error occurred")
                    hasError = true
                    synthesisComplete.signal()
                }
            )
            
            synthesizer.delegate = delegate
            
            // Start synthesis
            log("Starting synthesis")
            synthesizer.write(utterance) { buffer in
                if let audioBuffer = buffer as? AVAudioPCMBuffer {
                    // Schedule buffer for playback
                    let playerNode = AVAudioPlayerNode()
                    audioEngine.attach(playerNode)
                    audioEngine.connect(playerNode, to: mainMixer, format: format)
                    playerNode.scheduleBuffer(audioBuffer, completionHandler: nil)
                    playerNode.play()
                    
                    // Log progress
                    log("Audio buffer processed: \(audioBuffer.frameLength) frames")
                }
            }
            
            // Wait for synthesis to complete
            let timeout = DispatchTime.now() + .seconds(30)
            if synthesisComplete.wait(timeout: timeout) == .timedOut {
                log("Synthesis timed out")
                throw NSError(domain: "SpeechBridge", code: -1, userInfo: [NSLocalizedDescriptionKey: "Synthesis timed out"])
            }
            
            if hasError {
                log("Synthesis failed")
                throw NSError(domain: "SpeechBridge", code: -2, userInfo: [NSLocalizedDescriptionKey: "Synthesis failed"])
            }
            
            // Allow time for final audio to play
            Thread.sleep(forTimeInterval: 0.5)
            
            log("Synthesis completed successfully")
            print("\n---AUDIO_END---\n")
            fflush(stdout)
            
        } catch {
            log("Error during synthesis: \(error)")
            audioEngine.stop()
            audioEngine.mainMixerNode.removeTap(onBus: 0)
            throw error
        }
        
        // Clean up
        audioEngine.stop()
        audioEngine.mainMixerNode.removeTap(onBus: 0)
    }
}

SpeechBridge.main()