#!/usr/bin/env python3
import os
import argparse
from datetime import datetime
import json
import sys
from tqdm import tqdm
import concurrent.futures
import time # For sleeping
import random # For jitter

# Import required libraries for file types
import PyPDF2
import docx

from openai import OpenAI, RateLimitError

# --- Configuration ---
OPENAI_MODEL = "gpt-3.5-turbo"
TEXT_SNIPPET_LENGTH = 4000
PAGES_TO_READ = 3
SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.md']
MAX_WORKERS = 10
MAX_RETRIES = 5

# --- Language Texts ---
LANGUAGES = {
    "en": {
        "app_description": "Intelligently renames or finds document files (PDF, DOCX, TXT) using AI.",
        "app_epilog": "Examples (Rename):\n  papyr              # Rename files in current directory\n  papyr ~/Documents  # Rename files in a specific directory\n\nExamples (Find):\n  papyr -f \"payslip from May 2025\"\n  papyr -f \"contract with Mr. Schimpf\" ~/Documents",
        "arg_path_help": "Path to the directory or file. Defaults to the current directory.",
        "arg_recursive_help": "Recursively search directories.",
        "arg_find_help": "Find files based on a natural language prompt instead of renaming.",
        "arg_lang_help": "Set the output language (en/de).",
        "error_path_not_exist": "Error: Path '{path}' does not exist.",
        "error_not_supported_file": "Error: The specified file is not a supported document type.",
        "searching_recursive": "Recursively searching for documents in '{path}'...",
        "searching_folder": "Searching for documents in '{path}'...",
        "no_files_found": "No supported document files found to process.",
        "files_found_rename": "Found {count} document file(s) to rename. Starting parallel processing.",
        "files_found_find": "Found {count} document file(s) to search. Starting AI analysis.",
        "processing_desc_rename": "Renaming Files",
        "processing_desc_find": "Searching Files",
        "processing_unit": "file",
        "processing_complete": "✅ Processing complete.",
        "summary_renamed": "{renamed_count} of {total_count} file(s) renamed successfully.",
        "summary_found": "Found {found_count} matching file(s):",
        "summary_found_none": "No matching files found.",
        "notice_encrypted": "Notice: '{filename}' is encrypted and cannot be read.",
        "error_reading_file": "Error reading file '{filename}': {error}",
        "error_openai_request": "-> OpenAI API Error: {error}",
        "info_already_correct": "-> Filename '{filename}' is already correct.",
        "warning_already_exists": "-> Warning: Target file '{target}' already existed. Renaming to '{new_name}' instead.",
        "success_renamed": "✅ {original_name} -> '{new_name}'",
        "error_processing_ai": "-> Error processing AI response for '{filename}': {error}",
        "warning_rate_limit": "-> Rate limit hit. Retrying in {delay:.1f}s... (Attempt {attempt}/{max_retries})",
        "error_rate_limit_final": "-> Failed after multiple retries due to rate limiting.",
        "ai_prompt_rename": """
    Analyze the following text from a document and return the information in JSON format:
    1. "topic": A general keyword in uppercase (e.g., INVOICE, CONTRACT, APPLICATION, NOTES).
    2. "subject": The full first and last name of the person OR the name of the company the document refers to. Format as 'FirstName_LastName' or 'CompanyName'. If neither applies, provide a brief content description (e.g., 'Rental_Agreement_Apartment').
    3. "title": A short, specific title for the document itself (e.g., 'Cover_Letter_Job_XYZ', 'Resume', 'Meeting-Notes', 'Payslip_May'). Replace spaces with hyphens.
    4. "year": The year mentioned in the document as a four-digit number. If not found, use the current year ({current_year}).
    5. "month": The month mentioned in the document as a two-digit number (01-12). If not found, use the current month ({current_month}).
    Respond exclusively with a valid JSON object.
    Text excerpt:
    ---
    {text}
    ---
    """,
        "ai_prompt_find": """
    You are a search assistant. A user is looking for a specific file.
    User's search query: "{query}"

    Below is the text content from a document. Does this document match the user's search query?
    Answer ONLY with "YES" if it matches, or "NO" if it does not. Do not provide any explanation.

    Document Text:
    ---
    {text}
    ---
    """,
        "affirmative_response": "YES"
    },
    "de": {
        "app_description": "Benennt oder findet Dokumentdateien (PDF, DOCX, TXT) intelligent mit KI.",
        "app_epilog": "Beispiele (Umbenennen):\n  papyr              # Benennt Dateien im aktuellen Ordner um\n  papyr ~/Dokumente  # Benennt Dateien in einem bestimmten Ordner um\n\nBeispiele (Finden):\n  papyr -f \"gehaltsabrechnung von Mai 2025\"\n  papyr -f \"vertrag mit Herrn Schimpf\" ~/Dokumente",
        "arg_path_help": "Pfad zum Verzeichnis oder zur Datei. Standard ist der aktuelle Ordner.",
        "arg_recursive_help": "Durchsucht Ordner rekursiv.",
        "arg_find_help": "Findet Dateien basierend auf einer natürlichsprachigen Anfrage, anstatt sie umzubenennen.",
        "arg_lang_help": "Legt die Ausgabesprache fest (en/de).",
        "error_path_not_exist": "Fehler: Der Pfad '{path}' existiert nicht.",
        "error_not_supported_file": "Fehler: Die angegebene Datei ist kein unterstützter Dokumenttyp.",
        "searching_recursive": "Suche rekursiv nach Dokumenten in '{path}'...",
        "searching_folder": "Suche nach Dokumenten in '{path}'...",
        "no_files_found": "Keine unterstützten Dokumentdateien zum Verarbeiten gefunden.",
        "files_found_rename": "{count} Dokumentdatei(en) zum Umbenennen gefunden. Starte parallele Verarbeitung.",
        "files_found_find": "{count} Dokumentdatei(en) zum Durchsuchen gefunden. Starte KI-Analyse.",
        "processing_desc_rename": "Benenne um",
        "processing_desc_find": "Durchsuche",
        "processing_unit": "Datei",
        "processing_complete": "✅ Verarbeitung abgeschlossen.",
        "summary_renamed": "{renamed_count} von {total_count} Datei(en) erfolgreich umbenannt.",
        "summary_found": "{found_count} passende Datei(en) gefunden:",
        "summary_found_none": "Keine passenden Dateien gefunden.",
        "notice_encrypted": "Hinweis: '{filename}' ist verschlüsselt und kann nicht gelesen werden.",
        "error_reading_file": "Fehler beim Lesen der Datei '{filename}': {error}",
        "error_openai_request": "-> OpenAI API Fehler: {error}",
        "info_already_correct": "-> Dateiname '{filename}' ist bereits korrekt.",
        "warning_already_exists": "-> Warnung: Zieldatei '{target}' existierte bereits. Benenne stattdessen in '{new_name}' um.",
        "success_renamed": "✅ {original_name} -> '{new_name}'",
        "error_processing_ai": "-> Fehler beim Verarbeiten der KI-Antwort für '{filename}': {error}",
        "warning_rate_limit": "-> Rate-Limit erreicht. Erneuter Versuch in {delay:.1f}s... (Versuch {attempt}/{max_retries})",
        "error_rate_limit_final": "-> Nach mehreren Versuchen wegen Rate-Limits fehlgeschlagen.",
        "ai_prompt_rename": """
    Analysiere den folgenden Text aus einem Dokument und gib die Informationen im JSON-Format zurück:
    1. "topic": Ein allgemeines Schlagwort in Grossbuchstaben (z.B. RECHNUNG, VERTRAG, BEWERBUNG, NOTIZEN).
    2. "subject": Der vollständige Vor- und Nachname der Person ODER der Name der Firma, auf die sich das Dokument bezieht. Formatiere als 'Vorname_Nachname' oder 'Firmenname'. Falls beides nicht zutrifft, gib eine kurze Inhaltsbeschreibung (z.B. 'Mietvertrag_Wohnung').
    3. "title": Ein kurzer, spezifischer Titel für das Dokument selbst (z.B. 'Anschreiben_Stelle_XYZ', 'Lebenslauf', 'Meeting-Notizen' oder 'Gehaltsabrechnung_Mai'). Ersetze Leerzeichen mit Bindestrichen.
    4. "year": Das im Dokument genannte Jahr als vierstellige Zahl. Falls nicht vorhanden, nutze das aktuelle Jahr ({current_year}).
    5. "month": Der im Dokument genannte Monat als zweistellige Zahl (01-12). Falls nicht vorhanden, nutze den aktuellen Monat ({current_month}).
    Antworte ausschließlich mit einem validen JSON-Objekt.
    Textauszug:
    ---
    {text}
    ---
    """,
        "ai_prompt_find": """
    Du bist ein Suchassistent. Ein Benutzer sucht nach einer bestimmten Datei.
    Suchanfrage des Benutzers: "{query}"

    Unten steht der Textinhalt aus einem Dokument. Passt dieses Dokument zur Suchanfrage des Benutzers?
    Antworte NUR mit "JA", wenn es passt, oder "NEIN", wenn es nicht passt. Gib keine Erklärung.

    Dokumententext:
    ---
    {text}
    ---
    """,
        "affirmative_response": "JA"
    }
}

