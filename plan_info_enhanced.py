# -*- coding: utf-8 -*-
"""
Module pour extraire et formater les informations du plan de traitement RT
© 2025 Caroline Moreau-Noblet — RT-DENTX — Licence BSD 3-Clause
"""

import os
import pydicom
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def get_plan_info(ct_folder, rtdose_dcm):
    """
    Récupère les informations du RTPlan si disponible
    
    Args:
        ct_folder (str): Dossier contenant les fichiers DICOM
        rtdose_dcm: Dataset DICOM du RTDose
    
    Returns:
        dict: Informations du plan ou None si non trouvé
    """
    try:
        rtplan_files = []
        folder = Path(ct_folder)
        
        # Recherche principale par tag Modality (méthode fiable)
        logger.info("Recherche des fichiers RTPLAN par tag Modality...")
        
        for file_path in folder.glob("*.dcm"):
            try:
                # force=True pour gérer les fichiers DICOM problématiques
                ds = pydicom.dcmread(file_path, force=True, stop_before_pixels=True)
                
                # Vérifier le tag Modality
                if hasattr(ds, 'Modality') and ds.Modality == 'RTPLAN':
                    rtplan_files.append({
                        'path': str(file_path),
                        'filename': file_path.name,
                        'uid': getattr(ds, 'SOPInstanceUID', ''),
                        'label': getattr(ds, 'RTPlanLabel', 'Sans nom')
                    })
                    logger.debug(f"RTPLAN trouvé: {file_path.name}")
                    
                # Vérification alternative par SOPClassUID
                # UID standard pour RT Plan : 1.2.840.10008.5.1.4.1.1.481.5
                elif (hasattr(ds, 'SOPClassUID') and 
                      ds.SOPClassUID == "1.2.840.10008.5.1.4.1.1.481.5"):
                    rtplan_files.append({
                        'path': str(file_path),
                        'filename': file_path.name,
                        'uid': getattr(ds, 'SOPInstanceUID', ''),
                        'label': getattr(ds, 'RTPlanLabel', 'Sans nom')
                    })
                    logger.debug(f"RTPLAN trouvé via SOPClassUID: {file_path.name}")
                    
            except Exception as e:
                logger.debug(f"Erreur lecture {file_path.name}: {e}")
                continue
        
        if not rtplan_files:
            logger.info("Aucun fichier RTPLAN trouvé")
            return None
        
        logger.info(f"{len(rtplan_files)} fichier(s) RTPLAN trouvé(s)")
        
        # Récupérer l'UID référencé dans le RTDose
        rtdose_referenced_uid = None
        try:
            if hasattr(rtdose_dcm, 'ReferencedRTPlanSequence') and rtdose_dcm.ReferencedRTPlanSequence:
                rtdose_referenced_uid = rtdose_dcm.ReferencedRTPlanSequence[0].ReferencedSOPInstanceUID
                logger.info(f"RTDose référence le plan UID: {rtdose_referenced_uid}")
        except Exception as e:
            logger.debug(f"Erreur lecture UID RTDose: {e}")
        
        # Chercher le plan correspondant à l'UID référencé
        selected_plan = None
        
        # 1. Priorité au plan avec UID correspondant
        if rtdose_referenced_uid:
            for plan in rtplan_files:
                if plan['uid'] == rtdose_referenced_uid:
                    selected_plan = plan
                    logger.info(f"Plan correspondant trouvé: {plan['filename']}")
                    break
        
        # 2. Si aucun plan avec UID correspondant, prendre le premier
        if not selected_plan and rtplan_files:
            selected_plan = rtplan_files[0]
            logger.warning(f"Aucun plan avec UID correspondant, utilisation de: {selected_plan['filename']}")
        
        # Extraire les informations détaillées du plan sélectionné
        if selected_plan:
            try:
                rtplan_dcm = pydicom.dcmread(selected_plan['path'], force=True, stop_before_pixels=True)
                uid_verified = (selected_plan['uid'] == rtdose_referenced_uid) if rtdose_referenced_uid else False
                plan_info = _extract_plan_info(rtplan_dcm, selected_plan['path'], uid_verified)
                return plan_info
                
            except Exception as e:
                logger.error(f"Erreur extraction infos plan: {e}")
                return None
        
        return None
        
    except Exception as e:
        logger.error(f"Erreur get_plan_info: {e}")
        return None

