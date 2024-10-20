import requests
import json
import re


def get_github_release_assets(repo, tag):
    headers = {"Accept": "application/vnd.github.v3+json"}

    # Get the release ID for the specified tag
    releases_url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    response = requests.get(releases_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch release info for tag: {tag}")

    release_info = response.json()

    # Known ISO 639-1 language codes and some special cases
    known_lang_codes = {
        "en": "English",
        "zh": "Chinese",
        "fr": "French",
        "de": "German",
        "es": "Spanish",
        "pl": "Polish",
        "pt": "Portuguese",
        "ro": "Romanian",
        "sk": "Slovak",
        "sl": "Slovenian",
        "sv": "Swedish",
        "uk": "Ukrainian",
        "bn": "Bengali",
        "bg": "Bulgarian",
        "cs": "Czech",
        "et": "Estonian",
        "fi": "Finnish",
        "ga": "Irish",
        "hr": "Croatian",
        "lt": "Lithuanian",
        "lv": "Latvian",
        "mai": "Maithili",
        "af": "Afrikaans",
        "el": "Greek",
        "fa": "Persian",
        "gu": "Gujarati",
        "tn": "Tswana",
    }

    # Regex to match language codes in filenames or URLs
    lang_code_pattern = re.compile(r"-(?P<lang>[a-z]{2})([_-][A-Z]{2})?-")

    def extract_language_code_vits(url, name):
        # Special case for models supporting multiple languages like 'zh_en'
        if "zh_en" in url or "zh_en" in name:
            return ["zh", "en"]  # Multiple languages: Chinese and English

        # Match two-letter language codes or language-region patterns (e.g., af_ZA, el_GR)
        lang_match = lang_code_pattern.search(url)

        if lang_match:
            lang_code = lang_match.group("lang")
            if lang_code in known_lang_codes:
                return lang_code

        # Handle specific known model names
        if "ljs" in name.lower():
            return "en"  # LJSpeech is English

        # Fallback to "unknown" if no match found
        return "unknown"

    # Get the assets
    assets = []
    for asset in release_info.get("assets", []):
        filename = asset["name"]
        asset_url = asset["browser_download_url"]

        # Skip files that are executables (.exe)
        if filename.endswith(".exe"):
            continue

        # Remove the file extension for further processing
        filename_no_ext = re.sub(r"\.tar\.bz2|\.tar\.gz|\.zip", "", filename)
        parts = filename_no_ext.split("-")

        # Determine model type
        if parts[0] == "vits":
            model_type = "vits"
        elif "sherpa" in parts[0]:
            model_type = "sherpa-onnx"
        elif "icefall" in parts[0]:
            model_type = "icefall"
        else:
            model_type = "unknown"

        # Skip if model_type is unknown
        if model_type == "unknown":
            continue

        # Extract the language code using the updated extraction logic
        lang_code = extract_language_code_vits(
            filename_no_ext, parts[1] if len(parts) > 1 else "unknown"
        )

        # Handle VITS and Sherpa-specific parsing for names and quality
        if model_type == "vits":
            name = parts[3] if len(parts) > 3 else "unknown"
            quality = parts[4] if len(parts) > 4 else "unknown"
        elif model_type == "sherpa-onnx" or model_type == "icefall":
            name = parts[2] if len(parts) > 2 else "unknown"
            quality = parts[3] if len(parts) > 3 else "unknown"
        else:
            name = "unknown"
            quality = "unknown"

        # Simulated logic for sample rate and num speakers (based on model name or a database lookup)
        sample_rate = (
            22050 if "en_US" in filename else 16000
        )  # Default logic, adjust as needed
        num_speakers = (
            1
            if "single-speaker" in filename
            else int(parts[-2]) if "multi-speaker" in filename else 1
        )

        # Determine if the asset is compressed
        compression = filename.endswith((".tar.bz2", ".tar.gz", ".zip"))

        # Add asset info to the list
        assets.append(
            {
                "model_type": model_type,
                "developer": parts[1] if len(parts) > 1 else "unknown",
                "language": {"lang_code": lang_code},
                "name": name,
                "quality": quality,
                "sample_rate": sample_rate,
                "num_speakers": num_speakers,
                "url": asset_url,
                "compression": compression,
                "filesize_mb": round(
                    asset["size"] / (1024 * 1024), 2
                ),  # Convert from bytes to MB
            }
        )

    # Convert the list of assets to JSON
    assets_json = json.dumps(assets, indent=4)

    return assets_json


# Example usage
repo = "k2-fsa/sherpa-onnx"
tag = "tts-models"
assets_json = get_github_release_assets(repo, tag)
print(assets_json)