# --- Helper and Core Functions ---

def _extract_from_pdf(file_path: str, i18n: dict) -> str:
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        if reader.is_encrypted:
            tqdm.write(i18n["notice_encrypted"].format(filename=os.path.basename(file_path)), file=sys.stderr)
            return ""
        text = ""
        for i in range(min(len(reader.pages), PAGES_TO_READ)):
            text += reader.pages[i].extract_text() or ""
        return text

def _extract_from_docx(file_path: str, i18n: dict) -> str:
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def _extract_from_txt(file_path: str, i18n: dict) -> str:
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        return file.read()

def extract_text_from_file(file_path: str, i18n: dict) -> str:
    _, extension = os.path.splitext(file_path)
    try:
        if extension == '.pdf': return _extract_from_pdf(file_path, i18n)
        elif extension == '.docx': return _extract_from_docx(file_path, i18n)
        elif extension in ['.txt', '.md']: return _extract_from_txt(file_path, i18n)
        else: return ""
    except Exception as e:
        tqdm.write(i18n["error_reading_file"].format(filename=os.path.basename(file_path), error=e), file=sys.stderr)
        return ""

def call_openai_with_retry(client: OpenAI, prompt: str, i18n: dict, is_json: bool) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"} if is_json else None,
                temperature=0.0,
            )
            return response.choices[0].message.content
        except RateLimitError:
            if attempt < MAX_RETRIES - 1:
                delay = (2 ** attempt) + random.uniform(0, 1)
                tqdm.write(i18n["warning_rate_limit"].format(delay=delay, attempt=attempt + 1, max_retries=MAX_RETRIES), file=sys.stderr)
                time.sleep(delay)
            else:
                tqdm.write(i18n["error_rate_limit_final"], file=sys.stderr)
                return None
        except Exception as e:
            tqdm.write(i18n["error_openai_request"].format(error=e), file=sys.stderr)
            return None
    return None

