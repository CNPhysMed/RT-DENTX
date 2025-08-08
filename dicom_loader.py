#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de chargement DICOM
Gestion du chargement CT, RTStruct et RTDose
© 2025 Caroline Moreau-Noblet — RT-DENTX — Licence BSD 3-Clause
"""

import pydicom
from pydicom.dataset import FileMetaDataset
import numpy as np
from pathlib import Path
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class DicomLoader:
    """Chargeur DICOM inspiré de dicompyler-core"""
    
    @staticmethod
    def _find_dicom_files_by_modality(folder_path, modality, max_files=None):
        """
        Recherche les fichiers DICOM d'une modalité spécifique
        
        Args:
            folder_path: Chemin du dossier
            modality: Modalité recherchée (CT, RTSTRUCT, RTDOSE, RTPLAN)
            max_files: Nombre maximum de fichiers attendus (None = illimité)
        
        Returns:
            list: Liste des datasets DICOM correspondants
        """
        found_files = []
        folder = Path(folder_path)
        
        # Parcourir tous les fichiers .dcm du dossier
        for file_path in folder.glob("*.dcm"):
            try:
                # Lire l'entête DICOM avec force=True pour gérer les fichiers problématiques
                ds = pydicom.dcmread(file_path, force=True, stop_before_pixels=True)
                
                # Vérifier le tag Modality
                if hasattr(ds, 'Modality') and ds.Modality == modality:
                    # Pour les modalités autres que CT, lire le fichier complet
                    if modality != 'CT':
                        ds = pydicom.dcmread(file_path, force=True)
                    else:
                        # Pour CT, on relira plus tard avec les pixels
                        ds = pydicom.dcmread(file_path, force=True)
                    
                    # Corriger le TransferSyntaxUID manquant si nécessaire
                    if not hasattr(ds, 'file_meta'):
                        # Créer un file_meta minimal si absent
                        ds.file_meta = FileMetaDataset()
                        ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
                        logger.debug(f"FileMetaDataset créé pour {file_path.name}")
                    elif not hasattr(ds.file_meta, 'TransferSyntaxUID'):
                        # Ajouter TransferSyntaxUID si manquant
                        ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
                        logger.debug(f"TransferSyntaxUID ajouté pour {file_path.name}")
                    
                    found_files.append(ds)
                    logger.debug(f"Trouvé {modality}: {file_path.name}")
                    
                    # Si on a trouvé le nombre attendu de fichiers, arrêter
                    if max_files and len(found_files) >= max_files:
                        break
                        
            except Exception as e:
                logger.warning(f"Erreur lecture {file_path.name}: {e}")
                continue
        
        return found_files
    
    @staticmethod
    def load_ct_series(folder_path):
        """Charge une série CT depuis un dossier"""
        logger.info(f"Recherche des fichiers CT dans {folder_path}")
        
        # Rechercher tous les fichiers CT par tag Modality
        ct_files = DicomLoader._find_dicom_files_by_modality(folder_path, 'CT')
        
        if not ct_files:
            # Fallback : essayer l'ancienne méthode par nom de fichier
            logger.warning("Aucun fichier avec Modality='CT' trouvé, essai méthode par nom...")
            ct_files = []
            folder = Path(folder_path)
            
            for file_path in folder.glob("CT*.dcm"):
                try:
                    ds = pydicom.dcmread(file_path, force=True)
                    
                    # Corriger le TransferSyntaxUID manquant si nécessaire
                    if not hasattr(ds, 'file_meta'):
                        from pydicom.dataset import FileMetaDataset
                        ds.file_meta = FileMetaDataset()
                        ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
                        logger.debug(f"FileMetaDataset créé pour {file_path.name}")
                    elif not hasattr(ds.file_meta, 'TransferSyntaxUID'):
                        ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
                        logger.debug(f"TransferSyntaxUID ajouté pour {file_path.name}")
                    
                    ct_files.append(ds)
                    logger.debug(f"Chargé par nom: {file_path.name}")
                except Exception as e:
                    logger.warning(f"Erreur lecture {file_path.name}: {e}")
        
        if not ct_files:
            raise ValueError("Aucun fichier CT trouvé dans le dossier")
        
        # Trier par position Z
        try:
            ct_files.sort(key=lambda x: float(x.ImagePositionPatient[2]))
        except:
            logger.warning("Tri par ImagePositionPatient impossible, utilisation SliceLocation")
            try:
                ct_files.sort(key=lambda x: float(getattr(x, 'SliceLocation', 0)))
            except:
                logger.warning("Tri par SliceLocation impossible, ordre par défaut")
        
        logger.info(f"Série CT chargée: {len(ct_files)} coupes")
        return ct_files
    
    @staticmethod
    def load_rtstruct(folder_path, ct_slices):
        """Charge les contours RTStruct"""
        contours = defaultdict(dict)
        logger.info(f"Recherche du fichier RTStruct dans {folder_path}")
        
        # Rechercher le fichier RTStruct par tag Modality (1 seul fichier attendu)
        rtstruct_files = DicomLoader._find_dicom_files_by_modality(folder_path, 'RTSTRUCT', max_files=1)
        
        if not rtstruct_files:
            # Fallback : essayer l'ancienne méthode
            logger.warning("Aucun fichier avec Modality='RTSTRUCT' trouvé, essai méthode par nom...")
            folder = Path(folder_path)
            
            for file_path in folder.glob("RS*.dcm"):
                try:
                    ds = pydicom.dcmread(file_path, force=True)
                    
                    # Corriger le TransferSyntaxUID manquant si nécessaire
                    if not hasattr(ds, 'file_meta'):
                        from pydicom.dataset import FileMetaDataset
                        ds.file_meta = FileMetaDataset()
                        ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
                        logger.debug(f"FileMetaDataset créé pour {file_path.name}")
                    elif not hasattr(ds.file_meta, 'TransferSyntaxUID'):
                        ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
                        logger.debug(f"TransferSyntaxUID ajouté pour {file_path.name}")
                    
                    if hasattr(ds, 'Modality') and ds.Modality == 'RTSTRUCT':
                        rtstruct_files = [ds]
                        break
                except Exception as e:
                    logger.warning(f"Erreur lecture RTStruct {file_path.name}: {e}")
        
        if not rtstruct_files:
            logger.info("Aucun fichier RTStruct trouvé")
            return contours
        
        rs_file = rtstruct_files[0]
        
        # Extraire les noms des ROI
        roi_names = {}
        try:
            for roi in rs_file.StructureSetROISequence:
                roi_number = roi.ROINumber
                roi_name = roi.ROIName
                roi_names[roi_number] = roi_name
                logger.debug(f"ROI {roi_number}: {roi_name}")
        except Exception as e:
            logger.error(f"Erreur extraction ROI names: {e}")
            return contours
        
        # Extraire les contours
        z_positions = [float(s.ImagePositionPatient[2]) for s in ct_slices]
        z_tolerance = 2.0  # mm
        
        try:
            for roi_contour in rs_file.ROIContourSequence:
                roi_number = roi_contour.ReferencedROINumber
                roi_name = roi_names.get(roi_number, f"ROI_{roi_number}")
                
                if hasattr(roi_contour, 'ContourSequence'):
                    for contour in roi_contour.ContourSequence:
                        if contour.ContourGeometricType == 'CLOSED_PLANAR':
                            # Extraire les coordonnées
                            coords = np.array(contour.ContourData).reshape(-1, 3)
                            z_contour = coords[0, 2]  # Position Z du contour
                            
                            # Trouver la coupe CT correspondante
                            z_diffs = [abs(z_pos - z_contour) for z_pos in z_positions]
                            min_diff_idx = np.argmin(z_diffs)
                            
                            if z_diffs[min_diff_idx] <= z_tolerance:
                                # Coordonnées en mm dans le plan de coupe
                                xy_coords = coords[:, :2]
                                contours[roi_name][min_diff_idx] = xy_coords
                                
                logger.debug(f"ROI {roi_name}: {len(contours[roi_name])} contours")
        
        except Exception as e:
            logger.error(f"Erreur extraction contours: {e}")
        
        logger.info(f"RTStruct chargé: {len(contours)} structures")
        return contours
    
    @staticmethod
    def load_rtdose(folder_path):
        """Charge les données de dose"""
        logger.info(f"Recherche du fichier RTDose dans {folder_path}")
        
        # Rechercher le fichier RTDose par tag Modality (1 seul fichier attendu)
        rtdose_files = DicomLoader._find_dicom_files_by_modality(folder_path, 'RTDOSE', max_files=1)
        
        if not rtdose_files:
            # Fallback : essayer l'ancienne méthode
            logger.warning("Aucun fichier avec Modality='RTDOSE' trouvé, essai méthode par nom...")
            folder = Path(folder_path)
            
            for file_path in folder.glob("RD*.dcm"):
                try:
                    ds = pydicom.dcmread(file_path, force=True)
                    
                    # Corriger le TransferSyntaxUID manquant si nécessaire
                    if not hasattr(ds, 'file_meta'):
                        from pydicom.dataset import FileMetaDataset
                        ds.file_meta = FileMetaDataset()
                        ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
                        logger.debug(f"FileMetaDataset créé pour {file_path.name}")
                    elif not hasattr(ds.file_meta, 'TransferSyntaxUID'):
                        ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
                        logger.debug(f"TransferSyntaxUID ajouté pour {file_path.name}")
                    
                    if hasattr(ds, 'Modality') and ds.Modality == 'RTDOSE':
                        rtdose_files = [ds]
                        break
                except Exception as e:
                    logger.warning(f"Erreur lecture RTDose {file_path.name}: {e}")
        
        if not rtdose_files:
            logger.info("Aucun fichier RTDose trouvé")
            return None
        
        rtdose_ds = rtdose_files[0]
        logger.info(f"RTDose chargé: Modality={rtdose_ds.Modality}")
        
        # Log des informations de dose
        DicomLoader._log_dose_info(rtdose_ds)
        
        return rtdose_ds
    
    @staticmethod
    def _log_dose_info(rtdose_ds):
        """Log les informations de dose"""
        logger.info("=== Informations RTDose ===")
        
        # Dimensions de la grille
        logger.info(f"Dimensions grille: {getattr(rtdose_ds, 'Rows', 'N/A')} x {getattr(rtdose_ds, 'Columns', 'N/A')}")
        
        # Position et orientation
        logger.info(f"ImagePositionPatient: {getattr(rtdose_ds, 'ImagePositionPatient', 'MANQUANT')}")
        logger.info(f"ImageOrientationPatient: {getattr(rtdose_ds, 'ImageOrientationPatient', 'MANQUANT')}")
        logger.info(f"GridFrameOffsetVector: {len(getattr(rtdose_ds, 'GridFrameOffsetVector', []))} slices")
        
        # Échelle de dose
        logger.info(f"DoseGridScaling: {getattr(rtdose_ds, 'DoseGridScaling', 'MANQUANT')}")
        logger.info(f"DoseUnits: {getattr(rtdose_ds, 'DoseUnits', 'MANQUANT')}")
        logger.info(f"DoseType: {getattr(rtdose_ds, 'DoseType', 'MANQUANT')}")
        
        # Statistiques de dose
        if hasattr(rtdose_ds, 'pixel_array'):
            try:
                dose_array = rtdose_ds.pixel_array.astype(np.float32)
                if hasattr(rtdose_ds, 'DoseGridScaling'):
                    dose_array *= float(rtdose_ds.DoseGridScaling)
                
                logger.info(f"Dose min: {np.min(dose_array):.3f}")
                logger.info(f"Dose max: {np.max(dose_array):.3f}")
                logger.info(f"Dose moyenne: {np.mean(dose_array):.3f}")
                
            except Exception as e:
                logger.warning(f"Erreur calcul statistiques dose: {e}")
        
        logger.info("==========================")
    
    @staticmethod
    def validate_dicom_folder(folder_path):
        """Valide qu'un dossier contient des fichiers DICOM valides"""
        folder = Path(folder_path)
        if not folder.exists():
            raise ValueError(f"Le dossier {folder_path} n'existe pas")
        
        dicom_files = list(folder.glob("*.dcm"))
        if not dicom_files:
            raise ValueError(f"Aucun fichier .dcm trouvé dans {folder_path}")
        
        valid_files = 0
        modalities_found = set()
        
        for file_path in dicom_files[:10]:  # Tester les 10 premiers
            try:
                ds = pydicom.dcmread(file_path, force=True, stop_before_pixels=True)
                if hasattr(ds, 'Modality'):
                    valid_files += 1
                    modalities_found.add(ds.Modality)
            except:
                continue
        
        if valid_files == 0:
            raise ValueError(f"Aucun fichier DICOM valide trouvé dans {folder_path}")
        
        logger.info(f"Dossier DICOM valide: {folder_path}")
        logger.info(f"Modalités trouvées: {', '.join(sorted(modalities_found))}")
        return True
    
    @staticmethod
    def get_series_info(folder_path):
        """Retourne des informations sur les séries DICOM dans le dossier"""
        folder = Path(folder_path)
        series_info = {
            'CT': [],
            'RTSTRUCT': [],
            'RTDOSE': [],
            'RTPLAN': [],
            'OTHER': []
        }
        
        for file_path in folder.glob("*.dcm"):
            try:
                ds = pydicom.dcmread(file_path, force=True, stop_before_pixels=True)
                modality = getattr(ds, 'Modality', 'UNKNOWN')
                
                file_info = {
                    'filename': file_path.name,
                    'modality': modality,
                    'series_uid': getattr(ds, 'SeriesInstanceUID', 'N/A'),
                    'series_description': getattr(ds, 'SeriesDescription', 'N/A')
                }
                
                if modality == 'CT':
                    series_info['CT'].append(file_info)
                elif modality == 'RTSTRUCT':
                    series_info['RTSTRUCT'].append(file_info)
                elif modality == 'RTDOSE':
                    series_info['RTDOSE'].append(file_info)
                elif modality == 'RTPLAN':
                    series_info['RTPLAN'].append(file_info)
                else:
                    series_info['OTHER'].append(file_info)
                    
            except Exception as e:
                logger.warning(f"Erreur lecture info {file_path.name}: {e}")
        
        # Log du résumé
        logger.info("=== Résumé des séries DICOM ===")
        for modality, files in series_info.items():
            if files:
                logger.info(f"{modality}: {len(files)} fichier(s)")
        
        return series_info
    
    @staticmethod
    def load_dicom_file(file_path):
        """Charge un fichier DICOM individuel avec gestion d'erreur"""
        try:
            ds = pydicom.dcmread(file_path, force=True)
            
            # Corriger le TransferSyntaxUID manquant si nécessaire
            if not hasattr(ds, 'file_meta'):
                from pydicom.dataset import FileMetaDataset
                ds.file_meta = FileMetaDataset()
                ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
                logger.debug(f"FileMetaDataset créé pour {file_path}")
            elif not hasattr(ds.file_meta, 'TransferSyntaxUID'):
                ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
                logger.debug(f"TransferSyntaxUID ajouté pour {file_path}")
            
            logger.debug(f"Fichier DICOM chargé: {file_path}")
            return ds
        except Exception as e:
            logger.error(f"Erreur chargement {file_path}: {e}")
            return None
    
    @staticmethod
    def extract_patient_info(ct_slices):
        """Extrait les informations patient des coupes CT"""
        if not ct_slices:
            return {}
        
        ds = ct_slices[0]
        patient_info = {
            'name': getattr(ds, 'PatientName', 'Inconnu'),
            'id': getattr(ds, 'PatientID', 'Inconnu'),
            'birth_date': getattr(ds, 'PatientBirthDate', 'Inconnue'),
            'sex': getattr(ds, 'PatientSex', 'Inconnu'),
            'study_date': getattr(ds, 'StudyDate', 'Inconnue'),
            'study_description': getattr(ds, 'StudyDescription', 'Inconnue'),
            'series_description': getattr(ds, 'SeriesDescription', 'Inconnue'),
            'institution': getattr(ds, 'InstitutionName', 'Inconnue'),
            'manufacturer': getattr(ds, 'Manufacturer', 'Inconnu'),
            'model': getattr(ds, 'ManufacturerModelName', 'Inconnu')
        }
        
        return patient_info