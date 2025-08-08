#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intégration du bouton d'export RTStruct pour les contours dentaires
© 2025 Caroline Moreau-Noblet — RT-DENTX — Licence BSD 3-Clause
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import logging
from rtstruct_writer import RTStructWriter

logger = logging.getLogger(__name__)

class RTStructExportMixin:
    """Mixin pour ajouter la fonctionnalité d'export RTStruct aux panels dentaires"""
    
    def setup_rtstruct_export_section(self, parent):
        """Ajoute la section d'export RTStruct au panel"""
        export_frame = ttk.LabelFrame(parent, text="Export RTStruct", padding=10)
        export_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Bouton d'export principal
        self.btn_export_rtstruct = ttk.Button(
            export_frame,
            text="📁 Exporter RTStruct avec dents",
            command=self.export_rtstruct_with_teeth
        )
        self.btn_export_rtstruct.pack(fill=tk.X, pady=2)
        
        # Informations sur l'export
        info_text = """Exporte une copie du RTStruct original
avec les contours dentaires ajoutés.
Préserve toutes les structures existantes."""
        
        info_label = ttk.Label(
            export_frame, 
            text=info_text,
            font=('Arial', 8),
            foreground='#666666',
            justify=tk.LEFT
        )
        info_label.pack(anchor=tk.W, pady=(5, 0))
        
        return export_frame
    
    def export_rtstruct_with_teeth(self):
        """Exporte le RTStruct avec les contours dentaires"""
        try:
            # Vérifications préliminaires
            if not self._validate_export_conditions():
                return
            
            # Dialogue de sélection du fichier
            output_path = self._get_output_path()
            if not output_path:
                return
            
            # Extraire le nom du fichier sans extension pour le Structure Set
            import os
            filename_without_ext = os.path.splitext(os.path.basename(output_path))[0]
            
            # Plus besoin du dialogue d'options - on exporte tout
            dental_structures = [name for name in self.ct_viewer.contours.keys() 
                               if name.startswith(('C_', 'R_'))]
            
            export_options = {
                'structure_set_name': filename_without_ext,  # Utilise le nom du fichier
                'selected_structures': dental_structures
            }
            
            # Effectuer l'export
            self._perform_rtstruct_export(output_path, export_options)
            
        except Exception as e:
            logger.error(f"Erreur export RTStruct: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'export RTStruct:\n{str(e)}")
    
    def _validate_export_conditions(self):
        """Valide les conditions nécessaires pour l'export"""
        # Vérifier qu'on a des contours dentaires
        if not hasattr(self.ct_viewer, 'contours') or not self.ct_viewer.contours:
            messagebox.showwarning(
                "Attention", 
                "Aucun contour chargé.\nGénérez d'abord les cylindres 3D dentaires."
            )
            return False
        
        # Compter les structures dentaires
        dental_structures = [name for name in self.ct_viewer.contours.keys() 
                           if name.startswith(('C_', 'R_'))]
        
        if not dental_structures:
            messagebox.showwarning(
                "Attention",
                "Aucune structure dentaire trouvée.\n"
                "Placez des points de référence et générez les cylindres 3D."
            )
            return False
        
        # Vérifier qu'on a un RTStruct original
        original_rtstruct = self._find_original_rtstruct()
        if not original_rtstruct:
            messagebox.showwarning(
                "Attention",
                "Aucun fichier RTStruct original trouvé dans le dossier.\n"
                "L'export nécessite un RTStruct de base."
            )
            return False
        
        logger.info(f"Validation réussie: {len(dental_structures)} structures dentaires trouvées")
        return True
    
    def _find_original_rtstruct(self):
        """Trouve le fichier RTStruct original en utilisant le tag DICOM Modality"""
        if not hasattr(self.ct_viewer, 'folder_path') or not self.ct_viewer.folder_path:
            return None
            
        folder_path = self.ct_viewer.folder_path
        
        
        
        
        # Parcourir tous les fichiers DICOM du dossier
        for filename in os.listdir(folder_path):
            if filename.endswith('.dcm'):
                try:
                    import pydicom
                    full_path = os.path.join(folder_path, filename)
                    
                    # Lire seulement les tags DICOM, pas les pixels
                    ds = pydicom.dcmread(full_path, stop_before_pixels=True, force=True)
                    
                    # Vérifier le tag Modality
                    if hasattr(ds, 'Modality') and ds.Modality == 'RTSTRUCT':
                        logger.info(f"RTStruct trouvé via tag Modality: {filename}")
                        return full_path
                    
                    # Alternative : vérifier via SOPClassUID (plus robuste)
                    # UID standard pour RTSTRUCT : 1.2.840.10008.5.1.4.1.1.481.3
                    if (hasattr(ds, 'SOPClassUID') and 
                        ds.SOPClassUID == "1.2.840.10008.5.1.4.1.1.481.3"):
                        logger.info(f"RTStruct trouvé via SOPClassUID: {filename}")
                        return full_path
                        
                except Exception as e:
                    # Ignorer les fichiers qui ne peuvent pas être lus
                    logger.debug(f"Impossible de lire {filename}: {e}")
                    continue
        
        logger.warning("Aucun fichier RTStruct trouvé dans le dossier")
        return None
    
    def _get_output_path(self):
        """Dialogue pour sélectionner le chemin de sortie"""
        # Nom par défaut basé sur la date/heure
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"RS_DENTX_{timestamp}.dcm"
        
        # Dossier par défaut = dossier source
        initial_dir = self.ct_viewer.folder_path if hasattr(self.ct_viewer, 'folder_path') else ""
        
        output_path = filedialog.asksaveasfilename(
            title="Sauvegarder le RTStruct avec dents",
            initialdir=initial_dir,
            initialfile=default_name,
            defaultextension=".dcm",
            filetypes=[
                ("Fichiers DICOM", "*.dcm"),
                ("Tous les fichiers", "*.*")
            ]
        )
        
        return output_path
    
    
    
    def _perform_rtstruct_export(self, output_path, options):
        """Effectue l'export RTStruct"""
        
        
       
        # Trouver le RTStruct original
        original_rtstruct = self._find_original_rtstruct()
        
        # Créer le writer RTStruct
        writer = RTStructWriter(
            rtstruct_path=original_rtstruct,
            ct_folder=self.ct_viewer.folder_path,
            ct_slices=self.ct_viewer.ct_slices,
            structure_set_name=options['structure_set_name']
        )
        
        # Ajouter les structures sélectionnées
        structures_added = 0
        
        for structure_name in options['selected_structures']:
            if structure_name in self.ct_viewer.contours:
                contour_data = self.ct_viewer.contours[structure_name]
                
                # Convertir les contours du format d'affichage vers le format DICOM
                dicom_contours = self._convert_contours_to_dicom(contour_data)
                
                if dicom_contours:
                    writer.add_structure(structure_name, dicom_contours)
                    structures_added += 1
                    logger.info(f"Structure ajoutée: {structure_name} ({len(dicom_contours)} coupes)")
        
        # Sauvegarder
        writer.save(output_path)
        
        # Message de confirmation
        crown_count = len([s for s in options['selected_structures'] if s.startswith('C_')])
        root_count = len([s for s in options['selected_structures'] if s.startswith('R_')])
        
        success_message = f"""Export RTStruct terminé avec succès!

Fichier: {os.path.basename(output_path)}
Dossier: {os.path.dirname(output_path)}

Structures exportées: {structures_added}
• Couronnes: {crown_count}
• Racines: {root_count}

Structure Set: {options['structure_set_name']}"""
        
        messagebox.showinfo("Export réussi", success_message)
        logger.info(f"Export RTStruct terminé: {output_path}")
    
    def _convert_contours_to_dicom(self, display_contours):
        """Convertit les contours d'affichage vers le format DICOM"""
        dicom_contours = {}
        
        for slice_idx, contour_points in display_contours.items():
            # Convertir en numpy array si ce n'est pas déjà le cas
            if isinstance(contour_points, list):
                contour_points = np.array(contour_points)
            
            # Vérifier que c'est bien un array avec au moins 3 points
            if not isinstance(contour_points, np.ndarray):
                logger.warning(f"Contour invalide pour slice {slice_idx}: type {type(contour_points)}")
                continue
                
            if len(contour_points) < 3:
                logger.warning(f"Contour avec moins de 3 points pour slice {slice_idx}")
                continue
            
            # Vérifier que slice_idx est valide
            if not (0 <= slice_idx < len(self.ct_viewer.ct_slices)):
                logger.warning(f"Index de coupe invalide: {slice_idx}")
                continue
            
            try:
                # Les contours sont déjà en coordonnées DICOM correctes
                # PAS BESOIN de conversion Y, juste copier les points
                dicom_points = []
                
                for point in contour_points:
                    # S'assurer que le point a 2 coordonnées
                    if len(point) >= 2:
                        x_dicom = float(point[0])
                        y_dicom = float(point[1])
                        
                        dicom_points.append([x_dicom, y_dicom])
                
                if len(dicom_points) >= 3:
                    dicom_contours[slice_idx] = np.array(dicom_points)
                    logger.debug(f"Contour converti pour slice {slice_idx}: {len(dicom_points)} points")
                
            except Exception as e:
                logger.error(f"Erreur conversion contour slice {slice_idx}: {e}")
                continue
        
        return dicom_contours




