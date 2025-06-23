#!/usr/bin/env python3
import os
import argparse
import PyPDF2
from openai import OpenAI
import json
from datetime import datetime
import sys
from tqdm import tqdm

# --- Configuration ---
OPENAI_MODEL = "gpt-4o"
PAGES_TO_READ = 3

# --- Language Texts ---
LANGUAGES = {
    "en": {
        "error_api_key_not_found": """
Error: OpenAI API key not found.
'papyr' requires an OpenAI API key to function.

Please set the OPENAI_API_KEY environment variable.
For the current session, you can use:
  export OPENAI_API_KEY='your_api_key_here'

For permanent use, add this line to your shell configuration file (e.g., ~/.zshrc).
""",
        "app_description": "Intelligently renames PDF files using AI.",
        "app_epilog": "Examples:\n  papyr mydocument.pdf\n  papyr .\n  papyr ~/Downloads\n  papyr -r ~/Documents",
        "arg_path_help": "Path to a PDF file or a directory. Use '.' for the current directory.",
        "arg_recursive_help": "Recursively search directories for PDF files.",
        "arg_lang_help": "Set the output language (en/de).",
        "error_path_not_exist": "Error: Path '{path}' does not exist.",
        "error_not_pdf": "Error: The specified file is not a PDF.",
        "searching_recursive": "Recursively searching for PDFs in '{path}'...",
        "searching_folder": "Searching for PDFs in '{path}'...",
        "no_files_found": "No PDF files found to process.",
        "files_found": "Found {count} PDF file(s). Starting process.",
        "processing_desc": "Processing PDFs",
        "processing_unit": "file",
        "processing_complete": "✅ Processing complete.",
        "summary_renamed": "{renamed_count} of {total_count} file(s) renamed successfully.",
        "notice_encrypted": "Notice: '{filename}' is encrypted and cannot be read.",
        "error_reading_pdf": "Error reading PDF file '{filename}': {error}",
        "error_openai_request": "-> Error with OpenAI API request: {error}",
        "info_already_correct": "-> Filename '{filename}' is already correct.",
        "warning_already_exists": "-> Warning: Target file '{target}' already existed. Renaming to '{new_name}' instead.",
        "success_renamed": "✅ {original_name} -> '{new_name}'",
        "error_processing_ai": "-> Error processing AI response for '{filename}': {error}",
        "ai_prompt": """
    Analyze the following text from a PDF file and return the information in JSON format:
    1. "topic": A general keyword in uppercase (e.g., INVOICE, CONTRACT, APPLICATION).
    2. "subject": The full first and last name of the person OR the name of the company the document refers to. Format as 'FirstName_LastName' or 'CompanyName'. If neither applies, provide a brief content description (e.g., 'Rental_Agreement_Apartment').
    3. "title": A short, specific title for the document itself (e.g., 'Cover_Letter_Job_XYZ', 'Resume', 'Invoice_Mobile' or 'Payslip_May'). Replace spaces with hyphens.
    4. "year": The year mentioned in the document as a four-digit number. If not found, use the current year ({current_year}).
    5. "month": The month mentioned in the document as a two-digit number (01-12). If not found, use the current month ({current_month}).
    Respond exclusively with a valid JSON object.
    Text excerpt:
    ---
    {text}
    ---
    """
    },
    "de": {
        "error_api_key_not_found": """
Fehler: OpenAI API-Schlüssel nicht gefunden.
'papyr' benötigt einen OpenAI API-Schlüssel, um zu funktionieren.

Bitte setzen Sie die Umgebungsvariable OPENAI_API_KEY.
Für die aktuelle Sitzung können Sie folgenden Befehl verwenden:
  export OPENAI_API_KEY='Ihr_API_Schlüssel_hier'

Für die dauerhafte Nutzung fügen Sie diese Zeile zu Ihrer Shell-Konfigurationsdatei hinzu (z.B. ~/.zshrc).
""",
        "app_description": "Benennt PDFs intelligent mit KI um.",
        "app_epilog": "Beispiele:\n  papyr mydocument.pdf\n  papyr .\n  papyr ~/Downloads\n  papyr -r ~/Dokumente",
        "arg_path_help": "Pfad zu einer PDF-Datei oder einem Ordner. Verwenden Sie '.' für den aktuellen Ordner.",
        "arg_recursive_help": "Durchsucht Ordner rekursiv nach PDF-Dateien.",
        "arg_lang_help": "Legt die Ausgabesprache fest (en/de).",
        "error_path_not_exist": "Fehler: Der Pfad '{path}' existiert nicht.",
        "error_not_pdf": "Fehler: Die angegebene Datei ist keine PDF-Datei.",
        "searching_recursive": "Suche rekursiv nach PDFs in '{path}'...",
        "searching_folder": "Suche nach PDFs in '{path}'...",
        "no_files_found": "Keine PDF-Dateien zum Verarbeiten gefunden.",
        "files_found": "{count} PDF-Datei(en) gefunden. Start der Verarbeitung.",
        "processing_desc": "Verarbeite PDFs",
        "processing_unit": "Datei",
        "processing_complete": "✅ Verarbeitung abgeschlossen.",
        "summary_renamed": "{renamed_count} von {total_count} Datei(en) erfolgreich umbenannt.",
        "notice_encrypted": "Hinweis: '{filename}' ist verschlüsselt und kann nicht gelesen werden.",
        "error_reading_pdf": "Fehler beim Lesen der PDF-Datei '{filename}': {error}",
        "error_openai_request": "-> Fehler bei der Anfrage an die OpenAI-API: {error}",
        "info_already_correct": "-> Dateiname '{filename}' ist bereits korrekt.",
        "warning_already_exists": "-> Warnung: Zieldatei '{target}' existierte bereits. Benenne stattdessen in '{new_name}' um.",
        "success_renamed": "✅ {original_name} -> '{new_name}'",
        "error_processing_ai": "-> Fehler beim Verarbeiten der KI-Antwort für '{filename}': {error}",
        "ai_prompt": """
    Analysiere den folgenden Text aus einer PDF-Datei und gib die Informationen im JSON-Format zurück:
    1. "topic": Ein allgemeines Schlagwort in Grossbuchstaben (z.B. RECHNUNG, VERTRAG, BEWERBUNG).
    2. "subject": Der vollständige Vor- und Nachname der Person ODER der Name der Firma, auf die sich das Dokument bezieht. Formatiere als 'Vorname_Nachname' oder 'Firmenname'. Falls beides nicht zutrifft, gib eine kurze Inhaltsbeschreibung (z.B. 'Mietvertrag_Wohnung').
    3. "title": Ein kurzer, spezifischer Titel für das Dokument selbst (z.B. 'Anschreiben_Stelle_XYZ', 'Lebenslauf', 'Rechnung_Mobilfunk' oder 'Gehaltsabrechnung_Mai'). Ersetze Leerzeichen mit Bindestrichen.
    4. "year": Das im Dokument genannte Jahr als vierstellige Zahl. Falls nicht vorhanden, nutze das aktuelle Jahr ({current_year}).
    5. "month": Der im Dokument genannte Monat als zweistellige Zahl (01-12). Falls nicht vorhanden, nutze den aktuellen Monat ({current_month}).
    Antworte ausschließlich mit einem validen JSON-Objekt.
    Textauszug:
    ---
    {text}
    ---
    """
    }
}

