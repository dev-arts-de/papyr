# frozen_string_literal: true

class Papyr < Formula
  desc "Intelligently renames PDF files using AI"
  homepage "https://github.com/dev-arts-de/papyr"
  url "https://github.com/dev-arts-de/papyr/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "65287e6d1c163bfb3540bda3d83d77c3f05f9551b9a34ccdb71200316f5ad098"
  license "MIT"

  depends_on "python@3.12"

  resource "openai" do
    url "https://pypi.io/packages/source/o/openai/openai-1.35.7.tar.gz"
    sha256 "05663a848f2b386417754324f469248536e13b860ba26742531245b788a47816"
  end

  resource "pypdf2" do
    url "https://pypi.io/packages/source/P/PyPDF2/PyPDF2-3.0.1.tar.gz"
    sha256 "94b9f02c6347314c99c855cce24e2b0c4f826046e2a2215b252030d0758364cb"
  end

  resource "tqdm" do
    url "https://pypi.io/packages/source/t/tqdm/tqdm-4.66.4.tar.gz"
    sha256 "232de5fbe2a3c5822b39882256e093aad569f6e1f0611a9efe58a2d1522a46c1"
  end

  def install
    # Erstellt eine isolierte Python-Umgebung
    venv = virtualenv_create(libexec, "python3")
    # Installiert die Python-Pakete in diese Umgebung
    venv.pip_install resources
    # Kopiert Ihr Skript in die Umgebung
    libexec.install "papyr.py"
    # Erstellt den finalen 'papyr'-Befehl
    (bin/"papyr").write_env_script libexec/"papyr.py", PATH: "#{venv.root}/bin:$PATH"
  end

  test do
    # Ein einfacher Test, um zu prüfen, ob der Befehl funktioniert
    assert_match "usage: papyr", shell_output("#{bin}/papyr --help")
  end
end
