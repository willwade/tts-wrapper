import Foundation

//print("Testing getVoices...")
//if let voicesPointer = getVoices() {
//    let voicesJSON = String(cString: voicesPointer)
//    print("Available voices: \(voicesJSON)")
//    free(UnsafeMutablePointer(mutating: voicesPointer)) // Free the memory allocated by strdup
//} else {
//    print("Failed to retrieve voices.")
//}
//

// Declare and initialize the audioBuffer to collect audio chunks
// Initialize buffers to store audio chunks and word timings
var audioBuffer = [UInt8]()
var wordTimingsBuffer = [[String: Any]]()

// Save audio data to file
func saveAudioData(_ audioData: [UInt8], to fileName: String) {
    let url = URL(fileURLWithPath: FileManager.default.currentDirectoryPath).appendingPathComponent(fileName)
    do {
        let data = Data(audioData)
        try data.write(to: url)
        print("Audio data saved to \(fileName)")
    } catch {
        print("Failed to save audio data: \(error)")
    }
}

// Save word timings to a JSON file
func saveWordTimings(_ wordTimings: [[String: Any]], to fileName: String) {
    let url = URL(fileURLWithPath: FileManager.default.currentDirectoryPath).appendingPathComponent(fileName)
    print(url)
    do {
        let data = try JSONSerialization.data(withJSONObject: wordTimings, options: .prettyPrinted)
        try data.write(to: url)
        print("Word timings saved to \(fileName)")
    } catch {
        print("Failed to save word timings: \(error)")
    }
}

print("\nTesting streaming synthesis...")
let inputText = strdup("Streaming test example.")
audioBuffer.removeAll()
wordTimingsBuffer.removeAll()

synthesizeToByteStream(text: inputText!, voiceIdentifier: nil, isSSML: false) { chunkPointer, size, wordPointer in
    // Process the audio chunk
    let chunk = Array(UnsafeBufferPointer(start: chunkPointer, count: size))
    audioBuffer.append(contentsOf: chunk)
    print("Received audio chunk of size: \(chunk.count) bytes")

    // Process the word event
    if let wordPointer = wordPointer {
        let wordEventString = String(cString: wordPointer)
        print("Received word event: \(wordEventString)")

        // Convert the JSON string into a dictionary
        if let data = wordEventString.data(using: .utf8),
           let wordEvent = try? JSONSerialization.jsonObject(with: data, options: []) as? [String: Any] {
            wordTimingsBuffer.append(wordEvent) // Append as dictionary
        } else {
            print("Failed to parse word event JSON: \(wordEventString)")
        }
    }
}

// Save results
saveAudioData(audioBuffer, to: "output.wav")
saveWordTimings(wordTimingsBuffer, to: "word_timings.json")

free(inputText)
RunLoop.current.run(until: Date().addingTimeInterval(5))



// Test blocking synthesis
print("\nTesting blocking synthesis...")
let inputTextBytes = strdup("Blocking synthesis test example.") // Input text for blocking
audioBuffer.removeAll() // Clear buffer for the next test
var wordTimings: [[String: Any]] = [] // Clear word timings buffer for the next test

synthesizeToBytes(text: inputTextBytes!, voiceIdentifier: nil, isSSML: false) { wordTimingsPointer in
    if let wordTimingsPointer = wordTimingsPointer {
        let wordTimingsJSON = String(cString: wordTimingsPointer)
        print("Received word timings JSON: \(wordTimingsJSON)")
        free(UnsafeMutablePointer(mutating: wordTimingsPointer))
        
        // Deserialize JSON string into [[String: Any]]
        if let data = wordTimingsJSON.data(using: .utf8) {
            do {
                wordTimings = try JSONSerialization.jsonObject(with: data, options: []) as? [[String: Any]] ?? []
            } catch {
                print("Failed to parse word timings JSON: \(error)")
            }
        }
    }
}!.withMemoryRebound(to: UInt8.self, capacity: 1) { bufferPointer in
    // Copy audio bytes into the buffer
    audioBuffer.append(contentsOf: UnsafeBufferPointer(start: bufferPointer, count: audioBuffer.count))
}

// Save the blocking results
saveAudioData(audioBuffer, to: "blocking_output.wav")
saveWordTimings(wordTimings, to: "blocking_word_timings.json")

free(inputTextBytes)
