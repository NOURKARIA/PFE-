"""
TASK 5: Manipulation de fichiers JSON
Objectif: Apprendre à sauvegarder et charger des données
"""

import json
from datetime import datetime

# =============================================
# EXERCICE 1: Créer et sauvegarder un scénario
# =============================================

print("="*60)
print("EXERCICE 1: Sauvegarder un scénario de test")
print("="*60)

# 1. Crée un dictionnaire avec les informations d'un test
mon_scenario = {
    "nom": "Test Connexion",
    "date": str(datetime.now()),
    "auteur": "Nour",
    "etapes": [
        {"type": "Given", "description": "je suis sur la page login"},
        {"type": "When", "description": "je saisis mon email"},
        {"type": "When", "description": "je saisis mon mot de passe"},
        {"type": "When", "description": "je clique sur login"},
        {"type": "Then", "description": "je vois le tableau de bord"}
    ],
    "tags": ["smoke", "critique"],
    "priorite": "haute"
}

print("✅ Dictionnaire créé avec", len(mon_scenario["etapes"]), "étapes")

# 2. Sauvegarde dans un fichier JSON
with open("mon_scenario.json", "w", encoding="utf-8") as fichier:
    json.dump(mon_scenario, fichier, indent=2, ensure_ascii=False)

print("✅ Fichier 'mon_scenario.json' créé!")

# 3. Lit le fichier pour vérifier
with open("mon_scenario.json", "r", encoding="utf-8") as fichier:
    data_chargee = json.load(fichier)

print("\n📖 Données chargées avec succès!")
print(f"   Nom du test: {data_chargee['nom']}")
print(f"   Nombre d'étapes: {len(data_chargee['etapes'])}")
print(f"   Tags: {data_chargee['tags']}")