from fastapi import FastAPI, Response, HTTPException, Request
from pydantic import BaseModel
import uvicorn
import io
import soundfile as sf
from random import randint
from contextlib import asynccontextmanager
from misaki import zh
from kokoro_onnx import Kokoro
import sys # 匯入 sys 模組，memory_profiler 可能會用到

# 從 memory_profiler 匯入 profile 裝飾器
from memory_profiler import profile 

VOICE_LIST = ["zf_001","zf_002","zf_003","zf_004","zf_005","zf_006","zf_007","zf_008","zf_017","zf_018","zf_019","zf_021","zf_022","zf_023","zf_024","zf_026","zf_027","zf_028","zf_032","zf_036","zf_038","zf_039","zf_040","zf_042","zf_043","zf_044","zf_046","zf_047","zf_048","zf_049","zf_051","zf_059","zf_060","zf_067","zf_070","zf_071","zf_072","zf_073","zf_074","zf_075","zf_076","zf_077","zf_078","zf_079","zf_083","zf_084","zf_085","zf_086","zf_087","zf_088","zf_090","zf_092","zf_093","zf_094","zf_099"]
VOICE = VOICE_LIST[randint(0,len(VOICE_LIST)-1)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        g2p = zh.ZHG2P(version="1.1")
        kokoro = Kokoro("kokoro-v1.1-zh.onnx", "voices-v1.1-zh.bin", vocab_config="config.json")
        app.state.g2p = g2p
        app.state.kokoro = kokoro  # Store model in app.state
        app.state.voice_list = VOICE_LIST # Store voice list in app.state
        yield
        # Here you can add shutdown logic if needed, e.g., releasing resources
        print("Shutting down Kokoro TTS API")
        del app.state.kokoro
        del app.state.voice_list
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
@profile # 將 @profile 裝飾器添加到 synthesize_speech 函式上
async def synthesize_speech(synthesis_request: SynthesisRequest, request: Request):
    kokoro = request.app.state.kokoro
    g2p = request.app.state.g2p
    if not kokoro or not g2p:
        raise HTTPException(status_code=503, detail="TTS model not loaded yet.")

    try:
        SPEAKER_ID = VOICE
        if synthesis_request.speaker_id:
            SPEAKER_ID = synthesis_request.speaker_id
        
        # 執行 G2P 和 TTS 轉換
        phonemes, _ = g2p(synthesis_request.text)
        wav, sample_rate = kokoro.create(phonemes, voice=SPEAKER_ID, speed=1.0, is_phonemes=True)

        buffer = io.BytesIO()
        try:
            sf.write(buffer, wav, sample_rate, format='WAV')  # Specify format
        except Exception as e:
            print(f"Error writing WAV file: {e}")
            raise HTTPException(status_code=500, detail=f"Error writing WAV file: {e}")
        
        # 在 wav 數據被寫入緩衝區後，明確刪除對它的引用以加速回收
        del wav 
        
        buffer.seek(0)
        content_to_return = buffer.getvalue()
        buffer.close() # 顯式關閉 BytesIO 緩衝區，釋放其資源
        del buffer # 顯式刪除對 buffer 物件的引用

        return Response(content=content_to_return, media_type="audio/wav")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input for synthesis: {e}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed (RuntimeError): {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed (General): {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

