#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire de configuration pour RT-DENTX
Gère les seuils de dose, recommandations cliniques, etc.
Permet configuration de session ou persistante
© 2025 Caroline Moreau-Noblet — RT-DENTX — Licence BSD 3-Clause
"""

import json
import copy
from pathlib import Path

class ConfigManager:
    """Gestionnaire de configuration avec persistance optionnelle"""
    
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
        "recommendations": {
            "title": "Recommandations cliniques",
            "prevention_title": "PRÉVENTION DE L'OSTÉORADIONÉCROSE :",
            "prevention_items": [
                "",
                "• Des précautions particulières doivent être prises lors des soins bucco-dentaires,",
                "  en particulier en cas d'avulsion ou d'un autre geste chirurgical en territoire irradié.",
                "",
                "• Surveillance clinique renforcée pour les dents ayant reçu > 50 Gy (risque élevé)",
                "  et entre 30-50 Gy (risque modéré).",
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
    
    def __init__(self):
        self.config_file = self._get_config_file_path()
        self.session_config = None  # Configuration temporaire pour la session
        self.persistent_config = None  # Configuration persistante chargée
        
        # Charger la configuration persistante si elle existe
        self._load_persistent_config()
    
    def _get_config_file_path(self):
        """Détermine le chemin du fichier de configuration"""
        # Utiliser le répertoire utilisateur pour la persistance
        user_data_dir = Path.home() / ".rt_dentx"
        user_data_dir.mkdir(exist_ok=True)
        return user_data_dir / "config.json"
    
    def _load_persistent_config(self):
        """Charge la configuration persistante depuis le fichier"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.persistent_config = json.load(f)
                print(f"[INFO] Configuration persistante chargée depuis {self.config_file}")
            else:
                print(f"[INFO] Aucune configuration persistante trouvée, utilisation des valeurs par défaut")
        except Exception as e:
            print(f"[ERREUR] Impossible de charger la configuration persistante: {e}")
            self.persistent_config = None
    
    def get_config(self):
        """
        Retourne la configuration complète avec gestion des priorités
        Priorité: session > persistante > défaut
        """
        # Commencer avec la config par défaut complète
        config = copy.deepcopy(self.DEFAULT_CONFIG)
        
        # Appliquer la configuration persistante si elle existe
        if self.persistent_config:
            # Gérer les deux formats possibles
            if "recommendations_text" in self.persistent_config:
                # Nouveau format simple - convertir en structure
                config = self._apply_simple_format(config, self.persistent_config)
            else:
                # Ancien format complexe
                self._merge_config(config, self.persistent_config)
        
        # Appliquer la configuration de session (prioritaire)
        if self.session_config:
            if "recommendations_text" in self.session_config:
                config = self._apply_simple_format(config, self.session_config)
            else:
                self._merge_config(config, self.session_config)
        
        return config
    
    def _apply_simple_format(self, base_config, simple_config):
        """Applique le format simple (avec recommendations_text) sur la config de base"""
        config = copy.deepcopy(base_config)
        
        # Appliquer les seuils de risque
        if "risk_levels" in simple_config:
            config["risk_levels"].update(simple_config["risk_levels"])
        
        # Convertir recommendations_text en structure complexe SI nécessaire
        if "recommendations_text" in simple_config and simple_config["recommendations_text"]:
            # Pour le moment, garder la structure existante mais mettre à jour les seuils
            rec_text = simple_config["recommendations_text"]
            
            # Remplacer les valeurs dans les items de prévention
            risk = config["risk_levels"]
            updated_items = []
            
            for item in config["recommendations"]["prevention_items"]:
                if "50 Gy" in item:
                    item = item.replace("50 Gy", f"{risk['moderate_threshold']:.0f} Gy")
                if "30-50 Gy" in item:
                    item = item.replace("30-50 Gy", 
                                      f"{risk['low_threshold']:.0f}-{risk['moderate_threshold']:.0f} Gy")
                updated_items.append(item)
            
            config["recommendations"]["prevention_items"] = updated_items
        
        return config
    
    def _merge_config(self, base_config, override_config):
        """Fusionne deux configurations (récursif)"""
        for key, value in override_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                self._merge_config(base_config[key], value)
            else:
                base_config[key] = value
    
    def set_session_config(self, config):
        """Définit une configuration temporaire pour la session actuelle"""
        self.session_config = copy.deepcopy(config)
        print("[INFO] Configuration de session appliquée (temporaire)")
    
    def clear_session_config(self):
        """Supprime la configuration de session"""
        self.session_config = None
        print("[INFO] Configuration de session supprimée")
    
    def update_persistent_config(self, config):
        """Met à jour et sauvegarde la configuration persistante"""
        try:
            self.persistent_config = copy.deepcopy(config)
            
            # Sauvegarder dans le fichier
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.persistent_config, f, indent=2, ensure_ascii=False)
            
            print(f"[INFO] Configuration persistante sauvegardée dans {self.config_file}")
            
            # Appliquer immédiatement (effacer la config de session)
            self.session_config = None
            
        except Exception as e:
            raise Exception(f"Impossible de sauvegarder la configuration: {e}")
    
    def reset_to_default(self):
        """Remet la configuration aux valeurs par défaut"""
        try:
            # Supprimer le fichier de configuration persistante
            if self.config_file.exists():
                self.config_file.unlink()
                print(f"[INFO] Fichier de configuration supprimé: {self.config_file}")
            
            # Réinitialiser les configurations en mémoire
            self.persistent_config = None
            self.session_config = None
            
            print("[INFO] Configuration remise aux valeurs par défaut")
            
        except Exception as e:
            raise Exception(f"Impossible de remettre aux valeurs par défaut: {e}")
    
    def get_recommendations_text(self):
        """Retourne le texte des recommandations formaté pour le PDF"""
        config = self.get_config()
        
        # Si on a un format simple avec recommendations_text direct
        if "recommendations_text" in config and config["recommendations_text"]:
            # Remplacer les placeholders
            text = config["recommendations_text"]
            risk = config["risk_levels"]
            text = text.replace("{low_threshold}", f"{risk['low_threshold']:.0f}")
            text = text.replace("{moderate_threshold}", f"{risk['moderate_threshold']:.0f}")
            
            # Convertir en liste de lignes
            return text.split('\n')
        
        # Sinon utiliser le format complexe
        rec_config = config["recommendations"]
        lines = [rec_config["title"]]
        lines.append("")
        lines.append(rec_config["prevention_title"])
        lines.extend(rec_config["prevention_items"])
        lines.append("")
        lines.append(rec_config["contact_title"])
        lines.extend(rec_config["contact_items"])
        
        return lines
    
    
    def get_simplified_config(self):
        """Retourne la configuration simplifiée pour l'interface"""
        config = self.get_config()
        
        # Convertir en format simple
        simple_config = {
            "risk_levels": config["risk_levels"],
            "recommendations_text": None
        }
        
        # Si on a déjà recommendations_text, l'utiliser
        if "recommendations_text" in config:
            simple_config["recommendations_text"] = config["recommendations_text"]
        else:
            # Sinon, convertir depuis le format complexe
            simple_config["recommendations_text"] = "\n".join(self.get_recommendations_text())
        
        return simple_config
    
    def get_risk_thresholds(self):
        """Retourne les seuils de risque"""
        config = self.get_config()
        return {
            'low': config["risk_levels"]["low_threshold"],
            'moderate': config["risk_levels"]["moderate_threshold"]
        }
    
    def get_risk_labels(self):
        """Retourne les libellés des niveaux de risque"""
        config = self.get_config()
        risk_levels = config["risk_levels"]
        return {
            'low': risk_levels["low_label"],
            'moderate': risk_levels["moderate_label"],
            'high': risk_levels["high_label"]
        }
    
    def export_config(self, file_path):
        """Exporte la configuration actuelle vers un fichier"""
        try:
            current_config = self.get_config()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(current_config, f, indent=2, ensure_ascii=False)
            print(f"[INFO] Configuration exportée vers {file_path}")
        except Exception as e:
            raise Exception(f"Impossible d'exporter la configuration: {e}")
    
    def import_config(self, file_path, make_persistent=False):
        """Importe une configuration depuis un fichier"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Valider la structure de base
            self._validate_config_structure(imported_config)
            
            if make_persistent:
                self.update_persistent_config(imported_config)
            else:
                self.set_session_config(imported_config)
            
            print(f"[INFO] Configuration importée depuis {file_path}")
            
        except Exception as e:
            raise Exception(f"Impossible d'importer la configuration: {e}")
    
    def _validate_config_structure(self, config):
        """Valide la structure d'une configuration"""
        required_keys = ["risk_levels", "recommendations"]
        
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Clé manquante dans la configuration: {key}")
        
        # Valider les seuils
        risk_levels = config["risk_levels"]
        if risk_levels["low_threshold"] >= risk_levels["moderate_threshold"]:
            raise ValueError("Le seuil faible doit être inférieur au seuil modéré")
        
        print("[INFO] Structure de configuration validée")
    
    def get_config_info(self):
        """Retourne des informations sur la configuration actuelle"""
        info = {
            'active_type': 'default',
            'has_session': self.session_config is not None,
            'has_persistent': self.persistent_config is not None,
            'config_file': str(self.config_file),
            'config_file_exists': self.config_file.exists()
        }
        
        if self.session_config is not None:
            info['active_type'] = 'session'
        elif self.persistent_config is not None:
            info['active_type'] = 'persistent'
        
        return info
    
    

