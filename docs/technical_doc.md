# RT-DENTX - Documentation Technique

## Architecture du système

### Vue d'ensemble

RT-DENTX est construit sur une architecture modulaire permettant une maintenance et une évolution facilitées. Le système suit le pattern MVC (Model-View-Controller) avec une séparation claire entre la logique métier, l'interface utilisateur et la gestion des données.

### Diagramme d'architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              RT-DENTX ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         INTERFACE UTILISATEUR                        │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │   │
│  │  │ Main Window  │  │ Dose Panel   │  │ Tooth Panel  │             │   │
│  │  │              │  │              │  │              │             │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │   │
│  └─────────┼──────────────────┼──────────────────┼─────────────────────┘   │
│            │                  │                  │                          │
│  ┌─────────▼──────────────────▼──────────────────▼─────────────────────┐   │
│  │                      COUCHE LOGIQUE MÉTIER                          │   │
│  │                                                                      │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐       │   │
│  │  │ DicomViewer    │  │ DoseReport     │  │ RTStruct       │       │   │
│  │  │ Main          │  │ Generator      │  │ Writer         │       │   │
│  │  └────────────────┘  └────────────────┘  └────────────────┘       │   │
│  │                                                                      │   │
│  │  ┌────────────────┐  ┌────────────────┐                           │   │
│  │  │ ToothReference │  │ ToothGenerator │                           │   │
│  │  │ Editor        │  │                │                           │   │
│  │  └────────────────┘  └────────────────┘                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         COUCHE DONNÉES                               │   │
│  │                                                                      │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐       │   │
│  │  │ DicomLoader    │  │ ConfigManager  │  │ PlanInfo       │       │   │
│  │  │                │  │                │  │ Enhanced       │       │   │
│  │  └────────────────┘  └────────────────┘  └────────────────┘       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Flux de données détaillé

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MAIN ENTRY POINT                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                 main.py                                     │
│                                    │                                        │
│                                    ▼                                        │
│                          dicom_viewer_main.py                               │
│                                    │                                        │
└──────────────┬──────────────┬───┴────────────┬───────────────────────────┘
                 │              │                │
                 ▼              ▼                ▼
┌──────────────────────┐ ┌──────────────┐ ┌────────────────────────────────┐
│    UI Components     │ │ Core Logic   │ │    Data Processing             │
│                      │ │              │ │                                │
│  - ui_panels.py      │ │ - DicomViewer│ │ - dicom_loader.py              │
│  - ToothPanel        │ │   main class │ │ - CT/RTDose/RTStruct loading  │
│  - DosePanel         │ │ - Viewer     │ │ - DICOM data extraction        │
│  - ConfigDialog      │ │   logic      │ │                                │
│                      │ │ - Display    │ └────────────────────────────────┘
│  ┌────────────────┐  │ │   management │
│  │ToothReference  │  │ │              │ ┌────────────────────────────────┐
│  │    Editor      │  │ └──────────────┘ │   Tooth Generation System      │
│  └────────────────┘  │                  │                                │
└──────────────────────┘                  │ - tooth_reference_editor.py    │
                                          │ - tooth_generator.py          │
                                          │ - 6 reference points          │
                                          │ - Auto-generation algorithm   │
                                          └────────────────────────────────┘
                                          
                                          ┌─────────────────────────────────┐
                                          │   Dose Report Generation        │
                                          │                                 │
                                          │ - dose_report_generator.py      │
                                          │ - rapport_pdf_enhanced.py       │
                                          │ - plan_info_enhanced.py         │
                                          │                                 │
                                          └─────────────────────────────────┘
