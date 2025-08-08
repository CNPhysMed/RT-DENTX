#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de rapport PDF dosimétrique dentaire
© 2025 Caroline Moreau-Noblet — RT-DENTX — Licence BSD 3-Clause
"""

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("ReportLab non disponible. Installez avec: pip install reportlab")

import datetime
import os
import logging

logger = logging.getLogger(__name__)

def genere_rapport_pdf_enhanced(doses_data, parameters, patient_info=None, output_path="rapport_dentaire.pdf", config_manager=None):
    """
    Génère un rapport PDF dosimétrique dentaire complet
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("ReportLab requis pour générer le PDF. Installez avec: pip install reportlab")
    
    logger.info(f"Génération du rapport PDF: {output_path}")
    
    # Extraire la configuration
    if config_manager:
        risk_config = config_manager.get_config()["risk_levels"]
        recommendations_text = config_manager.get_recommendations_text()
    else:
        risk_config = {
            "low_threshold": 30.0,
            "moderate_threshold": 50.0,
            "low_label": "Faible",
            "moderate_label": "Modéré", 
            "high_label": "Élevé",
            "low_description": "Risque d'ostéoradionécrose faible",
            "moderate_description": "Risque d'ostéoradionécrose modéré",
            "high_description": "Risque d'ostéoradionécrose élevé"
        }
        recommendations_text = _get_default_recommendations(risk_config)
    
    # Créer le PDF
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    try:
        # === PAGE 1: EN-TÊTE ET PREMIÈRE CARTOGRAPHIE ===
        _draw_header(c, width, height, patient_info)
        y_pos = height - 250  # Position corrigée
        
        if parameters.get('dose_complete', True) and parameters.get('show_colors', True):
            title = "Cartographie dosimétrique - Dents complètes (dose moyenne en Gy)"
            _draw_anatomical_diagram(c, width/2, y_pos - 50, doses_data.get('complete', {}), 
                                   True, title, risk_config)
            _draw_legend_below_diagram(c, width/2, y_pos - 370, risk_config)
        
        _draw_footer(c, width, height)
        
        # === PAGES CARTOGRAPHIES SUPPLÉMENTAIRES ===
        if parameters.get('dose_couronne', False) and parameters.get('show_colors', True):
            c.showPage()
            # LOGO SUR CHAQUE PAGE
            _draw_logo(c, width, height)
            
            title = "Cartographie dosimétrique - Couronnes (dose moyenne en Gy)"
            _draw_anatomical_diagram(c, width/2, height/2 + 100, doses_data.get('couronne', {}), 
                                   True, title, risk_config)
            _draw_legend_below_diagram(c, width/2, height/2 - 200, risk_config)
            _draw_footer(c, width, height)
        
        if parameters.get('dose_racine', False) and parameters.get('show_colors', True):
            c.showPage()
            # LOGO SUR CHAQUE PAGE
            _draw_logo(c, width, height)
            
            title = "Cartographie dosimétrique - Racines (dose moyenne en Gy)"
            _draw_anatomical_diagram(c, width/2, height/2 + 100, doses_data.get('racine', {}), 
                                   True, title, risk_config)
            _draw_legend_below_diagram(c, width/2, height/2 - 200, risk_config)
            _draw_footer(c, width, height)
        
        # === PAGE TABLEAU ===
        c.showPage()
        # LOGO SUR CHAQUE PAGE
        _draw_logo(c, width, height)
        
        y_pos = height - 80
        c.setFont("Helvetica-Bold", 16)
        _draw_centered_text(c, width/2, y_pos, "Tableau récapitulatif des doses moyennes reçues")
        y_pos -= 40
        
        table_data = _create_dose_table_data(doses_data, parameters, risk_config)
        _draw_dose_table(c, table_data, doses_data.get('complete', {}), risk_config, y_pos, width)
        
        y_pos -= len(table_data) * 18 + 50
        if y_pos > 200:
            _draw_color_legend(c, y_pos, risk_config)
        
        _draw_footer(c, width, height)
        
        # === PAGE RECOMMANDATIONS ===
        c.showPage()
        # LOGO SUR CHAQUE PAGE
        _draw_logo(c, width, height)
        
        y_pos = height - 80
        _draw_recommendations(c, recommendations_text, y_pos)
        _draw_footer(c, width, height)
        
        # Finaliser le PDF
        c.save()
        logger.info(f"Rapport PDF généré avec succès: {output_path}")
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération PDF: {e}")
        raise

