import Foundation
import AVFoundation

class TTSManager {
    static let synthesizer = AVSpeechSynthesizer()
    static let audioEngine = AVAudioEngine()
    static var pitchMultiplier: Float = 1.0
    static var rate: Float = 0.5
    static var volume: Float = 1.0
    static var currentDelegate: TTSDelegate?
}



@_cdecl("synthToBytes")
public func synthToBytes(
    text: UnsafePointer<CChar>,
    isSSML: Bool,
    wordTimingCallback: @escaping @convention(c) (UnsafePointer<CChar>?) -> Void,
    logCallback: @escaping @convention(c) (UnsafePointer<CChar>?) -> Void
) -> UnsafeMutablePointer<UInt8>? {

    func log(_ message: String) {
        logCallback(message.cString(using: .utf8))
    }

    log("synthToBytes called")

    let inputString = String(cString: text)
    var audioData = [UInt8]()
    var processingComplete = false
    let semaphore = DispatchSemaphore(value: 0)

    let synthesizer = TTSManager.synthesizer
    let delegate = TTSDelegate()
    synthesizer.delegate = delegate

    delegate.onWordEvent = { event in
        log("Captured word event: \(event)")
        if let eventData = try? JSONSerialization.data(withJSONObject: event, options: []),
           let eventJSONString = String(data: eventData, encoding: .utf8) {
            eventJSONString.withCString { cString in
                wordTimingCallback(strdup(cString))
            }
        }
    }

    // Initialize the utterance
    let utterance: AVSpeechUtterance
    if isSSML {
        guard let ssmlUtterance = AVSpeechUtterance(ssmlRepresentation: inputString) else {
            log("Invalid SSML string")
            return nil
        }
        utterance = ssmlUtterance
    } else {
        utterance = AVSpeechUtterance(string: inputString)
    }

    utterance.voice = AVSpeechSynthesisVoice(language: "en-US")
    utterance.rate = TTSManager.rate
    utterance.pitchMultiplier = TTSManager.pitchMultiplier
    utterance.volume = TTSManager.volume

    log("Utterance details:")
    log("Text: \(utterance.speechString)")
    log("Voice: \(utterance.voice?.identifier ?? "Default voice")")
    log("Rate: \(utterance.rate), Pitch: \(utterance.pitchMultiplier), Volume: \(utterance.volume)")

    // Start processing buffers on the main thread
    DispatchQueue.main.async {
        synthesizer.write(utterance) { buffer in
            if let pcmBuffer = buffer as? AVAudioPCMBuffer {
                if pcmBuffer.frameLength > 0 {
                    // Process the audio data
                    log("PCM buffer processed, frame length: \(pcmBuffer.frameLength)")
                    if let channelData = pcmBuffer.floatChannelData {
                        let frameLength = Int(pcmBuffer.frameLength)
                        let audioBytes = UnsafeBufferPointer(start: channelData[0], count: frameLength)
                        let int16Data = audioBytes.map { Int16($0 * Float(Int16.max)) }
                        let byteData = int16Data.flatMap { int16Sample in
                            [UInt8(truncatingIfNeeded: int16Sample & 0xFF),
                            UInt8(truncatingIfNeeded: (int16Sample >> 8) & 0xFF)]
                        }
                        audioData.append(contentsOf: byteData)
                    }
                } else {
                    // Handle the final buffer
                    log("Final buffer received, synthesis complete")
                    processingComplete = true
                    semaphore.signal()
                }
            } else {
                log("No frame data or end of synthesis")
                processingComplete = true
                semaphore.signal()
            }
        }
    }

    // Run the main run loop to keep the process alive
    let runLoop = RunLoop.current
    let timeout = Date().addingTimeInterval(15)
    while !processingComplete && runLoop.run(mode: .default, before: Date(timeIntervalSinceNow: 0.1)) {
        if Date() > timeout {
            log("Synthesis timed out")
            return nil
        }
    }

    // Wait for the semaphore to ensure processing completion
    semaphore.wait()

    log("Synthesis complete")
    log("Audio data length: \(audioData.count)")

    if audioData.isEmpty {
        log("No audio data captured")
        return nil
    }

    // Convert audio data to an UnsafePointer
    let byteCount = audioData.count
    let combinedPointer = UnsafeMutablePointer<UInt8>.allocate(capacity: byteCount + MemoryLayout<Int>.size)

    // Store the length at the start
    let lengthPointer = combinedPointer.withMemoryRebound(to: Int.self, capacity: 1) { $0 }
    lengthPointer.pointee = byteCount

    // Store the audio data after the length
    combinedPointer.advanced(by: MemoryLayout<Int>.size).update(from: audioData, count: byteCount)

    return combinedPointer

}

class TTSDelegate: NSObject, AVSpeechSynthesizerDelegate {
    var onWordEvent: (([String: Any]) -> Void)?

    func speechSynthesizer(
        _ synthesizer: AVSpeechSynthesizer,
        willSpeakRangeOfSpeechString characterRange: NSRange,
        utterance: AVSpeechUtterance
    ) {
        let word = (utterance.speechString as NSString).substring(with: characterRange)
        let event: [String: Any] = [
            "word": word,
            "range": [
                "location": characterRange.location,
                "length": characterRange.length
            ]
        ]
        onWordEvent?(event)
    }
}


// Set parameters
@_cdecl("setPitch")
public func setPitch(pitch: Float) {
    TTSManager.pitchMultiplier = pitch
}

@_cdecl("setRate")
public func setRate(rate: Float) {
    TTSManager.rate = rate
}

@_cdecl("setVolume")
public func setVolume(volume: Float) {
    TTSManager.volume = volume
}

// Get parameters
@_cdecl("getPitch")
public func getPitch() -> Float {
    return TTSManager.pitchMultiplier
}

@_cdecl("getRate")
public func getRate() -> Float {
    return TTSManager.rate
}

@_cdecl("getVolume")
public func getVolume() -> Float {
    return TTSManager.volume
}

@_cdecl("getVoice")
public func getVoice() -> UnsafePointer<CChar>? {
    // Get the default voice (adjust language as needed)
    let systemVoice = AVSpeechSynthesisVoice(language: Locale.current.identifier)
                      ?? AVSpeechSynthesisVoice(language: "en-US") // Fallback to en-US

    guard let voiceIdentifier = systemVoice?.identifier else {
        return nil // No voice available
    }

    // Convert the string to a C-compatible string and cast to UnsafePointer<CChar>
    return UnsafePointer(strdup(voiceIdentifier))
}

// Voice Information
@_cdecl("getVoices")
public func getVoices() -> UnsafePointer<CChar>? {
    let voices = AVSpeechSynthesisVoice.speechVoices().map { voice in
        [
            "id": voice.identifier,
            "name": voice.name,
            "language": voice.language
        ]
    }
    do {
        let data = try JSONSerialization.data(withJSONObject: voices, options: [])
        let jsonString = String(data: data, encoding: .utf8)
        if let cString = jsonString.flatMap({ strdup($0) }) {
            return UnsafePointer(cString) // Explicitly cast to UnsafePointer<CChar>
        } else {
            return nil
        }
    } catch {
        return nil
    }
}