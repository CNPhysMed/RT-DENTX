#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'édition des points de référence dentaires -
Placement et gestion des 6 points de référence avec sélection multiple
© 2025 Caroline Moreau-Noblet — RT-DENTX — Licence BSD 3-Clause
"""

import numpy as np
from tkinter import simpledialog
import logging
from matplotlib.patches import Rectangle

logger = logging.getLogger(__name__)

class ToothReferenceEditor:
    """Éditeur pour le placement des points de référence dentaires """
    
    def __init__(self, ax, canvas, get_current_slice_index, ct_viewer):
        self.ax = ax
        self.canvas = canvas
        self.get_current_slice_index = get_current_slice_index
        self.ct_viewer = ct_viewer
        
        # Points de référence requis dans l'ordre
        self.reference_teeth = ["11", "13", "18", "41", "43", "48"]
        self.points = {}  # clé: nom dent, valeur: (x_mm, y_mm, z_slice)
        self.labels = {}  # clé: nom dent, valeur: (pt, lbl)
        
        # État
        self.placing_mode = False
        self.edit_mode = False
        self.current_tooth_index = 0
        self.next_point_to_place = None
        
        # Variables pour l'édition/déplacement
        self.selected = None
        self.selected_group = set()
        self.drag_start = None
        
        # Variables pour sélection rectangulaire (clic droit prolongé)
        self.rect_start = None
        self.rect_patch = None
        self.rect_mode = False
        self.is_right_dragging = False  # NOUVEAU: pour détecter le clic droit prolongé
        
        # Événements
        self.cid_press = None
        self.cid_motion = None
        self.cid_release = None
        self.cid_key = None
        
        logger.info(f"ToothReferenceEditor initialisé - Points requis: {', '.join(self.reference_teeth)}")
    
    def start_placing_mode(self):
        """Active le mode placement des points de référence"""
        self.placing_mode = True
        self.current_tooth_index = 0
        self.next_point_to_place = None
        
        # Connecter les événements seulement si pas déjà connectés
        if not self.cid_press:
            self.cid_press = self.canvas.mpl_connect('button_press_event', self.on_press)
        
        logger.info(f"Mode placement activé - Utilisez Ctrl+Clic gauche pour placer la dent {self.reference_teeth[0]}")
        
    def start_edit_mode(self):
        """Active le mode édition des points existants"""
        self.edit_mode = True
    
        # Connecter les événements seulement si pas déjà connectés
        if not self.cid_press:
            self.cid_press = self.canvas.mpl_connect('button_press_event', self.on_press)
        if not self.cid_motion:
            self.cid_motion = self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        if not self.cid_release:
            self.cid_release = self.canvas.mpl_connect('button_release_event', self.on_release)
        if not self.cid_key:
            self.cid_key = self.canvas.mpl_connect('key_press_event', self.on_key)
        
        logger.info("Mode édition activé - Contrôles disponibles:")
        logger.info("  • Clic gauche: sélectionner/déplacer point")
        logger.info("  • Ctrl+Clic gauche: placer nouveau point")
        logger.info("  • Ctrl+Clic droit: supprimer point")
        logger.info("  • Clic droit + glisser: sélection rectangulaire")
        logger.info("  • Touche R: rotation groupe sélectionné")
        logger.info("  • Suppr: supprimer sélection")
        
    def stop_placing_mode(self):
        """Désactive uniquement le mode placement"""
        self.placing_mode = False
        self.current_tooth_index = 0
        self.next_point_to_place = None
        logger.info("Mode placement désactivé")
    
    def stop_edit_mode(self):
        """Désactive uniquement le mode édition"""
        self.edit_mode = False
        
        # Réinitialiser les variables d'édition
        self.selected = None
        self.selected_group.clear()
        self.drag_start = None
        self.rect_start = None
        self.rect_mode = False
        self.is_right_dragging = False
        
        # Supprimer le rectangle de sélection s'il existe
        if self.rect_patch:
            self.rect_patch.remove()
            self.rect_patch = None
            self.canvas.draw_idle()
        
        logger.info("Mode édition désactivé")
        
    def stop_interaction(self):
        """Désactive tous les modes d'interaction"""
        self.placing_mode = False
        self.edit_mode = False
        
        # Déconnecter TOUS les événements
        if self.cid_press:
            self.canvas.mpl_disconnect(self.cid_press)
            self.cid_press = None
        if self.cid_motion:
            self.canvas.mpl_disconnect(self.cid_motion)
            self.cid_motion = None
        if self.cid_release:
            self.canvas.mpl_disconnect(self.cid_release)
            self.cid_release = None
        if self.cid_key:
            self.canvas.mpl_disconnect(self.cid_key)
            self.cid_key = None
            
        # Réinitialiser les variables d'état
        self.selected = None
        self.selected_group.clear()
        self.drag_start = None
        self.rect_start = None
        self.rect_mode = False
        self.is_right_dragging = False
        
        # Supprimer le rectangle de sélection s'il existe
        if self.rect_patch:
            self.rect_patch.remove()
            self.rect_patch = None
            self.canvas.draw_idle()
            
        logger.info("Mode interaction désactivé")
    
    def on_press(self, event):
        """Gestion des clics souris - VERSION AVEC CTRL"""
        if not event.inaxes or event.inaxes != self.ax:
            return
            
        x_mm, y_mm = event.xdata, event.ydata
        slice_index = self.get_current_slice_index()
        
        # Validation des coordonnées
        if not self._validate_coordinates(x_mm, y_mm, slice_index):
            return
        
        # IMPORTANT : Passer l'événement complet (event) et pas seulement event.button
        if self.edit_mode:
            self._handle_edit_click(x_mm, y_mm, slice_index, event.button, event)
        elif self.placing_mode:
            self._handle_placement_click(x_mm, y_mm, slice_index, event.button, event)
    
    def on_motion(self, event):
        """Gestion du déplacement de points et sélection rectangulaire """
        if not self.edit_mode or not event.inaxes:
            return
            
        if event.xdata is None or event.ydata is None:
            return
        
        x_mm, y_mm = event.xdata, event.ydata
        slice_index = self.get_current_slice_index()
        
        # Gestion de la sélection rectangulaire (clic droit prolongé)
        if self.is_right_dragging and self.rect_start:
            self._update_selection_rectangle(x_mm, y_mm)
            return
            
        # Déplacement de points existant
        if self.selected and self.drag_start:
            if not self._validate_coordinates(x_mm, y_mm, slice_index):
                return
            
            dx = x_mm - self.drag_start[0]
            dy = y_mm - self.drag_start[1]
            
            if self.selected in self.selected_group and len(self.selected_group) > 1:
                # Déplacer le groupe
                for name in self.selected_group:
                    if name in self.points:
                        x, y, z = self.points[name]
                        self.points[name] = (x + dx, y + dy, z)
                logger.debug(f"Déplacement de groupe: {len(self.selected_group)} points")
            else:
                # Déplacer le point sélectionné
                if self.selected in self.points:
                    x, y, z = self.points[self.selected]
                    self.points[self.selected] = (x_mm, y_mm, z)
            
            self.drag_start = (x_mm, y_mm)
            self.draw_all_points()
    
    def on_release(self, event):
        """Gestion du relâchement souris """
        if not self.edit_mode:
            return
        
        # Finaliser la sélection rectangulaire (clic droit prolongé)
        if self.is_right_dragging and self.rect_start:
            self._finalize_rectangle_selection()
            self.is_right_dragging = False
            return
            
        self.drag_start = None
        self.selected = None
        
    
    def _notify_tooth_generator_update(self):
        """Notifie le tooth_generator que les points ont été modifiés"""
        if hasattr(self.ct_viewer, 'tooth_generator') and self.ct_viewer.tooth_generator:
            # Mettre à jour les points de référence dans le générateur
            reference_teeth = ['11', '13', '18', '41', '43', '48']  # Les 6 VRAIS points de référence
            
            # Filtrer uniquement les points de référence
            reference_points = {name: coords for name, coords in self.points.items() 
                              if name in reference_teeth}
            
            # Mettre à jour le générateur
            self.ct_viewer.tooth_generator.reference_points = reference_points.copy()
            
            # Effacer les points générés pour forcer une régénération
            self.ct_viewer.tooth_generator.generated_points.clear()
            
            logger.info(f"🔄 ToothGenerator synchronisé avec {len(reference_points)} points de référence")
    
    
    def on_key(self, event):
        """Gestion des raccourcis clavier"""
        if not self.edit_mode:
            return
        
        logger.debug(f"Touche pressée: {event.key}")
        
        if event.key == 'r' or event.key == 'R':
            # Rotation du groupe sélectionné
            if self.selected_group:
                self._rotate_selected_group()
            else:
                logger.info("Aucun groupe sélectionné pour rotation")
        
        elif event.key == 'delete' or event.key == 'Delete':
            # Supprimer la sélection
            if self.selected_group:
                self._delete_selected_group()
            elif self.selected:
                self._remove_point(self.selected)
        
        elif event.key == 'escape' or event.key == 'Escape':
            # Désélectionner tout
            self.selected_group.clear()
            self.selected = None
            self.rect_mode = False
            if self.rect_patch:
                self.rect_patch.remove()
                self.rect_patch = None
            self.draw_all_points()
            logger.info("Tout désélectionné")
    
    def _handle_edit_click(self, x_mm, y_mm, slice_index, button, event):
        """Gère les clics en mode édition - VERSION AVEC CTRL"""
        # Vérifier si Ctrl est pressé
        ctrl_pressed = bool(event.guiEvent.state & 0x4) if hasattr(event, 'guiEvent') else False
        
        if button == 3:  # Clic droit
            if ctrl_pressed:
                # Ctrl + clic droit = supprimer un point
                clicked_point = self._find_closest_point(x_mm, y_mm, slice_index)
                if clicked_point:
                    self._remove_point(clicked_point)
                    return
            else:
                # Clic droit simple = démarrer sélection rectangulaire
                self._start_rectangle_selection(x_mm, y_mm)
                self.is_right_dragging = True
                return
                
        elif button == 1:  # Clic gauche
            # PRIORITÉ 1 : Si on doit replacer un point supprimé ET qu'on fait Ctrl+clic
            if ctrl_pressed and self.next_point_to_place:
                # Replacer le point supprimé
                tooth_name = self.next_point_to_place
                self.points[tooth_name] = (x_mm, y_mm, slice_index)
                self._draw_point(tooth_name, x_mm, y_mm)
                self.next_point_to_place = None
                logger.info(f"Point {tooth_name} replacé")
                
                # Mettre à jour l'état des boutons
                if hasattr(self.ct_viewer, 'tooth_panel') and hasattr(self.ct_viewer.tooth_panel, 'update_button_states'):
                    self.ct_viewer.tooth_panel.update_button_states()
                return
            
            # PRIORITÉ 2 : Vérifier si on clique sur un point existant (sans Ctrl)
            clicked_point = self._find_closest_point(x_mm, y_mm, slice_index, threshold=15)
            
            if clicked_point and not ctrl_pressed:
                # Clic gauche simple sur un point = sélectionner/déplacer
                self.selected = clicked_point
                self.drag_start = (x_mm, y_mm)
                
                # Gestion intelligente de la sélection
                if clicked_point in self.selected_group:
                    # Point déjà sélectionné - préparer le déplacement du groupe
                    logger.debug(f"Déplacement du groupe incluant {clicked_point}")
                else:
                    # Nouveau point - sélection unique
                    self.selected_group = {clicked_point}
                    self.draw_all_points()
                
                logger.debug(f"Point {clicked_point} sélectionné pour déplacement")
                
            elif ctrl_pressed and not clicked_point:
                # PRIORITÉ 3 : Ctrl + clic gauche dans le vide = placer un nouveau point
                self._place_new_reference_point(x_mm, y_mm, slice_index)
                
                # Mettre à jour l'état des boutons
                if hasattr(self.ct_viewer, 'tooth_panel') and hasattr(self.ct_viewer.tooth_panel, 'update_button_states'):
                    self.ct_viewer.tooth_panel.update_button_states()
    
    def _place_new_reference_point(self, x_mm, y_mm, slice_index):
        """Place un nouveau point de référence en mode édition"""
        # Trouver le prochain point de référence manquant
        placed_teeth = set(self.points.keys())
        missing_teeth = [t for t in self.reference_teeth if t not in placed_teeth]
        
        if missing_teeth:
            tooth_name = missing_teeth[0]
            self.points[tooth_name] = (x_mm, y_mm, slice_index)
            self._draw_point(tooth_name, x_mm, y_mm)
            logger.info(f"Point de référence {tooth_name} placé en mode édition")
            
            # Mettre à jour l'état des boutons
            if hasattr(self.ct_viewer, 'tooth_panel') and hasattr(self.ct_viewer.tooth_panel, 'update_button_states'):
                self.ct_viewer.tooth_panel.update_button_states()
        else:
            logger.info("Tous les points de référence sont déjà placés")
    
    def _start_rectangle_selection(self, x_mm, y_mm):
        """Démarre la sélection rectangulaire"""
        self.rect_start = (x_mm, y_mm)
        if self.rect_patch:
            self.rect_patch.remove()
        self.rect_patch = Rectangle((x_mm, y_mm), 0, 0, 
                                  linewidth=2, edgecolor='blue', 
                                  facecolor='lightblue', alpha=0.3)
        self.ax.add_patch(self.rect_patch)
        self.canvas.draw_idle()
        logger.debug(f"Sélection rectangulaire démarrée à ({x_mm:.1f}, {y_mm:.1f})")
    
    def _update_selection_rectangle(self, x_mm, y_mm):
        """Met à jour le rectangle de sélection"""
        if not self.rect_start or not self.rect_patch:
            return
            
        x0, y0 = self.rect_start
        width = x_mm - x0
        height = y_mm - y0
        
        self.rect_patch.set_width(width)
        self.rect_patch.set_height(height)
        self.canvas.draw_idle()
    
    def _finalize_rectangle_selection(self):
        """Finalise la sélection rectangulaire"""
        if not self.rect_start:
            return
        
        # Calculer les limites du rectangle
        x0, y0 = self.rect_start
        x1, y1 = self.rect_patch.get_x() + self.rect_patch.get_width(), \
                 self.rect_patch.get_y() + self.rect_patch.get_height()
        
        xmin, xmax = sorted([x0, x1])
        ymin, ymax = sorted([y0, y1])
        
        # Sélectionner tous les points dans le rectangle
        slice_index = self.get_current_slice_index()
        selected_points = set()
        
        for name, (x, y, z) in self.points.items():
            if z == slice_index and xmin <= x <= xmax and ymin <= y <= ymax:
                selected_points.add(name)
        
        if selected_points:
            self.selected_group = selected_points
            logger.info(f"Sélection rectangulaire: {len(selected_points)} points - {', '.join(sorted(selected_points))}")
        else:
            self.selected_group.clear()
            logger.info("Sélection rectangulaire: aucun point sélectionné")
        
        # Nettoyer le rectangle
        if self.rect_patch:
            self.rect_patch.remove()
            self.rect_patch = None
        self.rect_start = None
        
        # Redessiner avec la nouvelle sélection
        self.draw_all_points()
    
    def _rotate_selected_group(self):
        """Effectue une rotation du groupe sélectionné"""
        if len(self.selected_group) < 2:
            logger.info("Il faut au moins 2 points pour une rotation")
            return
        
        # Demander l'angle de rotation
        
        try:
            angle_deg = simpledialog.askfloat(
                "Rotation", 
                "Angle de rotation (degrés):", 
                initialvalue=10.0,
                minvalue=-180.0,
                maxvalue=180.0
            )
            if angle_deg is None:
                return
                
            angle_rad = np.radians(angle_deg)
            
            # Calculer le centre du groupe
            xs = [self.points[name][0] for name in self.selected_group]
            ys = [self.points[name][1] for name in self.selected_group]
            center_x = np.mean(xs)
            center_y = np.mean(ys)
            
            # Appliquer la rotation
            cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
            for name in self.selected_group:
                x, y, z = self.points[name]
                
                # Translation vers l'origine
                x_rel = x - center_x
                y_rel = y - center_y
                
                # Rotation
                x_new = x_rel * cos_a - y_rel * sin_a
                y_new = x_rel * sin_a + y_rel * cos_a
                
                # Translation retour
                self.points[name] = (center_x + x_new, center_y + y_new, z)
            
            self.draw_all_points()
            logger.info(f"Rotation de {angle_deg}° appliquée à {len(self.selected_group)} points")
            
        except Exception as e:
            logger.error(f"Erreur lors de la rotation: {e}")
    
    def _delete_selected_group(self):
        """Supprime tous les points du groupe sélectionné"""
        if not self.selected_group:
            return
        
        deleted_points = list(self.selected_group)
        
        for name in deleted_points:
            if name in self.points:
                del self.points[name]
            if name in self.labels:
                pt, lbl = self.labels[name]
                pt.remove()
                lbl.remove()
                del self.labels[name]
        
        self.selected_group.clear()
        self.canvas.draw_idle()
        
        logger.info(f"Supprimé {len(deleted_points)} points: {', '.join(deleted_points)}")
        
        # AJOUT: Synchroniser avec le tooth_generator
        self._notify_tooth_generator_update()
        
        # Mettre à jour l'état des boutons
        if hasattr(self.ct_viewer, 'tooth_panel') and hasattr(self.ct_viewer.tooth_panel, 'update_button_states'):
            self.ct_viewer.tooth_panel.update_button_states()
            
    
    def _handle_drag_end(self, x_mm, y_mm, slice_index):
        """Termine le déplacement d'un point ou groupe"""
        if not self.selected or not self.drag_start:
            return
        
        dx = x_mm - self.drag_start[0]
        dy = y_mm - self.drag_start[1]
        
        if abs(dx) < 1 and abs(dy) < 1:  # Mouvement trop petit
            self.selected = None
            self.drag_start = None
            return
        
        # Déplacer le point ou le groupe sélectionné
        points_to_move = self.selected_group if self.selected_group else {self.selected}
        
        for tooth_name in points_to_move:
            if tooth_name in self.points:
                old_x, old_y, _ = self.points[tooth_name]
                new_x = old_x + dx
                new_y = old_y + dy
                self.points[tooth_name] = (new_x, new_y, slice_index)
                
                logger.debug(f"Déplacé {tooth_name}: Δ({dx:.1f}, {dy:.1f})")
        
        # Redessiner
        self.draw_all_points()
        
        # AJOUT: Synchroniser avec le tooth_generator
        self._notify_tooth_generator_update()
        
        # Reset
        self.selected = None
        self.drag_start = None
    
    
    def _handle_placement_click(self, x_mm, y_mm, slice_index, button, event):
        """Gère les clics en mode placement - TOUJOURS AVEC CTRL"""
        if button != 1:  # Seulement clic gauche
            return
        
        # Vérifier si Ctrl est pressé
        ctrl_pressed = bool(event.guiEvent.state & 0x4) if hasattr(event, 'guiEvent') else False
        
        # TOUJOURS exiger Ctrl pour placer un point
        if not ctrl_pressed:
            return
        
        # Déterminer quelle dent placer
        if self.next_point_to_place:
            tooth_name = self.next_point_to_place
            self.next_point_to_place = None
        else:
            # Trouver la prochaine dent à placer
            placed_teeth = set(self.points.keys())
            missing_teeth = [t for t in self.reference_teeth if t not in placed_teeth]
            
            if not missing_teeth:
                logger.info("Tous les points de référence sont placés")
                return
                
            tooth_name = missing_teeth[0]
        
        # Placer le point
        self.points[tooth_name] = (x_mm, y_mm, slice_index)
        self._draw_point(tooth_name, x_mm, y_mm)
        
        logger.info(f"Point {tooth_name} placé à ({x_mm:.1f}, {y_mm:.1f}) mm, coupe {slice_index}")
        
        # Vérifier si tous les points sont placés
        if len(self.points) == len(self.reference_teeth):
            logger.info("Tous les points de référence sont placés!")
            if hasattr(self.ct_viewer, 'tooth_panel') and hasattr(self.ct_viewer.tooth_panel, 'update_button_states'):
                self.ct_viewer.tooth_panel.update_button_states()
    
    def _validate_coordinates(self, x_mm, y_mm, slice_index):
        """Valide que les coordonnées sont correctes"""
        if x_mm is None or y_mm is None:
            return False
            
        # Conversion automatique pixel -> mm si nécessaire
        try:
            ct_slice = self.ct_viewer.ct_slices[slice_index]
            ct_origin = np.array(ct_slice.ImagePositionPatient[:2], dtype=np.float32)
            ct_spacing = np.array(ct_slice.PixelSpacing, dtype=np.float32)
            
            x_extent = [ct_origin[0], ct_origin[0] + ct_slice.Columns * ct_spacing[0]]
            y_extent = [ct_origin[1], ct_origin[1] + ct_slice.Rows * ct_spacing[1]]
            
            # Vérification des limites avec tolérance
            if not (x_extent[0] - 50 <= x_mm <= x_extent[1] + 50):
                return False
            if not (y_extent[0] - 50 <= y_mm <= y_extent[1] + 50):
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Erreur validation coordonnées: {e}")
            return False
    
    def _find_closest_point(self, x_mm, y_mm, slice_index, threshold=10):
        """Trouve le point le plus proche dans un rayon donné"""
        closest_point = None
        min_distance = threshold
        
        for tooth_name, (px, py, pz) in self.points.items():
            if pz == slice_index:  # Même coupe
                distance = np.sqrt((x_mm - px)**2 + (y_mm - py)**2)
                if distance < min_distance:
                    min_distance = distance
                    closest_point = tooth_name
                    
        return closest_point
    
    def _remove_point(self, tooth_name):
        """Supprime un point et prépare son remplacement"""
        if tooth_name in self.points:
            del self.points[tooth_name]
            
        if tooth_name in self.labels:
            pt, lbl = self.labels[tooth_name]
            pt.remove()
            lbl.remove()
            del self.labels[tooth_name]
            
        # Retirer du groupe sélectionné
        if tooth_name in self.selected_group:
            self.selected_group.remove(tooth_name)
            
        self.next_point_to_place = tooth_name
        self.canvas.draw_idle()
        
        logger.info(f"Point {tooth_name} supprimé - Ctrl+Clic gauche pour le replacer")
        
        # Mettre à jour l'état des boutons
        if hasattr(self.ct_viewer, 'tooth_panel') and hasattr(self.ct_viewer.tooth_panel, 'update_button_states'):
            self.ct_viewer.tooth_panel.update_button_states()
    
    def _draw_point(self, tooth_name, x_mm, y_mm):
        """Dessine un point sur l'interface avec couleurs selon sélection"""
        # Supprimer l'ancien affichage si existant
        if tooth_name in self.labels:
            pt, lbl = self.labels[tooth_name]
            pt.remove()
            lbl.remove()
        
        # Couleurs selon l'état
        if tooth_name in self.selected_group:
            color = 'cyan'  # Points sélectionnés en cyan
            markersize = 8
        elif tooth_name == self.selected:
            color = 'yellow'  # Point en cours de déplacement en jaune
            markersize = 8
        else:
            color = 'red'  # Points normaux en rouge
            markersize = 6
        
        # Dessiner le nouveau point
        pt, = self.ax.plot([x_mm], [y_mm], 'o', color=color, markersize=markersize)
        lbl = self.ax.text(x_mm + 2, y_mm + 2, tooth_name, color=color, 
                          fontsize=10, weight='bold')
        self.labels[tooth_name] = (pt, lbl)
        self.canvas.draw_idle()
    
    def draw_all_points(self):
        """Redessine tous les points de la coupe courante"""
        current_slice = self.get_current_slice_index()
        
        # Nettoyer les anciens affichages
        for tooth_name, (pt, lbl) in list(self.labels.items()):
            pt.remove()
            lbl.remove()
        self.labels.clear()
        
        # Redessiner les points de la coupe courante
        for tooth_name, (x_mm, y_mm, z_slice) in self.points.items():
            if z_slice == current_slice:
                self._draw_point(tooth_name, x_mm, y_mm)
    
    def is_complete(self):
        """Vérifie si tous les points de référence sont placés"""
        return len(self.points) == len(self.reference_teeth)
    
    def get_missing_teeth(self):
        """Retourne la liste des dents manquantes"""
        placed = set(self.points.keys())
        return [t for t in self.reference_teeth if t not in placed]
    
    def get_completion_status(self):
        """Retourne le statut de complétude avec informations de sélection"""
        placed_count = len(self.points)
        total_count = len(self.reference_teeth)
        missing = self.get_missing_teeth()
        
        status = {
            'placed': placed_count,
            'total': total_count,
            'missing': missing,
            'complete': self.is_complete(),
            'percentage': (placed_count / total_count) * 100 if total_count > 0 else 0
        }
        
        # Informations de sélection
        if self.selected_group:
            status['selected_count'] = len(self.selected_group)
            status['selected_points'] = sorted(list(self.selected_group))
        else:
            status['selected_count'] = 0
            status['selected_points'] = []
        
        return status
    
    def clear_all_points(self):
        """Supprime tous les points"""
        # Supprimer les affichages
        for tooth_name, (pt, lbl) in list(self.labels.items()):
            pt.remove()
            lbl.remove()
        
        self.points.clear()
        self.labels.clear()
        self.selected_group.clear()
        self.next_point_to_place = None
        self.current_tooth_index = 0
        self.selected = None
        
        # Nettoyer le rectangle de sélection
        if self.rect_patch:
            self.rect_patch.remove()
            self.rect_patch = None
        self.rect_start = None
        self.rect_mode = False
        self.is_right_dragging = False
        
        self.canvas.draw_idle()
        logger.info("Tous les points supprimés")
        
        # Mettre à jour l'état des boutons
        if hasattr(self.ct_viewer, 'tooth_panel') and hasattr(self.ct_viewer.tooth_panel, 'update_button_states'):
            self.ct_viewer.tooth_panel.update_button_states()
    
    def export_points_to_dict(self):
        """Exporte tous les points vers un dictionnaire"""
        return self.points.copy()
    
    def import_points_from_dict(self, points_dict):
        """Importe des points depuis un dictionnaire"""
        try:
            # Valider les points
            for name, (x, y, z) in points_dict.items():
                if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                    raise ValueError(f"Coordonnées invalides pour {name}")
                if not isinstance(z, int) or z < 0:
                    raise ValueError(f"Index de coupe invalide pour {name}")
            
            # Importer les points
            self.points = points_dict.copy()
            logger.info(f"Importé {len(self.points)} points de référence")
            
            # Redessiner
            self.draw_all_points()
            
            # Mettre à jour l'état des boutons
            if hasattr(self.ct_viewer, 'tooth_panel') and hasattr(self.ct_viewer.tooth_panel, 'update_button_states'):
                self.ct_viewer.tooth_panel.update_button_states()
                
        except Exception as e:
            logger.error(f"Erreur import points: {e}")
    
    def validate_points(self):
        """Valide la cohérence des points placés"""
        issues = []
        
        # Vérifier que tous les points de référence sont présents
        missing = self.get_missing_teeth()
        if missing:
            issues.append(f"Points de référence manquants: {', '.join(missing)}")
        
        # Vérifier la cohérence anatomique
        for tooth_name, (x_mm, y_mm, z_slice) in self.points.items():
            # Vérifier les limites de coupe
            if z_slice < 0 or z_slice >= len(self.ct_viewer.ct_slices):
                issues.append(f"Point {tooth_name} sur coupe invalide: {z_slice}")
            
            # Vérifier la position relative des arcades
            if tooth_name.startswith(('1', '2')):  # Maxillaire
                # Les dents maxillaires doivent être au-dessus des mandibulaires
                mandibular_points = [(n, p) for n, p in self.points.items() 
                                   if n.startswith(('3', '4'))]
                for mand_name, (mx, my, mz) in mandibular_points:
                    if abs(z_slice - mz) <= 20 and y_mm < my:  # Même région Z
                        issues.append(f"Position suspecte: {tooth_name} (max) semble sous {mand_name} (mand)")
        
        if issues:
            logger.warning(f"Validation points - Problèmes détectés: {'; '.join(issues)}")
        else:
            logger.info("Validation points - Tous les points semblent cohérents")
        
        return issues