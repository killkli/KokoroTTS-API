# Kokoro TTS API（中文語音合成 API）

本專案將 KokoroTTS（zh 版本）包裝成 HTTP API，方便以 RESTful 方式呼叫中文語音合成。

## 安裝與啟動

1. 安裝 [uv](https://github.com/astral-sh/uv)：
```bash
pip install uv
```
2. 安裝相依套件：
```bash
uv pip install .
```
3. 啟動 API 伺服器：
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Docker 部署

你也可以使用 Docker 快速部署本服務：

1. 建立映像檔：
```bash
docker build -t kokoro-tts-api .
```
2. 啟動容器（僅供內部網路）：
```bash
docker run -d --name kokoro-tts-api -p 8000:8000 kokoro-tts-api
```

## 重要提醒

⚠️ **本系統僅供內部網路部署，API 無任何認證或存取控制機制，嚴禁對外公開或曝露於公網！**

## API 端點

* **GET `/`**：API 狀態檢查
* **GET `/voices`**：取得可用 speaker ID
* **POST `/tts/synthesize`**：語音合成，請求格式：
```json
{
  "text": "你好，這是一個測試。",
  "speaker_id": "zh_001", // 選填
  "language": "zh"         // 選填，預設 zh
}
```
回應：`audio/wav` 檔案

## 授權（License）

本專案與 KokoroTTS（模型權重與原始碼）皆採用 [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)。

- 你可以自由地用於商業與非商業用途。
- 請保留原始授權條款與版權聲明。
- 詳細授權內容請參閱 [Apache License 2.0 正體中文版](https://www.apache.org/licenses/LICENSE-2.0) 或原文。

KokoroTTS 專案（上游模型）：https://github.com/hexgrad/kokoro

本專案完全遵循上游授權規範，確保相容性與合法性。