def setup_api_key(i18n):
    try:
        # This line implicitly checks for the OPENAI_API_KEY environment variable.
        client = OpenAI()
        return client
    except Exception:
        # Print the helpful, multi-line error message from the language dictionary.
        print(i18n["error_api_key_not_found"].strip(), file=sys.stderr)
        sys.exit(1)

def extract_text_from_pdf(pdf_path: str, i18n: dict) -> str:
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            if reader.is_encrypted:
                tqdm.write(i18n["notice_encrypted"].format(filename=os.path.basename(pdf_path)), file=sys.stderr)
                return ""

            text = ""
            num_pages = len(reader.pages)
            pages_to_process = min(num_pages, PAGES_TO_READ)

            for i in range(pages_to_process):
                page = reader.pages[i]
                text += page.extract_text() or ""
            return text
    except Exception as e:
        tqdm.write(i18n["error_reading_pdf"].format(filename=os.path.basename(pdf_path), error=e), file=sys.stderr)
        return ""

def get_new_filename_from_ai(client: OpenAI, text: str, i18n: dict) -> dict:
    if not text.strip():
        return None

    prompt = i18n["ai_prompt"].format(
        current_year=datetime.now().year,
        current_month=datetime.now().strftime('%m'),
        text=text[:8000]
    )

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a precise assistant that analyzes documents and suggests structured filenames in JSON format."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        tqdm.write(i18n["error_openai_request"].format(error=e), file=sys.stderr)
        return None

