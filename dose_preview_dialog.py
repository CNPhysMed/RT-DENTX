#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialogue de prévisualisation des doses dentaires calculées
Affichage sous forme de tableau avec couleurs selon les seuils de risque
© 2025 Caroline Moreau-Noblet — RT-DENTX — Licence BSD 3-Clause
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QTableWidget, QTableWidgetItem,
                           QHeaderView, QGroupBox, QTextEdit, QTabWidget,
                           QWidget, QMessageBox, QCheckBox, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
import json

class DosePreviewDialog(QDialog):
    """Dialogue de prévisualisation des doses dentaires"""
    
    def __init__(self, doses_data, parent=None):
        super().__init__(parent)
        self.doses_data = doses_data
        
        # CORRECTION : Charger le ConfigManager directement
        try:
            from config_manager import ConfigManager
            self.config_manager = ConfigManager()
        except ImportError:
            self.config_manager = None
            print("[ATTENTION] ConfigManager non disponible dans DosePreviewDialog")
        
        self.setWindowTitle("Prévisualisation des doses dentaires")
        self.setModal(True)
        self.resize(900, 700)
        
        # Appliquer le style sombre
        self.setStyleSheet("""
            QDialog {
                background-color: #363636;
                color: #e0e0e0;
            }
            QTabWidget::pane {
                border: 1px solid #505050;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #505050;
                color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #505050;
                border-radius: 6px;
                margin-top: 1ex;
                padding-top: 12px;
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: #3498db;
                background-color: #2b2b2b;
            }
            QLabel {
                color: #e0e0e0;
            }
            QTableWidget {
                background-color: #404040;
                border: 1px solid #606060;
                border-radius: 4px;
                gridline-color: #606060;
                selection-background-color: #3498db;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QHeaderView::section {
                background-color: #505050;
                color: #e0e0e0;
                padding: 8px;
                border: 1px solid #606060;
                font-weight: bold;
            }
            QPushButton {
                background-color: #3498db;
                border: 1px solid #2980b9;
                border-radius: 4px;
                padding: 8px 16px;
                color: white;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f5f8b;
            }
            QTextEdit {
                background-color: #404040;
                border: 1px solid #606060;
                border-radius: 4px;
                color: #e0e0e0;
            }
            QComboBox {
                background-color: #404040;
                border: 1px solid #606060;
                border-radius: 4px;
                padding: 4px;
                color: #e0e0e0;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
            QCheckBox {
                color: #e0e0e0;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #606060;
                border-radius: 3px;
                background-color: #404040;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #2980b9;
            }
        """)
        
        self.init_ui()
        self.populate_data()
        
        self.init_ui()
        self.populate_data()
        
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Titre
        title = QLabel("Prévisualisation des doses dentaires calculées")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #3498db; margin: 10px;")
        layout.addWidget(title)
        
        # Statistiques générales
        self.create_stats_section(layout)
        
        # Onglets pour les différents types de données
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Onglet Dents complètes
        self.create_complete_teeth_tab(tab_widget)
        
        # Onglet Couronnes
        self.create_crowns_tab(tab_widget)
        
        # Onglet Racines
        self.create_roots_tab(tab_widget)
        
        # Onglet Résumé par risque
        self.create_risk_summary_tab(tab_widget)
        
        # Boutons de contrôle
        self.create_control_buttons(layout)
    
    def create_stats_section(self, layout):
        """Crée la section des statistiques générales - VERSION CORRIGÉE"""
        stats_group = QGroupBox("Statistiques générales")
        stats_layout = QHBoxLayout(stats_group)
        
        # Compter les données
        complete_count = len(self.doses_data.get('complete', {}))
        crown_count = len(self.doses_data.get('couronne', {}))
        root_count = len(self.doses_data.get('racine', {}))
        
        # Calculer min/max/moyenne
        all_doses = list(self.doses_data.get('complete', {}).values())
        if all_doses:
            min_dose = min(all_doses)
            max_dose = max(all_doses)
            avg_dose = sum(all_doses) / len(all_doses)
        else:
            min_dose = max_dose = avg_dose = 0
        
        # Affichage des statistiques
        stats_text = f"""Dents analysées: {complete_count}
    Couronnes: {crown_count} | Racines: {root_count}
    
    Dose minimale: {min_dose:.1f} Gy
    Dose maximale: {max_dose:.1f} Gy  
    Dose moyenne: {avg_dose:.1f} Gy"""
        
        stats_label = QLabel(stats_text)
        stats_label.setStyleSheet("font-family: monospace; font-size: 12px; padding: 10px;")
        stats_layout.addWidget(stats_label)
        
        # CORRECTION : Graphique de répartition avec gestion d'erreur
        if self.config_manager and all_doses:
            try:
                risk_counts = self.calculate_risk_distribution()
                risk_text = f"""Répartition des risques:
    • Faible: {risk_counts['low']} dents
    • Modéré: {risk_counts['moderate']} dents
    • Élevé: {risk_counts['high']} dents"""
                
                risk_label = QLabel(risk_text)
                risk_label.setStyleSheet("font-family: monospace; font-size: 12px; padding: 10px; border-left: 2px solid #3498db; margin-left: 20px;")
                stats_layout.addWidget(risk_label)
            except Exception as e:
                print(f"[ERREUR] Calcul répartition risques: {e}")
                # Afficher quand même les statistiques de base
                risk_label = QLabel("Répartition des risques:\nConfiguration non disponible")
                risk_label.setStyleSheet("font-family: monospace; font-size: 12px; padding: 10px; border-left: 2px solid #e74c3c; margin-left: 20px;")
                stats_layout.addWidget(risk_label)
        
        layout.addWidget(stats_group)
    
    def create_complete_teeth_tab(self, tab_widget):
        """Crée l'onglet des dents complètes"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Options d'affichage
        options_layout = QHBoxLayout()
        
        self.complete_sort_combo = QComboBox()
        self.complete_sort_combo.addItems([
            "Numéro de dent", "Dose croissante", "Dose décroissante", "Niveau de risque"
        ])
        self.complete_sort_combo.currentTextChanged.connect(self.update_complete_table)
        
        options_layout.addWidget(QLabel("Trier par:"))
        options_layout.addWidget(self.complete_sort_combo)
        options_layout.addStretch()
        
        layout.addLayout(options_layout)
        
        # Tableau
        self.complete_table = QTableWidget()
        self.complete_table.setColumnCount(4)
        self.complete_table.setHorizontalHeaderLabels([
            "Dent", "Dose (Gy)", "Niveau de risque", "Description"
        ])
        
        # Ajuster les colonnes
        header = self.complete_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        
        layout.addWidget(self.complete_table)
        
        tab_widget.addTab(tab, "Dents complètes")
    
    def create_crowns_tab(self, tab_widget):
        """Crée l'onglet des couronnes"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Options
        options_layout = QHBoxLayout()
        
        self.crown_sort_combo = QComboBox()
        self.crown_sort_combo.addItems([
            "Numéro de dent", "Dose croissante", "Dose décroissante"
        ])
        self.crown_sort_combo.currentTextChanged.connect(self.update_crown_table)
        
        options_layout.addWidget(QLabel("Trier par:"))
        options_layout.addWidget(self.crown_sort_combo)
        options_layout.addStretch()
        
        layout.addLayout(options_layout)
        
        # Tableau
        self.crown_table = QTableWidget()
        self.crown_table.setColumnCount(3)
        self.crown_table.setHorizontalHeaderLabels([
            "Dent", "Dose couronne (Gy)", "Niveau de risque"
        ])
        
        header = self.crown_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        layout.addWidget(self.crown_table)
        
        tab_widget.addTab(tab, "Couronnes")
    
    def create_roots_tab(self, tab_widget):
        """Crée l'onglet des racines"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Options
        options_layout = QHBoxLayout()
        
        self.root_sort_combo = QComboBox()
        self.root_sort_combo.addItems([
            "Numéro de dent", "Dose croissante", "Dose décroissante"
        ])
        self.root_sort_combo.currentTextChanged.connect(self.update_root_table)
        
        options_layout.addWidget(QLabel("Trier par:"))
        options_layout.addWidget(self.root_sort_combo)
        options_layout.addStretch()
        
        layout.addLayout(options_layout)
        
        # Tableau
        self.root_table = QTableWidget()
        self.root_table.setColumnCount(3)
        self.root_table.setHorizontalHeaderLabels([
            "Dent", "Dose racine (Gy)", "Niveau de risque"
        ])
        
        header = self.root_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        layout.addWidget(self.root_table)
        
        tab_widget.addTab(tab, "Racines")
    
    def create_risk_summary_tab(self, tab_widget):
        """Crée l'onglet de résumé par niveau de risque - VERSION CORRIGÉE"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        if not self.config_manager:
            # CORRECTION : Message plus informatif si pas de configuration
            no_config_label = QLabel("⚠️ ConfigManager non disponible\nUtilisation des seuils par défaut (30 et 50 Gy)")
            no_config_label.setStyleSheet("color: #f39c12; font-weight: bold; padding: 20px;")
            layout.addWidget(no_config_label)
        
        # Calculer la répartition par risque
        try:
            risk_data = self.calculate_detailed_risk_data()
            
            # Créer les groupes par niveau de risque
            for risk_level, data in risk_data.items():
                if data['teeth']:
                    group = QGroupBox(f"{data['label']} ({len(data['teeth'])} dents)")
                    group.setStyleSheet(f"QGroupBox::title {{ color: {data['color']}; }}")
                    group_layout = QVBoxLayout(group)
                    
                    # Liste des dents
                    teeth_text = f"Seuil: {data['description']}\n\n"
                    teeth_text += "Dents concernées:\n"
                    
                    sorted_teeth = sorted(data['teeth'], key=lambda x: float(x[0]))
                    for tooth, dose in sorted_teeth:
                        teeth_text += f"• Dent {tooth}: {dose:.1f} Gy\n"
                    
                    teeth_label = QLabel(teeth_text)
                    teeth_label.setStyleSheet("font-family: monospace; padding: 10px;")
                    teeth_label.setWordWrap(True)
                    group_layout.addWidget(teeth_label)
                    
                    layout.addWidget(group)
            
            layout.addStretch()
        except Exception as e:
            error_label = QLabel(f"Erreur lors du calcul des risques:\n{str(e)}")
            error_label.setStyleSheet("color: #e74c3c; padding: 20px;")
            layout.addWidget(error_label)
        
        tab_widget.addTab(tab, "Résumé par risque")
    
    def create_control_buttons(self, layout):
        """Crée les boutons de contrôle"""
        buttons_layout = QHBoxLayout()
        
        # Bouton Export CSV
        export_csv_button = QPushButton("Exporter CSV")
        export_csv_button.clicked.connect(self.export_to_csv)
        buttons_layout.addWidget(export_csv_button)
        
        # Bouton Statistiques détaillées
        stats_button = QPushButton("Statistiques détaillées")
        stats_button.clicked.connect(self.show_detailed_stats)
        buttons_layout.addWidget(stats_button)
        
        buttons_layout.addStretch()
        
        # Bouton Fermer
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.reject)
        buttons_layout.addWidget(close_button)
        
        # Bouton Générer rapport PDF
        pdf_button = QPushButton("Générer rapport PDF")
        pdf_button.setStyleSheet("background-color: #27ae60; border-color: #229954;")
        pdf_button.clicked.connect(self.accept)  # Ferme le dialogue avec code accepted
        buttons_layout.addWidget(pdf_button)
        
        layout.addLayout(buttons_layout)
    
    def populate_data(self):
        """Remplit les tableaux avec les données"""
        self.update_complete_table()
        self.update_crown_table()
        self.update_root_table()
    
    def update_complete_table(self):
        """Met à jour le tableau des dents complètes"""
        data = self.doses_data.get('complete', {})
        sort_method = self.complete_sort_combo.currentText()
        
        # Préparer les données
        rows = []
        for tooth, dose in data.items():
            risk_info = self.get_risk_info(dose)
            rows.append([tooth, dose, risk_info])
        
        # Trier selon la méthode choisie
        if sort_method == "Numéro de dent":
            rows.sort(key=lambda x: int(x[0]))
        elif sort_method == "Dose croissante":
            rows.sort(key=lambda x: x[1])
        elif sort_method == "Dose décroissante":  
            rows.sort(key=lambda x: x[1], reverse=True)
        elif sort_method == "Niveau de risque":
            # Trier par niveau de risque puis par dose
            risk_order = {'high': 0, 'moderate': 1, 'low': 2}
            rows.sort(key=lambda x: (risk_order.get(x[2]['level'], 3), -x[1]))
        
        # Remplir le tableau
        self.complete_table.setRowCount(len(rows))
        
        for i, (tooth, dose, risk_info) in enumerate(rows):
            # Numéro de dent
            tooth_item = QTableWidgetItem(str(tooth))
            tooth_item.setTextAlignment(Qt.AlignCenter)
            self.complete_table.setItem(i, 0, tooth_item)
            
            # Dose
            dose_item = QTableWidgetItem(f"{dose:.1f}")
            dose_item.setTextAlignment(Qt.AlignCenter)
            self.complete_table.setItem(i, 1, dose_item)
            
            # Niveau de risque
            risk_item = QTableWidgetItem(risk_info['label'])
            risk_item.setTextAlignment(Qt.AlignCenter)
            if 'color' in risk_info:
                risk_item.setBackground(QColor(risk_info['color']))
                if risk_info['level'] == 'high':
                    risk_item.setForeground(QColor('white'))
            self.complete_table.setItem(i, 2, risk_item)
            
            # Description
            desc_item = QTableWidgetItem(risk_info['description'])
            self.complete_table.setItem(i, 3, desc_item)
    
    def update_crown_table(self):
        """Met à jour le tableau des couronnes"""
        data = self.doses_data.get('couronne', {})
        sort_method = self.crown_sort_combo.currentText()
        
        # Préparer les données
        rows = []
        for tooth, dose in data.items():
            risk_info = self.get_risk_info(dose)
            rows.append([tooth, dose, risk_info])
        
        # Trier
        if sort_method == "Numéro de dent":
            rows.sort(key=lambda x: int(x[0]))
        elif sort_method == "Dose croissante":
            rows.sort(key=lambda x: x[1])
        elif sort_method == "Dose décroissante":
            rows.sort(key=lambda x: x[1], reverse=True)
        
        # Remplir le tableau
        self.crown_table.setRowCount(len(rows))
        
        for i, (tooth, dose, risk_info) in enumerate(rows):
            # Numéro de dent
            tooth_item = QTableWidgetItem(str(tooth))
            tooth_item.setTextAlignment(Qt.AlignCenter)
            self.crown_table.setItem(i, 0, tooth_item)
            
            # Dose
            dose_item = QTableWidgetItem(f"{dose:.1f}")
            dose_item.setTextAlignment(Qt.AlignCenter)
            self.crown_table.setItem(i, 1, dose_item)
            
            # Niveau de risque
            risk_item = QTableWidgetItem(risk_info['label'])
            risk_item.setTextAlignment(Qt.AlignCenter)
            if 'color' in risk_info:
                risk_item.setBackground(QColor(risk_info['color']))
                if risk_info['level'] == 'high':
                    risk_item.setForeground(QColor('white'))
            self.crown_table.setItem(i, 2, risk_item)
    
    def update_root_table(self):
        """Met à jour le tableau des racines"""
        data = self.doses_data.get('racine', {})
        sort_method = self.root_sort_combo.currentText()
        
        # Préparer les données
        rows = []
        for tooth, dose in data.items():
            risk_info = self.get_risk_info(dose)
            rows.append([tooth, dose, risk_info])
        
        # Trier
        if sort_method == "Numéro de dent":
            rows.sort(key=lambda x: int(x[0]))
        elif sort_method == "Dose croissante":
            rows.sort(key=lambda x: x[1])
        elif sort_method == "Dose décroissante":
            rows.sort(key=lambda x: x[1], reverse=True)
        
        # Remplir le tableau
        self.root_table.setRowCount(len(rows))
        
        for i, (tooth, dose, risk_info) in enumerate(rows):
            # Numéro de dent
            tooth_item = QTableWidgetItem(str(tooth))
            tooth_item.setTextAlignment(Qt.AlignCenter)
            self.root_table.setItem(i, 0, tooth_item)
            
            # Dose
            dose_item = QTableWidgetItem(f"{dose:.1f}")
            dose_item.setTextAlignment(Qt.AlignCenter)
            self.root_table.setItem(i, 1, dose_item)
            
            # Niveau de risque
            risk_item = QTableWidgetItem(risk_info['label'])
            risk_item.setTextAlignment(Qt.AlignCenter)
            if 'color' in risk_info:
                risk_item.setBackground(QColor(risk_info['color']))
                if risk_info['level'] == 'high':
                    risk_item.setForeground(QColor('white'))
            self.root_table.setItem(i, 2, risk_item)
    
    def get_risk_info(self, dose):
        """Détermine le niveau de risque d'une dose - VERSION CORRIGÉE"""
        if not self.config_manager:
            # Seuils par défaut si pas de configuration
            if dose < 30.0:
                return {
                    'level': 'low',
                    'label': 'Faible',
                    'description': 'Risque faible',
                    'color': '#27ae60'  # Vert
                }
            elif dose < 50.0:
                return {
                    'level': 'moderate',
                    'label': 'Modéré',
                    'description': 'Risque modéré',
                    'color': '#f39c12'  # Orange
                }
            else:
                return {
                    'level': 'high',
                    'label': 'Élevé',
                    'description': 'Risque élevé',
                    'color': '#e74c3c'  # Rouge
                }
        
        # CORRECTION : Utiliser la configuration active du ConfigManager
        try:
            config = self.config_manager.get_config()
            risk_levels = config['risk_levels']
            
            if dose < risk_levels['low_threshold']:
                return {
                    'level': 'low',
                    'label': risk_levels['low_label'],
                    'description': risk_levels['low_description'],
                    'color': '#27ae60'  # Vert
                }
            elif dose < risk_levels['moderate_threshold']:
                return {
                    'level': 'moderate', 
                    'label': risk_levels['moderate_label'],
                    'description': risk_levels['moderate_description'],
                    'color': '#f39c12'  # Orange
                }
            else:
                return {
                    'level': 'high',
                    'label': risk_levels['high_label'],
                    'description': risk_levels['high_description'],
                    'color': '#e74c3c'  # Rouge
                }
        except Exception as e:
            print(f"[ERREUR] get_risk_info: {e}")
            # Fallback sur les valeurs par défaut
            if dose < 30.0:
                return {
                    'level': 'low',
                    'label': 'Faible',
                    'description': 'Risque faible (défaut)',
                    'color': '#27ae60'
                }
            elif dose < 50.0:
                return {
                    'level': 'moderate',
                    'label': 'Modéré',
                    'description': 'Risque modéré (défaut)',
                    'color': '#f39c12'
                }
            else:
                return {
                    'level': 'high',
                    'label': 'Élevé',
                    'description': 'Risque élevé (défaut)',
                    'color': '#e74c3c'
                }
    
    def calculate_risk_distribution(self):
        """Calcule la répartition des doses par niveau de risque"""
        data = self.doses_data.get('complete', {})
        
        counts = {'low': 0, 'moderate': 0, 'high': 0}
        
        for dose in data.values():
            risk_info = self.get_risk_info(dose)
            counts[risk_info['level']] += 1
        
        return counts
    
    def calculate_detailed_risk_data(self):
        """Calcule les données détaillées par niveau de risque - VERSION CORRIGÉE"""
        data = self.doses_data.get('complete', {})
        
        risk_data = {
            'low': {'teeth': [], 'label': '', 'description': '', 'color': '#27ae60'},
            'moderate': {'teeth': [], 'label': '', 'description': '', 'color': '#f39c12'},
            'high': {'teeth': [], 'label': '', 'description': '', 'color': '#e74c3c'}
        }
        
        # CORRECTION : Obtenir les labels depuis la configuration active
        if self.config_manager:
            try:
                config = self.config_manager.get_config()
                risk_levels = config['risk_levels']
                
                risk_data['low']['label'] = risk_levels['low_label']
                risk_data['low']['description'] = f"< {risk_levels['low_threshold']:.1f} Gy"
                
                risk_data['moderate']['label'] = risk_levels['moderate_label']
                risk_data['moderate']['description'] = f"{risk_levels['low_threshold']:.1f} - {risk_levels['moderate_threshold']:.1f} Gy"
                
                risk_data['high']['label'] = risk_levels['high_label']
                risk_data['high']['description'] = f"> {risk_levels['moderate_threshold']:.1f} Gy"
            except Exception as e:
                print(f"[ERREUR] calculate_detailed_risk_data: {e}")
                # Utiliser les valeurs par défaut
                risk_data['low']['label'] = 'Faible'
                risk_data['low']['description'] = '< 30.0 Gy'
                risk_data['moderate']['label'] = 'Modéré'
                risk_data['moderate']['description'] = '30.0 - 50.0 Gy'
                risk_data['high']['label'] = 'Élevé'
                risk_data['high']['description'] = '> 50.0 Gy'
        else:
            # Valeurs par défaut
            risk_data['low']['label'] = 'Faible'
            risk_data['low']['description'] = '< 30.0 Gy'
            risk_data['moderate']['label'] = 'Modéré'
            risk_data['moderate']['description'] = '30.0 - 50.0 Gy'
            risk_data['high']['label'] = 'Élevé'
            risk_data['high']['description'] = '> 50.0 Gy'
        
        # Classer les dents
        for tooth, dose in data.items():
            risk_info = self.get_risk_info(dose)
            risk_data[risk_info['level']]['teeth'].append((tooth, dose))
        
        return risk_data
    
    def export_to_csv(self):
        """Exporte les données vers un fichier CSV"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            import csv
            
            # Sélection du fichier
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Exporter les doses vers CSV",
                "doses_dentaires.csv",
                "Fichiers CSV (*.csv);;Tous les fichiers (*)"
            )
            
            if not file_path:
                return
            
            # Écriture du CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # En-têtes
                writer.writerow(['# DOSES DENTAIRES RT-DENTX'])
                writer.writerow([])
                writer.writerow(['Dent', 'Dose_Complete_Gy', 'Dose_Couronne_Gy', 'Dose_Racine_Gy', 'Niveau_Risque', 'Description_Risque'])
                
                # Données
                complete_data = self.doses_data.get('complete', {})
                crown_data = self.doses_data.get('couronne', {})
                root_data = self.doses_data.get('racine', {})
                
                # Toutes les dents
                all_teeth = set(complete_data.keys()) | set(crown_data.keys()) | set(root_data.keys())
                
                for tooth in sorted(all_teeth, key=int):
                    complete_dose = complete_data.get(tooth, 0)
                    crown_dose = crown_data.get(tooth, 0)
                    root_dose = root_data.get(tooth, 0)
                    
                    # Utiliser la dose complète pour le niveau de risque
                    if complete_dose > 0:
                        risk_info = self.get_risk_info(complete_dose)
                        risk_level = risk_info['label']
                        risk_desc = risk_info['description']
                    else:
                        risk_level = 'N/A'
                        risk_desc = 'Dose non calculée'
                    
                    writer.writerow([
                        tooth,
                        f"{complete_dose:.2f}" if complete_dose > 0 else "N/A",
                        f"{crown_dose:.2f}" if crown_dose > 0 else "N/A",
                        f"{root_dose:.2f}" if root_dose > 0 else "N/A",
                        risk_level,
                        risk_desc
                    ])
            
            QMessageBox.information(
                self, "Export réussi",
                f"Données exportées vers:\n{file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Erreur d'export",
                f"Impossible d'exporter les données:\n{str(e)}"
            )
    
    def show_detailed_stats(self):
        """Affiche des statistiques détaillées"""
        try:
            # Calculer les statistiques
            complete_data = self.doses_data.get('complete', {})
            crown_data = self.doses_data.get('couronne', {})
            root_data = self.doses_data.get('racine', {})
            
            stats_text = "=== STATISTIQUES DÉTAILLÉES ===\n\n"
            
            # Statistiques générales
            stats_text += "DONNÉES GÉNÉRALES:\n"
            stats_text += f"• Dents avec dose complète: {len(complete_data)}\n"
            stats_text += f"• Dents avec dose couronne: {len(crown_data)}\n"
            stats_text += f"• Dents avec dose racine: {len(root_data)}\n\n"
            
            # Statistiques par type
            for data_type, data_name in [
                (complete_data, "DENTS COMPLÈTES"),
                (crown_data, "COURONNES"),
                (root_data, "RACINES")
            ]:
                if data:
                    doses = list(data.values())
                    stats_text += f"{data_name}:\n"
                    stats_text += f"• Nombre: {len(doses)}\n"
                    stats_text += f"• Minimum: {min(doses):.2f} Gy\n"
                    stats_text += f"• Maximum: {max(doses):.2f} Gy\n"
                    stats_text += f"• Moyenne: {sum(doses)/len(doses):.2f} Gy\n"
                    stats_text += f"• Médiane: {sorted(doses)[len(doses)//2]:.2f} Gy\n\n"
            
            # Répartition par risque
            if complete_data and self.config_manager:
                stats_text += "RÉPARTITION PAR NIVEAU DE RISQUE:\n"
                risk_data = self.calculate_detailed_risk_data()
                
                for risk_level, data in risk_data.items():
                    if data['teeth']:
                        count = len(data['teeth'])
                        percentage = (count / len(complete_data)) * 100
                        stats_text += f"• {data['label']}: {count} dents ({percentage:.1f}%)\n"
                
                stats_text += "\n"
            
            # Top 5 des doses les plus élevées
            if complete_data:
                stats_text += "TOP 5 DES DOSES LES PLUS ÉLEVÉES:\n"
                sorted_doses = sorted(complete_data.items(), key=lambda x: x[1], reverse=True)
                
                for i, (tooth, dose) in enumerate(sorted_doses[:5], 1):
                    risk_info = self.get_risk_info(dose)
                    stats_text += f"{i}. Dent {tooth}: {dose:.2f} Gy ({risk_info['label']})\n"
                
                stats_text += "\n"
            
            # Recommandations
            if self.config_manager:
                config = self.config_manager.get_config()
                high_risk_count = len([d for d in complete_data.values() 
                                     if d >= config['risk_levels']['moderate_threshold']])
                
                if high_risk_count > 0:
                    stats_text += "⚠️ ATTENTION:\n"
                    stats_text += f"• {high_risk_count} dents à risque élevé détectées\n"
                    stats_text += "• Surveillance clinique renforcée recommandée\n"
                    stats_text += "• Voir recommandations dans le rapport PDF\n"
            
            # Dialogue d'affichage
            stats_dialog = QDialog(self)
            stats_dialog.setWindowTitle("Statistiques détaillées")
            stats_dialog.resize(500, 600)
            
            layout = QVBoxLayout(stats_dialog)
            
            text_edit = QTextEdit()
            text_edit.setPlainText(stats_text)
            text_edit.setReadOnly(True)
            text_edit.setStyleSheet("font-family: monospace; font-size: 11px;")
            layout.addWidget(text_edit)
            
            close_button = QPushButton("Fermer")
            close_button.clicked.connect(stats_dialog.accept)
            layout.addWidget(close_button)
            
            stats_dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Erreur",
                f"Impossible d'afficher les statistiques:\n{str(e)}"
            )