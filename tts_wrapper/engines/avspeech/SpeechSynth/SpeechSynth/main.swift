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

print("\nTesting streaming synthesis...")
let inputText = strdup("Streaming test example.")
synthesizeToByteStream(text: inputText!, voiceIdentifier: nil) { chunkPointer, size in
    let chunk = Array(UnsafeBufferPointer(start: chunkPointer, count: size))
    print("Received audio chunk of size: \(chunk.count) bytes")
}
free(inputText)
RunLoop.current.run(until: Date().addingTimeInterval(5))
