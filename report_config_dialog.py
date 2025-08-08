#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialogue de configuration pour le rapport dosimétrique
Gère les seuils de risque et les recommandations cliniques
© 2025 Caroline Moreau-Noblet — RT-DENTX — Licence BSD 3-Clause
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
from pathlib import Path
import logging
import copy

logger = logging.getLogger(__name__)

class ReportConfigDialog:
    """Dialogue de configuration du rapport dosimétrique"""
    
    # Configuration par défaut
    DEFAULT_CONFIG = {
        "risk_levels": {
            "low_threshold": 30.0,
            "moderate_threshold": 50.0,
            "low_label": "Faible",
            "moderate_label": "Modéré",
            "high_label": "Élevé",
            "low_description": "Risque d'ostéoradionécrose faible",
            "moderate_description": "Risque d'ostéoradionécrose modéré",
            "high_description": "Risque d'ostéoradionécrose élevé"
        },
        "recommendations": """Recommandations cliniques

PRÉVENTION DE L'OSTÉORADIONÉCROSE :

• Des précautions particulières doivent être prises lors des soins bucco-dentaires,
  en particulier en cas d'avulsion ou d'un autre geste chirurgical en territoire irradié.

• Surveillance clinique renforcée pour les dents ayant reçu > {moderate_threshold} Gy (risque élevé)
  et entre {low_threshold}-{moderate_threshold} Gy (risque modéré).

• Maintien d'une hygiène bucco-dentaire optimale.

• Fluorothérapie quotidienne recommandée.

CONTACT :

En cas de doute, veuillez prendre contact avec :
• Le radiothérapeute référent, ou
• Le service d'odontologie ou de chirurgie maxillofaciale du CHU le plus proche."""
    }
    
    def __init__(self, parent, ct_viewer):
        self.parent = parent
        self.ct_viewer = ct_viewer
        self.dialog = None
        
        # Configuration temporaire pour cette session
        self.session_config = None
        
        # Charger la configuration existante ou utiliser les valeurs par défaut
        self._load_current_config()
    
    def _load_current_config(self):
        """Charge la configuration actuelle"""
        try:
            # D'abord essayer de récupérer la config de session si elle existe
            if hasattr(self.ct_viewer, '_report_session_config') and self.ct_viewer._report_session_config:
                self.current_config = self.ct_viewer._report_session_config.copy()
                logger.info("Configuration de session chargée")
            else:
                # Sinon, essayer ConfigManager
                try:
                    from config_manager import ConfigManager
                    cm = ConfigManager()
                    
                    # Utiliser get_simplified_config qui retourne le bon format
                    simple_config = cm.get_simplified_config()
                    
                    self.current_config = {
                        "risk_levels": simple_config["risk_levels"],
                        "recommendations": simple_config["recommendations_text"] or self.DEFAULT_CONFIG["recommendations"]
                    }
                    
                except Exception as e:
                    logger.warning(f"ConfigManager non disponible: {e}")
                    # Utiliser la configuration par défaut
                    self.current_config = self._get_default_config()
                    
        except Exception as e:
            logger.warning(f"Erreur chargement config: {e}")
            self.current_config = self._get_default_config()
    
    def _get_default_config(self):
        """Retourne une copie de la configuration par défaut"""
        return {
            "risk_levels": self.DEFAULT_CONFIG["risk_levels"].copy(),
            "recommendations": self.DEFAULT_CONFIG["recommendations"]
        }
    
    def _convert_recommendations_to_text(self, rec_dict):
        """Convertit le format dictionnaire des recommandations en texte"""
        if not rec_dict or not isinstance(rec_dict, dict):
            return self.DEFAULT_CONFIG["recommendations"]
        
        try:
            lines = []
            if "title" in rec_dict:
                lines.append(rec_dict["title"])
                lines.append("")
            
            if "prevention_title" in rec_dict:
                lines.append(rec_dict["prevention_title"])
                lines.append("")
            
            if "prevention_items" in rec_dict:
                for item in rec_dict["prevention_items"]:
                    lines.append(item)
            
            if "contact_title" in rec_dict:
                lines.append("")
                lines.append(rec_dict["contact_title"])
                lines.append("")
            
            if "contact_items" in rec_dict:
                for item in rec_dict["contact_items"]:
                    lines.append(item)
            
            text = "\n".join(lines)
            
            # Remplacer les placeholders des seuils
            risk = self.current_config.get("risk_levels", self.DEFAULT_CONFIG["risk_levels"])
            text = text.replace("50 Gy", "{moderate_threshold} Gy")
            text = text.replace("30-50 Gy", "{low_threshold}-{moderate_threshold} Gy")
            
            return text if text.strip() else self.DEFAULT_CONFIG["recommendations"]
            
        except:
            return self.DEFAULT_CONFIG["recommendations"]
    
    def show(self):
        """Affiche le dialogue de configuration"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("⚙️ Configuration du rapport dosimétrique")
        self.dialog.geometry("800x900")
        
        # Frame principal
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Créer les sections
        self._create_threshold_section(main_frame)
        self._create_recommendations_section(main_frame)
        self._create_button_section(main_frame)
        
        # Centrer la fenêtre
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Charger les valeurs actuelles
        self._load_values()
    
    def _create_threshold_section(self, parent):
        """Crée la section des seuils de risque"""
        frame = ttk.LabelFrame(parent, text="Seuils de risque (Gy)", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        # Grid pour les seuils
        grid_frame = ttk.Frame(frame)
        grid_frame.pack(fill=tk.X)
        
        # Seuil faible
        ttk.Label(grid_frame, text="Seuil risque faible (<):").grid(row=0, column=0, sticky='w', padx=(0, 10), pady=5)
        self.low_threshold_var = tk.DoubleVar()
        self.low_threshold_spin = ttk.Spinbox(grid_frame, from_=1.0, to=100.0, increment=1.0,
                                             textvariable=self.low_threshold_var, width=10)
        self.low_threshold_spin.grid(row=0, column=1, sticky='w', pady=5)
        ttk.Label(grid_frame, text="Gy").grid(row=0, column=2, sticky='w', padx=(5, 20), pady=5)
        
        # Seuil modéré
        ttk.Label(grid_frame, text="Seuil risque modéré (<):").grid(row=0, column=3, sticky='w', padx=(0, 10), pady=5)
        self.moderate_threshold_var = tk.DoubleVar()
        self.moderate_threshold_spin = ttk.Spinbox(grid_frame, from_=1.0, to=100.0, increment=1.0,
                                                  textvariable=self.moderate_threshold_var, width=10)
        self.moderate_threshold_spin.grid(row=0, column=4, sticky='w', pady=5)
        ttk.Label(grid_frame, text="Gy").grid(row=0, column=5, sticky='w', padx=(5, 0), pady=5)
        
        # Labels des niveaux
        labels_frame = ttk.Frame(frame)
        labels_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(labels_frame, text="Labels des niveaux de risque:", font=('Arial', 10, 'bold')).pack(anchor='w')
        
        labels_grid = ttk.Frame(labels_frame)
        labels_grid.pack(fill=tk.X, pady=(5, 0))
        
        # Label faible
        ttk.Label(labels_grid, text="Faible:").grid(row=0, column=0, sticky='w', padx=(20, 10), pady=2)
        self.low_label_var = tk.StringVar()
        ttk.Entry(labels_grid, textvariable=self.low_label_var, width=15).grid(row=0, column=1, sticky='w', pady=2)
        
        # Label modéré
        ttk.Label(labels_grid, text="Modéré:").grid(row=1, column=0, sticky='w', padx=(20, 10), pady=2)
        self.moderate_label_var = tk.StringVar()
        ttk.Entry(labels_grid, textvariable=self.moderate_label_var, width=15).grid(row=1, column=1, sticky='w', pady=2)
        
        # Label élevé
        ttk.Label(labels_grid, text="Élevé:").grid(row=2, column=0, sticky='w', padx=(20, 10), pady=2)
        self.high_label_var = tk.StringVar()
        ttk.Entry(labels_grid, textvariable=self.high_label_var, width=15).grid(row=2, column=1, sticky='w', pady=2)
        
        # Descriptions
        desc_frame = ttk.Frame(frame)
        desc_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(desc_frame, text="Descriptions:", font=('Arial', 10, 'bold')).pack(anchor='w')
        
        desc_grid = ttk.Frame(desc_frame)
        desc_grid.pack(fill=tk.X, pady=(5, 0))
        
        # Description faible
        ttk.Label(desc_grid, text="Faible:").grid(row=0, column=0, sticky='w', padx=(20, 10), pady=2)
        self.low_desc_var = tk.StringVar()
        ttk.Entry(desc_grid, textvariable=self.low_desc_var, width=40).grid(row=0, column=1, sticky='w', pady=2)
        
        # Description modérée
        ttk.Label(desc_grid, text="Modéré:").grid(row=1, column=0, sticky='w', padx=(20, 10), pady=2)
        self.moderate_desc_var = tk.StringVar()
        ttk.Entry(desc_grid, textvariable=self.moderate_desc_var, width=40).grid(row=1, column=1, sticky='w', pady=2)
        
        # Description élevée
        ttk.Label(desc_grid, text="Élevé:").grid(row=2, column=0, sticky='w', padx=(20, 10), pady=2)
        self.high_desc_var = tk.StringVar()
        ttk.Entry(desc_grid, textvariable=self.high_desc_var, width=40).grid(row=2, column=1, sticky='w', pady=2)
    
    def _create_recommendations_section(self, parent):
        """Crée la section des recommandations"""
        frame = ttk.LabelFrame(parent, text="Recommandations cliniques", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Note d'information
        info_label = ttk.Label(frame, 
                             text="Utilisez {low_threshold} et {moderate_threshold} pour insérer automatiquement les seuils",
                             font=('Arial', 9, 'italic'))
        info_label.pack(anchor='w', pady=(0, 5))
        
        # Zone de texte avec scrollbar
        self.recommendations_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=15)
        self.recommendations_text.pack(fill=tk.BOTH, expand=True)
        
        # Boutons pour les recommandations
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(btn_frame, text="↺ Défaut", 
                  command=self._reset_recommendations).pack(side=tk.LEFT, padx=(0, 5))
    
    def _create_button_section(self, parent):
        """Crée la section des boutons"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X)
        
        # Note importante
        note_frame = tk.Frame(frame)
        note_frame.pack(fill=tk.X, pady=(0, 10))
        
        note_text = """⚠️ Pour modifier les seuils et recommandations, utilisez cette fenêtre de configuration.
Les modifications seront visibles dans l'aperçu lors de la génération du rapport."""
        
        tk.Label(note_frame, text=note_text, font=('Arial', 9, 'italic'), 
                justify=tk.LEFT, fg='#666666').pack(anchor=tk.W)
        
        # Boutons à gauche
        left_frame = ttk.Frame(frame)
        left_frame.pack(side=tk.LEFT)
        
        ttk.Button(left_frame, text="↺ Tout réinitialiser", 
                  command=self._reset_all).pack(side=tk.LEFT, padx=(0, 5))
        
        # Boutons à droite
        right_frame = ttk.Frame(frame)
        right_frame.pack(side=tk.RIGHT)
        
        ttk.Button(right_frame, text="Annuler", 
                  command=self.dialog.destroy).pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(right_frame, text="💾 Enregistrer pour la session", 
                  command=self._save_session).pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(right_frame, text="💾 Enregistrer définitivement", 
                  command=self._save_permanent).pack(side=tk.LEFT, padx=(5, 0))
    
    def _load_values(self):
        """Charge les valeurs actuelles dans l'interface"""
        risk = self.current_config["risk_levels"]
        
        # Seuils
        self.low_threshold_var.set(risk["low_threshold"])
        self.moderate_threshold_var.set(risk["moderate_threshold"])
        
        # Labels
        self.low_label_var.set(risk["low_label"])
        self.moderate_label_var.set(risk["moderate_label"])
        self.high_label_var.set(risk["high_label"])
        
        # Descriptions
        self.low_desc_var.set(risk["low_description"])
        self.moderate_desc_var.set(risk["moderate_description"])
        self.high_desc_var.set(risk["high_description"])
        
        # Recommandations
        rec_text = self.current_config.get("recommendations", "")
        # S'assurer qu'on n'affiche jamais 'None' ou une chaîne vide
        if not rec_text or rec_text == "None" or rec_text.strip() == "":
            rec_text = self.DEFAULT_CONFIG["recommendations"]
        self.recommendations_text.delete('1.0', tk.END)
        self.recommendations_text.insert('1.0', rec_text)
    
    def _get_config_from_ui(self):
        """Récupère la configuration depuis l'interface"""
        return {
            "risk_levels": {
                "low_threshold": self.low_threshold_var.get(),
                "moderate_threshold": self.moderate_threshold_var.get(),
                "low_label": self.low_label_var.get(),
                "moderate_label": self.moderate_label_var.get(),
                "high_label": self.high_label_var.get(),
                "low_description": self.low_desc_var.get(),
                "moderate_description": self.moderate_desc_var.get(),
                "high_description": self.high_desc_var.get()
            },
            "recommendations": self.recommendations_text.get('1.0', 'end-1c')
        }
    
    def _validate_config(self, config):
        """Valide la configuration"""
        risk = config["risk_levels"]
        
        # Vérifier les seuils
        if risk["low_threshold"] >= risk["moderate_threshold"]:
            messagebox.showerror("Erreur", "Le seuil faible doit être inférieur au seuil modéré")
            return False
        
        if risk["low_threshold"] <= 0 or risk["moderate_threshold"] <= 0:
            messagebox.showerror("Erreur", "Les seuils doivent être positifs")
            return False
        
        # Vérifier les labels
        for key in ["low_label", "moderate_label", "high_label"]:
            if not risk[key].strip():
                messagebox.showerror("Erreur", "Tous les labels doivent être renseignés")
                return False
        
        return True
    
    def _save_session(self):
        """Enregistre la configuration pour cette session uniquement"""
        config = self._get_config_from_ui()
        
        if not self._validate_config(config):
            return
        
        # Stocker dans le viewer pour cette session
        self.ct_viewer._report_session_config = config
        
        messagebox.showinfo("Succès", 
                          "Configuration enregistrée pour cette session.\n"
                          "Elle sera utilisée pour les rapports générés maintenant.")
        
        self.dialog.destroy()
    
    def _save_permanent(self):
        """Enregistre la configuration de manière permanente"""
        config = self._get_config_from_ui()
        
        if not self._validate_config(config):
            return
        
        try:
            # Utiliser ConfigManager directement
            from config_manager import ConfigManager
            cm = ConfigManager()
            
            # Format simple pour ConfigManager (PAS de conversion complexe)
            cm_config = {
                "risk_levels": config["risk_levels"],
                "recommendations_text": config["recommendations"]  # Texte simple !
            }
            
            # Sauvegarder via ConfigManager
            cm.update_persistent_config(cm_config)
            
            # Aussi stocker pour la session
            self.ct_viewer._report_session_config = config
            
            messagebox.showinfo("Succès", 
                              f"Configuration enregistrée définitivement.\n"
                              f"Fichier: {cm.config_file}")
            
        except Exception as e:
            messagebox.showerror("Erreur", 
                               f"Impossible d'enregistrer la configuration:\n{str(e)}")
            logger.error(f"Erreur sauvegarde config: {e}")
        
        self.dialog.destroy()
    
    
    def _load_config_from_manager(self):
        """Charge la configuration depuis ConfigManager - VERSION CORRIGÉE"""
        try:
            if self.config_manager:
                # Récupérer la configuration complète
                full_config = self.config_manager.get_simplified_config()
                
                # Construire la structure attendue par le dialogue
                self.current_config = {
                    "risk_levels": full_config["risk_levels"],
                    "recommendations": full_config.get("recommendations_text", "") or self.DEFAULT_CONFIG["recommendations"]
                }
                
                logger.info("Configuration chargée depuis ConfigManager")
                
            else:
                # Mode fallback
                self.current_config = copy.deepcopy(self.DEFAULT_CONFIG)
                
                # Essayer de charger depuis le fichier
                config_file = Path.home() / '.rt_dentx' / 'report_config.json'
                if config_file.exists():
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            saved_config = json.load(f)
                        
                        # Appliquer les valeurs sauvegardées
                        if "risk_levels" in saved_config:
                            self.current_config["risk_levels"].update(saved_config["risk_levels"])
                        
                        if "recommendations_text" in saved_config:
                            self.current_config["recommendations"] = saved_config["recommendations_text"]
                        
                        logger.info(f"Configuration chargée depuis {config_file}")
                        
                    except Exception as e:
                        logger.warning(f"Impossible de charger la config: {e}")
                        
        except Exception as e:
            logger.error(f"Erreur chargement config: {e}")
            self.current_config = copy.deepcopy(self.DEFAULT_CONFIG)
    
    def _convert_to_config_manager_format(self, config):
        """Convertit vers le format ConfigManager"""
        # Parser les recommandations
        rec_text = config["recommendations"]
        lines = rec_text.split('\n')
        
        # Structure pour ConfigManager
        cm_config = {
            "risk_levels": config["risk_levels"],
            "recommendations": {
                "title": "Recommandations cliniques",
                "prevention_title": "PRÉVENTION DE L'OSTÉORADIONÉCROSE :",
                "prevention_items": [],
                "contact_title": "CONTACT :",
                "contact_items": []
            }
        }
        
        # Parser les lignes
        current_section = None
        for line in lines:
            if "PRÉVENTION" in line:
                current_section = "prevention"
            elif "CONTACT" in line:
                current_section = "contact"
            elif line.strip() and current_section:
                if current_section == "prevention":
                    cm_config["recommendations"]["prevention_items"].append(line)
                elif current_section == "contact":
                    cm_config["recommendations"]["contact_items"].append(line)
        
        return cm_config
    
    def _reset_recommendations(self):
        """Réinitialise les recommandations par défaut"""
        self.recommendations_text.delete('1.0', tk.END)
        self.recommendations_text.insert('1.0', self.DEFAULT_CONFIG["recommendations"])
    
    def _reset_all(self):
        """Réinitialise toute la configuration"""
        if messagebox.askyesno("Confirmation", 
                             "Réinitialiser toute la configuration aux valeurs par défaut?"):
            self.current_config = self._get_default_config()
            self._load_values()
    
    def _preview_recommendations(self):
        """Aperçu des recommandations avec les seuils actuels"""
        config = self._get_config_from_ui()
        risk = config["risk_levels"]
        
        # Remplacer les placeholders
        text = config["recommendations"]
        text = text.replace("{low_threshold}", f"{risk['low_threshold']:.0f}")
        text = text.replace("{moderate_threshold}", f"{risk['moderate_threshold']:.0f}")
        
        # Afficher dans une nouvelle fenêtre
        preview = tk.Toplevel(self.dialog)
        preview.title("Aperçu des recommandations")
        preview.geometry("600x500")
        
        text_widget = scrolledtext.ScrolledText(preview, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert('1.0', text)
        text_widget.config(state='disabled')
        
        ttk.Button(preview, text="Fermer", 
                  command=preview.destroy).pack(pady=10)