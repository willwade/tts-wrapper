from typing import Optional

from tts_wrapper.ssml import BaseSSMLRoot, SSMLNode


class WitAiSSML(BaseSSMLRoot):

    def break_(self, time: str) -> "WitAiSSML":
        self.add(SSMLNode("break", attrs={"time": time}))
        return self

    def say_as(
        self, text: str, interpret_as: str, format: Optional[str] = None
    ) -> "WitAiSSML":
        attrs = {"interpret-as": interpret_as}
        if format:
            attrs["format"] = format
        self.add(SSMLNode("say-as", attrs=attrs, children=[text]))
        return self

    def emphasis(self, text: str, level: str = "moderate") -> "WitAiSSML":
        self.add(SSMLNode("emphasis", attrs={"level": level}, children=[text]))
        return self

    def prosody(
        self,
        text: str,
        rate: Optional[str] = None,
        pitch: Optional[str] = None,
        volume: Optional[str] = None,
    ) -> "WitAiSSML":
        attrs = {}
        if rate:
            attrs["rate"] = rate
        if pitch:
            attrs["pitch"] = pitch
        if volume:
            attrs["volume"] = volume
        self.add(SSMLNode("prosody", attrs=attrs, children=[text]))
        return self

    def phoneme(self, text: str, ph: str, alphabet: str) -> "WitAiSSML":
        self.add(
            SSMLNode(
                "phoneme", attrs={"ph": ph, "alphabet": alphabet}, children=[text]
            ),
        )
        return self

    def voice(self, text: str, style: str) -> "WitAiSSML":
        self.add(SSMLNode("voice", attrs={"style": style}, children=[text]))
        return self

    def sfx(
        self,
        text: str,
        character: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> "WitAiSSML":
        attrs = {}
        if character:
            attrs["character"] = character
        if environment:
            attrs["environment"] = environment
        self.add(SSMLNode("sfx", attrs=attrs, children=[text]))
        return self

    def clear_ssml(self) -> None:
        self._inner.clear_ssml()
