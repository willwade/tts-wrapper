import json
import logging
import re
import tarfile
from io import BytesIO
from pathlib import Path
from typing import Any

import langcodes  # For enriching language data
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Regex to validate ISO language codes (1-8 alphanumeric characters)
iso_code_pattern = re.compile(r"^[a-zA-Z0-9]{1,8}$")
lang_code_pattern = re.compile(r"-(?P<lang>[a-z]{2})([_-][A-Z]{2})?")
result_json = {}


def validate_url(url: str, timeout: int = 10) -> bool:
    """Validate if a URL is accessible and returns a valid response.

    Args:
        url: The URL to validate
        timeout: Request timeout in seconds

    Returns:
        True if URL is accessible, False otherwise
    """
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        # Accept 200 (OK) and 302 (Found/Redirect) as valid responses
        return response.status_code in [200, 302]
    except requests.RequestException as e:
        logger.warning(f"URL validation failed for {url}: {e}")
        return False


def test_model_generation(model_data: dict[str, Any], test_text: str = "Hello world") -> bool:
    """Test if a model can generate audio bytes.

    Args:
        model_data: Model configuration dictionary
        test_text: Text to synthesize for testing

    Returns:
        True if model generates audio successfully, False otherwise
    """
    try:
        # Import here to avoid circular imports and handle missing dependencies
        from tts_wrapper.engines.sherpaonnx.client import SherpaOnnxClient

        logger.info(f"Testing model: {model_data['id']}")

        # Create a temporary client with the model
        client = SherpaOnnxClient(model_id=model_data['id'], no_default_download=False)

        # Try to generate audio bytes
        audio_bytes = client.synth_to_bytes(test_text)

        # Check if we got valid audio data
        if audio_bytes and len(audio_bytes) > 0:
            logger.info(f"✓ Model {model_data['id']} generated {len(audio_bytes)} bytes of audio")
            return True
        logger.warning(f"✗ Model {model_data['id']} generated empty audio")
        return False

    except Exception as e:
        logger.error(f"✗ Model {model_data['id']} failed to generate audio: {e}")
        return False


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
    filepath_path = Path(filepath)
    with filepath_path.open("w") as f:
        json.dump(merged_models, f, indent=4)


def merge_models(
    mms_models,
    published_models,
    output_file="merged_models.json",
    force=False,
):
    # Load existing models if file exists and force flag is not set
    output_path = Path(output_file)
    if output_path.exists() and not force:
        with output_path.open() as f:
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
        if (
            (index + 1) % 50 == 0 or (index + 1) == len(mms_models)
        ) and last_saved_index < index + 1:
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
        lang_match = re.search(r"vits-piper-(\w+)_(\w+)-", filename)
        if lang_match:
            lang_code = lang_match.group(1).lower()
            region = lang_match.group(2)
            return [(lang_code, region)]

    # Handle Mimic3 models - try URL patterns first
    if developer == "mimic3":
        # Try standard pattern first (e.g., vits-mimic3-pl_PL-m-ailabs_low)
        lang_match = re.search(r"vits-mimic3-(\w+)_(\w+)-", filename)
        if lang_match:
            lang_code = lang_match.group(1).lower()
            region = lang_match.group(2)
            return [(lang_code, region)]

        # Try simple pattern (e.g., vits-mimic3-fa-haaniye_low)
        lang_match = re.search(r"vits-mimic3-([a-z]{2})-", filename.lower())
        if lang_match:
            lang_code = lang_match.group(1)
            try:
                language = langcodes.get(lang_code)
                region = language.maximize().region
                if region:
                    return [(lang_code, region)]
            except LookupError:
                pass
            return [(lang_code, "Unknown")]

        # If URL patterns fail, try getting info from README
        lang_info = extract_mimic3_language_info(url)
        if lang_info:
            return lang_info

    # Handle Coqui models (e.g., vits-coqui-sv-cv)
    if developer == "coqui":
        lang_match = re.search(r"vits-coqui-(\w+)-", filename)
        if lang_match:
            lang_code = lang_match.group(1).lower()
            try:
                # Get the proper region from langcodes
                language = langcodes.get(lang_code)
                region = language.maximize().region
                if region:
                    return [(lang_code, region)]
            except LookupError:
                pass
            return [(lang_code, "Unknown")]

    # Handle Kokoro models (e.g., kokoro-en-v0_19, kokoro-multi-lang-v1_0)
    if developer == "kokoro":
        # Handle multi-language models
        if "multi-lang" in filename:
            # Kokoro multi-lang supports Chinese and English
            return [("zh", "CN"), ("en", "US")]

        # Handle single language models
        lang_match = re.search(r"kokoro-(\w+)-", filename)
        if lang_match:
            lang_code = lang_match.group(1).lower()
            try:
                # Get the proper region from langcodes
                language = langcodes.get(lang_code)
                region = language.maximize().region
                if region:
                    return [(lang_code, region)]
            except LookupError:
                pass
            return [(lang_code, "Unknown")]

    # Fallback to extracting from config if available
    if config_data and isinstance(config_data, dict):
        lang_code = config_data.get("language", "").lower()
        if lang_code:
            return [(lang_code, "Unknown")]

    # Try to extract from URL if no other method worked
    lang_match = lang_code_pattern.search(url)
    if lang_match:
        return [(lang_match.group("lang"), "Unknown")]

    return [("unknown", "Unknown")]


