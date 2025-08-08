#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'écriture de fichiers RTStruct DICOM
Permet d'ajouter de nouvelles structures (contours dentaires) à un RTStruct existant
© 2025 Caroline Moreau-Noblet — RT-DENTX — Licence BSD 3-Clause
"""

import pydicom
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class RTStructWriter:
    """Écriture de fichiers RTStruct avec nouvelles structures"""
    
    def __init__(self, rtstruct_path, ct_folder, ct_slices, structure_set_name="RT_DENTX_Structures"):
        self.rtstruct_path = rtstruct_path
        self.ct_folder = ct_folder
        self.ct_slices = ct_slices
        self.structure_set_name = structure_set_name
        
        # Charger le RTStruct original
        self.rtstruct_ds = pydicom.dcmread(rtstruct_path)
        
        # Nouvelles structures à ajouter
        self.new_structures = {}
        
        # Index pour les nouvelles structures
        self.next_roi_number = self._get_next_roi_number()
        
        logger.info(f"RTStructWriter initialisé - Prochain ROI: {self.next_roi_number}")
    
    def _get_next_roi_number(self):
        """Détermine le prochain numéro ROI disponible"""
        try:
            if hasattr(self.rtstruct_ds, 'StructureSetROISequence'):
                existing_numbers = [int(roi.ROINumber) for roi in self.rtstruct_ds.StructureSetROISequence]
                return max(existing_numbers) + 1 if existing_numbers else 1
            else:
                return 1
        except Exception as e:
            logger.warning(f"Erreur détermination ROI number: {e}")
            return 1000  # Numéro élevé pour éviter les conflits
    
    def add_structure(self, name, contour_slices):
        """Ajoute une nouvelle structure
        
        Args:
            name (str): Nom de la structure (ex: "C_11", "R_18")
            contour_slices (dict): {slice_index: np.array([[x,y], ...]), ...}
        """
        if not contour_slices:
            logger.warning(f"Aucun contour fourni pour {name}")
            return
        
        self.new_structures[name] = contour_slices
        logger.info(f"Structure {name} ajoutée: {len(contour_slices)} coupes")
    
    def save(self, output_path):
        """Sauvegarde le RTStruct avec les nouvelles structures"""
        if not self.new_structures:
            logger.warning("Aucune nouvelle structure à sauvegarder")
            return
        
        try:
            # Créer une copie du RTStruct original
            new_rtstruct = pydicom.dcmread(self.rtstruct_path)
            
            # Mettre à jour les métadonnées
            self._update_metadata(new_rtstruct)
            
            # Ajouter les nouvelles structures
            self._add_structure_definitions(new_rtstruct)
            self._add_roi_contours(new_rtstruct)
            self._add_rt_roi_observations(new_rtstruct)
            
            # Sauvegarder
            new_rtstruct.save_as(output_path)
            logger.info(f"RTStruct sauvegardé: {output_path}")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde RTStruct: {e}")
            raise
    
    def _update_metadata(self, ds):
        """Met à jour les métadonnées du RTStruct"""
        # Nouveau nom du structure set
        ds.StructureSetLabel = self.structure_set_name
        ds.StructureSetName = self.structure_set_name
        ds.StructureSetDescription = f"RT-DENTX - {len(self.new_structures)} structures dentaires ajoutées"
        
        # Mettre à jour les dates
        now = datetime.now()
        ds.StructureSetDate = now.strftime("%Y%m%d")
        ds.StructureSetTime = now.strftime("%H%M%S")
        
        # Nouveau UID pour différencier
        ds.SOPInstanceUID = pydicom.uid.generate_uid()
        
        logger.debug(f"Métadonnées mises à jour: {self.structure_set_name}")
    
    def _add_structure_definitions(self, ds):
        """Ajoute les définitions des nouvelles structures"""
        # S'assurer que la séquence existe
        if not hasattr(ds, 'StructureSetROISequence'):
            ds.StructureSetROISequence = pydicom.Sequence()
        
        for structure_name in self.new_structures.keys():
            # Créer la définition ROI
            roi_def = pydicom.Dataset()
            roi_def.ROINumber = str(self.next_roi_number)
            roi_def.ReferencedFrameOfReferenceUID = ds.ReferencedFrameOfReferenceSequence[0].FrameOfReferenceUID
            roi_def.ROIName = structure_name
            roi_def.ROIDescription = f"Dent {structure_name[2:]} - {self._get_structure_type(structure_name)}"
            roi_def.ROIGenerationAlgorithm = "AUTOMATIC"
            
            # Ajouter à la séquence
            ds.StructureSetROISequence.append(roi_def)
            
            logger.debug(f"ROI {self.next_roi_number} défini: {structure_name}")
            self.next_roi_number += 1
    
    def _add_roi_contours(self, ds):
        """Ajoute les contours géométriques"""
        # S'assurer que la séquence existe
        if not hasattr(ds, 'ROIContourSequence'):
            ds.ROIContourSequence = pydicom.Sequence()
        
        roi_number = self._get_next_roi_number()
        
        for structure_name, contour_slices in self.new_structures.items():
            # Créer la séquence de contours pour cette ROI
            roi_contour = pydicom.Dataset()
            roi_contour.ReferencedROINumber = str(roi_number)
            
            # Couleur selon le type de structure
            roi_contour.ROIDisplayColor = self._get_structure_color(structure_name)
            
            # Séquence des contours
            roi_contour.ContourSequence = pydicom.Sequence()
            
            for slice_idx, contour_points in contour_slices.items():
                if len(contour_points) < 3:
                    continue
                
                # Créer le contour pour cette coupe
                contour = pydicom.Dataset()
                contour.ContourGeometricType = "CLOSED_PLANAR"
                
                # Référence à l'image CT
                contour.ContourImageSequence = pydicom.Sequence()
                image_ref = pydicom.Dataset()
                image_ref.ReferencedSOPClassUID = self.ct_slices[slice_idx].SOPClassUID
                image_ref.ReferencedSOPInstanceUID = self.ct_slices[slice_idx].SOPInstanceUID
                contour.ContourImageSequence.append(image_ref)
                
                # Points du contour (conversion 2D → 3D)
                contour_3d = self._convert_to_3d_contour(slice_idx, contour_points)
                contour.NumberOfContourPoints = len(contour_3d) // 3
                contour.ContourData = [float(x) for x in contour_3d]
                
                roi_contour.ContourSequence.append(contour)
            
            ds.ROIContourSequence.append(roi_contour)
            roi_number += 1
            
            logger.debug(f"Contours ajoutés pour {structure_name}: {len(contour_slices)} coupes")
    
    def _add_rt_roi_observations(self, ds):
        """Ajoute les observations ROI (métadonnées cliniques)"""
        # S'assurer que la séquence existe
        if not hasattr(ds, 'RTROIObservationsSequence'):
            ds.RTROIObservationsSequence = pydicom.Sequence()
        
        roi_number = self._get_next_roi_number()
        
        for structure_name in self.new_structures.keys():
            # Créer l'observation
            roi_obs = pydicom.Dataset()
            roi_obs.ObservationNumber = str(roi_number)
            roi_obs.ReferencedROINumber = str(roi_number)
            roi_obs.ROIObservationLabel = structure_name
            roi_obs.ROIObservationDescription = f"Structure dentaire générée automatiquement"
            roi_obs.RTROIInterpretedType = "ORGAN"
            roi_obs.ROIInterpreter = "RT-DENTX"
            
            ds.RTROIObservationsSequence.append(roi_obs)
            roi_number += 1
        
        logger.debug(f"Observations ROI ajoutées: {len(self.new_structures)}")
    
    def _convert_to_3d_contour(self, slice_idx, contour_2d):
        """Convertit un contour 2D en coordonnées 3D DICOM"""
        try:
            # Position Z de la coupe
            z_position = float(self.ct_slices[slice_idx].ImagePositionPatient[2])
            
            # Convertir chaque point 2D en 3D
            contour_3d = []
            for x, y in contour_2d:
                contour_3d.extend([float(x), float(y), z_position])
            
            return contour_3d
            
        except Exception as e:
            logger.error(f"Erreur conversion 3D coupe {slice_idx}: {e}")
            return []
    
    def _get_structure_type(self, structure_name):
        """Détermine le type de structure (couronne/racine)"""
        if structure_name.startswith("C_"):
            return "Couronne"
        elif structure_name.startswith("R_"):
            return "Racine"
        else:
            return "Inconnue"
    
    def _get_structure_color(self, structure_name):
        """Détermine la couleur d'affichage"""
        if structure_name.startswith("C_"):
            return [0, 255, 0]  # Vert pour les couronnes
        elif structure_name.startswith("R_"):
            return [255, 0, 0]  # Rouge pour les racines
        else:
            return [128, 128, 128]  # Gris par défaut
    
    def get_structure_count(self):
        """Retourne le nombre de nouvelles structures"""
        return len(self.new_structures)
    
    def clear_structures(self):
        """Efface toutes les nouvelles structures"""
        self.new_structures.clear()
        logger.info("Nouvelles structures effacées")
    
    def list_structures(self):
        """Liste toutes les nouvelles structures"""
        if not self.new_structures:
            logger.info("Aucune nouvelle structure")
            return
        
        logger.info(f"Nouvelles structures ({len(self.new_structures)}):")
        for name, contours in self.new_structures.items():
            logger.info(f"  - {name}: {len(contours)} coupes")
    
    def validate_structure(self, structure_name):
        """Valide une structure avant sauvegarde"""
        if structure_name not in self.new_structures:
            return False, "Structure non trouvée"
        
        contours = self.new_structures[structure_name]
        
        if not contours:
            return False, "Aucun contour"
        
        # Vérifier que les contours ont au moins 3 points
        for slice_idx, points in contours.items():
            if len(points) < 3:
                return False, f"Contour invalide coupe {slice_idx}: < 3 points"
        
        return True, "Structure valide"
    
    def get_statistics(self):
        """Retourne des statistiques sur les structures"""
        if not self.new_structures:
            return {"total_structures": 0}
        
        total_contours = sum(len(contours) for contours in self.new_structures.values())
        total_points = sum(
            sum(len(points) for points in contours.values())
            for contours in self.new_structures.values()
        )
        
        structure_types = {}
        for name in self.new_structures.keys():
            struct_type = self._get_structure_type(name)
            structure_types[struct_type] = structure_types.get(struct_type, 0) + 1
        
        return {
            "total_structures": len(self.new_structures),
            "total_contours": total_contours,
            "total_points": total_points,
            "structure_types": structure_types,
            "next_roi_number": self.next_roi_number
        }