def create_simple_logo(c, x, y, width, height):
    """Crée un logo simple RT-DENTX si pas d'image disponible"""
    # Fond avec dégradé simulé
    c.setFillColor(colors.HexColor('#1E88E5'))
    c.rect(x, y, width, height, fill=1, stroke=0)
    
    # Bordure
    c.setStrokeColor(colors.HexColor('#1565C0'))
    c.setLineWidth(2)
    c.rect(x, y, width, height, fill=0, stroke=1)
    
    # Texte principal
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 12)
    text_x = x + width/2
    text_y = y + height/2 + 5
    _draw_centered_text(c, text_x, text_y, "RT-DENTX")
    
    # Sous-titre
    c.setFont("Helvetica", 8)
    _draw_centered_text(c, text_x, text_y - 15, "Dosimétrie dentaire")
    

def _draw_logo(c, width, height):
    """Dessine le logo RT-DENTX - PLUS PETIT ET PLUS HAUT"""
    try:
        logo_path = "assets/rt_dentx_logo.png"
        if os.path.exists(logo_path):
            # Logo plus petit (80x48 au lieu de 100x60) et plus haut (height - 60 au lieu de height - 80)
            c.drawImage(logo_path, width - 100, height - 60, 
                       width=80, height=48, preserveAspectRatio=True, mask='auto')
        else:
            # Logo texte simple PLUS PETIT et PLUS HAUT
            c.setFillColor(colors.HexColor('#1E88E5'))
            c.setFont("Helvetica-Bold", 10)  # Plus petit (10 au lieu de 12)
            _draw_centered_text(c, width - 60, height - 40, "RT-DENTX")  # Plus haut
            
            c.setFont("Helvetica", 7)  # Plus petit (7 au lieu de 8)
            c.setFillColor(colors.HexColor('#1565C0'))
            _draw_centered_text(c, width - 60, height - 52, "Dosimétrie dentaire")  # Plus haut
    except Exception as e:
        pass

def _draw_header(c, width, height, patient_info):
    """Dessine l'en-tête du rapport """
    
    # Logo RT-DENTX en haut à droite (sera appelé sur chaque page)
    _draw_logo(c, width, height)
    
    # Titre principal
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 18)
    _draw_centered_text(c, width/2, height - 50, "Rapport dosimétrique dentaire")
    
    # Informations patient NETTOYÉES (SANS date de génération)
    y_pos = height - 85
    if patient_info:
        c.setFont("Helvetica", 12)
        
        # Formatage de la date de naissance si disponible
        birth_date = patient_info.get('Date de naissance', 'Inconnue')
        if birth_date and birth_date != 'Inconnue' and len(birth_date) == 8 and birth_date.isdigit():
            # Dictionnaire des mois en français
            mois_fr = {
                '01': 'janvier', '02': 'février', '03': 'mars',
                '04': 'avril', '05': 'mai', '06': 'juin',
                '07': 'juillet', '08': 'août', '09': 'septembre',
                '10': 'octobre', '11': 'novembre', '12': 'décembre'
            }
            jour = birth_date[6:8]
            mois = birth_date[4:6]
            annee = birth_date[0:4]
            
            # Supprimer le 0 initial du jour si présent
            if jour.startswith('0'):
                jour = jour[1:]
            
            # Formater avec le nom du mois en français
            mois_texte = mois_fr.get(mois, mois)
            birth_date_formatted = f"{jour} {mois_texte} {annee}"
        else:
            birth_date_formatted = birth_date
        
        # SEULEMENT les informations essentielles
        essential_info = [
            ('Nom Prénom', patient_info.get('Nom', 'Inconnu')),
            ('Date de naissance', birth_date_formatted),
            ('ID Patient', patient_info.get('ID Patient', 'Inconnu'))
        ]
        
        # Ajouter le plan de traitement si disponible
        if 'Plan de traitement' in patient_info and patient_info['Plan de traitement']:
            plan_text = str(patient_info['Plan de traitement'])
            if '\n' in plan_text:
                lines = plan_text.split('\n')
                essential_info.append(('Plan', lines[0]))
                for line in lines[1:]:
                    essential_info.append(('', line))
            else:
                essential_info.append(('Plan', plan_text))
        
        for key, value in essential_info:
            if key:  # Si c'est un label
                c.drawString(50, y_pos, f"{key}: {value}")
            else:  # Si c'est une ligne de continuation
                c.drawString(50, y_pos, value)
            y_pos -= 15


