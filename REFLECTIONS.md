# Réflexions — TD 4

## Étape 0 — Disponibilité des données

J'aurais consulté la documentation du paramètre `past_days` d'Open-Meteo puis envoyé une requête d'essai pour 90 jours de `carbon_dioxide`. J'aurais vérifié les dates et le nombre de valeurs retournées avant de décider qu'il fallait générer une série synthétique.

## Étape 1 — Prédiction avant la collecte

Avant d'exécuter la collecte, je prévois une hausse du CO₂ au Mans sur les 90 derniers jours (environ mi-août à début novembre). La végétation de l'hémisphère Nord absorbe moins de CO₂ quand la saison de croissance se termine, ce qui devrait faire remonter la concentration, même si la météo et le modèle peuvent brouiller cette tendance.

## Étape 2 — Nettoyage

Un résultat sans lacune sur une exécution ne garantit pas que les suivantes seront complètes. Le modèle de réanalyse remplit généralement les heures, mais une panne d'API, un changement de format ou un autre producteur de données peut créer des trous ; conserver le contrôle explicite des dates permet de les voir au lieu de les masquer.

## Étape 3 — Deux lissages

Sur les cinq derniers jours, la moyenne mobile passe de 450,30 à 456,60 ppm, tandis que le lissage exponentiel passe de 451,78 à 455,84 ppm avec un pic à 459,28 ppm. Je choisirais la moyenne mobile pour un bilan hebdomadaire facile à expliquer, où chaque jour récent compte autant. Pour détecter rapidement une hausse comme celle observée dans les dernières valeurs brutes (jusqu'à 470,6 ppm), je choisirais le lissage exponentiel : il réagit davantage à la mesure récente, puis redescend plus vite.

## Étape 4 — Échec de la collecte automatique

Si les quatre essais de l'API échouent, le script s'arrête avant d'écrire le CSV. Les étapes suivantes du workflow ne s'exécutent pas : le JSON et le CSV déjà publiés gardent les valeurs de la semaine précédente, et le tableau de bord reste visible avec une date d'analyse ancienne. Il faut surveiller l'échec de l'Action et la fraîcheur affichée pour détecter cette situation.

## Étape 5 — Limite de projection

La pente mesurée est de +0,1655 ppm par jour et les sept points projetés vont de 450,19 à 451,18 ppm. Je ne leur accorderais une confiance pratique que sur trois jours : les dernières mesures réelles varient de 451,3 à 470,6 ppm, bien plus que la hausse projetée sur une semaine. Sept jours restent utiles pour visualiser la direction, mais pas comme valeurs précises, surtout près d'un changement de saison.

## Étape 6 — Autre lieu

Sur la même fenêtre de 90 jours, la pente est de +0,1655 ppm/jour au Mans et de +0,3384 ppm/jour à Madrid, soit une hausse environ deux fois plus rapide à Madrid ; aucun jour ne manque dans les deux séries. Le script de comparaison réutilise les mêmes fonctions d'analyse, qui manipulent seulement des jours, des dates et des valeurs numériques : elles ne contiennent ni nom de ville, ni coordonnées, ni champ `carbon_dioxide`. Le choix du lieu reste dans la couche de collecte.