def discover_files(path: str, is_recursive: bool, i18n: dict) -> list:
    files_to_process = []
    if not os.path.exists(path):
        print(i18n["error_path_not_exist"].format(path=path), file=sys.stderr)
        sys.exit(1)

    if os.path.isfile(path):
        if any(path.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
            files_to_process.append(path)
        else:
            print(i18n["error_not_supported_file"], file=sys.stderr)
            sys.exit(1)

    elif os.path.isdir(path):
        print(i18n["searching_recursive"].format(path=path) if is_recursive else i18n["searching_folder"].format(path=path))
        for root, _, files in os.walk(path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                    files_to_process.append(os.path.join(root, file))
            if not is_recursive: break

    return files_to_process

# --- Rename Mode Logic ---

def process_and_rename_file(client: OpenAI, file_path: str, i18n: dict) -> bool:
    text = extract_text_from_file(file_path, i18n)
    if not text: return False

    prompt = i18n["ai_prompt_rename"].format(
        current_year=datetime.now().year,
        current_month=datetime.now().strftime('%m'),
        text=text[:TEXT_SNIPPET_LENGTH]
    )
    response_str = call_openai_with_retry(client, prompt, i18n, is_json=True)
    if not response_str: return False

    try:
        name_parts = json.loads(response_str)
        topic = name_parts.get('topic', 'UNKNOWN').upper()
        subject = name_parts.get('subject', 'unknown').replace(" ", "_")
        title = name_parts.get('title', 'untitled').replace(" ", "-")
        year = name_parts.get('year', str(datetime.now().year))
        month = name_parts.get('month', datetime.now().strftime('%m'))

        _, extension = os.path.splitext(file_path)
        new_name = f"{topic}_{subject}_{title}_{year}-{month}{extension}"
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

def run_rename_mode(client: OpenAI, path: str, is_recursive: bool, i18n: dict):
    files_to_process = discover_files(path, is_recursive, i18n)
    if not files_to_process:
        print(i18n["no_files_found"])
        return

    total_files = len(files_to_process)
    print(f"\n{i18n['files_found_rename'].format(count=total_files)}")
    renamed_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_file = {executor.submit(process_and_rename_file, client, f, i18n): f for f in files_to_process}
        pbar = tqdm(concurrent.futures.as_completed(future_to_file), total=total_files, desc=i18n["processing_desc_rename"], unit=f" {i18n['processing_unit']}", ncols=100, leave=False)
        for future in pbar:
            if future.result():
                renamed_count += 1

    sys.stdout.write("\r" + " " * (pbar.ncols or 80) + "\r")
    sys.stdout.flush()
    print("----------------------------------------")
    print(i18n["processing_complete"])
    print(i18n["summary_renamed"].format(renamed_count=renamed_count, total_count=total_files))
    print("----------------------------------------")

# --- Find Mode Logic ---

def check_file_for_match(client: OpenAI, file_path: str, query: str, i18n: dict) -> str or None:
    text = extract_text_from_file(file_path, i18n)
    if not text: return None

    prompt = i18n["ai_prompt_find"].format(query=query, text=text[:TEXT_SNIPPET_LENGTH])
    response_str = call_openai_with_retry(client, prompt, i18n, is_json=False)

    # CORRECTED LOGIC: Check for the affirmative response of the selected language
    affirmative_response = i18n["affirmative_response"]
    if response_str and response_str.strip().upper() == affirmative_response:
        return file_path
    return None

def run_find_mode(client: OpenAI, path: str, query: str, is_recursive: bool, i18n: dict):
    files_to_process = discover_files(path, is_recursive, i18n)
    if not files_to_process:
        print(i18n["no_files_found"])
        return

    total_files = len(files_to_process)
    print(f"\n{i18n['files_found_find'].format(count=total_files)}")
    found_files = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_file = {executor.submit(check_file_for_match, client, f, query, i18n): f for f in files_to_process}
        pbar = tqdm(concurrent.futures.as_completed(future_to_file), total=total_files, desc=i18n["processing_desc_find"], unit=f" {i18n['processing_unit']}", ncols=100, leave=False)
        for future in pbar:
            result = future.result()
            if result:
                found_files.append(result)

    sys.stdout.write("\r" + " " * (pbar.ncols or 80) + "\r")
    sys.stdout.flush()
    print("----------------------------------------")
    print(i18n["processing_complete"])
    if found_files:
        print(i18n["summary_found"].format(found_count=len(found_files)))
        for f in sorted(found_files):
            print(f"  -> {f}")
    else:
        print(i18n["summary_found_none"])
    print("----------------------------------------")

# --- Main Application ---

def main():
    # Setup initial parser to get language
    lang_parser = argparse.ArgumentParser(add_help=False)
    lang_parser.add_argument('-l', '--lang', choices=['en', 'de'], default='en')
    lang_args, _ = lang_parser.parse_known_args()
    i18n = LANGUAGES[lang_args.lang]

    # Setup the main parser with translated texts
    parser = argparse.ArgumentParser(
        description=i18n["app_description"],
        prog="papyr",
        epilog=i18n["app_epilog"],
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help=i18n["arg_path_help"]
    )
    parser.add_argument(
        '-f', '--find',
        dest='find_query',
        type=str,
        default=None,
        help=i18n["arg_find_help"]
    )
    parser.add_argument('-r', '--recursive', action='store_true', help=i18n["arg_recursive_help"])
    parser.add_argument('-l', '--lang', choices=['en', 'de'], default='en', help=i18n["arg_lang_help"])

    args = parser.parse_args()

    try:
        client = OpenAI()
    except Exception:
        # Re-get language in case it was passed after other args
        final_lang = args.lang
        final_i18n = LANGUAGES[final_lang]
        # This part of the code is not used anymore, but I will keep it for now.
        # print(final_i18n["error_api_key_not_found"].strip(), file=sys.stderr)
        sys.exit(1)

    target_path = os.path.expanduser(args.path)

    if args.find_query:
        run_find_mode(client, target_path, args.find_query, args.recursive, i18n)
    else:
        run_rename_mode(client, target_path, args.recursive, i18n)

if __name__ == '__main__':
    main()