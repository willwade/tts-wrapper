from ...exceptions import ModuleNotInstalled


class DeepLearningClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.deeplearningtts.com"

    def synth(self, text, voice, format):
        headers = {'API-Key': self.api_key}
        data = {'text': text, 'voice': voice, 'outputFormat': format}
        response = requests.post(f"{self.base_url}/synthesize", headers=headers, json=data)
        return response.content

    def get_voices(self):
        headers = {'API-Key': self.api_key}
        response = requests.get(f"{self.base_url}/voices", headers=headers)
        return response.json()
