# Skept Provider Eval

Eval harness for comparing deepfake detection API providers. Runs a social media clip URL through Resemble AI, Aurigin, Sightengine, and Reality Defender in parallel, logs results to SQLite, and surfaces them in a review UI.

Used to select the best provider(s) for audio deepfake, video deepfake, and synthetic generation detection before integrating into [Skept-prototype](https://github.com/DustyDingo/Skept-prototype).

## Providers evaluated
| Provider | Modality |
|---|---|
| Resemble AI (DETECT-3B Omni) | Audio + Video |
| Aurigin AI | Audio |
| Sightengine | Synthetic generation (video) |
| Reality Defender | Audio + Video |

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in API keys
uvicorn main:app --reload --port 8000
```

Open `http://localhost:8000`, paste a clip URL, click Analyse.

## Environment variables
```
RESEMBLE_API_KEY=
AURIGIN_API_KEY=
SIGHTENGINE_API_USER=
SIGHTENGINE_API_SECRET=
REALITY_DEFENDER_API_KEY=
```

## Routes
| Method | Path | Description |
|---|---|---|
| POST | /analyse | Download clip, run all providers, return results |
| GET | /jobs | All jobs with results |
| GET | /jobs/{id} | Single job |
| POST | /jobs/{id}/ground_truth | Label a job fake/authentic/unknown |
| GET | /export | Download all results as CSV |
