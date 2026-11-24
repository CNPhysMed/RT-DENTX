#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module des panneaux d'interface utilisateur
© 2025 Caroline Moreau-Noblet — RT-DENTX — Licence BSD 3-Clause
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import logging
import os
from PIL import Image, ImageTk
import json
from pathlib import Path
import tkinter
import copy
from tooth_generator import get_tooth_default_values, TOOTH_ANATOMY, TOOTH_INCLINATIONS
from rtstruct_export_integration import RTStructExportMixin

logger = logging.getLogger(__name__)
try:
    from report_config_dialog import ReportConfigDialog
    REPORT_SYSTEM_AVAILABLE = True
except ImportError:
    REPORT_SYSTEM_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Système de rapport dosimétrique non disponible")

class NavigationPanel:
    """Panneau de navigation des coupes"""
    
    def __init__(self, parent, viewer):
        self.parent = parent
        self.viewer = viewer
        self.slice_var = None
        self.slice_scale = None
        self.slice_label = None
        self.setup_navigation()
    
    def setup_navigation(self):
        """Configuration du panel de navigation"""
        nav_frame = ttk.LabelFrame(self.parent, text="Navigation", padding=10, style="Bold.TLabelframe")
        nav_frame.pack(fill=tk.X, pady=(0, 10))

        self.slice_var = tk.IntVar()
        self.slice_scale = ttk.Scale(nav_frame, from_=0, to=0, variable=self.slice_var,
                                     command=self.viewer.on_slice_change, orient=tk.HORIZONTAL)
        self.slice_scale.pack(fill=tk.X, pady=(0, 5))

        nav_buttons = ttk.Frame(nav_frame)
        nav_buttons.pack(fill=tk.X)
        ttk.Button(nav_buttons, text="◀◀", width=6, command=self.viewer.first_slice).pack(side=tk.LEFT)
        ttk.Button(nav_buttons, text="◀", width=6, command=self.viewer.previous_slice).pack(side=tk.LEFT, padx=(5, 0))
        self.slice_label = ttk.Label(nav_buttons, text="0 / 0", font=('Arial', 10, 'bold'))
        self.slice_label.pack(side=tk.LEFT, expand=True)
        ttk.Button(nav_buttons, text="▶", width=6, command=self.viewer.next_slice).pack(side=tk.RIGHT)
        ttk.Button(nav_buttons, text="▶▶", width=6, command=self.viewer.last_slice).pack(side=tk.RIGHT, padx=(0, 5))
    
    def update_slice_label(self):
        """Met à jour le label de navigation"""
        if self.viewer.ct_slices and self.slice_label:
            total = len(self.viewer.ct_slices)
            self.slice_label.config(text=f"{self.viewer.current_slice + 1} / {total}")

class DualSlider(tk.Canvas):
    """Slider personnalisé avec deux curseurs pour min/max"""
    
    def __init__(self, parent, min_val=-1500, max_val=2000, initial_min=0, initial_max=1000, callback=None, bg_color=None):
        canvas_bg = bg_color if bg_color else 'white'
        super().__init__(parent, height=30, bg=canvas_bg, highlightthickness=1, highlightbackground='#ccc')
        
        self.min_val = min_val
        self.max_val = max_val
        self.current_min = initial_min
        self.current_max = initial_max
        self.callback = callback
        
        # Dimensions
        self.slider_width = 0
        self.slider_height = 20
        self.cursor_width = 12
        self.cursor_height = 20
        
        # États
        self.dragging_min = False
        self.dragging_max = False
        
        # Bind events
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Configure>", self.on_resize)
        
        # Dessiner après un court délai pour que les dimensions soient définies
        self.after(1, self.draw)
    
    def on_resize(self, event):
        """Redessine quand la taille change"""
        self.slider_width = self.winfo_width() - 20
        self.draw()
    
    def value_to_x(self, value):
        """Convertit une valeur en position X"""
        if self.slider_width <= 0:
            return 10
        ratio = (value - self.min_val) / (self.max_val - self.min_val)
        return 10 + ratio * self.slider_width
    
    def x_to_value(self, x):
        """Convertit une position X en valeur"""
        if self.slider_width <= 0:
            return self.min_val
        ratio = max(0, min(1, (x - 10) / self.slider_width))
        return self.min_val + ratio * (self.max_val - self.min_val)
    
    def draw(self):
        """Dessine le slider"""
        self.delete("all")
        
        if self.slider_width <= 0:
            self.slider_width = self.winfo_width() - 20
            if self.slider_width <= 0:
                return
        
        # Ligne de fond
        y_center = 15
        self.create_line(10, y_center, 10 + self.slider_width, y_center, 
                        fill='#ddd', width=4, tags='track')
        
        # Zone active (entre les deux curseurs)
        min_x = self.value_to_x(self.current_min)
        max_x = self.value_to_x(self.current_max)
        self.create_line(min_x, y_center, max_x, y_center, 
                        fill='#3498db', width=6, tags='active_range')
        
        # Curseur minimum (gris foncé)
        self.create_rectangle(min_x - 3, y_center - 10, min_x + 3, y_center + 10,
                            fill='#555555', outline='', width=0, tags='min_cursor')
                
        # Curseur maximum (gris foncé)
        self.create_rectangle(max_x - 3, y_center - 10, max_x + 3, y_center + 10,
                            fill='#555555', outline='', width=0, tags='max_cursor')
    
    def on_click(self, event):
        """Gère le clic initial"""
        min_x = self.value_to_x(self.current_min)
        max_x = self.value_to_x(self.current_max)
        
        # Détermine quel curseur est le plus proche
        dist_to_min = abs(event.x - min_x)
        dist_to_max = abs(event.x - max_x)
        
        if dist_to_min < dist_to_max and dist_to_min < 15:
            self.dragging_min = True
        elif dist_to_max < 15:
            self.dragging_max = True
    
    def on_drag(self, event):
        """Gère le glissement"""
        if self.dragging_min:
            new_val = int(self.x_to_value(event.x))
            self.current_min = max(self.min_val, min(new_val, self.current_max - 10))
            self.draw()
            if self.callback:
                self.callback()
        elif self.dragging_max:
            new_val = int(self.x_to_value(event.x))
            self.current_max = min(self.max_val, max(new_val, self.current_min + 10))
            self.draw()
            if self.callback:
                self.callback()
    
    def on_release(self, event):
        """Arrête le glissement"""
        self.dragging_min = False
        self.dragging_max = False
    
    def set_values(self, min_val, max_val):
        """Définit les valeurs programmatiquement"""
        self.current_min = max(self.min_val, min(min_val, self.max_val))
        self.current_max = min(self.max_val, max(max_val, self.min_val))
        self.draw()
    
    def get_values(self):
        """Retourne les valeurs actuelles"""
        return self.current_min, self.current_max

