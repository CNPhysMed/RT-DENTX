# RT-DENTX API Reference

## Table des matières

1. [DicomViewer](#dicomviewer)
2. [DicomLoader](#dicomloader)
3. [DoseReportGenerator](#dosereportgenerator)
4. [ConfigManager](#configmanager)
5. [RTStructWriter](#rtstructwriter)
6. [UIPanel](#uipanel)
7. [ToothGenerator](#toothgenerator)
8. [ToothReferenceEditor](#toothreferenceeditor)

---

## DicomViewer

**Classe principale de l'application RT-DENTX**

```python
class DicomViewer(tk.Tk)
```

### Méthodes principales

#### `__init__(self)`
Initialise l'application principale.

#### `load_dicom_folder(self, folder_path=None)`
Charge un dossier DICOM complet.

**Paramètres:**
- `folder_path` (str, optional): Chemin vers le dossier DICOM

**Retour:**
- `bool`: True si chargement réussi

#### `update_display(self)`
Met à jour l'affichage de la vue courante.

#### `extract_doses_for_structures(self, structures, ct_slices, rtdose_data, pixel_array)`
Extrait les doses pour les structures spécifiées.

**Paramètres:**
- `structures` (dict): Dictionnaire des structures {nom: contours}
- `ct_slices` (list): Liste des coupes CT
- `rtdose_data` (dict): Données RTDose
- `pixel_array` (np.array): Matrice de dose

**Retour:**
- `dict`: Doses par structure

---

## DicomLoader

**Module de chargement des fichiers DICOM**

```python
class DicomLoader
```

### Fonctions

#### `load_ct_series(folder_path)`
Charge une série CT depuis un dossier.

**Paramètres:**
- `folder_path` (str): Chemin du dossier

**Retour:**
- `list`: Liste des slices CT triées

#### `load_rtstruct(file_path, ct_slices)`
Charge un fichier RTStruct.

**Paramètres:**
- `file_path` (str): Chemin du fichier RTStruct
- `ct_slices` (list): Slices CT de référence

**Retour:**
- `tuple`: (contours, roi_names)

#### `load_rtdose(file_path, ct_slices)`
Charge un fichier RTDose.

**Paramètres:**
- `file_path` (str): Chemin du fichier RTDose
- `ct_slices` (list): Slices CT de référence

**Retour:**
- `dict`: Données de dose avec clés 'pixel_array', 'grid_positions', etc.

---

## DoseReportGenerator

**Générateur de rapports dosimétriques**

```python
class DoseReportGenerator(tk.Toplevel)
```

### Méthodes

#### `__init__(self, parent, ct_viewer)`
Initialise le générateur de rapport.

**Paramètres:**
- `parent`: Widget parent
- `ct_viewer`: Instance du DicomViewer

#### `calculate_doses(self)`
Calcule les doses pour toutes les structures dentaires.

**Retour:**
- `dict`: Dictionnaire des doses calculées

#### `generate_report(self)`
Lance la génération du rapport PDF.

#### `update_risk_display(self)`
Met à jour l'affichage des niveaux de risque.

### Propriétés

- `risk_thresholds` (dict): Seuils de risque configurables
- `report_parameters` (dict): Paramètres du rapport

---

## ConfigManager

**Gestionnaire de configuration**

```python
class ConfigManager
```

### Méthodes

#### `__init__(self)`
Initialise le gestionnaire avec la configuration par défaut.

#### `get_tooth_params(self, tooth_name)`
Récupère les paramètres d'une dent.

**Paramètres:**
- `tooth_name` (str): Nom de la dent (ex: "C_11")

**Retour:**
- `dict`: Paramètres de la dent

#### `update_tooth_params(self, tooth_name, params)`
Met à jour les paramètres d'une dent.

**Paramètres:**
- `tooth_name` (str): Nom de la dent
- `params` (dict): Nouveaux paramètres

#### `get_risk_thresholds(self)`
Récupère les seuils de risque.

**Retour:**
- `dict`: {'low': 30, 'moderate': 50}

#### `save_config(self)`
Sauvegarde la configuration actuelle.

#### `reset_to_default(self)`
Réinitialise aux valeurs par défaut.

---

## RTStructWriter

**Écriture de fichiers RTStruct**

```python
class RTStructWriter
```

### Méthodes

#### `create_rtstruct_from_ct(ct_slices, patient_info=None)`
Crée un nouveau RTStruct depuis des slices CT.

**Paramètres:**
- `ct_slices` (list): Slices CT de référence
- `patient_info` (dict, optional): Informations patient

**Retour:**
- `Dataset`: RTStruct DICOM

#### `add_roi_contour(rtstruct_ds, roi_name, contours, color)`
Ajoute un ROI au RTStruct.

**Paramètres:**
- `rtstruct_ds` (Dataset): RTStruct cible
- `roi_name` (str): Nom du ROI
- `contours` (dict): Contours par slice
- `color` (tuple): Couleur RGB (0-255)

#### `merge_rtstructs(original_rs, dental_rs)`
Fusionne deux RTStruct.

**Paramètres:**
- `original_rs` (Dataset): RTStruct original
- `dental_rs` (Dataset): RTStruct avec structures dentaires

**Retour:**
- `Dataset`: RTStruct fusionné

---

## UIPanel

**Panneau d'interface utilisateur**

```python
class UIPanel
```

### Classes principales

#### `ToothPanel`
Gère l'interface des outils dentaires.

**Méthodes:**
- `update_button_states()`: Met à jour l'état des boutons
- `show_tooth_config()`: Affiche la configuration dentaire

#### `ToothConfigDialog`
Dialogue de configuration des paramètres dentaires.

**Méthodes:**
- `populate_table()`: Remplit le tableau des dents
- `save_changes()`: Sauvegarde les modifications
- `bulk_edit_dialog()`: Édition en masse

#### `DosePanel`
Panneau de contrôle de l'affichage de dose.

**Méthodes:**
- `toggle_dose()`: Active/désactive l'affichage
- `apply_threshold_entry()`: Applique le seuil Dmin
- `update_custom_dose_scale()`: Met à jour l'échelle

---

## ToothGenerator

**Génération automatique des positions dentaires**

```python
class ToothGenerator
```

### Méthodes principales

#### `__init__(self, reference_points)`
Initialise le générateur avec les points de référence.

**Paramètres:**
- `reference_points` (dict): Points de référence {nom_dent: (x, y, z)}

#### `generate_all_teeth(self, ct_viewer=None)`
Génère toutes les positions dentaires à partir des points de référence.

**Paramètres:**
- `ct_viewer` (DicomViewer, optional): Instance du viewer pour récupérer la config

**Retour:**
- `dict`: Positions de toutes les dents {nom_dent: (x, y, z)}

#### `get_tooth_crown_height(self, tooth_name, ct_viewer=None)`
Récupère la hauteur de couronne configurée.

**Paramètres:**
- `tooth_name` (str): Nom de la dent
- `ct_viewer` (DicomViewer, optional): Instance pour config personnalisée

**Retour:**
- `float`: Hauteur de couronne en mm

#### `get_tooth_root_height(self, tooth_name, ct_viewer=None)`
Récupère la hauteur de racine configurée.

**Retour:**
- `float`: Hauteur de racine en mm

#### `get_tooth_diameter(self, tooth_name, ct_viewer=None)`
Récupère le diamètre configuré.

**Retour:**
- `float`: Diamètre en mm

#### `get_tooth_inclination(self, tooth_name, ct_viewer=None)`
Récupère l'inclinaison configurée.

**Retour:**
- `float`: Inclinaison en degrés

---

## ToothReferenceEditor

**Éditeur interactif de points de référence**

```python
class ToothReferenceEditor
```

### Méthodes principales

#### `__init__(self, ax, canvas, get_current_slice_index, ct_viewer)`
Initialise l'éditeur de points.

**Paramètres:**
- `ax`: Axes matplotlib pour l'affichage
- `canvas`: Canvas matplotlib
- `get_current_slice_index`: Fonction pour obtenir l'index de coupe
- `ct_viewer`: Instance du DicomViewer

#### `start_placing_mode(self)`
Active le mode placement des points de référence.

#### `start_edit_mode(self)`
Active le mode édition des points existants.

#### `is_complete(self)`
Vérifie si tous les points de référence sont placés.

**Retour:**
- `bool`: True si les 6 points sont placés

#### `draw_all_points(self)`
Redessine tous les points sur la vue actuelle.

#### `on_press(self, event)`
Gère les événements de clic souris.

**Paramètres:**
- `event`: Événement matplotlib

#### `on_motion(self, event)`
Gère les mouvements de souris.

#### `on_release(self, event)`
Gère le relâchement du clic souris.

### Propriétés

- `reference_teeth` (list): Liste des 6 dents de référence ["11", "13", "18", "41", "43", "48"]
- `points` (dict): Dictionnaire des points placés {nom_dent: (x, y, z)}
- `edit_mode` (bool): Mode édition actif
- `placing_mode` (bool): Mode placement actif

---

## Structures de données

### Structure dentaire
```python
tooth_structure = {
    'name': 'C_11',
    'crown_height': 11.0,
    'root_height': 12.0,
    'diameter': 7.5,
    'inclination': 0.0,
    'position': (x, y, z)
}
```

### Données de dose
```python
dose_data = {
    'pixel_array': np.array,  # Matrice 3D de dose
    'grid_positions': {
        'x': np.array,
        'y': np.array,
        'z': np.array
    },
    'dose_units': 'GY',
    'scaling_factor': 1.0
}
```

### Configuration de risque
```python
risk_config = {
    'thresholds': {
        'low': 30,    # Gy
        'medium': 50  # Gy
    },
    'colors': {
        'low': '#4CAF50',
        'medium': '#FF9800',
        'high': '#F44336'
    }
}
```

---

## Exemples d'utilisation

### Chargement et analyse basique

```python
# Créer l'application
app = DicomViewer()

# Charger les données
app.load_dicom_folder('/path/to/dicom')

# Générer les structures dentaires
app.generate_3d_cylinders()

# Calculer les doses
doses = app.extract_doses_for_structures(
    app.dental_structures,
    app.ct_slices,
    app.rtdose_data,
    app.dose_pixel_array
)
```

### Génération de rapport

```python
# Ouvrir le générateur
generator = DoseReportGenerator(app, app)

# Configurer les seuils
generator.risk_thresholds = {'low': 25, 'medium': 45}

# Générer le rapport
generator.generate_report()
```

### Export RTStruct

```python
from rtstruct_writer import RTStructWriter

# Créer un nouveau RTStruct
writer = RTStructWriter()
rtstruct = writer.create_rtstruct_from_ct(ct_slices)

# Ajouter les structures dentaires
for name, contours in dental_structures.items():
    writer.add_roi_contour(
        rtstruct,
        name,
        contours,
        color=(255, 0, 0)
    )

# Sauvegarder
rtstruct.save_as('dental_structures.dcm')
```