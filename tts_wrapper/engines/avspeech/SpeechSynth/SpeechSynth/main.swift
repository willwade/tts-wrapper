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
//print("\nTesting blocking synthesis...")
//let text = "Hello, this is a test."
//if let audioBytesPointer = synthesizeToBytes(text: strdup(text), voiceIdentifier: nil) {
//    print("Synthesized audio size (blocking): \(audioBytesPointer) bytes")
//} else {
//    print("Blocking synthesis failed.")
//}


// Declare and initialize the audioBuffer to collect audio chunks
var audioBuffer = [UInt8]()

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

print("\nTesting streaming synthesis...")
let inputText = strdup("Streaming test example.")

// Example callback modification
synthesizeToByteStream(text: inputText!, voiceIdentifier: nil) { chunkPointer, size in
    let chunk = Array(UnsafeBufferPointer(start: chunkPointer, count: size))
    print("Received audio chunk of size: \(chunk.count) bytes")

    // Append to audio buffer for validation
    audioBuffer.append(contentsOf: chunk)
}

// At the end of the test
saveAudioData(audioBuffer, to: "output.wav")

// Free allocated memory
free(inputText)

// Keep the run loop active for the test duration
RunLoop.current.run(until: Date().addingTimeInterval(5))