class WindowingPanel:
    """Panneau de fenêtrage CT avec slider double"""
    
    def __init__(self, parent, viewer):
        self.parent = parent
        self.viewer = viewer
        self.dual_slider = None
        self.min_label = None
        self.max_label = None
        self.setup_windowing()
    
    def setup_windowing(self):
        """Configuration du fenêtrage"""
        window_frame = ttk.LabelFrame(self.parent, text="Fenêtrage CT", padding=10, style="Bold.TLabelframe")
        window_frame.pack(fill=tk.X, pady=(0, 10))
        
        # === TITRE ET VALEURS ===
        header_frame = ttk.Frame(window_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="Plage de valeurs CT:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        
        values_frame = ttk.Frame(header_frame)
        values_frame.pack(side=tk.RIGHT)
        
        # Calcul des valeurs initiales min/max à partir de center/width
        center = self.viewer.ct_window_center
        width = self.viewer.ct_window_width
        initial_min = center - width // 2
        initial_max = center + width // 2
        
        ttk.Label(values_frame, text="Min:", font=('Arial', 9), foreground="black").pack(side=tk.LEFT)
        self.min_label = ttk.Label(values_frame, text=f"{initial_min}", 
                                  font=('Arial', 9, 'bold'), foreground="black")
        self.min_label.pack(side=tk.LEFT, padx=(2, 10))
        
        ttk.Label(values_frame, text="Max:", font=('Arial', 9), foreground="black").pack(side=tk.LEFT)
        self.max_label = ttk.Label(values_frame, text=f"{initial_max}", 
                                  font=('Arial', 9, 'bold'), foreground="black")
        self.max_label.pack(side=tk.LEFT, padx=(2, 0))
        
        # === SLIDER DOUBLE ===
        # Récupérer la couleur de fond par défaut depuis la fenêtre principale
        try:
            # Remonter dans la hiérarchie pour trouver un widget tk avec bg
            current_widget = self.parent
            default_bg = None
            
            while current_widget and default_bg is None:
                try:
                    if hasattr(current_widget, 'cget'):
                        default_bg = current_widget.cget('bg')
                        break
                except:
                    pass
                current_widget = current_widget.master
            
            # Si pas trouvé, utiliser la couleur système par défaut
            if not default_bg:
                default_bg = window_frame.tk.call('tk', 'windowingsystem') == 'win32' and 'SystemButtonFace' or '#f0f0f0'
                
        except:
            default_bg = '#f0f0f0'  # Couleur de fallback
        
        self.dual_slider = DualSlider(window_frame, min_val=-1500, max_val=3000,
                                     initial_min=initial_min, initial_max=initial_max,
                                     callback=self.on_slider_change, bg_color=default_bg)
        self.dual_slider.pack(fill=tk.X, pady=(0, 10))
        
        # === PRESETS ===
        preset_frame = ttk.Frame(window_frame)
        preset_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(preset_frame, text="Presets:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        
        buttons_frame = ttk.Frame(preset_frame)
        buttons_frame.pack(side=tk.RIGHT)
        
        ttk.Button(buttons_frame, text="Os", width=8,
                   command=lambda: self.set_preset_range(-450, 1050)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="Tissu mou", width=10,  
                   command=lambda: self.set_preset_range(-160, 240)).pack(side=tk.LEFT)
        ttk.Button(buttons_frame, text="Dents", width=10,
                   command=lambda: self.set_preset_range(0, 2300)).pack(side=tk.LEFT, padx=(5, 0))
        
        
    
    def on_slider_change(self):
        """Appelé quand le slider change"""
        min_val, max_val = self.dual_slider.get_values()
        
        # Mettre à jour les labels
        self.min_label.config(text=f"{min_val}")
        self.max_label.config(text=f"{max_val}")
        
        # Calculer center et width pour le viewer
        center = (min_val + max_val) // 2
        width = max_val - min_val
        
        # Mettre à jour les attributs du viewer directement
        self.viewer.ct_window_center = center
        self.viewer.ct_window_width = width
        
        # Appeler la mise à jour de l'affichage
        if hasattr(self.viewer, 'update_display'):
            self.viewer.update_display()
    
    def set_preset_range(self, min_val, max_val):
        """Applique un preset avec des valeurs min/max directes"""
        self.dual_slider.set_values(min_val, max_val)
        self.on_slider_change()
    
    def set_preset_center_width(self, center, width):
        """Applique un preset avec center/width (format standard médical)"""
        min_val = center - width // 2
        max_val = center + width // 2
        self.dual_slider.set_values(min_val, max_val)
        self.on_slider_change()


class EnhancedToothConfigDialog:
    """Dialogue amélioré de configuration des paramètres dentaires avec gestionnaire de config"""
    
    def __init__(self, parent, viewer):
        self.parent = parent
        self.viewer = viewer
        self.dialog = None
        self.tooth_data = {}
        self.original_data = {}
        self.modified_teeth = set()
        
        # Gestionnaire de configuration
        self.config_manager = None
        self._init_config_manager()
        
        # Charger la configuration actuelle
        self.load_current_config()
    
    def _init_config_manager(self):
        """Initialise le gestionnaire de configuration"""
        try:
            # Utiliser la classe définie dans le même fichier
            self.config_manager = ToothConfigManager()
            logger.info("Gestionnaire de configuration dentaire initialisé dans le dialogue")
        except Exception as e:
            logger.warning(f"ToothConfigManager non disponible - mode dégradé: {e}")
            self.config_manager = None
    
    def load_current_config(self):
        """Charge la configuration actuelle """
    
        # ÉTAPE 1: Charger la configuration de base
        if self.config_manager:
            self.tooth_data = copy.deepcopy(self.config_manager.get_tooth_config())
            self.original_data = copy.deepcopy(self.tooth_data)
        else:
            self.load_fallback_config()
        
        # ÉTAPE 2: PRIORITÉ ABSOLUE - Configuration de session du viewer
        session_config_found = False
        if hasattr(self.viewer, 'custom_tooth_config') and self.viewer.custom_tooth_config:
            viewer_config = self.viewer.custom_tooth_config
            
            for tooth, params in viewer_config.items():
                if tooth in self.tooth_data:
                    self.tooth_data[tooth].update(params)
                    # Ne plus ajouter automatiquement à modified_teeth
                    session_config_found = True
        
        # ÉTAPE 3: Si pas de config session, vérifier le config_manager
        if not session_config_found and self.config_manager:
            config_info = self.config_manager.get_config_info()
            if config_info['active_type'] == 'session':
                session_config_found = True
        
        # ÉTAPE 4: Marquer les dents modifiées par rapport aux valeurs par défaut
        self.detect_modified_teeth()
        
    
    def get_current_table_data(self):
        """Récupère les données actuelles depuis le tableau TreeView - NOUVELLE MÉTHODE"""
        current_data = {}
        
        try:
            # Parcourir tous les éléments du TreeView
            for item in self.tree.get_children():
                values = self.tree.item(item, 'values')
                if len(values) >= 6:
                    tooth = values[0]  # Numéro de dent
                    
                    # Extraire les valeurs numériques (enlever les unités)
                    try:
                        crown_height = float(values[2].replace(' mm', '').strip())
                        root_height = float(values[3].replace(' mm', '').strip())
                        diameter = float(values[4].replace(' mm', '').strip())
                        inclination = float(values[5].replace('°', '').strip())
                        
                        current_data[tooth] = {
                            'crown_height': crown_height,
                            'root_height': root_height,
                            'diameter': diameter,
                            'inclination': inclination
                        }
                        
                    except (ValueError, AttributeError) as e:
                        print(f"[WARNING] Erreur parsing dent {tooth}: {e}")
                        # Utiliser les valeurs par défaut si erreur
                        if tooth in self.tooth_data:
                            current_data[tooth] = self.tooth_data[tooth].copy()
        
            return current_data
            
        except Exception as e:
            print(f"[ERROR] get_current_table_data: {e}")
            # Fallback: retourner les données internes
            return copy.deepcopy(self.tooth_data)
    
    def detect_modified_teeth(self):
        """Détecte les dents modifiées par rapport aux valeurs par défaut"""
        self.modified_teeth.clear()
        
        if not self.config_manager:
            return
        
        default_config = self.config_manager.default_config
        
        for tooth, current_params in self.tooth_data.items():
            if tooth in default_config:
                default_params = default_config[tooth]
                
                # Vérifier chaque paramètre
                for key, current_value in current_params.items():
                    default_value = default_params.get(key, current_value)
                    
                    # Considérer comme modifié si différence > 0.01
                    if abs(current_value - default_value) > 0.01:
                        self.modified_teeth.add(tooth)
                        break  # Pas besoin de vérifier les autres paramètres
        
    
    def load_fallback_config(self):
        """Charge la configuration en mode dégradé - UTILISE LES CONSTANTES GLOBALES"""
        try:
            # Utiliser les constantes globales au lieu d'instancier ToothGenerator
            self.tooth_data = {}
            
            # Récupérer toutes les dents définies
            all_teeth = set(TOOTH_ANATOMY.keys()) | set(TOOTH_INCLINATIONS.keys())
            
            for tooth in sorted(all_teeth):
                self.tooth_data[tooth] = get_tooth_default_values(tooth)
            
            self.original_data = copy.deepcopy(self.tooth_data)
            
        except Exception as e:
            logger.error(f"Erreur chargement config fallback: {e}")
            # Configuration minimale d'urgence
            self.tooth_data = {'11': get_tooth_default_values('11')}
            self.original_data = copy.deepcopy(self.tooth_data)
            
    def show(self):
        """Affiche le dialogue de configuration avec schémas"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Configuration des paramètres dentaires")
        self.dialog.geometry("1400x900")  # Plus large pour accommoder les schémas
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Créer l'interface
        self.create_interface()
        
        # Centrer le dialogue
        self.center_dialog()
    
    def create_interface(self):
        """Crée l'interface du dialogue avec schémas des métriques"""
        # Frame principal avec scrollbar
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Layout horizontal : contenu à gauche, schémas à droite
        content_container = ttk.Frame(main_frame)
        content_container.pack(fill=tk.BOTH, expand=True)
        
        # === PARTIE GAUCHE: Contenu principal ===
        left_frame = ttk.Frame(content_container)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Canvas scrollable pour le contenu principal
        canvas = tk.Canvas(left_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # === PARTIE DROITE: Schémas des métriques ===
        right_frame = ttk.Frame(content_container, width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        right_frame.pack_propagate(False)
        
        # Titre des schémas
        schemas_title = ttk.Label(right_frame, text="Métriques dentaires", 
                                 font=('Arial', 12, 'bold'))
        schemas_title.pack(pady=(0, 10))
        
        # SCHÉMA 1: Schéma de positionnement
        schema1_frame = ttk.LabelFrame(right_frame, text="Positionnement des dents", padding=5)
        schema1_frame.pack(fill=tk.X, pady=(0, 10))
        
        schema1_path = "assets/dental_schema_2.png"
        if os.path.exists(schema1_path):
            try:
                schema1_image = Image.open(schema1_path)
                max_width = 550
                max_height = 400
                ratio_w = max_width / schema1_image.width
                ratio_h = max_height / schema1_image.height
                ratio = min(ratio_w, ratio_h, 1.0)
                new_size = (int(schema1_image.width * ratio), int(schema1_image.height * ratio))
                schema1_image = schema1_image.resize(new_size, Image.Resampling.LANCZOS)
                schema1_photo = ImageTk.PhotoImage(schema1_image)
    
                schema1_label = ttk.Label(schema1_frame, image=schema1_photo)
                schema1_label.image = schema1_photo  # Garder la référence
                schema1_label.pack()
            except Exception as e:
                ttk.Label(schema1_frame, text=f"⚠️ Erreur: {e}", 
                         foreground="red", font=('Arial', 8)).pack()
        else:
            ttk.Label(schema1_frame, text="⚠️ Schéma de positionnement non trouvé\n(assets/dental_schema_2.png)", 
                     foreground="red", font=('Arial', 8)).pack()
        
        # SCHÉMA 2: Métriques utilisées
        schema2_frame = ttk.LabelFrame(right_frame, text="Métriques utilisées", padding=5)
        schema2_frame.pack(fill=tk.X, pady=(0, 10))
        
        schema2_path = "assets/dental_metrics.png"
        if os.path.exists(schema2_path):
            try:
                schema2_image = Image.open(schema2_path)
                max_width = 350
                max_height = 250
                ratio_w = max_width / schema2_image.width
                ratio_h = max_height / schema2_image.height
                ratio = min(ratio_w, ratio_h, 1.0)
                new_size = (int(schema2_image.width * ratio), int(schema2_image.height * ratio))
                schema2_image = schema2_image.resize(new_size, Image.Resampling.LANCZOS)
                schema2_photo = ImageTk.PhotoImage(schema2_image)
    
                schema2_label = ttk.Label(schema2_frame, image=schema2_photo)
                schema2_label.image = schema2_photo  # Garder la référence
                schema2_label.pack()
            except Exception as e:
                ttk.Label(schema2_frame, text=f"⚠️ Erreur: {e}", 
                         foreground="red", font=('Arial', 8)).pack()
        else:
            ttk.Label(schema2_frame, text="⚠️ Schéma des métriques non trouvé\n(assets/dental_metrics.png)", 
                     foreground="red", font=('Arial', 8)).pack()
        

        
        # === CONTENU PRINCIPAL (partie gauche) ===
        # Sections de l'interface
        self.create_header_section(scrollable_frame)
        self.create_config_status_section(scrollable_frame)
        self.create_table_section(scrollable_frame)
        self.create_bulk_operations_section(scrollable_frame)
        self.create_file_operations_section(scrollable_frame)
        self.create_control_buttons(scrollable_frame)
        
        # Liaison molette souris pour le contenu principal
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        def unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind("<Enter>", bind_mousewheel)
        canvas.bind("<Leave>", unbind_mousewheel)
    
    def create_header_section(self, parent):
        """Crée la section d'en-tête"""
        header_frame = ttk.LabelFrame(parent, text="Configuration des paramètres dentaires", padding=10)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_text = ("Configurez individuellement les paramètres anatomiques de chaque dent :\n"
                    "• Hauteur des couronnes et racines (en mm)\n"
                    "• Diamètre des cylindres 3D (en mm)\n"
                    "• Inclinaison facio-linguale (en degrés)\n\n"
                    "Les modifications sont automatiquement mises en évidence.")
        
        info_label = tk.Label(header_frame, text=info_text, font=('Arial', 10), 
                             fg='#333333', justify=tk.LEFT)
        info_label.pack(anchor=tk.W)
    
    def create_config_status_section(self, parent):
        """Crée la section d'état de la configuration"""
        status_frame = ttk.LabelFrame(parent, text="État de la configuration", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.config_status_label = ttk.Label(status_frame, text="", font=('Arial', 10, 'bold'))
        self.config_status_label.pack(anchor=tk.W)
        
        # Mettre à jour le statut
        self.update_config_status()
    
    def update_config_status(self):
        """Met à jour l'affichage du statut de configuration"""
        if self.config_manager:
            info = self.config_manager.get_config_info()
            
            if info['active_type'] == 'session':
                status_text = f"🟡 Configuration temporaire active ({info['teeth_count']} dents configurées)"
                color = "#f39c12"
            elif info['active_type'] == 'persistent':
                status_text = f"🟢 Configuration permanente active ({info['teeth_count']} dents configurées)"
                color = "#27ae60"
            else:
                status_text = "🔵 Configuration par défaut active"
                color = "#3498db"
            
            self.config_status_label.config(text=status_text, foreground=color)
        else:
            self.config_status_label.config(text="⚪ Mode dégradé (gestionnaire non disponible)", 
                                          foreground="#95a5a6")
    
    def create_table_section(self, parent):
        """Crée la section du tableau éditable """
        table_frame = ttk.LabelFrame(parent, text="Paramètres par dent", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Instructions d'utilisation
        info_frame = ttk.Frame(table_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_text = "💡 Double-cliquez sur une valeur numérique pour la modifier directement"
        ttk.Label(info_frame, text=info_text, font=('Arial', 9, 'italic'), 
                 foreground='#2980b9').pack(anchor=tk.W)
        
        # Boutons de contrôle 
        control_frame = ttk.Frame(table_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(control_frame, text="🔄 Réinitialiser ", 
                  command=self.reset_selected_tooth).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="📊 Statistiques", 
                  command=self.show_statistics).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="🎨 Révéler modifications", 
                  command=self.highlight_modifications).pack(side=tk.LEFT)
        
        # === CONTAINER PRINCIPAL POUR LE TABLEAU ET LA SCROLLBAR ===
        # Frame container qui contiendra le Treeview et les scrollbars
        tree_container = ttk.Frame(table_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        # Créer le Treeview
        columns = ('dent', 'type', 'h_couronne', 'h_racine', 'diametre', 'inclinaison', 'statut')
        self.tree = ttk.Treeview(tree_container, columns=columns, show='headings', height=15)
        
        # Configuration des colonnes avec indicateur d'éditabilité
        column_config = {
            'dent': ('Dent', 60, False),
            'type': ('Type', 140, False), 
            'h_couronne': ('H. Couronne (mm) ✏️', 120, True),  # ✏️ indique éditable
            'h_racine': ('H. Racine (mm) ✏️', 120, True),
            'diametre': ('Diamètre (mm) ✏️', 120, True),
            'inclinaison': ('Inclinaison (°) ✏️', 120, True),
            'statut': ('Statut', 100, False)
        }
        
        # Stocker les colonnes éditables
        self.editable_columns = {col: editable for col, (_, _, editable) in column_config.items()}
        
        for col, (text, width, _) in column_config.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=tk.CENTER)
        
        # === CRÉER ET PLACER LES SCROLLBARS AVEC GRID ===
        # Scrollbar verticale
        v_scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        # Scrollbar horizontale
        h_scrollbar = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=self.tree.xview)
        
        # Configurer le Treeview pour utiliser les scrollbars
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # === PLACEMENT AVEC GRID POUR UN BON POSITIONNEMENT ===
        # Le Treeview en position (0,0)
        self.tree.grid(row=0, column=0, sticky='nsew')
        
        # La scrollbar verticale À DROITE en position (0,1)
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        
        # La scrollbar horizontale EN BAS en position (1,0)
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        # Configurer le poids des lignes et colonnes pour l'expansion
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        # Bind pour l'édition en place 
        self.tree.bind('<Double-1>', self.on_cell_double_click)
        self.tree.bind('<Button-1>', self.on_cell_single_click)
        
        # Variables pour l'édition en place
        self.edit_entry = None
        self.edit_item = None
        self.edit_column = None
        
        # Remplir le tableau
        self.populate_table()
    
    def populate_table(self):
        """Remplit le tableau avec mise en forme des modifications"""
                                                                                    # Nettoyer le tableau
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Configuration des tags de couleur
        self.tree.tag_configure('modified', foreground='red', font=('Arial', 10, 'bold'))
        self.tree.tag_configure('default', foreground='black', font=('Arial', 10))
        
        # Types de dents complets
        tooth_types = {
            # Maxillaire droite (Q1)
            '18': 'Q1 - 3e molaire droite', '17': 'Q1 - 2e molaire droite', '16': 'Q1 - 1re molaire droite',
            '15': 'Q1 - 2e prémolaire droite', '14': 'Q1 - 1re prémolaire droite', '13': 'Q1 - Canine droite',
            '12': 'Q1 - Incisive latérale droite', '11': 'Q1 - Incisive centrale droite',
            
            # Maxillaire gauche (Q2)
            '21': 'Q2 - Incisive centrale gauche', '22': 'Q2 - Incisive latérale gauche', '23': 'Q2 - Canine gauche',
            '24': 'Q2 - 1re prémolaire gauche', '25': 'Q2 - 2e prémolaire gauche', '26': 'Q2 - 1re molaire gauche',
            '27': 'Q2 - 2e molaire gauche', '28': 'Q2 - 3e molaire gauche',
            
            # Mandibule gauche (Q3)
            '38': 'Q3 - 3e molaire gauche', '37': 'Q3 - 2e molaire gauche', '36': 'Q3 - 1re molaire gauche',
            '35': 'Q3 - 2e prémolaire gauche', '34': 'Q3 - 1re prémolaire gauche', '33': 'Q3 - Canine gauche',
            '32': 'Q3 - Incisive latérale gauche', '31': 'Q3 - Incisive centrale gauche',
            
            # Mandibule droite (Q4)
            '41': 'Q4 - Incisive centrale droite', '42': 'Q4 - Incisive latérale droite', '43': 'Q4 - Canine droite',
            '44': 'Q4 - 1re prémolaire droite', '45': 'Q4 - 2e prémolaire droite', '46': 'Q4 - 1re molaire droite',
            '47': 'Q4 - 2e molaire droite', '48': 'Q4 - 3e molaire droite'
        }
        
        # Ordre d'affichage par quadrant
        tooth_order = [
            # Q1 - Maxillaire droite
            '18', '17', '16', '15', '14', '13', '12', '11',
            # Q2 - Maxillaire gauche  
            '21', '22', '23', '24', '25', '26', '27', '28',
            # Q3 - Mandibule gauche
            '38', '37', '36', '35', '34', '33', '32', '31',
            # Q4 - Mandibule droite
            '41', '42', '43', '44', '45', '46', '47', '48'
        ]
        
        # Remplir le tableau
        for tooth in tooth_order:
            if tooth in self.tooth_data:
                data = self.tooth_data[tooth]
                is_modified = tooth in self.modified_teeth
                
                # Déterminer le tag et le statut
                if is_modified:
                    tag = 'modified'
                    statut = "🔶 Modifiée"
                else:
                    tag = 'default'
                    statut = "✅ Défaut"
                
                # Valeurs formatées avec unités
                values = (
                    tooth,  # Non éditable
                    tooth_types.get(tooth, 'Type inconnu'),  # Non éditable
                    f"{data['crown_height']:.1f} mm",  # Éditable
                    f"{data['root_height']:.1f} mm",   # Éditable
                    f"{data['diameter']:.1f} mm",      # Éditable
                    f"{data['inclination']:.1f}°",     # Éditable
                    statut  # Non éditable
                )
                
                # Insérer avec le bon tag de couleur
                self.tree.insert('', 'end', values=values, tags=(tag,))
        
    
    def on_cell_single_click(self, event):
        """Gère le clic simple - ferme l'édition en cours"""
        if self.edit_entry:
            self.finish_edit()
    
    def on_cell_double_click(self, event):
        """Gère le double-clic - démarre l'édition d'une cellule"""
        # Identifier l'élément cliqué
        item = self.tree.identify('item', event.x, event.y)
        if not item:
            return
        
        # Identifier la colonne cliquée
        column = self.tree.identify('column', event.x, event.y)
        if not column:
            return
        
        # Convertir l'ID de colonne (#1, #2, etc.) en nom de colonne
        column_names = list(self.tree['columns'])
        try:
            col_index = int(column.replace('#', '')) - 1
            if col_index < 0 or col_index >= len(column_names):
                return
            column_name = column_names[col_index]
        except (ValueError, IndexError):
            return
        
        # Vérifier si la colonne est éditable
        if not self.editable_columns.get(column_name, False):
            return
        
        
        # Commencer l'édition
        self.start_cell_edit(item, column_name)
    
    def start_cell_edit(self, item, column):
        """Démarre l'édition d'une cellule"""
        # Fermer l'édition précédente
        if self.edit_entry:
            self.finish_edit()
        
        # Obtenir la valeur actuelle
        values = self.tree.item(item, 'values')
        column_names = list(self.tree['columns'])
        col_index = column_names.index(column)
        current_value = values[col_index]
        
        # Obtenir les coordonnées de la cellule
        bbox = self.tree.bbox(item, column)
        if not bbox:
            return
        
        
        # Créer le champ d'édition
        self.edit_entry = tk.Entry(self.tree, font=('Arial', 10), justify='center')
        self.edit_entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        
        # Nettoyer la valeur (enlever les unités)
        clean_value = current_value
        if 'mm' in clean_value:
            clean_value = clean_value.replace(' mm', '').strip()
        if '°' in clean_value:
            clean_value = clean_value.replace('°', '').strip()
        
        # Insérer la valeur et sélectionner
        self.edit_entry.insert(0, clean_value)
        self.edit_entry.select_range(0, tk.END)
        self.edit_entry.focus()
        
        # Stocker les infos d'édition
        self.edit_item = item
        self.edit_column = column
        
        # Événements pour terminer l'édition
        self.edit_entry.bind('<Return>', lambda e: self.finish_edit())
        self.edit_entry.bind('<Escape>', lambda e: self.cancel_edit())
        self.edit_entry.bind('<FocusOut>', lambda e: self.finish_edit())
    
    def finish_edit(self):
        """Termine l'édition et sauvegarde la valeur """
        if not self.edit_entry or not self.edit_item or not self.edit_column:
            return
        
        try:
            # Récupérer la nouvelle valeur
            new_value_str = self.edit_entry.get().strip()
            
            # Validation numérique
            try:
                new_value = float(new_value_str.replace(',', '.'))
            except ValueError:
                messagebox.showerror("Erreur", "Veuillez entrer une valeur numérique valide")
                self.cancel_edit()
                return
            
            # Validation des plages
            limits = {
                'h_couronne': (3.0, 15.0, "Hauteur couronne"),
                'h_racine': (5.0, 25.0, "Hauteur racine"),
                'diametre': (2.0, 15.0, "Diamètre"),
                'inclinaison': (-45.0, 45.0, "Inclinaison")
            }
            
            if self.edit_column in limits:
                min_val, max_val, param_name = limits[self.edit_column]
                if new_value < min_val or new_value > max_val:
                    messagebox.showerror("Valeur invalide", 
                                       f"{param_name} doit être entre {min_val} et {max_val}")
                    self.cancel_edit()
                    return
            
            # Récupérer le numéro de dent
            tooth_values = self.tree.item(self.edit_item, 'values')
            tooth = tooth_values[0]
            
            # Mapper colonne vers clé de données
            column_to_key = {
                'h_couronne': 'crown_height',
                'h_racine': 'root_height', 
                'diametre': 'diameter',
                'inclinaison': 'inclination'
            }
            
            if self.edit_column in column_to_key:
                data_key = column_to_key[self.edit_column]
                old_value = self.tooth_data[tooth][data_key]
                
                # Mettre à jour les données internes
                self.tooth_data[tooth][data_key] = new_value
                
                # Gérer le statut de modification
                original_value = self.original_data[tooth][data_key]
                if abs(new_value - original_value) > 0.01:
                    self.modified_teeth.add(tooth)
                else:
                    self.modified_teeth.discard(tooth)
                
            
            # Nettoyer et mettre à jour l'affichage
            self.cleanup_edit()
            self.populate_table()
            
            # Sélectionner à nouveau l'élément modifié
            for item in self.tree.get_children():
                if self.tree.item(item, 'values')[0] == tooth:
                    self.tree.selection_set(item)
                    self.tree.focus(item)
                    break
                    
        except Exception as e:
            print(f"[ERROR] finish_edit: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {e}")
            self.cancel_edit()
    
    def cancel_edit(self):
        """Annule l'édition en cours"""
        self.cleanup_edit()
    
    def cleanup_edit(self):
        """Nettoie les ressources d'édition"""
        if self.edit_entry:
            self.edit_entry.destroy()
            self.edit_entry = None
        self.edit_item = None
        self.edit_column = None
    
    def highlight_modifications(self):
        """Met en évidence les modifications"""
        if self.modified_teeth:
            count = len(self.modified_teeth)
            teeth_list = ", ".join(sorted(self.modified_teeth))
            messagebox.showinfo("Modifications détectées", 
                              f"{count} dent(s) modifiée(s) :\n{teeth_list}\n\n"
                              "Les valeurs modifiées apparaissent en rouge dans le tableau.")
        else:
            messagebox.showinfo("Aucune modification", 
                              "Aucune dent n'a été modifiée par rapport aux valeurs par défaut.")
    
    
    
    
    def reset_selected_tooth(self):
        """Remet TOUTES les dents aux valeurs par défaut """
        result = messagebox.askyesno("Confirmation", 
                                   "Remettre TOUTES les dents aux valeurs par défaut ?\n\n"
                                   "Cela supprimera toutes les modifications personnalisées.")
        if not result:
            return
        
        
        try:
            # Utiliser le gestionnaire si disponible
            if self.config_manager and hasattr(self.config_manager, 'reset_to_default'):
                success = self.config_manager.reset_to_default()
                if success:
                    print("[DEBUG] Réinitialisation via config_manager réussie")
                else:
                    print("[WARNING] Échec réinitialisation config_manager, fallback")
                    self.reset_all_to_hardcoded_defaults()
            else:
                self.reset_all_to_hardcoded_defaults()
            
            # IMPORTANT: Vider complètement la liste des modifications
            self.modified_teeth.clear()
            
            # Recharger la configuration
            self.load_current_config()
            
            # Mettre à jour l'affichage
            self.populate_table()
            self.update_config_status()
            
            messagebox.showinfo("Réinitialisation complète", 
                              "✅ Toutes les dents ont été remises aux valeurs par défaut.")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la réinitialisation complète:\n{str(e)}")
            print(f"[ERROR] Erreur réinitialisation complète: {e}")
    
    
    def reset_tooth_to_hardcoded_default(self, tooth):
        """Remet une dent aux valeurs par défaut depuis les constantes globales"""
        try:
            # Utiliser la fonction utilitaire globale
            default_values = get_tooth_default_values(tooth)
            self.tooth_data[tooth] = default_values.copy()
            
        except Exception as e:
            print(f"[ERROR] Erreur récupération valeurs par défaut pour {tooth}: {e}")
            # Fallback absolu
            self.tooth_data[tooth] = {
                'crown_height': 8.0,
                'root_height': 12.0, 
                'diameter': 7.0,
                'inclination': 15.0
            }
    
    def reset_all_to_hardcoded_defaults(self):
        """Remet toutes les dents aux valeurs par défaut depuis les constantes globales"""
        try:
            # Utiliser les constantes globales directement
            self.tooth_data = {}
            
            # Récupérer toutes les dents définies
            all_teeth = set(TOOTH_ANATOMY.keys()) | set(TOOTH_INCLINATIONS.keys())
            
            for tooth in sorted(all_teeth):
                self.tooth_data[tooth] = get_tooth_default_values(tooth)
            
            # Mettre à jour les données originales aussi
            self.original_data = copy.deepcopy(self.tooth_data)
            
            
        except Exception as e:
            print(f"[ERROR] Erreur réinitialisation globale: {e}")
            # Fallback minimal
            self.tooth_data = {'11': get_tooth_default_values('11')}
            self.original_data = copy.deepcopy(self.tooth_data)
    
    
    def show_statistics(self):
        """Affiche les statistiques des paramètres"""
        stats_dialog = tk.Toplevel(self.dialog)
        stats_dialog.title("Statistiques des paramètres dentaires")
        stats_dialog.geometry("500x400")
        stats_dialog.transient(self.dialog)
        
        frame = ttk.Frame(stats_dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Calculer les statistiques
        import numpy as np
        
        crowns = [data['crown_height'] for data in self.tooth_data.values()]
        roots = [data['root_height'] for data in self.tooth_data.values()]
        diameters = [data['diameter'] for data in self.tooth_data.values()]
        inclinations = [data['inclination'] for data in self.tooth_data.values()]
        
        stats_text = f"""Statistiques des paramètres dentaires:

Hauteurs des couronnes:
• Minimum: {min(crowns):.1f} mm
• Maximum: {max(crowns):.1f} mm
• Moyenne: {np.mean(crowns):.1f} mm

Hauteurs des racines:
• Minimum: {min(roots):.1f} mm
• Maximum: {max(roots):.1f} mm
• Moyenne: {np.mean(roots):.1f} mm

Diamètres:
• Minimum: {min(diameters):.1f} mm
• Maximum: {max(diameters):.1f} mm
• Moyenne: {np.mean(diameters):.1f} mm

Inclinaisons:
• Minimum: {min(inclinations):.1f}°
• Maximum: {max(inclinations):.1f}°
• Moyenne: {np.mean(inclinations):.1f}°

Configuration:
• Total dents configurées: {len(self.tooth_data)}
• Dents modifiées: {len(self.modified_teeth)}
• Dents par défaut: {len(self.tooth_data) - len(self.modified_teeth)}"""
        
        text_widget = tk.Text(frame, wrap=tk.WORD, font=('Consolas', 10))
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert('1.0', stats_text)
        text_widget.config(state=tk.DISABLED)
        
        ttk.Button(frame, text="Fermer", command=stats_dialog.destroy).pack(pady=(10, 0))
    
    def create_bulk_operations_section(self, parent):
        """Crée la section des opérations en lot"""
        bulk_frame = ttk.LabelFrame(parent, text="Opérations en lot", padding=10)
        bulk_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Opérations par arcade
        arcade_frame = ttk.Frame(bulk_frame)
        arcade_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(arcade_frame, text="Modifier par arcade:").pack(side=tk.LEFT)
        
        ttk.Button(arcade_frame, text="Maxillaire", 
                  command=lambda: self.bulk_edit_arcade('maxillaire')).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Button(arcade_frame, text="Mandibule", 
                  command=lambda: self.bulk_edit_arcade('mandibule')).pack(side=tk.LEFT, padx=(0, 5))
        
        # Opérations par type
        type_frame = ttk.Frame(bulk_frame)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(type_frame, text="Modifier par type:").pack(side=tk.LEFT)
        
        ttk.Button(type_frame, text="Incisives", 
                  command=lambda: self.bulk_edit_type('incisives')).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Button(type_frame, text="Canines", 
                  command=lambda: self.bulk_edit_type('canines')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(type_frame, text="Prémolaires", 
                  command=lambda: self.bulk_edit_type('premolaires')).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(type_frame, text="Molaires", 
                  command=lambda: self.bulk_edit_type('molaires')).pack(side=tk.LEFT, padx=(0, 5))
        
        # Copier paramètres
        copy_frame = ttk.Frame(bulk_frame)
        copy_frame.pack(fill=tk.X)
        
        ttk.Button(copy_frame, text="📋 Copier paramètres entre dents", 
                  command=self.copy_tooth_params).pack(side=tk.LEFT)
    
    def bulk_edit_arcade(self, arcade):
        """Édition en lot par arcade"""
        if arcade == 'maxillaire':
            teeth = [t for t in self.tooth_data.keys() if t.startswith(('1', '2'))]
            title = "Modifier toutes les dents maxillaires"
        else:
            teeth = [t for t in self.tooth_data.keys() if t.startswith(('3', '4'))]
            title = "Modifier toutes les dents mandibulaires"
        
        self.bulk_edit_dialog(teeth, title)
    
    def bulk_edit_type(self, tooth_type):
        """Édition en lot par type de dent"""
        type_mapping = {
            'incisives': ['11', '12', '21', '22', '31', '32', '41', '42'],
            'canines': ['13', '23', '33', '43'],
            'premolaires': ['14', '15', '24', '25', '34', '35', '44', '45'],
            'molaires': ['16', '17', '18', '26', '27', '28', '36', '37', '38', '46', '47', '48']
        }
        
        teeth = [t for t in type_mapping.get(tooth_type, []) if t in self.tooth_data]
        title = f"Modifier toutes les {tooth_type}"
        
        self.bulk_edit_dialog(teeth, title)
    
    def bulk_edit_dialog(self, teeth, title):
        """Dialogue d'édition en lot"""
        if not teeth:
            messagebox.showinfo("Information", "Aucune dent trouvée pour cette catégorie.")
            return
        
        bulk_dialog = tk.Toplevel(self.dialog)
        bulk_dialog.title(title)
        bulk_dialog.geometry("450x300")
        bulk_dialog.transient(self.dialog)
        bulk_dialog.grab_set()
        
        frame = ttk.Frame(bulk_dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=f"{title} ({len(teeth)} dents)", 
                 font=('Arial', 12, 'bold')).pack(pady=(0, 20))
        
        # Variables pour l'édition
        vars_dict = {
            'crown': tk.StringVar(),
            'root': tk.StringVar(),
            'diameter': tk.StringVar(),
            'inclination': tk.StringVar()
        }
        
        # Checkboxes pour choisir quoi modifier
        check_vars = {
            'crown': tk.BooleanVar(),
            'root': tk.BooleanVar(),
            'diameter': tk.BooleanVar(),
            'inclination': tk.BooleanVar()
        }
        
        fields = [
            ('crown', 'Hauteur couronne (mm):', 5.0, 20.0),
            ('root', 'Hauteur racine (mm):', 8.0, 25.0),
            ('diameter', 'Diamètre (mm):', 3.0, 15.0),
            ('inclination', 'Inclinaison (degrés):', -45.0, 45.0)
        ]
        
        for key, label_text, min_val, max_val in fields:
            field_frame = ttk.Frame(frame)
            field_frame.pack(fill=tk.X, pady=5)
            
            ttk.Checkbutton(field_frame, text="", variable=check_vars[key], width=3).pack(side=tk.LEFT)
            ttk.Label(field_frame, text=label_text, width=20).pack(side=tk.LEFT)
            ttk.Entry(field_frame, textvariable=vars_dict[key], width=10).pack(side=tk.LEFT, padx=(10, 5))
            ttk.Label(field_frame, text=f"({min_val}-{max_val})", 
                     font=('Arial', 8), foreground='gray').pack(side=tk.LEFT)
        
        # Boutons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def apply_bulk_changes():
            try:
                changes_made = False
                
                for key, var in vars_dict.items():
                    if check_vars[key].get() and var.get().strip():
                        value = float(var.get())
                        
                        # Validation selon le type
                        if key == 'crown' and (value < 5.0 or value > 20.0):
                            raise ValueError("Hauteur couronne doit être entre 5.0 et 20.0")
                        elif key == 'root' and (value < 8.0 or value > 25.0):
                            raise ValueError("Hauteur racine doit être entre 8.0 et 25.0")
                        elif key == 'diameter' and (value < 3.0 or value > 15.0):
                            raise ValueError("Diamètre doit être entre 3.0 et 15.0")
                        elif key == 'inclination' and (value < -45.0 or value > 45.0):
                            raise ValueError("Inclinaison doit être entre -45.0 et 45.0")
                        
                        # Appliquer aux dents sélectionnées
                        param_key = key + '_height' if key in ['crown', 'root'] else key
                        for tooth in teeth:
                            if tooth in self.tooth_data:
                                self.tooth_data[tooth][param_key] = value
                                self.modified_teeth.add(tooth)
                                changes_made = True
                
                if changes_made:
                    self.populate_table()
                    bulk_dialog.destroy()
                    messagebox.showinfo("Succès", f"Modifications appliquées à {len(teeth)} dents.")
                else:
                    messagebox.showwarning("Attention", "Aucune modification sélectionnée.")
                    
            except ValueError as e:
                messagebox.showerror("Erreur", str(e))
        
        ttk.Button(button_frame, text="Appliquer", command=apply_bulk_changes).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Annuler", command=bulk_dialog.destroy).pack(side=tk.LEFT)
    
    def copy_tooth_params(self):
        """Copie les paramètres d'une dent vers d'autres"""
        copy_dialog = tk.Toplevel(self.dialog)
        copy_dialog.title("Copier paramètres dentaires")
        copy_dialog.geometry("500x400")
        copy_dialog.transient(self.dialog)
        copy_dialog.grab_set()
        
        frame = ttk.Frame(copy_dialog, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Sélection dent source
        ttk.Label(frame, text="Dent source (copier depuis):").pack(anchor=tk.W, pady=(0, 5))
        source_var = tk.StringVar()
        source_combo = ttk.Combobox(frame, textvariable=source_var, state='readonly')
        source_combo['values'] = sorted(self.tooth_data.keys())
        source_combo.pack(fill=tk.X, pady=(0, 15))
        
        # Sélection dents cibles
        ttk.Label(frame, text="Dents cibles (copier vers):").pack(anchor=tk.W, pady=(0, 5))
        
        target_frame = ttk.Frame(frame)
        target_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Scrollable frame pour les checkboxes
        canvas = tk.Canvas(target_frame, height=200)
        scrollbar = ttk.Scrollbar(target_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Checkboxes pour les dents cibles
        target_vars = {}
        row, col = 0, 0
        for tooth in sorted(self.tooth_data.keys()):
            var = tk.BooleanVar()
            target_vars[tooth] = var
            ttk.Checkbutton(scrollable_frame, text=tooth, variable=var).grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            col += 1
            if col > 7:  # 8 colonnes
                col = 0
                row += 1
        
        # Boutons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X)
        
        def do_copy():
            source = source_var.get()
            if not source:
                messagebox.showwarning("Attention", "Sélectionnez une dent source")
                return
            
            targets = [tooth for tooth, var in target_vars.items() if var.get()]
            if not targets:
                messagebox.showwarning("Attention", "Sélectionnez au moins une dent cible")
                return
            
            # Copier les paramètres
            source_params = self.tooth_data[source]
            for target in targets:
                self.tooth_data[target] = copy.deepcopy(source_params)
                self.modified_teeth.add(target)
            
            self.populate_table()
            copy_dialog.destroy()
            messagebox.showinfo("Copie", f"Paramètres copiés de {source} vers {len(targets)} dent(s)")
        
        ttk.Button(button_frame, text="Copier", command=do_copy).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Annuler", command=copy_dialog.destroy).pack(side=tk.LEFT)
    
    def create_file_operations_section(self, parent):
        """Crée la section des opérations de fichiers"""
        file_frame = ttk.LabelFrame(parent, text="Import/Export", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Boutons d'import/export
        import_frame = ttk.Frame(file_frame)
        import_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(import_frame, text="📁 Charger configuration...", 
                  command=self.load_config_file).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(import_frame, text="💾 Sauvegarder configuration...", 
                  command=self.save_config_file).pack(side=tk.LEFT)
        
        # Information sur les fichiers
        info_text = "Les configurations sont sauvegardées au format JSON et peuvent être partagées entre utilisateurs."
        ttk.Label(file_frame, text=info_text, font=('Arial', 8), foreground='gray').pack(anchor=tk.W, pady=(5, 0))
    
    def load_config_file(self):
        """Charge une configuration depuis un fichier """
        file_path = filedialog.askopenfilename(
            title="Charger configuration des dents",
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")]
        )
        
        if file_path:
            try:
                if self.config_manager:
                    imported_config = self.config_manager.import_config(file_path)
                    
                    # Appliquer la configuration importée
                    self.tooth_data = copy.deepcopy(imported_config)
                    
                    # Détecter SEULEMENT les vraies modifications
                    self.detect_modified_teeth()
                    
                    self.populate_table()
                    messagebox.showinfo("Configuration chargée", 
                                      f"Configuration chargée depuis {Path(file_path).name}")
                else:
                    # Mode dégradé
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if 'config' in data:
                        self.tooth_data = copy.deepcopy(data['config'])
                    else:
                        self.tooth_data = copy.deepcopy(data)
                    
                    # Détecter les modifications par rapport aux valeurs par défaut
                    self.detect_modified_teeth()
                    
                    self.populate_table()
                    messagebox.showinfo("Configuration chargée", 
                                      f"Configuration chargée depuis {Path(file_path).name}")
            
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de charger la configuration:\n{e}")
    
    def save_config_file(self):
        """Sauvegarde la configuration actuelle dans un fichier -"""
        file_path = filedialog.asksaveasfilename(
            title="Sauvegarder configuration des dents",
            defaultextension=".json",
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")]
        )
        
        if file_path:
            try:
                #  Utiliser les données actuelles du tableau
                current_config = self.get_current_table_data()
                
                # Préparer les données d'export
                export_data = {
                    'version': '1.0',
                    'description': 'Configuration des paramètres dentaires RT-DENTX',
                    'teeth_count': len(current_config),
                    'parameters': ['crown_height', 'root_height', 'diameter', 'inclination'],
                    'config': current_config
                }
                
                # Sauvegarder
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Configuration sauvegardée", 
                                  f"Configuration sauvegardée dans {Path(file_path).name}")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de sauvegarder la configuration:\n{e}")
    
    def create_control_buttons(self, parent):
        """Crée les boutons de contrôle"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Info de configuration à gauche
        info_frame = ttk.Frame(button_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        modification_count = len(self.modified_teeth)
        if modification_count > 0:
            info_text = f"🔶 {modification_count} dent(s) modifiée(s)"
            color = "#f39c12"
        else:
            info_text = "✅ Aucune modification"
            color = "#27ae60"
        
        self.modification_info_label = ttk.Label(info_frame, text=info_text, 
                                               font=('Arial', 10, 'bold'), foreground=color)
        self.modification_info_label.pack(anchor="w")
        
        # Boutons d'action à droite
        buttons_frame = ttk.Frame(button_frame)
        buttons_frame.pack(side=tk.RIGHT)
        
        # Configuration des boutons
        button_configs = [
            ("Valeurs par défaut", self.reset_to_default),
            ("Session uniquement", self.apply_session_config),
            ("Toutes les sessions", self.apply_persistent_config),
            ("Fermer", self.dialog.destroy)
        ]
        
        for text, command in button_configs:
            btn = ttk.Button(buttons_frame, text=text, command=command, width=18)
            btn.pack(side=tk.LEFT, padx=3)
    
    def reset_to_default(self):
        """Remet toutes les valeurs par défaut"""
        result = messagebox.askyesno("Confirmation", 
                                   "Remettre toutes les valeurs par défaut ?\n"
                                   "Cela supprimera toutes les modifications.")
        if result:
            try:
                # IMPORTANT : Vider la configuration de session du viewer
                if hasattr(self.viewer, 'custom_tooth_config'):
                    self.viewer.custom_tooth_config = None
                
                # IMPORTANT: Vider complètement la liste des modifications
                self.modified_teeth.clear()
                
                if self.config_manager:
                    success = self.config_manager.reset_to_default()
                    if success:
                        self.load_current_config()
                        self.populate_table()
                        self.update_config_status()
                        messagebox.showinfo("Configuration réinitialisée", 
                                          "Configuration remise aux valeurs par défaut.")
                else:
                    # Mode dégradé
                    self.load_fallback_config()
                    self.populate_table()
                    messagebox.showinfo("Configuration réinitialisée", 
                                      "Configuration remise aux valeurs par défaut.")
            except Exception as e:
                print(f"[ERROR] reset_to_default: {e}")
                messagebox.showerror("Erreur", f"Erreur lors de la réinitialisation: {e}")
    
    def apply_session_config(self):
        """Applique la configuration pour la session uniquement"""
        try:
            # Utiliser les données ACTUELLES du tableau
            current_config = self.get_current_table_data()
            
            for tooth in list(current_config.keys())[:3]:  # 3 premiers pour debug
                print(f"  {tooth}: {current_config[tooth]}")
            
            if self.config_manager:
                success = self.config_manager.set_session_config(current_config)
                if success:
                    self.update_config_status()
                    
                    # Appliquer au viewer avec les bonnes données
                    if hasattr(self.viewer, 'custom_tooth_config'):
                        self.viewer.custom_tooth_config = copy.deepcopy(current_config)
                    else:
                        setattr(self.viewer, 'custom_tooth_config', copy.deepcopy(current_config))
                    
                    # Mettre à jour les données internes du dialogue
                    self.tooth_data = copy.deepcopy(current_config)
                    
                    # Mettre à jour le tooth_generator si il existe
                    if hasattr(self.viewer, 'tooth_generator') and self.viewer.tooth_generator:
                        self.viewer.tooth_generator.update_viewer_config(self.viewer)
                        
                    messagebox.showinfo("Session", "Configuration appliquée à cette session uniquement.")
                    # Recalculer les modifications après la sauvegarde
                    self.detect_modified_teeth()
                    self.populate_table()  # Actualiser l'affichage
            else:
                # Mode dégradé
                if hasattr(self.viewer, 'custom_tooth_config'):
                    self.viewer.custom_tooth_config = copy.deepcopy(current_config)
                else:
                    setattr(self.viewer, 'custom_tooth_config', copy.deepcopy(current_config))
                
                # Mettre à jour aussi en mode dégradé
                self.tooth_data = copy.deepcopy(current_config)
                
                messagebox.showinfo("Session", "Configuration appliquée à cette session (mode dégradé).")
                # Recalculer les modifications après la sauvegarde
                self.detect_modified_teeth()
                self.populate_table()  # Actualiser l'affichage
                
        except Exception as e:
            print(f"[ERROR] apply_session_config: {e}")
            import traceback
            traceback.print_exc()
    
    def apply_persistent_config(self):
        """Sauvegarde la configuration de manière permanente"""
        try:
            # Utiliser les données actuelles du tableau
            current_config = self.get_current_table_data()
            
            for tooth in list(current_config.keys())[:3]:
                print(f"  {tooth}: {current_config[tooth]}")
            
            result = messagebox.askyesno("Confirmation", 
                                       "Sauvegarder cette configuration de manière permanente ?\n"
                                       "Elle sera utilisée pour toutes les futures sessions.")
            if result:
                if self.config_manager:
                    success = self.config_manager.save_persistent_config(current_config)
                    if success:
                        # Mettre à jour les données internes
                        self.tooth_data = copy.deepcopy(current_config)
                        
                        self.update_config_status()
                        messagebox.showinfo("Sauvegardé", "Configuration sauvegardée de manière permanente.")
                else:
                    messagebox.showwarning("Mode dégradé", 
                                         "Sauvegarde permanente non disponible en mode dégradé.\n"
                                         "Utilisez 'Sauvegarder configuration...' à la place.")
                                         
        except Exception as e:
            print(f"[ERROR] apply_persistent_config: {e}")
            import traceback
            traceback.print_exc()
    
    
    
    def center_dialog(self):
        """Centre le dialogue sur l'écran"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

class ToothConfigManager:
    """Gestionnaire de configuration des paramètres dentaires"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".rt_dentx"
        self.config_dir.mkdir(exist_ok=True)
        self.tooth_config_file = self.config_dir / "tooth_config.json"
        
        # Configuration par défaut (utilise les constantes globales)
        self.default_config = {}
        self._build_default_config()
        
        # Configurations en mémoire
        self.persistent_config = None
        self.session_config = None
        
        # Charger la configuration persistante
        self._load_persistent_config()
    
    
    def _build_default_config(self):
        """Construit la configuration par défaut depuis les constantes globales"""
        try:
            all_teeth = set(TOOTH_ANATOMY.keys()) | set(TOOTH_INCLINATIONS.keys())
            
            for tooth in sorted(all_teeth):
                self.default_config[tooth] = get_tooth_default_values(tooth)
            
            logger.info(f"Configuration par défaut construite: {len(self.default_config)} dents")
            
        except Exception as e:
            logger.error(f"Erreur construction config par défaut: {e}")
            # Fallback minimal
            self.default_config = {'11': get_tooth_default_values('11')}
    
    def _load_persistent_config(self):
        """Charge la configuration persistante depuis le fichier"""
        try:
            if self.tooth_config_file.exists():
                with open(self.tooth_config_file, 'r', encoding='utf-8') as f:
                    self.persistent_config = json.load(f)
                logger.info(f"Configuration dentaire persistante chargée: {len(self.persistent_config)} dents")
            else:
                logger.info("Aucune configuration dentaire persistante trouvée - utilisation des valeurs par défaut")
        except Exception as e:
            logger.error(f"Erreur chargement configuration dentaire: {e}")
            self.persistent_config = None
    
    def get_tooth_config(self, tooth_name=None):
        """
        Récupère la configuration d'une dent ou de toutes les dents
        
        Priorité: session > persistante > défaut
        
        Args:
            tooth_name (str, optional): Numéro de la dent. Si None, retourne toute la config.
            
        Returns:
            dict: Configuration de la dent ou de toutes les dents
        """
        # Configuration de base
        base_config = copy.deepcopy(self.default_config)
        
        # Appliquer la configuration persistante
        if self.persistent_config:
            for tooth, params in self.persistent_config.items():
                if tooth in base_config:
                    base_config[tooth].update(params)
        
        # Appliquer la configuration de session (prioritaire)
        if self.session_config:
            for tooth, params in self.session_config.items():
                if tooth in base_config:
                    base_config[tooth].update(params)
        
        # Retourner la dent spécifique ou toute la configuration
        if tooth_name:
            return base_config.get(tooth_name, self.default_config.get(tooth_name, {}))
        else:
            return base_config
    
    def set_session_config(self, config):
        """Définit une configuration temporaire pour la session """
        self.session_config = copy.deepcopy(config)
        
        # DEBUG: Afficher quelques valeurs
        sample_teeth = list(config.keys())[:3]
        for tooth in sample_teeth:
            print(f"[DEBUG] Session config {tooth}: {config[tooth]}")
        
        logger.info(f"Configuration dentaire de session appliquée: {len(config)} dents modifiées")
        return True
    
    def save_persistent_config(self, config):
        """Sauvegarde la configuration de manière permanente"""
        try:
            # Sauvegarder dans le fichier
            with open(self.tooth_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # Mettre à jour la configuration en mémoire
            self.persistent_config = copy.deepcopy(config)
            
            # Effacer la configuration de session
            self.session_config = None
            
            logger.info(f"Configuration dentaire sauvegardée: {self.tooth_config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde configuration dentaire: {e}")
            return False
    
    def reset_to_default(self):
        """Remet la configuration aux valeurs par défaut"""
        try:
            # Supprimer le fichier de configuration
            if self.tooth_config_file.exists():
                self.tooth_config_file.unlink()
                logger.info("Fichier de configuration dentaire supprimé")
            
            # Réinitialiser les configurations en mémoire
            self.persistent_config = None
            self.session_config = None
            
            logger.info("Configuration dentaire remise aux valeurs par défaut")
            return True
            
        except Exception as e:
            logger.error(f"Erreur reset configuration dentaire: {e}")
            return False
    
    def get_config_info(self):
        """Retourne des informations sur la configuration active"""
        if self.session_config:
            return {
                'active_type': 'session',
                'description': 'Configuration temporaire active',
                'teeth_count': len(self.session_config)
            }
        elif self.persistent_config:
            return {
                'active_type': 'persistent',
                'description': 'Configuration sauvegardée active',
                'teeth_count': len(self.persistent_config)
            }
        else:
            return {
                'active_type': 'default',
                'description': 'Configuration par défaut active',
                'teeth_count': len(self.default_config)
            }
    
    def export_config(self, filepath):
        """Exporte la configuration actuelle vers un fichier"""
        try:
            current_config = self.get_tooth_config()
            
            export_data = {
                'version': '1.0',
                'description': 'Configuration des paramètres dentaires RT-DENTX',
                'teeth_count': len(current_config),
                'parameters': ['crown_height', 'root_height', 'diameter', 'inclination'],
                'config': current_config
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration exportée vers: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur export configuration: {e}")
            return False
    
    def import_config(self, filepath):
        """Importe une configuration depuis un fichier"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Valider le format
            if 'config' not in data:
                raise ValueError("Format de fichier invalide - clé 'config' manquante")
            
            imported_config = data['config']
            
            # Valider que toutes les dents ont les paramètres requis
            required_params = ['crown_height', 'root_height', 'diameter', 'inclination']
            for tooth, params in imported_config.items():
                if not all(param in params for param in required_params):
                    raise ValueError(f"Paramètres manquants pour la dent {tooth}")
            
            logger.info(f"Configuration importée: {len(imported_config)} dents")
            return imported_config
            
        except Exception as e:
            logger.error(f"Erreur import configuration: {e}")
            raise
    
    def validate_config(self, config):
        """Valide une configuration"""
        errors = []
        
        for tooth, params in config.items():
            # Vérifier que la dent existe dans la config par défaut
            if tooth not in self.default_config:
                errors.append(f"Dent inconnue: {tooth}")
                continue
            
            # Vérifier les paramètres requis
            required_params = ['crown_height', 'root_height', 'diameter', 'inclination']
            for param in required_params:
                if param not in params:
                    errors.append(f"Paramètre manquant pour {tooth}: {param}")
                elif not isinstance(params[param], (int, float)):
                    errors.append(f"Valeur invalide pour {tooth}.{param}: {params[param]}")
                elif params[param] <= 0:
                    errors.append(f"Valeur négative ou nulle pour {tooth}.{param}: {params[param]}")
        
        return errors




class ContourPanel:
    """Panneau de gestion des contours - COMPLET AVEC BOUTON CONFIGURATION"""
    
    def __init__(self, parent, viewer):
        self.parent = parent
        self.viewer = viewer
        self.contour_frame = None
        self.contour_canvas = None
        self.contour_scrollbar = None
        self.contour_scrollable_frame = None
        self.contour_canvas_window = None
        self.setup_contours()
    
    def setup_contours(self):
        """Configuration des contrôles de contours """
        self.contour_frame = ttk.LabelFrame(self.parent, text="Contours dentaire", padding=10, style="Bold.TLabelframe")
        self.contour_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.contour_frame.configure(height=250)
        
        # PAS de bouton de configuration ici - il est maintenant dans ToothPanel
        
        # Initialiser directement les contrôles de contours
        self.setup_contour_controls()
    
    
    def setup_contour_controls(self):
        """Configuration des contrôles de contours """
        
        # Pas de nettoyage spécial car pas de bouton à préserver
        
        # Frame pour les boutons de sélection globale
        button_frame = ttk.Frame(self.contour_frame)
        button_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(button_frame, text="Tout sélectionner", 
                   command=self.select_all_contours,
                   width=17).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Tout désélectionner", 
                   command=self.deselect_all_contours,
                   width=20).pack(side=tk.LEFT)
        
        # Frame container pour le canvas et scrollbar
        scroll_container = ttk.Frame(self.contour_frame)
        scroll_container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas avec scrollbar
        self.contour_canvas = tk.Canvas(scroll_container, 
                                       highlightthickness=0,
                                       bg='#f0f0f0')
        self.contour_scrollbar = ttk.Scrollbar(scroll_container, 
                                              orient="vertical", 
                                              command=self.contour_canvas.yview)
        
        # Frame interne scrollable
        self.contour_scrollable_frame = ttk.Frame(self.contour_canvas)
        
        # Configuration du scrolling
        def configure_contour_scroll(event=None):
            self.contour_canvas.configure(scrollregion=self.contour_canvas.bbox("all"))
            canvas_width = self.contour_canvas.winfo_width()
            if canvas_width > 1:
                self.contour_canvas.itemconfig(self.contour_canvas_window, width=canvas_width)
        
        self.contour_scrollable_frame.bind("<Configure>", configure_contour_scroll)
        self.contour_canvas.bind("<Configure>", configure_contour_scroll)
        
        # Créer la fenêtre dans le canvas
        self.contour_canvas_window = self.contour_canvas.create_window(
            (0, 0), window=self.contour_scrollable_frame, anchor="nw")
        
        # Configurer la scrollbar
        self.contour_canvas.configure(yscrollcommand=self.contour_scrollbar.set)
        
        # Packing - scrollbar toujours visible
        self.contour_scrollbar.pack(side="right", fill="y")
        self.contour_canvas.pack(side="left", fill="both", expand=True)
        
        # Label si pas de contours
        if not hasattr(self.viewer, 'contours') or not self.viewer.contours:
            self.no_contours_label = ttk.Label(self.contour_scrollable_frame, 
                                             text="Aucun contour chargé",
                                             font=('Arial', 10, 'italic'))
            self.no_contours_label.pack(pady=20)
    
    def setup_contour_checkboxes(self):
        """Configuration des checkboxes pour les contours"""
        
        # Supprimer les anciens widgets dans le frame scrollable
        if self.contour_scrollable_frame:
            for widget in self.contour_scrollable_frame.winfo_children():
                widget.destroy()
        
        if not self.viewer.contours:
            self.no_contours_label = ttk.Label(self.contour_scrollable_frame, 
                                             text="Aucun contour trouvé",
                                             font=('Arial', 10, 'italic'))
            self.no_contours_label.pack(pady=20)
            return
        
        # Couleurs pour les contours
        colors = ['red', 'green', 'blue', 'yellow', 'magenta', 'cyan', 
                 'orange', 'purple', 'brown', 'pink', 'lime', 'navy']
        
        # Trier les noms de structures pour un affichage ordonné
        previous_states = {}
        if hasattr(self.viewer, 'show_contours'):
            for roi_name, var in self.viewer.show_contours.items():
                previous_states[roi_name] = var.get()
        
        # Initialiser les variables de contrôle
        self.viewer.show_contours = {}
        
        for i, roi_name in enumerate(sorted(self.viewer.contours.keys())):
            # Frame pour chaque structure
            roi_frame = ttk.Frame(self.contour_scrollable_frame)
            roi_frame.pack(fill=tk.X, pady=2)
            
            # Variable pour cette structure
            var = tk.BooleanVar()
            var.set(previous_states.get(roi_name, True))
            self.viewer.show_contours[roi_name] = var
            
            # Checkbox avec callback
            checkbox = ttk.Checkbutton(
                roi_frame,
                text=roi_name,
                variable=var,
                command=lambda name=roi_name: self.toggle_contour_visibility(name)
            )
            checkbox.pack(side=tk.LEFT, anchor=tk.W)
            
            # Indicateur de couleur
            color = colors[i % len(colors)]
            color_label = tk.Label(
                roi_frame,
                text="●",
                font=('Arial', 12),
                fg=color,
                bg='#f0f0f0'
            )
            color_label.pack(side=tk.RIGHT, padx=(5, 0))
    
    def select_all_contours(self):
        """Sélectionne tous les contours"""
        if hasattr(self.viewer, 'show_contours'):
            for var in self.viewer.show_contours.values():
                var.set(True)
            if hasattr(self.viewer, 'update_display'):
                self.viewer.update_display()
    
    def deselect_all_contours(self):
        """Désélectionne tous les contours"""
        if hasattr(self.viewer, 'show_contours'):
            for var in self.viewer.show_contours.values():
                var.set(False)
            if hasattr(self.viewer, 'update_display'):
                self.viewer.update_display()
    
    def toggle_contour_visibility(self, roi_name):
        """Toggle la visibilité d'un contour spécifique"""
        if hasattr(self.viewer, 'update_display'):
            self.viewer.update_display()
class DosePanel:
    """Panneau de gestion de la dose """
    
    def __init__(self, parent, viewer):
        self.parent = parent
        self.viewer = viewer
        self.dose_controls = None
        self.dose_check_var = None
        self.dose_alpha_var = None
        self.dose_threshold_var = None
        self.threshold_entry_var = None
        self.dose_max_entry_var = None
        self.dose_scale_frame = None
        self.dose_scale_canvas = None
        self.setup_dose()
    
    def setup_dose(self):
        """Configuration des contrôles de dose"""
        dose_frame = ttk.LabelFrame(self.parent, text="Dose RTDose", padding=10, style="Bold.TLabelframe")
        dose_frame.pack(fill=tk.X)
        
        self.dose_check_var = tk.BooleanVar()
        ttk.Checkbutton(dose_frame, text="Afficher dose", variable=self.dose_check_var,
                        command=self.toggle_dose).pack(anchor=tk.W)
        
        self.dose_controls = ttk.Frame(dose_frame)
        self.dose_controls.pack(fill=tk.X, pady=(10, 0))
        
        # === Seuil Dmin / Dmax ===
        threshold_frame = ttk.LabelFrame(self.dose_controls, text="Seuil dose", padding=8)
        threshold_frame.pack(fill=tk.X, pady=(0, 10))
        threshold_grid = ttk.Frame(threshold_frame)
        threshold_grid.pack(fill=tk.X)
        
        ttk.Label(threshold_grid, text="Dmin (Gy):").grid(row=0, column=0, padx=5, pady=(0, 2), sticky='w')
        self.threshold_entry_var = tk.StringVar(value=f"{self.viewer.dose_threshold:.1f}")
        threshold_entry = ttk.Entry(threshold_grid, textvariable=self.threshold_entry_var, width=6, justify='center')
        threshold_entry.grid(row=1, column=0, padx=5)
        threshold_entry.bind('<Return>', lambda e: self.apply_threshold_entry())
        
        ttk.Label(threshold_grid, text="Dmax (Gy):").grid(row=0, column=1, padx=5, pady=(0, 2), sticky='w')
        self.dose_max_entry_var = tk.StringVar()
        self.dose_max_entry = ttk.Entry(threshold_grid, textvariable=self.dose_max_entry_var, width=6, justify='center')
        self.dose_max_entry.grid(row=1, column=1, padx=5)
        self.dose_max_entry.bind('<Return>', lambda e: self.apply_manual_dmax())
        
        # === Échelle de dose ===
        self.dose_scale_container = ttk.Frame(self.dose_controls)
        self.dose_scale_container.pack(fill=tk.X, pady=(0, 10))
        
        self.dose_scale_frame = ttk.LabelFrame(self.dose_scale_container, text="Échelle de dose", padding=8)
        self.dose_scale_frame.pack(fill=tk.X)
        
        # Canvas pour l'échelle de couleur
        def _from_rgb(rgb):
            return "#%02x%02x%02x" % rgb 
        
        self.dose_scale_canvas = tk.Canvas(self.dose_scale_frame, width=250, height=50, bg=_from_rgb((240, 240, 240)))
        self.dose_scale_canvas.pack(pady=5)
        
        # Label centré sous le canvas
        label_center = ttk.Label(self.dose_scale_frame, text="Dose (Gy)", font=('Arial', 8, 'bold'))
        label_center.pack(pady=(0, 5))
        
        # Transparence
        transparency_frame = ttk.Frame(self.dose_scale_container)
        transparency_frame.pack(fill=tk.X, pady=(8, 0))
        
        ttk.Label(transparency_frame, text="Transparence:").pack(anchor=tk.W, pady=(0, 5))
        self.dose_alpha_var = tk.DoubleVar(value=self.viewer.dose_alpha)
        ttk.Scale(transparency_frame, from_=0.1, to=1.0,
                  variable=self.dose_alpha_var,
                  command=self.on_dose_alpha_change,
                  orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        # Désactiver tous les contrôles de dose initialement
        self.disable_dose_controls()
    
    def enable_dose_controls(self):
        """Active tous les contrôles de dose"""
        for widget in self.dose_controls.winfo_children():
            self.set_widget_state(widget, 'normal')
    
    def disable_dose_controls(self):
        """Désactive tous les contrôles de dose"""
        for widget in self.dose_controls.winfo_children():
            self.set_widget_state(widget, 'disabled')
    
    def set_widget_state(self, widget, state):
        """Définit l'état d'un widget récursivement"""
        try:
            widget.configure(state=state)
        except:
            pass  # Certains widgets ne supportent pas 'state'
        
        # Traiter les enfants
        for child in widget.winfo_children():
            self.set_widget_state(child, state)
    
    def toggle_dose(self):
        """Active/désactive l'affichage de dose"""
        self.viewer.show_dose = self.dose_check_var.get()
        
        if not self.viewer.show_dose:
            self.hide_custom_dose_scale()
        
        self.viewer.update_display()
    
    def apply_threshold_entry(self):
        """Applique la valeur Dmin saisie au clavier"""
        try:
            value_str = self.threshold_entry_var.get().strip().replace(',', '.')
            new_threshold = float(value_str)
            new_threshold = max(0.0, min(100.0, new_threshold))
            self.viewer.dose_threshold = new_threshold
            self.viewer.update_display()
            logger.info(f"✅ Nouveau seuil Dmin: {new_threshold:.1f} Gy")
        except Exception as e:
            logger.error(f"Erreur seuil: {e}")
            messagebox.showerror("Erreur", "Dmin invalide")
    
    def apply_manual_dmax(self):
        """Applique la valeur Dmax saisie au clavier"""
        try:
            value_str = self.dose_max_entry_var.get().strip().replace(',', '.')
            new_dmax = float(value_str)
            if new_dmax > 0:
                self.viewer.manual_dmax = new_dmax
                self.viewer.update_display()
                logger.info(f"✅ Nouvelle Dmax fixée: {new_dmax:.1f} Gy")
            else:
                raise ValueError("Dmax doit être > 0")
        except Exception as e:
            logger.error(f"Erreur Dmax: {e}")
            messagebox.showerror("Erreur", "Dmax invalide")
    
    def on_dose_alpha_change(self, value=None):
        """Callback changement transparence dose"""
        self.viewer.dose_alpha = self.dose_alpha_var.get()
        if self.viewer.show_dose:
            self.viewer.update_display()
    
    def update_custom_dose_scale(self, min_dose, max_dose):
        """Met à jour l'échelle de dose personnalisée dans l'interface"""
        try:
            self.dose_scale_frame.pack(fill=tk.X)
            self.dose_scale_canvas.delete("all")
            
            width = 250
            height = 85
            gradient_height = 25
            padding = 10
            label_y_offset = 60
            
            self.dose_scale_canvas.config(height=height)
            
            import matplotlib.cm as cm
            colormap = cm.get_cmap('hot')
            
            # Gradient de couleurs
            for i in range(width - 2 * padding):
                ratio = i / (width - 2 * padding - 1)
                rgba = colormap(ratio)
                color = f"#{int(rgba[0]*255):02x}{int(rgba[1]*255):02x}{int(rgba[2]*255):02x}"
                self.dose_scale_canvas.create_line(i + padding, 5, i + padding, gradient_height, fill=color, width=1)
            
            # Graduations et valeurs
            num_ticks = 5
            for i in range(num_ticks):
                x = i * (width - 2 * padding) / (num_ticks - 1) + padding
                dose_value = min_dose + (max_dose - min_dose) * i / (num_ticks - 1)
                
                # Ligne de graduation
                self.dose_scale_canvas.create_line(x, gradient_height, x, gradient_height + 8, 
                                                 fill='black', width=2)
                
                # Texte des valeurs
                self.dose_scale_canvas.create_text(x, label_y_offset, 
                                                 text=f"{dose_value:.1f}", 
                                                 fill='black', 
                                                 anchor='s',
                                                 font=('Arial', 8, 'normal'))
            
            logger.debug(f"Échelle de dose mise à jour: {min_dose:.1f} - {max_dose:.1f} Gy")
            
        except Exception as e:
            logger.warning(f"Erreur mise à jour échelle dose: {e}")
    
    def hide_custom_dose_scale(self):
        """Cache l'échelle de dose personnalisée"""
        try:
            if self.dose_scale_frame:
                self.dose_scale_frame.pack_forget()
            logger.debug("Échelle de dose cachée")
        except Exception as e:
            logger.debug(f"Erreur masquage échelle dose: {e}")
    
    def display_dose_overlay(self):
        """Affiche la superposition de dose """
        if not self.viewer.rtdose_data:
            return
        
        try:
            # Obtenir les données de dose
            dose_array = self.viewer.rtdose_data.pixel_array.astype(np.float32)
            
            # Appliquer l'échelle de dose
            if hasattr(self.viewer.rtdose_data, 'DoseGridScaling'):
                dose_array *= float(self.viewer.rtdose_data.DoseGridScaling)
            
            # Trouver la coupe de dose correspondante
            ct_z = float(self.viewer.ct_slices[self.viewer.current_slice].ImagePositionPatient[2])
            
            # Position de départ de la grille de dose avec vérification
            if not hasattr(self.viewer.rtdose_data, 'ImagePositionPatient') or self.viewer.rtdose_data.ImagePositionPatient is None:
                logger.warning("ImagePositionPatient manquant dans RTDose - utilisation position par défaut")
                # Utiliser la position de la première coupe CT comme fallback
                ct_origin = self.viewer.ct_slices[0].ImagePositionPatient
                dose_origin = np.array([ct_origin[0], ct_origin[1], ct_origin[2]])
            else:
                dose_origin = np.array(self.viewer.rtdose_data.ImagePositionPatient)
            
            # Espacement des pixels de dose avec vérifications
            pixel_spacing_x = getattr(self.viewer.rtdose_data, 'PixelSpacing', [1.0, 1.0])
            if pixel_spacing_x is None or len(pixel_spacing_x) < 2:
                pixel_spacing_x = [1.0, 1.0]
                logger.warning("PixelSpacing manquant dans RTDose - utilisation 1.0mm par défaut")
            
            # Espacement Z (épaisseur de coupe dose)
            slice_thickness_dose = None
            
            # Méthode 1: SliceThickness
            if hasattr(self.viewer.rtdose_data, 'SliceThickness') and self.viewer.rtdose_data.SliceThickness is not None:
                slice_thickness_dose = float(self.viewer.rtdose_data.SliceThickness)
            
            # Méthode 2: GridFrameOffsetVector - calculer l'espacement entre coupes
            elif hasattr(self.viewer.rtdose_data, 'GridFrameOffsetVector') and self.viewer.rtdose_data.GridFrameOffsetVector is not None:
                offset_vector = self.viewer.rtdose_data.GridFrameOffsetVector
                if len(offset_vector) > 1:
                    # Calculer l'espacement entre la première et deuxième coupe
                    slice_thickness_dose = float(offset_vector[1]) - float(offset_vector[0])
                    logger.info(f"Espacement Z calculé depuis GridFrameOffsetVector: {slice_thickness_dose}mm")
                elif len(offset_vector) == 1:
                    slice_thickness_dose = 2.5  # Défaut basé sur PixelSpacing
                    logger.warning(f"Une seule valeur dans GridFrameOffsetVector, utilisation espacement par défaut: {slice_thickness_dose}mm")
            
            # Méthode 3: Calculé à partir des positions si plusieurs coupes
            elif dose_array.ndim == 3 and dose_array.shape[0] > 1:
                slice_thickness_dose = 1.0
                logger.warning(f"SliceThickness calculé par estimation: {slice_thickness_dose}mm")
            else:
                slice_thickness_dose = 1.0  # Défaut si une seule coupe
                logger.warning("Épaisseur de coupe dose indéterminée - utilisation 1.0mm par défaut")
            
            dose_spacing = np.array([
                float(pixel_spacing_x[0]),
                float(pixel_spacing_x[1]),
                slice_thickness_dose
            ])
            
            logger.info(f"Configuration dose - Origin: {dose_origin}, Spacing: {dose_spacing}")
            
            # Calculer l'index de coupe de dose
            if dose_array.ndim == 3:  # Volume 3D
                dose_slice_idx = None
                
                # Méthode précise avec GridFrameOffsetVector si disponible
                if hasattr(self.viewer.rtdose_data, 'GridFrameOffsetVector') and self.viewer.rtdose_data.GridFrameOffsetVector is not None:
                    offset_vector = self.viewer.rtdose_data.GridFrameOffsetVector
                    dose_z_positions = [dose_origin[2] + float(offset) for offset in offset_vector]
                    
                    # Trouver la coupe dose la plus proche
                    z_differences = [abs(z_pos - ct_z) for z_pos in dose_z_positions]
                    closest_idx = np.argmin(z_differences)
                    min_diff = z_differences[closest_idx]
                    
                    # Tolérance de 5mm pour la correspondance
                    if min_diff <= 5.0:
                        dose_slice_idx = closest_idx
                        logger.info(f"Correspondance trouvée - CT Z:{ct_z:.1f}mm → Dose coupe {dose_slice_idx} Z:{dose_z_positions[closest_idx]:.1f}mm (diff: {min_diff:.1f}mm)")
                    else:
                        logger.warning(f"Correspondance trop éloignée - diff: {min_diff:.1f}mm > 5.0mm")
                
                # Méthode fallback avec espacement uniforme
                if dose_slice_idx is None and dose_spacing[2] > 0:
                    z_diff = ct_z - dose_origin[2]
                    dose_slice_idx = int(round(z_diff / dose_spacing[2]))
                    logger.info(f"Correspondance par espacement uniforme - index: {dose_slice_idx}")
                
                # Vérifier les limites
                if dose_slice_idx is not None and 0 <= dose_slice_idx < dose_array.shape[0]:
                    dose_slice = dose_array[dose_slice_idx]
                    logger.info(f"Affichage coupe dose {dose_slice_idx+1}/{dose_array.shape[0]}")
                else:
                    if dose_slice_idx is not None:
                        logger.warning(f"Index de coupe dose hors limites: {dose_slice_idx} (max: {dose_array.shape[0]-1})")
                        # Utiliser la coupe la plus proche dans les limites
                        dose_slice_idx = max(0, min(dose_slice_idx, dose_array.shape[0]-1))
                        dose_slice = dose_array[dose_slice_idx]
                        logger.info(f"Utilisation coupe limite: {dose_slice_idx}")
                    else:
                        # Utiliser la coupe du milieu comme dernier recours
                        dose_slice_idx = dose_array.shape[0] // 2
                        dose_slice = dose_array[dose_slice_idx]
                        logger.warning(f"Aucune correspondance trouvée - utilisation coupe centrale: {dose_slice_idx}")
            else:  # Coupe unique 2D
                dose_slice = dose_array
                logger.info("Affichage dose 2D unique")
            
            # Extent de la dose
            rows, cols = dose_slice.shape
            dose_extent = [
                dose_origin[0],
                dose_origin[0] + cols * dose_spacing[0],
                dose_origin[1],
                dose_origin[1] + rows * dose_spacing[1]
            ]
            
            logger.debug(f"Dose extent: {dose_extent}")
            
            # Diagnostic des valeurs de dose
            dose_stats = {
                'min': np.min(dose_slice),
                'max': np.max(dose_slice), 
                'mean': np.mean(dose_slice),
                'non_zero_count': np.count_nonzero(dose_slice),
                'above_threshold': np.sum(dose_slice >= self.viewer.dose_threshold)
            }
            
            logger.info(f"📊 Stats dose coupe {dose_slice_idx}: min={dose_stats['min']:.2f}, "
                       f"max={dose_stats['max']:.2f}, mean={dose_stats['mean']:.2f}, "
                       f"non-zero={dose_stats['non_zero_count']}, above_threshold={dose_stats['above_threshold']}")
            
            # Vérifier qu'il y a des doses significatives
            max_dose = self.viewer.manual_dmax if self.viewer.manual_dmax is not None else dose_stats['max']
            if max_dose < self.viewer.dose_threshold:
                logger.info(f"Dose max ({max_dose:.2f}Gy) < seuil ({self.viewer.dose_threshold}Gy) - rien à afficher")
                # Supprimer l'échelle de dose s'il n'y a pas de dose à afficher
                self.hide_custom_dose_scale()
                return
            
            # Masquer les doses faibles
            dose_masked = np.ma.masked_where(dose_slice < self.viewer.dose_threshold, dose_slice)
            
            # Comparer les systèmes de coordonnées CT vs Dose
            ct_slice_ref = self.viewer.ct_slices[self.viewer.current_slice]
            ct_origin = np.array(ct_slice_ref.ImagePositionPatient[:2])
            ct_spacing = np.array(ct_slice_ref.PixelSpacing)
            ct_rows, ct_cols = ct_slice_ref.Rows, ct_slice_ref.Columns
            
            # Extent CT pour comparaison
            ct_extent = [
                ct_origin[0],
                ct_origin[0] + ct_cols * ct_spacing[0],
                ct_origin[1],
                ct_origin[1] + ct_rows * ct_spacing[1]
            ]
            
            logger.debug(f"CT extent: {ct_extent}")
            logger.debug(f"Dose extent: {dose_extent}")
            
            # Retourner la dose pour alignement correct
            dose_to_display = np.flipud(dose_masked)
            
            # Affichage sur l'axe du viewer
            im = self.viewer.ax.imshow(dose_to_display, cmap='hot', 
                          alpha=self.viewer.dose_alpha,
                          extent=dose_extent, 
                          origin='upper',  # Même origin que l'image CT
                          aspect='equal',
                          vmin=self.viewer.dose_threshold,
                          vmax=max_dose)
            
            # Utiliser notre échelle de dose personnalisée au lieu de la colorbar Matplotlib
            self.update_custom_dose_scale(self.viewer.dose_threshold, max_dose)
            
            logger.info(f"Dose affichée - Seuil: {self.viewer.dose_threshold}Gy, Max: {max_dose:.1f}Gy")
            
        except Exception as e:
            logger.error(f"Erreur affichage dose: {e}")
            import traceback
            logger.debug(traceback.format_exc())

class ToothPanel(RTStructExportMixin):
    """Panneau des outils dentaires """
    
    def __init__(self, parent, viewer):
        self.parent = parent
        self.viewer = viewer
        self.ct_viewer = viewer 
        
        # Variables pour les boutons toggle
        self.placement_active = False
        self.edit_active = False
        
        # Références des boutons
        self.btn_start_placement = None
        self.btn_edit_points = None
        self.btn_generate_teeth = None
        self.btn_clear_teeth = None
        self.btn_generate_cylinders = None
        self.btn_export_rtstruct = None  
        self.btn_dose_report = None
        self.btn_help = None
        
        # Labels d'information
        self.tooth_status_label = None
        self.selection_info_label = None
        
        self.setup_tooth_tools()
    
    def setup_tooth_tools(self):
        """Configuration du panneau dentaire amélioré"""
        
        # Panneau droit
        tooth_panel = ttk.Frame(self.parent, width=280)
        tooth_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        tooth_panel.pack_propagate(False)
        
        # Titre
        title_label = ttk.Label(tooth_panel, text="Outils Dentaires", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # === NOUVEAU: SECTION RACCOURCIS ===
        shortcuts_frame = ttk.LabelFrame(tooth_panel, text="Raccourcis", padding=10, style="Bold.TLabelframe")
        shortcuts_frame.pack(fill=tk.X, pady=(0, 10))
        
        shortcuts_text = """Souris:
    - Molette : Navigation coupes
    - Ctrl + Molette : zoom
    - Clic molette + glisser : Pan 
    (préférer l'outil croix en bas de l'image)
    
    Placement/Édition : 
    - Ctrl+Clic gauche : placer point
    - Clic gauche sur point : sélection 
    - Clic gauche glissé : translation 
    - Ctrl+Clic droit : supprimer point
    - Clic droit + glisser : sélection multiple
    
    Clavier:
    - Flèches : Navigation coupes  
    - R : Rotation sélection 
    - Suppr : Supprimer sélection 
    - Échap : Désélectionner tout"""
        
        # Créer le style italique pour le texte des raccourcis
        try:
            style = ttk.Style()
            style.configure('Shortcuts.TLabel', 
                          font=('Arial', 8, 'italic'),
                          foreground='#555555')
        except:
            pass  # En cas d'erreur de style, continuer sans
        
        shortcuts_label = ttk.Label(shortcuts_frame, text=shortcuts_text, 
                                  font=('Arial', 8, 'italic'), 
                                  foreground='#555555',
                                  justify=tk.LEFT)
        shortcuts_label.pack(anchor=tk.W)
        
        # === SECTION 1: POINTS DE RÉFÉRENCE (AMÉLIORÉE) ===
        ref_frame = ttk.LabelFrame(tooth_panel, text="Points de référence", padding=10, style="Bold.TLabelframe")
        ref_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Bouton placement avec toggle
        self.btn_start_placement = ttk.Button(ref_frame, 
                                             text="Tracer les 6 points de référence",
                                             command=self.toggle_placement_mode)
        self.btn_start_placement.pack(fill=tk.X, pady=(0, 5))
        
        # Bouton édition avec toggle
        self.btn_edit_points = ttk.Button(ref_frame, 
                                         text="Modifier/Supprimer points",
                                         command=self.toggle_edit_mode,
                                         state='normal')
        self.btn_edit_points.pack(fill=tk.X, pady=(0, 5))
        
        # Bouton Aide
        self.btn_help = ttk.Button(ref_frame, 
                                  text="Aide",
                                  command=self.show_help_dialog)
        self.btn_help.pack(fill=tk.X, pady=(0, 5))
        
        # Génération auto des autres points
        self.btn_generate_teeth = ttk.Button(ref_frame, 
                                            text="Génération auto des autres points",
                                            command=self.viewer.generate_other_teeth,
                                            state='disabled')
        self.btn_generate_teeth.pack(fill=tk.X)
        
        # === SECTION 2: CONTOURS DENTAIRES AVEC BOUTON CONFIGURATION ===
        contours_frame = ttk.LabelFrame(tooth_panel, text="Contours dentaires", padding=10, style="Bold.TLabelframe")
        contours_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Bouton de configuration des dents 
        config_button_frame = ttk.Frame(contours_frame)
        config_button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.tooth_config_button = ttk.Button(
            config_button_frame,
            text="⚙️ Configuration des contours dentaires",
            command=self.show_tooth_config_dialog,
            style='Accent.TButton'
        )
        self.tooth_config_button.pack(fill=tk.X, pady=(0, 5))
        
        
        
        # Boutons de génération des cylindres
        self.btn_generate_cylinders = ttk.Button(contours_frame, 
                                               text="Générer cylindres 3D dentaires",
                                               command=self.viewer.generate_tooth_cylinders,
                                               state='disabled')
        self.btn_generate_cylinders.pack(fill=tk.X, pady=(0, 5))
        
        self.btn_clear_teeth = ttk.Button(contours_frame, 
                                         text="🗑️ Supprimer TOUTES les dents",
                                         command=self.viewer.clear_all_teeth)
        self.btn_clear_teeth.pack(fill=tk.X)
        
        # === SECTION 3: RAPPORT DOSIMÉTRIQUE ===
        # Utiliser _create_report_section() 
        if REPORT_SYSTEM_AVAILABLE:
            report_frame = ttk.LabelFrame(tooth_panel, text="Rapport dosimétrique", padding=10, style="Bold.TLabelframe")
            report_frame.pack(fill=tk.X, pady=(0, 10))
            
            # Bouton de configuration
            self.btn_config_report = ttk.Button(
                report_frame,
                text="⚙️ Configuration du rapport",
                command=self._open_report_config,  # Utiliser _open_report_config
                style='Accent.TButton'
            )
            self.btn_config_report.pack(fill=tk.X, pady=(0, 5))
            
            # Bouton de génération du rapport
            self.btn_generate_report = ttk.Button(
                report_frame,
                text="📄 Générer rapport PDF",
                command=self._generate_report,  # Utiliser _generate_report
                state='disabled'
            )
            self.btn_generate_report.pack(fill=tk.X, pady=(0, 5))
            
            # Info sur le rapport
            report_info_text = ("Génère un PDF avec cartographies anatomiques,\n"
                               "tableau des doses et commentaires")
            report_info = tk.Label(
                report_frame,
                text=report_info_text,
                font=('Arial', 8),
                fg='#666666',
                justify=tk.LEFT,
                bg='#f0f0f0'
            )
            report_info.pack(anchor=tk.W, pady=(5, 0))
        
        # === SECTION 4: EXPORT RTSTRUCT ===
        export_frame = ttk.LabelFrame(tooth_panel, text="Export RTStruct", padding=10, style="Bold.TLabelframe")
        export_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.btn_export_rtstruct = ttk.Button(
            export_frame,
            text="📁 Exporter RTStruct avec dents",
            command=self.export_rtstruct_with_teeth,
            state='disabled'
        )
        self.btn_export_rtstruct.pack(fill=tk.X, pady=(0, 5))
        
        # Info sur l'export RTStruct
        export_info_text = ("Exporte une copie du RTStruct\navec les contours dentaires ajoutés")
        export_info = tk.Label(
            export_frame,
            text=export_info_text,
            font=('Arial', 8),
            fg='#666666',
            justify=tk.LEFT,
            bg='#f0f0f0'
        )
        export_info.pack(anchor=tk.W, pady=(5, 0))
        
        # === STATUS ET INFOS ===
        status_frame = ttk.Frame(tooth_panel)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.selection_info_label = ttk.Label(status_frame, text="", 
                                            foreground="blue", font=('Arial', 8))
        self.selection_info_label.pack(anchor=tk.W)
    
    def _create_report_section(self):
        """Crée la section des rapports dosimétriques"""
        if not REPORT_SYSTEM_AVAILABLE:
            return
            
        # Frame pour les rapports
        report_frame = ttk.LabelFrame(
            self.tooth_frame, 
            text="📊 Rapports dosimétriques", 
            padding=10,
            style="Bold.TLabelframe"
        )
        report_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Bouton de configuration
        self.btn_config_report = ttk.Button(
            report_frame,
            text="⚙️ Configuration du rapport dosimétrique",
            command=self._open_report_config
        )
        self.btn_config_report.pack(fill=tk.X, pady=(0, 5))
        
        # Bouton de génération
        self.btn_generate_report = ttk.Button(
            report_frame,
            text="📄 Générer rapport dosimétrique",
            command=self._generate_report
        )
        self.btn_generate_report.pack(fill=tk.X, pady=(0, 2))
        
        # Note d'information
        info_text = "Configurez d'abord les seuils et commentaires d'analyse,\npuis générez le rapport avec aperçu."
        tk.Label(
            report_frame, 
            text=info_text, 
            font=('Arial', 8, 'italic'), 
            justify=tk.CENTER, 
            fg='#666666'
        ).pack(pady=(5, 0))
        
        # État initial du bouton de génération
        self.btn_generate_report.configure(state='disabled')
    
    def _open_report_config(self):
        """Ouvre la configuration du rapport"""
        try:
            from report_config_dialog import ReportConfigDialog
            # Utiliser self.parent.winfo_toplevel() pour obtenir la fenêtre principale
            root_window = self.parent.winfo_toplevel()
            config_dialog = ReportConfigDialog(root_window, self.viewer)
            config_dialog.show()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir la configuration:\n{str(e)}")
            logger.error(f"Erreur ouverture configuration: {e}")
    
    def _generate_report(self):
        """Génère le rapport dosimétrique"""
        try:
            from dose_report_generator import DoseReportGenerator
            generator = DoseReportGenerator(self.viewer)
            generator.show_report_dialog()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de générer le rapport:\n{str(e)}")
            logger.error(f"Erreur génération rapport: {e}")
    
    
    def show_tooth_config_dialog(self):
        """Affiche le dialogue de configuration des dents"""
        try:
            # Importer depuis ui_panels
            from ui_panels import EnhancedToothConfigDialog
            config_dialog = EnhancedToothConfigDialog(self.viewer.master, self.viewer)
            config_dialog.show()
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Erreur Configuration", 
                               f"Impossible d'ouvrir la configuration des dents:\n{str(e)}")
            print(f"[ERREUR] Configuration dents: {e}")
            import traceback
            traceback.print_exc()
    
    
    def toggle_placement_mode(self):
        """Active/désactive le mode placement avec couleur"""
        if hasattr(self.viewer, 'tooth_editor') and self.viewer.tooth_editor:
            is_currently_placing = getattr(self.viewer.tooth_editor, 'placing_mode', False)
            
            if is_currently_placing:
                # Désactiver uniquement le placement
                if hasattr(self.viewer, 'stop_tooth_placement'):
                    self.viewer.stop_tooth_placement()
            else:
                # Activer le placement
                if hasattr(self.viewer, 'start_tooth_placement'):
                    self.viewer.start_tooth_placement()
        
        # Configuration du style une seule fois au début
        try:
            style = ttk.Style()
            style.configure('Active.TButton', 
                          background='#e8f5e8',      # Fond vert clair
                          foreground='#27ae60',      # Texte vert foncé
                          font=('Arial', 10, 'bold'), # Police grasse
                          borderwidth=2,             # Bordure
                          relief='solid',           # Mode enfoncé
                          focuscolor='#27ae60')         # Pas de contour de focus
            
            # Effets au survol
            style.map('Active.TButton',
                     background=[('active', '#d5e8d4'),    # Vert plus foncé au survol
                                ('pressed', '#c8e6c9')],   # Encore plus foncé quand pressé
                     relief=[('active', 'sunken'), ('pressed', 'sunken')])
        except Exception as e:
            print(f"Erreur de style: {e}")
        
        # update_button_states se chargera de synchroniser l'affichage et self.placement_active
        self.update_button_states()
    
    def toggle_edit_mode(self):
        """Active/désactive le mode édition avec couleur"""
        if hasattr(self.viewer, 'tooth_editor') and self.viewer.tooth_editor:
            is_currently_editing = getattr(self.viewer.tooth_editor, 'edit_mode', False)
            
            if is_currently_editing:
                # Désactiver uniquement l'édition
                if hasattr(self.viewer, 'stop_tooth_edit'):
                    self.viewer.stop_tooth_edit()
            else:
                # Activer l'édition
                if hasattr(self.viewer, 'toggle_tooth_edit_mode'):
                    self.viewer.toggle_tooth_edit_mode()
        
        # Configuration du style une seule fois au début
        try:
            style = ttk.Style()
            style.configure('EditActive.TButton', 
                          background='#fff3e0',        # Fond orange très clair
                          foreground='#f57c00',        # Texte orange foncé
                          font=('Arial', 10, 'bold'),  # Police grasse
                          borderwidth=2,               # Bordure
                          relief='sunken',             # Mode enfoncé
                          focuscolor='none')           # Pas de contour de focus
            
            # Effets au survol
            style.map('EditActive.TButton',
                     background=[('active', '#ffe0b2'),    # Orange plus foncé au survol
                                ('pressed', '#ffcc80')],   # Encore plus foncé quand pressé
                     relief=[('active', 'sunken'), ('pressed', 'sunken')])
        except Exception as e:
            print(f"Erreur de style: {e}")
        
        # update_button_states se chargera de synchroniser l'affichage et self.edit_active
        self.update_button_states()
    
    def show_help_dialog(self):
        """Affiche la boîte de dialogue d'aide avec le schéma à droite, plus grand"""
        
    
        help_sections = [
            ("Comment tracer les 6 points de référence :", [
                "• Cliquer sur Tracer les 6 points de référence",
                "• Se référer au schéma ci-dessous",
                "• Ctrl+Clic gauche pour placer un point",
                "• Placer d'abord les points aux emplacements des dents 11, 13 et 18 de la maxillaire sup",
                "• Placer ensuite les points aux emplacements des dents 41, 43 et 48 de la maxillaire inf",
                "• Choisir la coupe où apparaît le début des couronnes",
                "• Comment repérer le début des racines : zones grisâtres entre les dents"
            ]),
            ("Placement automatique des points suivants :", [
                "• une fois que les points de référence sont placés manuellement, cliquer sur Génération auto des autres points",
                "• Vérifier leur placement et le modifier si besoin.",
                "• Il est possible de supprimer des points si on ne veut pas relever la dose pour une dent en particulier"
            ]),
            ("Modification de la position des points :", [
                "• Cliquer sur Modifier/Supprimer points",
                "• Clic gauche sur un point : sélection du point",
                "• Clic gauche glissé sur un point : déplacement du point",
                "• Ctrl+Clic gauche dans le vide : placer nouveau point",
                "• Ctrl+Clic droit sur un point : suppression du point",
                "• Clic droit + glisser : sélection multiple rectangulaire",
                "• R : rotation du groupe sélectionné",
                "• Suppr : supprimer la sélection",
                "• Echap : désélectionner le groupe"
            ]),
            ("Génération des dents :", [
                "• Quand la position de tous les points de référence est correcte, cliquer sur Générer cylindres 3D dentaires"
            ])
        ]
    
        button_labels = {
            "Tracer les 6 points de référence",
            "Génération auto des autres points",
            "Modifier/Supprimer points",
            "Générer cylindres 3D dentaires"
        }
    
        help_window = tk.Toplevel(self.viewer.master)
        help_window.title("Aide - Points de référence")
        help_window.geometry("960x700")  # Large pour permettre affichage côte à côte
        help_window.resizable(False, False)
        help_window.transient(self.viewer.master)
        help_window.grab_set()
    
        container = ttk.Frame(help_window)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
    
        # Conteneur horizontal pour texte + schéma
        content_frame = ttk.Frame(container)
        content_frame.pack(fill=tk.BOTH, expand=True)
    
        # === Partie texte ===
        text = tk.Text(content_frame, wrap=tk.WORD, font=('Arial', 10), bg="#fdfdfd", relief=tk.FLAT, width=70, height=32)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
    
        # Styles texte
        text.tag_configure("title", font=('Arial', 13, 'bold'), justify='center', foreground="#003366", spacing1=2, spacing3=10)
        text.tag_configure("section", font=('Arial', 10, 'bold'), foreground="#005588", spacing1=6, spacing3=3)
        text.tag_configure("bold", font=('Arial', 10, 'bold'))
        text.tag_configure("bullet", lmargin1=12, lmargin2=28)
    
        text.insert(tk.END, "Placement des points de référence et génération des dents\n", "title")
    
        for section_title, lines in help_sections:
            text.insert(tk.END, f"{section_title}\n", "section")
            for line in lines:
                content = line.replace("•", "").strip()
                text.insert(tk.END, "• ", "bullet")
    
                if "début des couronnes" in content:
                    before, after = content.split("début des couronnes", 1)
                    text.insert(tk.END, before)
                    text.insert(tk.END, "début des couronnes", "bold")
                    text.insert(tk.END, after + "\n")
                    continue
    
                inserted = False
                for label in button_labels:
                    if label in content:
                        before, after = content.split(label, 1)
                        text.insert(tk.END, before)
                        btn = tk.Button(text, text=label, state='disabled', font=('Arial', 9, 'bold'),
                                        relief='raised', borderwidth=2, background="#cce4ff",
                                        disabledforeground='black', cursor='arrow', padx=6)
                        text.window_create(tk.END, window=btn)
                        text.insert(tk.END, after + "\n")
                        inserted = True
                        break
                if not inserted:
                    text.insert(tk.END, content + "\n")
            text.insert(tk.END, "\n")
    
        text.config(state=tk.DISABLED)
    
        # === Partie schéma (à droite) ===
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
    
        schema_path = "assets/dental_schema.png"
        if os.path.exists(schema_path):
            schema_image = Image.open(schema_path)
            max_width = 400
            max_height = 500
            ratio_w = max_width / schema_image.width
            ratio_h = max_height / schema_image.height
            ratio = min(ratio_w, ratio_h, 1.0)
            new_size = (int(schema_image.width * ratio), int(schema_image.height * ratio))
            schema_image = schema_image.resize(new_size, Image.Resampling.LANCZOS)
            schema_photo = ImageTk.PhotoImage(schema_image)
    
            ttk.Label(right_panel, text="Schéma de référence", font=('Arial', 9, 'italic')).pack(pady=(0, 5))
            schema_label = ttk.Label(right_panel, image=schema_photo)
            schema_label.image = schema_photo
            schema_label.pack()
        else:
            ttk.Label(right_panel, text="⚠️ Schéma non trouvé", foreground="red").pack(pady=5)
    
        # === Bouton fermer ===
        ttk.Button(container, text="Fermer", command=help_window.destroy).pack(pady=(10, 5))



    
    def update_button_states(self):
        """Met à jour l'état des boutons selon le contexte"""
        if not hasattr(self.viewer, 'tooth_editor') or not self.viewer.tooth_editor:
            return
            
        has_points = len(self.viewer.tooth_editor.points) > 0
        is_complete = self.viewer.tooth_editor.is_complete()
        is_placing = getattr(self.viewer.tooth_editor, 'placing_mode', False)
        is_editing = getattr(self.viewer.tooth_editor, 'edit_mode', False)
        
        # Synchroniser les états internes avec l'éditeur
        if is_placing != self.placement_active:
            self.placement_active = is_placing
            # Mettre à jour le bouton
            if is_placing:
                self.btn_start_placement.configure(
                    style='Active.TButton',
                    text="ACTIF - Tracer les 6 points"
                )
            else:
                self.btn_start_placement.configure(
                    style='',
                    text="Tracer les 6 points de référence"
                )
        
        if is_editing != self.edit_active:
            self.edit_active = is_editing
            # Mettre à jour le bouton
            if is_editing:
                self.btn_edit_points.configure(
                    style='EditActive.TButton',
                    text="ACTIF - Modifier/Supprimer"
                )
                self.selection_info_label.config(text="Mode édition actif", foreground="#f57c00")
            else:
                self.btn_edit_points.configure(
                    style='',
                    text="Modifier/Supprimer points"
                )
                self.selection_info_label.config(text="Mode édition arrêté", foreground="gray")
        
        # Bouton génération automatique
        self.btn_generate_teeth.config(state='normal' if is_complete else 'disabled')
        
        # Bouton génération cylindres 3D
        self.btn_generate_cylinders.config(state='normal' if has_points else 'disabled')
        
        # Bouton export RTStruct
        has_dental_structures = False
        if hasattr(self.viewer, 'contours'):
            has_dental_structures = any(name.startswith(('C_', 'R_')) 
                                      for name in self.viewer.contours.keys())
        self.btn_export_rtstruct.config(state='normal' if has_dental_structures else 'disabled')
        
        # Boutons de rapport
        if REPORT_SYSTEM_AVAILABLE and hasattr(self, 'btn_generate_report'):
            # Le bouton est actif si on a des doses ET des structures dentaires
            has_rtdose = hasattr(self.viewer, 'rtdose_data') and self.viewer.rtdose_data is not None
            has_structures = False
            
            if hasattr(self.viewer, 'contours') and self.viewer.contours:
                # Vérifier qu'on a au moins une structure dentaire (C_ ou R_)
                has_structures = any(
                    name.startswith(('C_', 'R_')) 
                    for name in self.viewer.contours.keys()
                )
            
               
           
            # Le bouton est actif si on a les deux
            can_generate = has_rtdose and has_structures
            
            self.btn_generate_report.configure(
                state='normal' if can_generate else 'disabled'
            )
            
            # Afficher un tooltip explicatif si désactivé
            if not can_generate:
                if not has_rtdose:
                    tooltip_text = "Chargez d'abord un fichier RTDose"
                elif not has_structures:
                    tooltip_text = "Générez d'abord les cylindres dentaires"
                else:
                    tooltip_text = "Données insuffisantes"
            print(f"[DEBUG RAPPORT] État du bouton de génération:")
            print(f"  - RTDose présent: {has_rtdose}")
            print(f"  - RTDose type: {type(self.viewer.rtdose_data) if hasattr(self.viewer, 'rtdose_data') else 'N/A'}")
            print(f"  - Structures dentaires: {has_structures}")
            if hasattr(self.viewer, 'contours'):
                dental_structures = [name for name in self.viewer.contours.keys() if name.startswith(('C_', 'R_'))]
                print(f"  - Nombre structures dentaires: {len(dental_structures)}")
                if dental_structures:
                    print(f"  - Exemples: {dental_structures[:3]}")
            print(f"  - Bouton actif: {can_generate}")
        
        # Mise à jour du statut principal
        point_count = len(self.viewer.tooth_editor.points) if hasattr(self.viewer.tooth_editor, 'points') else 0
        
        if is_complete:
            status = "✅ 6 points placés - Prêt pour génération"
            color = "green"
        elif has_points:
            status = f"⏳ {point_count}/6 points de référence"
            color = "orange"
        else:
            status = "Aucun point placé"
            color = "gray"
            
        #self.tooth_status_label.config(text=status, foreground=color)
        
        # Mise à jour des informations de sélection
        if is_editing and hasattr(self.viewer.tooth_editor, 'selected_group'):
            selected_count = len(getattr(self.viewer.tooth_editor, 'selected_group', set()))
            if selected_count > 0:
                selected_names = sorted(list(self.viewer.tooth_editor.selected_group))
                if selected_count <= 3:
                    selection_text = f"Sélection: {', '.join(selected_names)}"
                else:
                    selection_text = f"Sélection: {selected_count} points ({', '.join(selected_names[:2])}, ...)"
                self.selection_info_label.config(text=selection_text, foreground="blue")
            else:
                self.selection_info_label.config(text="", foreground="blue")
        else:
            self.selection_info_label.config(text="", foreground="blue")
    
    def update_display_after_config_change(self):
        """Met à jour l'affichage après modification de la configuration"""
        try:
            # Actualiser les couleurs de dose si nécessaire
            if hasattr(self.viewer, 'dose_data') and self.viewer.dose_data is not None:
                # Recharger la configuration et mettre à jour l'affichage de la dose
                from config_manager import ConfigManager
                config_manager = ConfigManager()
                new_thresholds = config_manager.get_risk_thresholds()
                
                # Mettre à jour les seuils du viewer si nécessaire
                if hasattr(self.viewer, 'dose_threshold'):
                    self.viewer.dose_threshold = new_thresholds['low']
                
                # Rafraîchir l'affichage
                self.viewer.update_display()
                
            print("[INFO] Affichage mis à jour après changement de configuration")
            
        except Exception as e:
            print(f"[ATTENTION] Impossible de mettre à jour l'affichage: {e}")
    
    # 6. INTÉGRATION AVEC LE GÉNÉRATEUR DE RAPPORT
    
    def generate_dose_report(self):
        """Lance le générateur de rapport dosimétrique avec la config actuelle"""
        try:
            from dose_report_generator import DoseReportGenerator
            
            # Le générateur utilisera automatiquement ConfigManager pour les seuils
            report_generator = DoseReportGenerator(self.viewer)
            
            # Vérifier si une configuration personnalisée est active
            try:
                from config_manager import ConfigManager
                config_manager = ConfigManager()
                config_info = config_manager.get_config_info()
                
                if config_info['active_type'] != 'default':
                    from tkinter import messagebox
                    msg = f"Configuration {config_info['active_type']} active.\n"
                    msg += "Le rapport utilisera les seuils et commentaires d'analyse."
                    messagebox.showinfo("Configuration active", msg)
            
            except Exception:
                pass  # ConfigManager non disponible, continuer normalement
            
            # Générer le rapport
            report_generator.show_report_dialog()
            
        except ImportError as e:
            from tkinter import messagebox
            messagebox.showerror(
                "Module manquant",
                f"Module de rapport dosimétrique non disponible:\n{str(e)}\n\n"
                "Assurez-vous que dose_report_generator.py est présent."
            )
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Erreur", f"Erreur lors de la génération du rapport:\n{str(e)}")
    
    def show_report_config_dialog(self):
        """Affiche le dialogue de configuration des seuils et commentaires d'analyse """
        try:
            # Utiliser la nouvelle classe de configuration
            config_dialog = ReportConfigDialog(self.viewer.master, self.viewer)
            config_dialog.show()
            
            # Optionnel : rafraîchir l'affichage si nécessaire après modification de la config
            # self.viewer.update_display()
            
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Erreur Configuration", 
                               f"Impossible d'ouvrir la configuration des seuils:\n{str(e)}")
            
            # Log pour debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur dialogue configuration: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
    
    
    

    
