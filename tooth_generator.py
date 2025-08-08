#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de génération automatique des dents
Interpolation et symétrie à partir des points de référence 
© 2025 Caroline Moreau-Noblet — RT-DENTX — Licence BSD 3-Clause
"""

import numpy as np
import os
import pydicom
import logging
import tkinter as tk

logger = logging.getLogger(__name__)

# SOURCES PRINCIPALES :
# 1. Al-Habib, M.A. et al. (2024). "Advancing Endodontic and Prosthodontic Precision: 
#    A Cone-Beam Computed Tomography-based Study of Crown-root Ratios and Root Canal 
#    Lengths in a Saudi Subpopulation Cohort" - Crown lengths: 8.1-10.3mm, Root lengths: 12.9-18.2mm
#
# 2. Lim, J.H. et al. (2013). "Crown and root lengths of incisors, canines, and premolars 
#    measured by cone-beam computed tomography in patients with malocclusions"
#    PMC3879283 - Validation CBCT vs mesures directes
#
# 3. Al-Sharawi, B.M. et al. (2019). "In-depth morphological evaluation of tooth anatomic 
#    lengths with root canal configurations using cone beam computed tomography in North 
#    American population" PMC6999117
#
# 4. Wheeler's Dental Anatomy, Physiology and Occlusion, 11th Edition (Nelson & Ash, 2023)
#    - Référence classique en anatomie dentaire
#
# 5. Galucci, G.O. et al. (2003). "Anatomic crown width/length ratios of unworn and worn 
#    maxillary teeth in white subjects" J Prosthet Dent. PubMed: 12806322
TOOTH_ANATOMY = {
    # INCISIVES MAXILLAIRES
    # Source: Al-Habib et al. - "longest crowns found in the maxillary central incisors"
    # Galucci et al. - Incisives centrales max: W=8.6±0.6mm, L=10.8±1.1mm
    '11': {'crown': 10.5, 'root': 13.0, 'diameter': 7.0},   # ✓ Cohérent avec littérature
    '12': {'crown': 9.0, 'root': 13.0, 'diameter': 6.0},    # ✓ Cohérent avec Wheeler's
    '21': {'crown': 10.5, 'root': 13.0, 'diameter': 7.0},   # ✓ Symétrique à 11
    '22': {'crown': 9.0, 'root': 13.0, 'diameter': 6.0},    # ✓ Symétrique à 12

    # CANINES MAXILLAIRES 
    # Source: Al-Habib et al. - "canines having the longest roots" (jusqu'à 18.2mm)
    # Al-Sharawi et al. - Ratios couronne/racine canines: 2.05 (maxillaires)
    '13': {'crown': 10.0, 'root': 17.0, 'diameter': 8.0},   # ✓ Racine la plus longue confirmée
    '23': {'crown': 10.0, 'root': 17.0, 'diameter': 8.0},   # ✓ Symétrique

    # PRÉMOLAIRES MAXILLAIRES
    # Source: Lim et al. - Mesures CBCT prémolaires, Wheeler's Dental Anatomy
    '14': {'crown': 8.5, 'root': 14.0, 'diameter': 9.0},    # ✓ Wheeler's confirmed
    '15': {'crown': 8.5, 'root': 14.0, 'diameter': 9.0},    # ✓ Wheeler's confirmed
    '24': {'crown': 8.5, 'root': 14.0, 'diameter': 9.0},    # ✓ Symétrique
    '25': {'crown': 8.5, 'root': 14.0, 'diameter': 9.0},    # ✓ Symétrique

    # MOLAIRES MAXILLAIRES
    # Source: Wheeler's Dental Anatomy, Al-Sharawi et al.
    '16': {'crown': 7.5, 'root': 12.0, 'diameter': 11.0},   # ✓ Wheeler's standard
    '17': {'crown': 7.0, 'root': 12.0, 'diameter': 11.0},   # ✓ Wheeler's standard
    '18': {'crown': 6.5, 'root': 11.0, 'diameter': 10.0},   # ✓ Wheeler's standard
    '26': {'crown': 7.5, 'root': 12.0, 'diameter': 11.0},   # ✓ Symétrique
    '27': {'crown': 7.0, 'root': 12.0, 'diameter': 11.0},   # ✓ Symétrique
    '28': {'crown': 6.5, 'root': 11.0, 'diameter': 10.0},   # ✓ Symétrique

    # INCISIVES MANDIBULAIRES
    # Source: Dimensions of Dental Hygiene (2021) - "Mandibular anteriors have extremely narrow roots"
    # Al-Habib et al. - Incisives mandibulaires généralement plus courtes que maxillaires
    # Lim et al. - Mesures CBCT: couronnes mandibulaires < maxillaires
    '31': {'crown': 8.5, 'root': 12.5, 'diameter': 6.0},    # AJUSTÉ: 9→8.5mm (littérature)
    '32': {'crown': 8.8, 'root': 14.0, 'diameter': 6.5},    # AJUSTÉ: 9.5→8.8mm (littérature)
    '41': {'crown': 8.5, 'root': 12.5, 'diameter': 6.0},    # AJUSTÉ: symétrique à 31
    '42': {'crown': 8.8, 'root': 14.0, 'diameter': 6.5},    # AJUSTÉ: symétrique à 32

    # CANINES MANDIBULAIRES
    # Source: Al-Habib et al. - Ratios couronne/racine canines mand: 1.91
    # Al-Sharawi et al. - Canines: racines longues mais < maxillaires
    '33': {'crown': 11.0, 'root': 15.5, 'diameter': 7.5},   # AJUSTÉ: 16→15.5mm (CBCT data)
    '43': {'crown': 11.0, 'root': 15.5, 'diameter': 7.5},   # AJUSTÉ: symétrique

    # PRÉMOLAIRES MANDIBULAIRES
    # Source: Wheeler's Dental Anatomy, Lim et al. - Mesures CBCT validées
    '34': {'crown': 8.5, 'root': 14.0, 'diameter': 7.0},    # ✓ Wheeler's confirmed
    '35': {'crown': 8.0, 'root': 14.5, 'diameter': 8.0},    # ✓ Wheeler's confirmed
    '44': {'crown': 8.5, 'root': 14.0, 'diameter': 7.0},    # ✓ Symétrique
    '45': {'crown': 8.0, 'root': 14.5, 'diameter': 8.0},    # ✓ Symétrique

    # MOLAIRES MANDIBULAIRES
    # Source: Wheeler's Dental Anatomy, Al-Sharawi et al.
    '36': {'crown': 7.5, 'root': 14.0, 'diameter': 10.5},   # ✓ Wheeler's standard
    '37': {'crown': 7.0, 'root': 13.0, 'diameter': 10.0},   # ✓ Wheeler's standard
    '38': {'crown': 7.0, 'root': 11.0, 'diameter': 9.5},    # ✓ Wheeler's standard
    '46': {'crown': 7.5, 'root': 14.0, 'diameter': 10.5},   # ✓ Symétrique
    '47': {'crown': 7.0, 'root': 13.0, 'diameter': 10.0},   # ✓ Symétrique
    '48': {'crown': 7.0, 'root': 11.0, 'diameter': 9.5}     # ✓ Symétrique
}

# Inclinaisons facio-linguales moyennes (source CBCT, données typiques en ortho/dento)
# Sources: Données CBCT typiques utilisées en orthodontie et dentisterie
# Basées sur les standards de Wheeler's Dental Anatomy et études d'inclinaison dentaire
TOOTH_INCLINATIONS = {
    # MAXILLAIRES - Plus inclinées vers l'avant (lingual vers vestibulaire)
    '11': 28.0, '12': 26.0, '13': 20.0, '14': 10.0, '15': 8.0,  '16': 6.0,  '17': 5.0,  '18': 4.0,
    '21': 28.0, '22': 26.0, '23': 20.0, '24': 10.0, '25': 8.0,  '26': 6.0,  '27': 5.0,  '28': 4.0,
    
    # MANDIBULAIRES - Légèrement moins inclinées que les maxillaires
    '31': 25.0, '32': 24.0, '33': 18.0, '34': 10.0, '35': 9.0,  '36': 6.0,  '37': 5.0,  '38': 4.0,
    '41': 25.0, '42': 24.0, '43': 18.0, '44': 10.0, '45': 9.0,  '46': 6.0,  '47': 5.0,  '48': 4.0
}

# Fonction utilitaire pour obtenir les valeurs par défaut d'une dent
def get_tooth_default_values(tooth_name):
    """
    Retourne les valeurs par défaut complètes d'une dent
    
    Args:
        tooth_name (str): Numéro de la dent (ex: '11', '23', etc.)
        
    Returns:
        dict: Dictionnaire avec crown_height, root_height, diameter, inclination
    """
    if tooth_name not in TOOTH_ANATOMY:
        # Valeur de fallback
        return {
            'crown_height': 8.0,
            'root_height': 12.0,
            'diameter': 7.0,
            'inclination': 15.0
        }
    
    anatomy = TOOTH_ANATOMY[tooth_name]
    inclination = TOOTH_INCLINATIONS.get(tooth_name, 0.0)
    
    return {
        'crown_height': anatomy['crown'],
        'root_height': anatomy['root'],
        'diameter': anatomy['diameter'],
        'inclination': inclination
    }

class ToothGenerator:
    """Générateur automatique de points dentaires avec symétrie"""
    
    
    
    # Utiliser les constantes globales au lieu de redéfinir
    TOOTH_ANATOMY = TOOTH_ANATOMY  # Référence vers la constante globale
    TOOTH_INCLINATIONS = TOOTH_INCLINATIONS  # Référence vers la constante globale
    
    def __init__(self, reference_points):
        self.reference_points = reference_points.copy()
        self.generated_points = {}
        self.symmetry_offset = -3
        
        # Gestionnaire de configuration
        self.config_manager = None
        self._init_config_manager()  
    
    def _init_config_manager(self):
        """Initialise le gestionnaire de configuration"""
        try:
            from tooth_config_manager import ToothConfigManager
            self.config_manager = ToothConfigManager()
            logger.info("Gestionnaire de configuration dentaire initialisé")
        except ImportError:
            logger.warning("ToothConfigManager non disponible - utilisation des valeurs par défaut")
            self.config_manager = None
    
    
            
    def get_tooth_crown_height(self, tooth_name, ct_viewer=None):
        """Récupère la hauteur de la couronne avec configuration dynamique"""
        # PRIORITÉ 1 : Configuration de session du viewer (déjà implémenté)
        if ct_viewer and hasattr(ct_viewer, 'custom_tooth_config'):
            custom_config = ct_viewer.custom_tooth_config.get(tooth_name, {})
            if 'crown_height' in custom_config:
                return custom_config['crown_height']
        
        # PRIORITÉ 2 : Gestionnaire de configuration (déjà implémenté)
        if self.config_manager:
            config = self.config_manager.get_tooth_config(tooth_name)
            if 'crown_height' in config:
                return config['crown_height']
        
        # PRIORITÉ 3 : Valeurs par défaut
        return self.TOOTH_ANATOMY.get(tooth_name, {'crown': 8.0})['crown']
    
    def get_tooth_root_height(self, tooth_name, ct_viewer=None):
        """Récupère la hauteur de la racine avec configuration dynamique """
        # PRIORITÉ 1 : Configuration de session du viewer
        if ct_viewer and hasattr(ct_viewer, 'custom_tooth_config'):
            custom_config = ct_viewer.custom_tooth_config.get(tooth_name, {})
            if 'root_height' in custom_config:
                print(f"[DEBUG] {tooth_name}.root_height depuis viewer: {custom_config['root_height']}")
                return custom_config['root_height']
        
        # PRIORITÉ 2 : Gestionnaire de configuration
        if self.config_manager:
            config = self.config_manager.get_tooth_config(tooth_name)
            if 'root_height' in config:
                print(f"[DEBUG] {tooth_name}.root_height depuis config_manager: {config['root_height']}")
                return config['root_height']
        
        # PRIORITÉ 3 : Valeurs par défaut
        default_value = self.TOOTH_ANATOMY.get(tooth_name, {'root': 12.0})['root']
        print(f"[DEBUG] {tooth_name}.root_height depuis défaut: {default_value}")
        return default_value
    
    def get_tooth_diameter(self, tooth_name, ct_viewer=None):
        """Récupère le diamètre de la dent avec configuration dynamique """
        # PRIORITÉ 1 : Configuration de session du viewer
        if ct_viewer and hasattr(ct_viewer, 'custom_tooth_config'):
            custom_config = ct_viewer.custom_tooth_config.get(tooth_name, {})
            if 'diameter' in custom_config:
                print(f"[DEBUG] {tooth_name}.diameter depuis viewer: {custom_config['diameter']}")
                return custom_config['diameter']
        
        # PRIORITÉ 2 : Gestionnaire de configuration
        if self.config_manager:
            config = self.config_manager.get_tooth_config(tooth_name)
            if 'diameter' in config:
                print(f"[DEBUG] {tooth_name}.diameter depuis config_manager: {config['diameter']}")
                return config['diameter']
        
        # PRIORITÉ 3 : Valeurs par défaut
        default_value = self.TOOTH_ANATOMY.get(tooth_name, {'diameter': 6.0})['diameter']
        print(f"[DEBUG] {tooth_name}.diameter depuis défaut: {default_value}")
        return default_value
    
    def get_tooth_inclination(self, tooth_name, ct_viewer=None):
        """Récupère l'inclinaison de la dent avec configuration dynamique"""
        # PRIORITÉ 1 : Configuration de session du viewer
        if ct_viewer and hasattr(ct_viewer, 'custom_tooth_config'):
            custom_config = ct_viewer.custom_tooth_config.get(tooth_name, {})
            if 'inclination' in custom_config:
                print(f"[DEBUG] {tooth_name}.inclination depuis viewer: {custom_config['inclination']}")
                return custom_config['inclination']
        
        # PRIORITÉ 2 : Gestionnaire de configuration
        if self.config_manager:
            config = self.config_manager.get_tooth_config(tooth_name)
            if 'inclination' in config:
                print(f"[DEBUG] {tooth_name}.inclination depuis config_manager: {config['inclination']}")
                return config['inclination']
        
        # PRIORITÉ 3 : Valeurs par défaut
        default_value = self.TOOTH_INCLINATIONS.get(tooth_name, 0.0)
        print(f"[DEBUG] {tooth_name}.inclination depuis défaut: {default_value}")
        return default_value
    
    def get_tooth_anatomy_complete(self, tooth_name, ct_viewer=None):
        """Récupère tous les paramètres anatomiques d'une dent"""
        return {
            'crown_height': self.get_tooth_crown_height(tooth_name, ct_viewer),
            'root_height': self.get_tooth_root_height(tooth_name, ct_viewer),
            'diameter': self.get_tooth_diameter(tooth_name, ct_viewer),
            'inclination': self.get_tooth_inclination(tooth_name, ct_viewer)
        }
    
    def update_tooth_config(self, config, session_only=False):
        """Met à jour la configuration des dents"""
        if not self.config_manager:
            logger.warning("Gestionnaire de configuration non disponible")
            return False
        
        try:
            # Valider la configuration
            errors = self.config_manager.validate_config(config)
            if errors:
                logger.error(f"Configuration invalide: {errors}")
                return False
            
            if session_only:
                self.config_manager.set_session_config(config)
                logger.info("Configuration appliquée pour la session")
            else:
                success = self.config_manager.save_persistent_config(config)
                if success:
                    logger.info("Configuration sauvegardée de manière permanente")
                return success
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur mise à jour configuration: {e}")
            return False
    
    def update_viewer_config(self, ct_viewer):
        """Met à jour la référence au viewer pour récupérer la config à jour"""
        print(f"[DEBUG] ToothGenerator.update_viewer_config appelé")
        if hasattr(ct_viewer, 'custom_tooth_config'):
            print(f"[DEBUG] Viewer a custom_tooth_config: {len(ct_viewer.custom_tooth_config)} dents")
        else:
            print(f"[DEBUG] Viewer n'a PAS de custom_tooth_config")
    
    def reset_tooth_config(self):
        """Remet la configuration aux valeurs par défaut"""
        if self.config_manager:
            return self.config_manager.reset_to_default()
        return False
    
    def get_config_info(self):
        """Retourne des informations sur la configuration active"""
        if self.config_manager:
            return self.config_manager.get_config_info()
        return {'active_type': 'default', 'description': 'Configuration par défaut'}
    
    def export_tooth_config(self, filepath):
        """Exporte la configuration actuelle"""
        if self.config_manager:
            return self.config_manager.export_config(filepath)
        return False
    
    def import_tooth_config(self, filepath):
        """Importe une configuration depuis un fichier"""
        if self.config_manager:
            return self.config_manager.import_config(filepath)
        return None

    
        
    
    def generate_all_teeth(self, ct_viewer=None):
        """Génère tous les points dentaires à partir des références"""
        logger.info("Démarrage génération automatique des dents")
        
        
        
        # Interpolation dans chaque demi-arcade - MÊME LOGIQUE QUE L'ANCIEN
        self.interpolate_half_arcade('sup', ['11', '13'], ['12'])
        self.interpolate_half_arcade('sup', ['13', '18'], ['14', '15', '16', '17'])
        self.interpolate_half_arcade('inf', ['41', '43'], ['42'])
        self.interpolate_half_arcade('inf', ['43', '48'], ['44', '45', '46', '47'])
        
        # Utiliser la même logique de symétrie que l'ancien fichier
        self.generate_symmetric_arcade('sup', offset=self.symmetry_offset)
        self.generate_symmetric_arcade('inf', offset=self.symmetry_offset)
        
        
        
        logger.info(f"Génération terminée: {len(self.generated_points)} points générés")
        return self.generated_points
    
    
    
    def get_tooth_anatomy(self, tooth_name, ct_viewer=None):
        """
        Récupère les paramètres anatomiques d'une dent avec support de la configuration personnalisée
    
        LOGIQUE :
        1. Commence par les valeurs par défaut de TOOTH_ANATOMY (crown, root, diameter)
        2. Si une config personnalisée existe, surcharge SEULEMENT les paramètres modifiés
        3. Les paramètres non mentionnés dans la config personnalisée gardent leurs valeurs par défaut
        
        Args:
            tooth_name (str): Numéro de la dent (ex: '11', '23', etc.)
            ct_viewer: Instance du viewer pour accéder à la config personnalisée
            
        Returns:
            dict: Paramètres anatomiques complets (diameter, crown, root)
        """
        # Paramètres par défaut depuis TOOTH_ANATOMY
        default_params = self.TOOTH_ANATOMY.get(tooth_name, {
            'crown': 8.0, 'root': 12.0, 'diameter': 6.0 # Fallback si dent inconnue
        })
        
        final_params = default_params.copy()
    
        #Appliquer les surcharges personnalisées SI elles existent
        if ct_viewer and hasattr(ct_viewer, 'custom_tooth_config'):
            custom_config = ct_viewer.custom_tooth_config.get(tooth_name, {})
            
            # Surcharger UNIQUEMENT le diamètre si spécifié
            if 'diameter' in custom_config:
                final_params['diameter'] = custom_config['diameter']
        
        return default_params
    
    
    
    
    def interpolate_half_arcade(self, arcade, ref_keys, new_keys):
        """Interpolation linéaire entre deux points de référence """
        if not all(k in self.reference_points for k in ref_keys):
            logger.warning(f"Points de référence manquants pour {arcade}: {ref_keys}")
            return

        (x1, y1, z1) = self.reference_points[ref_keys[0]]
        (x2, y2, z2) = self.reference_points[ref_keys[1]]
        z = int(round((z1 + z2) / 2))

        n = len(new_keys)
        for i, name in enumerate(new_keys):
            t = (i + 1) / (n + 1)
            x = (1 - t) * x1 + t * x2
            y = (1 - t) * y1 + t * y2
            self.generated_points[name] = (x, y, z)
            logger.debug(f"Interpolé {name}: ({x:.1f}, {y:.1f}, {z})")
    
    def generate_symmetric_arcade(self, arcade, offset=5):
        """Génération symétrique d'une arcade """
        if arcade == 'sup':
            base_keys = ['11', '12', '13', '14', '15', '16', '17', '18']
            tgt_keys = ['21', '22', '23', '24', '25', '26', '27', '28']
            origin_key = '11'
        else:
            base_keys = ['41', '42', '43', '44', '45', '46', '47', '48']  # Quadrant 4 (droite)
            tgt_keys = ['31', '32', '33', '34', '35', '36', '37', '38']   # Quadrant 3 (gauche)
            origin_key = '41'

        if origin_key not in self.reference_points:
            logger.warning(f"Point d'origine manquant pour symétrie {arcade}: {origin_key}")
            return

        x0, _, _ = self.reference_points[origin_key]
        x_axis = x0 - offset  # MÊME CALCUL QUE L'ANCIEN

        logger.info(f"🦷 Symétrie {arcade} - Axe: X = {x_axis:.1f} mm (offset: {offset})")

        for src, tgt in zip(base_keys, tgt_keys):
            source_point = None
            
            # Chercher le point source (référence ou généré)
            if src in self.reference_points:
                source_point = self.reference_points[src]
            elif src in self.generated_points:
                source_point = self.generated_points[src]
            
            if source_point:
                x, y, z = source_point
                # FORMULE EXACTE DE L'ANCIEN: x_sym = 2 * x_axis - x
                x_sym = 2 * x_axis - x
                self.generated_points[tgt] = (x_sym, y, z)
                
                logger.debug(f"Symétrie {src} → {tgt}: ({x:.1f}, {y:.1f}) → ({x_sym:.1f}, {y:.1f})")
        
        logger.info(f"✅ Symétrie {arcade} terminée avec axe X={x_axis:.1f}mm")
    
    def _get_midline(self):
        """Calcule l'axe médian """
        xs = [x for (x, _, _) in self.reference_points.values()]
        return np.mean(xs)
    
    def get_all_points(self):
        """Retourne tous les points (référence + générés)"""
        return {**self.reference_points, **self.generated_points}
    
    def clear_generated_points(self):
        """Efface tous les points générés"""
        self.generated_points.clear()
        logger.info("Points générés effacés")
    
    
    
    def set_symmetry_offset(self, offset):
        """Permet de modifier l'offset de symétrie """
        old_offset = self.symmetry_offset
        self.symmetry_offset = float(offset)
        logger.info(f"🔧 Offset de symétrie modifié: {old_offset} → {self.symmetry_offset}")
        
        # Si des points ont déjà été générés, avertir qu'il faut régénérer
        if self.generated_points:
            logger.warning("⚠️ Points déjà générés - Il faut relancer la génération pour appliquer le nouvel offset")
    
    def get_symmetry_offset(self):
        """Retourne l'offset de symétrie actuel"""
        return self.symmetry_offset
    
    
    
    def _generate_tooth_cylinders(self, name, x_mm, y_mm, z_slice, slice_thickness, 
                          ct_viewer, rtstruct_writer):
        """Génère les cylindres pour une dent spécifique """
        
        try:
            ct_slice = ct_viewer.ct_slices[z_slice]
            ct_origin = np.array(ct_slice.ImagePositionPatient, dtype=np.float32)
            ct_spacing = np.array(ct_slice.PixelSpacing, dtype=np.float32)
            ct_rows = ct_slice.Rows
            
            # Paramètres de la dent
            is_maxillary = name.startswith("1") or name.startswith("2")
            
            # Récupérer TOUS les paramètres via les nouvelles méthodes
            h_couronne = self.get_tooth_crown_height(name, ct_viewer)
            h_racine = self.get_tooth_root_height(name, ct_viewer)
            diam = self.get_tooth_diameter(name, ct_viewer)
            angle_deg = self.get_tooth_inclination(name, ct_viewer)
            
            
            
            # Inclinaison facio-linguale = axe Y (antéro-postérieur)
            # En odontologie :
            # - Facio = vers l'avant (vestibulaire) = Y positif
            # - Lingual = vers l'arrière (lingual/palatin) = Y négatif
            
            # Calcul des angles d'inclinaison SELON L'AXE Y
            if is_maxillary:
                # Maxillaires : couronnes vers l'avant (vestibulaire), racines vers l'arrière (palatin)
                theta_couronne = np.radians(-angle_deg)   # Couronne penche vers l'avant (+Y)
                theta_racine = np.radians(angle_deg)    # Racine penche vers l'arrière (-Y)
            else:  # Mandibulaire
                # Mandibulaires : couronnes vers l'avant (vestibulaire), racines vers l'arrière (lingual)
                theta_couronne = np.radians(-angle_deg)   # Couronne penche vers l'avant (+Y)
                theta_racine = np.radians(angle_deg)    # Racine penche vers l'arrière (-Y)
            
            # Rayon unique pour couronne et racine
            radius_mm = diam / 2
            
            print(f"    Angles calculés - Couronne: {np.degrees(theta_couronne):.1f}°, Racine: {np.degrees(theta_racine):.1f}°")
            
            # Directions anatomiques selon l'orientation des coupes Z
            z_positions = [float(ct.ImagePositionPatient[2]) for ct in ct_viewer.ct_slices]
            z_ascending = len(z_positions) > 1 and z_positions[1] > z_positions[0]
            
            if is_maxillary:
                if z_ascending:
                    dir_z_couronne = -1  # Couronnes vers le haut (indices décroissants)
                    dir_z_racine = +1    # Racines vers le bas (indices croissants)
                else:
                    dir_z_couronne = +1  # Couronnes vers le haut (indices croissants)
                    dir_z_racine = -1    # Racines vers le bas (indices décroissants)
            else:  # Mandibulaire
                if z_ascending:
                    dir_z_couronne = +1  # Couronnes vers le haut (indices croissants)
                    dir_z_racine = -1    # Racines vers le bas (indices décroissants)
                else:
                    dir_z_couronne = -1  # Couronnes vers le haut (indices décroissants)
                    dir_z_racine = +1    # Racines vers le bas (indices croissants)
            
            # === GÉNÉRATION COURONNE ===
            couronne_slices = max(1, int(h_couronne / slice_thickness))
            print(f"    Couronne: {couronne_slices} slices, rayon {radius_mm:.1f}mm")
            
            couronne_points = []
            for i_slice in range(couronne_slices):
                z_offset = i_slice * dir_z_couronne
                target_z = z_slice + z_offset
                
                if 0 <= target_z < len(ct_viewer.ct_slices):
                    # Calcul de l'inclinaison SELON L'AXE Y (facio-linguale)
                    height_ratio = i_slice / max(1, couronne_slices - 1)
                    dy_mm = height_ratio * h_couronne * np.tan(theta_couronne)  # CHANGÉ : dx_mm → dy_mm
                    
                    # Centre incliné EN COORDONNÉES PHYSIQUES
                    center_x_mm = x_mm          # X reste constant (pas d'inclinaison latérale)
                    center_y_mm = y_mm + dy_mm  # Y varie selon l'inclinaison facio-linguale
                    
                    print(f"      Couronne slice {i_slice}: center=({center_x_mm:.1f}, {center_y_mm:.1f}), dy_mm={dy_mm:.1f}")
                    
                    # Génération du cercle directement en coordonnées physiques
                    circle_points_physical = self._generate_circle_points_physical(
                        center_x_mm, center_y_mm, radius_mm, 16
                    )
                    
                    couronne_points.extend([
                        [pt[0], pt[1], float(target_z)] for pt in circle_points_physical
                    ])
            
            # === GÉNÉRATION RACINE ===
            racine_slices = max(1, int(h_racine / slice_thickness))
            print(f"    Racine: {racine_slices} slices, rayon {radius_mm:.1f}mm")
            
            racine_points = []
            for i_slice in range(racine_slices):
                z_offset = (i_slice + 1) * dir_z_racine  # +1 pour éviter la superposition
                target_z = z_slice + z_offset
                
                if 0 <= target_z < len(ct_viewer.ct_slices):
                    # Calcul de l'inclinaison SELON L'AXE Y (facio-linguale)
                    height_ratio = i_slice / max(1, racine_slices - 1)
                    dy_mm = height_ratio * h_racine * np.tan(theta_racine)  
                    
                    # Centre incliné EN COORDONNÉES PHYSIQUES
                    center_x_mm = x_mm          # X reste constant (pas d'inclinaison latérale)
                    center_y_mm = y_mm + dy_mm  # Y varie selon l'inclinaison facio-linguale
                    
                    print(f"      Racine slice {i_slice}: center=({center_x_mm:.1f}, {center_y_mm:.1f}), dy_mm={dy_mm:.1f}")
                    
                    # Génération du cercle directement en coordonnées physiques
                    circle_points_physical = self._generate_circle_points_physical(
                        center_x_mm, center_y_mm, radius_mm, 16
                    )
                    
                    racine_points.extend([
                        [pt[0], pt[1], float(target_z)] for pt in circle_points_physical
                    ])
            
            # === CRÉATION DES CONTOURS RTStruct ===
            if couronne_points:
                contour_name_c = f"C_{name}"
                rtstruct_writer.add_roi(contour_name_c, couronne_points, color=[255, 100, 100])
                print(f"    ✅ Couronne {contour_name_c}: {len(couronne_points)} points")
            
            if racine_points:
                contour_name_r = f"R_{name}"
                rtstruct_writer.add_roi(contour_name_r, racine_points, color=[100, 100, 255])
                print(f"    ✅ Racine {contour_name_r}: {len(racine_points)} points")
            
        except Exception as e:
            print(f"  ❌ Erreur génération {name}: {e}")
            import traceback
            traceback.print_exc()
    
    # AJOUT : Méthode pour générer les cercles en coordonnées physiques
    def _generate_circle_points_physical(self, center_x_mm, center_y_mm, radius_mm, num_points):
        """Génère les points d'un cercle directement en coordonnées physiques (mm)"""
        points = []
        
        for i in range(num_points):
            angle = 2 * np.pi * i / num_points
            x_mm = center_x_mm + radius_mm * np.cos(angle)
            y_mm = center_y_mm + radius_mm * np.sin(angle)
            points.append([x_mm, y_mm])
        
        return points
    
    def _generate_circle_points(self, center_x_px, center_y_px, radius_mm, spacing, num_points):
        """Génère les points d'un cercle"""
        points = []
        radius_x_px = radius_mm / spacing[0]
        radius_y_px = radius_mm / spacing[1]
        
        for i in range(num_points):
            angle = 2 * np.pi * i / num_points
            x_px = center_x_px + radius_x_px * np.cos(angle)
            y_px = center_y_px + radius_y_px * np.sin(angle)
            points.append([x_px, y_px])
        
        return points
    
    def generate_3d_cylinders(self, ct_viewer, rtstruct_writer=None):
        """Génère les contours cylindriques 3D pour toutes les dents"""
        
        
        if not rtstruct_writer or not hasattr(rtstruct_writer, "ct_folder"):
            print("❌ DEBUG: RTStruct writer ou dossier CT non fourni")
            logger.error("RTStruct writer ou dossier CT non fourni.")
            return
        
        try:
            print(f"DEBUG: Lecture du dossier {rtstruct_writer.ct_folder}")
            
            # NOUVELLE MÉTHODE : Recherche par tag Modality
            ct_files = []
            from pathlib import Path
            folder = Path(rtstruct_writer.ct_folder)
            
            # Parcourir tous les fichiers .dcm
            for file_path in folder.glob("*.dcm"):
                try:
                    # Lire seulement l'entête pour vérifier la modalité
                    ds = pydicom.dcmread(file_path, force=True, stop_before_pixels=True)
                    
                    # Vérifier si c'est un CT
                    if hasattr(ds, 'Modality') and ds.Modality == 'CT':
                        ct_files.append(file_path.name)
                        
                except Exception as e:
                    # Ignorer les fichiers qui ne peuvent pas être lus
                    continue
            
            
            # Si aucun fichier trouvé par modalité, essayer l'ancienne méthode
            if not ct_files:
                ct_files = [f for f in os.listdir(rtstruct_writer.ct_folder) 
                           if f.startswith("CT") and f.endswith(".dcm")]
            
            if not ct_files:
                print("❌ DEBUG: Aucun fichier CT trouvé dans le dossier")
                return
                
            # Lire le premier fichier CT pour obtenir le SliceThickness
            first_ct_path = os.path.join(rtstruct_writer.ct_folder, ct_files[0])
            first_ct = pydicom.dcmread(first_ct_path, force=True)
            
            # Corriger le TransferSyntaxUID manquant si nécessaire
            if hasattr(first_ct, 'file_meta') and not hasattr(first_ct.file_meta, 'TransferSyntaxUID'):
                first_ct.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
            elif not hasattr(first_ct, 'file_meta'):
                from pydicom.dataset import FileMetaDataset
                first_ct.file_meta = FileMetaDataset()
                first_ct.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
            
            slice_thickness = float(first_ct.SliceThickness)
            logger.info(f"Slice thickness détecté : {slice_thickness} mm")
            
        except Exception as e:
            print(f"❌ DEBUG: Erreur lecture SliceThickness: {e}")
            logger.error(f"Erreur lors de la lecture du SliceThickness : {e}")
            return
        
        
        
        # Combiner points de référence et points générés
        all_points = {**self.reference_points, **self.generated_points}
        
        if not all_points:
            print("❌ DEBUG: PROBLÈME - Aucun point à traiter après combinaison !")
            return
        
        logger.info(f"🔍 Génération 3D:")
        logger.info(f"   Points droite: {len([p for p in all_points.keys() if p.startswith(('1', '4'))])}")
        logger.info(f"   Points gauche: {len([p for p in all_points.keys() if p.startswith(('2', '3'))])}")
        
        # Génération des contours pour chaque dent
        generated_count = 0
        for name, (x_mm, y_mm, z_slice) in all_points.items():
            
            if name not in self.TOOTH_ANATOMY:
                print(f"⚠️ DEBUG: Anatomie inconnue pour {name}")
                logger.warning(f"Anatomie inconnue pour la dent {name}")
                continue
            
            try:
                self._generate_tooth_cylinders(name, x_mm, y_mm, z_slice, 
                                             slice_thickness, ct_viewer, rtstruct_writer)
                generated_count += 1
                
            except Exception as e:
                print(f"❌ DEBUG: Erreur génération {name}: {e}")
                logger.error(f"Erreur génération de la dent {name} : {e}")
                import traceback
                traceback.print_exc()
        
        logger.info(f"✅ Génération des cylindres 3D terminée: {generated_count} dents traitées")
        
       
            
        
    
    def add_roi(self, roi_name, contour_points, color=None):
        """Ajoute un ROI (Region of Interest) aux contours du viewer """
        try:
            
            # Organiser les points par coupe Z
            slice_contours = {}
            for point in contour_points:
                if len(point) >= 3:
                    x_mm, y_mm, z = point[0], point[1], point[2]
                    slice_idx = int(round(z))
                    
                    if slice_idx not in slice_contours:
                        slice_contours[slice_idx] = []
                    
                    # Les points sont en coordonnées PHYSIQUES (mm)
                    slice_contours[slice_idx].append([x_mm, y_mm])
            
            # Convertir les listes en numpy arrays
            numpy_slice_contours = {}
            for slice_idx, points_list in slice_contours.items():
                if len(points_list) >= 3:  # Au moins 3 points pour former un contour
                    numpy_slice_contours[slice_idx] = np.array(points_list, dtype=np.float32)
                else:
                    print(f"  WARNING: Coupe {slice_idx} ignorée: seulement {len(points_list)} points")
            
            # Ajouter aux contours du viewer
            if numpy_slice_contours:
                self.ct_viewer.contours[roi_name] = numpy_slice_contours
                
                # Ajouter la variable de contrôle
                if not hasattr(self.ct_viewer, 'show_contours'):
                    self.ct_viewer.show_contours = {}
                
                var = tk.BooleanVar(value=True)
                self.ct_viewer.show_contours[roi_name] = var
                
                # Ajouter la couleur si fournie
                if color and hasattr(self.ct_viewer, 'structure_colors'):
                    # Convertir RGB en hex si nécessaire
                    if isinstance(color, list) and len(color) >= 3:
                        hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                        self.ct_viewer.structure_colors[roi_name] = hex_color
                
                #  Vérifier le type final
                first_slice = list(numpy_slice_contours.keys())[0]
                first_array = numpy_slice_contours[first_slice]
                #print(f"  ✅ ROI {roi_name} ajouté: {len(numpy_slice_contours)} coupes")
                #print(f"  DEBUG: Type final: {type(first_array)}, Shape: {first_array.shape}")
                #print(f"  DEBUG: Échantillon points: {first_array[:2]}")
                return True
            else:
                print(f"  ❌ ROI {roi_name}: aucune coupe valide")
                return False
                
        except Exception as e:
            print(f"  ❌ Erreur ajout ROI {roi_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    

    
    def update_reference_points(self, new_reference_points):
        """Met à jour les points de référence et efface les points générés"""
        self.reference_points = new_reference_points.copy()
        self.generated_points.clear()
        logger.info(f"🔄 Points de référence mis à jour: {len(self.reference_points)} points")
        logger.info(f"Points générés effacés - Régénération nécessaire")
    
    def get_current_all_points(self):
        """Retourne tous les points actuels (référence + générés) """
        # S'assurer que les dictionnaires ne sont pas None
        reference = self.reference_points if self.reference_points else {}
        generated = self.generated_points if self.generated_points else {}
        return {**reference, **generated}
    