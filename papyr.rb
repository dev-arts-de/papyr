# frozen_string_literal: true

class Papyr < Formula
  desc "A CLI tool to intelligently rename PDF files using AI"
  homepage "https://github.com/IHR_GITHUB_BENUTZERNAME/papyr"
  # Diese URL bekommen Sie von der Release-Seite Ihres papyr-Projekts ("Source code (tar.gz)")
  url "https://github.com/IHR_GITHUB_BENUTZERNAME/papyr/archive/refs/tags/v1.0.0.tar.gz" 
  # Den SHA256-Hash müssen Sie selbst generieren (siehe unten)
  sha256 "HIER_DEN_SHA256_HASH_EINFUEGEN" 
  license "MIT"

  # Hier definieren wir die Abhängigkeiten
  depends_on "python@3.12" # Oder eine andere aktuelle Python-Version

  # In "resource"-Blöcken werden die Python-Pakete definiert
  resource "openai" do
    url "https://pypi.io/packages/source/o/openai/openai-1.35.7.tar.gz"
    sha256 "05663a848f2b386417754324f469248536e13b860ba26742531245b788a47816"
  end

  resource "pypdf2" do
    url "https://pypi.io/packages/source/P/PyPDF2/PyPDF2-3.0.1.tar.gz"
    sha256 "94b9f02c6347314c99c855cce24e2b0c4f826046e2a2215b252030d0758364cb"
  end

  def install
    # Erstellt eine isolierte Python-Umgebung, um Konflikte zu vermeiden
    venv = virtualenv_create(libexec, "python3")
    
    # Installiert die Abhängigkeiten in diese Umgebung
    venv.pip_install resources

    # Kopiert Ihr Skript in die Umgebung
    venv.pip_install_and_link buildpath

    # Erstellt die finale ausführbare Datei in /usr/local/bin
    bin.install_symlink libexec/"bin/papyr.py" => "papyr"
  end

  test do
    # Ein einfacher Test, um zu sehen, ob der Befehl ausgeführt werden kann
    assert_match "usage: papyr", shell_output("#{bin}/papyr --help")
  end
end
