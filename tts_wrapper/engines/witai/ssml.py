from . import BaseSSMLRoot, SSMLNode, Child

class WitSSML(BaseSSMLRoot):
    def break_(self, time: str) -> "WitSSML":
        self.add(SSMLNode("break", attrs={"time": time}))
        return self

    def say_as(self, text: str, interpret_as: str, format: str = None) -> "WitSSML":
        attrs = {"interpret-as": interpret_as}
        if format:
            attrs["format"] = format
        self.add(SSMLNode("say-as", attrs=attrs, children=[text]))
        return self

    def emphasis(self, text: str, level: str = "moderate") -> "WitSSML":
        self.add(SSMLNode("emphasis", attrs={"level": level}, children=[text]))
        return self

    def prosody(self, text: str, rate: str = None, pitch: str = None, volume: str = None) -> "WitSSML":
        attrs = {}
        if rate:
            attrs["rate"] = rate
        if pitch:
            attrs["pitch"] = pitch
        if volume:
            attrs["volume"] = volume
        self.add(SSMLNode("prosody", attrs=attrs, children=[text]))
        return self

    def phoneme(self, text: str, ph: str, alphabet: str) -> "WitSSML":
        self.add(SSMLNode("phoneme", attrs={"ph": ph, "alphabet": alphabet}, children=[text]))
        return self

    def voice(self, text: str, style: str) -> "WitSSML":
        self.add(SSMLNode("voice", attrs={"style": style}, children=[text]))
        return self

    def sfx(self, text: str, character: str = None, environment: str = None) -> "WitSSML":
        attrs = {}
        if character:
            attrs["character"] = character
        if environment:
            attrs["environment"] = environment
        self.add(SSMLNode("sfx", attrs=attrs, children=[text]))
        return self