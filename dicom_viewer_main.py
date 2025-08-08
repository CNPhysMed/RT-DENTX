#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visualiseur DICOM principal - Version avec pan clic molette et génération corrigée
Interface principale avec toutes les fonctionnalités - 
© 2025 Caroline Moreau-Noblet — RT-DENTX — Licence BSD 3-Clause
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
import logging
import os
from PIL import Image, ImageTk
import ctypes
import sys


# Imports des modules

from tooth_reference_editor import ToothReferenceEditor
from tooth_generator import ToothGenerator
from ui_panels import NavigationPanel, WindowingPanel, ContourPanel, DosePanel, ToothPanel
from improved_about_dialogs import (
    improved_show_about_rt_dentx, 
    improved_show_sources,
    show_splash_screen
)

# Configuration du logging 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
from dicom_loader import DicomLoader

class DicomViewer:
    """Interface principale du visualiseur DICOM - Version sans intégration automatique"""
    
    def __init__(self, master):
        self.master = master
        self.master.title("RT-DENTX")
        self.master.geometry("1600x950")
        self.master.withdraw()  # Cacher la fenêtre au début
        
        self.set_app_user_model_id()
        
        # Variables pour le logo
        self.logo_img = None
        #self.logo_label = None
        
        # Définir l'icône de la fenêtre (barre Windows)
        self.set_window_icon()
        
        # Données DICOM
        self.ct_slices = []
        self.contours = {}
        self.rtdose_data = None
        self.current_slice = 0
        self.folder_path = ""
        
        # Variables d'affichage
        self.ct_window_width = 400
        self.ct_window_center = 40
        self.show_contours = {}
        self.show_dose = False
        self.dose_alpha = 0.6
        self.dose_threshold = 5.0
        self.dose_colorbar = None
        self.manual_dmax = None
        self.current_extent = None
        
        # Système de couleurs pour les structures
        self.structure_colors = {}
        
        # Variables pour la gestion du zoom persistant
        self.saved_xlim = None
        self.saved_ylim = None
        self.zoom_active = False
        self.updating_display = False
        self.navigation_in_progress = False
        
        # Variables pour le pan avec clic molette 
        self.pan_active = False
        self.pan_start_x = None
        self.pan_start_y = None
        self.pan_start_xlim = None
        self.pan_start_ylim = None
        self.pan_last_update = 0
        
        # Éditeurs spécialisés
        self.tooth_editor = None
        self.tooth_generator = None
        
        # Panneaux UI
        self.navigation_panel = None
        self.windowing_panel = None
        self.contour_panel = None
        self.dose_panel = None
        self.tooth_panel = None
        
        self.setup_styles()
        
        # Afficher le splash screen au début
        self.show_splash_screen()
        
        
    
    
    
    
        
    def setup_styles(self):
        """Configure tous les styles personnalisés de l'application"""
        style = ttk.Style()
        
        # Styles pour les LabelFrame
        style.configure("Bold.TLabelframe.Label", font=('Arial', 11, 'bold'))
        
    def set_app_user_model_id(self):
        """Définit un AppUserModelID unique pour Windows - CRITIQUE pour l'icône"""
        try:
            if sys.platform.startswith('win'):
                # Définir un ID unique pour votre application
                app_id = 'CarolineNoblet.RTDentX.DosimetrieRadiotherapie.1.0'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
                print("✅ AppUserModelID défini")
        except Exception as e:
            print(f"⚠️ Erreur AppUserModelID: {e}")
            
    
    def create_ico_file(self):
        """Crée un fichier ICO de haute qualité avec antialiasing optimisé"""
        try:
            png_path = "assets/rt_dentx_logo.png"
            ico_path = "assets/rt_dentx_logo.ico"
            
            if not os.path.exists(png_path):
                print(f"❌ Fichier {png_path} non trouvé")
                return None
            
            # Supprimer l'ancien ICO pour forcer la régénération
            if os.path.exists(ico_path):
                os.remove(ico_path)
                print("🗑️ Ancien fichier ICO supprimé")
            
            print("🔄 Création du fichier ICO haute qualité...")
            
            # Ouvrir l'image source
            img = Image.open(png_path)
            
            max_size = max(img.size)
        
            # Créer une nouvelle image carrée transparente
            square_img = Image.new('RGBA', (max_size, max_size), (0, 0, 0, 0))
            
            # Calculer la position pour centrer le logo
            paste_x = (max_size - img.size[0]) // 2
            paste_y = (max_size - img.size[1]) // 2
            
            # Coller le logo au centre de l'image carrée
            square_img.paste(img, (paste_x, paste_y), img if img.mode == 'RGBA' else None)
            
            print(f"📐 Logo original: {img.size} → Carré: {square_img.size}")
            print(f"   Position du logo: ({paste_x}, {paste_y})")
            
            # Utiliser l'image carrée centrée pour la suite
            img = square_img
            
            # Convertir en RGBA pour la transparence
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # IMPORTANT: Tailles Windows standard complètes incluant le DPI scaling
            sizes = [
                #(16, 16),    # Petites icônes (explorateur, menus)
                #(20, 20),    # 125% DPI
                #(24, 24),    # 150% DPI
                #(32, 32),    # Icônes standard
                #(40, 40),    # 125% DPI pour icônes moyennes
                #(48, 48),    # 150% DPI pour icônes moyennes
                #(64, 64),    # 200% DPI
                #(80, 80),    # 250% DPI
                #(96, 96),    # 300% DPI
                #(128, 128)  # Très grandes icônes
                (256, 256)   # Barre des tâches Windows 10/11
                #(512, 512),  # Pour les écrans 4K et futures versions Windows
                #(1024, 1024) #Ultra haute résolution pour la compatibilité future
            ]
            
            # Créer les images redimensionnées individuellement
            ico_images = []
            
            for target_size in sizes:
                # Redimensionner avec LANCZOS
                resized = img.resize(target_size, Image.Resampling.LANCZOS)
                
                # Améliorer la netteté selon la taille
                from PIL import ImageEnhance
                
                if target_size[0] <= 32:
                    # Plus de netteté pour les petites icônes
                    sharpener = ImageEnhance.Sharpness(resized)
                    resized = sharpener.enhance(1.8)
                elif target_size[0] <= 48:
                    # Netteté modérée pour les icônes moyennes
                    sharpener = ImageEnhance.Sharpness(resized)
                    resized = sharpener.enhance(1.4)
                elif target_size[0] >= 256:
                   # Légère amélioration pour les grandes tailles
                   sharpener = ImageEnhance.Sharpness(resized)
                   resized = sharpener.enhance(1.1)
               
                # S'assurer que chaque image est en RGBA
                if resized.mode != 'RGBA':
                    resized = resized.convert('RGBA')
                
                ico_images.append(resized)
            
            # Sauvegarder l'ICO - Méthode corrigée
            # Utiliser la première image comme base et ajouter les autres
            ico_images[0].save(
                ico_path, 
                format='ICO', 
                sizes=sizes,
                append_images=ico_images[1:],
                # Options supplémentaires pour la qualité
                quality=100,
                bitmap_format='bmp'
                #save_all=True
            )
            
            print(f"✅ Fichier ICO ultra haute qualité créé: {ico_path}")
            print(f"   Tailles incluses: {len(sizes)} résolutions (max: 1024x1024)")
            print(f"   512x512 et 1024x1024 inclus: Oui (futures versions Windows)")
            
            # Vérifier la taille du fichier
            file_size = os.path.getsize(ico_path) / 1024
            print(f"   Taille du fichier: {file_size:.1f} KB")
            
            # Vérification supplémentaire du contenu
            self.verify_ico_content(ico_path)
            
            return ico_path
            
        except Exception as e:
            print(f"❌ Erreur création ICO: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def verify_ico_content(self, ico_path):
        """Vérifie que l'ICO contient bien toutes les tailles"""
        try:
            test_ico = Image.open(ico_path)
            if hasattr(test_ico, 'ico'):
                available_sizes = test_ico.ico.sizes()
                print(f"   Vérification: {len(available_sizes)} tailles trouvées")
                if (256, 256) not in available_sizes:
                    print("   ⚠️ ATTENTION: Taille 256x256 manquante!")
            test_ico.close()
        except:
            pass
    
    
        
    def set_window_icon(self):
        """Définit l'icône de la fenêtre pour la barre Windows """
        
        ico_path = None
        
        try:
            # Étape 1: Créer le fichier ICO
            ico_path = self.create_ico_file()
            
            if ico_path and os.path.exists(ico_path):
                # Étape 2: Attendre que la fenêtre soit prête
                self.master.after(100, lambda: self.apply_icon_after_window_ready(ico_path))
            else:
                print("❌ Impossible de créer le fichier ")
                
        except Exception as e:
            print(f"❌ Erreur set_window_icon_ultimate: {e}")
            
    def apply_icon_after_window_ready(self, ico_path):
        """Applique l'icône après que la fenêtre soit prête"""
        try:
            # Méthode 1: iconbitmap (pour la barre des tâches)
            if os.path.exists(ico_path):
                self.master.iconbitmap(ico_path)
                print("✅ iconbitmap appliqué")
            
            # Méthode 2: iconphoto (pour le titre de fenêtre)
            png_path = "rt_dentx_logo.png"
            if os.path.exists(png_path):
                icon_img = Image.open(png_path)
                
                # Créer plusieurs tailles PhotoImage
                for size in [16, 32, 48]:
                    resized = icon_img.resize((size, size), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(resized)
                    
                    # Appliquer l'icône
                    self.master.iconphoto(True, photo)
                    
                    # Garder la référence
                    if not hasattr(self.master, 'icon_references'):
                        self.master.icon_references = []
                    self.master.icon_references.append(photo)
                
                print("✅ iconphoto appliqué")
            
            # Méthode 3: Windows API direct (solution de force)
            self.set_icon_via_windows_api(ico_path)
            
        except Exception as e:
            print(f"❌ Erreur apply_icon_after_window_ready: {e}")
            import traceback
            traceback.print_exc()
    
    def set_icon_via_windows_api(self, ico_path):
        """Force l'icône via l'API Windows directe"""
        try:
            if not sys.platform.startswith('win') or not os.path.exists(ico_path):
                return
            
            import ctypes
            
            # Attendre que la fenêtre ait un handle valide
            self.master.update_idletasks()
            
            # Obtenir le handle de la fenêtre
            hwnd = self.master.winfo_id()
            
            if hwnd:
                # Charger l'icône depuis le fichier ICO
                hicon_small = ctypes.windll.user32.LoadImageW(
                    0,  # hInst
                    ico_path,  # name
                    1,  # IMAGE_ICON
                    16,  # cx
                    16,  # cy
                    0x00000010  # LR_LOADFROMFILE
                )
                
                hicon_big = ctypes.windll.user32.LoadImageW(
                    0,  # hInst
                    ico_path,  # name
                    1,  # IMAGE_ICON
                    32,  # cx
                    32,  # cy
                    0x00000010  # LR_LOADFROMFILE
                )
                
                if hicon_small:
                    # WM_SETICON, ICON_SMALL
                    ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, hicon_small)
                    print("✅ Icône petite définie via API Windows")
                
                if hicon_big:
                    # WM_SETICON, ICON_BIG
                    ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, hicon_big)
                    print("✅ Icône grande définie via API Windows")
                
                # Forcer le rafraîchissement de la barre des tâches
                self.refresh_taskbar_icon()
                
        except Exception as e:
            print(f"⚠️ API Windows non disponible: {e}")
    
    def refresh_taskbar_icon(self):
        """Force le rafraîchissement de l'icône dans la barre des tâches"""
        try:
            if sys.platform.startswith('win'):
                import ctypes
                
                # Obtenir le handle de la fenêtre
                hwnd = self.master.winfo_id()
                
                if hwnd:
                    # Forcer la mise à jour de la barre des tâches
                    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)  # SHCNE_ASSOCCHANGED
                    
                    # Alternative: redessiner la fenêtre
                    ctypes.windll.user32.RedrawWindow(hwnd, None, None, 0x0001 | 0x0004)  # RDW_INVALIDATE | RDW_UPDATENOW
                    
                    print("✅ Rafraîchissement barre des tâches demandé")
                
        except Exception as e:
            print(f"⚠️ Erreur rafraîchissement: {e}")
                
    
    def convert_png_to_ico(self):
        """Convertit le PNG en fichier ICO permanent"""
        try:
            png_path = "assets\rt_dentx_logo.png"
            ico_path = "assets\rt_dentx_logo.ico"
            
            if os.path.exists(png_path) and not os.path.exists(ico_path):
                print("🔄 Conversion PNG → ICO...")
                
                # Ouvrir l'image PNG
                img = Image.open(png_path)
                
                # Convertir en mode RGBA si nécessaire
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Créer plusieurs tailles pour un meilleur rendu
                sizes = [(16, 16), (24, 24), (32, 32), (48, 48)]
                
                # Sauvegarder en .ico
                img.save(ico_path, format='ICO', sizes=sizes)
                
                print("✅ Fichier rt_dentx_logo.ico créé")
                return True
            elif os.path.exists(ico_path):
                print("✅ Fichier rt_dentx_logo.ico existe déjà")
                return True
            else:
                print("❌ Aucun fichier PNG trouvé pour la conversion")
                return False
                
        except Exception as e:
            print(f"❌ Erreur conversion ICO: {e}")
            return False
    
    def load_main_logo(self):
        """Charge le logo principal pour l'affichage dans l'interface"""
        try:
            logo_path = "assets/rt_dentx_logo.png"
            
            if os.path.exists(logo_path):
                # Charger et redimensionner pour l'affichage principal
                img = Image.open(logo_path)
                # Taille pour l'affichage dans l'interface (plus grand)
                img = img.resize((240, 240), Image.Resampling.LANCZOS)
                # Améliorer la netteté après redimensionnement
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.1)  # Légère amélioration de la netteté
                
                self.logo_img = ImageTk.PhotoImage(img)
                return True
            else:
                print("⚠️ Logo rt_dentx_logo.png non trouvé")
                return False
                
        except Exception as e:
            print(f"❌ Erreur chargement logo principal: {e}")
            return False
    
    
    
    def detect_spyder(self):
        """Détecte si on est dans Spyder"""
        import sys
        return 'spyder' in sys.modules or 'spyder_kernels' in sys.modules
    
    def show_splash_screen(self):
        """Affiche l'écran de démarrage - Version compatible Spyder"""
        if self.detect_spyder():
            print("🔍 Spyder détecté - Splash simplifié")
            self.show_spyder_safe_splash()
        else:
            # Utiliser le splash normal
            try:
                from improved_about_dialogs import show_splash_screen
                show_splash_screen(self.master, self.on_splash_accept, self.on_splash_decline)
            except Exception as e:
                print(f"⚠️ Erreur splash normal: {e}")
                self.show_spyder_safe_splash()
    
    def show_spyder_safe_splash(self):
        """Splash screen compatible Spyder"""
        try:
            # Créer la fenêtre splash directement
            splash = tk.Toplevel(self.master)
            splash.title("RT-DENTX - Conditions d'utilisation")
            splash.geometry("500x400")
            splash.configure(bg='#f0f0f0')
            
            # Centrer
            splash.update_idletasks()
            x = (splash.winfo_screenwidth() // 2) - 250
            y = (splash.winfo_screenheight() // 2) - 200
            splash.geometry(f"500x400+{x}+{y}")
            
            def on_accept():
                print("✅ Conditions acceptées")
                splash.destroy()
                self.on_splash_accept()
            
            def on_decline():
                print("❌ Conditions déclinées")
                splash.destroy()
                self.on_splash_decline()
            
            # Contenu simplifié
            main_frame = tk.Frame(splash, bg='#f0f0f0')
            main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
            
            # Titre
            tk.Label(main_frame, text="RT-DENTX", 
                    font=('Arial', 20, 'bold'),
                    bg='#f0f0f0', fg='#2c3e50').pack(pady=(10, 5))
            
            tk.Label(main_frame, text="DENTal eXposure in Radiation Therapy",
                    font=('Arial', 12),
                    bg='#f0f0f0', fg='#5dade2').pack(pady=(0, 20))
            
            # Conditions
            conditions = """Logiciel libre pour l'évaluation dosimétrique dentaire
    en radiothérapie de la sphère ORL
    
    Auteur: Caroline MOREAU-NOBLET
    Version: 1.0 | Licence: BSD 3-Clause
    
    ⚠️ USAGE RECHERCHE ET ENSEIGNEMENT UNIQUEMENT
    
    Ce logiciel ne constitue pas un dispositif médical validé.
    L'utilisateur assume l'entière responsabilité de l'utilisation."""
            
            tk.Label(main_frame, text=conditions,
                    font=('Arial', 9), bg='#f0f0f0', fg='#34495e',
                    justify=tk.CENTER).pack(pady=20)
            
            # Boutons
            button_frame = tk.Frame(main_frame, bg='#f0f0f0')
            button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)
            
            tk.Button(button_frame, text="Décliner", 
                     font=('Arial', 12, 'bold'),
                     bg='#e74c3c', fg='white',
                     padx=20, pady=10,
                     command=on_decline).pack(side=tk.LEFT)
            
            tk.Button(button_frame, text="Accepter", 
                     font=('Arial', 12, 'bold'),
                     bg='#27ae60', fg='white',
                     padx=20, pady=10,
                     command=on_accept).pack(side=tk.RIGHT)
            
            # Empêcher fermeture par X
            splash.protocol("WM_DELETE_WINDOW", on_decline)
            
            # Afficher
            splash.lift()
            splash.focus_force()
            
        except Exception as e:
            print(f"❌ Erreur splash Spyder: {e}")
            # En cas d'erreur, lancer directement
            self.on_splash_accept()
    
    def show_splash_screen(self):
        """Affiche l'écran de démarrage"""
        show_splash_screen(self.master, self.on_splash_accept, self.on_splash_decline)
    
    def on_splash_accept(self):
        """Appelé quand l'utilisateur accepte les conditions"""
        # Afficher la fenêtre principale
        self.master.deiconify()
        
        # Continuer l'initialisation de l'interface
        self.setup_ui()
        self.setup_keyboard_bindings()
        self.master.focus_set()
        
    def on_splash_decline(self):
        """Appelé quand l'utilisateur décline les conditions"""
        # Fermer l'application
        self.master.quit()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur modulaire"""
        # Menu principal
        self.setup_menu()
        
        # Layout principal
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # *** SUPPRIMEZ CETTE LIGNE ***
        # self.setup_header_with_logo(main_frame)
        
        # Panel gauche pour les contrôles
        self.setup_left_panel(main_frame)
        
        # Zone d'affichage centrale avec panneau droit
        self.setup_display_area(main_frame)
        
        # Barre d'état
        self.setup_status_bar()
    
    def setup_menu(self):
        """Configuration du menu"""
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)
        
        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Ouvrir dossier DICOM...", command=self.open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.master.quit)
        
        # Menu Affichage
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Affichage", menu=view_menu)
        view_menu.add_command(label="Réinitialiser vue", command=self.reset_view)
        view_menu.add_command(label="Ajuster fenêtrage", command=self.auto_window_level)
        
        # Menu À propos
        apropos_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="À propos", menu=apropos_menu)
        apropos_menu.add_command(label="Raccourcis", command=self.show_shortcuts)
        apropos_menu.add_command(label="Sources", command=self.show_sources)
        apropos_menu.add_command(label="À propos de RT-DENTX", command=self.show_about_rt_dentx)
        
    


    
    
    
    def show_sources(self):
        """Affiche le dialogue Sources amélioré"""
        improved_show_sources(self.master)
    
    def show_about_rt_dentx(self):
        """Affiche le dialogue À propos de RT-DENTX amélioré"""
        improved_show_about_rt_dentx(self.master)   

    
    
    def setup_left_panel(self, parent):
        """Configuration du panneau gauche avec les contrôles principaux"""
        control_frame = ttk.Frame(parent, width=320)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        control_frame.pack_propagate(False)
        
        # Canvas scrollable pour les contrôles
        self.control_canvas = tk.Canvas(control_frame, highlightthickness=0, bg='#f0f0f0')
        self.control_scrollbar = ttk.Scrollbar(control_frame, orient="vertical", 
                                              command=self.control_canvas.yview)
        self.scrollable_control_frame = ttk.Frame(self.control_canvas)
        
        # Configuration scrolling
        def configure_scroll_region(event=None):
            self.control_canvas.configure(scrollregion=self.control_canvas.bbox("all"))
            canvas_width = self.control_canvas.winfo_width()
            self.control_canvas.itemconfig(self.canvas_window, width=canvas_width)
        
        self.scrollable_control_frame.bind("<Configure>", configure_scroll_region)
        self.control_canvas.bind("<Configure>", configure_scroll_region)
        
        self.canvas_window = self.control_canvas.create_window(
            (0, 0), window=self.scrollable_control_frame, anchor="nw")
        self.control_canvas.configure(yscrollcommand=self.control_scrollbar.set)
        
        self.control_scrollbar.pack(side="right", fill="y")
        self.control_canvas.pack(side="left", fill="both", expand=True)
        
        # Initialiser les panneaux modulaires
        self.setup_control_panels()
    
    def setup_control_panels(self):
        """Configuration des panneaux de contrôle modulaires"""
        # Information patient
        info_frame = ttk.LabelFrame(self.scrollable_control_frame, text="Informations Patient", padding=10, style="Bold.TLabelframe")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        self.patient_info = ttk.Label(info_frame, text="Aucun patient chargé", font=('Arial', 9))
        self.patient_info.pack(anchor=tk.W)
        
        # Panneaux modulaires
        self.navigation_panel = NavigationPanel(self.scrollable_control_frame, self)
        self.windowing_panel = WindowingPanel(self.scrollable_control_frame, self)
        self.contour_panel = ContourPanel(self.scrollable_control_frame, self)
        self.dose_panel = DosePanel(self.scrollable_control_frame, self)
    
    def setup_display_area(self, parent):
        """Configuration de la zone d'affichage avec panneau droit"""
        display_frame = ttk.Frame(parent)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Frame principal pour l'affichage
        display_main_frame = ttk.Frame(display_frame)
        display_main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Zone image (gauche de la zone d'affichage)
        image_frame = ttk.Frame(display_main_frame)
        image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Panneau droit pour les outils dentaires
        self.tooth_panel = ToothPanel(display_main_frame, self)
        
       
        # Le ToothPanel dans ui_panels.py gère déjà le bouton de rapport
        logger.info("✅ Interface dentaire configurée (sans intégration automatique)")
        
        # Configuration matplotlib
        self.setup_matplotlib(image_frame)
    
    def setup_matplotlib(self, parent):
        """Configuration de l'affichage matplotlib"""
        self.fig = Figure(figsize=(10, 8), facecolor='black')
        self.ax = self.fig.add_subplot(111, facecolor='black')
        
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        toolbar = NavigationToolbar2Tk(self.canvas, parent)
        toolbar.update()
        
        # Configuration des axes
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_title("Aucune image chargée", color='white', fontsize=14)
        
        # Événements
        self.setup_canvas_events()
        self.canvas.draw()
    
    def setup_canvas_events(self):
        """Configuration des événements du canvas - AVEC PAN CLIC MOLETTE"""
        # Navigation molette et événements souris
        self.canvas.mpl_connect('scroll_event', self.on_matplotlib_scroll)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        
        # NOUVEAU: Événements pour le pan avec clic molette
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release_canvas)
        
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.focus_set()
        canvas_widget.bind('<MouseWheel>', self.wheel_handler, '+')
        canvas_widget.bind('<Button-4>', self.wheel_up_handler, '+')
        canvas_widget.bind('<Button-5>', self.wheel_down_handler, '+')
        canvas_widget.bind('<Enter>', lambda e: canvas_widget.focus_set())
        self.master.bind('<MouseWheel>', self.wheel_handler_global, '+')
        
        # Événements pour détecter les changements de zoom
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
    
    def setup_status_bar(self):
        """Configuration de la barre d'état avec copyright"""
        self.status_frame = ttk.Frame(self.master)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Frame pour organiser les éléments de la barre d'état
        status_content = ttk.Frame(self.status_frame)
        status_content.pack(fill=tk.X, padx=5, pady=2)
        
        # Label pour les coordonnées (AJOUTER CETTE LIGNE)
        self.coord_label = ttk.Label(status_content, text="")
        self.coord_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Barre d'état principale (côté gauche)
        self.status_label = ttk.Label(status_content, text="Prêt")
        self.status_label.pack(side=tk.LEFT)
        
        # Copyright (côté droit)
        copyright_text = "RT-DENTX — © 2025 Caroline Moreau-Noblet — Licence BSD 3-Clause — Usage académique uniquement"
        
        self.copyright_label = ttk.Label(
            status_content, 
            text=copyright_text,
            font=('Arial', 8, 'italic'),
            foreground='gray'
        )
        self.copyright_label.pack(side=tk.RIGHT)
        
    def on_mouse_press(self, event):
        """Gestion du clic souris - AVEC PAN CLIC MOLETTE"""
        if event.button == 2 and event.inaxes == self.ax:  # Clic molette
            self.pan_active = True
            self.pan_start_x = event.xdata
            self.pan_start_y = event.ydata
            self.pan_start_xlim = self.ax.get_xlim()
            self.pan_start_ylim = self.ax.get_ylim()
            logger.debug(f"Pan démarré à ({event.xdata:.1f}, {event.ydata:.1f})")
    
    def on_mouse_release_canvas(self, event):
        """Gestion du relâchement souris pour le pan"""
        if event.button == 2 and self.pan_active:  # Relâchement clic molette
            self.pan_active = False
            # Sauvegarder la nouvelle position après pan
            self.save_current_zoom()
            logger.debug("Pan terminé")
    
    def on_mouse_release(self, event):
        """Détecte les changements de zoom après relâchement de souris"""
        if event.inaxes == self.ax and not self.updating_display and not self.navigation_in_progress:
            # Attendre que matplotlib termine ses calculs
            self.master.after(100, self.save_current_zoom)
    
    def save_current_zoom(self):
        """Sauvegarde le zoom actuel"""
        if not self.ct_slices or self.updating_display or self.navigation_in_progress:
            return
            
        current_xlim = self.ax.get_xlim()
        current_ylim = self.ax.get_ylim()
        
        # Vérifier si on est dans les limites par défaut
        if hasattr(self, 'current_extent') and self.current_extent:
            default_xlim = (self.current_extent[0], self.current_extent[1])
            default_ylim = (self.current_extent[2], self.current_extent[3])
            
            # Tolérance pour déterminer si on est zoomé
            tolerance = 10.0  # mm
            
            x_diff = max(abs(current_xlim[0] - default_xlim[0]), 
                        abs(current_xlim[1] - default_xlim[1]))
            y_diff = max(abs(current_ylim[0] - default_ylim[0]), 
                        abs(current_ylim[1] - default_ylim[1]))
            
            if x_diff > tolerance or y_diff > tolerance:
                # On est zoomé - sauvegarder seulement si différent de la sauvegarde actuelle
                if (self.saved_xlim is None or self.saved_ylim is None or
                    abs(current_xlim[0] - self.saved_xlim[0]) > 1.0 or
                    abs(current_xlim[1] - self.saved_xlim[1]) > 1.0 or
                    abs(current_ylim[0] - self.saved_ylim[0]) > 1.0 or
                    abs(current_ylim[1] - self.saved_ylim[1]) > 1.0):
                    
                    self.saved_xlim = current_xlim
                    self.saved_ylim = current_ylim
                    self.zoom_active = True
                    logger.info(f"Zoom sauvegardé: X={current_xlim}, Y={current_ylim}")
            else:
                # On est au zoom par défaut
                self.saved_xlim = None
                self.saved_ylim = None
                self.zoom_active = False
                logger.info("Zoom désactivé (retour vue par défaut)")
    
    def setup_keyboard_bindings(self):
        """Configuration des raccourcis clavier globaux"""
        # Raccourcis de navigation existants
        self.master.bind_all('<Left>', self.on_key_left)
        self.master.bind_all('<Right>', self.on_key_right)
        self.master.bind_all('<Up>', self.on_key_up)
        self.master.bind_all('<Down>', self.on_key_down)
        self.master.bind_all('<Control-o>', lambda e: self.open_folder())
        self.master.bind_all('<Control-O>', lambda e: self.open_folder())
        
        # Raccourcis pour le zoom
        self.master.bind_all('<Control-plus>', lambda e: self.zoom_in())
        self.master.bind_all('<Control-equal>', lambda e: self.zoom_in())
        self.master.bind_all('<Control-KP_Add>', lambda e: self.zoom_in())
        self.master.bind_all('<Control-minus>', lambda e: self.zoom_out())
        self.master.bind_all('<Control-KP_Subtract>', lambda e: self.zoom_out())
        self.master.bind_all('<Control-0>', lambda e: self.reset_view())
        
        
        
        # Raccourcis dentaires
        self.master.bind_all('<Control-t>', lambda e: self.start_tooth_placement() if hasattr(self, 'start_tooth_placement') else None)
        self.master.bind_all('<Control-e>', lambda e: self.toggle_tooth_edit_mode() if hasattr(self, 'toggle_tooth_edit_mode') else None)
        self.master.bind_all('<Control-g>', lambda e: self.generate_other_teeth() if hasattr(self, 'generate_other_teeth') else None)
        self.master.bind_all('<Control-G>', lambda e: self.generate_tooth_cylinders() if hasattr(self, 'generate_tooth_cylinders') else None)
        self.master.bind_all('<Control-i>', lambda e: self.show_tooth_info() if hasattr(self, 'show_tooth_info') else None)
        
        # Alternatives avec Alt
        self.master.bind_all('<Alt-e>', lambda e: self.export_tooth_data() if hasattr(self, 'export_tooth_data') else None)
        self.master.bind_all('<Alt-v>', lambda e: self.validate_tooth_placement() if hasattr(self, 'validate_tooth_placement') else None)
        
        
    
    # === Méthodes de navigation clavier ===
    def on_key_left(self, event):
        if isinstance(event.widget, tk.Entry):
            return
        self.navigate_with_zoom_preservation(self.previous_slice)
        return "break"
    
    def on_key_right(self, event):
        if isinstance(event.widget, tk.Entry):
            return
        self.navigate_with_zoom_preservation(self.next_slice)
        return "break"
    
    def on_key_up(self, event):
        if isinstance(event.widget, tk.Entry):
            return
        if self.ct_slices:
            new_slice = max(0, self.current_slice - 10)
            if hasattr(self.navigation_panel, 'slice_var'):
                self.navigation_panel.slice_var.set(new_slice)
        return "break"
    
    def on_key_down(self, event):
        if isinstance(event.widget, tk.Entry):
            return
        if self.ct_slices:
            new_slice = min(len(self.ct_slices) - 1, self.current_slice + 10)
            if hasattr(self.navigation_panel, 'slice_var'):
                self.navigation_panel.slice_var.set(new_slice)
        return "break"
    
    def navigate_with_zoom_preservation(self, navigation_func):
        """Navigue en préservant le zoom"""
        # Sauvegarder le zoom AVANT la navigation
        if not self.navigation_in_progress:
            self.save_current_zoom()
        
        # Marquer qu'on est en navigation
        self.navigation_in_progress = True
        
        # Effectuer la navigation
        navigation_func()
        
        # Remettre le flag après la navigation
        self.master.after(50, self.end_navigation)
    
    def end_navigation(self):
        """Termine le processus de navigation"""
        self.navigation_in_progress = False
    
    # === Méthodes de chargement ===
    def open_folder(self):
        """Ouvre un dossier DICOM - Utilise DicomLoader"""
        folder = filedialog.askdirectory(title="Sélectionner le dossier DICOM")
        if not folder:
            return
        
        self.set_status("Chargement des données DICOM...")
        self.master.update()
        
        try:
            # Utiliser les modules de chargement
            self.folder_path = folder
            self.ct_slices = DicomLoader.load_ct_series(folder)
            self.contours = DicomLoader.load_rtstruct(folder, self.ct_slices)
            self.rtdose_data = DicomLoader.load_rtdose(folder)
            
            self.setup_after_loading()
            
            self.set_status(f"Chargé: {len(self.ct_slices)} coupes CT, "
                          f"{len(self.contours)} structures")
            
        except Exception as e:
            error_msg = f"Erreur lors du chargement:\n{str(e)}"
            messagebox.showerror("Erreur", error_msg)
            self.set_status("Erreur de chargement")
            logger.error(f"Erreur chargement: {e}")
    
    def setup_after_loading(self):
        """Configuration après chargement - Initialise les modules"""
        # Configuration navigation
        if hasattr(self.navigation_panel, 'slice_scale'):
            self.navigation_panel.slice_scale.configure(to=len(self.ct_slices) - 1)
        self.current_slice = len(self.ct_slices) // 2
        if hasattr(self.navigation_panel, 'slice_var'):
            self.navigation_panel.slice_var.set(self.current_slice)
        
        # Information patient
        if self.ct_slices:
            ds = self.ct_slices[0]
            patient_name = getattr(ds, 'PatientName', 'Inconnu')
            patient_id = getattr(ds, 'PatientID', 'Inconnu')
            study_date = getattr(ds, 'StudyDate', 'Inconnue')
            
            info_text = f"Patient: {patient_name}\nID: {patient_id}\nDate: {study_date}"
            self.patient_info.config(text=info_text)
        
        # Initialiser l'éditeur de dents
        self.tooth_editor = ToothReferenceEditor(
            self.ax, self.canvas, 
            lambda: self.current_slice, 
            self
        )
        
        # Configuration des autres panneaux
        if self.contour_panel:
            self.contour_panel.setup_contour_checkboxes()
        
        # Configuration dose
        if self.rtdose_data and self.dose_panel:
            self.dose_panel.enable_dose_controls()
            try:
                dose_array = self.rtdose_data.pixel_array.astype(np.float32)
                if hasattr(self.rtdose_data, 'DoseGridScaling'):
                    dose_array *= float(self.rtdose_data.DoseGridScaling)
                self.manual_dmax = np.max(dose_array)
                if hasattr(self.dose_panel, 'dose_max_entry_var'):
                    self.dose_panel.dose_max_entry_var.set(f"{self.manual_dmax:.1f}")
            except Exception as e:
                logger.warning(f"Impossible d'initialiser Dmax: {e}")
                self.manual_dmax = None
        
        # Fenêtrage automatique
        self.auto_window_level()
        
        # Forcer la mise à jour de la région de scroll
        self.master.after(200, self.update_scroll_region)
        
        # Affichage initial
        self.update_display()
    
    def update_scroll_region(self):
        """Met à jour la région de scroll du panel de contrôles"""
        try:
            self.scrollable_control_frame.update_idletasks()
            self.control_canvas.configure(scrollregion=self.control_canvas.bbox("all"))
        except Exception as e:
            logger.debug(f"Erreur update scroll: {e}")
    
    # === Méthodes dentaires ===
    def start_tooth_placement(self):
        """Démarre le placement des points de référence"""
        if self.tooth_editor:
            self.tooth_editor.start_placing_mode()
            if self.tooth_panel:
                self.tooth_panel.update_button_states()
    
    def toggle_tooth_edit_mode(self):
        """Active/désactive le mode édition"""
        if not self.tooth_editor:
            return
            
        if self.tooth_editor.edit_mode:
            self.tooth_editor.stop_interaction()
        else:
            self.tooth_editor.start_edit_mode()
            
        if self.tooth_panel:
            self.tooth_panel.update_button_states()
    
    def stop_tooth_mode(self):
        """Arrête tous les modes d'interaction dentaire"""
        if self.tooth_editor:
            self.tooth_editor.stop_interaction()
        if self.tooth_panel:
            self.tooth_panel.update_button_states()
    
    def stop_tooth_placement(self):
        """Arrête uniquement le mode placement"""
        if self.tooth_editor:
            self.tooth_editor.stop_placing_mode()
        if self.tooth_panel:
            self.tooth_panel.update_button_states()
    
    def stop_tooth_edit(self):
        """Arrête uniquement le mode édition"""
        if self.tooth_editor:
            self.tooth_editor.stop_edit_mode()
        if self.tooth_panel:
            self.tooth_panel.update_button_states()
    
    
    def generate_other_teeth(self):
        """Génère automatiquement les autres dents à partir des points de référence"""
        if not hasattr(self, 'tooth_editor') or not self.tooth_editor or not self.tooth_editor.is_complete():
            print("Il faut d'abord placer les 6 points de référence")
            return
        
        try:
            
            # Toujours créer un nouveau générateur avec les points actuels
            reference_teeth = ['11', '13', '18', '41', '43', '48']  # Les 6 VRAIS points de référence
            reference_points = {name: coords for name, coords in self.tooth_editor.points.items() 
                              if name in reference_teeth}
            
            # Créer un nouveau générateur avec les points actuels
            self.tooth_generator = ToothGenerator(reference_points)
            
            logger.info(f"Génération avec offset de symétrie fixe: {self.tooth_generator.symmetry_offset}mm")
            logger.info(f"Points de référence utilisés: {list(reference_points.keys())}")
            
            # Générer les points
            generated_points = self.tooth_generator.generate_all_teeth(ct_viewer=self)
            
            # Ajouter les points générés à l'éditeur
            self.tooth_editor.points.update(generated_points)
            self.tooth_editor.draw_all_points()
            
            print(f"Généré {len(generated_points)} points supplémentaires")
            
            # Validation de la symétrie
            if hasattr(self.tooth_generator, 'validate_symmetry'):
                issues = self.tooth_generator.validate_symmetry()
                if not issues:
                    print("✅ Symétrie correcte")
                else:
                    print(f"⚠️ {len(issues)} problèmes de symétrie détectés")
            
            if hasattr(self, 'tooth_panel') and self.tooth_panel:
                self.tooth_panel.update_button_states()
                
        except Exception as e:
            print(f"Erreur génération: {e}")
            import traceback
            traceback.print_exc()
    
    def generate_tooth_cylinders(self):
        """Génère les cylindres 3D dentaires """
        if not hasattr(self, 'tooth_editor') or not self.tooth_editor or len(self.tooth_editor.points) == 0:
            print("Aucun point placé pour la génération 3D")
            return
        
        try:
            
            
            if hasattr(self, 'custom_tooth_config') and self.custom_tooth_config:
                sample_teeth = list(self.custom_tooth_config.keys())[:3]
                for tooth in sample_teeth:
                    config = self.custom_tooth_config[tooth]
            else:
                print(f"[DEBUG] Aucune configuration personnalisée trouvée")
            
            # Utiliser UNIQUEMENT les points actuellement présents
            current_points = self.tooth_editor.points.copy()
            print(f"Génération des cylindres pour {len(current_points)} points présents")
            
            temp_generator = ToothGenerator(current_points)
            
            # S'assurer que le générateur utilise la config du viewer
            if hasattr(self, 'custom_tooth_config'):
                temp_generator.update_viewer_config(self)
            
            # Créer le writer avec la correction des coordonnées
            class FunctionalWriter:
                def __init__(self, folder, ct_viewer):
                    self.ct_folder = folder
                    self.ct_viewer = ct_viewer
                    
                def add_structure(self, name, contours):
                    pass
                
                def add_roi(self, roi_name, contour_points, color=None):
                    try:
                        print(f"  DEBUG: Ajout ROI {roi_name} avec {len(contour_points)} points")
                        
                        slice_contours = {}
                        for point in contour_points:
                            if len(point) >= 3:
                                x_mm, y_mm, z = point[0], point[1], point[2]
                                slice_idx = int(round(z))
                                
                                if slice_idx not in slice_contours:
                                    slice_contours[slice_idx] = []
                                
                                slice_contours[slice_idx].append([x_mm, y_mm])
                        
                        if slice_contours:
                            self.ct_viewer.contours[roi_name] = slice_contours
                            
                            if not hasattr(self.ct_viewer, 'show_contours'):
                                self.ct_viewer.show_contours = {}
                            
                            import tkinter as tk
                            var = tk.BooleanVar(value=True)
                            self.ct_viewer.show_contours[roi_name] = var
                            
                            if color and hasattr(self.ct_viewer, 'structure_colors'):
                                if isinstance(color, list) and len(color) >= 3:
                                    hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                                    self.ct_viewer.structure_colors[roi_name] = hex_color
                            
                            print(f"  ✅ ROI {roi_name} ajouté: {len(slice_contours)} coupes")
                            return True
                        else:
                            print(f"  ❌ ROI {roi_name}: aucune coupe valide")
                            return False
                            
                    except Exception as e:
                        print(f"  ❌ Erreur ajout ROI {roi_name}: {e}")
                        return False
            
            writer = FunctionalWriter(self.folder_path, self)
            
            # Génération avec debug
            temp_generator.generate_3d_cylinders(self, writer)
            
            # Mise à jour de l'affichage
            self.update_display()
            if hasattr(self, 'contour_panel') and self.contour_panel:
                self.contour_panel.setup_contour_checkboxes()
            
            # Message de succès
            crown_count = len([name for name in self.contours.keys() if name.startswith("C_")])
            root_count = len([name for name in self.contours.keys() if name.startswith("R_")])
            
            print("✅ Génération des cylindres 3D terminée")
            print(f"   🟢 {crown_count} couronnes générées")
            print(f"   🔴 {root_count} racines générées")
            
            if hasattr(self, 'tooth_panel') and self.tooth_panel:
                self.tooth_panel.update_button_states()
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération des cylindres 3D: {e}")
            import traceback
            traceback.print_exc()
    
    # Autres méthodes dentaires restent identiques...
    def export_tooth_data(self):
        """Exporte les données dentaires"""
        if not hasattr(self, 'tooth_generator') or not self.tooth_generator:
            print("Aucune donnée dentaire à exporter")
            return
        
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                title="Exporter les données dentaires",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filename and hasattr(self.tooth_generator, 'export_points_to_csv'):
                self.tooth_generator.export_points_to_csv(filename)
                print(f"Données exportées vers {filename}")
        except Exception as e:
            print(f"Erreur export: {e}")
    
    
    
    
    def show_tooth_info(self):
        """Affiche des informations sur les dents"""
        if not hasattr(self, 'tooth_editor') or not self.tooth_editor:
            return
        
        try:
            status = self.tooth_editor.get_completion_status()
            info = f"Points de référence: {status['placed']}/{status['total']} ({status['percentage']:.1f}%)"
            
            if status['missing']:
                info += f"\nPoints manquants: {', '.join(status['missing'])}"
            
            if hasattr(self.tooth_editor, 'selected_group') and self.tooth_editor.selected_group:
                info += f"\nSélection: {len(self.tooth_editor.selected_group)} points"
            
            if hasattr(self, 'tooth_generator') and self.tooth_generator:
                if hasattr(self.tooth_generator, 'generated_points'):
                    info += f"\nPoints générés: {len(self.tooth_generator.generated_points)}"
                
                if hasattr(self.tooth_generator, 'get_symmetry_offset'):
                    info += f"\nOffset symétrie: {self.tooth_generator.get_symmetry_offset()}mm"
            
            from tkinter import messagebox
            messagebox.showinfo("Informations Dentaires", info)
        except Exception as e:
            print(f"Erreur info: {e}")
    
    def validate_tooth_placement(self):
        """Valide le placement des points"""
        if not hasattr(self, 'tooth_editor') or not self.tooth_editor:
            return
        
        try:
            # Validation basique
            if hasattr(self.tooth_editor, 'validate_points'):
                issues = self.tooth_editor.validate_points()
            else:
                # Validation simple si la méthode n'existe pas
                issues = []
                if not self.tooth_editor.is_complete():
                    issues.append("Points de référence incomplets")
            
            from tkinter import messagebox
            if issues:
                messagebox.showwarning("Validation", f"Problèmes:\n" + "\n".join(f"• {issue}" for issue in issues))
            else:
                messagebox.showinfo("Validation", "✅ Placement correct")
        except Exception as e:
            print(f"Erreur validation: {e}")
    
    def clear_all_teeth(self):
        """Efface tous les points de dents avec confirmation"""
        # NOUVEAU: Message de confirmation
        from tkinter import messagebox
        
        # Compter les éléments à supprimer
        points_count = len(self.tooth_editor.points) if self.tooth_editor else 0
        
        # Compter les structures dentaires générées
        dental_structures = [name for name in self.contours.keys() if name.startswith("C_") or name.startswith("R_")]
        structures_count = len(dental_structures)
        
        if points_count == 0 and structures_count == 0:
            messagebox.showinfo("Information", "Aucune donnée dentaire à supprimer.")
            return
        
        # Message de confirmation détaillé
        message = "⚠️ ATTENTION ⚠️\n\n"
        message += "Cette action va supprimer DÉFINITIVEMENT :\n"
        
        if points_count > 0:
            message += f"• {points_count} points de référence placés\n"
        
        if structures_count > 0:
            message += f"• {structures_count} structures dentaires générées\n"
            message += "  (couronnes et racines)\n"
        
        message += "\n❓ Voulez-vous vraiment continuer ?"
        
        # Dialogue de confirmation
        response = messagebox.askyesno(
            "Confirmation de suppression", 
            message,
            icon='warning'
        )
        
        if not response:
            return  # L'utilisateur a annulé
        
        # Effectuer la suppression
        try:
            # Supprimer les points de l'éditeur
            if self.tooth_editor:
                self.tooth_editor.clear_all_points()
            
            # Supprimer les structures dentaires générées
            for structure_name in dental_structures:
                if structure_name in self.contours:
                    del self.contours[structure_name]
                if structure_name in self.show_contours:
                    del self.show_contours[structure_name]
                if structure_name in self.structure_colors:
                    del self.structure_colors[structure_name]
            
            # Supprimer les checkboxes dentaires du panel contours
            if hasattr(self, 'contour_panel') and self.contour_panel:
                self.contour_panel.setup_contour_checkboxes()
            
            # Réinitialiser le générateur
            if hasattr(self, 'tooth_generator'):
                self.tooth_generator = None
            
            # Mettre à jour l'affichage
            self.update_display()
            
            # Mettre à jour l'état des boutons
            if self.tooth_panel:
                self.tooth_panel.update_button_states()
            
            # Message de confirmation
            total_deleted = points_count + structures_count
            messagebox.showinfo(
                "Suppression terminée", 
                f"✅ Suppression réussie!\n\n"
                f"• {points_count} points supprimés\n"
                f"• {structures_count} structures supprimées\n"
                f"• Total: {total_deleted} éléments"
            )
            
            logger.info(f"Suppression dentaire complète: {points_count} points + {structures_count} structures")
        
        except Exception as e:
            error_msg = f"❌ Erreur lors de la suppression:\n{str(e)}"
            messagebox.showerror("Erreur", error_msg)
            logger.error(f"Erreur suppression dentaire: {e}")
            import traceback
            traceback.print_exc()
    
    # === Méthodes de navigation ===
    def on_slice_change(self, value):
        """Callback changement de coupe"""
        if not self.navigation_in_progress:
            self.save_current_zoom()
        
        new_slice = int(float(value))
        self.current_slice = new_slice
        if hasattr(self.navigation_panel, 'update_slice_label'):
            self.navigation_panel.update_slice_label()
        self.update_display()
    
    def previous_slice(self):
        """Coupe précédente"""
        if self.current_slice > 0:
            new_slice = self.current_slice - 1
            self.current_slice = new_slice
            if hasattr(self.navigation_panel, 'slice_var'):
                self.navigation_panel.slice_var.set(new_slice)
            if hasattr(self.navigation_panel, 'update_slice_label'):
                self.navigation_panel.update_slice_label()
            self.update_display()
    
    def next_slice(self):
        """Coupe suivante"""
        if self.ct_slices and self.current_slice < len(self.ct_slices) - 1:
            new_slice = self.current_slice + 1
            self.current_slice = new_slice
            if hasattr(self.navigation_panel, 'slice_var'):
                self.navigation_panel.slice_var.set(new_slice)
            if hasattr(self.navigation_panel, 'update_slice_label'):
                self.navigation_panel.update_slice_label()
            self.update_display()
    
    def first_slice(self):
        """Première coupe"""
        if self.ct_slices and hasattr(self.navigation_panel, 'slice_var'):
            self.navigation_panel.slice_var.set(0)
    
    def last_slice(self):
        """Dernière coupe"""
        if self.ct_slices and hasattr(self.navigation_panel, 'slice_var'):
            self.navigation_panel.slice_var.set(len(self.ct_slices) - 1)
    
    # === Méthodes de fenêtrage ===
    def on_window_change(self, value=None):
        """Callback changement fenêtrage"""
        if hasattr(self.windowing_panel, 'window_width_var'):
            self.ct_window_width = self.windowing_panel.window_width_var.get()
        if hasattr(self.windowing_panel, 'window_center_var'):
            self.ct_window_center = self.windowing_panel.window_center_var.get()
        self.update_display()
    
    def set_window_preset(self, width, center):
        """Applique un preset de fenêtrage"""
        if hasattr(self.windowing_panel, 'window_width_var'):
            self.windowing_panel.window_width_var.set(width)
        if hasattr(self.windowing_panel, 'window_center_var'):
            self.windowing_panel.window_center_var.set(center)
        self.on_window_change()
    
    def auto_window_level(self):
        """Calcul automatique du fenêtrage"""
        if not self.ct_slices:
            return
        
        # Utiliser la coupe actuelle
        ct_slice = self.ct_slices[self.current_slice]
        image_array = ct_slice.pixel_array.astype(np.float32)
        
        if hasattr(ct_slice, 'RescaleSlope') and hasattr(ct_slice, 'RescaleIntercept'):
            image_array = image_array * ct_slice.RescaleSlope + ct_slice.RescaleIntercept
        
        # Calcul statistique
        mean_val = np.mean(image_array)
        std_val = np.std(image_array)
        
        # Fenêtrage basé sur l'écart-type
        center = int(mean_val)
        width = int(4 * std_val)
        
        self.set_window_preset(width, center)
    
    # === Méthodes d'affichage ===
    def update_display(self):
        """Met à jour l'affichage principal"""
        if not self.ct_slices:
            return
    
        # Flag pour éviter les boucles infinies
        self.updating_display = True
        
        try:
            # Effacer l'affichage
            self.ax.clear()
            
            # Configuration des axes
            self.ax.set_facecolor('black')
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            
            # Afficher l'image CT
            self._display_ct_image()
            
            # Afficher les contours
            self._display_contours()
            
            # Afficher la dose si activée
            self._display_dose()
            
            # Afficher les points dentaires
            if self.tooth_editor:
                self.tooth_editor.draw_all_points()
            
            # Finaliser l'affichage
            self._finalize_display()
            
        finally:
            self.updating_display = False
    
    def _display_ct_image(self):
        """Affiche l'image CT"""
        ct_slice = self.ct_slices[self.current_slice]
        
        # Appliquer la correction Hounsfield
        image_array = ct_slice.pixel_array.astype(np.float32)
        if hasattr(ct_slice, 'RescaleSlope') and hasattr(ct_slice, 'RescaleIntercept'):
            image_array = image_array * ct_slice.RescaleSlope + ct_slice.RescaleIntercept
        
        # Calcul de l'extent en coordonnées physiques
        origin = np.array(ct_slice.ImagePositionPatient[:2])
        spacing = np.array(ct_slice.PixelSpacing)
        rows, cols = ct_slice.Rows, ct_slice.Columns
        
        extent = [
            origin[0],
            origin[0] + cols * spacing[0],
            origin[1] + rows * spacing[1],
            origin[1]
        ]
        
        # Affichage avec fenêtrage
        vmin = self.ct_window_center - self.ct_window_width / 2
        vmax = self.ct_window_center + self.ct_window_width / 2
        
        self.ax.imshow(image_array, cmap='gray', 
                      vmin=vmin, vmax=vmax,
                      extent=extent, origin='upper',
                      aspect='equal')
        
        self.current_extent = extent
    
    
    
    def _display_contours(self):
        """Affiche les contours avec couleurs personnalisées"""
        if not self.contours:
            return
            
        # Couleurs par défaut
        default_colors = ['red', 'green', 'blue', 'yellow', 'magenta', 'cyan', 
                         'orange', 'purple', 'brown', 'pink']
        
        for i, (roi_name, roi_contours) in enumerate(self.contours.items()):
            if (roi_name in self.show_contours and 
                self.show_contours[roi_name].get() and
                self.current_slice in roi_contours):
                
                contour = roi_contours[self.current_slice]
                
                # Utiliser couleur personnalisée si définie, sinon couleur par défaut
                if roi_name in self.structure_colors:
                    color = self.structure_colors[roi_name]
                else:
                    color = default_colors[i % len(default_colors)]
                
                if len(contour) > 0:
                    try:
                        # Fermer le contour
                        closed_contour = np.vstack([contour, contour[0]])
                        
                        # Tracer le contour
                        self.ax.plot(closed_contour[:, 0], closed_contour[:, 1], 
                                   color=color, linewidth=2, label=roi_name)
                                   
                    except Exception as e:
                        logger.error(f"Erreur affichage contour {roi_name}: {e}")
    
    
    def _plot_contour_safe(self, contour, color, label):
        """Méthode alternative pour tracer un contour avec gestion des cas limites"""
        try:
            # Diviser les contours qui sortent des limites en segments
            extent = self.current_extent
            x_min, x_max = extent[0], extent[1]
            y_min, y_max = extent[3], extent[2]  # Attention: y inversé
            
            # Fermer le contour
            contour_closed = np.vstack([contour, contour[0]])
            
            # Tracer segment par segment pour éviter les artefacts
            for i in range(len(contour_closed) - 1):
                x1, y1 = contour_closed[i]
                x2, y2 = contour_closed[i + 1]
                
                # Vérifier si le segment est dans les limites raisonnables
                if (abs(x2 - x1) < (x_max - x_min) * 0.5 and 
                    abs(y2 - y1) < (y_max - y_min) * 0.5):
                    self.ax.plot([x1, x2], [y1, y2], 
                               color=color, linewidth=2, 
                               label=label if i == 0 else "")
            
        except Exception as e:
            logger.warning(f"Erreur tracé contour sécurisé: {e}")
   
    
    
    
    def _display_dose(self):
        """Affiche la dose"""
        if self.show_dose and self.rtdose_data and self.dose_panel:
            self.dose_panel.display_dose_overlay()
        else:
            # Cacher l'échelle de dose si la dose n'est pas affichée
            if self.dose_panel:
                self.dose_panel.hide_custom_dose_scale()
    
    def _finalize_display(self):
        """Finalise l'affichage avec gestion du zoom"""
        # Configuration des axes
        if self.current_extent:
            # D'abord, appliquer les limites par défaut
            self.ax.set_xlim(self.current_extent[0], self.current_extent[1])
            self.ax.set_ylim(self.current_extent[2], self.current_extent[3])
            
            # Ensuite, si on a un zoom sauvegardé, l'appliquer
            if self.zoom_active and self.saved_xlim and self.saved_ylim:
                self.ax.set_xlim(self.saved_xlim)
                self.ax.set_ylim(self.saved_ylim)
            
            self.ax.set_aspect('equal')
        
        # Titre avec informations de coupe
        if self.ct_slices:
            ct_slice = self.ct_slices[self.current_slice]
            z_pos = float(ct_slice.ImagePositionPatient[2])
            slice_thickness = float(getattr(ct_slice, 'SliceThickness', 1.0))
            
            zoom_info = " [ZOOMÉ]" if self.zoom_active else ""
            pan_info = " [PAN]" if self.pan_active else ""
            
            title = (f"Coupe {self.current_slice + 1}/{len(self.ct_slices)} | "
                    f"Z = {z_pos:.1f} mm | "
                    f"Épaisseur = {slice_thickness:.1f} mm{zoom_info}{pan_info}")
            
            self.ax.set_title(title, color='white', fontsize=12)
        
        # Légende si contours visibles
        handles, labels = self.ax.get_legend_handles_labels()
        if handles:
            self.ax.legend(loc='upper right', fontsize=8)
        
        self.canvas.draw_idle()
    
    
    def analyze_contours_consistency(self):
        """Analyse la cohérence des contours à travers les coupes"""
        if not self.contours:
            logger.info("Aucun contour à analyser")
            return
        
        logger.info("\n" + "="*60)
        logger.info("ANALYSE DE COHÉRENCE DES CONTOURS")
        logger.info("="*60)
        
        truncated_total = 0
        
        for roi_name, roi_contours in self.contours.items():
            if not roi_contours:
                continue
                
            # Statistiques pour chaque ROI
            slice_indices = sorted(roi_contours.keys())
            point_counts = []
            x_ranges = []
            y_ranges = []
            
            for slice_idx in slice_indices:
                contour = roi_contours[slice_idx]
                if len(contour) > 0:
                    contour_array = np.array(contour)
                    x_range = np.max(contour_array[:, 0]) - np.min(contour_array[:, 0])
                    y_range = np.max(contour_array[:, 1]) - np.min(contour_array[:, 1])
                    
                    point_counts.append(len(contour))
                    x_ranges.append(x_range)
                    y_ranges.append(y_range)
            
            if point_counts:
                # Calculer les statistiques
                avg_points = np.mean(point_counts)
                std_points = np.std(point_counts)
                avg_x_range = np.mean(x_ranges)
                avg_y_range = np.mean(y_ranges)
                
                logger.info(f"\n{roi_name}:")
                logger.info(f"  Coupes: {len(slice_indices)} ({slice_indices[0]+1} à {slice_indices[-1]+1})")
                logger.info(f"  Points par contour: {np.min(point_counts)} - {np.max(point_counts)} (moy: {avg_points:.1f})")
                logger.info(f"  Taille X moyenne: {avg_x_range:.1f}mm")
                logger.info(f"  Taille Y moyenne: {avg_y_range:.1f}mm")
                
                # Détecter les anomalies
                anomalies = []
                for i, slice_idx in enumerate(slice_indices):
                    # Anomalie si le nombre de points dévie de plus de 2 écarts-types
                    if abs(point_counts[i] - avg_points) > 2 * std_points and std_points > 10:
                        anomalies.append(f"Coupe {slice_idx+1}: {point_counts[i]} points (normal: ~{avg_points:.0f})")
                    
                    # Anomalie si la taille est trop petite pour un poumon
                    if ("poumon" in roi_name.lower() or "lung" in roi_name.lower()):
                        if x_ranges[i] < 50 or y_ranges[i] < 50:
                            anomalies.append(f"Coupe {slice_idx+1}: taille {x_ranges[i]:.1f}x{y_ranges[i]:.1f}mm trop petite")
                            truncated_total += 1
                
                if anomalies:
                    logger.warning(f"  ⚠️ ANOMALIES DÉTECTÉES:")
                    for anomaly in anomalies[:5]:  # Limiter à 5 pour la lisibilité
                        logger.warning(f"    - {anomaly}")
                    if len(anomalies) > 5:
                        logger.warning(f"    ... et {len(anomalies) - 5} autres anomalies")
        
        if truncated_total > 0:
            logger.warning(f"\n⚠️ TOTAL: {truncated_total} contours potentiellement tronqués détectés")
        
        logger.info("\n" + "="*60 + "\n")
    
    
    def show_contour_analysis(self):
        """Affiche l'analyse des contours"""
        self.analyze_contours_consistency()
        
        # Message simple pour l'utilisateur
        from tkinter import messagebox
        messagebox.showinfo("Analyse des contours", 
                           "Analyse terminée.\n\nVoir la console/terminal pour les détails.")
    
  
    # (méthodes de zoom, molette, statut, etc.)
    
    def on_mouse_move(self, event):
        """Callback mouvement souris - AVEC PAN OPTIMISÉ"""
        if event.inaxes and self.ct_slices:
            if self.pan_active and self.pan_start_x is not None and self.pan_start_y is not None:
                import time
                current_time = time.time()
                
                if current_time - self.pan_last_update < 0.016:  # ~60 FPS
                    return
                
                self.pan_last_update = current_time
                
                # Calculer le déplacement
                dx = self.pan_start_x - event.xdata
                dy = self.pan_start_y - event.ydata
                
                # Appliquer le déplacement aux limites
                new_xlim = (self.pan_start_xlim[0] + dx, self.pan_start_xlim[1] + dx)
                new_ylim = (self.pan_start_ylim[0] + dy, self.pan_start_ylim[1] + dy)
                
                self.ax.set_xlim(new_xlim)
                self.ax.set_ylim(new_ylim)
                
                self.canvas.draw_idle()
                return
            
            # Affichage des coordonnées classique
            x, y = event.xdata, event.ydata
            
            # Conversion en coordonnées pixel
            ct_slice = self.ct_slices[self.current_slice]
            origin = np.array(ct_slice.ImagePositionPatient[:2])
            spacing = np.array(ct_slice.PixelSpacing)
            rows, cols = ct_slice.Rows, ct_slice.Columns
            
            pixel_x = int((x - origin[0]) / spacing[0])
            pixel_y = int((origin[1] + rows * spacing[1] - y) / spacing[1])
            
            # Valeur HU si dans l'image
            if (0 <= pixel_x < cols and 0 <= pixel_y < rows):
                image_array = ct_slice.pixel_array.astype(np.float32)
                if hasattr(ct_slice, 'RescaleSlope') and hasattr(ct_slice, 'RescaleIntercept'):
                    image_array = image_array * ct_slice.RescaleSlope + ct_slice.RescaleIntercept
                
                hu_value = image_array[pixel_y, pixel_x]
                
                coord_text = (f"X: {x:.1f} mm, Y: {y:.1f} mm | "
                            f"Pixel: ({pixel_x}, {pixel_y}) | "
                            f"HU: {hu_value:.0f}")
            else:
                coord_text = f"X: {x:.1f} mm, Y: {y:.1f} mm"
            
            #self.coord_label.config(text=coord_text)
        else:
            self.coord_label.config(text="")
    
    def wheel_handler(self, event):
        """Handler principal pour la molette (Windows)"""
        if not self.ct_slices:
            return "break"
        
        # Si on tient Ctrl, on fait du zoom au lieu de naviguer
        if event.state & 0x4:  # Ctrl enfoncé
            if event.delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            return "break"
        
        direction = -1 if event.delta > 0 else 1
        self.navigate_slice_with_wheel(direction)
        return "break"
    
    def wheel_up_handler(self, event):
        """Handler molette Unix/Linux - Scroll vers le haut"""
        if self.ct_slices:
            self.navigate_slice_with_wheel(-1)
        return "break"
    
    def wheel_down_handler(self, event):
        """Handler molette Unix/Linux - Scroll vers le bas"""
        if self.ct_slices:
            self.navigate_slice_with_wheel(1)
        return "break"
    
    def wheel_handler_global(self, event):
        """Handler global sur la fenêtre principale (backup)"""
        if not self.ct_slices:
            return "break"
        
        try:
            canvas_widget = self.canvas.get_tk_widget()
            if str(event.widget) == str(canvas_widget):
                direction = -1 if event.delta > 0 else 1
                self.navigate_slice_with_wheel(direction)
        except:
            pass
        
        return "break"
    
    def navigate_slice_with_wheel(self, direction):
        """Navigation centralisée pour la molette"""
        if not self.ct_slices:
            return
        
        # Sauvegarder le zoom AVANT de changer de coupe
        if not self.navigation_in_progress:
            self.save_current_zoom()
        
        # Marquer qu'on navigue
        self.navigation_in_progress = True
        
        current = self.current_slice
        new_slice = current + direction
        
        if 0 <= new_slice < len(self.ct_slices):
            self.current_slice = new_slice
            if hasattr(self.navigation_panel, 'slice_var'):
                self.navigation_panel.slice_var.set(new_slice)
            if hasattr(self.navigation_panel, 'update_slice_label'):
                self.navigation_panel.update_slice_label()
            self.update_display()
        
        # Terminer la navigation après un délai
        self.master.after(50, self.end_navigation)
    
    def on_matplotlib_scroll(self, event):
        """Gestion de la molette via Matplotlib scroll_event (backup)"""
        if not self.ct_slices:
            return
        
        if event.button == 'up':
            self.navigate_slice_with_wheel(-1)
        elif event.button == 'down':
            self.navigate_slice_with_wheel(1)
        
        return True
    
    # === Méthodes utilitaires ===
    def set_status(self, text):
        """Met à jour la barre d'état"""
        #self.status_label.config(text=text)
        #self.master.update()
        pass
    
    def reset_view(self):
        """Réinitialise la vue"""
        if self.ct_slices:
            # Réinitialiser le zoom
            self.zoom_active = False
            self.saved_xlim = None
            self.saved_ylim = None
            
            # Arrêter le pan si actif
            self.pan_active = False
            
            # Appliquer les limites par défaut
            if hasattr(self, 'current_extent') and self.current_extent:
                self.ax.set_xlim(self.current_extent[0], self.current_extent[1])
                self.ax.set_ylim(self.current_extent[2], self.current_extent[3])
            else:
                self.ax.set_xlim(auto=True)
                self.ax.set_ylim(auto=True)
            
            self.ax.set_aspect('equal')
            self.canvas.draw()
            logger.info("Vue réinitialisée")
    
    def zoom_in(self, factor=0.8):
        """Zoom avant programmé"""
        if not self.ct_slices:
            return
            
        current_xlim = self.ax.get_xlim()
        current_ylim = self.ax.get_ylim()
        
        # Calculer le centre
        x_center = (current_xlim[0] + current_xlim[1]) / 2
        y_center = (current_ylim[0] + current_ylim[1]) / 2
        
        # Calculer les nouvelles limites
        x_range = (current_xlim[1] - current_xlim[0]) * factor / 2
        y_range = (current_ylim[1] - current_ylim[0]) * factor / 2
        
        new_xlim = (x_center - x_range, x_center + x_range)
        new_ylim = (y_center - y_range, y_center + y_range)
        
        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        self.canvas.draw()
        
        # Sauvegarder immédiatement ce zoom
        self.saved_xlim = new_xlim
        self.saved_ylim = new_ylim
        self.zoom_active = True
        logger.info(f"Zoom programmé appliqué: X={new_xlim}, Y={new_ylim}")

    def zoom_out(self, factor=1.25):
        """Zoom arrière programmé"""
        self.zoom_in(factor)

    
    
    def show_shortcuts(self):
        """Affiche les raccourcis clavier - AVEC PAN CLIC MOLETTE"""
        shortcuts = """Raccourcis clavier:
    
    Navigation:
    • ← → : Coupe précédente/suivante (avec zoom persistant)
    • ↑ ↓ : Navigation rapide (±10 coupes)
    • Molette souris : Navigation entre coupes (avec zoom persistant)
    • Ctrl+Molette : Zoom in/out
    • Ctrl+O : Ouvrir dossier
    
    Zoom et Vue:
    • Ctrl + + : Zoom avant
    • Ctrl + - : Zoom arrière  
    • Ctrl + 0 : Réinitialiser vue
    • Clic molette + glisser : Pan (déplacer la vue)
    
    Outils Dentaires:
    • Ctrl + T : Commencer placement points
    • Ctrl + E : Mode édition points
    • Ctrl + G : Génération automatique
    • Ctrl + Shift + G : Générer cylindres 3D
    • Ctrl + I : Informations dentaires
    • Ctrl + Shift + E : Exporter données
    • Ctrl + Shift + V : Valider placement
    
    Mode Édition Dentaire:
    • Clic droit + glisser : Sélection rectangulaire
    • R : Rotation du groupe sélectionné
    • Suppr : Supprimer sélection
    • Échap : Désélectionner tout
    • Clic droit simple : Supprimer un point
    • Glisser : Déplacer point/groupe
    
    Souris:
    • Mouvement : Coordonnées et valeurs HU
    • Clic gauche + glisser : Zoom rectangle (toolbar)
    • Clic molette + glisser : Pan (déplacer la vue)
    
    Debug:
    • Ctrl + D : Afficher état du zoom"""
        
        messagebox.showinfo("Raccourcis", shortcuts)
    
    def show_about(self):
        """Affiche les informations sur l'application"""
        about_text = """DICOM Viewer - Version Modulaire Dentaire
    Inspiré de Dicompyler
    
    Fonctionnalités:
    • Visualisation coupes CT avec zoom persistant
    • Navigation intuitive (flèches, molette)
    • Pan avec clic molette + glisser
    • Superposition contours RTStruct
    • Superposition dose RTDose avec échelle personnalisée
    • Fenêtrage interactif
    
    Outils Dentaires Avancés:
    • Placement de 6 points de référence dentaires
    • Sélection multiple par rectangle (clic droit + glisser)
    • Génération automatique des autres points
    • Symétrie automatique basée sur l'ancien algorithme éprouvé
    • Génération de cylindres 3D pour toutes les dents
    • Export des données vers CSV
    • Validation de la cohérence anatomique
    
    Raccourcis Pratiques:
    • Ctrl+T : Placement dentaire
    • Ctrl+E : Édition points (toujours accessible)
    • Clic droit + glisser : Sélection rectangle
    • Clic molette + glisser : Pan
    • R : Rotation groupe sélectionné
    
    Développé avec Python, Tkinter et Matplotlib
    Version sans intégration automatique - Interface propre"""
        
        messagebox.showinfo("À propos", about_text)