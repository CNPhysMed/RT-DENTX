#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialogues "À propos" améliorés pour RT-DENTX
© 2025 Caroline Moreau-Noblet — RT-DENTX — Licence BSD 3-Clause
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import webbrowser
import os


# Texte de la licence BSD 3-Clause
BSD_LICENSE_TEXT = """BSD 3-Clause License

Copyright (c) 2025, Caroline Moreau-Noblet
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

3. Neither the name of Caroline Moreau-Noblet nor the names of its contributors may be used
   to endorse or promote products derived from this software without
   specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."""


class LicenseDialog(tk.Toplevel):
    """Dialogue pour afficher la licence BSD 3-Clause"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Licence BSD 3-Clause")
        self.geometry("700x600")
        self.configure(bg='#f0f0f0')
        self.resizable(True, True)
        
        # Centrer la fenêtre
        self.center_window()
        
        # Rendre la fenêtre modale
        self.transient(parent)
        self.grab_set()
        
        self.setup_content()
        
    def center_window(self):
        """Centre la fenêtre sur l'écran"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 350
        y = (self.winfo_screenheight() // 2) - 300
        self.geometry(f"700x600+{x}+{y}")
        
    def setup_content(self):
        """Configure le contenu de la fenêtre"""
        main_frame = tk.Frame(self, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Titre
        title_label = tk.Label(main_frame, text="Licence BSD 3-Clause",
                              font=('Arial', 16, 'bold'),
                              bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=(0, 20))
        
        # Texte de la licence avec scroll
        text_frame = tk.Frame(main_frame, bg='#f0f0f0')
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Widget Text avec scrollbar
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Courier', 10),
                             bg='white', fg='black', relief=tk.SUNKEN, bd=2)
        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Texte de la licence
        license_text = """BSD 3-Clause License

Copyright (c) 2025, Caroline Moreau-Noblet
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

3. Neither the name of Caroline Moreau-Noblet nor the names of its contributors may be used
   to endorse or promote products derived from this software without
   specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."""
        
        text_widget.insert(tk.END, license_text)
        text_widget.config(state=tk.DISABLED)
        
        # Pack text et scrollbar
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bouton Fermer
        #button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        close_btn = tk.Button(button_frame, text="Fermer",
                             font=('Segoe UI', 11, 'bold'),
                             bg='#3498db', fg='white',
                             activebackground='#2980b9', activeforeground='white',
                             relief='solid', borderwidth=1,
                             padx=20, pady=3,
                             cursor='hand2',
                             command=self.destroy)
        
        
        
        
        close_btn.pack(side=tk.RIGHT)

