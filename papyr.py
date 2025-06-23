#!/usr/bin/env python3
import os
import argparse
import PyPDF2
from openai import OpenAI
import json
from datetime import datetime
import sys

# --- Konfiguration ---
OPENAI_MODEL = "gpt-4o"
PAGES_TO_READ = 3

# --- Initialisierung des OpenAI-Clients ---
try:
    client = OpenAI()
except Exception:
    print("Fehler: OpenAI API-Schlüssel nicht gefunden.")
    print("Bitte stellen Sie sicher, dass die Umgebungsvariable 'OPENAI_API_KEY' gesetzt ist.")
    sys.exit(1)

def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            if reader.is_encrypted:
                print(f"Hinweis: '{os.path.basename(pdf_path)}' ist verschlüsselt und kann nicht gelesen werden.")
                return ""
            
            text = ""
            num_pages = len(reader.pages)
            pages_to_process = min(num_pages, PAGES_TO_READ)
            
            for i in range(pages_to_process):
                page = reader.pages[i]
                text += page.extract_text() or ""
            return text
    except Exception as e:
        print(f"Fehler beim Lesen der PDF-Datei '{os.path.basename(pdf_path)}': {e}")
        return ""

def get_new_filename_from_ai(text: str) -> dict:
    if not text.strip():
        return None

    prompt = f"""
    Analysiere den folgenden Text aus einer PDF-Datei und gib die Informationen im JSON-Format zurück:
    1. "topic": Ein allgemeines Schlagwort in Grossbuchstaben (z.B. RECHNUNG, VERTRAG, STUDIE, MARKETING, BEWERBUNG).
    2. "subject": Eine kurze, spezifische Beschreibung des Inhalts in 2-4 Wörtern, getrennt durch Unterstriche (z.B. Stromabrechnung_Juni, Mietvertrag_Wohnung_Mueller, Analyse_Quartal_2, Social_Media_Plan).
    3. "year": Das im Dokument genannte Jahr als vierstellige Zahl. Falls nicht vorhanden, nutze das aktuelle Jahr ({datetime.now().year}).
    4. "month": Der im Dokument genannte Monat als zweistellige Zahl (01-12). Falls nicht vorhanden, nutze den aktuellen Monat ({datetime.now().strftime('%m')}).
    
    Antworte ausschließlich mit einem validen JSON-Objekt. Gib keinen zusätzlichen Text aus.
    Textauszug:
    ---
    {text[:8000]}
    ---
    """

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Du bist ein präziser Assistent, der Dokumente analysiert und strukturierte Dateinamen im JSON-Format vorschlägt."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"-> Fehler bei der Anfrage an die OpenAI-API: {e}")
        return None

def rename_pdf_file(file_path: str):
    print(f"Analysiere: {file_path}")

    text = extract_text_from_pdf(file_path)
    if not text:
        print("-> Konnte keinen Text extrahieren. Überspringe Datei.")
        return

    name_parts = get_new_filename_from_ai(text)
    if not name_parts:
        print("-> KI konnte keinen Dateinamen generieren. Überspringe Datei.")
        return

    try:
        topic = name_parts.get('topic', 'UNBEKANNT').upper()
        subject = name_parts.get('subject', 'unbekannt').replace(" ", "_")
        year = name_parts.get('year', str(datetime.now().year))
        month = name_parts.get('month', datetime.now().strftime('%m'))

        new_name = f"{topic}_{subject}_{year}_{month}.pdf"
        new_name = "".join(c for c in new_name if c.isalnum() or c in ('_', '-', '.'))

        directory = os.path.dirname(file_path)
        new_file_path = os.path.join(directory, new_name)

        if file_path == new_file_path:
            print(f"-> Dateiname '{new_name}' ist bereits korrekt.")
            return

        if os.path.exists(new_file_path):
            i = 1
            base, ext = os.path.splitext(new_name)
            while os.path.exists(new_file_path):
                new_name = f"{base}_{i}{ext}"
                new_file_path = os.path.join(directory, new_name)
                i += 1
            print(f"-> Warnung: Zieldatei existierte bereits. Benenne stattdessen in '{new_name}' um.")

        os.rename(file_path, new_file_path)
        print(f"✅ Umbenannt zu: '{new_name}'")

    except Exception as e:
        print(f"-> Fehler beim Verarbeiten der KI-Antwort: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Benennt PDFs intelligent mit KI um.",
        prog="namify",
        epilog="Beispiele:\n"
               "  namify mydocument.pdf\n"
               "  namify .\n"
               "  namify ~/Downloads\n"
               "  namify -r ~/Dokumente",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'path', 
        metavar='PFAD', 
        type=str, 
        help="Pfad zu einer PDF-Datei oder einem Ordner. Verwenden Sie '.' für den aktuellen Ordner."
    )
    parser.add_argument(
        '-r', '--recursive', 
        action='store_true', 
        help="Durchsucht Ordner rekursiv nach PDF-Dateien."
    )
    args = parser.parse_args()

    target_path = os.path.expanduser(args.path)
    pdf_files_to_process = []

    if not os.path.exists(target_path):
        print(f"Fehler: Der Pfad '{target_path}' existiert nicht.")
        sys.exit(1)

    if os.path.isfile(target_path):
        if target_path.lower().endswith('.pdf'):
            pdf_files_to_process.append(target_path)
        else:
            print("Fehler: Die angegebene Datei ist keine PDF-Datei.")
            sys.exit(1)
            
    elif os.path.isdir(target_path):
        if args.recursive:
            print(f"Suche rekursiv nach PDFs in '{target_path}'...")
            for root, _, files in os.walk(target_path):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_files_to_process.append(os.path.join(root, file))
        else:
            print(f"Suche nach PDFs in '{target_path}'...")
            for item in os.listdir(target_path):
                full_path = os.path.join(target_path, item)
                if os.path.isfile(full_path) and item.lower().endswith('.pdf'):
                    pdf_files_to_process.append(full_path)

    if not pdf_files_to_process:
        print("Keine PDF-Dateien zum Verarbeiten gefunden.")
        return

    print(f"\n{len(pdf_files_to_process)} PDF-Datei(en) gefunden. Start der Verarbeitung.")
    print("-" * 40)
    
    for file_path in pdf_files_to_process:
        rename_pdf_file(file_path)
        print("-" * 20)
    
    print("Verarbeitung abgeschlossen.")

if __name__ == '__main__':
    main()