def _draw_anatomical_diagram(c, center_x, center_y, doses_data, show_colors, title, risk_config):
    """Dessine le diagramme anatomique des dents avec doses"""
    # Titre
    c.setFont("Helvetica-Bold", 14)
    _draw_centered_text(c, center_x, center_y + 120, title)
    
    # Positions anatomiques des dents
    upper_positions = {
        # Maxillaire - disposition anatomique
        '21': (center_x + 15, center_y + 60),    # Incisive centrale gauche
        '11': (center_x - 15, center_y + 60),    # Incisive centrale droite
        '22': (center_x + 35, center_y + 55),    # Incisive latérale gauche
        '12': (center_x - 35, center_y + 55),    # Incisive latérale droite
        '23': (center_x + 55, center_y + 45),    # Canine gauche
        '13': (center_x - 55, center_y + 45),    # Canine droite
        '24': (center_x + 70, center_y + 30),    # Première prémolaire gauche
        '14': (center_x - 70, center_y + 30),    # Première prémolaire droite
        '25': (center_x + 85, center_y + 10),    # Deuxième prémolaire gauche
        '15': (center_x - 85, center_y + 10),    # Deuxième prémolaire droite
        '26': (center_x + 95, center_y - 15),    # Première molaire gauche
        '16': (center_x - 95, center_y - 15),    # Première molaire droite
        '27': (center_x + 100, center_y - 40),   # Deuxième molaire gauche
        '17': (center_x - 100, center_y - 40),   # Deuxième molaire droite
        '28': (center_x + 105, center_y - 65),   # Troisième molaire gauche
        '18': (center_x - 105, center_y - 65)    # Troisième molaire droite
    }
    
    lower_positions = {
        # Mandibule - disposition anatomique
        '48': (center_x - 100, center_y - 95),   # Troisième molaire droite
        '47': (center_x - 95, center_y - 120),   # Deuxième molaire droite
        '46': (center_x - 90, center_y - 145),   # Première molaire droite
        '45': (center_x - 80, center_y - 170),   # Deuxième prémolaire droite
        '44': (center_x - 65, center_y - 190),   # Première prémolaire droite
        '43': (center_x - 50, center_y - 205),   # Canine droite
        '42': (center_x - 30, center_y - 215),   # Incisive latérale droite
        '41': (center_x - 12, center_y - 220),   # Incisive centrale droite
        '31': (center_x + 12, center_y - 220),   # Incisive centrale gauche
        '32': (center_x + 30, center_y - 215),   # Incisive latérale gauche
        '33': (center_x + 50, center_y - 205),   # Canine gauche
        '34': (center_x + 65, center_y - 190),   # Première prémolaire gauche
        '35': (center_x + 80, center_y - 170),   # Deuxième prémolaire gauche
        '36': (center_x + 90, center_y - 145),   # Première molaire gauche
        '37': (center_x + 95, center_y - 120),   # Deuxième molaire gauche
        '38': (center_x + 100, center_y - 95)    # Troisième molaire gauche
    }
    
    all_positions = {**upper_positions, **lower_positions}
    
    # Dessiner les dents
    for tooth, (tx, ty) in all_positions.items():
        if tooth in doses_data:
            dose = doses_data[tooth]
            if show_colors:
                color = _get_dose_color(dose, risk_config)
                c.setFillColor(color)
            else:
                c.setFillColor(colors.lightgrey)
        else:
            c.setFillColor(colors.grey)
        
        # Forme de la dent (rectangle arrondi)
        tooth_width = 16
        tooth_height = 20
        c.roundRect(tx - tooth_width/2, ty - tooth_height/2, tooth_width, tooth_height, 3, fill=1, stroke=1)
        
        # Numéro et dose
        c.setFillColor(colors.black if tooth in doses_data else colors.white)
        
        c.setFont("Helvetica-Bold", 9)
        _draw_centered_text(c, tx, ty + 2, tooth)
        
        if tooth in doses_data:
            c.setFont("Helvetica", 7)
            _draw_centered_text(c, tx, ty - 8, f"{doses_data[tooth]:.1f}")
        else:
            c.setFont("Helvetica", 6)
            _draw_centered_text(c, tx, ty - 8, "N/C")
    
    # Annotations anatomiques
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    _draw_centered_text(c, center_x, center_y + 90, "MAXILLAIRE")
    _draw_centered_text(c, center_x, center_y - 250, "MANDIBULE")
    
    # Annotations latérales
    c.setFont("Helvetica-Bold", 10)
    
    # Côté droit du patient (gauche sur le diagramme)
    c.saveState()
    c.translate(center_x - 140, center_y - 60)
    c.rotate(90)
    _draw_centered_text(c, 0, 0, "DROITE")
    c.restoreState()
    
    # Côté gauche du patient (droite sur le diagramme)
    c.saveState()
    c.translate(center_x + 140, center_y - 60)
    c.rotate(-90)
    _draw_centered_text(c, 0, 0, "GAUCHE")
    c.restoreState()

