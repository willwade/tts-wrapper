from __future__ import annotations

from dataclasses import dataclass

import langcodes


@dataclass
class StandardizedLanguage:
    """Standardized language information across all TTS engines."""

    iso639_3: str
    bcp47: str
    display_name: str
    country_code: str | None = None


class LanguageNormalizer:
    """Helper class to normalize language codes across different formats."""

    @staticmethod
    def normalize(
        lang_code: str, country_code: str | None = None
    ) -> StandardizedLanguage:
        """
        Normalize a language code to standard formats.

        Args:
            lang_code: Input language code (can be ISO639-1/2/3, BCP47, or locale)
            country_code: Optional country code to help with regionalization

        Returns:
            StandardizedLanguage object containing normalized codes
        """
        try:
            # Handle MMS prefix if present
            lang_code = lang_code.removeprefix("mms_")

            # Parse the input language code
            lang = langcodes.get(lang_code)

            # If country code is provided, include it in the language tag
            if country_code:
                lang = lang.update_region(country_code)

            return StandardizedLanguage(
                iso639_3=lang.to_alpha3(),
                bcp47=str(lang),
                display_name=lang.display_name(),
                country_code=lang.region,
            )
        except (LookupError, ValueError):
            # Fallback for unknown codes
            return StandardizedLanguage(
                iso639_3="und", bcp47="und", display_name="Unknown", country_code=None
            )
