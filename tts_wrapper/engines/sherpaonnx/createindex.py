import requests
import json
import re
import tarfile
import os
from io import BytesIO
import langcodes  # For enriching language data

# Regex to validate ISO language codes (1-8 alphanumeric characters)
iso_code_pattern = re.compile(r"^[a-zA-Z0-9]{1,8}$")


def handle_special_cases(developer, name, quality, url):
    if developer == "mimic3":
        name_quality_match = re.search(
            r"-(?P<name>[a-zA-Z0-9_]+)-(?P<quality>low|medium|high|nwu_low|ailabs_low)",
            url,
        )
        if name_quality_match:
            name = name_quality_match.group("name")
            quality = name_quality_match.group("quality")
    if developer == "cantonese" and "hf" in url:
        name = "xiaomaiiwn" if "xiaomaiiwn" in url else name
    return name, quality


def extract_language_code_from_config(config_data):
    """
    Extracts language information from the config.json file if available.
    Returns language code and country information if present.
    """
    text_language = config_data.get("text_language", "unknown")
    if (
        text_language != "unknown"
        and text_language.isascii()
        and iso_code_pattern.match(text_language)
    ):
        # Return the language code from config.json
        return [(text_language, "Unknown")]
    return None  # Return None if language isn't found in the config


# Update function to handle fallback correctly
def extract_language_code_vits(url, name, developer, config_data=None):
    """
    Extracts the language code either from the config file or the URL.
    """
    # Try extracting from the config.json first if available
    if config_data:
        config_lang = extract_language_code_from_config(config_data)
        if config_lang:
            return config_lang

    # Fallback: Special case for models supporting multiple languages
    if "zh_en" in url or "zh_en" in name:
        return [
            ("zh", "CN"),
            ("en", "US"),
        ]  # Chinese and English with respective regions

    # Handle known developer-specific logic
    if developer == "mimic3":
        # Mimic3 follows the pattern: <lang_code>_<region>-<name>
        lang_match = re.search(r"-(?P<lang>[a-z]{2})([_-][A-Z]{2})", url)
        if lang_match:
            lang_code = lang_match.group("lang")
            region_match = re.search(
                r"_([A-Z]{2})", url
            )  # Extract region (e.g., HU, KO)
            region = region_match.group(1) if region_match else "Unknown"
            return [(lang_code, region)]
        return [("unknown", "Unknown")]

    # Generic case: match two-letter language codes with optional region (e.g., en_GB, en-US)
    lang_match = lang_code_pattern.search(url)
    if lang_match:
        lang_code = lang_match.group("lang")
        region_match = re.search(r"_([A-Z]{2})", url)  # Extract region (e.g., GB, US)
        region = region_match.group(1) if region_match else "Unknown"
        return [
            (lang_code, region)
        ]  # Return language and region as tuple (lang, country)

    if "ljs" in name.lower():
        return [("en", "US")]  # LJSpeech is US English by default

    return [("unknown", "Unknown")]


