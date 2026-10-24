# CompressLab Archive — Clone WinRAR / 7-Zip & Moteurs Manuels
> **Projet de Compression de Données — Codage et Traitement du Signal**  
> **Technologies** : Python 3.11, PySide6, Pytest, ReportLab  
> **Algorithmes programmés manuellement** : LZ77, Codage Arithmétique 32-bit, Pipeline Combiné, Huffman, RLE, LZ78, LZW

---

## 1. Vue d'ensemble du projet

**CompressLab Archive** est une application de bureau Windows native d'archivage, de compression et de décompression inspirée de **WinRAR** et **7-Zip**.

Caractéristiques principales :
- **Moteurs développés à 100% de façon autonome** : aucune bibliothèque tierce de compression externe (`bz2`, `lzma`, `zlib.compress`, 7-Zip externe) n'est appelée.
- Les algorithmes **LZ77**, **Codage Arithmétique 32 bits**, **Huffman**, **RLE** et **LZW/LZ78** sont intégralement implémentés à la main à partir des principes fondamentaux de la théorie de l'information.
- L'application dispose d'un **format d'archive binaire sécurisé (`.cla`)** prenant en charge l'arborescence complète de fichiers et sous-dossiers, avec contrôle d'intégrité **SHA-256** et sommes de contrôle **CRC32** par bloc.
- Une interface graphique Windows native professionnelle (PySide6) permet de naviguer dans les répertoires, créer des archives, prévisualiser leur contenu, tester leur intégrité en mémoire et extraire les données.
- Des modules d'analyse pas à pas permettent d'inspecter dynamiquement les structures internes (tableaux de fréquences, fenêtres glissantes, triplets, découpage d'intervalles fractionnaires).

---

## 2. Architecture du code source

```text
exam_codage_et_traitement_de_signal/
│
├── main.py                          # Point d'entrée de l'application WinRAR (PySide6)
├── requirements.txt                 # Dépendances (PySide6, pytest, reportlab)
├── README.md                        # Documentation complète en français
├── RAPPORT_COMPRESSLAB_EXAMEN.pdf   # Rapport technique d'évaluation généré sur mesures réelles
│
├── core/                            # Moteurs algorithmiques et conteneur .cla
│   ├── algorithms/
│   │   ├── lz77_engine.py           # Encodage/Décodage LZ77 avec buffer glissant et overlap
│   │   └── arithmetic_engine.py     # Codage Arithmétique entier 32-bit (Witten-Neal-Cleary)
│   ├── archive_format.py            # Format binaire propriétaire .cla & table des matières
│   ├── compression.py               # Orchestrateur de compression (LZ77, Arithmétique, Combiné)
│   ├── decompression.py             # Orchestrateur de décompression et sécurisation anti-traversée
│   ├── integrity.py                 # Contrôle cryptographique SHA-256
│   └── metrics.py                   # Calcul des taux de réduction et des débits
│
├── ui/                              # Interface graphique PySide6 (Clone WinRAR)
│   ├── main_window.py               # Fenêtre principale (menus, toolbar WinRAR, explorateur)
│   ├── theme.py                     # Thème WinRAR et générateur d'icônes vectorielles nettes
│   ├── archive_dialog.py            # Dialogue WinRAR « Ajouter à l'archive »
│   ├── extract_dialog.py            # Dialogue WinRAR « Extraire vers »
│   ├── progress_dialog.py           # Dialogue de progression avec annulation
│   ├── lz77_demo.py                 # Démonstration pédagogique pas à pas LZ77
│   ├── arithmetic_demo.py           # Démonstration pédagogique pas à pas CALCUL -> 0,144
│   ├── comparison_dialog.py         # Comparatif et benchmark des 4 catégories
│   └── info_dialog.py               # Propriétés et statistiques de l'archive
│
├── workers/                         # Tâches asynchrones non-bloquantes (QThread)
│   └── compression_worker.py        # Threads de compression, extraction et test
│
├── samples/                         # Échantillons réels pour les 4 catégories imposées
│   ├── generate_samples.py          # Générateur des 12 formats
│   ├── text/                        # sample.txt, sample.csv, sample.json
│   ├── audio/                       # sample.wav, sample.flac, sample.mp3
│   ├── image/                       # sample.bmp, sample.png, sample.jpeg
│   └── video/                       # sample.avi, sample.mkv, sample.mp4
│
├── reports/
│   └── generate_pdf_report.py       # Générateur du rapport officiel d'examen en PDF
│
└── tests/                           # Suite complète de tests automatisés (Pytest)
    ├── test_lz77.py                 # Tests unitaires LZ77 et exemples du cours
    ├── test_arithmetic.py           # Tests unitaires Arithmétique et exemple CALCUL
    ├── test_combined.py             # Tests du pipeline combiné
    ├── test_archive.py              # Tests du format .cla, CRC32 et anti-traversée
    ├── test_integrity.py            # Tests de l'intégrité SHA-256
    └── test_four_categories.py      # Tests sur les 12 formats réels
```

---

## 3. Installation sous Windows (PowerShell)

### Prérequis
- Windows 10 ou 11
- Python 3.11 installé et accessible dans le `PATH`

### Étapes d'installation
Ouvrez un terminal **PowerShell** dans le dossier du projet :

```powershell
# 1. Vérifier la version de Python
python --version

# 2. Installer les dépendances requises
python -m pip install -r requirements.txt

# 3. Générer les 12 fichiers d'échantillons multimédias
python samples/generate_samples.py

# 4. Lancer la suite de tests automatisés (26 tests)
python -m pytest tests/ -v

# 5. Démarrer l'application CompressLab Archive (Interface WinRAR)
python main.py
```

---

## 4. Explication pédagogique des algorithmes

### 4.1. Codage LZ77 (Lempel-Ziv 1977)
Le codage LZ77 repose sur l'exploitation des redondances textuelles et binaires à travers un **dictionnaire glissant** en mémoire :
1. **Buffer de recherche (Search Buffer)** : Zone contenant les octets déjà traités immédiatement précédents (taille configurable, typiquement 7 pour les exercices de cours, 4096 par défaut en production).
2. **Buffer d'entrée (Lookahead Buffer)** : Zone contenant les prochains octets à encoder (taille configurable, 6 pour le cours, 256 par défaut).
3. **Triplets de sortie** : L'algorithme recherche la plus longue chaîne du buffer d'entrée présente dans le buffer de recherche. Il émet un triplet selon la convention officielle du cours :
   $$\text{Triplet} = (\text{distance}, \text{longueur}, \text{caractère\_suivant})$$
   - $\text{distance}$ : Décalage en arrière (1-indexé depuis la fin du buffer de recherche). Vaut $0$ si aucune correspondance n'est trouvée.
   - $\text{longueur}$ : Nombre d'octets consécutifs qui coïncident. Vaut $0$ si aucun motif ne se répète.
   - $\text{caractère\_suivant}$ : Le premier octet non apparié qui suit la répétition.
4. **Gestion du chevauchement (Overlap)** : Si la répétition est périodique (longueur supérieure à la distance), le motif se répète de façon cyclique :
   $$\text{octet}(i) = \text{octet}(i \pmod d)$$
   Cette propriété est indispensable pour reproduire l'exemple du cours `(3, 5, D)` sur `RARRAD`.
5. **Décodage** : Le décodeur reconstruit le flux sans le fichier original : il recule de la distance indiquée, copie la longueur requise (avec gestion du chevauchement cyclique), puis ajoute le symbole suivant.

#### Validation du support de cours (`CABRACADABRARRARRAD`, $S=7, L=6$) :
| Étape | Buffer de recherche | Buffer d'entrée | Répétition | Triplet généré | Texte reconstruit |
|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | `[ ]` | `[CABRAC]` | - | `(0, 0, 'C')` | `C` |
| 2 | `[ C]` | `[ABRACA]` | - | `(0, 0, 'A')` | `CA` |
| 3 | `[ CA]` | `[BRACAD]` | - | `(0, 0, 'B')` | `CAB` |
| 4 | `[ CAB]` | `[RACADA]` | - | `(0, 0, 'R')` | `CABR` |
| 5 | `[ CABR]` | `[ACADAB]` | `'A'` | `(3, 1, 'C')` | `CABRAC` |
| 6 | `[ CABRAC]` | `[ADABRA]` | `'A'` | `(2, 1, 'D')` | `CABRACAD` |
| 7 | `[ABRACAD]` | `[ABRARR]` | `'ABRA'` | `(7, 4, 'R')` | `CABRACADABRAR` |
| 8 | `[ADABRAR]` | `[RARRAD]` | `'RARRA'` | `(3, 5, 'D')` | `CABRACADABRARRARRAD` |

---

### 4.2. Codage Arithmétique
Contrairement au codage de Huffman qui attribue un nombre entier de bits à chaque symbole, le codage arithmétique représente l'ensemble du message par un **unique sous-intervalle réel** dans $[0, 1[$ :

1. **Modélisation statistique** : On compte les occurrences de chaque symbole $s_i$ et on détermine sa fréquence relative $p(s_i) = \frac{\text{count}(s_i)}{N}$.
2. **Intervalles initiaux cumulés** : À chaque symbole est associé un intervalle disjoint $[L(s_i), H(s_i)[$ :
   $$L(s_i) = \sum_{j < i} p(s_j), \quad H(s_i) = L(s_i) + p(s_i)$$
3. **Raffinement successif** : En initialisant avec $[Low_0, High_0[ = [0, 1[$, chaque symbole lu $s_k$ rétrécit l'intervalle :
   $$\text{Range}_k = High_{k-1} - Low_{k-1}$$
   $$Low_k = Low_{k-1} + \text{Range}_k \times L(s_k)$$
   $$High_k = Low_{k-1} + \text{Range}_k \times H(s_k)$$
4. **Décodage** : On situe la valeur dans les intervalles cumulés pour retrouver le symbole, puis on retire la borne inférieure et on divise par la probabilité du symbole pour préparer l'étape suivante.

#### Exemple du cours `CALCUL` :
- Modèle : `C` (2 occurrences, probabilité $0,333$), `A` (1 occ., $0,166$), `L` (2 occ., $0,333$), `U` (1 occ., $0,166$).
- Intervalles initiaux arrondis : `C`: $[0 ; 0,333[$, `A`: $[0,333 ; 0,499[$, `L`: $[0,499 ; 0,832[$, `U`: $[0,832 ; 0,998[$.
- Raffinement pour `CALCUL` : intervalle final $[0,144499 ; 0,144832[$, aboutissant à la valeur tronquée **$0,144$** comme indiqué dans le transparent de cours.
- **Différence avec la version industrielle** : Les nombres flottants subissent un épuisement de précision (mantisse 64 bits limitée à ~15 caractères). Pour traiter des fichiers réels de plusieurs mégaoctets, notre logiciel applique l'algorithme de **Witten-Neal-Cleary** à intervalles entiers 32-bit avec renormalisation dynamique continue (échelles E1, E2 et E3 pour l'underflow), garantissant un décodage exact à 100% sans aucune dérive d'arrondi.

---

### 4.3. Pipeline Combiné (LZ77 + Arithmétique)
1. **Étape 1 (Dé-corrélation structurelle)** : Les données brutes sont encodées par le moteur LZ77 en triplets $(d, l, c)$.
2. **Étape 2 (Sérialisation binaire standardisée)** : Les triplets sont packés au format binaire compact (2 octets pour la distance, 2 octets pour la longueur, 1 octet pour le symbole suivant).
3. **Étape 3 (Compression entropique)** : Le flux binaire intermédiaire est encodé par le codeur arithmétique 32-bit, qui compresse drastiquement les zéros et les distributions statistiques des triplets.
4. **Décompression symétrique** : Décodeur Arithmétique $\to$ Reconstitution des triplets $\to$ Décodeur LZ77 $\to$ Données originales identiques au bit près.

---

## 5. Schéma du format d'archive propriétaire `.cla`

Le format **CompressLab Archive (`.cla`)** a été conçu pour être robuste, indépendant et insensible aux corruptions partielles :

```
┌────────────────────────────────────────────────────────────────────────┐
│ EN-TÊTE PRINCIPAL (20 octets)                                          │
│   • Magic Signature    : 4 octets b"CLAZ"                              │
│   • Version Majeure    : uint8 (1)                                     │
│   • Version Mineure    : uint8 (0)                                     │
│   • Flags              : uint16 (0)                                    │
│   • Nombre d'entrées   : uint32                                        │
│   • Offset Table (TOC) : uint64                                        │
├────────────────────────────────────────────────────────────────────────┤
│ BLOCS DE DONNÉES COMPRESSÉES                                           │
│   ┌──────────────────────────────────────────────────────────────┐     │
│   │ Bloc 1 : Payload compressé (LZ77 / Arithmétique / Combiné)   │     │
│   └──────────────────────────────────────────────────────────────┘     │
│   ┌──────────────────────────────────────────────────────────────┐     │
│   │ Bloc 2 : Payload compressé du fichier suivant...             │     │
│   └──────────────────────────────────────────────────────────────┘     │
├────────────────────────────────────────────────────────────────────────┤
│ TABLE DES MATIÈRES CENTRALE (TOC)                                      │
│   Pour chaque fichier ou sous-dossier :                                │
│   • Longueur du chemin relatif : uint16                                │
│   • Chemin relatif en UTF-8    : N octets                              │
│   • Is_Directory               : uint8 (0=Fichier, 1=Dossier)          │
│   • Taille non compressée      : uint64                                │
│   • Taille compressée          : uint64                                │
│   • Offset du bloc dans l'arch : uint64                                │
│   • Identifiant Algorithme     : uint8 (0=STORE, 1=LZ77, 2=ARITH, 3=CB)│
│   • Fenêtre Search Buffer      : uint16 (ex: 4096)                     │
│   • Fenêtre Lookahead Buffer   : uint16 (ex: 256)                      │
│   • Timestamp modification     : uint32 (Epoch)                        │
│   • Empreinte SHA-256 originale: 32 octets binaire                     │
│   • Checksum CRC32 du bloc     : uint32                                │
├────────────────────────────────────────────────────────────────────────┤
│ TRAILER DE FIN D'ARCHIVE (20 octets)                                   │
│   • Magic Fin d'archive        : 4 octets b"CLAE"                      │
│   • Checksum CRC32 de la TOC   : uint32                                │
│   • Nombre total d'entrées     : uint32                                │
│   • Taille totale de la TOC    : uint64                                │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Guide de démonstration devant l'examinateur

### Démonstration 1 : Les exemples officiels du cours
1. Lancez `python main.py`.
2. Cliquez sur **« Démo LZ77 »** dans la barre d'outils (ou menu *Outils* $\to$ *Démonstration Cours LZ77*).
   - Choisissez le préréglage 1 : `CABRACADABRARRARRAD`.
   - Observez le tableau étape par étape calculé en direct : la distance, la longueur, le symbole suivant et le triplet généré sont strictement identiques au support de cours.
   - Choisissez le préréglage 2 : `ABBBTTAYFGCABRYUIUUIACADBRARRARRAD` pour observer le comportement sur un alphabet plus étendu.
3. Cliquez sur **« Démo Arithmétique »** dans la barre d'outils.
   - Cliquez sur **« Exemple 'CALCUL' »**.
   - Constatez la table des fréquences, le découpage d'intervalles progressif et l'aboutissement au code `0,144`.
   - Basculez sur l'onglet **« Décodage progressif »** pour voir la reconstruction du mot `CALCUL`.

### Démonstration 2 : Création et extraction d'une archive .cla
1. Naviguez dans le dossier `samples/text/`.
2. Sélectionnez `sample.txt`, `sample.csv` et `sample.json`.
3. Cliquez sur le bouton **« Ajouter »** (icône livres WinRAR).
4. Choisissez l'algorithme (ex: *Pipeline Combiné* ou *LZ77 Seul*), puis cliquez sur **OK**.
5. Observez la fenêtre de progression et l'ouverture automatique de l'archive créée.
6. Cliquez sur **« Tester »** : le logiciel décompresse l'archive en mémoire et vérifie les empreintes SHA-256 de chaque fichier.
7. Double-cliquez sur un fichier dans l'archive pour le prévisualiser en direct.
8. Cliquez sur **« Extraire vers »** pour extraire les fichiers dans un dossier de votre choix en toute sécurité.

### Démonstration 3 : Comparatif réel et rapport PDF
1. Cliquez sur **« Comparatif 4 Catégories »** dans la barre d'outils.
2. Le logiciel exécute les 3 moteurs en direct sur les 12 formats et affiche les temps, les taux de réduction et l'intégrité SHA-256.
3. Cliquez sur **« Générer le rapport PDF officiel »** pour créer `RAPPORT_COMPRESSLAB_EXAMEN.pdf`.

---

## 7. Résultats mesurés sur les 4 catégories de fichiers

Calcul du taux de réduction :  
$$\text{Taux de réduction} = \frac{\text{Taille Originale} - \text{Taille Archive}}{\text{Taille Originale}} \times 100$$

| Catégorie | Format | Taille Orig. | LZ77 Seul | Arithmétique Seul | Pipeline Combiné | Intégrité SHA-256 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Texte** | TXT | 2 974 o | +64.5 % | +62.2 % | **+77.4 %** | Validée (100% Identique) |
| **Texte** | CSV | 4 826 o | +61.1 % | +53.8 % | **+71.7 %** | Validée (100% Identique) |
| **Texte** | JSON | 8 103 o | +81.6 % | +59.6 % | **+89.2 %** | Validée (100% Identique) |
| **Audio** | WAV | 8 044 o | +73.4 % | +72.1 % | **+84.4 %** | Validée (100% Identique) |
| **Audio** | FLAC | 346 o | +48.0 % | +31.8 % | **+64.2 %** | Validée (100% Identique) |
| **Audio** | MP3 | 4 190 o | -85.1 % | -2.3 % | **-70.4 %** | Validée (100% Identique) |
| **Image** | BMP | 12 342 o | -47.1 % | -1.1 % | **-34.4 %** | Validée (100% Identique) |
| **Image** | PNG | 195 o | -61.5 % | -12.3 % | **-10.8 %** | Validée (100% Identique) |
| **Image** | JPEG | 414 o | -193.5 % | -5.8 % | **-172.7 %** | Validée (100% Identique) |
| **Vidéo** | AVI | 1 408 o | +77.4 % | +61.2 % | **+86.6 %** | Validée (100% Identique) |
| **Vidéo** | MKV | 858 o | -173.2 % | -4.4 % | **-141.1 %** | Validée (100% Identique) |
| **Vidéo** | MP4 | 1 402 o | -110.1 % | -3.7 % | **-91.5 %** | Validée (100% Identique) |

> **Note scientifique sur les résultats négatifs** :  
> Conformément au théorème du codage de source de Shannon, les formats déjà compressés (MP3, JPEG, MP4) possèdent une entropie maximale. L'ajout d'en-têtes et de triplets LZ77 crée nécessairement une dilatation de taille. Ces valeurs négatives sont affichées en toute transparence sans masquer la réalité physique des données.

---

## 8. Exécution des tests automatisés (Pytest)

Pour relancer l'intégralité des 26 tests unitaires et d'intégration :

```powershell
python -m pytest tests/ -v
```

Tous les tests valident la propriété fondamentale :
$$\text{decode}(\text{encode}(\text{donnees})) == \text{donnees}$$
avec correspondance bit à bit des empreintes cryptographiques SHA-256.
