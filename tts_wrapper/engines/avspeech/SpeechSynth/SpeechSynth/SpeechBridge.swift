import AVFoundation

class TTSManager {
    static let synthesizer = AVSpeechSynthesizer()
    static let audioEngine = AVAudioEngine()
    static var pitchMultiplier: Float = 1.0
    static var rate: Float = 0.5
    static var volume: Float = 1.0
    static var currentDelegate: TTSDelegate? // Add this line
}


class TTSDelegate: NSObject, AVSpeechSynthesizerDelegate {
    var onWordEvent: (([String: Any]) -> Void)?

    func speechSynthesizer(
        _ synthesizer: AVSpeechSynthesizer,
        willSpeakRangeOfSpeechString characterRange: NSRange,
        utterance: AVSpeechUtterance
    ) {
        // Extract the word and its properties
        print("Delegate triggered for word range: \(characterRange)")
        let word = (utterance.speechString as NSString).substring(with: characterRange)
        print("Word event: \(word)")
        let event: [String: Any] = [
            "text_position": characterRange.location,
            "length": characterRange.length,
            "word": word
        ]
        // Trigger the callback with the event
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
        print("Error serializing voices: \(error)")
        return nil
    }
}

@_cdecl("synthesizeToByteStream")
public func synthesizeToByteStream(
    text: UnsafePointer<CChar>,
    voiceIdentifier: UnsafePointer<CChar>?,
    isSSML: Bool,
    callback: @escaping @convention(c) (UnsafePointer<UInt8>, Int, UnsafePointer<CChar>?) -> Void
) {
    let inputString = String(cString: text)
    let voiceIdentifierString = voiceIdentifier != nil ? String(cString: voiceIdentifier!) : nil

    let utterance: AVSpeechUtterance
    if isSSML {
        guard let ssmlUtterance = AVSpeechUtterance(ssmlRepresentation: inputString) else {
            print("Invalid SSML string")
            return
        }
        utterance = ssmlUtterance
    } else {
        utterance = AVSpeechUtterance(string: inputString)
    }

    if let voiceID = voiceIdentifierString, let voice = AVSpeechSynthesisVoice(identifier: voiceID) {
        utterance.voice = voice
    }
    utterance.rate = 0.5

    // Delegate to handle word events
    let delegate = TTSDelegate()
    delegate.onWordEvent = { event in
        print("Received word event: \(event)")
        if let wordData = try? JSONSerialization.data(withJSONObject: event, options: []),
           let wordCString = String(data: wordData, encoding: .utf8)?.cString(using: .utf8) {
            wordCString.withUnsafeBufferPointer { pointer in
                let emptyAudioChunk = UnsafeMutablePointer<UInt8>.allocate(capacity: 1)
                emptyAudioChunk.initialize(to: 0)
                callback(emptyAudioChunk, 0, pointer.baseAddress)
                emptyAudioChunk.deinitialize(count: 1)
                emptyAudioChunk.deallocate()
            }
        }
    }
    TTSManager.synthesizer.delegate = delegate
    
    // Use `write(_:completionHandler:)` for audio data
    TTSManager.synthesizer.write(utterance) { buffer in
        guard let pcmBuffer = buffer as? AVAudioPCMBuffer, pcmBuffer.frameLength > 0 else {
            // Perform cleanup when synthesis is finished
            TTSManager.audioEngine.stop()
            TTSManager.audioEngine.reset()
            TTSManager.synthesizer.delegate = nil
            print("Audio engine stopped")
            return
        }

        if let channelData = pcmBuffer.floatChannelData {
            let frameLength = Int(pcmBuffer.frameLength)
            let audioBytes = UnsafeBufferPointer(start: channelData[0], count: frameLength)
            let int16Data = audioBytes.map { Int16($0 * Float(Int16.max)) }
            let byteData = int16Data.flatMap { int16Sample in
                [UInt8(truncatingIfNeeded: int16Sample & 0xFF),
                 UInt8(truncatingIfNeeded: (int16Sample >> 8) & 0xFF)]
            }
            byteData.withUnsafeBufferPointer { pointer in
                callback(pointer.baseAddress!, byteData.count, nil)
            }
        }
    }

    // Ensure cleanup happens when the utterance completes
    DispatchQueue.main.async {
        while TTSManager.synthesizer.isSpeaking {
            Thread.sleep(forTimeInterval: 0.1)
        }

        TTSManager.audioEngine.stop()
        TTSManager.audioEngine.reset()
        TTSManager.synthesizer.delegate = nil
        print("Audio engine stopped")
    }
}

public func synthesizeToBytes(
    text: UnsafePointer<CChar>,
    voiceIdentifier: UnsafePointer<CChar>?,
    isSSML: Bool,
    wordTimingCallback: @escaping @convention(c) (UnsafePointer<CChar>?) -> Void
) -> UnsafePointer<UInt8>? {
    let inputString = String(cString: text)
    let voiceIdentifierString = voiceIdentifier != nil ? String(cString: voiceIdentifier!) : nil

    let audioEngine = TTSManager.audioEngine
    let mainMixer = audioEngine.mainMixerNode
    let outputFormat = mainMixer.outputFormat(forBus: 0)
    var audioData = [UInt8]()
    var wordTimings = [[String: Any]]()

    let utterance: AVSpeechUtterance
    if isSSML {
        guard let ssmlUtterance = AVSpeechUtterance(ssmlRepresentation: inputString) else {
            print("Invalid SSML string")
            return nil
        }
        utterance = ssmlUtterance
    } else {
        utterance = AVSpeechUtterance(string: inputString)
    }

    if let voiceID = voiceIdentifierString, let voice = AVSpeechSynthesisVoice(identifier: voiceID) {
        utterance.voice = voice
    }
    utterance.rate = 0.5

    let delegate = TTSDelegate()
    delegate.onWordEvent = { event in
        print("Word event: \(event)")
        wordTimings.append(event)
    }
    TTSManager.synthesizer.delegate = delegate
    TTSManager.currentDelegate = delegate

    do {
        mainMixer.installTap(onBus: 0, bufferSize: 4096, format: outputFormat) { buffer, _ in
            if let channelData = buffer.floatChannelData {
                let frameLength = Int(buffer.frameLength)
                let audioBytes = UnsafeBufferPointer(start: channelData[0], count: frameLength)
                let int16Data = audioBytes.map { Int16($0 * Float(Int16.max)) }
                let byteData = int16Data.flatMap { int16Sample in
                    [UInt8(truncatingIfNeeded: int16Sample & 0xFF),
                     UInt8(truncatingIfNeeded: (int16Sample >> 8) & 0xFF)]
                }
                audioData.append(contentsOf: byteData)
            }
        }

        audioEngine.prepare()
        try audioEngine.start()
        print("Audio engine started")

        TTSManager.synthesizer.speak(utterance)

        while TTSManager.synthesizer.isSpeaking {
            Thread.sleep(forTimeInterval: 0.1)
        }

        mainMixer.removeTap(onBus: 0)
        audioEngine.stop()

        if let wordTimingData = try? JSONSerialization.data(withJSONObject: wordTimings, options: []),
           let wordTimingJSONString = String(data: wordTimingData, encoding: .utf8) {
            wordTimingJSONString.withCString { cString in
                wordTimingCallback(strdup(cString))
            }
        }

    } catch {
        print("Error during synthesis: \(error)")
    }

    TTSManager.currentDelegate = nil
    
    let byteCount = audioData.count
    let buffer = UnsafeMutablePointer<UInt8>.allocate(capacity: byteCount)
    buffer.initialize(from: audioData, count: byteCount)
    
    return UnsafePointer(buffer)
}