# Modification du ToothPanel existant pour intégrer l'export RTStruct
class EnhancedToothPanelWithRTStruct(RTStructExportMixin):
    """ToothPanel amélioré avec export RTStruct"""
    
    def __init__(self, parent_frame, ct_viewer):
        self.parent_frame = parent_frame
        self.ct_viewer = ct_viewer
        self.setup_ui()
    
    def setup_ui(self):
        """Configure l'interface du panel dentaire avec export RTStruct"""
        # Frame principal
        self.tooth_frame = ttk.Frame(self.parent_frame, width=300)
        self.tooth_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        self.tooth_frame.pack_propagate(False)
        
        # Canvas scrollable
        self.canvas = tk.Canvas(self.tooth_frame, highlightthickness=0, bg='#f0f0f0')
        self.scrollbar = ttk.Scrollbar(self.tooth_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Titre
        title_label = ttk.Label(
            self.scrollable_frame,
            text="Outils Dentaires",
            font=('Arial', 12, 'bold')
        )
        title_label.pack(pady=(0, 10))
        
        # Sections existantes
        self._create_placement_section()
        self._create_generation_section()
        
        # NOUVELLE SECTION: Export RTStruct
        self.setup_rtstruct_export_section(self.scrollable_frame)
        
        # Section gestion
        self._create_management_section()
    
    def _create_placement_section(self):
        """Section placement des points"""
        placement_frame = ttk.LabelFrame(self.scrollable_frame, text="Points de référence", padding=10)
        placement_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.btn_place_points = ttk.Button(
            placement_frame,
            text="🦷 Tracer les 6 points de référence",
            command=self.start_tooth_placement
        )
        self.btn_place_points.pack(fill=tk.X, pady=2)
        
        self.btn_edit_mode = ttk.Button(
            placement_frame,
            text="✏️ Modifier/Supprimer points",
            command=self.toggle_edit_mode
        )
        self.btn_edit_mode.pack(fill=tk.X, pady=2)
        
        self.placement_status = ttk.Label(
            placement_frame,
            text="Aucun point placé",
            foreground="gray"
        )
        self.placement_status.pack(anchor=tk.W, pady=2)
    
    def _create_generation_section(self):
        """Section génération automatique"""
        generation_frame = ttk.LabelFrame(self.scrollable_frame, text="Génération automatique", padding=10)
        generation_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.btn_generate_teeth = ttk.Button(
            generation_frame,
            text="🔄 Générer les autres dents",
            command=self.generate_other_teeth,
            state='disabled'
        )
        self.btn_generate_teeth.pack(fill=tk.X, pady=2)
        
        self.btn_generate_cylinders = ttk.Button(
            generation_frame,
            text="🏗️ Générer cylindres 3D",
            command=self.generate_cylinders,
            state='disabled'
        )
        self.btn_generate_cylinders.pack(fill=tk.X, pady=2)
        
        self.generation_status = ttk.Label(
            generation_frame,
            text="Génération non lancée",
            foreground="gray"
        )
        self.generation_status.pack(anchor=tk.W, pady=2)
    
    def _create_management_section(self):
        """Section gestion"""
        management_frame = ttk.LabelFrame(self.scrollable_frame, text="Gestion", padding=10)
        management_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.btn_info = ttk.Button(
            management_frame,
            text="ℹ️ Informations dentaires",
            command=self.show_tooth_info
        )
        self.btn_info.pack(fill=tk.X, pady=2)
        
        self.btn_clear = ttk.Button(
            management_frame,
            text="🗑️ Effacer toutes les dents",
            command=self.clear_all_teeth
        )
        self.btn_clear.pack(fill=tk.X, pady=2)
    
    # Méthodes de base du ToothPanel
    def start_tooth_placement(self):
        if hasattr(self.ct_viewer, 'start_tooth_placement'):
            self.ct_viewer.start_tooth_placement()
            self.update_button_states()
    
    def toggle_edit_mode(self):
        if hasattr(self.ct_viewer, 'toggle_tooth_edit_mode'):
            self.ct_viewer.toggle_tooth_edit_mode()
            self.update_button_states()
    
    def generate_other_teeth(self):
        if hasattr(self.ct_viewer, 'generate_other_teeth'):
            self.ct_viewer.generate_other_teeth()
            self.generation_status.config(text="Dents générées", foreground="green")
            self.update_button_states()
    
    def generate_cylinders(self):
        if hasattr(self.ct_viewer, 'generate_tooth_cylinders'):
            self.ct_viewer.generate_tooth_cylinders()
            self.generation_status.config(text="Cylindres 3D générés", foreground="green")
            self.update_button_states()
    
    def show_tooth_info(self):
        if hasattr(self.ct_viewer, 'show_tooth_info'):
            self.ct_viewer.show_tooth_info()
    
    def clear_all_teeth(self):
        if hasattr(self.ct_viewer, 'clear_all_teeth'):
            self.ct_viewer.clear_all_teeth()
            self.placement_status.config(text="Aucun point placé", foreground="gray")
            self.generation_status.config(text="Génération non lancée", foreground="gray")
            self.update_button_states()
    
    def update_button_states(self):
        """Met à jour l'état des boutons"""
        has_points = False
        has_generated = False
        has_structures = False
        
        if hasattr(self.ct_viewer, 'tooth_editor') and self.ct_viewer.tooth_editor:
            has_points = len(self.ct_viewer.tooth_editor.points) > 0
            has_generated = len(self.ct_viewer.tooth_editor.points) >= 6
        
        if hasattr(self.ct_viewer, 'contours'):
            has_structures = any(name.startswith(('C_', 'R_')) 
                               for name in self.ct_viewer.contours.keys())
        
        # Mettre à jour les boutons existants
        self.btn_generate_teeth.configure(
            state='normal' if has_generated else 'disabled'
        )
        self.btn_generate_cylinders.configure(
            state='normal' if has_generated else 'disabled'
        )
        
        # Mettre à jour le bouton d'export RTStruct
        if hasattr(self, 'btn_export_rtstruct'):
            self.btn_export_rtstruct.configure(
                state='normal' if has_structures else 'disabled'
            )
        
        # Mettre à jour les statuts
        if has_points:
            point_count = len(self.ct_viewer.tooth_editor.points)
            self.placement_status.config(
                text=f"{point_count} points placés",
                foreground="blue"
            )