def extract_piper_language_info(url):
    """Extract language information from Piper model's MODEL_CARD file."""
    # Extract language code from the filename pattern: vits-piper-{lang_code}-{name}-{quality}
    filename = url.split("/")[-1].replace(".tar.bz2", "")
    if not filename.startswith("vits-piper-"):
        return None

    # Pattern: vits-piper-en_GB-name-quality
    lang_match = re.search(r"vits-piper-(\w+)_(\w+)-", filename)
    if lang_match:
        lang_code = lang_match.group(1).lower()
        region = lang_match.group(2)
        return [(lang_code, region)]

    return None


def extract_mimic3_language_info(url):
    """Extract language information from Mimic3 model's README file."""
    try:
        readme_content = read_file_from_tar_bz2(url, "README.md")
        if not readme_content:
            return None

        # Convert bytes to string if necessary
        if isinstance(readme_content, bytes):
            readme_content = readme_content.decode("utf-8", errors="ignore")

        # Try to find language information in the first line
        first_line = readme_content.split("\n")[0].lower()

        # Common language mappings
        language_mappings = {
            "persian": "fa",
            "farsi": "fa",
            "english": "en",
            "spanish": "es",
            "french": "fr",
            "german": "de",
            "italian": "it",
            "portuguese": "pt",
            "russian": "ru",
            "chinese": "zh",
            "japanese": "ja",
            "korean": "ko",
        }

        # Try to find any of the language names in the first line
        for lang_name, lang_code in language_mappings.items():
            if lang_name in first_line:
                try:
                    # Get the proper region from langcodes
                    language = langcodes.get(lang_code)
                    region = language.maximize().region
                    if region:
                        return [(lang_code, region)]
                except LookupError:
                    pass
                return [(lang_code, "Unknown")]

        # If we can't find a match, try to find any ISO language code in the URL
        url_match = re.search(r"vits-mimic3-([a-z]{2})-", url.lower())
        if url_match:
            lang_code = url_match.group(1)
            try:
                language = langcodes.get(lang_code)
                region = language.maximize().region
                if region:
                    return [(lang_code, region)]
            except LookupError:
                pass
            return [(lang_code, "Unknown")]

    except Exception as e:
        print(f"Error extracting Mimic3 language info: {e!s}")

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
        print(f"Error reading {filename_pattern} from {url}: {e!s}")
    return None


