# Intelligent Agent For Functional Test Automation (Self-Healing)

Backend FastAPI pour automatiser des tests fonctionnels a partir de scenarios Gherkin. Le pipeline combine NLP pour transformer le langage naturel en actions executables, puis vision par ordinateur avec YOLO, OpenCV et OCR pour assurer un fallback self-healing quand les selecteurs Playwright echouent.

## Project Overview

Le systeme suit 4 phases principales :

1. NLP et classification d'intention
   Transformer les etapes Gherkin en actions machine avec extraction de `TARGET` et `VALUE`, puis classification en `CLICK`, `TYPE`, `NAVIGATE`, `VERIFICATION`.
2. Vision et detection UI
   Detecter les elements UI par YOLO, lire leur texte avec OCR, et faire le lien semantique entre la cible NLP et les boites detectees.
3. Moteur d'execution
   `Plan A`: utiliser Playwright et des selecteurs derives du NLP.
   `Plan B`: si Plan A echoue, basculer vers `YOLO + OpenCV + OCR` pour cliquer ou saisir par coordonnees.
4. Reporting
   Produire des rapports JSON/HTML, des captures et un resume de l'execution avec le nombre d'etapes passees par Plan A et Plan B.

## API Endpoints

- `GET /health`
- `POST /api/ia/parse-gherkin`
- `POST /api/ia/semantic-mapping`
- `POST /api/ia/detect-ui`
- `POST /api/ia/segment`
- `POST /api/ia/generate-test`
- `POST /api/ia/execute-test`
- `GET /api/ia/reports`
- `GET /api/ia/reports/{execution_id}`
- `GET /api/ia/reports/{execution_id}/summary`

## Phases And Deliverables

### Phase 1: NLP & Intent Classification

- `nlp/entity_extractor.py`: extracteur d'entites `TARGET` et `VALUE`
- `nlp/intent_classifier.py`: classifieur d'intention
- `trained_models/nlp/entity_extractor.pt`
- `trained_models/nlp/intention_classifier.pt`
- endpoint: `POST /api/ia/parse-gherkin`

### Phase 2: Computer Vision & UI Detection

- `app/services/vision_service.py`: YOLO + OCR + ranking semantique
- `app/utils/image_processing.py`: OpenCV preprocessing + OCR
- `trained_models/vision/yolov8_ui_elements.pt`
- endpoints: `POST /api/ia/detect-ui`, `POST /api/ia/segment`

### Phase 3: Execution Engine

- `app/services/executor_service.py`: orchestration self-healing
- `app/services/generator_service.py`: execution Playwright et generation de script
- `app/services/mapping_service.py`: mapping NLP -> action + selecteurs candidats
- endpoint: `POST /api/ia/execute-test`

### Phase 4: Reporting & Dashboard

- `app/services/report_service.py`
- `app/api/reporting.py`
- `app/templates/report.html.j2`
- sorties: rapports JSON/HTML et screenshots

## Self-Healing Strategy

- `Plan A`: Playwright avec selecteurs `text`, `button`, `input`, `xpath`, etc.
- `Plan B`: capture d'ecran, detection YOLO, preprocessing OpenCV, OCR, matching semantique, puis action par coordonnees
- les rapports exposent `plan_a_steps` et `plan_b_steps`

## Running Locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Docker

```bash
docker compose up --build
```

## Tests

```bash
venv\Scripts\python -m pytest tests -q
```

## Project Structure

- `app/`: API, services, schemas, templates, utilitaires
- `nlp/`: composants NLP et chargement des modeles
- `trained_models/`: poids NLP et vision
- `notebooks/`: exploration et experimentation
- `tests/`: tests unitaires et integration legere
- `reports/`: rapports et screenshots generes a l'execution

## Current Status

Le backend, les endpoints, la logique self-healing, le reporting et la documentation technique sont en place. La qualite finale des modeles depends encore de la validite reelle des checkpoints `.pt`, de vos jeux de donnees et des entrainements effectifs realises pour le PFE.
