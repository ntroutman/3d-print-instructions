"""Main module for generating assembly instructions from image folders."""

import os
import sys
from pathlib import Path
from typing import List, Dict
from instructions_writer.gemini import GeminiClient


class InstructionGenerator:
    def __init__(self):
        self.gemini = GeminiClient()
    
    def parse_folder_structure(self, folder_path: str) -> Dict:
        """Parse folder structure to extract project title and sections."""
        path = Path(folder_path)
        project_title = path.name
        
        sections = []
        root_steps = []
        
        # Check for images in root directory
        for image_file in sorted(path.iterdir()):
            if image_file.is_file() and image_file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                root_steps.append({
                    'filename': image_file.name,
                    'path': str(image_file)
                })
        
        # Check for numbered section directories
        for section_dir in sorted(path.iterdir()):
            if section_dir.is_dir() and section_dir.name[0].isdigit():
                section_name = section_dir.name
                steps = []
                
                for image_file in sorted(section_dir.iterdir()):
                    if image_file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                        steps.append({
                            'filename': image_file.name,
                            'path': str(image_file)
                        })
                
                sections.append({
                    'name': section_name,
                    'steps': steps
                })
        
        # If no sections but root images exist, create a single section
        if not sections and root_steps:
            sections.append({
                'name': 'Instructions',
                'steps': root_steps
            })
        
        return {
            'title': project_title,
            'sections': sections
        }
    
    def generate_instructions(self, folder_path: str, dry_run: bool) -> str:
        """Generate markdown instructions for the given folder."""
        structure = self.parse_folder_structure(folder_path)
        
        prompt = f"""Generate assembly instructions in markdown format for a project called "{structure['title']}".

The project has the following sections and steps:
"""
        
        for section in structure['sections']:
            prompt += f"\n## {section['name']}\n"
            for step in section['steps']:
                prompt += f"- {step['filename']}\n"
        
        prompt += """
Create detailed assembly instructions with:
1. A main title
2. Section headers for each major assembly step
3. Numbered steps within each section
4. Reference the image file names exactly using markdown image syntax
5. Write clear, concise instructions for each step

Format as proper markdown with headers, numbered lists, and image references.
"""
        if dry_run:
            print(prompt)
            sys.exit(0)
            
        markdown = self.gemini.generate(prompt)
        fixed_markdown = self._fix_image_paths(markdown, structure)
        return self._add_jekyll_front_matter(fixed_markdown, structure['title'])
    
    def _fix_image_paths(self, markdown: str, structure: Dict) -> str:
        """Fix image paths to include section folders."""
        for section in structure['sections']:
            section_folder = section['name']
            for step in section['steps']:
                filename = step['filename']
                # For root-level images (Instructions section), don't add folder prefix
                if section_folder == 'Instructions':
                    markdown = markdown.replace(f"({filename})", f"(<{filename}>)")
                else:
                    # Replace bare filename with section/filename path
                    markdown = markdown.replace(f"({filename})", f"(<{section_folder}/{filename}>)")
        return markdown
    
    def _add_jekyll_front_matter(self, markdown: str, title: str) -> str:
        """Add Jekyll front matter to the markdown content."""
        front_matter = f"""---
layout: default
title: {title}
---

"""
        return front_matter + markdown


def main():
    """Entry point for the CLI application."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate assembly instructions from image folders")
    parser.add_argument("folder_path", help="Path to instruction images folder")
    parser.add_argument("--dry-run", action="store_true", help="Print prompt without generating instructions")
    
    args = parser.parse_args()
    
    generator = InstructionGenerator()
    instructions = generator.generate_instructions(args.folder_path, args.dry_run)
    
    if not args.dry_run:
        # Write to file
        output_file = "instructions.md"
        with open(os.path.join(args.folder_path, output_file), 'w') as f:
            f.write(instructions)

        print(f"Instructions written to {os.path.join(args.folder_path, output_file)}")
        print(instructions)


if __name__ == "__main__":
    main()