def rename_pdf_file(client: OpenAI, file_path: str, i18n: dict) -> bool:
    text = extract_text_from_pdf(file_path, i18n)
    if not text:
        return False
    name_parts = get_new_filename_from_ai(client, text, i18n)
    if not name_parts:
        return False

    try:
        topic = name_parts.get('topic', 'UNKNOWN').upper()
        subject = name_parts.get('subject', 'unknown').replace(" ", "_")
        title = name_parts.get('title', 'untitled').replace(" ", "-")
        year = name_parts.get('year', str(datetime.now().year))
        month = name_parts.get('month', datetime.now().strftime('%m'))

        new_name = f"{topic}_{subject}_{title}_{year}-{month}.pdf"
        new_name = "".join(c for c in new_name if c.isalnum() or c in ('_', '-', '.'))

        directory = os.path.dirname(file_path)
        new_file_path = os.path.join(directory, new_name)

        original_basename = os.path.basename(file_path)
        if file_path == new_file_path:
            tqdm.write(i18n["info_already_correct"].format(filename=original_basename))
            return False

        if os.path.exists(new_file_path):
            i = 1
            base, ext = os.path.splitext(new_name)
            while os.path.exists(new_file_path):
                new_name = f"{base}_{i}{ext}"
                new_file_path = os.path.join(directory, new_name)
                i += 1
            tqdm.write(i18n["warning_already_exists"].format(target=os.path.basename(new_file_path), new_name=new_name))

        os.rename(file_path, new_file_path)
        tqdm.write(i18n["success_renamed"].format(original_name=original_basename, new_name=new_name))
        return True

    except Exception as e:
        tqdm.write(i18n["error_processing_ai"].format(filename=os.path.basename(file_path), error=e), file=sys.stderr)
        return False

def main():
    # Setup initial parser just to get the language
    lang_parser = argparse.ArgumentParser(add_help=False)
    lang_parser.add_argument('-l', '--lang', choices=['en', 'de'], default='en', help="Set the output language (en/de).")
    lang_args, _ = lang_parser.parse_known_args()

    # Select the language dictionary
    i18n = LANGUAGES[lang_args.lang]

    # Initialize OpenAI client (which checks for the API key)
    client = setup_api_key(i18n)

    # Setup the main parser with translated texts
    parser = argparse.ArgumentParser(
        description=i18n["app_description"],
        prog="papyr",
        epilog=i18n["app_epilog"],
        formatter_class=argparse.RawTextHelpFormatter,
        parents=[lang_parser] # Inherit the --lang argument
    )
    parser.add_argument('path', metavar='PATH', type=str, help=i18n["arg_path_help"])
    parser.add_argument('-r', '--recursive', action='store_true', help=i18n["arg_recursive_help"])

    args = parser.parse_args()

    target_path = os.path.expanduser(args.path)
    pdf_files_to_process = []

    if not os.path.exists(target_path):
        print(i18n["error_path_not_exist"].format(path=target_path), file=sys.stderr)
        sys.exit(1)

    if os.path.isfile(target_path):
        if target_path.lower().endswith('.pdf'):
            pdf_files_to_process.append(target_path)
        else:
            print(i18n["error_not_pdf"], file=sys.stderr)
            sys.exit(1)

    elif os.path.isdir(target_path):
        search_path = target_path
        if args.recursive:
            print(i18n["searching_recursive"].format(path=search_path))
            for root, _, files in os.walk(search_path):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_files_to_process.append(os.path.join(root, file))
        else:
            print(i18n["searching_folder"].format(path=search_path))
            for item in os.listdir(search_path):
                full_path = os.path.join(search_path, item)
                if os.path.isfile(full_path) and item.lower().endswith('.pdf'):
                    pdf_files_to_process.append(full_path)

    if not pdf_files_to_process:
        print(i18n["no_files_found"])
        return

    total_files = len(pdf_files_to_process)
    print(f"\n{i18n['files_found'].format(count=total_files)}")

    renamed_count = 0
    with tqdm(total=total_files, desc=i18n["processing_desc"], unit=f" {i18n['processing_unit']}", ncols=100, leave=False) as pbar:
        for file_path in pdf_files_to_process:
            if rename_pdf_file(client, file_path, i18n):
                renamed_count += 1
            pbar.update(1)

    sys.stdout.write("\r" + " " * (pbar.ncols or 80) + "\r")
    sys.stdout.flush()
    print("----------------------------------------")
    print(i18n["processing_complete"])
    print(i18n["summary_renamed"].format(renamed_count=renamed_count, total_count=total_files))
    print("----------------------------------------")


if __name__ == '__main__':
    main()