import streamlit as st
import pandas as pd
import os
import requests
import json
from tts_wrapper import (
    PollyTTS, PollyClient, MicrosoftTTS, MicrosoftClient, WatsonTTS, WatsonClient,
    GoogleTTS, GoogleClient, ElevenLabsTTS, ElevenLabsClient
)

# Load settings and create clients
def load_settings():
    try:
        with open('settings.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Settings file not found. Ensure 'settings.json' is in the correct location.")
        return {}

def create_tts_client(service, settings):
    creds = settings.get(service, {})
    if service == "polly":
        client = PollyClient(credentials=(creds['region'], creds['aws_key_id'], creds['aws_access_key']))
        tts = PollyTTS(client=client)
    elif service == "microsoft":
        client = MicrosoftClient(credentials=creds['token'], region=creds['region'])
        tts = MicrosoftTTS(client=client)
    elif service == "watson":
        client = WatsonClient(credentials=(creds['api_key'], creds['region'],creds['instance_id']))
        tts = WatsonTTS(client=client)
    elif service == "google":
        client = GoogleClient(credentials=creds['creds_path'])
        tts = GoogleTTS(client=client)
    elif service == "elevenlabs":
        client = ElevenLabsClient(credentials=creds.get('api_key'))
        tts = ElevenLabsTTS(client=client)
    else:
        raise ValueError("Unsupported TTS service")
    return tts

# Retrieve all voices from all TTS engines
def list_all_voices(tts_engines):
    voices_list = []
    for name, tts in tts_engines.items():
        try:
            for voice in tts.get_voices():
                voice_data = {
                    'Engine': name,
                    'ID': voice['id'],
                    'Language': voice['language_codes'][0],
                    'Name': voice['name'],
                    'Gender': voice['gender']
                }
                voices_list.append(voice_data)
        except Exception as e:
            st.error(f"Failed to retrieve voices from {name}: {str(e)}")
    return pd.DataFrame(voices_list)

def load_language_data():
    json_file_path = 'languages.json'
    
    # Check if the file exists locally; if not, download it
    if not os.path.exists(json_file_path):
        url = 'https://raw.githubusercontent.com/mattcg/language-subtag-registry/master/data/json/registry.json'
        response = requests.get(url)
        if response.status_code == 200:
            with open(json_file_path, 'w') as file:
                json.dump(response.json(), file)
        else:
            raise Exception("Failed to download language data")
    
    # Load data from the local file
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    
    # Map subtags to descriptions
    language_map = ["{} ({})".format(item['Description'][0], item['Subtag']) for item in data if 'Subtag' in item and 'Description' in item]
    #language_map = {item['Subtag']: item['Description'][0] for item in data if item['Type'] == 'language'}
    return language_map


# Assume you have an enhanced voices DataFrame from the TTS wrapper setup

def load_language_population():
    # This should be replaced with actual loading of a JSON or database that includes language data and population
    data = {
        'Language': ['English', 'Mandarin Chinese', 'Hindi', 'Spanish', 'French', 'Modern Standard Arabic',
                     'Bengali', 'Portuguese', 'Russian', 'Urdu', 'Indonesian', 'Standard German', 'Japanese',
                     'Nigerian Pidgin', 'Egyptian Arabic', 'Marathi', 'Telugu', 'Turkish', 'Tamil', 'Yue Chinese',
                     'Vietnamese', 'Wu Chinese', 'Tagalog', 'Korean', 'Iranian Persian', 'Hausa', 'Swahili', 'Javanese',
                     'Italian', 'Western Punjabi', 'Gujarati', 'Thai', 'Kannada', 'Amharic', 'Bhojpuri', 'Eastern Punjabi',
                     'Min Nan Chinese', 'Jin Chinese', 'Levantine Arabic', 'Yoruba'],
        'Population': [1456000000, 1138000000, 610000000, 559000000, 310000000, 274000000, 273000000, 264000000,
                       255000000, 232000000, 199000000, 133000000, 123200000, 121000000, 102000000, 99000000, 96000000,
                       90000000, 87000000, 87000000, 86000000, 83000000, 83000000, 82000000, 79000000, 79000000,
                       72000000, 68000000, 68000000, 67000000, 62000000, 61000000, 59000000, 58000000, 52000000,
                       52000000, 50000000, 48000000, 48000000, 46000000]
    }
    return pd.DataFrame(data)

def main():
    settings = load_settings()
    language_map = load_language_data()
    engines = ["elevenlabs", "polly", "google", "microsoft", "watson"]
    tts_engines = {engine: create_tts_client(engine, settings) for engine in engines}
    voices_df = list_all_voices(tts_engines)
    # Right now they are all online
    voices_df['Status'] = 'Online'
    st.title('TTS Voice Availability Analysis')

    lang_population_df = load_language_population()

    languages = sorted(voices_df['Language'].unique())
    selected_language = st.selectbox('Select a language', language_map)
    selected_language_code = selected_language.split(' ')[-1].strip('()')  # Extract the language code from the selected language
    filtered_voices = voices_df[voices_df['Language'].str.startswith(selected_language_code)]  # Filter the DataFrame based on the selected language

    # Display the relevant columns
    st.write("### Available Voices")
    st.write(filtered_voices[['Engine', 'Gender', 'Name', 'Status']])

    # Display statistics
    st.write("### Detailed Statistics")
    stats_df = voices_df.groupby(['Language', 'Engine']).size().unstack(fill_value=0)
    st.write(stats_df)

    online_status = voices_df.groupby(['Engine', 'Status']).size().unstack(fill_value=0)
    st.write("### Engine Status (Online/Offline)")
    st.write(online_status)

    # Calculate and display global language coverage
    supported_langs = set(voices_df['Language'].str[:2])
    total_langs = set(lang_population_df['Language'])
    unsupported_langs = total_langs - supported_langs

    st.write(f"### Supported Languages: {len(supported_langs)}")
    st.write(f"### Unsupported Languages: {len(unsupported_langs)}")
    unsupported_with_population = lang_population_df[lang_population_df['Language'].isin(unsupported_langs)]
    total_population = lang_population_df['Population'].sum()
    unsupported_population = unsupported_with_population['Population'].sum()
    coverage = ((total_population - unsupported_population) / total_population) * 100
    st.write(f"### Global Population Coverage by TTS: {coverage:.2f}%")

    # List unsupported languages
    st.write("### Unsupported Languages by Population")
    st.write(unsupported_with_population)

if __name__ == "__main__":
    main()
