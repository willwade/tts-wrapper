import json
import os
import re
import tarfile
from io import BytesIO
from pathlib import Path

import langcodes  # For enriching language data
import requests

# Regex to validate ISO language codes (1-8 alphanumeric characters)
iso_code_pattern = re.compile(r"^[a-zA-Z0-9]{1,8}$")
lang_code_pattern = re.compile(r"-(?P<lang>[a-z]{2})([_-][A-Z]{2})?")
result_json = {}


def handle_special_cases(developer, name, quality, url):
    # Remove prefixes like 'chars_' from the quality field
    quality = re.sub(r".*?_", "", quality)

    # For Mimic3, remove quality from the name if it is part of the name
    if developer == "mimic3":
        name = re.sub(r"(_low|_medium|_high|_nwu_low|_ailabs_low)$", "", name)

        # Handle the name/quality separation logic if still needed
        name_quality_match = re.search(
            r"-(?P<name>[a-zA-Z0-9_]+)-(?P<quality>low|medium|high|nwu_low|ailabs_low)",
            url,
        )
        if name_quality_match:
            name = name_quality_match.group("name")
            quality = name_quality_match.group("quality")

    return name, quality


def extract_language_code_from_config(config_data):
    """Extracts language information from the config.json file if available.
    Returns language code and country information if present.
    """
    if config_data and isinstance(config_data, str):
        try:
            config_data = json.loads(config_data)
        except json.JSONDecodeError:
            return None

    if not isinstance(config_data, dict):
        return None

    # Prioritize extracting "text_language" or "phoneme_language"
    text_language = config_data.get("text_language", None)
    phoneme_language = config_data.get("phoneme_language", None)

    # Return valid language from config
    if (
        text_language
        and text_language.isascii()
        and re.match(r"^[a-z]{2,3}$", text_language)
    ):
        return [(text_language, "Unknown")]

    if (
        phoneme_language
        and phoneme_language.isascii()
        and re.match(r"^[a-z]{2,3}$", phoneme_language)
    ):
        return [(phoneme_language, "Unknown")]

    return None


# Function to get detailed language information using langcodes library
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


def save_models(merged_models, filepath="merged_models.json") -> None:
    with open(filepath, "w") as f:
        json.dump(merged_models, f, indent=4)


def merge_models(
    mms_models, published_models, output_file="merged_models.json", force=False,
):
    # Load existing models if file exists and force flag is not set
    if os.path.exists(output_file) and not force:
        with open(output_file) as f:
            merged_models = json.load(f)
    else:
        merged_models = {}

    # Total number of models to process
    total_models = len(mms_models) + len(published_models)
    if total_models == 0:
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
        ((index + 1) / total_models) * 100

    # Final save at the end if the last model processed wasn't just saved
    if last_saved_index < len(mms_models):
        save_models(merged_models, output_file)

    return merged_models


# Function to extract language codes from config or URL
# Updated function to prioritize language extraction
# Function to extract language codes from config or URL
def extract_language_code_vits(url, developer_type, developer, config_data=None):
    """Extract language code from VITS model URL or config."""
    filename = url.split("/")[-1]

    # Handle Piper models (e.g., vits-piper-en_GB-alan-low)
    if developer == "piper":
        lang_match = re.search(r'vits-piper-(\w+)_(\w+)-', filename)
        if lang_match:
            lang_code = lang_match.group(1).lower()
            region = lang_match.group(2)
            return [(lang_code, region)]

    # Handle Mimic3 models (e.g., vits-mimic3-pl_PL-m-ailabs_low)
    if developer == "mimic3":
        lang_match = re.search(r'vits-mimic3-(\w+)_(\w+)-', filename)
        if lang_match:
            lang_code = lang_match.group(1).lower()
            region = lang_match.group(2)
            return [(lang_code, region)]

    # Handle Coqui models (e.g., vits-coqui-sv-cv)
    if developer == "coqui":
        lang_match = re.search(r'vits-coqui-(\w+)-', filename)
        if lang_match:
            lang_code = lang_match.group(1).lower()
            return [(lang_code, "US")]  # Default to US as region for Coqui

    # Fallback to extracting from config if available
    if config_data:
        if isinstance(config_data, dict):
            lang_code = config_data.get("language", "").lower()
            if lang_code:
                return [(lang_code, "US")]

    # Default fallback
    return [("en", "US")]


def extract_piper_language_info(url):
    """Extract language information from Piper model's MODEL_CARD file."""
    # Extract language code from the filename pattern: vits-piper-{lang_code}-{name}-{quality}
    filename = url.split('/')[-1].replace('.tar.bz2', '')
    if not filename.startswith('vits-piper-'):
        return None
        
    # Pattern: vits-piper-en_GB-name-quality
    lang_match = re.search(r'vits-piper-(\w+)_(\w+)-', filename)
    if lang_match:
        lang_code = lang_match.group(1).lower()
        region = lang_match.group(2)
        return [(lang_code, region)]
        
    return None


def read_file_from_tar_bz2(url, filename_pattern):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            fileobj = BytesIO(response.content)
            with tarfile.open(fileobj=fileobj, mode="r:bz2") as tar:
                for member in tar.getmembers():
                    if filename_pattern in member.name:
                        file = tar.extractfile(member)
                        return file.read().decode() if file else None
    except Exception as e:
        print(f"Error reading {filename_pattern} from {url}: {str(e)}")
    return None


