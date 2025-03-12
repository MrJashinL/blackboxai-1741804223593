import json
import os
from settings import *

class SurvivorClass:
    def __init__(self, name, base_stats):
        self.name = name
        self.base_stats = base_stats
        self.level = 1
        self.experience = 0
        self.exp_to_next_level = 100
        
    def to_dict(self):
        return {
            'name': self.name,
            'base_stats': self.base_stats,
            'level': self.level,
            'experience': self.experience,
            'exp_to_next_level': self.exp_to_next_level
        }
        
    @classmethod
    def from_dict(cls, data):
        survivor = cls(data['name'], data['base_stats'])
        survivor.level = data['level']
        survivor.experience = data['experience']
        survivor.exp_to_next_level = data['exp_to_next_level']
        return survivor

class SurvivorManager:
    def __init__(self):
        self.classes = {
            'Scout': {
                'health': 80,
                'speed': 1.2,
                'stamina': 120,
                'stealth': 1.3,
                'strength': 0.8,
                'description': 'Veloce e furtivo, ideale per l\'esplorazione'
            },
            'Fighter': {
                'health': 120,
                'speed': 0.9,
                'stamina': 100,
                'stealth': 0.7,
                'strength': 1.3,
                'description': 'Forte e resistente, migliore nel combattimento'
            },
            'Survivor': {
                'health': 100,
                'speed': 1.0,
                'stamina': 100,
                'stealth': 1.0,
                'strength': 1.0,
                'description': 'Bilanciato in tutte le statistiche'
            },
            'Ghost': {
                'health': 70,
                'speed': 1.1,
                'stamina': 90,
                'stealth': 1.5,
                'strength': 0.7,
                'description': 'Massima furtività, ideale per evitare i nemici'
            },
            'Tank': {
                'health': 150,
                'speed': 0.8,
                'stamina': 80,
                'stealth': 0.6,
                'strength': 1.4,
                'description': 'Massima resistenza, lento ma molto forte'
            }
        }
        
        self.selected_class = None
        self.progress_file = 'survivor_progress.json'
        self.load_progress()

    def get_class_stats(self, class_name):
        """Ottieni le statistiche base di una classe"""
        return self.classes.get(class_name, None)

    def create_survivor(self, class_name):
        """Crea un nuovo sopravvissuto della classe specificata"""
        if class_name in self.classes:
            self.selected_class = SurvivorClass(class_name, self.classes[class_name])
            self.save_progress()
            return self.selected_class
        return None

    def add_experience(self, amount):
        """Aggiungi esperienza e gestisci il level up"""
        if self.selected_class:
            self.selected_class.experience += amount
            while self.selected_class.experience >= self.selected_class.exp_to_next_level:
                self.level_up()
            self.save_progress()

    def level_up(self):
        """Gestisce il level up e l'incremento delle statistiche"""
        if self.selected_class:
            self.selected_class.experience -= self.selected_class.exp_to_next_level
            self.selected_class.level += 1
            self.selected_class.exp_to_next_level = int(self.selected_class.exp_to_next_level * 1.5)
            
            # Incrementa le statistiche base
            for stat in self.selected_class.base_stats:
                if stat not in ['description']:
                    self.selected_class.base_stats[stat] *= 1.1

    def get_current_stats(self):
        """Ottieni le statistiche attuali considerando il livello"""
        if not self.selected_class:
            return None
            
        current_stats = self.selected_class.base_stats.copy()
        return current_stats

    def save_progress(self):
        """Salva i progressi del sopravvissuto"""
        if self.selected_class:
            data = self.selected_class.to_dict()
            try:
                with open(self.progress_file, 'w') as f:
                    json.dump(data, f)
            except Exception as e:
                print(f"Errore nel salvataggio dei progressi: {e}")

    def load_progress(self):
        """Carica i progressi salvati"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    self.selected_class = SurvivorClass.from_dict(data)
        except Exception as e:
            print(f"Errore nel caricamento dei progressi: {e}")

    def get_experience_rewards(self, action_type):
        """Restituisce la quantità di esperienza per diverse azioni"""
        rewards = {
            'exploration': 10,  # Per area esplorata
            'combat': 25,      # Per nemico evitato/sconfitto
            'extraction': 100   # Per estrazione completata
        }
        return rewards.get(action_type, 0)
