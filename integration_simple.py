#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'intégration simple pour ajouter le bouton de rapport dosimétrique
au projet existant sans modifier les fichiers principaux - 
© 2025 Caroline Moreau-Noblet — RT-DENTX — Licence BSD 3-Clause
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging

logger = logging.getLogger(__name__)

def add_dose_report_to_existing_project(ct_viewer):
    """
    Fonction pour ajouter le rapport dosimétrique à un projet existant 
    
    Args:
        ct_viewer: Instance du DicomViewer existant
    """
    try:
        # Trouver le panel dentaire existant
        if not hasattr(ct_viewer, 'tooth_panel'):
            logger.warning("Aucun panel dentaire trouvé")
            return False
        
        tooth_panel = ct_viewer.tooth_panel
        logger.info(f"ToothPanel trouvé: {type(tooth_panel)}")
        
        # CORRECTION: Trouver le frame d'export existant dans ui_panels.py
        export_frame = None
        
        # Dans ui_panels.py, il y a un ToothPanel avec plusieurs LabelFrame
        # On cherche le frame "Export RTStruct"
        try:
            # Le ToothPanel de ui_panels.py crée directement des widgets dans self.parent
            # Parcourir tous les frames de l'interface pour trouver celui avec "Export"
            for widget in ct_viewer.master.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for sub_widget in widget.winfo_children():
                        if isinstance(sub_widget, ttk.Frame):
                            for sub_sub_widget in sub_widget.winfo_children():
                                if isinstance(sub_sub_widget, ttk.Frame):
                                    # Frame de droite (outils dentaires)
                                    for tooth_widget in sub_sub_widget.winfo_children():
                                        if isinstance(tooth_widget, ttk.LabelFrame):
                                            frame_text = tooth_widget.cget("text")
                                            if "Export" in frame_text:
                                                export_frame = tooth_widget
                                                logger.info(f"✅ Frame d'export trouvé: {frame_text}")
                                                break
                                    if export_frame:
                                        break
                            if export_frame:
                                break
                    if export_frame:
                        break
            
            # Si pas trouvé par cette méthode, chercher directement dans le parent du tooth_panel
            if not export_frame:
                parent_widget = tooth_panel.parent
                for child in parent_widget.winfo_children():
                    if isinstance(child, ttk.Frame):
                        for subchild in child.winfo_children():
                            if isinstance(subchild, ttk.LabelFrame):
                                frame_text = subchild.cget("text")
                                if "Export" in frame_text:
                                    export_frame = subchild
                                    logger.info(f"✅ Frame d'export trouvé (méthode 2): {frame_text}")
                                    break
                        if export_frame:
                            break
        
        except Exception as e:
            logger.error(f"Erreur recherche frame d'export: {e}")
        
        # Si toujours pas trouvé, créer un nouveau frame
        if not export_frame:
            logger.warning("Frame d'export non trouvé, création d'un nouveau")
            # Trouver le frame principal du tooth panel
            tooth_frame = None
            try:
                parent_widget = tooth_panel.parent
                for child in parent_widget.winfo_children():
                    if isinstance(child, ttk.Frame) and child.winfo_width() > 250:
                        tooth_frame = child
                        break
                
                if tooth_frame:
                    export_frame = ttk.LabelFrame(
                        tooth_frame, 
                        text="📊 Rapports avancés", 
                        padding=10
                    )
                    export_frame.pack(fill=tk.X, pady=(0, 10))
                else:
                    logger.error("Impossible de trouver le frame principal du tooth panel")
                    return False
            except Exception as e:
                logger.error(f"Erreur création frame d'export: {e}")
                return False
        
        if not export_frame:
            logger.error("Impossible de trouver ou créer le frame d'export")
            return False
        
        # CORRECTION 1: Ajouter le bouton APRÈS le bouton RTStruct existant
        # Trouver la position du bouton RTStruct
        rtstruct_button_found = False
        insert_position = None
        
        try:
            children = export_frame.winfo_children()
            for i, child in enumerate(children):
                if isinstance(child, ttk.Button):
                    button_text = child.cget("text")
                    if "RTStruct" in button_text:
                        rtstruct_button_found = True
                        # Insérer après ce bouton
                        insert_position = i + 1
                        logger.info(f"✅ Bouton RTStruct trouvé à la position {i}")
                        break
        except Exception as e:
            logger.error(f"Erreur recherche bouton RTStruct: {e}")
        
        # CORRECTION 2: Créer le bouton avec options corrects (pas de background)
        dose_report_btn = ttk.Button(
            export_frame,
            text="📊 Générer rapport dosimétrique",
            command=lambda: launch_dose_report(ct_viewer),
            state='disabled'
        )
        
        # Positionner le bouton
        if rtstruct_button_found and insert_position is not None:
            # Récupérer tous les widgets après la position d'insertion
            children_after = export_frame.winfo_children()[insert_position:]
            
            # Temporairement retirer ces widgets
            for child in children_after:
                child.pack_forget()
            
            # Ajouter notre bouton
            dose_report_btn.pack(fill=tk.X, pady=2)
            
            # Remettre les widgets qui étaient après
            for child in children_after:
                if isinstance(child, ttk.Button):
                    child.pack(fill=tk.X, pady=2)
                elif isinstance(child, ttk.Label):
                    child.pack(anchor=tk.W, pady=(5, 0))
                else:
                    child.pack(fill=tk.X, pady=2)
        else:
            # Si pas de bouton RTStruct trouvé, ajouter à la fin
            dose_report_btn.pack(fill=tk.X, pady=2)
        
        # Stocker la référence du bouton pour la mise à jour d'état
        tooth_panel.btn_dose_report = dose_report_btn
        
        # CORRECTION 3: Remplacer ttk.Label par tk.Label pour éviter l'erreur foreground
        try:
            # Obtenir la couleur de fond du parent pour l'harmonie visuelle
            parent_bg = export_frame.cget('bg') if hasattr(export_frame, 'cget') else '#f0f0f0'
        except:
            parent_bg = '#f0f0f0'
        
        info_label = tk.Label(
            export_frame,
            text="Génère un PDF avec doses, cartographies et recommandations",
            font=('Arial', 8),
            fg='#666666',  # fg au lieu de foreground pour tk.Label
            bg=parent_bg,  # Couleur de fond harmonieuse
            justify=tk.LEFT
        )
        info_label.pack(anchor=tk.W, pady=(2, 0))
        
        # Modifier la méthode update_button_states si elle existe
        if hasattr(tooth_panel, 'update_button_states'):
            original_method = tooth_panel.update_button_states
            
            def enhanced_update_button_states():
                # Appeler la méthode originale
                try:
                    original_method()
                except Exception as e:
                    logger.debug(f"Erreur méthode originale update_button_states: {e}")
                
                # Mettre à jour notre bouton
                update_dose_report_button_state(ct_viewer, dose_report_btn)
            
            tooth_panel.update_button_states = enhanced_update_button_states
        else:
            # Créer une méthode de mise à jour simple
            def update_dose_report_button():
                update_dose_report_button_state(ct_viewer, dose_report_btn)
            
            tooth_panel.update_dose_report_button = update_dose_report_button
        
        # Faire une mise à jour immédiate de l'état du bouton
        update_dose_report_button_state(ct_viewer, dose_report_btn)
        
        logger.info("✅ Bouton de rapport dosimétrique ajouté avec succès")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'ajout du bouton de rapport: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_dose_report_button_state(ct_viewer, button):
    """Met à jour l'état du bouton de rapport dosimétrique"""
    try:
        # Vérifier les prérequis
        has_dental_structures = False
        has_rtdose = False
        
        # Vérifier les structures dentaires
        if hasattr(ct_viewer, 'contours') and ct_viewer.contours:
            dental_structures = [name for name in ct_viewer.contours.keys() 
                               if name.startswith(('C_', 'R_'))]
            has_dental_structures = len(dental_structures) > 0
        
        # Vérifier RTDose
        if hasattr(ct_viewer, 'rtdose_data'):
            has_rtdose = ct_viewer.rtdose_data is not None
        
        # Mettre à jour l'état du bouton
        can_generate = has_dental_structures and has_rtdose
        button.configure(state='normal' if can_generate else 'disabled')
        
        # Mettre à jour le texte selon l'état
        if not has_rtdose:
            button.configure(text="📊 Rapport (RTDose requis)")
        elif not has_dental_structures:
            button.configure(text="📊 Rapport (Structures requises)")
        else:
            button.configure(text="📊 Générer rapport dosimétrique")
            
    except Exception as e:
        logger.error(f"Erreur mise à jour état bouton: {e}")

