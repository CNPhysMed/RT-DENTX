#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fonction d'intégration pour ajouter le bouton de configuration du rapport
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging

logger = logging.getLogger(__name__)

def add_report_config_button_to_tooth_panel(tooth_panel, ct_viewer):
    """Ajoute le bouton de configuration du rapport au panel dentaire"""
    try:
        # Trouver ou créer le frame de gestion
        management_frame = None
        for child in tooth_panel.tooth_frame.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                label_text = child.cget("text")
                if "Gestion" in label_text or "Management" in label_text or "Configuration" in label_text:
                    management_frame = child
                    break
        
        if not management_frame:
            # Créer un nouveau frame de gestion
            management_frame = ttk.LabelFrame(tooth_panel.tooth_frame, text="Configuration et gestion", padding=10)
            management_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Ajouter le bouton de configuration
        config_btn = ttk.Button(
            management_frame,
            text="⚙️ Configuration du rapport dosimétrique",
            command=lambda: open_report_config(ct_viewer)
        )
        config_btn.pack(fill=tk.X, pady=2)
        
        logger.info("Bouton de configuration du rapport ajouté au panel dentaire")
        
    except Exception as e:
        logger.error(f"Erreur ajout bouton configuration: {e}")

def open_report_config(ct_viewer):
    """Ouvre le dialogue de configuration du rapport"""
    try:
        from report_config_dialog import ReportConfigDialog
        
        config_dialog = ReportConfigDialog(ct_viewer.root, ct_viewer)
        config_dialog.show()
        
    except ImportError:
        messagebox.showerror(
            "Module manquant",
            "Le module de configuration du rapport n'est pas disponible.\n"
            "Assurez-vous que report_config_dialog.py est présent."
        )
    except Exception as e:
        messagebox.showerror(
            "Erreur",
            f"Impossible d'ouvrir la configuration:\n{str(e)}"
        )
        logger.error(f"Erreur ouverture configuration: {e}")

# Fonction complète d'intégration
def integrate_report_system(tooth_panel, ct_viewer):
    """Intègre le système complet de rapport dosimétrique"""
    try:
        # Frame principal pour les rapports
        report_frame = ttk.LabelFrame(tooth_panel.tooth_frame, text="📊 Rapports dosimétriques", padding=10)
        report_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Bouton de configuration
        config_btn = ttk.Button(
            report_frame,
            text="⚙️ Configuration du rapport dosimétrique",
            command=lambda: open_report_config(ct_viewer)
        )
        config_btn.pack(fill=tk.X, pady=(0, 5))
        
        # Bouton de génération
        from dose_report_generator import DoseReportGenerator
        
        generate_btn = ttk.Button(
            report_frame,
            text="📄 Générer rapport dosimétrique",
            command=lambda: DoseReportGenerator(ct_viewer).show_report_dialog()
        )
        generate_btn.pack(fill=tk.X, pady=(0, 2))
        
        # Note d'information
        info_text = "Configurez d'abord les seuils et recommandations,\npuis générez le rapport avec aperçu."
        tk.Label(report_frame, text=info_text, font=('Arial', 8, 'italic'), 
                justify=tk.CENTER, fg='#666666').pack(pady=(5, 0))
        
        logger.info("Système de rapport dosimétrique intégré avec succès")
        
    except Exception as e:
        logger.error(f"Erreur intégration système rapport: {e}")
        messagebox.showerror(
            "Erreur d'intégration",
            f"Impossible d'intégrer le système de rapport:\n{str(e)}"
        )