class RTDentxSplashScreen(tk.Toplevel):
    """Écran de démarrage RT-DENTX amélioré"""
    
    def __init__(self, parent, on_accept_callback, on_decline_callback):
        super().__init__(parent)
        self.parent = parent
        self.on_accept_callback = on_accept_callback
        self.on_decline_callback = on_decline_callback
        self.user_choice_made = False
        self.logo_img = None  # Pour stocker l'image du logo
        
        # Configuration de la fenêtre - Ajustement largeur et hauteur
        self.title("RT-DENTX - Conditions d'utilisation")
        self.geometry("1000x850")  # Moins large (900) et un peu plus haute (850) pour les boutons
        self.configure(bg='#f0f0f0')
        self.resizable(False, False)
        
        # Centrer la fenêtre
        self.center_window()
        
        # Empêcher la fermeture par X - rediriger vers decline
        self.protocol("WM_DELETE_WINDOW", self.on_decline)
        
        # Forcer la fenêtre au premier plan
        self.lift()
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
        
        self.setup_content()
        
    def center_window(self):
        """Centre la fenêtre sur l'écran"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 500  # 900/2
        y = (self.winfo_screenheight() // 2) - 425  # 850/2
        self.geometry(f"900x850+{x}+{y}")
        
    def load_logo(self):
        """Charge le logo RT-DENTX - VERSION HAUTE RÉSOLUTION"""
        try:
            logo_path = "assets/rt_dentx_logo.png"
            if os.path.exists(logo_path):
                img = Image.open(logo_path)
                
                target_size = (130, 120)  
                
                img = img.resize(target_size, Image.Resampling.LANCZOS)
                
                # Améliorer la netteté
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.1)
                
                self.logo_img = ImageTk.PhotoImage(img)
                return True
        except Exception as e:
            print(f"Erreur chargement logo: {e}")
        return False
        
    def setup_content(self):
        """Configure le contenu de la fenêtre"""
        # Container principal avec padding - 
        main_container = tk.Frame(self, bg='#f0f0f0')
        main_container.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)  # Padding réduit
        
        # Zone scrollable pour le contenu principal (tout sauf les boutons)
        content_frame = tk.Frame(main_container, bg='#f0f0f0', height=750)  # Hauteur augmentée
        content_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))
        content_frame.pack_propagate(False)  # Empêche le redimensionnement automatique
        
        # Logo et titre (sans répéter RT-DENTX puisque déjà dans le logo)
        self.add_header_section(content_frame)
        
        # Informations générales avec référence scientifique
        self.add_info_section(content_frame)
        
        # Licence et conditions d'utilisation
        self.add_license_section(content_frame)
        
        # Boutons Décliner/Accepter TOUJOURS VISIBLES en bas
        self.add_buttons_section(main_container)
        
    def add_header_section(self, parent):
        """Ajoute la section en-tête avec logo et titre"""
        header_frame = tk.Frame(parent, bg='#f0f0f0')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Logo RT-DENTX
        if self.load_logo():
            logo_label = tk.Label(header_frame, image=self.logo_img, bg='#f0f0f0')
            logo_label.pack(pady=(0, 12))
        else:
            # Logo de remplacement si image non trouvée
            logo_frame = tk.Frame(header_frame, bg='#2980b9', width=100, height=100)
            logo_frame.pack_propagate(False)
            logo_frame.pack(pady=(0, 12))
            
            logo_label = tk.Label(logo_frame, text="🦷", font=('Arial', 40), 
                                 bg='#2980b9', fg='white')
            logo_label.pack(expand=True)
        
        # Sous-titre en gras comme demandé
        subtitle_label = tk.Label(header_frame, 
                                 text="DENTal eXposure in Radiation Therapy",
                                 font=('Arial', 16, 'bold'),  # En gras
                                 bg='#f0f0f0', fg='#5dade2')
        subtitle_label.pack(pady=(0, 15))  # Réduit de 30 à 15
        
    def add_info_section(self, parent):
        """Ajoute la section informations avec référence scientifique - LIGNES ULTRA RESSERREES"""
        info_frame = tk.LabelFrame(parent, text="Informations", 
                                  font=('Arial', 12, 'bold'),
                                  bg='#f0f0f0', fg='#2c3e50',
                                  relief=tk.RIDGE, bd=2, padx=15, pady=0)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Informations du logiciel - SEULEMENT 3 LIGNES, ZERO espacement
        info_data = [
            ("Auteur:", "Caroline MOREAU-NOBLET"),
            ("Contact:", "caroline.noblet.physmed@gmail.com"),
            ("Version:", "1.0")
            # "Type" supprimé comme demandé
        ]
        
        for label, value in info_data:
            row_frame = tk.Frame(info_frame, bg='#f0f0f0')
            row_frame.pack(fill=tk.X)  # AUCUN pady - lignes collées
            
            tk.Label(row_frame, text=label, font=('Arial', 10, 'bold'),
                    bg='#f0f0f0', fg='#2c3e50', width=12, anchor='w').pack(side=tk.LEFT)
            tk.Label(row_frame, text=value, font=('Arial', 10),
                    bg='#f0f0f0', fg='#34495e', anchor='w').pack(side=tk.LEFT, fill=tk.X)
        
        # Séparateur plus fin
        separator = tk.Frame(info_frame, height=1, bg='#bdc3c7')
        separator.pack(fill=tk.X, pady=(6, 6))
        
        # Référence scientifique en plus petit et italique
        ref_label = tk.Label(info_frame, text="RT-DENTX est basé sur l'article de ",
                            font=('Arial', 9, 'italic'), bg='#f0f0f0', fg='#7f8c8d')
        ref_label.pack(anchor=tk.W, pady=(0, 1))
        
        # Lien cliquable pour l'article
        link_frame = tk.Frame(info_frame, bg='#f0f0f0')
        link_frame.pack(fill=tk.X, pady=(0, 1))
        
        link_label = tk.Label(link_frame, 
                             text="Delpon et al. - Dental exposure assessment in head and neck radiotherapy",
                             font=('Arial', 9, 'italic', 'underline'), bg='#f0f0f0',
                             fg='#3498db', cursor='hand2')
        link_label.pack(anchor=tk.W)
        
        # Effet hover et clic
        def on_enter(e):
            link_label.config(fg='#2980b9')
        def on_leave(e):
            link_label.config(fg='#3498db')
        def on_click(e):
            import webbrowser
            webbrowser.open("https://doi.org/10.1016/j.canrad.2022.08.003")
            
        link_label.bind("<Enter>", on_enter)
        link_label.bind("<Leave>", on_leave)
        link_label.bind("<Button-1>", on_click)
        
        # Journal et année
        journal_label = tk.Label(info_frame, text="Cancer/Radiothérapie, 2022",
                               font=('Arial', 8, 'italic'), bg='#f0f0f0', fg='#95a5a6')
        journal_label.pack(anchor=tk.W, pady=(0, 2))
                    
    def add_license_section(self, parent):
        """Ajoute la section licence et conditions d'utilisation - VERSION CORRIGÉE"""
        license_frame = tk.LabelFrame(parent, text="Licence et conditions d'utilisation", 
                                     font=('Arial', 12, 'bold'),
                                     bg='#f0f0f0', fg='#2c3e50',
                                     relief=tk.RIDGE, bd=2, padx=20, pady=10)
        license_frame.pack(fill=tk.X, pady=(0, 10))  # SUPPRIMÉ expand=True
        
        # Récupérer la couleur de fond par défaut
        try:
            default_bg = parent.cget('bg')
        except:
            try:
                current_widget = parent
                while current_widget and hasattr(current_widget, 'master'):
                    try:
                        default_bg = current_widget.cget('bg')
                        break
                    except:
                        current_widget = current_widget.master
                else:
                    default_bg = '#f0f0f0'  # Fallback
            except:
                default_bg = '#f0f0f0'  # Fallback
        
        # Licence BSD 3-Clause cliquable
        license_header_frame = tk.Frame(license_frame, bg='#f0f0f0')
        license_header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(license_header_frame, text="📄 Licence ", 
                font=('Arial', 11, 'bold'), bg='#f0f0f0', fg='#3498db').pack(side=tk.LEFT)
        
        license_link = tk.Label(license_header_frame, text="BSD 3-Clause", 
                               font=('Arial', 11, 'bold', 'underline'), 
                               bg='#f0f0f0', fg='#3498db', cursor='hand2')
        license_link.pack(side=tk.LEFT)
        
        # Rendre la licence cliquable
        def on_license_enter(e):
            license_link.config(fg='#2980b9')
        def on_license_leave(e):
            license_link.config(fg='#3498db')
        def on_license_click(e):
            LicenseDialog(self)
            
        license_link.bind("<Enter>", on_license_enter)
        license_link.bind("<Leave>", on_license_leave)
        license_link.bind("<Button-1>", on_license_click)
        
        # Avertissement important en rouge
        warning_label = tk.Label(license_frame, 
                       text="⚠️ Important - Usage recherche et enseignement",
                       font=('Arial', 12, 'bold'),
                       bg='#f0f0f0', fg='#e74c3c')
        warning_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Texte des conditions
        conditions_text = """Ce logiciel ne constitue pas un dispositif médical validé et ne doit pas être utilisé comme outil de diagnostic, de planification ou de décision thérapeutique sans validation indépendante par un professionnel de santé qualifié.
    
    Les résultats affichés (notamment les doses moyennes estimées aux structures dentaires) sont basés sur des calculs à partir des données DICOM, et peuvent être sujets à des imprécisions dues aux contours, à la résolution des images ou à d'autres facteurs techniques.
    
    Aucune garantie n'est donnée quant à l'exactitude, la fiabilité ou l'adéquation des résultats pour un usage clinique. L'auteur et les contributeurs déclinent toute responsabilité en cas de dommage, direct ou indirect, résultant de l'usage du logiciel, y compris mais sans s'y limiter aux décisions médicales prises sur la base de ses résultats.
    
    L'utilisateur assume l'entière responsabilité de l'interprétation et de l'utilisation des données générées."""
        
        # Frame avec hauteur fixe BEAUCOUP plus importante
        text_frame = tk.Frame(license_frame, bg='#f0f0f0', height=500)  # Hauteur encore augmentée
        text_frame.pack(fill=tk.X, pady=(0, 15))
        text_frame.pack_propagate(False)  # Empêche le redimensionnement automatique
        
        # Widget Text avec fond par défaut
        text_widget = tk.Text(text_frame, wrap=tk.WORD, 
                             font=('Arial', 10), bg=default_bg, fg='#2c3e50',
                             relief=tk.SUNKEN, bd=2, padx=10, pady=8)
        
        # UNE SEULE scrollbar
        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview,
                               width=20, bg='#bdc3c7', troughcolor='#ecf0f1',
                               activebackground='#95a5a6')
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Configurer le tag pour le gras
        text_widget.tag_configure("bold", font=('Arial', 10, 'bold'))
        
        # Insérer le texte
        text_widget.insert(tk.END, conditions_text)
        
        # Appliquer le gras aux phrases importantes
        bold_phrases = [
            "ne constitue pas",
            "Aucune garantie", 
            "L'utilisateur assume l'entière responsabilité"
        ]
        
        for phrase in bold_phrases:
            start = "1.0"
            while True:
                pos = text_widget.search(phrase, start, tk.END)
                if not pos:
                    break
                end = f"{pos}+{len(phrase)}c"
                text_widget.tag_add("bold", pos, end)
                start = end
        
        # Désactiver l'édition
        text_widget.config(state=tk.DISABLED)
        
        # Pack les widgets - UNE SEULE FOIS
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def add_buttons_section(self, parent):
        """Ajoute les boutons Décliner/Accepter harmonieusement en bas"""
        # Boutons SANS Frame - directement dans le container parent qui est main_container
        # Bouton Décliner
        decline_btn = tk.Button(parent, text="Décliner", 
                               font=('Arial', 12, 'bold'),
                               bg='#e74c3c', fg='white',
                               activebackground='#c0392b', activeforeground='white',
                               relief='raised', borderwidth=2,
                               padx=25, pady=10,
                               width=12,
                               cursor='hand2',
                               command=self.on_decline)
        decline_btn.pack(side=tk.LEFT, padx=(30, 20), pady=10)
        
        # Bouton Accepter
        accept_btn = tk.Button(parent, text="Accepter", 
                              font=('Arial', 12, 'bold'),
                              bg='#27ae60', fg='white',
                              activebackground='#229954', activeforeground='white',
                              relief='raised', borderwidth=2,
                              padx=25, pady=10,
                              width=12,
                              cursor='hand2',
                              command=self.on_accept)
        accept_btn.pack(side=tk.RIGHT, padx=(20, 30), pady=10)
        
    def on_accept(self):
        """Gérer l'acceptation des conditions"""
        if not self.user_choice_made:
            self.user_choice_made = True
            print("✅ Conditions acceptées")
            self.destroy()
            if self.on_accept_callback:
                self.on_accept_callback()
                
    def on_decline(self):
        """Gérer le refus des conditions"""
        if not self.user_choice_made:
            self.user_choice_made = True
            print("❌ Conditions déclinées")
            self.destroy()
            if self.on_decline_callback:
                self.on_decline_callback()

