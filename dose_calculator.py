#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculateur de dose pour les structures dentaires
Calcule les doses moyennes dans les contours cylindriques générés
© 2025 Caroline Moreau-Noblet — RT-DENTX — Licence BSD 3-Clause
"""

import numpy as np
import logging
import matplotlib.path as mpath

logger = logging.getLogger(__name__)

class DoseCalculator:
    """Calculateur de dose pour structures dentaires"""
    
    def __init__(self, rtdose_data, ct_slices):
        self.rtdose_data = rtdose_data
        self.ct_slices = ct_slices
        
        # Traitement des données de dose
        self.dose_array = None
        self.dose_spacing = None
        self.dose_origin = None
        self.dose_grid_scaling = 1.0
        
        # Correspondance dose-CT
        self.slice_correspondence = {}
        
        self._initialize_dose_data()
        self._establish_slice_correspondence()
    
    def _initialize_dose_data(self):
        """Initialise et traite les données de dose"""
        if not self.rtdose_data:
            raise ValueError("Aucune donnée RTDose fournie")
        
        try:
            # Array de dose
            self.dose_array = self.rtdose_data.pixel_array.astype(np.float32)
            
            # Appliquer l'échelle de dose
            if hasattr(self.rtdose_data, 'DoseGridScaling'):
                self.dose_grid_scaling = float(self.rtdose_data.DoseGridScaling)
                self.dose_array *= self.dose_grid_scaling
                logger.info(f"Échelle de dose appliquée: {self.dose_grid_scaling}")
            
            # Position et espacement
            if hasattr(self.rtdose_data, 'ImagePositionPatient'):
                self.dose_origin = np.array(self.rtdose_data.ImagePositionPatient, dtype=np.float32)
            else:
                # Fallback sur la première coupe CT
                logger.warning("ImagePositionPatient manquant dans RTDose, utilisation position CT")
                self.dose_origin = np.array(self.ct_slices[0].ImagePositionPatient, dtype=np.float32)
            
            # Espacement des pixels - UTILISER RTDose PixelSpacing
            if (hasattr(self.rtdose_data, 'PixelSpacing') and 
                self.rtdose_data.PixelSpacing is not None):
                pixel_spacing = list(self.rtdose_data.PixelSpacing)
                logger.info(f"PixelSpacing RTDose utilisé: {pixel_spacing}")
            else:
                # Fallback sur CT si RTDose n'a pas de PixelSpacing
                if self.ct_slices and hasattr(self.ct_slices[0], 'PixelSpacing'):
                    pixel_spacing = list(self.ct_slices[0].PixelSpacing)
                    logger.warning("PixelSpacing RTDose manquant, utilisation CT")
                else:
                    pixel_spacing = [1.0, 1.0]  # Fallback 1mm
                    logger.warning("PixelSpacing manquant partout, utilisation 1mm par défaut")
            
            # Espacement entre coupes - UTILISER CT SliceThickness
            slice_spacing = None
            
            # Méthode 1: SliceThickness du CT (PRIORITÉ)
            if self.ct_slices and hasattr(self.ct_slices[0], 'SliceThickness'):
                ct_thickness = self.ct_slices[0].SliceThickness
                if ct_thickness is not None:
                    try:
                        slice_spacing = float(ct_thickness)
                        logger.info(f"SliceThickness pris depuis CT: {slice_spacing} mm")
                    except (ValueError, TypeError):
                        logger.warning("SliceThickness CT invalide")
            
            # Méthode 2: Calculer depuis positions CT consécutives
            if slice_spacing is None and len(self.ct_slices) > 1:
                try:
                    ct_z1 = float(self.ct_slices[0].ImagePositionPatient[2])
                    ct_z2 = float(self.ct_slices[1].ImagePositionPatient[2])
                    slice_spacing = abs(ct_z2 - ct_z1)
                    logger.info(f"Espacement calculé depuis positions CT: {slice_spacing} mm")
                except (ValueError, TypeError, IndexError, AttributeError):
                    logger.warning("Impossible de calculer l'espacement depuis positions CT")
            
            # Méthode 3: GridFrameOffsetVector RTDose (fallback)
            if slice_spacing is None:
                if (hasattr(self.rtdose_data, 'GridFrameOffsetVector') and 
                    self.rtdose_data.GridFrameOffsetVector is not None and 
                    len(self.rtdose_data.GridFrameOffsetVector) > 1):
                    try:
                        offsets = list(self.rtdose_data.GridFrameOffsetVector)
                        slice_spacing = abs(float(offsets[1]) - float(offsets[0]))
                        logger.info(f"Espacement fallback depuis GridFrameOffsetVector: {slice_spacing} mm")
                    except (ValueError, TypeError, IndexError):
                        logger.warning("GridFrameOffsetVector invalide")
            
            # Fallback final
            if slice_spacing is None:
                slice_spacing = 2.0  # Fallback 2mm
                logger.warning("Aucun espacement trouvé, utilisation 2mm par défaut")
            
            self.dose_spacing = np.array([float(pixel_spacing[0]), float(pixel_spacing[1]), slice_spacing])
            
            logger.info(f"Dose array shape: {self.dose_array.shape}")
            logger.info(f"Dose spacing: {self.dose_spacing}")
            logger.info(f"Dose origin: {self.dose_origin}")
            
        except Exception as e:
            logger.error(f"Erreur initialisation données dose: {e}")
            raise
    
    def _establish_slice_correspondence(self):
        """Établit la correspondance entre coupes CT et coupes dose"""
        if not self.ct_slices:
            raise ValueError("Aucune coupe CT fournie")
        
        # Positions Z des coupes CT
        ct_z_positions = []
        for ct_slice in self.ct_slices:
            if hasattr(ct_slice, 'ImagePositionPatient'):
                z_pos = float(ct_slice.ImagePositionPatient[2])
                ct_z_positions.append(z_pos)
            else:
                logger.warning("ImagePositionPatient manquant pour une coupe CT")
        
        # Positions Z des coupes dose
        dose_z_positions = []
        
        if (hasattr(self.rtdose_data, 'GridFrameOffsetVector') and 
            self.rtdose_data.GridFrameOffsetVector is not None):
            # Méthode précise avec GridFrameOffsetVector
            offset_vector = self.rtdose_data.GridFrameOffsetVector
            dose_z_positions = [self.dose_origin[2] + float(offset) for offset in offset_vector]
            logger.info("Positions Z dose calculées depuis GridFrameOffsetVector")
        else:
            # Méthode par espacement uniforme - UTILISER L'ESPACEMENT CT
            logger.info("GridFrameOffsetVector absent, utilisation espacement uniforme")
            for i in range(self.dose_array.shape[0]):
                z_pos = self.dose_origin[2] + i * self.dose_spacing[2]
                dose_z_positions.append(z_pos)
        
        # Log des ranges pour diagnostic
        if ct_z_positions and dose_z_positions:
            logger.info(f"Range Z CT: {min(ct_z_positions):.1f} à {max(ct_z_positions):.1f} mm")
            logger.info(f"Range Z Dose: {min(dose_z_positions):.1f} à {max(dose_z_positions):.1f} mm")
        
        # Établir les correspondances (tolérance 5mm)
        tolerance = 5.0
        
        for ct_idx, ct_z in enumerate(ct_z_positions):
            best_dose_idx = None
            min_diff = float('inf')
            
            for dose_idx, dose_z in enumerate(dose_z_positions):
                diff = abs(ct_z - dose_z)
                if diff < min_diff and diff <= tolerance:
                    min_diff = diff
                    best_dose_idx = dose_idx
            
            if best_dose_idx is not None:
                self.slice_correspondence[ct_idx] = best_dose_idx
                logger.debug(f"CT coupe {ct_idx} (Z={ct_z:.1f}) → Dose coupe {best_dose_idx} (Z={dose_z_positions[best_dose_idx]:.1f}), diff={min_diff:.1f}mm")
        
        logger.info(f"Correspondance établie pour {len(self.slice_correspondence)} coupes sur {len(self.ct_slices)}")
        
        # Vérification de la cohérence
        if len(self.slice_correspondence) < len(self.ct_slices) * 0.5:
            logger.warning("⚠️  Correspondance faible entre CT et RTDose. Vérifiez les positions et orientations.")
        
        if not self.slice_correspondence:
            raise ValueError("Aucune correspondance trouvée entre CT et RTDose. Vérifiez l'alignement des données.")
    
    def calculate_mean_dose_for_structure(self, contour_slices, method='weighted_average'):
        """Calcule la dose moyenne pour une structure multi-coupes """
        if not contour_slices:
            logger.warning("Aucun contour fourni pour le calcul de dose")
            return 0.0
    
        doses_by_slice = []
        weights_by_slice = []
    
        logger.info(f"Calcul dose pour structure avec {len(contour_slices)} coupes")
    
        for ct_slice_idx, contour_points in contour_slices.items():
            try:
                logger.debug(f"Traitement coupe {ct_slice_idx}, type contour: {type(contour_points)}")
                
                # Convertir les listes en numpy arrays
                if isinstance(contour_points, list):
                    try:
                        contour_points = np.array(contour_points, dtype=np.float32)
                        logger.debug(f"Conversion liste→array réussie: {contour_points.shape}")
                    except Exception as e:
                        logger.error(f"Erreur conversion contour coupe {ct_slice_idx}: {e}")
                        continue
                
                # Vérifier le format du contour
                if contour_points.shape[1] != 2:
                    logger.warning(f"Format contour incorrect coupe {ct_slice_idx}: {contour_points.shape}")
                    continue
                
                # Vérifier correspondance coupe dose
                if ct_slice_idx not in self.slice_correspondence:
                    logger.debug(f"Pas de correspondance dose pour coupe CT {ct_slice_idx}")
                    continue
                
                dose_slice_idx = self.slice_correspondence[ct_slice_idx]
                
                # Calculer la dose pour cette coupe
                slice_dose = self._calculate_dose_for_slice(ct_slice_idx, dose_slice_idx, contour_points)
                
                if slice_dose is not None and slice_dose > 0:
                    doses_by_slice.append(slice_dose)
                    
                    # Calculer le poids (aire du contour)
                    if method == 'weighted_average':
                        area = self._calculate_contour_area(contour_points)
                        weights_by_slice.append(area)
                    
                    logger.debug(f"Coupe {ct_slice_idx}: dose={slice_dose:.3f} Gy")
                else:
                    logger.debug(f"Dose nulle ou invalide pour coupe {ct_slice_idx}: {slice_dose}")
    
            except Exception as e:
                logger.error(f"Erreur calcul dose coupe {ct_slice_idx}: {e}")
                import traceback
                traceback.print_exc()
                continue
    
        if not doses_by_slice:
            logger.warning("Aucune dose calculée pour cette structure - toutes les coupes ont échoué")
            return 0.0
    
        # Calcul final selon la méthode
        if method == 'weighted_average' and len(weights_by_slice) == len(doses_by_slice):
            # Moyenne pondérée par l'aire
            total_weighted_dose = sum(d * w for d, w in zip(doses_by_slice, weights_by_slice))
            total_weight = sum(weights_by_slice)
            mean_dose = total_weighted_dose / total_weight if total_weight > 0 else 0.0
        else:
            # Moyenne simple
            mean_dose = np.mean(doses_by_slice)
    
        logger.info(f"Dose moyenne calculée: {mean_dose:.2f} Gy ({len(doses_by_slice)} coupes utilisées)")
        return mean_dose
    
    def _calculate_dose_for_slice(self, ct_slice_idx, dose_slice_idx, contour_points):
        """Calcule la dose pour une coupe spécifique"""
        try:
            # Récupérer la coupe de dose
            if self.dose_array.ndim == 3:
                dose_slice = self.dose_array[dose_slice_idx]
            else:
                dose_slice = self.dose_array
            
            # Créer le masque du contour
            mask = self._create_contour_mask(ct_slice_idx, dose_slice_idx, contour_points, dose_slice.shape)
            
            if not np.any(mask):
                logger.debug(f"Masque vide pour coupe {ct_slice_idx}")
                return None
            
            # Extraire les doses dans le masque
            masked_doses = dose_slice[mask]
            
            # Filtrage des doses nulles (optionnel)
            valid_doses = masked_doses[masked_doses > 0.001]  # Seuil 1 mGy
            
            if len(valid_doses) == 0:
                logger.debug(f"Aucune dose valide dans le masque coupe {ct_slice_idx}")
                return 0.0
            
            mean_dose = np.mean(valid_doses)
            return float(mean_dose)
            
        except Exception as e:
            logger.error(f"Erreur calcul dose coupe {ct_slice_idx}: {e}")
            return None
    
    def _create_contour_mask(self, ct_slice_idx, dose_slice_idx, contour_points, dose_shape):
        """Crée un masque binaire pour le contour sur la grille dose"""
        try:
            # Convertir les coordonnées du contour vers l'espace dose
            dose_coords = self._convert_contour_to_dose_space(ct_slice_idx, contour_points)
            
            if dose_coords is None:
                return np.zeros(dose_shape, dtype=bool)
            
            # Créer le masque avec matplotlib.path
            y_indices, x_indices = np.mgrid[0:dose_shape[0], 0:dose_shape[1]]
            points = np.column_stack((x_indices.ravel(), y_indices.ravel()))
            
            path = mpath.Path(dose_coords)
            mask = path.contains_points(points)
            mask = mask.reshape(dose_shape)
            
            return mask
            
        except Exception as e:
            logger.error(f"Erreur création masque: {e}")
            return np.zeros(dose_shape, dtype=bool)
    
    def _convert_contour_to_dose_space(self, ct_slice_idx, contour_points):
        """Convertit les coordonnées contour CT vers l'espace dose - UTILISE ESPACEMENT RTDose"""
        try:
            if ct_slice_idx >= len(self.ct_slices):
                logger.error(f"Index CT invalide: {ct_slice_idx}")
                return None
            
            ct_slice = self.ct_slices[ct_slice_idx]
            
            # Position et espacement CT pour les coordonnées de départ
            ct_origin = np.array(ct_slice.ImagePositionPatient, dtype=np.float32)
            ct_spacing = np.array([float(ct_slice.PixelSpacing[0]), 
                                  float(ct_slice.PixelSpacing[1])], dtype=np.float32)
            
            # Utiliser l'espacement RTDose pour la conversion finale
            dose_pixel_spacing = np.array([self.dose_spacing[0], self.dose_spacing[1]], dtype=np.float32)
            
            # Convertir vers indices dose
            dose_coords = []
            
            for point in contour_points:
                # Étape 1: Convertir indices CT vers coordonnées spatiales (mm)
                #x_spatial = ct_origin[0] + point[0] * ct_spacing[0]
                #y_spatial = ct_origin[1] + point[1] * ct_spacing[1]
                x_spatial = point[0]
                y_spatial = point[1]

                
                # Étape 2: Convertir coordonnées spatiales vers indices dose (avec espacement RTDose)
                x_dose_idx = (x_spatial - self.dose_origin[0]) / dose_pixel_spacing[0]
                y_dose_idx = (y_spatial - self.dose_origin[1]) / dose_pixel_spacing[1]
                
                dose_coords.append([x_dose_idx, y_dose_idx])
            
            dose_coords_array = np.array(dose_coords, dtype=np.float32)
            
            # Log pour debug (seulement pour la première conversion)
            if ct_slice_idx == list(self.slice_correspondence.keys())[0]:
                logger.debug(f"Conversion contour: CT spacing={ct_spacing}, Dose spacing={dose_pixel_spacing[:2]}")
                logger.debug(f"Premier point: CT=({contour_points[0][0]:.1f},{contour_points[0][1]:.1f}) → Dose=({dose_coords_array[0][0]:.1f},{dose_coords_array[0][1]:.1f})")
            
            return dose_coords_array
            
        except Exception as e:
            logger.error(f"Erreur conversion contour vers dose: {e}")
            return None
    
    def _calculate_contour_area(self, contour_points):
        """Calcule l'aire d'un contour (formule du lacet) - UTILISE ESPACEMENT RTDose"""
        try:
            if len(contour_points) < 3:
                return 0.0
            
            x = contour_points[:, 0]
            y = contour_points[:, 1]
            
            # Formule du lacet (aire en pixels²)
            area_pixels = 0.5 * abs(sum(x[i] * y[i+1] - x[i+1] * y[i] 
                                       for i in range(-1, len(x)-1)))
            
            # Convertir en unités spatiales avec l'espacement RTDose
            pixel_area = self.dose_spacing[0] * self.dose_spacing[1]  # mm²
            spatial_area = area_pixels * pixel_area
            
            return spatial_area
            
        except Exception as e:
            logger.error(f"Erreur calcul aire: {e}")
            return 1.0  # Poids par défaut
    
    def calculate_all_dental_doses(self):
        """Calcule toutes les doses dentaires - MÉTHODE MANQUANTE AJOUTÉE"""
        # Cette méthode doit être appelée avec les contours depuis l'extérieur
        # Car le DoseCalculator n'a pas accès direct aux contours
        raise NotImplementedError("Utilisez calculate_all_dental_doses_from_viewer() depuis les fonctions utilitaires")
    
    def get_dose_statistics(self):
        """Retourne des statistiques sur les données de dose"""
        if self.dose_array is None:
            return {}
        
        stats = {
            'shape': self.dose_array.shape,
            'min_dose': float(np.min(self.dose_array)),
            'max_dose': float(np.max(self.dose_array)),
            'mean_dose': float(np.mean(self.dose_array)),
            'spacing': self.dose_spacing.tolist(),
            'origin': self.dose_origin.tolist(),
            'grid_scaling': self.dose_grid_scaling,
            'slice_correspondences': len(self.slice_correspondence)
        }
        
        return stats
    
    def debug_dose_at_point(self, x_mm, y_mm, z_mm):
        """Debug: retourne la dose à un point donné"""
        try:
            # Convertir coordonnées spatiales vers indices dose
            if self.dose_array.ndim == 3:
                x_idx = int((x_mm - self.dose_origin[0]) / self.dose_spacing[0])
                y_idx = int((y_mm - self.dose_origin[1]) / self.dose_spacing[1])
                z_idx = int((z_mm - self.dose_origin[2]) / self.dose_spacing[2])
                
                if (0 <= x_idx < self.dose_array.shape[2] and 
                    0 <= y_idx < self.dose_array.shape[1] and 
                    0 <= z_idx < self.dose_array.shape[0]):
                    
                    dose = self.dose_array[z_idx, y_idx, x_idx]
                    return {
                        'coordinates': (x_mm, y_mm, z_mm),
                        'indices': (z_idx, y_idx, x_idx),
                        'dose': float(dose)
                    }
            else:
                # Dose 2D
                x_idx = int((x_mm - self.dose_origin[0]) / self.dose_spacing[0])
                y_idx = int((y_mm - self.dose_origin[1]) / self.dose_spacing[1])
                
                if (0 <= x_idx < self.dose_array.shape[1] and 
                    0 <= y_idx < self.dose_array.shape[0]):
                    
                    dose = self.dose_array[y_idx, x_idx]
                    return {
                        'coordinates': (x_mm, y_mm),
                        'indices': (y_idx, x_idx),
                        'dose': float(dose)
                    }
            
            return {'error': 'Point hors de la grille dose'}
            
        except Exception as e:
            return {'error': f'Erreur debug point: {e}'}
        
    
        
        
    
    def diagnose_spacing_parameters(ct_viewer):
        """Diagnostique les paramètres d'espacement CT et RTDose"""
        print("\n" + "="*50)
        print("DIAGNOSTIC ESPACEMENTS CT-RTDose")
        print("="*50)
        
        if not ct_viewer.ct_slices:
            print("❌ Pas de coupes CT")
            return
        
        if not hasattr(ct_viewer, 'rtdose_data') or not ct_viewer.rtdose_data:
            print("❌ Pas de données RTDose")
            return
        
        ct_slice = ct_viewer.ct_slices[0]
        rtdose = ct_viewer.rtdose_data
        
        print(f"\n1. ESPACEMENT CT:")
        
        # PixelSpacing CT
        if hasattr(ct_slice, 'PixelSpacing'):
            ct_pixel_spacing = ct_slice.PixelSpacing
            print(f"   PixelSpacing CT: {ct_pixel_spacing} mm")
        else:
            print("   ❌ PixelSpacing CT manquant")
        
        # SliceThickness CT
        if hasattr(ct_slice, 'SliceThickness'):
            ct_slice_thickness = ct_slice.SliceThickness
            print(f"   SliceThickness CT: {ct_slice_thickness} mm")
        else:
            print("   ❌ SliceThickness CT manquant")
        
        # Espacement calculé entre coupes CT
        if len(ct_viewer.ct_slices) > 1:
            ct_z1 = float(ct_viewer.ct_slices[0].ImagePositionPatient[2])
            ct_z2 = float(ct_viewer.ct_slices[1].ImagePositionPatient[2])
            calculated_spacing = abs(ct_z2 - ct_z1)
            print(f"   Espacement calculé CT: {calculated_spacing:.3f} mm")
        
        print(f"\n2. ESPACEMENT RTDose:")
        
        # PixelSpacing RTDose
        if hasattr(rtdose, 'PixelSpacing'):
            dose_pixel_spacing = rtdose.PixelSpacing
            print(f"   PixelSpacing RTDose: {dose_pixel_spacing} mm")
            print(f"   Tag (0028,0030): ✓")
        else:
            print("   ❌ PixelSpacing RTDose manquant")
            print("   Tag (0028,0030): ✗")
        
        # SliceThickness RTDose
        if hasattr(rtdose, 'SliceThickness'):
            dose_slice_thickness = rtdose.SliceThickness
            print(f"   SliceThickness RTDose: {dose_slice_thickness}")
        else:
            print("   SliceThickness RTDose: None (normal)")
        
        # GridFrameOffsetVector
        if hasattr(rtdose, 'GridFrameOffsetVector'):
            offsets = rtdose.GridFrameOffsetVector
            if offsets and len(offsets) > 1:
                dose_z_spacing = abs(float(offsets[1]) - float(offsets[0]))
                print(f"   GridFrameOffsetVector: {len(offsets)} valeurs")
                print(f"   Espacement Z calculé: {dose_z_spacing:.3f} mm")
            else:
                print("   GridFrameOffsetVector: invalide ou trop court")
        else:
            print("   ❌ GridFrameOffsetVector manquant")
        
        print(f"\n3. CONFIGURATION RECOMMANDÉE:")
        print(f"   Pour la grille XY → PixelSpacing RTDose")
        print(f"   Pour l'espacement Z → SliceThickness CT ou espacement calculé CT")
        
        # Test du calculateur avec cette config
        print(f"\n4. TEST CALCULATEUR:")
        try:
            from dose_calculator import DoseCalculator
            calc = DoseCalculator(rtdose, ct_viewer.ct_slices)
            
            print(f"   ✅ DoseCalculator créé avec succès")
            print(f"   Espacement final utilisé: {calc.dose_spacing}")
            print(f"   Origine: {calc.dose_origin}")
            
            stats = calc.get_dose_statistics()
            print(f"   Correspondances CT-Dose: {stats['slice_correspondences']}")
            
        except Exception as e:
            print(f"   ❌ Erreur création DoseCalculator: {e}")
        
        print("="*50 + "\n")
    
    
