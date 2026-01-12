# 🚄 Travel Order Resolver (2026)

<p align="center">
  <img src="./public/thumbnail.png" alt="thumbnail" /><br>
  <img src="https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/SpaCy-09A3D5?logo=spacy&logoColor=white" alt="SpaCy"/>
  <img src="https://img.shields.io/badge/uv-package%20manager-blueviolet" alt="uv"/>
</p>

🚄 NLP-powered system designed to process natural language travel requests (in French), extract departure/destination points and times, then generate optimal train itineraries via the Navitia API.

## 🚀 Demo

[🎬 Watch the Travel Order Resolver application in action](https://cdn.lenysauzet.com/Demos/travel-order-resolver.mp4)

## ✨ Features

- 🎙️ **Voice Transcription**: Converts audio commands to text via Faster-Whisper
- 🧠 **Custom NER**: SpaCy model trained to extract DEPARTURE, DESTINATION and TIME entities
- 🔍 **Fuzzy Matching**: Smart station name matching with TheFuzz
- 📍 **Geolocation**: Automatic detection of the nearest station to the user
- ⏰ **Time Normalization**: Interpretation of French expressions ("demain matin", "15h30", "ce soir")
- 🗺️ **Interactive Maps**: Journey visualization with Folium and Google Maps Directions
- 🚆 **Journey Search**: Integration with Navitia SNCF API

## 📁 Project Structure

```
travel-order-resolver/
├── backend/                 # FastAPI API
│   ├── app/
│   │   ├── api/v1/          # API routes
│   │   │   ├── transcription.py   # Audio transcription
│   │   │   ├── travel.py          # Identification & search
│   │   │   └── user.py            # User management
│   │   ├── core/            # Configuration & logging
│   │   ├── db/              # SQLAlchemy schemas
│   │   ├── models/          # Pydantic models
│   │   └── services/        # Business logic
│   │       ├── transcription_service.py  # Whisper ASR
│   │       ├── travel_service.py         # NER + matching
│   │       ├── station_matcher.py        # Station fuzzy matching
│   │       ├── time_normalizer.py        # Time normalization
│   │       ├── geolocation.py            # Proximity search
│   │       └── navitia_service.py        # Navitia API
│   └── tests/               # Unit tests
├── frontend/                # Streamlit interface
│   ├── app.py               # Entry point (chat)
│   ├── api.py               # Backend API client
│   ├── components/          # Reusable UI components
│   ├── models/              # Frontend Pydantic models
│   └── pages/
│       └── itinerary.py     # Journey detail page + map
├── base/                    # ML/NLP pipeline
│   ├── data/
│   │   ├── raw/             # Raw data (stations, municipalities, audio)
│   │   └── processed/       # Processed data (entries.csv, dataset)
│   ├── models/
│   │   └── travel-order-ner-model/  # Trained SpaCy NER model
│   ├── notebooks/           # Jupyter notebooks
│   │   ├── 01_data_exploration.ipynb
│   │   ├── 02_model_training.ipynb
│   │   ├── 03_evaluation.ipynb
│   │   └── data_processing/  # Data preparation notebooks
│   └── src/                 # ML source code
│       ├── preprocessing.py
│       ├── training.py
│       └── ner/             # NER scripts
└── public/                  # Public resources
    └── docs/                # Project documentation
```

---

## 🚀 Local Development

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (package manager)

### Installation

```bash
# Clone the project
git clone https://github.com/LenySauzet/travel-order-resolver.git
cd travel-order-resolver

# Install dependencies
uv sync --locked
```

### Environment Variables

Create a `.env` file at the project root:

```env
# Navitia API (required for journey search)
NAVITIA_API_KEY=
NAVITIA_COVERAGE=

# Google Maps (optional, for route drawing)
GOOGLE_MAPS_API_KEY=
```

| Variable              | Description                                             | Required |
| --------------------- | ------------------------------------------------------- | -------- |
| `NAVITIA_API_KEY`     | Navitia SNCF API key ([get a key](https://navitia.io/)) | ✅       |
| `NAVITIA_COVERAGE`    | Navitia SNCF coverage (sncf)                            | ✅       |
| `GOOGLE_MAPS_API_KEY` | Google Maps API key (Directions API)                    | ❌       |

### Download French SpaCy Model

```bash
uv run python -m spacy download fr_core_news_md
```

### Run Services

| Command              | Description                          |
| -------------------- | ------------------------------------ |
| `uv run poe api`     | Start FastAPI backend (port 8000)    |
| `uv run poe front`   | Start Streamlit frontend (port 8501) |
| `uv run poe jupyter` | Start Jupyter Lab                    |
| `uv run poe dev`     | Start all services in parallel       |
| `uv run poe test`    | Run pytest tests                     |

### Service Access

- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

## 🐳 Docker

### With Docker Compose (recommended)

```bash
# Build and start
docker compose up --build

# Run in background
docker compose up -d --build

# Stop services
docker compose down

# View logs
docker compose logs -f
```

### Available Services

| Service            | URL                        | Port |
| ------------------ | -------------------------- | ---- |
| Frontend Streamlit | http://localhost:8501      | 8501 |
| Backend API        | http://localhost:8000      | 8000 |
| API Documentation  | http://localhost:8000/docs | 8000 |

### Access Container

```bash
docker exec -it travel-resolver-api bash
```

---

## 📡 API Endpoints

### Transcription

```http
POST /api/v1/transcribe
Content-Type: multipart/form-data

file: <audio_file>
```

### Travel Request Identification

```http
GET /api/v1/identify-travel-order?text=je+veux+aller+a+Lyon+demain+matin&lat=48.85&lon=2.35
```

### Station List

```http
GET /api/v1/stations
```

### Journey Search

```http
GET /api/v1/journeys?departure_id=123&destination_id=456&datetime_iso=2024-01-15T14:30:00
```

---

## 🧠 NLP Pipeline

### Named Entity Recognition (NER)

The custom SpaCy model extracts 3 entity types:

| Entity        | Description       | Example                       |
| ------------- | ----------------- | ----------------------------- |
| `DEPARTURE`   | Departure station | "Paris", "Gare de Lyon"       |
| `DESTINATION` | Arrival station   | "Marseille", "Lyon Part-Dieu" |
| `TIME`        | Time expression   | "demain", "15h30", "ce soir"  |

### Station Fuzzy Matching

The `StationMatcher` service uses TheFuzz to find the matching station even with typos or name variations (minimum score: 60%).

### Time Normalization

The `TimeNormalizer` interprets:

- French time formats: "15h", "8h30", "à 17h"
- Vague expressions: "matin" (8am), "midi" (12pm), "soir" (6pm)
- Relative expressions via dateparser: "demain", "après-demain", "lundi prochain"

---

## 📓 Notebooks

| Notebook                    | Description                               |
| --------------------------- | ----------------------------------------- |
| `01_data_exploration.ipynb` | Station and municipality data exploration |
| `02_model_training.ipynb`   | SpaCy NER model training                  |
| `03_evaluation.ipynb`       | Model performance evaluation              |
| `data_processing/`          | Data preparation notebooks                |

---

## 🧪 Tests

```bash
# Run all tests
uv run poe test

# With coverage
uv run pytest -v --cov=backend
```

---

## 📦 Technologies

| Category     | Technologies                               |
| ------------ | ------------------------------------------ |
| **Backend**  | FastAPI, Uvicorn, SQLAlchemy, Pydantic     |
| **Frontend** | Streamlit, Folium, Streamlit-Folium        |
| **NLP/ML**   | SpaCy, Faster-Whisper, TheFuzz, dateparser |
| **APIs**     | Navitia SNCF, Google Maps Directions       |
| **Tools**    | uv, Docker, Jupyter, pytest                |

---

## 📄 License

This project is developed for educational purposes.
