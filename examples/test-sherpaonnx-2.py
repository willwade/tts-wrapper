import logging
from tts_wrapper import SherpaOnnxClient, SherpaOnnxTTS
import time
from io import BytesIO
from pathlib import Path


client = SherpaOnnxClient(model_path=None, tokens_path=None)

# Initialize the SherpaOnnxTTS engine with the client
tts = SherpaOnnxTTS(client=client)

# Retrieve and display available voices
voices = tts.get_voices()
logging.info(f"Available voices: {voices}")

# Set the desired voice using its ISO code
iso_code = "eng"  # Replace with a valid ISO code from the voices list
tts.set_voice(voice_id=iso_code)
logging.info(f"Voice set to ISO code: {iso_code}")

        # Define the text to be synthesized
text = (
" Title The Silent Truth "
"The town of Brookhollow was the kind of place where people left their doors unlocked and trusted everyone they met. Tucked away in the rolling hills of the countryside, it was a town where time seemed to stand still. But on a crisp October morning, something sinister shattered the peace. "
"Chapter 1 A Quiet Morning "
"Detective Emma Hayes had just finished her morning coffee when the phone rang. It was a local officer from the Brookhollow precinct. Something felt wrong from the tone of his voice. "
"'Detective Hayes, there's been an incident', Officer Morgan said, his voice tight. 'You need to come to the Harrison estate right away'. "
"The Harrison estate was the largest property in Brookhollow, home to George Harrison, a well-known philanthropist and businessman. Emma grabbed her coat, knowing instinctively that this wasn’t a routine call. "
"When she arrived, the estate was cordoned off. Police officers and forensic teams were scattered around the front lawn. Emma approached Officer Morgan, who was standing by the front entrance. "
"'What's the situation?' she asked. "
"Morgan gestured towards the house. 'George Harrison. He’s dead. The maid found him this morning, lying in his study. Looks like a murder.' "
"Emma followed him inside, her mind racing. The air was thick with tension as they entered the study. The room was tastefully decorated, books lined the walls, and a grand mahogany desk stood in the center. But the most striking thing was the body slumped over the desk, a pool of blood soaking the papers beneath George Harrison's hand. A single gunshot to the back of the head. "
"Emma examined the scene carefully. There were no signs of a struggle, and nothing seemed out of place. It was clean. Too clean. "
)
logging.info(f"Text to synthesize: {text}")

# Specify the output file and format
output_file = "output_streamed.wav"  # Change to 'output_streamed.mp3' or other formats as needed
audio_format = "wav"  # Supported formats: 'wav', 'mp3', 'flac'

# # # pausng
try:
    ssml_text = tts.ssml.add(text)
    print("ssml text")
    print(ssml_text)
    tts.speak_streamed(ssml_text)
    # Pause after 5 seconds
except Exception as e:
    print(f"Error at speak_streamed: {e}")
#   
# time.sleep(3)        
# # Demonstrate saving audio to a file
try:
    text = "Test saving speech to file for sherpaonnx"
    ssml_text = tts.ssml.add(text)
    output_file = Path(f"output_sherpaonnx.wav")
    tts.speak_streamed(ssml_text, str(output_file), audio_format='wav')
#     # or you could do
     #tts.speak(ssml_text)
    print(f"Audio content saved to {output_file}")
except Exception as e:
    print(f"Error at saving: {e}")
#   
# 