def _extract_plan_info(rtplan_dcm, rtplan_file, uid_verified):
    """Extrait les informations d'un dataset RTPlan"""
    plan_info = {
        "plan_name": str(getattr(rtplan_dcm, "RTPlanLabel", "Plan non nommé")),
        "plan_id": str(getattr(rtplan_dcm, "RTPlanName", "")),
        "plan_date": str(getattr(rtplan_dcm, "RTPlanDate", "")),
        "plan_time": str(getattr(rtplan_dcm, "RTPlanTime", "")),
        "plan_description": str(getattr(rtplan_dcm, "RTPlanDescription", "")),
        "plan_file": os.path.basename(rtplan_file),
        "uid_verified": uid_verified,
        "modality": str(getattr(rtplan_dcm, "Modality", "UNKNOWN"))
    }
    
    # Récupérer dose prescrite et nombre de fractions
    try:
        if hasattr(rtplan_dcm, 'FractionGroupSequence') and rtplan_dcm.FractionGroupSequence:
            fraction_group = rtplan_dcm.FractionGroupSequence[0]
            
            # Nombre de fractions
            if hasattr(fraction_group, 'NumberOfFractionsPlanned'):
                plan_info["fractions"] = int(fraction_group.NumberOfFractionsPlanned)
            
            # Dose prescrite
            if hasattr(rtplan_dcm, 'DoseReferenceSequence') and rtplan_dcm.DoseReferenceSequence:
                for dose_ref in rtplan_dcm.DoseReferenceSequence:
                    if hasattr(dose_ref, 'TargetPrescriptionDose'):
                        plan_info["prescribed_dose"] = float(dose_ref.TargetPrescriptionDose)
                        break
                    elif hasattr(dose_ref, 'DoseReferencePointDose'):
                        # Fallback sur DoseReferencePointDose
                        plan_info["prescribed_dose"] = float(dose_ref.DoseReferencePointDose)
                        break
            
            # Informations sur les faisceaux
            if (hasattr(fraction_group, 'ReferencedBeamSequence') and 
                hasattr(rtplan_dcm, 'BeamSequence')):
                beam_count = len(rtplan_dcm.BeamSequence)
                plan_info["beam_count"] = beam_count
                
    except Exception as e:
        logger.debug(f"Erreur extraction dose/fractions: {e}")
    
    return plan_info

def format_plan_info_for_report(plan_info):
    """
    Formate les informations du plan pour le rapport - SANS nombre de faisceaux
    """
    if not plan_info:
        return "Plan de traitement non identifié"
    
    # Formatage de la date et heure
    date_str = ""
    if plan_info.get("plan_date"):
        try:
            date_raw = plan_info["plan_date"]
            if len(date_raw) == 8:  # Format YYYYMMDD
                date_str = f"{date_raw[6:8]}/{date_raw[4:6]}/{date_raw[0:4]}"
            else:
                date_str = date_raw
        except:
            date_str = plan_info["plan_date"]
    
    time_str = ""
    if plan_info.get("plan_time"):
        try:
            time_raw = plan_info["plan_time"]
            if len(time_raw) >= 6:  # Format HHMMSS
                time_str = f"{time_raw[0:2]}:{time_raw[2:4]}:{time_raw[4:6]}"
            else:
                time_str = time_raw
        except:
            time_str = plan_info["plan_time"]
    
    # Construction du texte principal
    plan_text = f"{plan_info['plan_name']}"
    
    if plan_info.get("plan_id") and plan_info["plan_id"] != plan_info["plan_name"]:
        plan_text += f" (ID: {plan_info['plan_id']})"
    
    if date_str:
        plan_text += f" - {date_str}"
        if time_str:
            plan_text += f" {time_str}"
    
    # Ajouter dose prescrite et fractions sur une nouvelle ligne
    dose_line_parts = []
    if plan_info.get("prescribed_dose"):
        dose_line_parts.append(f"Dose prescrite: {plan_info['prescribed_dose']:.1f} Gy")
    
    if plan_info.get("fractions"):
        dose_line_parts.append(f"en {plan_info['fractions']} fractions")
    
    if dose_line_parts:
        plan_text += "\n" + " ".join(dose_line_parts)
    
    # SUPPRIMÉ: Informations sur les faisceaux
    # Ne pas ajouter le nombre de faisceaux dans le rapport
    
    # Ajouter informations supplémentaires si disponibles (SANS faisceaux)
    additional_info = []
    
    if not plan_info.get("uid_verified", True):
        additional_info.append("UID non vérifié")
    
    if additional_info:
        plan_text += f" ({', '.join(additional_info)})"
    
    return plan_text

