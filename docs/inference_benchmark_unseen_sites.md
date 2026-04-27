# Inference Benchmark On 3 Unseen Websites

Ce benchmark sert a evaluer l'agent sur 3 sites jamais vus pendant l'entrainement.

## Sites retenus

1. Wikipedia
   URL: `https://www.wikipedia.org/`
   Etape: `When I type 'test automation' into the 'Search Wikipedia' field`
2. Python
   URL: `https://www.python.org/`
   Etape: `When I click the 'Downloads' button`
3. GitHub Login
   URL: `https://github.com/login`
   Etape: `When I type 'demo@example.com' into the 'Username or email address' field`

## Objectif

- verifier la generalisation NLP sur des cibles jamais vues
- verifier le comportement de `Plan A` sur selecteurs textuels/attributaires
- verifier le fallback `Plan B` quand les selecteurs echouent
- recuperer des rapports JSON/HTML pour le PFE

## Execution

Le test est volontairement `opt-in` pour ne pas rendre la suite CI instable.

```bash
$env:RUN_LIVE_INFERENCE="1"
venv\Scripts\python -m pytest tests/test_inference_unseen_sites.py -q
```

## Criteres de succes

- code HTTP `200`
- `status = completed`
- `result.result.status = success`
- `plan_used` vaut `plan_a_selector_playwright` ou `plan_b_yolo_ocr`
- un rapport JSON et un rapport HTML sont generes

## Resultats a reporter

Pour chaque site, relever :

- intention predite
- entites extraites
- plan utilise
- temps d'execution
- capture d'ecran
- succes ou echec final

## Note

Les sites reels peuvent evoluer dans le temps. Ce benchmark mesure la robustesse d'inference de l'agent dans des conditions realistes, pas une verite absolue figee.