def launch_dose_report(ct_viewer):
    """Lance le générateur de rapport dosimétrique"""
    try:
        # Vérifications préliminaires
        if not validate_prerequisites(ct_viewer):
            return
        
        # Importer et lancer le générateur
        from dose_report_generator import DoseReportGenerator
        
        report_generator = DoseReportGenerator(ct_viewer)
        report_generator.show_report_dialog()
        
    except ImportError as e:
        messagebox.showerror(
            "Module manquant",
            "Le module de rapport dosimétrique n'est pas disponible.\n\n"
            "Assurez-vous que les fichiers suivants sont présents :\n"
            "• dose_report_generator.py\n"
            "• rapport_pdf_enhanced.py\n"
            "• plan_info_enhanced.py\n\n"
            f"Erreur : {str(e)}"
        )
    except Exception as e:
        messagebox.showerror(
            "Erreur",
            f"Erreur lors du lancement du rapport dosimétrique :\n\n{str(e)}"
        )
        logger.error(f"Erreur lancement rapport: {e}")

def validate_prerequisites(ct_viewer):
    """Valide les prérequis pour générer un rapport"""
    # Vérifier RTDose
    if not hasattr(ct_viewer, 'rtdose_data') or not ct_viewer.rtdose_data:
        messagebox.showwarning(
            "RTDose manquant",
            "Aucune donnée RTDose trouvée.\n\n"
            "Pour générer un rapport dosimétrique, vous devez :\n"
            "1. Charger un dossier DICOM contenant un fichier RTDose\n"
            "2. Générer les structures dentaires (cylindres 3D)"
        )
        return False
    
    # Vérifier structures dentaires
    dental_structures = []
    if hasattr(ct_viewer, 'contours') and ct_viewer.contours:
        dental_structures = [name for name in ct_viewer.contours.keys() 
                           if name.startswith(('C_', 'R_'))]
    
    if not dental_structures:
        messagebox.showwarning(
            "Structures dentaires manquantes",
            "Aucune structure dentaire trouvée.\n\n"
            "Pour générer un rapport dosimétrique, vous devez :\n"
            "1. Placer les points de référence dentaires\n"
            "2. Générer les cylindres 3D (bouton 'Générer cylindres 3D')\n"
            "3. Vérifier que les contours sont visibles dans l'interface"
        )
        return False
    
    logger.info(f"Prérequis validés : {len(dental_structures)} structures dentaires trouvées")
    return True

