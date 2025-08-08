#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de rapport dosimétrique dentaire avec interface et export PDF
© 2025 Caroline Moreau-Noblet — RT-DENTX — Licence BSD 3-Clause
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
from datetime import datetime
import logging
import sys, os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

logger = logging.getLogger(__name__)

class DoseReportGenerator:
    """Générateur de rapport dosimétrique avec interface"""
    
    def __init__(self, ct_viewer):
        
        self.ct_viewer = ct_viewer
        self.doses_data = None
        self.dialog = None
        self.config_manager = None
        self.risk_config = None
        self.recommendations_text = None
        
        # Charger la configuration au démarrage
        self._load_current_config()
    
    def _load_current_config(self):
        """Charge la configuration actuelle depuis ConfigManager ou session"""
        try:
            # Priorité 1: Configuration de session si elle existe
            if hasattr(self.ct_viewer, '_report_session_config') and self.ct_viewer._report_session_config:
                session_config = self.ct_viewer._report_session_config
                self.risk_config = session_config['risk_levels'].copy()
                self.recommendations_text = session_config.get('recommendations', None)
                logger.info("Configuration chargée depuis la session")
                logger.info(f"  Seuil faible: {self.risk_config['low_threshold']} Gy")
                logger.info(f"  Seuil modéré: {self.risk_config['moderate_threshold']} Gy")
                return
            
            # Priorité 2: ConfigManager
            try:
                from config_manager import ConfigManager
                self.config_manager = ConfigManager()
                
                # Récupérer la configuration active
                current_config = self.config_manager.get_config()
                
                # Utiliser la configuration active
                self.risk_config = current_config['risk_levels'].copy()
                self.recommendations_text = None  # Sera généré par ConfigManager
                
                config_info = self.config_manager.get_config_info()
                logger.info(f"Configuration chargée depuis ConfigManager:")
                logger.info(f"  Type: {config_info['active_type']}")
                logger.info(f"  Seuil faible: {self.risk_config['low_threshold']} Gy")
                logger.info(f"  Seuil modéré: {self.risk_config['moderate_threshold']} Gy")
            except:
                raise Exception("ConfigManager non disponible")
            
        except Exception as e:
            logger.warning(f"Utilisation config par défaut: {e}")
            # Configuration par défaut
            self.risk_config = {
                "low_threshold": 30.0,
                "moderate_threshold": 50.0,
                "low_label": "Faible",
                "moderate_label": "Modéré",
                "high_label": "Élevé",
                "low_description": "Risque d'ostéoradionécrose faible",
                "moderate_description": "Risque d'ostéoradionécrose modéré",
                "high_description": "Risque d'ostéoradionécrose élevé"
            }
            self.recommendations_text = None
    
    def show_report_dialog(self):
        """Affiche le dialogue de génération de rapport avec aperçu"""
        # Recharger la configuration
        self._load_current_config()
        
        if not self._validate_prerequisites():
            return
        
        # Calculer les doses
        try:
            self.doses_data = self._calculate_dental_doses()
            if not self.doses_data:
                messagebox.showerror("Erreur", "Impossible de calculer les doses dentaires")
                return
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du calcul des doses:\n{str(e)}")
            logger.error(f"Erreur calcul doses: {e}")
            return
        
        # Créer le dialogue
        self._create_dialog()
    
    def _validate_prerequisites(self):
        """Valide les prérequis pour générer un rapport"""
        # Vérifier qu'on a des données RTDose
        if not hasattr(self.ct_viewer, 'rtdose_data') or not self.ct_viewer.rtdose_data:
            messagebox.showwarning(
                "Données manquantes",
                "Aucune donnée RTDose trouvée.\nChargez un fichier RTDose pour générer un rapport."
            )
            return False
        
        # Vérifier qu'on a des structures dentaires
        dental_structures = [name for name in self.ct_viewer.contours.keys() 
                           if name.startswith(('C_', 'R_'))]
        
        if not dental_structures:
            messagebox.showwarning(
                "Structures manquantes",
                "Aucune structure dentaire trouvée.\n"
                "Générez d'abord les cylindres 3D dentaires."
            )
            return False
        
        return True
    
    def _calculate_dental_doses(self):
        """Calcule les doses dentaires"""
        try:
            # Utiliser la fonction utilitaire qui gère tout
            from dose_calculator import calculate_all_dental_doses_from_viewer
            return calculate_all_dental_doses_from_viewer(self.ct_viewer)
        except Exception as e:
            logger.error(f"Erreur calcul doses: {e}")
            raise


    
    
    def _create_dialog(self):
        """Crée le dialogue principal avec aperçu"""
        # Obtenir la fenêtre racine correctement
        if hasattr(self.ct_viewer, 'root'):
            parent_window = self.ct_viewer.root
        elif hasattr(self.ct_viewer, 'master'):
            parent_window = self.ct_viewer.master
        else:
            # Remonter jusqu'à la fenêtre principale
            parent_window = self.ct_viewer
            while hasattr(parent_window, 'master') and parent_window.master is not None:
                parent_window = parent_window.master
        
        self.dialog = tk.Toplevel(parent_window)
        self.dialog.title("📊 Aperçu et génération du rapport dosimétrique")
        self.dialog.geometry("1000x800")
        self.dialog.title("📊 Aperçu et génération du rapport dosimétrique")
        self.dialog.geometry("1000x800")
        
        # Notebook pour organiser les sections
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Onglet 1 : Configuration appliquée
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Configuration appliquée")
        self._create_config_display(config_frame)
        
        # Onglet 2 : Tableau récapitulatif
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="Tableau récapitulatif des doses")
        self._create_summary_table(summary_frame)
        
        # Onglet 3 : Options d'export
        options_frame = ttk.Frame(notebook)
        notebook.add(options_frame, text="Options d'export")
        self._create_export_options(options_frame)
        
        # Boutons de contrôle
        self._create_control_buttons()
    
    def _create_config_display(self, parent):
        """Affiche la configuration qui sera appliquée"""
        # Frame principal avec scrollbar
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Seuils de risque
        risk_frame = ttk.LabelFrame(scrollable_frame, text="Seuils de risque appliqués", padding=10)
        risk_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        seuils_text = f"""Les seuils suivants seront utilisés pour ce rapport :

• Risque {self.risk_config['low_label']} : < {self.risk_config['low_threshold']:.0f} Gy
  {self.risk_config['low_description']}

• Risque {self.risk_config['moderate_label']} : {self.risk_config['low_threshold']:.0f} - {self.risk_config['moderate_threshold']:.0f} Gy
  {self.risk_config['moderate_description']}

• Risque {self.risk_config['high_label']} : > {self.risk_config['moderate_threshold']:.0f} Gy
  {self.risk_config['high_description']}"""
        
        tk.Label(risk_frame, text=seuils_text, font=('Arial', 10), 
                justify=tk.LEFT).pack(anchor=tk.W)
        
        # Code couleur
        color_frame = tk.Frame(risk_frame)
        color_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Vert
        green_frame = tk.Frame(color_frame)
        green_frame.pack(side=tk.LEFT, padx=(0, 20))
        tk.Label(green_frame, text="  ", bg='#27ae60', width=3).pack(side=tk.LEFT)
        tk.Label(green_frame, text=f"< {self.risk_config['low_threshold']:.0f} Gy", 
                font=('Arial', 9)).pack(side=tk.LEFT, padx=(5, 0))
        
        # Orange
        orange_frame = tk.Frame(color_frame)
        orange_frame.pack(side=tk.LEFT, padx=(0, 20))
        tk.Label(orange_frame, text="  ", bg='#f39c12', width=3).pack(side=tk.LEFT)
        tk.Label(orange_frame, text=f"{self.risk_config['low_threshold']:.0f}-{self.risk_config['moderate_threshold']:.0f} Gy", 
                font=('Arial', 9)).pack(side=tk.LEFT, padx=(5, 0))
        
        # Rouge
        red_frame = tk.Frame(color_frame)
        red_frame.pack(side=tk.LEFT)
        tk.Label(red_frame, text="  ", bg='#e74c3c', width=3).pack(side=tk.LEFT)
        tk.Label(red_frame, text=f"> {self.risk_config['moderate_threshold']:.0f} Gy", 
                font=('Arial', 9)).pack(side=tk.LEFT, padx=(5, 0))
        
        # Recommandations cliniques
        rec_frame = ttk.LabelFrame(scrollable_frame, text="Recommandations cliniques qui seront incluses", padding=10)
        rec_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        # Obtenir le texte des recommandations
        rec_text = self._get_formatted_recommendations()
        
        # Zone de texte en lecture seule
        rec_display = tk.Text(rec_frame, wrap=tk.WORD, height=25, width=80)
        rec_display.pack(fill=tk.BOTH, expand=True)
        rec_display.insert('1.0', rec_text)
        rec_display.config(state='disabled', bg='#f5f5f5')
        
        # Placer le canvas et la scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_summary_table(self, parent):
        """Crée le tableau récapitulatif des doses"""
        # Frame pour le tableau
        table_frame = ttk.Frame(parent, padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre et statistiques
        info_frame = ttk.Frame(table_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Calculer les statistiques
        total_teeth = len(self.doses_data['complete'])
        dose_values = list(self.doses_data['complete'].values())
        
        if dose_values:
            stats_text = f"Nombre de dents analysées : {total_teeth}\n"
            stats_text += f"Dose minimale : {min(dose_values):.1f} Gy\n"
            stats_text += f"Dose maximale : {max(dose_values):.1f} Gy\n"
            stats_text += f"Dose moyenne : {np.mean(dose_values):.1f} Gy"
        else:
            stats_text = "Aucune dose calculée"
        
        tk.Label(info_frame, text=stats_text, font=('Arial', 10, 'bold'), 
                justify=tk.LEFT).pack(anchor=tk.W)
        
        # Créer le Treeview pour le tableau
        columns = ('couronne', 'racine', 'complete', 'statut')
        tree = ttk.Treeview(table_frame, columns=columns, show='tree headings', height=20)
        
        # Définir les colonnes
        tree.heading('#0', text='Dent')
        tree.heading('couronne', text='Dose couronne (Gy)')
        tree.heading('racine', text='Dose racine (Gy)')
        tree.heading('complete', text='Dose complète (Gy)')
        tree.heading('statut', text='Statut de risque')
        
        # Largeur des colonnes
        tree.column('#0', width=80)
        tree.column('couronne', width=150, anchor='center')
        tree.column('racine', width=150, anchor='center')
        tree.column('complete', width=150, anchor='center')
        tree.column('statut', width=200, anchor='center')
        
        # Styles pour les couleurs
        tree.tag_configure('low', background='#d5f4e6')
        tree.tag_configure('moderate', background='#fdebd0')
        tree.tag_configure('high', background='#fadbd8')
        
        # Remplir le tableau
        all_teeth = set()
        for data_type in ['complete', 'couronne', 'racine']:
            if data_type in self.doses_data:
                all_teeth.update(self.doses_data[data_type].keys())
        
        for tooth_num in sorted(all_teeth):
            # Récupérer les doses
            dose_couronne = self.doses_data.get('couronne', {}).get(tooth_num, 0)
            dose_racine = self.doses_data.get('racine', {}).get(tooth_num, 0)
            dose_complete = self.doses_data.get('complete', {}).get(tooth_num, 0)
            
            # Déterminer la dose maximale pour le statut
            max_dose = max(dose_couronne, dose_racine, dose_complete)
            
            # Déterminer le statut et la couleur
            if max_dose < self.risk_config['low_threshold']:
                statut = self.risk_config['low_label']
                tag = 'low'
            elif max_dose < self.risk_config['moderate_threshold']:
                statut = self.risk_config['moderate_label']
                tag = 'moderate'
            else:
                statut = self.risk_config['high_label']
                tag = 'high'
            
            # Ajouter la ligne
            values = (
                f"{dose_couronne:.1f}" if dose_couronne > 0 else "-",
                f"{dose_racine:.1f}" if dose_racine > 0 else "-",
                f"{dose_complete:.1f}" if dose_complete > 0 else "-",
                statut
            )
            
            tree.insert('', 'end', text=str(tooth_num), values=values, tags=(tag,))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Placer le tableau et la scrollbar
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Légende
        legend_frame = ttk.Frame(parent)
        legend_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(legend_frame, text="Légende :", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        legend_colors = tk.Frame(legend_frame)
        legend_colors.pack(fill=tk.X, pady=(5, 0))
        
        # Légende des couleurs
        for color, label, desc in [
            ('#d5f4e6', self.risk_config['low_label'], f"< {self.risk_config['low_threshold']:.0f} Gy"),
            ('#fdebd0', self.risk_config['moderate_label'], f"{self.risk_config['low_threshold']:.0f}-{self.risk_config['moderate_threshold']:.0f} Gy"),
            ('#fadbd8', self.risk_config['high_label'], f"> {self.risk_config['moderate_threshold']:.0f} Gy")
        ]:
            item_frame = tk.Frame(legend_colors)
            item_frame.pack(side=tk.LEFT, padx=(0, 20))
            tk.Label(item_frame, text="  ", bg=color, width=3).pack(side=tk.LEFT)
            tk.Label(item_frame, text=f"{label} : {desc}").pack(side=tk.LEFT, padx=(5, 0))
    
    def _create_export_options(self, parent):
        """Crée les options d'export"""
        options_frame = ttk.Frame(parent, padding=20)
        options_frame.pack(fill=tk.BOTH, expand=True)
        
        # Variables
        self.export_complete = tk.BooleanVar(value=True)
        self.export_crowns = tk.BooleanVar(value=True)
        self.export_roots = tk.BooleanVar(value=True)
        self.include_cartography = tk.BooleanVar(value=True)
        self.include_table = tk.BooleanVar(value=True)
        self.include_recommendations = tk.BooleanVar(value=True)
        
        # Section doses
        dose_frame = ttk.LabelFrame(options_frame, text="Types de doses à inclure", padding=10)
        dose_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Checkbutton(dose_frame, text="Dents complètes (couronne + racine)", 
                       variable=self.export_complete).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(dose_frame, text="Couronnes séparément", 
                       variable=self.export_crowns).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(dose_frame, text="Racines séparément", 
                       variable=self.export_roots).pack(anchor=tk.W, pady=2)
        
        # Section contenu
        content_frame = ttk.LabelFrame(options_frame, text="Contenu du rapport", padding=10)
        content_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Checkbutton(content_frame, text="Cartographies anatomiques avec code couleur", 
                       variable=self.include_cartography).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(content_frame, text="Tableau récapitulatif des doses", 
                       variable=self.include_table).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(content_frame, text="Recommandations cliniques", 
                       variable=self.include_recommendations).pack(anchor=tk.W, pady=2)
        
        # Note d'information
        info_text = """Note : Le rapport PDF contiendra les éléments sélectionnés ci-dessus.
Les seuils de risque et recommandations affichés dans l'onglet "Configuration appliquée" 
seront automatiquement utilisés."""
        
        tk.Label(options_frame, text=info_text, font=('Arial', 9, 'italic'), 
                justify=tk.LEFT, wraplength=500).pack(pady=(20, 0))
    
    def _create_control_buttons(self):
        """Crée les boutons de contrôle"""
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, pady=(0, 10), padx=10)
        
        # Bouton Configuration (optionnel - pour modifier la config)
        config_btn = ttk.Button(button_frame, text="⚙️ Modifier la configuration", 
                               command=self._open_config_dialog)
        config_btn.pack(side=tk.LEFT)
        
        # Boutons à droite
        ttk.Button(button_frame, text="Annuler", 
                  command=self.dialog.destroy).pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Button(button_frame, text="📄 Générer le rapport PDF", 
                  command=self._generate_pdf_report).pack(side=tk.RIGHT, padx=(10, 0))
    
    def _open_config_dialog(self):
        """Ouvre le dialogue de configuration"""
        try:
            from report_config_dialog import ReportConfigDialog
            
            # Fermer la fenêtre actuelle
            self.dialog.destroy()
            
            # Obtenir la fenêtre parente correctement
            if hasattr(self.ct_viewer, 'master'):
                parent_window = self.ct_viewer.master
            else:
                # Utiliser la fenêtre par défaut
                import tkinter as tk
                parent_window = tk._default_root
            
            # Ouvrir la configuration
            config_dialog = ReportConfigDialog(parent_window, self.ct_viewer)
            config_dialog.show()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir la configuration:\n{str(e)}")
            logger.error(f"Erreur ouverture config: {e}")
    
    def _get_formatted_recommendations(self):
        """Obtient les recommandations formatées avec les seuils actuels"""
        if self.recommendations_text:
            # Recommandations personnalisées
            text = self.recommendations_text
            text = text.replace("{low_threshold}", f"{self.risk_config['low_threshold']:.0f}")
            text = text.replace("{moderate_threshold}", f"{self.risk_config['moderate_threshold']:.0f}")
            return text
        
        # Recommandations par défaut ou du ConfigManager
        if self.config_manager:
            try:
                rec_lines = self.config_manager.get_recommendations_text()
                # Mettre à jour les seuils
                formatted_lines = []
                for line in rec_lines:
                    if "50 Gy" in line and "30-50 Gy" in line:
                        line = line.replace("50 Gy", f"{self.risk_config['moderate_threshold']:.0f} Gy")
                        line = line.replace("30-50 Gy", f"{self.risk_config['low_threshold']:.0f}-{self.risk_config['moderate_threshold']:.0f} Gy")
                    formatted_lines.append(line)
                return '\n'.join(formatted_lines)
            except:
                pass
        
        # Recommandations par défaut
        return f"""Recommandations cliniques

PRÉVENTION DE L'OSTÉORADIONÉCROSE :

• Des précautions particulières doivent être prises lors des soins bucco-dentaires,
  en particulier en cas d'avulsion ou d'un autre geste chirurgical en territoire irradié.

• Surveillance clinique renforcée pour les dents ayant reçu > {self.risk_config['moderate_threshold']:.0f} Gy (risque élevé)
  et entre {self.risk_config['low_threshold']:.0f}-{self.risk_config['moderate_threshold']:.0f} Gy (risque modéré).

• Maintien d'une hygiène bucco-dentaire optimale.

• Fluorothérapie quotidienne recommandée.

CONTACT :

En cas de doute, veuillez prendre contact avec :
• Le radiothérapeute référent, ou
• Le service d'odontologie ou de chirurgie maxillofaciale du CHU le plus proche."""
    
    def _generate_pdf_report(self):
        """Génère le rapport PDF"""
        try:
            # Demander l'emplacement de sauvegarde
            output_path = filedialog.asksaveasfilename(
                title="Enregistrer le rapport PDF",
                defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf"), ("Tous fichiers", "*.*")],
                initialfile=f"rapport_dentaire_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            
            if not output_path:
                return
            
            # Préparer les paramètres
            parameters = {
                'dose_complete': self.export_complete.get(),
                'dose_couronne': self.export_crowns.get(),
                'dose_racine': self.export_roots.get(),
                'show_colors': self.include_cartography.get(),
                'show_legend': True,
                'show_recommendations': self.include_recommendations.get(),
                'show_table': self.include_table.get()
            }
            
            # Informations patient
            patient_info = self._extract_patient_info()
            plan_info = self._get_plan_info()
            if plan_info:
                patient_info["Plan de traitement"] = plan_info['formatted_text']
            
            # Créer un gestionnaire de configuration temporaire
            temp_config_manager = TempConfigManager(self.risk_config, self.config_manager, self.recommendations_text)
            
            # Générer le PDF
            from rapport_pdf_enhanced import genere_rapport_pdf_enhanced
            
            genere_rapport_pdf_enhanced(
                doses_data=self.doses_data,
                parameters=parameters,
                patient_info=patient_info,
                output_path=output_path,
                config_manager=temp_config_manager
            )
            
            # Message de succès
            messagebox.showinfo(
                "Rapport généré",
                f"Rapport PDF généré avec succès!\n\nFichier: {output_path}"
            )
            
            # Fermer le dialogue
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la génération PDF:\n{str(e)}")
            logger.error(f"Erreur génération PDF: {e}")
            import traceback
            traceback.print_exc()
    
    def _extract_patient_info(self):
        """Extrait les informations patient"""
        if not self.ct_viewer.ct_slices:
            return {}
        
        ds = self.ct_viewer.ct_slices[0]
        
        return {
            'Nom': str(getattr(ds, 'PatientName', 'Inconnu')).replace('^', ' '),
            'ID Patient': getattr(ds, 'PatientID', 'Inconnu'),
            'Date de naissance': getattr(ds, 'PatientBirthDate', ''),
            'Sexe': getattr(ds, 'PatientSex', ''),
            'Date étude': getattr(ds, 'StudyDate', ''),
            'Description': getattr(ds, 'StudyDescription', ''),
            'Institution': getattr(ds, 'InstitutionName', '')
        }
    

    def _get_plan_info(self):
        """Récupère les informations du plan de traitement"""
        try:
            from plan_info_enhanced import get_plan_info, format_plan_info_for_report
            
            if hasattr(self.ct_viewer, 'rtdose_data') and self.ct_viewer.rtdose_data:
                plan_info = get_plan_info(
                    self.ct_viewer.folder_path,  # Ajout du dossier
                    self.ct_viewer.rtdose_data
                )
                
                if plan_info:
                    # Formater les informations pour le rapport
                    formatted_text = format_plan_info_for_report(plan_info)
                    
                    logger.info(f"Plan trouvé : {plan_info.get('plan_name', 'Inconnu')}")
                    logger.info(f"Dose prescrite : {plan_info.get('prescribed_dose', 'N/A')} Gy")
                    logger.info(f"Fractions : {plan_info.get('fractions', 'N/A')}")
                    
                    return {
                        'formatted_text': formatted_text,
                        'raw_info': plan_info
                    }
            
            logger.warning("Aucune donnée RTDose disponible pour extraire les infos du plan")
            return None
            
        except Exception as e:
            logger.error(f"Erreur extraction plan info: {e}")
            import traceback
            traceback.print_exc()
            return None


class TempConfigManager:
    """Gestionnaire de configuration temporaire pour le rapport"""
    
    def __init__(self, risk_config, original_config_manager=None, recommendations_text=None):
        self.temp_risk_config = risk_config
        self.original_config_manager = original_config_manager
        self.recommendations_text = recommendations_text
    
    def get_config(self):
        """Retourne la configuration avec les seuils temporaires"""
        if self.original_config_manager:
            # Récupérer la config complète et remplacer les seuils
            config = self.original_config_manager.get_config()
            config['risk_levels'] = self.temp_risk_config.copy()
            return config
        else:
            # Configuration par défaut avec seuils temporaires
            return {
                "risk_levels": self.temp_risk_config,
                "recommendations": {
                    "title": "Recommandations cliniques",
                    "prevention_title": "PRÉVENTION DE L'OSTÉORADIONÉCROSE :",
                    "prevention_items": [
                        "",
                        "• Des précautions particulières doivent être prises lors des soins bucco-dentaires,",
                        "  en particulier en cas d'avulsion ou d'un autre geste chirurgical en territoire irradié.",
                        "",
                        f"• Surveillance clinique renforcée pour les dents ayant reçu > {self.temp_risk_config['moderate_threshold']:.0f} Gy (risque élevé)",
                        f"  et entre {self.temp_risk_config['low_threshold']:.0f}-{self.temp_risk_config['moderate_threshold']:.0f} Gy (risque modéré).",
                        "",
                        "• Maintien d'une hygiène bucco-dentaire optimale.",
                        "",
                        "• Fluorothérapie quotidienne recommandée."
                    ],
                    "contact_title": "CONTACT :",
                    "contact_items": [
                        "",
                        "En cas de doute, veuillez prendre contact avec :",
                        "• Le radiothérapeute référent, ou",
                        "• Le service d'odontologie ou de chirurgie maxillofaciale du CHU le plus proche."
                    ]
                }
            }
    
    def get_recommendations_text(self):
        """Retourne les recommandations formatées avec les seuils temporaires"""
        # Si on a des recommandations personnalisées
        if self.recommendations_text:
            # Remplacer les placeholders
            text = self.recommendations_text
            text = text.replace("{low_threshold}", f"{self.temp_risk_config['low_threshold']:.0f}")
            text = text.replace("{moderate_threshold}", f"{self.temp_risk_config['moderate_threshold']:.0f}")
            return text.split('\n')
        
        # Sinon utiliser le format standard
        config = self.get_config()
        rec = config.get("recommendations", {})
        
        # Si les recommandations ne sont pas complètes, utiliser les valeurs par défaut
        if not rec or "title" not in rec:
            return [
                "Recommandations cliniques",
                "",
                "PRÉVENTION DE L'OSTÉORADIONÉCROSE :",
                "",
                "• Des précautions particulières doivent être prises lors des soins bucco-dentaires,",
                "  en particulier en cas d'avulsion ou d'un autre geste chirurgical en territoire irradié.",
                "",
                f"• Surveillance clinique renforcée pour les dents ayant reçu > {self.temp_risk_config['moderate_threshold']:.0f} Gy (risque élevé)",
                f"  et entre {self.temp_risk_config['low_threshold']:.0f}-{self.temp_risk_config['moderate_threshold']:.0f} Gy (risque modéré).",
                "",
                "• Maintien d'une hygiène bucco-dentaire optimale.",
                "",
                "• Fluorothérapie quotidienne recommandée.",
                "",
                "CONTACT :",
                "",
                "En cas de doute, veuillez prendre contact avec :",
                "• Le radiothérapeute référent, ou",
                "• Le service d'odontologie ou de chirurgie maxillofaciale du CHU le plus proche."
            ]
        
        # Utiliser les recommandations du config manager
        lines = [rec["title"]]
        lines.append("")
        lines.append(rec["prevention_title"])
        
        # Mettre à jour les seuils dans les recommandations
        prevention_items = []
        for item in rec["prevention_items"]:
            if "50 Gy" in item and "30-50 Gy" in item:
                # Remplacer les seuils par défaut par les seuils temporaires
                item = item.replace("50 Gy", f"{self.temp_risk_config['moderate_threshold']:.0f} Gy")
                item = item.replace("30-50 Gy", f"{self.temp_risk_config['low_threshold']:.0f}-{self.temp_risk_config['moderate_threshold']:.0f} Gy")
            prevention_items.append(item)
        
        lines.extend(prevention_items)
        lines.append("")
        lines.append(rec["contact_title"]) 
        lines.extend(rec["contact_items"])
        
        return lines


# Fonction d'intégration pour le viewer principal
def add_report_button_to_tooth_panel(tooth_panel, ct_viewer):
    """Ajoute le bouton de rapport au panel dentaire existant"""
    try:
        # Trouver le frame d'export ou de gestion
        for child in tooth_panel.tooth_frame.winfo_children():
            if isinstance(child, ttk.LabelFrame) and "Export" in child.cget("text"):
                export_frame = child
                break
        else:
            # Créer un nouveau frame d'export
            export_frame = ttk.LabelFrame(tooth_panel.tooth_frame, text="Export et rapports", padding=10)
            export_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Ajouter le bouton de rapport
        report_btn = ttk.Button(
            export_frame,
            text="📊 Générer rapport dosimétrique",
            command=lambda: DoseReportGenerator(ct_viewer).show_report_dialog()
        )
        report_btn.pack(fill=tk.X, pady=2)
        
        logger.info("Bouton de rapport dosimétrique ajouté au panel dentaire")
        
    except Exception as e:
        logger.error(f"Erreur ajout bouton rapport: {e}")