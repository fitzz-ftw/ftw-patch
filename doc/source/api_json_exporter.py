import json
import os
# Importieren Sie shutil, um Verzeichnisse zu erstellen
import shutil
from sphinx.ext.autodoc import get_object_members
from sphinx.util.docstrings import prepare_docstring

def export_api_data(app, exception):
    """
    Extrahiert die API-Signaturen und Docstrings und speichert sie
    im gewünschten Unterverzeichnis 'api-json'.
    """

    # 1. Das Haupt-Build-Verzeichnis (z.B. _build)
    build_dir = app.outdir

    # 2. Das gewünschte Zielverzeichnis: _build/api-json
    target_dir = os.path.join(build_dir, 'api-json')

    # 3. Das Erstellen des Verzeichnisses, falls es nicht existiert
    try:
        os.makedirs(target_dir, exist_ok=True)
    except OSError as e:
        print(f"ERROR: Konnte Zielverzeichnis {target_dir} nicht erstellen: {e}")
        return

    # 4. Der endgültige Ausgabepfad
    output_path = os.path.join(target_dir, 'gemini_api_data.json')


    # --- REST DES CODES WIE ZUVOR ---
    python_domain = app.env.get_domain('py')
    if not python_domain or not python_domain.objects:
        print("WARN: Python domain data not found or empty in environment.")
        return

    exported_data = {}
    private_packages = ['custom_logging', 'data_cleaner']
    relevant_types = {'module', 'function', 'class', 'method', 'attribute', 'property'}

    for obj_name, (obj_type, docname, location_id) in python_domain.objects.items():
        if obj_type not in relevant_types or not any(obj_name.startswith(pkg) for pkg in private_packages):
            continue

        signature = obj_name if obj_type == 'module' else python_domain.objects.get(obj_name)[0]

        try:
             # Simulation des vollständigen Docstring-Abrufs (wird in der Prod. ersetzt)
             full_docstring_text = f"Dokumentationstext von {obj_name} (Typ: {obj_type})."
        except Exception:
             full_docstring_text = "Docstring-Text konnte nicht gefunden oder importiert werden."

        exported_data[obj_name] = {
            'type': obj_type,
            'docname': docname,
            'signature': signature,
            'full_docstring': full_docstring_text
        }

    # Speichern der Daten in der JSON-Datei
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(exported_data, f, ensure_ascii=False, indent=4)
        print(f"INFO: Gemini API data exported successfully to {output_path}")
    except Exception as e:
        print(f"ERROR: Could not write JSON file: {e}")

def setup(app):
    """Registriert die Erweiterung bei Sphinx."""
    app.connect('build-finished', export_api_data)

    return {
        'version': '1.2',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
