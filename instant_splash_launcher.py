#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RT-DENTX - Build Dual-EXE Corrigé
© 2025 Caroline Moreau-Noblet — RT-DENTX — Licence BSD 3-Clause

Crée 2 exe dans dist/ :
- RT-DENTX.exe : AVEC icône (pour que l'utilisateur clique dessus)
- RT-DENTX-Core.exe : SANS icône (pour ne pas confondre)
"""

import os
import sys
import subprocess
import shutil

# ============= LANCEUR MINIMAL =============
LAUNCHER_CODE = '''#!/usr/bin/env python3
"""RT-DENTX - Lanceur instantané"""
import tkinter as tk
import subprocess
import os
import sys

# Splash immédiat
root = tk.Tk()
root.overrideredirect(True)
root.attributes('-topmost', True)

# Transparence
if sys.platform == 'win32':
    root.attributes('-transparentcolor', 'magenta')
    root.configure(bg='magenta')
else:
    root.configure(bg='black')

# Centrer
size = 256
root.geometry(f'{size}x{size}+{(root.winfo_screenwidth()-size)//2}+{(root.winfo_screenheight()-size)//2}')

# Afficher le logo
try:
    # En mode exe, chercher dans _MEIPASS
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    logo_path = os.path.join(base_path, 'rt_dentx_logo.png')
    
    if os.path.exists(logo_path):
        logo = tk.PhotoImage(file=logo_path)
        if logo.width() > size:
            factor = (logo.width() // size) + 1
            logo = logo.subsample(factor, factor)
        label = tk.Label(root, image=logo, bg='magenta' if sys.platform == 'win32' else 'black')
        label.pack()
    else:
        # Emoji si pas de logo
        tk.Label(root, text="🦷", font=('Arial', 100), 
                bg='magenta' if sys.platform == 'win32' else 'black', 
                fg='#3498db').pack(expand=True)
except:
    tk.Label(root, text="🦷", font=('Arial', 100), 
            bg='magenta' if sys.platform == 'win32' else 'black', 
            fg='#3498db').pack(expand=True)

root.update()

# Lancer l'app principale
def launch():
    exe_dir = os.path.dirname(os.path.abspath(sys.executable if hasattr(sys, 'frozen') else __file__))
    core_exe = os.path.join(exe_dir, "RT-DENTX-Core.exe")
    
    if os.path.exists(core_exe):
        subprocess.Popen([core_exe])
        root.after(2000, root.destroy)
    else:
        tk.Label(root, text="Erreur: Core non trouvé", fg='red', bg='white').pack()
        root.after(3000, root.destroy)

root.after(100, launch)
root.mainloop()
'''

def clean():
    """Nettoie les dossiers de build"""
    print("🧹 Nettoyage...")
    for folder in ['build', 'dist', '__pycache__']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    for file in ['*.spec', 'launcher_temp.py']:
        import glob
        for f in glob.glob(file):
            os.remove(f)
    print("   ✓ Nettoyé")

def verify_assets():
    """Vérifie que les assets existent"""
    print("\n📁 Vérification des assets...")
    
    required_files = {
        'assets/rt_dentx_logo.png': 'Logo PNG',
        'assets/rt_dentx_logo.ico': 'Icône ICO (pour le lanceur)'
    }
    
    all_ok = True
    for file, desc in required_files.items():
        if os.path.exists(file):
            size = os.path.getsize(file) / 1024
            print(f"   ✓ {desc}: {file} ({size:.1f} KB)")
        else:
            print(f"   ⚠️ {desc} manquant: {file}")
            if file.endswith('.ico'):
                print("      (Le lanceur n'aura pas d'icône)")
            all_ok = False
    
    return all_ok

def build_launcher():
    """Compile le lanceur ultra-léger AVEC ICÔNE"""
    print("\n🚀 [1/2] Compilation du lanceur léger...")
    print("         → AVEC icône (pour que l'utilisateur clique dessus)")
    
    # Créer le fichier temporaire
    with open('launcher_temp.py', 'w', encoding='utf-8') as f:
        f.write(LAUNCHER_CODE)
    
    # Préparer la commande PyInstaller
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm',
        '--onefile',
        '--windowed',
        '--name', 'RT-DENTX',
        '--distpath', 'dist',
        '--workpath', 'build/launcher',
        '--specpath', 'build'
    ]
    
    # AJOUTER L'ICÔNE pour le lanceur (celui sur lequel on clique)
    if os.path.exists('assets/rt_dentx_logo.ico'):
        cmd.extend(['--icon', 'assets/rt_dentx_logo.ico'])
        print("   → Icône ajoutée au lanceur ✓")
    else:
        print("   → Pas d'icône (fichier .ico manquant)")
    
    # Ajouter SEULEMENT le logo PNG (pas tout le dossier assets)
    if os.path.exists('assets/rt_dentx_logo.png'):
        # Copier temporairement le logo à la racine pour éviter les problèmes de chemin
        shutil.copy('assets/rt_dentx_logo.png', 'rt_dentx_logo.png')
        cmd.extend(['--add-data', 'rt_dentx_logo.png;.'])
    
    # Exclure les modules lourds
    exclusions = [
        'numpy', 'scipy', 'matplotlib', 'PIL', 'pydicom', 
        'reportlab', 'pandas', 'setuptools', 'pip', 'wheel'
    ]
    for module in exclusions:
        cmd.extend(['--exclude-module', module])
    
    # Ajouter le script
    cmd.append('launcher_temp.py')
    
    # Exécuter
    print("   Compilation...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Nettoyer les fichiers temporaires
    if os.path.exists('launcher_temp.py'):
        os.remove('launcher_temp.py')
    if os.path.exists('rt_dentx_logo.png'):
        os.remove('rt_dentx_logo.png')
    
    if result.returncode != 0:
        print("   ❌ Erreur compilation lanceur")
        print("   Stderr:", result.stderr[-500:] if result.stderr else "")
        return False
    
    if os.path.exists('dist/RT-DENTX.exe'):
        size = os.path.getsize('dist/RT-DENTX.exe') / (1024 * 1024)
        print(f"   ✓ Lanceur créé: {size:.1f} MB (avec icône)")
        return True
    else:
        print("   ❌ Lanceur non créé")
        return False

def build_main():
    """Compile l'application principale SANS ICÔNE"""
    print("\n📦 [2/2] Compilation de l'application principale...")
    print("         → SANS icône (pour ne pas confondre l'utilisateur)")
    
    # Vérifier que main.py existe
    if not os.path.exists('main.py'):
        print("   ❌ main.py introuvable!")
        return False
    
    # Commande PyInstaller pour l'app principale
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm',
        '--onefile',
        '--windowed',
        '--name', 'RT-DENTX-Core',
        '--distpath', 'dist',
        '--workpath', 'build/main',
        '--specpath', 'build'
    ]
    
    # PAS D'ICÔNE pour RT-DENTX-Core.exe !
    # On n'ajoute PAS --icon pour que l'exe ait l'icône Windows par défaut
    print("   → Pas d'icône personnalisée (icône Windows par défaut)")
    
    # Ajouter le dossier assets complet pour l'app principale
    if os.path.exists('assets'):
        # Utiliser le chemin absolu pour éviter les problèmes
        assets_path = os.path.abspath('assets')
        cmd.extend(['--add-data', f'{assets_path};assets'])
    
    # Hidden imports
    imports = [
        'numpy', 'scipy', 'scipy.interpolate', 'scipy.spatial',
        'matplotlib', 'PIL', 'pydicom', 'reportlab'
    ]
    
    # Ajouter les imports optionnels s'ils existent
    optional_imports = [
        'scipy.special', 'scipy.special._cdflib', 
        'scipy._lib.messagestream', 'skimage', 
        'tooth_generator', 'pkg_resources.extern'
    ]
    
    for imp in imports:
        cmd.extend(['--hidden-import', imp])
    
    # Essayer d'ajouter les imports optionnels
    for imp in optional_imports:
        try:
            __import__(imp)
            cmd.extend(['--hidden-import', imp])
        except ImportError:
            pass  # Module non installé, on l'ignore
    
    # Script principal
    cmd.append('main.py')
    
    # Exécuter
    print("   Compilation en cours (peut prendre 2-3 minutes)...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("   ❌ Erreur compilation application")
        print("   Stderr:", result.stderr[-500:] if result.stderr else "")
        return False
    
    if os.path.exists('dist/RT-DENTX-Core.exe'):
        size = os.path.getsize('dist/RT-DENTX-Core.exe') / (1024 * 1024)
        print(f"   ✓ Application créée: {size:.1f} MB (sans icône)")
        return True
    else:
        print("   ❌ Application non créée")
        return False

def main():
    """Build principal"""
    print("=" * 60)
    print("RT-DENTX - BUILD DUAL-EXE")
    print("Lanceur AVEC icône | Core SANS icône")
    print("=" * 60)
    
    # Vérifier Python et PyInstaller
    print("\n🔍 Vérification de l'environnement...")
    try:
        import PyInstaller
        print(f"   ✓ PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("   ❌ PyInstaller non installé!")
        print("   Installez avec: pip install pyinstaller")
        return
    
    # Nettoyer
    clean()
    
    # Vérifier les assets
    if not verify_assets():
        print("\n⚠️ Des assets sont manquants mais on continue...")
    
    # Build du lanceur
    if not build_launcher():
        print("\n❌ Échec du build du lanceur")
        return
    
    # Build de l'app principale
    if not build_main():
        print("\n❌ Échec du build de l'application")
        return
    
    # Nettoyer les fichiers temporaires
    print("\n🧹 Nettoyage final...")
    if os.path.exists('build'):
        shutil.rmtree('build')
    for file in ['*.spec']:
        import glob
        for f in glob.glob(file):
            os.remove(f)
    
    # Résumé
    print("\n" + "=" * 60)
    print("✅ BUILD TERMINÉ AVEC SUCCÈS!")
    print("=" * 60)
    print("\n📁 Fichiers créés dans dist/:")
    print("   • RT-DENTX.exe      → Lanceur (AVEC icône) ✨")
    print("   • RT-DENTX-Core.exe → Application (SANS icône)")
    print("\n🎯 L'utilisateur voit clairement sur quel fichier cliquer !")
    print("\n🚀 Utilisation:")
    print("   1. Les 2 exe doivent être dans le même dossier")
    print("   2. L'utilisateur lance RT-DENTX.exe (celui avec l'icône)")
    print("   3. L'icône apparaît instantanément!")
    print("\n📦 Pour distribuer:")
    print("   - Créez un ZIP avec les 2 exe")
    print("   - Ou un installateur avec Inno Setup")
    
    # Ouvrir le dossier
    if sys.platform == 'win32' and os.path.exists('dist'):
        os.startfile('dist')

if __name__ == "__main__":
    main()