def _draw_legend_below_diagram(c, center_x, y_pos, risk_config):
    """Dessine la légende sous le diagramme"""
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.black)
    
    legend_y = y_pos - 30
    c.drawString(center_x - 150, legend_y, "Légende des niveaux de risque:")
    legend_y -= 20
    
    c.setFont("Helvetica", 9)
    
    # Vert - Risque faible
    c.setFillColor(colors.green)
    c.rect(center_x - 150, legend_y-3, 12, 8, fill=1)
    c.setFillColor(colors.black)
    c.drawString(center_x - 130, legend_y, 
                f"Vert: Dose moyenne < {risk_config['low_threshold']:.0f} Gy - {risk_config['low_description']}")
    legend_y -= 15
    
    # Orange - Risque modéré
    c.setFillColor(colors.orange)
    c.rect(center_x - 150, legend_y-3, 12, 8, fill=1)
    c.setFillColor(colors.black)
    c.drawString(center_x - 130, legend_y, 
                f"Orange: {risk_config['low_threshold']:.0f}-{risk_config['moderate_threshold']:.0f} Gy - {risk_config['moderate_description']}")
    legend_y -= 15
    
    # Rouge - Risque élevé
    c.setFillColor(colors.red)
    c.rect(center_x - 150, legend_y-3, 12, 8, fill=1)
    c.setFillColor(colors.black)
    c.drawString(center_x - 130, legend_y, 
                f"Rouge: > {risk_config['moderate_threshold']:.0f} Gy - {risk_config['high_description']}")
    legend_y -= 15
    
    # Gris - Non contourée
    c.setFillColor(colors.grey)
    c.rect(center_x - 150, legend_y-3, 12, 8, fill=1)
    c.setFillColor(colors.black)
    c.drawString(center_x - 130, legend_y, "Gris: Dent non contourée - Dose non évaluée")

def _create_dose_table_data(doses_data, parameters, risk_config):
    """Crée les données du tableau de doses"""
    headers = ["Dent"]
    
    if parameters.get('dose_complete', True):
        headers.append("Dent complète\n(Gy)")
    if parameters.get('dose_couronne', False):
        headers.append("Couronne\n(Gy)")
    if parameters.get('dose_racine', False):
        headers.append("Racine\n(Gy)")
    
    headers.append("Niveau de\nrisque")
    
    # Ordre anatomique des dents
    tooth_order = [
        # Maxillaire droite (Q1)
        '18', '17', '16', '15', '14', '13', '12', '11',
        # Maxillaire gauche (Q2)
        '21', '22', '23', '24', '25', '26', '27', '28',
        # Mandibule gauche (Q3)
        '38', '37', '36', '35', '34', '33', '32', '31',
        # Mandibule droite (Q4)
        '41', '42', '43', '44', '45', '46', '47', '48'
    ]
    
    table_data = [headers]
    
    doses_complete = doses_data.get('complete', {})
    doses_crowns = doses_data.get('couronne', {})
    doses_roots = doses_data.get('racine', {})
    
    for tooth in tooth_order:
        is_contoured = tooth in doses_complete or tooth in doses_crowns or tooth in doses_roots
        
        if is_contoured:
            dose_complete = doses_complete.get(tooth, 0)
            dose_crown = doses_crowns.get(tooth, 0)
            dose_root = doses_roots.get(tooth, 0)
            
            row = [tooth]
            doses_in_row = []
            
            if parameters.get('dose_complete', True):
                if dose_complete > 0:
                    row.append(f"{dose_complete:.1f}")
                    doses_in_row.append(dose_complete)
                else:
                    row.append("N/C")
            
            if parameters.get('dose_couronne', False):
                if dose_crown > 0:
                    row.append(f"{dose_crown:.1f}")
                    doses_in_row.append(dose_crown)
                else:
                    row.append("N/C")
            
            if parameters.get('dose_racine', False):
                if dose_root > 0:
                    row.append(f"{dose_root:.1f}")
                    doses_in_row.append(dose_root)
                else:
                    row.append("N/C")
            
            # Niveau de risque basé sur la dose maximale de la ligne
            if doses_in_row:
                max_dose = max(doses_in_row)
                risk_level = _get_risk_level(max_dose, risk_config)
            else:
                risk_level = "Non évaluable"
            
            row.append(risk_level)
        else:
            # Dent non contourée
            row = [tooth]
            
            if parameters.get('dose_complete', True):
                row.append("Non contourée")
            if parameters.get('dose_couronne', False):
                row.append("Non contourée")
            if parameters.get('dose_racine', False):
                row.append("Non contourée")
            
            row.append("Non évaluable")
        
        table_data.append(row)
    
    return table_data