def diagnose_spacing_parameters(ct_viewer):
    """Diagnostique les paramètres d'espacement pour le RTDose"""
    logger.info("Diagnostic des paramètres RTDose déclenché")
    # Tu peux afficher ici quelques infos utiles pour debug
    if hasattr(ct_viewer, 'rtdose_data'):
        dose = ct_viewer.rtdose_data
        logger.info(f"PixelSpacing: {getattr(dose, 'PixelSpacing', None)}")
        logger.info(f"GridFrameOffsetVector: {getattr(dose, 'GridFrameOffsetVector', None)}")

def calculate_all_dental_doses_from_viewer(ct_viewer):
    """Fonction utilitaire appelée depuis DoseReportGenerator"""
    if not ct_viewer.rtdose_data or not ct_viewer.ct_slices:
        raise ValueError("RTDose ou CT manquants dans le viewer")
    
    # Créer le calculateur de dose
    calculator = DoseCalculator(ct_viewer.rtdose_data, ct_viewer.ct_slices)
    
    # Obtenir les contours dentaires (C_ et R_)
    dental_contours = {name: contour for name, contour in ct_viewer.contours.items()
                       if name.startswith('C_') or name.startswith('R_')}
    
    doses_couronne = {}
    doses_racine = {}
    
    for name, contour in dental_contours.items():
        dose = calculator.calculate_mean_dose_for_structure(contour)
        tooth = name[2:]  # Supprimer "C_" ou "R_"
        if name.startswith("C_"):
            doses_couronne[tooth] = dose
        elif name.startswith("R_"):
            doses_racine[tooth] = dose
    
    # Calculer les doses complètes en fusionnant les contours
    doses_complete = {}
    all_teeth = set(doses_couronne.keys()) | set(doses_racine.keys())
    
    for tooth in all_teeth:
        # Si on a couronne ET racine, fusionner les contours
        if tooth in doses_couronne and tooth in doses_racine:
            # Récupérer les contours originaux
            crown_contour = ct_viewer.contours.get(f"C_{tooth}", {})
            root_contour = ct_viewer.contours.get(f"R_{tooth}", {})
            
            # Fusionner les contours
            merged_contour = {}
            # Ajouter tous les contours de la couronne
            for slice_idx, points in crown_contour.items():
                merged_contour[slice_idx] = points
            
            # Ajouter les contours de la racine (sans écraser si même slice)
            for slice_idx, points in root_contour.items():
                if slice_idx in merged_contour:
                    # Si la slice contient déjà la couronne, on pourrait fusionner
                    # mais généralement couronne et racine sont sur des slices différentes
                    pass
                else:
                    merged_contour[slice_idx] = points
            
            # Calculer la dose sur le volume fusionné
            doses_complete[tooth] = calculator.calculate_mean_dose_for_structure(merged_contour)
        else:
            # Si on n'a que couronne OU racine
            d_c = doses_couronne.get(tooth, 0)
            d_r = doses_racine.get(tooth, 0)
            doses_complete[tooth] = d_c if d_c > 0 else d_r
    
    return {
        'couronne': doses_couronne,
        'racine': doses_racine,
        'complete': doses_complete
    }



    

    