# Fonction utilitaire pour créer le splash screen
def show_splash_screen(parent, on_accept_callback, on_decline_callback):
    """Affiche l'écran de démarrage RT-DENTX"""
    splash = RTDentxSplashScreen(parent, on_accept_callback, on_decline_callback)
    return splash




class ModernDialog(tk.Toplevel):
    """Classe de base pour les dialogues modernes"""
    
    def __init__(self, parent, title, width=800, height=650):
        super().__init__(parent)
        self.parent = parent
        
        # Configuration de base de la fenêtre
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True)
        
        # Centrer la fenêtre
        self.center_window(width, height)
        
        # Style moderne
        self.configure(bg='#f0f0f0')
        
        # Style pour les widgets
        self.setup_styles()
        
        # Frame principal avec padding
        self.main_frame = ttk.Frame(self, style='Modern.TFrame', padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
    def center_window(self, width, height):
        """Centre la fenêtre sur l'écran"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
    def setup_styles(self):
        """Configure les styles TTK modernes"""
        style = ttk.Style()
        
        # Couleur de fond principale
        bg_color = '#f0f0f0'
        
        # Frame moderne
        style.configure('Modern.TFrame', 
                       background=bg_color,
                       relief='flat')
        
        # Headers
        style.configure('Header.TLabel',
                       background=bg_color,
                       foreground='#2c3e50',
                       font=('Segoe UI', 18, 'bold'))
        
        style.configure('SubHeader.TLabel',
                       background=bg_color,
                       foreground='#3498db',
                       font=('Segoe UI', 14, 'bold'))
        
        # Texte normal
        style.configure('Body.TLabel',
                       background=bg_color,
                       foreground='#34495e',
                       font=('Segoe UI', 10))
        
        # Texte info
        style.configure('Info.TLabel',
                       background=bg_color,
                       foreground='#7f8c8d',
                       font=('Segoe UI', 9))
        
        # Boutons modernes avec texte visible
        style.configure('Modern.TButton',
                       relief='solid',
                       borderwidth=1,
                       background='#3498db',
                       foreground='white',
                       font=('Segoe UI', 11, 'bold'),
                       padding=(25, 12),
                       focuscolor='none')
        
        style.map('Modern.TButton',
                 relief=[('pressed', 'solid'), ('active', 'solid')],
                 borderwidth=[('pressed', 1), ('active', 1)],
                 background=[('active', '#2980b9'), ('pressed', '#21618c')],
                 foreground=[('active', 'white'), ('pressed', 'white'), ('focus', 'white')])


class AboutRTDentxDialog(ModernDialog):
    """Dialogue À propos de RT-DENTX amélioré"""
    
    def __init__(self, parent):
        super().__init__(parent, "À propos de RT-DENTX", width=850, height=700)
        self.setup_content()
        
    def setup_content(self):
        """Configure le contenu du dialogue"""
        # Conteneur principal avec scrollbar
        canvas = tk.Canvas(self.main_frame, bg='#f0f0f0', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Modern.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Configuration pour que le contenu prenne toute la largeur
        def configure_canvas(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas_width = canvas.winfo_width()
            canvas.itemconfig(canvas_window, width=canvas_width)
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', configure_canvas)
        
        # === HEADER AVEC LOGO ===
        header_frame = ttk.Frame(scrollable_frame, style='Modern.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Logo RT-DENTX (si disponible)
        self.add_logo(header_frame)
        
        # Titre principal
        
        
        # Sous-titre avec style
        subtitle_label = ttk.Label(header_frame, 
                                  text="DENTal eXposure in Radiation Therapy",
                                  style='SubHeader.TLabel')
        subtitle_label.pack(pady=(0, 5))
        
        # Description
        desc_label = ttk.Label(header_frame,
                              text="Logiciel libre pour l'évaluation dosimétrique dentaire en radiothérapie de la sphère ORL",
                              style='Body.TLabel',
                              wraplength=600,
                              justify=tk.CENTER)
        desc_label.pack(pady=(5, 20))
        
        # === INFORMATIONS PRINCIPALES ===
        # Créer d'abord le style
        style = ttk.Style()
        style.configure("Info.TLabelframe.Label", font=('Arial', 12, 'bold'))
        
        # Puis utiliser le style
        info_frame = ttk.LabelFrame(scrollable_frame, text="Informations", 
                                   style="Info.TLabelframe", padding=20)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        
        self.add_info_section(info_frame)
        
        # === DESCRIPTION TECHNIQUE ===
        tech_frame = ttk.LabelFrame(scrollable_frame, text="Description technique", style="Info.TLabelframe",padding=20)
        tech_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.add_technical_section(tech_frame)
        
        # === LICENCE ET AVERTISSEMENT ===
        license_frame = ttk.LabelFrame(scrollable_frame, text="Licence et conditions d'utilisation", style="Info.TLabelframe",padding=20)
        license_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.add_license_section(license_frame)
        
        # === RÉFÉRENCE SCIENTIFIQUE ===
        ref_frame = ttk.LabelFrame(scrollable_frame, text="Référence scientifique", style="Info.TLabelframe",padding=20)
        ref_frame.pack(fill=tk.X, pady=(0, 30))
        
        self.add_reference_section(ref_frame)
        
        # Pack canvas et scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # === BOUTON FERMER ===
        button_frame = ttk.Frame(self, style='Modern.TFrame')
        button_frame.pack(fill=tk.X, padx=20, pady=(10, 20))
        
        # Bouton avec style personnalisé pour meilleure visibilité
        close_btn = tk.Button(button_frame, 
                             text="Fermer", 
                             font=('Segoe UI', 11, 'bold'),
                             bg='#3498db',
                             fg='white',
                             activebackground='#2980b9',
                             activeforeground='white',
                             relief='solid',
                             borderwidth=1,
                             padx=20,
                             pady=3,
                             cursor='hand2',
                             command=self.destroy)
        close_btn.pack(side=tk.RIGHT)
        
        # Binding scrolling souris
        self.bind_mousewheel(canvas)
        
    def add_logo(self, parent):
        """Ajoute le logo RT-DENTX si disponible"""
        logo_path = os.path.join(os.path.dirname(__file__), "assets/rt_dentx_logo.png")
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
                
                logo_label = ttk.Label(parent, image=self.logo_img, style='Modern.TLabel')
                logo_label.pack(pady=(0, 10))
            except Exception:
                pass  # Si erreur, pas de logo
                
    def add_info_section(self, parent):
        """Ajoute la section informations"""
        info_data = [
            ("Auteur", "Caroline MOREAU-NOBLET"),
            ("Contact", "caroline.noblet.physmed@gmail.com"),
            ("Version", "1.0"),
        ]
        
        for i, (label, value) in enumerate(info_data):
            row_frame = ttk.Frame(parent, style='Modern.TFrame')
            row_frame.pack(fill=tk.X, pady=2)
            
            label_widget = ttk.Label(row_frame, text=f"{label}:", 
                                   style='Body.TLabel', font=('Segoe UI', 10, 'bold'))
            label_widget.pack(side=tk.LEFT, anchor=tk.W)
            
            value_widget = ttk.Label(row_frame, text=value, style='Body.TLabel')
            value_widget.pack(side=tk.LEFT, padx=(10, 0), anchor=tk.W)
            
    def add_technical_section(self, parent):
        """Ajoute la section technique"""
        tech_text = """RT-DENTX est un outil spécialisé permettant l'évaluation dosimétrique des structures dentaires lors de traitements de radiothérapie de la sphère ORL.

Le logiciel propose des fonctionnalités pour :
• Visualisation des images DICOM CT, RTStruct et RTDose
• Contourage simplifiée des dents (couronnes et racines)
• Calcul de la dose moyenne reçue par chaque structure dentaire contourée
• Génération de rapports dosimétriques détaillés
• Export d'un RTStruct avec ajout des dents
"""
        
        text_widget = tk.Text(parent, wrap=tk.WORD, height=9, 
                             font=('Segoe UI', 10), bg='#f0f0f0', 
                             relief=tk.FLAT, borderwidth=0,
                             highlightthickness=0)
        text_widget.insert(tk.END, tech_text)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill=tk.X, expand=True)
        
    def add_license_section(self, parent):
        """Ajoute la section licence"""
        # En-tête licence avec lien cliquable
        license_header_frame = ttk.Frame(parent, style='Modern.TFrame')
        license_header_frame.pack(fill=tk.X, pady=(0, 10))
        
        license_text_label = ttk.Label(license_header_frame, 
                                     text="📄 Licence ",
                                     font=('Segoe UI', 11, 'bold'),
                                     foreground='#3498db',
                                     background='#f0f0f0')
        license_text_label.pack(side=tk.LEFT)
        
        license_link_label = ttk.Label(license_header_frame, 
                                     text="BSD 3-Clause",
                                     font=('Segoe UI', 11, 'bold', 'underline'),
                                     foreground='#3498db',
                                     background='#f0f0f0',
                                     cursor='hand2')
        license_link_label.pack(side=tk.LEFT)
        license_link_label.bind("<Button-1>", lambda e: LicenseDialog(self))
        
        # Effet hover
        def on_enter(e):
            license_link_label.config(foreground='#2980b9')
        def on_leave(e):
            license_link_label.config(foreground='#3498db')
            
        license_link_label.bind("<Enter>", on_enter)
        license_link_label.bind("<Leave>", on_leave)
        
        # Avertissement en rouge
        warning_frame = ttk.Frame(parent, style='Modern.TFrame')
        warning_frame.pack(fill=tk.X, pady=(0, 15))
        
        warning_label = ttk.Label(warning_frame, 
                                 text="⚠️ IMPORTANT - USAGE RECHERCHE ET ENSEIGNEMENT",
                                 font=('Segoe UI', 11, 'bold'),
                                 foreground='#e74c3c',
                                 background='#f0f0f0')
        warning_label.pack(anchor=tk.W)
        
        # Texte de licence avec formatage
        license_text = """**RT-DENTX** est un logiciel fourni à des fins de recherche, d'enseignement ou d'analyse dosimétrique. Il ne constitue **pas un dispositif médical validé** et **ne doit pas être utilisé comme outil de diagnostic, de planification ou de décision thérapeutique sans validation indépendante par un professionnel de santé qualifié**.

Les résultats affichés (notamment les doses moyennes estimées aux structures dentaires) sont basés sur des calculs à partir des données DICOM, et peuvent être sujets à des imprécisions dues aux contours, à la résolution des images ou à d'autres facteurs techniques.

**Aucune garantie n'est donnée** quant à l'exactitude, la fiabilité ou l'adéquation des résultats pour un usage clinique. L'auteur et les contributeurs déclinent toute responsabilité en cas de dommage, direct ou indirect, résultant de l'usage du logiciel, y compris mais sans s'y limiter aux décisions médicales prises sur la base de ses résultats.

**L'utilisateur assume l'entière responsabilité de l'interprétation et de l'utilisation des données générées.**"""
        
        text_widget = tk.Text(parent, wrap=tk.WORD, height=15,
                             font=('Segoe UI', 10), bg='#f0f0f0',
                             relief=tk.FLAT, borderwidth=0,
                             highlightthickness=0)
        
        # Configuration des tags pour le formatage
        text_widget.tag_configure("bold", font=('Segoe UI', 9, 'bold'))
        text_widget.tag_configure("normal", font=('Segoe UI', 9))
        
        # Insertion du texte avec formatage
        lines = license_text.split('\n')
        for line in lines:
            if line.strip():
                # Recherche des parties en gras
                parts = line.split('**')
                for i, part in enumerate(parts):
                    if i % 2 == 1:  # Parties impaires = en gras
                        text_widget.insert(tk.END, part, "bold")
                    else:  # Parties paires = normal
                        text_widget.insert(tk.END, part, "normal")
            text_widget.insert(tk.END, '\n', "normal")
        
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill=tk.X, expand=True)
        
    def add_reference_section(self, parent):
        """Ajoute la section référence scientifique"""
        ref_text = "RT-DENTX est basé sur l'article de "
        ref_label = ttk.Label(parent, text=ref_text, 
                             font=('Segoe UI', 10),
                             foreground='#34495e',
                             background='#f0f0f0')
        ref_label.pack(anchor=tk.W)
        
        # Lien cliquable
        link_frame = ttk.Frame(parent, style='Modern.TFrame')
        link_frame.pack(fill=tk.X, pady=(5, 0))
        
        link_label = ttk.Label(link_frame, 
                              text="Delpon et al. - Cancer/Radiothérapie (2022)",
                              foreground='#3498db',
                              background='#f0f0f0',
                              font=('Segoe UI', 10, 'underline'),
                              cursor='hand2')
        link_label.pack(anchor=tk.W)
        link_label.bind("<Button-1>", 
                       lambda e: webbrowser.open("https://doi.org/10.1016/j.canrad.2022.08.003"))
        
    def bind_mousewheel(self, canvas):
        """Binding pour le scroll avec la molette"""
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
            
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
            
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)


class SourcesDialog(ModernDialog):
    """Dialogue Sources scientifiques amélioré"""
    
    def __init__(self, parent):
        super().__init__(parent, "Sources scientifiques", width=900, height=650)
        self.setup_content()
        
    def setup_content(self):
        """Configure le contenu du dialogue sources"""
        # Header
        header_frame = ttk.Frame(self.main_frame, style='Modern.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="Sources scientifiques", style='Header.TLabel')
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(header_frame,
                                  text="Références bibliographiques utilisées dans RT-DENTX",
                                  style='Info.TLabel')
        subtitle_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Conteneur avec scrollbar
        canvas = tk.Canvas(self.main_frame, bg='#f0f0f0', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Modern.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Configuration pour que le contenu prenne toute la largeur
        def configure_canvas(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas_width = canvas.winfo_width()
            canvas.itemconfig(canvas_window, width=canvas_width)
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', configure_canvas)
        
        # === RÉFÉRENCES PRINCIPALES ===
        main_refs = [
            {
                "authors": "Delpon et al.",
                "title": "Dental exposure assessment in head and neck radiotherapy: A prospective study",
                "journal": "Cancer/Radiothérapie",
                "year": "2022",
                "url": "https://doi.org/10.1016/j.canrad.2022.08.003",
                "description": "Article de référence principal sur lequel est basé RT-DENTX"
            },
            {
                "authors": "Carsuzaa et al.",
                "title": "Oral health and dental care in oncology patients",
                "journal": "Bulletin du Cancer",
                "year": "2024",
                "url": "https://doi.org/10.1016/j.bulcan.2024.01.008",
                "description": "Recommandations pour la prise en charge dentaire en oncologie"
            }
        ]
        
        main_frame = ttk.LabelFrame(scrollable_frame, text="Références principales", padding=15)
        main_frame.pack(fill=tk.X, pady=(0, 20))
        
        for ref in main_refs:
            self.add_reference_card(main_frame, ref, is_main=True)
            
        # === RÉFÉRENCES COMPLÉMENTAIRES ===
        comp_refs = [
            {
                "authors": "Wheeler's Dental Anatomy",
                "title": "Textbook and Coloring Book, 10th Edition",
                "journal": "Elsevier",
                "year": "2020",
                "url": "https://www.educate.elsevier.com/book/details/9780323638784",
                "description": "Référence anatomique pour la morphologie dentaire"
            },
            {
                "authors": "Al-Habib et al.",
                "title": "Dental complications in head and neck radiotherapy",
                "journal": "J Indian College Dent Res Oncol",
                "year": "2024",
                "url": "https://10.4103/jicdro.jicdro_107_24",
                "description": "Complications dentaires en radiothérapie cervico-faciale"
            },
            {
                "authors": "Kim et al.",
                "title": "Three-dimensional analysis of tooth movement in extraction cases",
                "journal": "Korean J Orthod",
                "year": "2013",
                "url": "https://10.4041/kjod.2013.43.6.271",
                "description": "Analyse 3D du mouvement dentaire"
            },
            {
                "authors": "Kulkarni et al.",
                "title": "Radiotherapy-induced oral mucositis and periodontitis",
                "journal": "J Appl Oral Sci",
                "year": "2019",
                "url": "https://10.1590/1678-7757-2019-0103",
                "description": "Effets de la radiothérapie sur les tissus bucco-dentaires"
            },
            {
                "authors": "Magne et al.",
                "title": "Influence of tooth preparation on stress distribution in molars",
                "journal": "J Prosthet Dent",
                "year": "2003",
                "url": "https://10.1016/S0022-3913(03)00125-2",
                "description": "Distribution des contraintes dans les molaires"
            }
        ]
        
        comp_frame = ttk.LabelFrame(scrollable_frame, text="Références complémentaires", padding=15)
        comp_frame.pack(fill=tk.X, pady=(0, 20))
        
        for ref in comp_refs:
            self.add_reference_card(comp_frame, ref, is_main=False)
            
        # Pack canvas et scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # === BOUTON FERMER ===
        button_frame = ttk.Frame(self, style='Modern.TFrame')
        button_frame.pack(fill=tk.X, padx=20, pady=(10, 20))
        
        # Bouton avec style personnalisé pour meilleure visibilité
        close_btn = tk.Button(button_frame, 
                             text="Fermer", 
                             font=('Segoe UI', 11, 'bold'),
                             bg='#3498db',
                             fg='white',
                             activebackground='#2980b9',
                             activeforeground='white',
                             relief='solid',
                             borderwidth=1,
                             padx=20,
                             pady=3,
                             cursor='hand2',
                             command=self.destroy)
        
        
        close_btn.pack(side=tk.RIGHT)
        
        # Binding scrolling
        self.bind_mousewheel(canvas)
        
    def add_reference_card(self, parent, ref_data, is_main=False):
        """Ajoute une carte de référence"""
        # Frame pour la référence
        ref_frame = ttk.Frame(parent, style='Modern.TFrame', relief=tk.RIDGE, borderwidth=1)
        ref_frame.pack(fill=tk.X, pady=(0, 15), padx=5)
        
        # Padding interne
        content_frame = ttk.Frame(ref_frame, style='Modern.TFrame', padding=12)
        content_frame.pack(fill=tk.X)
        
        # Auteurs (en gras)
        authors_label = ttk.Label(content_frame, text=ref_data["authors"],
                                 font=('Segoe UI', 11, 'bold'),
                                 foreground='#2c3e50' if is_main else '#34495e',
                                 background='#f0f0f0')
        authors_label.pack(anchor=tk.W)
        
        # Titre
        title_label = ttk.Label(content_frame, text=ref_data["title"],
                               style='Body.TLabel',
                               wraplength=780)
        title_label.pack(anchor=tk.W, pady=(2, 0), fill=tk.X)
        
        # Journal et année
        journal_text = f"{ref_data['journal']} ({ref_data['year']})"
        journal_label = ttk.Label(content_frame, text=journal_text,
                                 font=('Segoe UI', 9, 'italic'),
                                 foreground='#7f8c8d',
                                 background='#f0f0f0')
        journal_label.pack(anchor=tk.W, pady=(2, 0))
        
        # Description
        if ref_data.get("description"):
            desc_label = ttk.Label(content_frame, text=ref_data["description"],
                                  style='Info.TLabel',
                                  wraplength=780)
            desc_label.pack(anchor=tk.W, pady=(5, 0), fill=tk.X)
        
        # Lien cliquable
        link_label = ttk.Label(content_frame, text="🔗 Accéder à la publication",
                              foreground='#3498db',
                              background='#f0f0f0',
                              font=('Segoe UI', 9, 'underline'),
                              cursor='hand2')
        link_label.pack(anchor=tk.W, pady=(8, 0))
        link_label.bind("<Button-1>", 
                       lambda e, url=ref_data["url"]: webbrowser.open(url))
        
        # Effet hover
        def on_enter(e):
            link_label.config(foreground='#2980b9')
        def on_leave(e):
            link_label.config(foreground='#3498db')
            
        link_label.bind("<Enter>", on_enter)
        link_label.bind("<Leave>", on_leave)
        
    def bind_mousewheel(self, canvas):
        """Binding pour le scroll avec la molette"""
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
            
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")
            
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)


# === FONCTIONS UTILITAIRES POUR L'INTÉGRATION ===

def show_splash_screen(parent, on_accept_callback, on_decline_callback):
    """Affiche l'écran de démarrage RT-DENTX"""
    splash = RTDentxSplashScreen(parent, on_accept_callback, on_decline_callback)
    splash.focus_set()

def show_improved_about_rt_dentx(parent):
    """Affiche le dialogue À propos de RT-DENTX amélioré"""
    dialog = AboutRTDentxDialog(parent)
    dialog.focus_set()

def show_improved_sources(parent):
    """Affiche le dialogue Sources amélioré"""
    dialog = SourcesDialog(parent)
    dialog.focus_set()


# === MÉTHODES DE REMPLACEMENT POUR DicomViewer ===

def improved_show_about_rt_dentx(parent):
    """Méthode de remplacement pour DicomViewer.show_about_rt_dentx"""
    show_improved_about_rt_dentx(parent)

def improved_show_sources(parent):
    """Méthode de remplacement pour DicomViewer.show_sources"""
    show_improved_sources(parent)


if __name__ == "__main__":
    # Test des dialogues et du splash screen
    root = tk.Tk()
    root.title("Test RT-DENTX")
    root.geometry("400x300")
    root.withdraw()  # Cacher la fenêtre principale au début
    
    def on_splash_accept():
        """Appelé quand l'utilisateur accepte les conditions"""
        print("Conditions acceptées - Lancement de l'application")
        root.deiconify()  # Afficher la fenêtre principale
    
    def on_splash_decline():
        """Appelé quand l'utilisateur décline les conditions"""
        print("Conditions déclinées - Fermeture de l'application")
        root.quit()  # Fermer l'application
    
    # Afficher le splash screen en premier
    show_splash_screen(root, on_splash_accept, on_splash_decline)
    
    # Interface de test
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(frame, text="Test des dialogues RT-DENTX", 
             font=('Arial', 14, 'bold')).pack(pady=20)
    
    ttk.Button(frame, text="À propos de RT-DENTX",
              command=lambda: show_improved_about_rt_dentx(root)).pack(pady=10)
    
    ttk.Button(frame, text="Sources scientifiques",
              command=lambda: show_improved_sources(root)).pack(pady=10)
    
    ttk.Button(frame, text="Licence BSD 3-Clause",
              command=lambda: LicenseDialog(root)).pack(pady=10)
    
    ttk.Button(frame, text="Quitter", command=root.quit).pack(pady=20)
    
    root.mainloop()