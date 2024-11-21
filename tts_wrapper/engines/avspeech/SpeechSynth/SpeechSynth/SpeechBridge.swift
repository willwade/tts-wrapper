import AVFoundation

class TTSManager {
    static let synthesizer = AVSpeechSynthesizer()
    static let audioEngine = AVAudioEngine()
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
    callback: @escaping @convention(c) (UnsafePointer<UInt8>, Int) -> Void
) {
    let textString = String(cString: text)
    let voiceIdentifierString = voiceIdentifier != nil ? String(cString: voiceIdentifier!) : nil

    let audioEngine = TTSManager.audioEngine
    let mainMixer = audioEngine.mainMixerNode
    let outputFormat = mainMixer.outputFormat(forBus: 0)

    let utterance = AVSpeechUtterance(string: textString)
    if let voiceID = voiceIdentifierString, let voice = AVSpeechSynthesisVoice(identifier: voiceID) {
        utterance.voice = voice
    }
    utterance.rate = 0.5

    do {
        // Install tap to capture audio
        mainMixer.installTap(onBus: 0, bufferSize: 1024, format: outputFormat) { buffer, _ in
            if let channelData = buffer.floatChannelData {
                let frameLength = Int(buffer.frameLength)
                let audioBytes = UnsafeBufferPointer(start: channelData[0], count: frameLength)
                let int16Data = audioBytes.map { Int16($0 * Float(Int16.max)) }
                let byteData = int16Data.flatMap { int16Sample in
                    [UInt8(truncatingIfNeeded: int16Sample & 0xFF),
                     UInt8(truncatingIfNeeded: (int16Sample >> 8) & 0xFF)]
                }
                byteData.withUnsafeBufferPointer { pointer in
                    callback(pointer.baseAddress!, byteData.count)
                }
            }
        }

        // Prepare and start the audio engine
        audioEngine.prepare()
        try audioEngine.start()
        print("Audio engine started")

        // Generate audio data using AVSpeechSynthesizer
        TTSManager.synthesizer.write(utterance) { buffer in
            guard let pcmBuffer = buffer as? AVAudioPCMBuffer, pcmBuffer.frameLength > 0 else {
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
                    callback(pointer.baseAddress!, byteData.count)
                }
            }
        }

        // Wait for synthesis to complete
        while TTSManager.synthesizer.isSpeaking {
            Thread.sleep(forTimeInterval: 0.1)
        }

        // Cleanup
        mainMixer.removeTap(onBus: 0)
        audioEngine.stop()
        print("Audio engine stopped")

    } catch {
        print("Error during synthesis: \(error)")
    }
}

// Synthesize Speech to Bytes (Blocking)
@_cdecl("synthesizeToBytes")
public func synthesizeToBytes(text: UnsafePointer<CChar>, voiceIdentifier: UnsafePointer<CChar>?) -> UnsafePointer<UInt8>? {
    let textString = String(cString: text)
    let voiceIdentifierString = voiceIdentifier != nil ? String(cString: voiceIdentifier!) : nil
    let synthesizer = TTSManager.synthesizer
    let audioEngine = TTSManager.audioEngine
    let mainMixer = audioEngine.mainMixerNode
    let outputFormat = mainMixer.outputFormat(forBus: 0)
    var audioData = [UInt8]()

    let utterance = AVSpeechUtterance(string: textString)
    if let voiceID = voiceIdentifierString, let voice = AVSpeechSynthesisVoice(identifier: voiceID) {
        utterance.voice = voice
    }
    utterance.rate = 0.5

    do {
        mainMixer.installTap(onBus: 0, bufferSize: 1024, format: outputFormat) { buffer, _ in
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
        synthesizer.speak(utterance)

        // Wait for synthesis to complete
        while synthesizer.isSpeaking {
            Thread.sleep(forTimeInterval: 0.1)
        }

        mainMixer.removeTap(onBus: 0)
        audioEngine.stop()

    } catch {
        print("Error during synthesis: \(error)")
    }

    let byteCount = audioData.count
    let buffer = UnsafeMutablePointer<UInt8>.allocate(capacity: byteCount)

    // Copy audioData contents into the buffer
    buffer.initialize(from: audioData, count: byteCount)

    // Return the pointer to the buffer
    return UnsafePointer(buffer)
}