def get_plan_summary_stats(plan_info):
    """
    Retourne des statistiques résumées du plan
    
    Args:
        plan_info (dict): Informations du plan
        
    Returns:
        dict: Statistiques du plan
    """
    if not plan_info:
        return {}
    
    stats = {
        'has_plan': True,
        'plan_name': plan_info.get('plan_name', ''),
        'has_dose_info': bool(plan_info.get('prescribed_dose')),
        'has_fraction_info': bool(plan_info.get('fractions')),
        'uid_verified': plan_info.get('uid_verified', False),
        'modality': plan_info.get('modality', 'UNKNOWN')
    }
    
    # Calculer dose par fraction si les deux infos sont disponibles
    if stats['has_dose_info'] and stats['has_fraction_info']:
        try:
            dose_per_fraction = plan_info['prescribed_dose'] / plan_info['fractions']
            stats['dose_per_fraction'] = dose_per_fraction
            stats['standard_fractionation'] = 1.8 <= dose_per_fraction <= 2.2
        except:
            pass
    
    return stats

def validate_plan_consistency(plan_info, rtdose_data):
    """
    Valide la cohérence entre le plan et les données de dose
    
    Args:
        plan_info (dict): Informations du plan
        rtdose_data: Données RTDose
        
    Returns:
        list: Liste des problèmes détectés
    """
    issues = []
    
    if not plan_info:
        issues.append("Aucune information de plan disponible")
        return issues
    
    if not plan_info.get('uid_verified'):
        issues.append("UID du plan non vérifié avec le RTDose")
    
    # Vérifier la cohérence des dates
    if (plan_info.get('plan_date') and 
        hasattr(rtdose_data, 'InstanceCreationDate')):
        plan_date = plan_info['plan_date']
        dose_date = rtdose_data.InstanceCreationDate
        
        if plan_date > dose_date:
            issues.append("Le plan semble plus récent que la dose calculée")
    
    # Vérifier la présence d'informations essentielles
    if not plan_info.get('prescribed_dose'):
        issues.append("Dose prescrite non trouvée dans le plan")
    
    if not plan_info.get('fractions'):
        issues.append("Nombre de fractions non trouvé dans le plan")
    
    # Vérifier que la modalité est correcte
    if plan_info.get('modality') != 'RTPLAN':
        issues.append(f"Modalité incorrecte: {plan_info.get('modality')} au lieu de RTPLAN")
    
    return issues

# Fonctions utilitaires pour l'intégration
def extract_plan_info_for_viewer(ct_viewer):
    """
    Fonction pratique pour extraire les infos de plan depuis un viewer
    
    Args:
        ct_viewer: Instance du viewer DICOM
        
    Returns:
        dict: Informations formatées du plan
    """
    try:
        if not (hasattr(ct_viewer, 'rtdose_data') and ct_viewer.rtdose_data):
            return None
        
        if not hasattr(ct_viewer, 'folder_path'):
            return None
        
        plan_info = get_plan_info(ct_viewer.folder_path, ct_viewer.rtdose_data)
        
        if plan_info:
            return {
                'raw_info': plan_info,
                'formatted_text': format_plan_info_for_report(plan_info),
                'summary_stats': get_plan_summary_stats(plan_info),
                'validation_issues': validate_plan_consistency(plan_info, ct_viewer.rtdose_data)
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Erreur extraction plan info pour viewer: {e}")
        return None

def find_all_rtplan_files(folder_path):
    """
    Fonction utilitaire pour lister tous les fichiers RTPLAN d'un dossier
    
    Args:
        folder_path (str): Chemin du dossier
        
    Returns:
        list: Liste des fichiers RTPLAN avec leurs informations
    """
    rtplan_files = []
    folder = Path(folder_path)
    
    for file_path in folder.glob("*.dcm"):
        try:
            ds = pydicom.dcmread(file_path, force=True, stop_before_pixels=True)
            
            if hasattr(ds, 'Modality') and ds.Modality == 'RTPLAN':
                rtplan_info = {
                    'filename': file_path.name,
                    'path': str(file_path),
                    'label': getattr(ds, 'RTPlanLabel', 'Sans nom'),
                    'date': getattr(ds, 'RTPlanDate', ''),
                    'uid': getattr(ds, 'SOPInstanceUID', '')
                }
                rtplan_files.append(rtplan_info)
                
        except Exception as e:
            logger.debug(f"Erreur lecture {file_path.name}: {e}")
    
    return rtplan_files

