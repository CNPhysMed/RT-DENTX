#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RT-DENTX - Point d'entrée pour l'exécutable final
© 2025 Caroline Moreau-Noblet — RT-DENTX — Licence BSD 3-Clause
"""
# ============ OPTIMISATIONS POUR L'EXÉCUTABLE ============
import sys
import os

# Détection si on est dans l'exécutable compilé
if getattr(sys, 'frozen', False):
    # On est dans l'exe PyInstaller
    os.environ['MPLBACKEND'] = 'TkAgg'  # Force le backend matplotlib
    
# Configuration matplotlib AVANT l'import
import matplotlib
matplotlib.use('TkAgg')  # Backend optimisé pour Tkinter

# Désactiver les fonctionnalités non utilisées
import matplotlib.pyplot as plt
plt.ioff()  # Mode non-interactif = plus rapide

# ============ IMPORTS OPTIMISÉS ============
# Au lieu d'importer tout numpy, importez seulement ce dont vous avez besoin
from numpy import array, zeros, ones, float32, int32, ndarray
from numpy import min as np_min, max as np_max, mean as np_mean
from numpy import sqrt, ceil, floor

# Imports sélectifs pour scipy
from scipy.interpolate import interp1d, RegularGridInterpolator
from scipy.spatial import distance

# Import tkinter optimisé
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ============ VOS IMPORTS HABITUELS ============

def main():
    """Point d'entrée principal pour l'exécutable"""
    print("🦷 RT-DENTX - Version Release")
    print("=" * 50)
    
    try:
        # Créer la fenêtre racine
        root = tk.Tk()
        root.title("RT-DENTX")
        root.geometry("1600x900")
        root.withdraw()  # Cacher au début
        
        # Importer DicomViewer normalement
        from dicom_viewer_main import DicomViewer
        
        # Créer l'application avec splash normal
        app = DicomViewer(root)
        
        print("✅ RT-DENTX prêt")
        root.mainloop()
        print("✅ Application fermée")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        messagebox.showerror("Erreur", f"Erreur de lancement: {e}")

if __name__ == "__main__":
    main()