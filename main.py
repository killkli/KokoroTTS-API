from fastapi import FastAPI, Response, HTTPException, Request
from pydantic import BaseModel
import uvicorn
import io
import soundfile as sf
from kokoro import KModel, KPipeline
from random import randint
import torch
from contextlib import asynccontextmanager

REPO_ID = 'hexgrad/Kokoro-82M-v1.1-zh'
SAMPLE_RATE = 24000
N_ZEROS = 5000
JOIN_SENTENCES = True
VOICE_LIST = ["zf_001","zf_002","zf_003","zf_004","zf_005","zf_006","zf_007","zf_008","zf_017","zf_018","zf_019","zf_021","zf_022","zf_023","zf_024","zf_026","zf_027","zf_028","zf_032","zf_036","zf_038","zf_039","zf_040","zf_042","zf_043","zf_044","zf_046","zf_047","zf_048","zf_049","zf_051","zf_059","zf_060","zf_067","zf_070","zf_071","zf_072","zf_073","zf_074","zf_075","zf_076","zf_077","zf_078","zf_079","zf_083","zf_084","zf_085","zf_086","zf_087","zf_088","zf_090","zf_092","zf_093","zf_094","zf_099"]
VOICE = VOICE_LIST[randint(0,len(VOICE_LIST)-1)]

model: KModel|None = None
pipeline: KPipeline|None = None

device = 'cuda' if torch.cuda.is_available() else 'cpu'
# device = 'mps'

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, pipeline
    try:
        en_pipeline = KPipeline(lang_code='a', repo_id=REPO_ID, model=False)
        def en_callable(text):
            if text == 'Kokoro':
                return 'kˈOkəɹO'
            elif text == 'Sol':
                return 'sˈOl'
            return next(en_pipeline(text)).phonemes

        model = KModel(repo_id=REPO_ID).to(device).eval()
        zh_pipeline = KPipeline(lang_code='z', repo_id=REPO_ID, model=model, en_callable=en_callable)
        pipeline = zh_pipeline
        print(f"Kokoro TTS model and pipeline loaded successfully on device: {device}")
        app.state.model = model  # Store model in app.state
        app.state.pipeline = pipeline  # Store pipeline in app.state
        app.state.voice_list = VOICE_LIST # Store voice list in app.state
        yield
        # Here you can add shutdown logic if needed, e.g., releasing resources
        print("Shutting down Kokoro TTS API")
        del app.state.model
        del app.state.pipeline
        del app.state.voice_list
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception as e:
        print(f"Error loading model or pipeline: {e}")
        # It's crucial to handle startup errors properly.  If the model fails to load,
        # the application should not start.  We can raise the exception to prevent the app from running.
        raise  # Re-raise the exception to prevent the app from starting

app = FastAPI(
    title="Kokoro TTS API",
    description="API service for the Kokoro Text-to-Speech model.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
async def read_root():
    return {"message": "Kokoro TTS API is running!"}

@app.get("/voices")
async def list_voices(request: Request):
    """
    Returns a list of available voice IDs.
    """
    try:
        voice_list = request.app.state.voice_list
        return {"voices": voice_list}
    except AttributeError:
        raise HTTPException(status_code=503, detail="Voice list not initialized.  Model may not have loaded yet.")


class SynthesisRequest(BaseModel):
    text: str
    speaker_id: str|None = None  # Optional speaker ID
    language: str = "en"    # Default language to English

@app.post("/tts/synthesize",
           response_class=Response,
           responses={
               200: {"content": {"audio/wav": {}}},
               400: {"description": "Invalid input"},
               500: {"description": "Internal server error"}
           })
async def synthesize_speech(synthesis_request: SynthesisRequest, request: Request):
    model = request.app.state.model
    pipeline = request.app.state.pipeline
    if not model or not pipeline:
        raise HTTPException(status_code=503, detail="TTS model not loaded yet.")

    try:
        def speed_callable(len_ps):
            speed = 0.8
            if len_ps <= 83:
                speed = 1
            elif len_ps < 183:
                speed = 1 - (len_ps - 83) / 500
            return speed * 1.1

        SPEAKER_ID = VOICE
        if synthesis_request.speaker_id:
            SPEAKER_ID = synthesis_request.speaker_id
        generator = pipeline(synthesis_request.text, voice=SPEAKER_ID, speed=speed_callable)
        result = next(generator)
        wav = result.audio

        buffer = io.BytesIO()
        try:
            wav = wav.cpu().numpy()  # Move to CPU and convert to NumPy
            sf.write(buffer, wav, SAMPLE_RATE, format='WAV')  # Specify format
        except Exception as e:
            print(f"Error writing WAV file: {e}")
            raise HTTPException(status_code=500, detail=f"Error writing WAV file: {e}")

        buffer.seek(0)
        return Response(content=buffer.getvalue(), media_type="audio/wav")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input for synthesis: {e}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed (RuntimeError): {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed (General): {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
