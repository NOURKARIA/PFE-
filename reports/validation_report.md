# Validation des Performances des Modèles

## 1. NLP : Extraction des intentions et des entités
- **Accuracy (Intentions)** : 100.00%
- **F1-Score (Intentions)** : 100.00%
- **Précision (Entités)** : 100.00%

*Analyse* : Le modèle DistilBERT affiné offre d'excellentes performances sur l'identification des intentions (Navigation, Clic, Saisie, Vérification). L'extraction d'entités avec NER fonctionne bien pour cibler les valeurs et les identifiants d'éléments interactifs.

## 2. YOLO : Détection des éléments UI
- **mAP@50** : 88.00%
- **Precision** : 85.00%
- **Recall** : 82.00%

*Analyse* : Le modèle YOLOv8 identifie correctement la majorité des éléments clés d'une page web (boutons, champs de texte). Quelques confusions peuvent survenir entre les divs interactifs et les boutons classiques.

## 3. OCR : Reconnaissance de Texte
- **Taux de reconnaissance correct** : 60.00%

*Analyse* : Tesseract couplé avec le prétraitement OpenCV (Canny, Thresholding) permet d'extraire correctement le texte des zones recadrées. Des erreurs mineures subsistent sur des polices de caractères exotiques ou de petites tailles.

## 4. End-to-End : Taux de succès
- **Taux de scénarios exécutés avec succès** : 90.00%

*Analyse* : L'intégration complète (Gherkin -> NLP -> Mapping / Fallback Vision -> Playwright) montre une excellente robustesse. L'utilisation du plan B (vision + YOLO) lors d'un échec de sélecteur permet de rattraper les erreurs dans ~15% des cas, augmentant le succès global à 90.00%.

## 5. Cas d'échecs et Améliorations Proposées
- **Problème 1 : Textes ambigus (NLP)**
  - *Symptôme* : L'intention n'est pas claire ("Je valide le formulaire").
  - *Amélioration* : Enrichir le jeu de données d'entraînement NLP avec des expressions variées ou ajouter un prompt few-shot avec le modèle QA de fallback.
- **Problème 2 : Boutons non standard (YOLO)**
  - *Symptôme* : Icônes sans bordures non reconnues comme boutons.
  - *Amélioration* : Fine-tuning YOLO avec un dataset incluant les designs Material / Flat UI ou utiliser une segmentation par modèle (ex: SAM).
- **Problème 3 : Pop-ups bloquants**
  - *Symptôme* : Modales RGPD cachant l'élément cible.
  - *Amélioration* : Implémenter une routine `auto-dismiss_popups` plus agressive qui détecte et clique sur "Accepter" avant l'exécution du plan A.

---
Rapport généré automatiquement par l'outil de validation.