# Fonctions utilitaires
def create_empty_rtstruct(ct_slices, output_path, structure_set_name="RT_DENTX"):
    """Crée un RTStruct vide à partir des coupes CT"""
    try:
        # Créer un nouveau dataset RTStruct
        ds = pydicom.Dataset()
        
        # Métadonnées obligatoires
        ds.SpecificCharacterSet = 'ISO_IR 100'
        ds.SOPClassUID = '1.2.840.10008.5.1.4.1.1.481.3'  # RT Structure Set Storage
        ds.SOPInstanceUID = pydicom.uid.generate_uid()
        ds.StudyInstanceUID = ct_slices[0].StudyInstanceUID
        ds.SeriesInstanceUID = pydicom.uid.generate_uid()
        ds.StudyID = getattr(ct_slices[0], 'StudyID', '1')
        ds.SeriesNumber = '999'
        ds.StructureSetLabel = structure_set_name
        ds.StructureSetName = structure_set_name
        
        # Dates
        now = datetime.now()
        ds.StudyDate = now.strftime("%Y%m%d")
        ds.StudyTime = now.strftime("%H%M%S")
        ds.StructureSetDate = ds.StudyDate
        ds.StructureSetTime = ds.StudyTime
        
        # Patient info depuis CT
        ds.PatientName = getattr(ct_slices[0], 'PatientName', 'RT_DENTX')
        ds.PatientID = getattr(ct_slices[0], 'PatientID', 'DENTX001')
        ds.PatientBirthDate = getattr(ct_slices[0], 'PatientBirthDate', '')
        ds.PatientSex = getattr(ct_slices[0], 'PatientSex', '')
        
        # Référence au frame of reference
        ds.ReferencedFrameOfReferenceSequence = pydicom.Sequence()
        frame_ref = pydicom.Dataset()
        frame_ref.FrameOfReferenceUID = ct_slices[0].FrameOfReferenceUID
        
        # Référence aux études RT
        frame_ref.RTReferencedStudySequence = pydicom.Sequence()
        study_ref = pydicom.Dataset()
        study_ref.ReferencedSOPClassUID = '1.2.840.10008.3.1.2.3.1'
        study_ref.ReferencedSOPInstanceUID = ct_slices[0].StudyInstanceUID
        
        # Référence aux séries CT
        study_ref.RTReferencedSeriesSequence = pydicom.Sequence()
        series_ref = pydicom.Dataset()
        series_ref.SeriesInstanceUID = ct_slices[0].SeriesInstanceUID
        
        # Références aux images CT
        series_ref.ContourImageSequence = pydicom.Sequence()
        for ct_slice in ct_slices:
            image_ref = pydicom.Dataset()
            image_ref.ReferencedSOPClassUID = ct_slice.SOPClassUID
            image_ref.ReferencedSOPInstanceUID = ct_slice.SOPInstanceUID
            series_ref.ContourImageSequence.append(image_ref)
        
        study_ref.RTReferencedSeriesSequence.append(series_ref)
        frame_ref.RTReferencedStudySequence.append(study_ref)
        ds.ReferencedFrameOfReferenceSequence.append(frame_ref)
        
        # Séquences vides pour les structures
        ds.StructureSetROISequence = pydicom.Sequence()
        ds.ROIContourSequence = pydicom.Sequence()
        ds.RTROIObservationsSequence = pydicom.Sequence()
        
        # Métadonnées fichier
        ds.file_meta = pydicom.dataset.FileMetaDataset()
        ds.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
        ds.file_meta.MediaStorageSOPClassUID = ds.SOPClassUID
        ds.file_meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID
        ds.file_meta.ImplementationClassUID = pydicom.uid.generate_uid()
        ds.file_meta.ImplementationVersionName = 'RT_DENTX_1.0'
        
        # Sauvegarder
        ds.save_as(output_path)
        logger.info(f"RTStruct vide créé: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Erreur création RTStruct vide: {e}")
        raise


