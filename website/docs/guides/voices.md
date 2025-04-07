---
sidebar_position: 4
---

# Voices

TTS Wrapper allows getting and setting voices in a unified way. We provide a mixture of language codes and details as rich as possible for all TTS engines. 

## Get Voices 

All engines support ``get_voices()`` method to get the list of available voices. 

```python
voices = client.get_voices()
```

By default the result is a JSON of dictionaries with the following fields:

```json
[
  {
    "id": "af",
    "language_codes": [
      "af"
    ],
    "name": "Afrikaans",
    "gender": "Unknown"
  },
  {
    "id": "am",
    "language_codes": [
      "am"
    ],
    "name": "Amharic",
    "gender": "Unknown"
  }
  ```

  This is BCP-47 format. You can also get it in ISO 639-3 format.    
  
  ```python
  voices_iso = client.get_voices(langcodes="iso639_3")
  print(json.dumps(voices_iso[:3], indent=2))
  ```

  ```json
  [
    {
      "id": "afr",
      "language_codes": [
        "afr"
      ],
      "name": "Afrikaans",
      "gender": "Unknown"
    },
    {
      "id": "amh",
      "language_codes": [
        "amh"
      ],
      "name": "Amharic",
      "gender": "Unknown"
    }
  ```

  Or Human readable format

  eg 

``python
    voices_display = client.get_voices(langcodes="display")
    print("\n3. Human-readable display names:")
    print(json.dumps(voices_display[:3], indent=2))
```

```json
3. Human-readable display names:
[
  {
    "id": "af",
    "language_codes": [
      "Afrikaans"
    ],
    "name": "Afrikaans",
    "gender": "Unknown"
  },
  {
    "id": "am",
    "language_codes": [
      "Amharic"
    ],
    "name": "Amharic",
    "gender": "Unknown"
  },
  {
    "id": "ar",
    "language_codes": [
      "Arabic"
    ],
    "name": "Arabic",
    "gender": "Unknown"
  }
]
```

Or lastly - All formats in a dictionary

```python
    voices_all = client.get_voices(langcodes="all")
    print("\n4. All formats in a dictionary:")
    print(json.dumps(voices_all[:3], indent=2))
```

```json
[
  {
    "id": "af",
    "language_codes": {
      "af": {
        "bcp47": "af",
        "iso639_3": "afr",
        "display": "Afrikaans"
      }
    },
    "name": "Afrikaans",
    "gender": "Unknown"
  },
  {
    "id": "am",
    "language_codes": {
      "am": {
        "bcp47": "am",
        "iso639_3": "amh",
        "display": "Amharic"
      }
    },
    "name": "Amharic",
    "gender": "Unknown"
  },
  {
    "id": "ar",
    "language_codes": {
      "ar": {
        "bcp47": "ar",
        "iso639_3": "ara",
        "display": "Arabic"
      }
    },
    "name": "Arabic",
    "gender": "Unknown"
  }
]
```