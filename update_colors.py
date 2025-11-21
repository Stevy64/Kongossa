#!/usr/bin/env python3
"""
Script pour mettre à jour automatiquement les couleurs dans les templates
Remplace les couleurs purple/pink/orange par la nouvelle palette premium
"""
import re
import os
from pathlib import Path

# Dossier des templates (exclure chat/messagerie)
TEMPLATES_DIR = Path("templates")
EXCLUDE_DIRS = {"chat"}  # Exclure la messagerie

# Mappings de remplacement
REPLACEMENTS = [
    # Gradients
    (r'bg-gradient-to-r from-purple-600 to-pink-600', 'bg-gradient-gold'),
    (r'bg-gradient-to-r from-purple-600 via-pink-600 to-orange-500', 'bg-gradient-gold'),
    (r'bg-gradient-to-br from-purple-500 via-pink-500 to-orange-500', 'bg-gradient-gold'),
    (r'bg-gradient-to-r from-purple-500 to-pink-500', 'bg-gradient-gold'),
    (r'bg-gradient-to-br from-purple-500 to-pink-500', 'bg-gradient-gold'),
    
    # Text colors
    (r'text-purple-300', 'text-gold'),
    (r'text-purple-400', 'text-gold'),
    (r'text-purple-600', 'text-gold'),
    (r'text-purple-700', 'text-gold'),
    (r'hover:text-purple-300', 'hover:text-gold'),
    (r'hover:text-purple-400', 'hover:text-gold'),
    (r'hover:text-purple-700', 'hover:text-gold'),
    (r'text-pink-400', 'text-gold'),
    (r'hover:text-pink-400', 'hover:text-gold'),
    
    # Focus rings
    (r'focus:ring-purple-500', 'focus:ring-gold'),
    
    # Shadows
    (r'shadow-purple-500/50', 'shadow-gold'),
    
    # Borders
    (r'border-purple-500', 'border-gold'),
    (r'border-l-4 border-purple-500', 'border-l-4 border-gold'),
]

def should_process_file(file_path):
    """Vérifier si le fichier doit être traité"""
    parts = file_path.parts
    # Exclure les fichiers dans les dossiers chat
    if 'chat' in parts:
        return False
    return file_path.suffix == '.html'

def update_file(file_path):
    """Mettre à jour un fichier avec les nouveaux remplacements"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Appliquer les remplacements
        for pattern, replacement in REPLACEMENTS:
            content = re.sub(pattern, replacement, content)
        
        # Remplacements spéciaux pour les boutons avec text-white
        # Remplacer les boutons avec gradient purple/pink qui ont text-white par text-brand-primary
        content = re.sub(
            r'(bg-gradient-gold)\s+text-white',
            r'\1 text-brand-primary font-bold',
            content
        )
        
        # Si le contenu a changé, sauvegarder
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Mis à jour: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"✗ Erreur avec {file_path}: {e}")
        return False

def main():
    """Fonction principale"""
    updated_count = 0
    
    for html_file in TEMPLATES_DIR.rglob("*.html"):
        if should_process_file(html_file):
            if update_file(html_file):
                updated_count += 1
    
    print(f"\n✓ {updated_count} fichiers mis à jour")

if __name__ == "__main__":
    main()