def _draw_dose_table(c, table_data, doses_complete, risk_config, y_pos, width):
    """Dessine le tableau des doses avec couleurs"""
    try:
        # Calculer les largeurs de colonnes
        num_columns = len(table_data[0])
        if num_columns == 3:
            col_widths = [60, 100, 150]
        elif num_columns == 4:
            col_widths = [60, 90, 90, 150]
        elif num_columns == 5:
            col_widths = [60, 80, 80, 80, 150]
        else:
            col_widths = [60] + [80] * (num_columns - 2) + [150]
        
        # Créer le tableau ReportLab
        table = Table(table_data, colWidths=col_widths)
        
        # Styles de base
        styles = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]
        
        # Appliquer les couleurs selon les doses
        for i, row in enumerate(table_data[1:], 1):
            tooth = row[0]
            
            # Extraire les doses numériques de la ligne
            doses_in_row = []
            for cell in row[1:-1]:  # Exclure dent et niveau de risque
                if isinstance(cell, str) and cell.replace('.', '').replace(',', '').isdigit():
                    try:
                        dose_val = float(cell.replace(',', '.'))
                        doses_in_row.append(dose_val)
                    except:
                        pass
            
            if doses_in_row:
                max_dose = max(doses_in_row)
                bg_color = _get_dose_color(max_dose, risk_config)
                styles.append(('BACKGROUND', (0, i), (-1, i), bg_color))
                
                # Texte blanc pour les doses élevées (rouge)
                if max_dose >= risk_config["moderate_threshold"]:
                    styles.append(('TEXTCOLOR', (0, i), (-1, i), colors.white))
            else:
                # Dent non contourée
                styles.append(('BACKGROUND', (0, i), (-1, i), colors.lightgrey))
                styles.append(('TEXTCOLOR', (0, i), (-1, i), colors.grey))
        
        table.setStyle(TableStyle(styles))
        
        # Dessiner le tableau
        table.wrapOn(c, width - 50, 600)
        table_height = len(table_data) * 18
        table.drawOn(c, 25, y_pos - table_height)
        
    except Exception as e:
        logger.error(f"Erreur création tableau: {e}")
        # Fallback simple en cas d'erreur
        _draw_simple_table_fallback(c, table_data, y_pos)

def _draw_simple_table_fallback(c, table_data, y_pos):
    """Dessine un tableau simple en cas d'erreur avec ReportLab"""
    c.setFont("Helvetica", 8)
    
    for i, row in enumerate(table_data):
        y = y_pos - (i * 12)
        text = " | ".join(str(cell) for cell in row)
        c.drawString(50, y, text)