def install_dependencies():
    """Vérifie et installe les dépendances nécessaires"""
    try:
        logger.info("ReportLab disponible")
        return True
    except ImportError:
        messagebox.showwarning(
            "Dépendance manquante",
            "Le module ReportLab est requis pour générer les rapports PDF.\n\n"
            "Installez-le avec la commande :\n"
            "pip install reportlab\n\n"
            "Puis redémarrez l'application."
        )
        return False

def auto_integrate_to_viewer(ct_viewer):
    """
    Intégration automatique appelée depuis le viewer principal
    
    Args:
        ct_viewer: Instance du DicomViewer
    
    Returns:
        bool: Succès de l'intégration
    """
    try:
        # Vérifier les dépendances
        if not install_dependencies():
            return False
        
        # Ajouter le bouton
        success = add_dose_report_to_existing_project(ct_viewer)
        
        if success:
            logger.info("✅ Rapport dosimétrique intégré avec succès")
            
            # Mise à jour initiale de l'état du bouton
            if hasattr(ct_viewer.tooth_panel, 'btn_dose_report'):
                update_dose_report_button_state(ct_viewer, ct_viewer.tooth_panel.btn_dose_report)
            
            return True
        else:
            logger.error("❌ Échec de l'intégration du rapport dosimétrique")
            return False
            
    except Exception as e:
        logger.error(f"Erreur intégration automatique: {e}")
        return False


