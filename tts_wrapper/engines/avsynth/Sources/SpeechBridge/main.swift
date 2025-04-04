import Foundation
import AVFoundation
import ArgumentParser

// Extensions for converting integers to bytes
extension UInt32 {
    var bytes: [UInt8] {
        var value = self
        return withUnsafeBytes(of: &value) { Array($0) }
    }
}

extension UInt16 {
    var bytes: [UInt8] {
        var value = self
        return withUnsafeBytes(of: &value) { Array($0) }
    }
}

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

// Define SpeechDelegate at file scope
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

        let delegate = SpeechDelegate(
            spokenText: text,
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

            // Add WAV header to the audio data
            let sampleRate: UInt32 = 16000
            let numChannels: UInt16 = 1
            let bitsPerSample: UInt16 = 16
            let byteRate = sampleRate * UInt32(numChannels * bitsPerSample / 8)
            let blockAlign = numChannels * bitsPerSample / 8
            let dataSize = UInt32(audioData.count)
            let fileSize = 36 + dataSize

            var wavHeader = Data()

            // RIFF header
            wavHeader.append(contentsOf: "RIFF".utf8)  // ChunkID
            wavHeader.append(contentsOf: UInt32(fileSize).littleEndian.bytes)  // ChunkSize
            wavHeader.append(contentsOf: "WAVE".utf8)  // Format

            // fmt subchunk
            wavHeader.append(contentsOf: "fmt ".utf8)  // Subchunk1ID
            wavHeader.append(contentsOf: UInt32(16).littleEndian.bytes)  // Subchunk1Size (16 for PCM)
            wavHeader.append(contentsOf: UInt16(1).littleEndian.bytes)  // AudioFormat (1 for PCM)
            wavHeader.append(contentsOf: numChannels.littleEndian.bytes)  // NumChannels
            wavHeader.append(contentsOf: sampleRate.littleEndian.bytes)  // SampleRate
            wavHeader.append(contentsOf: byteRate.littleEndian.bytes)  // ByteRate
            wavHeader.append(contentsOf: blockAlign.littleEndian.bytes)  // BlockAlign
            wavHeader.append(contentsOf: bitsPerSample.littleEndian.bytes)  // BitsPerSample

            // data subchunk
            wavHeader.append(contentsOf: "data".utf8)  // Subchunk2ID
            wavHeader.append(contentsOf: dataSize.littleEndian.bytes)  // Subchunk2Size

            // Combine header and audio data
            let wavData = wavHeader + audioData

            // Create response
            let response: [String: Any] = [
                "audio_data": [UInt8](wavData),
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
        let plainText: String

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
            plainText = text
        } else {
            log("Using plain text synthesis")
            utterance = AVSpeechUtterance(string: text)
            plainText = text

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
        var hasError = false
        var isComplete = false

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

        // First synthesize to get word timings
        synthesizer.write(utterance) { _ in }

        // Wait for completion
        let startTime = Date()
        while !isComplete && !hasError {
            if Date().timeIntervalSince(startTime) > 30 {
                log("Synthesis timed out")
                throw NSError(domain: "SpeechBridge", code: -1, userInfo: [NSLocalizedDescriptionKey: "Synthesis timed out"])
            }
            RunLoop.current.run(mode: .default, before: Date(timeIntervalSinceNow: 0.1))
        }

        // Send format info with word timings
        let formatInfo: [String: Any] = [
            "sample_rate": 16000,
            "channels": 1,
            "sample_format": "int16",
            "word_timings": wordTimings
        ]

        if let jsonData = try? JSONSerialization.data(withJSONObject: formatInfo),
           let jsonString = String(data: jsonData, encoding: .utf8) {
            print(jsonString)
        }

        print("---AUDIO_START---")

        // Now stream the audio
        synthesizer.write(utterance) { buffer in
            if let audioBuffer = buffer as? AVAudioPCMBuffer {
                // Convert float samples to 16-bit PCM
                let frameCount = Int(audioBuffer.frameLength)
                var pcmData = Data(capacity: frameCount * 2)

                if let channelData = audioBuffer.floatChannelData?[0] {
                    for i in 0..<frameCount {
                        let sample = channelData[i]
                        let intSample = Int16(max(-1.0, min(1.0, sample)) * 32767.0)
                        pcmData.append(UInt8(intSample & 0xFF))
                        pcmData.append(UInt8((intSample >> 8) & 0xFF))
                    }
                }

                // Write PCM data directly to stdout
                FileHandle.standardOutput.write(pcmData)
            }
        }
    }
}

SpeechBridge.main()