# Main function for fetching GitHub models
def get_github_release_assets(repo, tag):
    headers = {"Accept": "application/vnd.github.v3+json"}
    releases_url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    response = requests.get(releases_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch release info for tag: {tag}")

    release_info = response.json()

    assets = []
    for asset in release_info.get("assets", []):
        filename = asset["name"]
        asset_url = asset["browser_download_url"]

        # Skip executables and models from the "mms" developer
        if filename.endswith(".exe") or "-mms-" in filename:
            continue

        filename_no_ext = re.sub(r"\.tar\.bz2|\.tar\.gz|\.zip", "", filename)
        parts = filename_no_ext.split("-")

        model_type = parts[0] if parts[0] == "vits" else "unknown"
        if model_type == "unknown":
            continue

        developer = parts[1] if len(parts) > 1 else "unknown"

        # Read config.json or any other json in the archive
        config_data = read_file_from_tar_bz2(asset_url, "config.json")
        if not config_data:
            config_data = read_file_from_tar_bz2(asset_url, "*.json")  # Try fallback

        # Extract language code, prioritizing config.json, fallback to URL
        lang_codes_and_regions = extract_language_code_vits(
            filename_no_ext,
            parts[1] if len(parts) > 1 else "unknown",
            developer,
            config_data,
        )

        name = parts[3] if len(parts) > 3 else "unknown"
        quality = parts[4] if len(parts) > 4 else "unknown"

        # Handle special edge cases for developer-specific naming/quality issues
        name, quality = handle_special_cases(developer, name, quality, asset_url)

        # Get detailed language information
        lang_details = [
            get_language_data(code, region) for code, region in lang_codes_and_regions
        ]

        # Get sample rate from config.json if present, otherwise set it to 0
        sample_rate = (
            config_data.get("audio", {}).get("sample_rate", 0) if config_data else 0
        )

        id = generate_model_id(
            developer, [code for code, _ in lang_codes_and_regions], name, quality
        )

        assets.append(
            {
                "id": id,
                "model_type": model_type,
                "developer": developer,
                "name": name,  # Include the name
                "language": lang_details,  # Store detailed language data
                "quality": quality,
                "sample_rate": sample_rate,  # Use extracted or fallback sample rate
                "num_speakers": 1,
                "url": asset_url,
                "compression": True,
                "filesize_mb": round(asset["size"] / (1024 * 1024), 2),
            }
        )

    return assets


# Function to fetch data from a URL
def fetch_data_from_url(url: str) -> dict:
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


# Known ISO 639-1 language codes (you can expand this as needed)
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


# Extract detailed language information using langcodes library
def get_language_data(lang_code: str, region: str):
    if (
        lang_code == "unknown"
        or not lang_code.isascii()
        or not iso_code_pattern.match(lang_code)
    ):
        return {
            "lang_code": "unknown",
            "language_name": "Unknown",
            "country": "Unknown",
        }

    try:
        language_info = langcodes.get(lang_code)
        country = (
            region
            if region != "Unknown"
            else (language_info.maximize().region or "Unknown")
        )
        return {
            "lang_code": lang_code,
            "language_name": language_info.language_name(),
            "country": country,
        }
    except LookupError:
        pass
    return {"lang_code": lang_code, "language_name": "Unknown", "country": region}


# Function to generate a unique ID for non-MMS models
def generate_model_id(developer, lang_codes, name, quality):
    if quality != "unknown":
        return f"{developer}-{'_'.join(lang_codes)}-{name}-{quality}"
    else:
        return f"{developer}-{'_'.join(lang_codes)}-{name}"


# Read a JSON file from within a .tar.bz2 archive
def read_file_from_tar_bz2(url, filename_in_archive):
    response = requests.get(url)
    if response.status_code == 200:
        fileobj = BytesIO(response.content)
        with tarfile.open(fileobj=fileobj, mode="r:bz2") as tar:
            for member in tar.getmembers():
                if member.name.endswith(".json"):
                    file_content = tar.extractfile(member).read().decode()
                    try:
                        return json.loads(file_content)  # Parse JSON data
                    except json.JSONDecodeError:
                        print(f"Failed to parse JSON from {member.name}")
                        return None
    return None


# Function to save the merged models
def save_models(merged_models, filepath="merged_models.json"):
    with open(filepath, "w") as f:
        json.dump(merged_models, f, indent=4)
    print(f"Saved {len(merged_models)} models to {filepath}")


def merge_models(
    mms_models, published_models, output_file="merged_models.json", force=False
):
    # Load existing models if file exists and force flag is not set
    if os.path.exists(output_file) and not force:
        with open(output_file, "r") as f:
            merged_models = json.load(f)
            print("Loaded existing merged models.")
    else:
        merged_models = {}

    # Total number of models to process
    total_models = len(mms_models) + len(published_models)
    if total_models == 0:
        print("No models to merge.")
        return merged_models

    # Filter out models with developer 'mms' from published models
    filtered_published_models = [
        model for model in published_models if model["developer"] != "mms"
    ]

    # Create a dictionary for easy lookup and merging
    merged_models.update({model["id"]: model for model in filtered_published_models})

    last_saved_index = 0  # Track the last save point to avoid repetitive saving

    # Add MMS models to the merged models (MMS models default to 16000 sample rate)
    for index, mms_model in enumerate(mms_models):
        iso_code = mms_model["Iso Code"]
        language_info = get_language_data(iso_code, "Unknown")

        merged_models[iso_code] = {
            "id": iso_code,
            "model_type": "mms",
            "developer": "mms",
            "name": mms_model["Language Name"],
            "language": [language_info],
            "quality": "unknown",
            "sample_rate": 16000,  # Set to 16000 by default for MMS models
            "num_speakers": 1,
            "url": mms_model["ONNX Model URL"],
            "compression": False,
            "filesize_mb": "unknown",
        }

        # Save every 50 models or at the very end
        if (index + 1) % 50 == 0 or (index + 1) == len(mms_models):
            if last_saved_index < index + 1:
                save_models(merged_models, output_file)
                last_saved_index = index + 1  # Update last saved index

        # Print progress percentage
        progress = ((index + 1) / total_models) * 100
        print(f"Processed {index + 1}/{total_models} models ({progress:.2f}%)")

    # Final save at the end if the last model processed wasn't just saved
    if last_saved_index < len(mms_models):
        save_models(merged_models, output_file)

    return merged_models


# Main entry point
def main():
    # Step 1: Download MMS models
    mms_url = "https://huggingface.co/willwade/mms-tts-multilingual-models-onnx/raw/main/languages-supported.json"
    mms_models = fetch_data_from_url(mms_url)

    # Step 2: Fetch GitHub models (VITS, Piper, etc.)
    repo = "k2-fsa/sherpa-onnx"
    tag = "tts-models"
    output_file = "merged_models.json"
    merged_models = merge_models(mms_models, [], output_file)
    get_github_release_assets(repo, tag)


if __name__ == "__main__":
    main()