def merge_rtstructs(original_path, new_structures_path, output_path):
    """Fusionne deux fichiers RTStruct"""
    try:
        # Charger les deux RTStruct
        original_ds = pydicom.dcmread(original_path)
        new_ds = pydicom.dcmread(new_structures_path)
        
        # Créer le RTStruct fusionné basé sur l'original
        merged_ds = pydicom.dcmread(original_path)
        
        # Déterminer le prochain ROI number
        next_roi = 1
        if hasattr(merged_ds, 'StructureSetROISequence'):
            existing_numbers = [int(roi.ROINumber) for roi in merged_ds.StructureSetROISequence]
            next_roi = max(existing_numbers) + 1 if existing_numbers else 1
        
        # Ajouter les nouvelles structures
        if hasattr(new_ds, 'StructureSetROISequence'):
            for roi in new_ds.StructureSetROISequence:
                roi.ROINumber = str(next_roi)
                merged_ds.StructureSetROISequence.append(roi)
                next_roi += 1
        
        # Ajouter les nouveaux contours
        if hasattr(new_ds, 'ROIContourSequence'):
            for contour in new_ds.ROIContourSequence:
                merged_ds.ROIContourSequence.append(contour)
        
        # Ajouter les nouvelles observations
        if hasattr(new_ds, 'RTROIObservationsSequence'):
            for obs in new_ds.RTROIObservationsSequence:
                merged_ds.RTROIObservationsSequence.append(obs)
        
        # Mettre à jour les métadonnées
        merged_ds.StructureSetLabel = f"{original_ds.StructureSetLabel}_MERGED"
        merged_ds.SOPInstanceUID = pydicom.uid.generate_uid()
        
        # Sauvegarder
        merged_ds.save_as(output_path)
        logger.info(f"RTStruct fusionné sauvegardé: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Erreur fusion RTStruct: {e}")
        raise