def get_supported_languages() -> dict:
    languages_url = "https://huggingface.co/willwade/mms-tts-multilingual-models-onnx/raw/main/languages-supported.json"
    response_json = fetch_data_from_url(languages_url)

    for index, model in enumerate(response_json):
        iso_code = model["Iso Code"]
        response_json[index]["Iso Code"] = "mms_" + iso_code

        # Fix the URL to point to the base directory for MMS models
        url = model["ONNX Model URL"]
        new_url = url.replace("api/models/", "", 1).replace("/tree/", "/resolve/")
        model["ONNX Model URL"] = new_url
        response_json[index]["ONNX Model URL"] = model["ONNX Model URL"]

        response_json[index] = transform_json_structure(response_json[index])
    # result_json['languages_supported'] = response_json

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
        "Iso Code": input_data["Iso Code"].split("_")[
            -1
        ],  # Extract 'abi' from 'mms_abi'
        "Language Name": input_data["Language Name"],
        "Country": input_data["Country"],
    }

    # Create new structure
    return {
        "id": input_data["Iso Code"],
        "language": [language_info],  # Put language info in an array
        "Region": input_data["Region"],
        "ONNX Exists": input_data["ONNX Exists"],
        "Sample Exists": input_data["Sample Exists"],
        "url": input_data["ONNX Model URL"],
    }


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
    if "Iso Code" not in combined:
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
    logger.info("Fetching models from GitHub...")

    try:
        response = requests.get(releases_url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        msg = f"Failed to fetch release info for tag {tag}: {e}"
        logger.error(msg)
        raise Exception(msg)

    release_info = response.json()
    assets = release_info.get("assets", [])
    total_assets = len(assets)
    logger.info(f"Found {total_assets} assets in release")

    # Filter assets to only process model files
    model_assets = []
    for asset in assets:
        filename = asset["name"]
        # Skip executables, checksums, and non-model files
        if (filename.endswith(".exe") or
            filename == "checksum.txt" or
            filename.startswith("espeak-") or
            "-mms-" in filename):
            continue
        model_assets.append(asset)

    logger.info(f"Processing {len(model_assets)} model files...")

    processed_count = 0
    skipped_count = 0
    error_count = 0

    for idx, asset in enumerate(model_assets, 1):
        filename = asset["name"]
        asset_url = asset["browser_download_url"]

        filename_no_ext = re.sub(r"\.tar\.bz2|\.tar\.gz|\.zip", "", filename)
        parts = filename_no_ext.split("-")

        # Determine model type - support more than just vits
        model_type = parts[0] if parts[0] in ["vits", "matcha", "kokoro"] else "unknown"
        if model_type == "unknown":
            logger.debug(f"Skipping unknown model type: {filename}")
            continue

        # For Kokoro models, the developer is "kokoro", not the second part
        if model_type == "kokoro":
            developer = "kokoro"
        else:
            developer = parts[1] if len(parts) > 1 else "unknown"
        logger.info(f"[{idx}/{len(model_assets)}] Processing {filename} ({developer})")

        # Check if the model has already been processed and saved
        if filename_no_ext in merged_models:
            logger.debug("  → Skipping (already processed)")
            skipped_count += 1
            continue

        try:
            # Extract language code, prioritizing config.json, fallback to URL
            lang_codes_and_regions = extract_language_code_vits(
                asset_url,
                parts[0],
                developer,
                None,  # Skip config data for faster processing
            )

            # Log language information
            for lang_code, region in lang_codes_and_regions:
                lang_info = get_language_data(lang_code, region)
                logger.debug(
                    f"  → Language: {lang_info['language_name']} "
                    f"({lang_info['lang_code']}, {lang_info['country']})"
                )

            # Handle name and quality parsing based on model type
            if model_type == "kokoro":
                # For Kokoro: kokoro-en-v0_19 -> name="en", quality="v0_19"
                name = parts[1] if len(parts) > 1 else "unknown"
                quality = parts[2] if len(parts) > 2 else "unknown"
            else:
                # For other models: vits-piper-en_GB-alan-low -> name="alan", quality="low"
                name = parts[3] if len(parts) > 3 else "unknown"
                quality = parts[4] if len(parts) > 4 else "unknown"

            # Handle special edge cases for developer-specific naming/quality issues
            name, quality = handle_special_cases(developer, name, quality, asset_url)

            # Get detailed language information
            lang_details = [
                get_language_data(code, region) for code, region in lang_codes_and_regions
            ]

            id = generate_model_id(
                developer,
                [code for code, _ in lang_codes_and_regions],
                name,
                quality,
            )

            # Determine sample rate based on model type and developer
            if developer == "piper":
                sample_rate = 22050
            elif model_type == "kokoro":
                sample_rate = 24000
            else:
                sample_rate = 16000

            model_data = {
                "id": id,
                "model_type": model_type,
                "developer": developer,
                "name": name,
                "language": lang_details,
                "quality": quality,
                "sample_rate": sample_rate,
                "num_speakers": 1,
                "url": asset_url,
                "compression": True,
                "filesize_mb": round(asset["size"] / (1024 * 1024), 2),
            }

            # Add to merged models
            merged_models[id] = model_data
            logger.info(f"  → Added model: {id}")
            processed_count += 1

        except Exception as e:
            logger.error(f"  → Error processing {filename}: {e}")
            error_count += 1
            continue

    logger.info("GitHub asset processing complete:")
    logger.info(f"  - Processed: {processed_count}")
    logger.info(f"  - Skipped: {skipped_count}")
    logger.info(f"  - Errors: {error_count}")

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
def main(
    force_refresh: bool = False,
    validate_urls: bool = True,
    test_models: bool = False,
    test_sample_size: int = 5
) -> None:
    """Main function to build and validate the merged_models.json file.

    Args:
        force_refresh: If True, rebuild the entire models file from scratch
        validate_urls: If True, validate that model URLs are accessible
        test_models: If True, test a sample of models to ensure they generate audio
        test_sample_size: Number of models to test from each developer type
    """
    # Save to the same directory as this script
    script_dir = Path(__file__).parent
    output_file = script_dir / "merged_models.json"
    logger.info("Starting model index creation/update process")

    # Step 1: Load existing models or start fresh
    output_path = Path(output_file)
    if force_refresh or not output_path.exists():
        logger.info("Starting fresh model index")
        merged_models = {}
    else:
        try:
            with output_path.open() as f:
                merged_models = json.load(f)
            logger.info(f"Loaded {len(merged_models)} existing models")
        except FileNotFoundError:
            logger.info("No existing models file found, starting fresh")
            merged_models = {}

    # Step 2: Fetch GitHub models (VITS, Piper, etc.)
    repo = "k2-fsa/sherpa-onnx"
    tag = "tts-models"
    logger.info("Fetching models from GitHub releases")

    if not force_refresh and merged_models:
        logger.info("Using existing GitHub models, add --force to refresh")
    else:
        merged_models = get_github_release_assets(repo, tag, merged_models, output_file)

    # Step 3: Add MMS languages
    logger.info("Fetching supported MMS languages")
    languages_json = get_supported_languages()
    models_languages = combine_json_parts(merged_models, languages_json)

    # Step 4: Validate URLs if requested
    if validate_urls:
        logger.info("Validating model URLs...")
        validate_model_urls(models_languages)

    # Step 5: Test models if requested
    if test_models:
        logger.info(f"Testing sample of models (max {test_sample_size} per type)...")
        test_model_samples(models_languages, test_sample_size)

    # Step 6: Save final results
    save_models(models_languages, output_file)
    logger.info(f"Model index saved to {output_file} with {len(models_languages)} models")


def validate_model_urls(models: dict[str, Any]) -> None:
    """Validate URLs for all models and mark invalid ones.

    Args:
        models: Dictionary of model configurations
    """
    logger.info("Starting URL validation...")
    invalid_models = []

    for model_id, model_data in models.items():
        if 'url' not in model_data:
            continue

        url = model_data['url']
        logger.info(f"Validating {model_id}: {url}")

        # For MMS models, validate the individual file URLs instead of directory
        if model_id.startswith('mms_'):
            # Check if model.onnx exists in the directory
            model_url = f"{url}/model.onnx"
            tokens_url = f"{url}/tokens.txt"

            model_valid = validate_url(model_url)
            tokens_valid = validate_url(tokens_url)

            if model_valid and tokens_valid:
                logger.info(f"✓ {model_id} MMS model files are valid")
            else:
                logger.warning(f"✗ {model_id} MMS model files are invalid: model.onnx={model_valid}, tokens.txt={tokens_valid}")
                invalid_models.append(model_id)
                model_data['url_valid'] = False
        # For other models, validate the URL directly
        elif validate_url(url):
            logger.info(f"✓ {model_id} URL is valid")
        else:
            logger.warning(f"✗ {model_id} URL is invalid: {url}")
            invalid_models.append(model_id)
            # Mark as invalid but don't remove
            model_data['url_valid'] = False

    if invalid_models:
        logger.warning(f"Found {len(invalid_models)} models with invalid URLs:")
        for model_id in invalid_models:
            logger.warning(f"  - {model_id}")
    else:
        logger.info("All model URLs are valid!")


def test_model_samples(models: dict[str, Any], sample_size: int = 5) -> None:
    """Test a sample of models from each developer type.

    Args:
        models: Dictionary of model configurations
        sample_size: Maximum number of models to test per developer
    """
    logger.info("Starting model testing...")

    # Group models by developer
    developers = {}
    for model_id, model_data in models.items():
        if 'developer' not in model_data:
            continue
        developer = model_data['developer']
        if developer not in developers:
            developers[developer] = []
        developers[developer].append((model_id, model_data))

    # Test samples from each developer
    total_tested = 0
    total_passed = 0

    for developer, model_list in developers.items():
        logger.info(f"Testing {developer} models (max {sample_size})...")

        # Take a sample
        sample = model_list[:sample_size]

        for model_id, model_data in sample:
            total_tested += 1
            if test_model_generation(model_data):
                total_passed += 1
                model_data['test_passed'] = True
            else:
                model_data['test_passed'] = False

    logger.info(f"Model testing complete: {total_passed}/{total_tested} models passed")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create and validate SherpaOnnx model index")
    parser.add_argument("--force", action="store_true", help="Force refresh of all models")
    parser.add_argument("--no-validate", action="store_true", help="Skip URL validation")
    parser.add_argument("--test", action="store_true", help="Test model generation")
    parser.add_argument("--test-size", type=int, default=5, help="Number of models to test per type")

    args = parser.parse_args()

    main(
        force_refresh=args.force,
        validate_urls=not args.no_validate,
        test_models=args.test,
        test_sample_size=args.test_size
    )