def get_supported_languages () -> dict:
    languages_url = "https://huggingface.co/willwade/mms-tts-multilingual-models-onnx/raw/main/languages-supported.json"
    response_json = fetch_data_from_url(languages_url)

    for index, model in enumerate(response_json):
        iso_code = model["Iso Code"]
        response_json[index]["Iso Code"] = "mms_" + iso_code

        url = model["ONNX Model URL"]
        new_url = url.replace("api/models/", "", 1).replace("/tree/", "/resolve/")    
        model["ONNX Model URL"] = new_url
        response_json[index]["ONNX Model URL"] = model["ONNX Model URL"]

        response_json[index] = transform_json_structure(response_json[index])
    #result_json['languages_supported'] = response_json

    return response_json

def transform_json_structure(input_data):
    """
    Transform a single JSON object to the desired format with nested language information.
    
    Args:
        input_data (dict): Input JSON data
        
    Returns:
        dict: Transformed JSON data
    """
    # Create language information dictionary
    language_info = {
        "Iso Code": input_data["Iso Code"].split('_')[-1],  # Extract 'abi' from 'mms_abi'
        "Language Name": input_data["Language Name"],
        "Country": input_data["Country"]
    }
    
    # Create new structure
    transformed_data = {
        "id": input_data["Iso Code"],
        "language": [language_info],  # Put language info in an array
        "Region": input_data["Region"],
        "ONNX Exists": input_data["ONNX Exists"],
        "Sample Exists": input_data["Sample Exists"],
        "url": input_data["ONNX Model URL"]
    }
    
    return transformed_data


def combine_json_parts(json_part1, json_part2):
    """
    Combine two JSON dictionaries, only adding 'other' if it doesn't exist in the first dict
    
    Args:
        json_part1 (dict): First JSON part as dictionary
        json_part2 (dict): Second JSON part as dictionary
    
    Returns:
        dict: Combined JSON object
    """
    # Create a copy of the first dictionary to avoid modifying the original

    combined = json_part1.copy()

    # Only add 'other' if it doesn't exist in the first dictionary
    if 'Iso Code' not in combined:
        # Create a new combined dictionary starting with the object_json
        
        # Add each item from array_json using the ISO code as the key
        for item in json_part2:
            combined[item["id"]] = item
    
    return combined    

# Function to generate a unique model ID
def generate_model_id(developer, lang_codes, name, quality) -> str:
    return (
        f"{developer}-{'_'.join(lang_codes)}-{name}-{quality}"
        if quality != "unknown"
        else f"{developer}-{'_'.join(lang_codes)}-{name}"
    )

# Function to fetch data from a URL
def fetch_data_from_url(url: str) -> dict:
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# Main function for fetching GitHub models
def get_github_release_assets(repo, tag, merged_models, output_file):
    headers = {"Accept": "application/vnd.github.v3+json"}
    releases_url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    print("\nFetching models from GitHub...")
    response = requests.get(releases_url, headers=headers)

    if response.status_code != 200:
        msg = f"Failed to fetch release info for tag: {tag}"
        raise Exception(msg)

    release_info = response.json()
    assets = release_info.get("assets", [])
    total_assets = len(assets)
    print(f"\nProcessing {total_assets} models...")
    
    for idx, asset in enumerate(assets, 1):
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
        print(f"\n[{idx}/{total_assets}] Processing {filename}")

        # Check if the model has already been processed and saved
        if filename_no_ext in merged_models:
            print(f"  → Skipping (already processed)")
            continue

        # Extract language code, prioritizing config.json, fallback to URL
        lang_codes_and_regions = extract_language_code_vits(
            asset_url,
            parts[0],
            developer,
            None  # Skip config data for faster processing
        )
        
        # Print language information
        for lang_code, region in lang_codes_and_regions:
            lang_info = get_language_data(lang_code, region)
            print(f"  → Language: {lang_info['language_name']} ({lang_info['lang_code']}, {lang_info['country']})")

        name = parts[3] if len(parts) > 3 else "unknown"
        quality = parts[4] if len(parts) > 4 else "unknown"

        # Handle special edge cases for developer-specific naming/quality issues
        name, quality = handle_special_cases(developer, name, quality, asset_url)

        # Get detailed language information
        lang_details = [
            get_language_data(code, region) for code, region in lang_codes_and_regions
        ]

        id = generate_model_id(
            developer, [code for code, _ in lang_codes_and_regions], name, quality,
        )

        model_data = {
            "id": id,
            "model_type": model_type,
            "developer": developer,
            "name": name,
            "language": lang_details,
            "quality": quality,
            "sample_rate": 22050 if developer == "piper" else 16000,  # Default sample rates
            "num_speakers": 1,
            "url": asset_url,
            "compression": True,
            "filesize_mb": round(asset["size"] / (1024 * 1024), 2),
        }

        # Add to merged models
        merged_models[id] = model_data
        print(f"  → Added model: {id}")

    print(f"\nProcessed {total_assets} models successfully!")
    return merged_models

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


# Main entry point
def main() -> None:
    output_file = "merged_models.json"

    # Step 1: Load existing models or start fresh
    try:
        with open(output_file) as f:
            merged_models = json.load(f)
    except FileNotFoundError:
        merged_models = {}

    # Step 2: Fetch GitHub models (VITS, Piper, etc.)
    repo = "k2-fsa/sherpa-onnx"
    tag = "tts-models"
    print("Build merged_models.json file\n")
    merged_models_path = Path(output_file)

    if merged_models_path.exists():
        print("merged models already exist, getting supported languages")
        with open(merged_models_path, 'r') as file:
            merge_models = json.load(file)
    else:
        merged_models = get_github_release_assets(repo, tag, merged_models, output_file)

    #add languages json to merged_models.json
    print("Get suppported languages\n")
    languages_json = get_supported_languages()

    models_languages = combine_json_parts (merged_models, languages_json)
    print (models_languages)
    save_models(models_languages, output_file)

if __name__ == "__main__":
    main()