def _draw_color_legend(c, y_pos, risk_config):
    """Dessine la légende des couleurs du tableau"""
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_pos, "Légende des niveaux de risque:")
    y_pos -= 20
    
    c.setFont("Helvetica", 10)
    
    # Vert
    c.setFillColor(colors.green)
    c.rect(50, y_pos-3, 15, 10, fill=1)
    c.setFillColor(colors.black)
    c.drawString(75, y_pos, f"Vert: Dose < {risk_config['low_threshold']:.0f} Gy - {risk_config['low_description']}")
    y_pos -= 18
    
    # Orange
    c.setFillColor(colors.orange)
    c.rect(50, y_pos-3, 15, 10, fill=1)
    c.setFillColor(colors.black)
    c.drawString(75, y_pos, f"Orange: {risk_config['low_threshold']:.0f}-{risk_config['moderate_threshold']:.0f} Gy - {risk_config['moderate_description']}")
    y_pos -= 18
    
    # Rouge
    c.setFillColor(colors.red)
    c.rect(50, y_pos-3, 15, 10, fill=1)
    c.setFillColor(colors.black)
    c.drawString(75, y_pos, f"Rouge: > {risk_config['moderate_threshold']:.0f} Gy - {risk_config['high_description']}")

def _draw_recommendations(c, recommendations_text, y_pos):
    """Dessine les recommandations cliniques"""
    for i, line in enumerate(recommendations_text):
        if i == 0:  # Titre principal
            c.setFont("Helvetica-Bold", 16)
        elif line.startswith("•"):
            c.setFont("Helvetica", 11)
        elif line.isupper() and ":" in line:
            c.setFont("Helvetica-Bold", 12)
        else:
            c.setFont("Helvetica", 11)
        
        c.drawString(50, y_pos, line)
        y_pos -= 16

def _draw_footer(c, width, height):
    """Dessine le pied de page avec mention légale"""
    # Mention légale
    disclaimer_lines = [
        "Ce rapport dosimétrique a été généré automatiquement à partir des données TPS et du choix des volumes dentaires par l'opérateur.",
        "Les doses indiquées représentent une estimation de la dose délivrée dans un volume géométrique simplifié et doivent être interprétées en fonction du contexte clinique.",
        "L'utilisation de ce rapport et des données qu'il contient se fait sous la responsabilité de l'utilisateur uniquement."
    ]
    
    y_start = 80
    line_height = 8
    
    c.setFont("Helvetica-Oblique", 7)
    c.setFillColor(colors.grey)
    
    for i, line in enumerate(disclaimer_lines):
        y_pos = y_start - (i * line_height)
        _draw_centered_text(c, width/2, y_pos, line)
    
    # Ligne de bas de page
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.black)
    _draw_centered_text(c, width/2, 30, f"Rapport généré par RT-DENTX - {datetime.datetime.now().strftime('%d/%m/%Y')}")

def _draw_centered_text(c, x, y, text):
    """Dessine du texte centré"""
    text_width = c.stringWidth(text)
    c.drawString(x - text_width / 2, y, text)

def _get_dose_color(dose, risk_config):
    """Retourne la couleur selon la dose et la configuration"""
    if dose < risk_config["low_threshold"]:
        return colors.green
    elif dose < risk_config["moderate_threshold"]:
        return colors.orange
    else:
        return colors.red

def _get_risk_level(dose, risk_config):
    """Retourne le niveau de risque selon la dose"""
    if dose < risk_config["low_threshold"]:
        return risk_config["low_label"]
    elif dose < risk_config["moderate_threshold"]:
        return risk_config["moderate_label"]
    else:
        return risk_config["high_label"]

def _get_default_recommendations(risk_config):
    """Retourne les recommandations par défaut"""
    return [
        "Recommandations cliniques",
        "",
        "PRÉVENTION DE L'OSTÉORADIONÉCROSE :",
        "",
        "• Des précautions particulières doivent être prises lors des soins bucco-dentaires,",
        "  en particulier en cas d'avulsion ou d'un autre geste chirurgical en territoire irradié.",
        "",
        f"• Surveillance clinique renforcée pour les dents ayant reçu > {risk_config['moderate_threshold']:.0f} Gy (risque élevé)",
        f"  et entre {risk_config['low_threshold']:.0f}-{risk_config['moderate_threshold']:.0f} Gy (risque modéré).",
        "",
        "CONTACT :",
        "",
        "En cas de doute, veuillez prendre contact avec :",
        "• Le radiothérapeute référent, ou",
        "• Le service d'odontologie ou de chirurgie maxillofaciale du CHU le plus proche."
    ]