```

### Modules principaux

#### 1. Interface utilisateur (ui_panels.py)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ui_panels.py                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ToothPanel:                                                                │
│  - Gestion des outils dentaires                                            │
│  - Placement des points de référence                                       │
│  - Génération des cylindres 3D                                             │
│  - Configuration des paramètres dentaires                                  │
│                                                                             │
│  DosePanel:                                                                 │
│  - Contrôles d'affichage de dose                                          │
│  - Ajustement Dmin/Dmax                                                    │
│  - Transparence et échelle de couleurs                                     │
│                                                                             │
│  ToothConfigDialog:                                                         │
│  - Édition des paramètres dentaires                                        │
│  - Modification en masse                                                    │
│  - Sauvegarde/réinitialisation                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 2. Génération de rapports

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WORKFLOW RAPPORT DOSIMÉTRIQUE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│            dicom_viewer_main.py                                             │
│                    │                                                        │
│                    ▼                                                        │
│         dose_report_generator.py                                            │
│                    │                                                        │
│         ┌──────────┴──────────┐                                            │
│         │                     │                                             │
│         ▼                     ▼                                             │
│  rapport_pdf_enhanced.py   plan_info_enhanced.py                           │
│         │                     │                                             │
│         └──────────┬──────────┘                                            │
│                    ▼                                                        │
│              PDF Report                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 3. Export RTStruct

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXPORT RTSTRUCT WORKFLOW                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│         rtstruct_export_integration.py                                      │
│                    │                                                        │
│                    ▼                                                        │
│            rtstruct_writer.py                                               │
│                    │                                                        │
│         ┌──────────┴──────────┐                                            │
│         │                     │                                             │
│         ▼                     ▼                                             │
│    Create New            Merge with                                        │
│    RTStruct              Existing                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 4. Système de génération dentaire

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TOOTH GENERATION WORKFLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│     1. Placement manuel (tooth_reference_editor.py)                         │
│        └─> 6 points de référence: 11, 13, 18, 41, 43, 48                   │
│                                                                             │
│     2. Génération automatique (tooth_generator.py)                          │
│        ├─> Interpolation latérale (dents adjacentes)                       │
│        ├─> Symétrie axiale (dents controlatérales)                         │
│        └─> Calcul des positions intermédiaires                             │
│                                                                             │
│     3. Mode édition (tooth_reference_editor.py)                             │
│        ├─> Ajustement manuel des positions                                 │
│        ├─> Sélection multiple et déplacement                               │
│        └─> Validation des positions                                        │
│                                                                             │
│     4. Génération 3D (dicom_viewer_main.py)                                │
│        └─> Création des cylindres avec paramètres configurables            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Configuration système

### Structure de configuration

```json
{
  "risk_levels": {
    "low_threshold": 30,
    "moderate_threshold": 50,
    "low_label": "Risque faible",
    "moderate_label": "Risque modéré",
    "high_label": "Risque élevé"
  },
  "tooth_parameters": {
    "11": {
      "crown_height": 11.0,
      "root_height": 12.0,
      "diameter": 7.5,
      "inclination": 0.0
    }
  },
  "recommendations": {
    "title": "Recommandations cliniques",
    "content": "..."
  }
}
```

### Hiérarchie de configuration

1. **Configuration par défaut** (code source)
2. **Configuration persistante** (~/.rt_dentx/config.json)
3. **Configuration de session** (mémoire)

## Formats de données

### Format DICOM supporté

- **CT Series** : Images scanner
- **RTStruct** : Structures anatomiques
- **RTDose** : Distribution de dose
- **RTPlan** : Plan de traitement (optionnel)

### Format de sortie

- **PDF** : Rapports dosimétriques
- **DICOM RTStruct** : Structures dentaires exportées
- **JSON** : Configuration exportée

## Performance et optimisation

### Gestion mémoire

- Chargement progressif des slices CT
- Cache des calculs de dose
- Libération automatique des ressources non utilisées



## Déploiement

### Build de l'exécutable

```bash
# Script de build principal
python instant_splash_launcher.py

# Crée deux exécutables:
# - RT-DENTX.exe (lanceur avec splash screen)
# - RT-DENTX-Core.exe (application principale)
```

### Structure de distribution

```
RT-DENTX/
├── RT-DENTX.exe           # Lanceur principal
├── RT-DENTX-Core.exe      # Application
└── assets/                # Ressources
    ├── rt_dentx_logo.png
    ├── rt_dentx_logo.ico
    ├── dental_metrics.png
    ├── dental_schema.png
    └── dental_schema_2.png
```

## Tests et validation

### Tests unitaires recommandés

- Chargement DICOM
- Calculs dosimétriques
- Génération de positions dentaires
- Export RTStruct
- Génération PDF

### Validation clinique

- Comparaison avec TPS commercial
- Validation des doses calculées
- Vérification des seuils de risque


---

*Document technique RT-DENTX v2.0 - © 2025 Caroline Moreau-Noblet*