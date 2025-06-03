## Kokoro TTS API Documentation

This document outlines the API endpoints for the Kokoro Text-to-Speech service.

### 1. Root Endpoint

**GET `/`**

*   **Description:** Checks if the API is running.
*   **Responses:**
    *   `200 OK`:
        ```json
        {
          "message": "Kokoro TTS API is running!"
        }
        ```

### 2. List Available Voices

**GET `/voices`**

*   **Description:** Returns a list of available speaker IDs (voices) that can be used for speech synthesis.
*   **Responses:**
    *   `200 OK`:
        ```json
        {
          "voices": ["zf_001", "zf_002", ...]
        }
        ```
    *   `503 Service Unavailable`:
        ```json
        {
          "detail": "Voice list not initialized. Model may not have loaded yet."
        }
        ```

### 3. Synthesize Speech

**POST `/tts/synthesize`**

*   **Description:** Generates speech audio from the provided text.
*   **Request Body:** `application/json`
    *   **Schema:** `SynthesisRequest`
        ```json
        {
          "text": "string",
          "speaker_id": "string | null",
          "language": "string"
        }
        ```
    *   **Fields:**
        *   `text` (string, required): The text to be synthesized.
        *   `speaker_id` (string, optional): The ID of the speaker voice to use. If not provided, a random voice from the pre-defined list will be used.
        *   `language` (string, default: "en"): The language of the input text. (Currently, only "zh" for Chinese and "en" for English are fully supported by the underlying model, though the API defaults to "en").
*   **Responses:**
    *   `200 OK`: Returns the synthesized audio as a WAV file.
        *   **Content-Type:** `audio/wav`
    *   `400 Bad Request`: Invalid input provided in the request body or text.
        ```json
        {
          "detail": "Invalid input for synthesis: [error message]"
        }
        ```
    *   `500 Internal Server Error`: An error occurred during the speech synthesis process.
        ```json
        {
          "detail": "Speech synthesis failed (RuntimeError): [error message]"
        }
        ```
        or
        ```json
        {
          "detail": "Error writing WAV file: [error message]"
        }
        ```
    *   `503 Service Unavailable`: The TTS model and/or pipeline are not yet loaded or initialized.
        ```json
        {
          "detail": "TTS model not loaded yet."
        }
        ```
