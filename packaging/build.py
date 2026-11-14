#!/usr/bin/env python3
"""Gera os pacotes do doguia-usage em dist/.

    python packaging/build.py              dist/doguia-usage.pyz (qualquer sistema com Python 3.9 ou mais novo)
    python packaging/build.py --binary     também o executável deste sistema, em build/bin (PyInstaller)
    python packaging/build.py --installer  também o instalador deste sistema, em dist/:
                                             Linux   doguia-usage_<v>_<arq>.deb e doguia-usage-<v>-linux-<arq>.tar.gz
                                             macOS   doguia-usage-<v>-macos-<arq>.pkg (pkgbuild)
                                             Windows doguia-usage-<v>-windows-<arq>-setup.exe (Inno Setup 6)

O executável leva o próprio Python: quem instala não precisa de nada. O PyInstaller não compila para outro sistema,
então cada instalador sai do workflow .github/workflows/companion.yml, num runner de cada sistema.
"""
import os, platform, re, shutil, subprocess, sys, tarfile, tempfile, zipapp
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "packaging"
DIST = ROOT / "dist"
BIN = ROOT / "build" / "bin"
VERSION = re.search(r'__version__ = "([^"]+)"', (ROOT / "doguia_usage/__init__.py").read_text()).group(1)


def arch() -> str:
    m = platform.machine().lower()
    return {"amd64": "x64", "x86_64": "x64", "aarch64": "arm64", "arm64": "arm64"}.get(m, m)


def pyz() -> Path:
    DIST.mkdir(exist_ok=True)
    out = DIST / "doguia-usage.pyz"
    with tempfile.TemporaryDirectory() as t:
        shutil.copytree(ROOT / "doguia_usage", Path(t) / "doguia_usage", ignore=shutil.ignore_patterns("__pycache__"))
        zipapp.create_archive(t, out, interpreter="/usr/bin/env python3", main="doguia_usage.cli:main", compressed=True)
    return out


def pyinstaller(name: str, *extra: str) -> None:
    with tempfile.TemporaryDirectory() as t:
        entry = Path(t) / "entry.py"
        entry.write_text("from doguia_usage.cli import main\nmain()\n")
        subprocess.run([sys.executable, "-m", "PyInstaller", "--onefile", "--name", name, "--clean", "--noconfirm",
                        "--paths", str(ROOT), "--collect-submodules", "doguia_usage", "--collect-data", "doguia_usage", *extra,
                        "--distpath", str(BIN), "--workpath", t, "--specpath", t, str(entry)], check=True)


def binary() -> Path:
    shutil.rmtree(BIN, ignore_errors=True)
    pyinstaller("doguia-usage", *(["--strip"] if sys.platform.startswith("linux") else []))  # no macOS quebraria a assinatura
    if sys.platform == "win32":  # cópia sem janela para o início automático (platforms.BACKGROUND_EXE)
        pyinstaller("doguia-usage-bg", "--noconsole")
    exe = BIN / ("doguia-usage.exe" if sys.platform == "win32" else "doguia-usage")
    subprocess.run([str(exe), "--version"], check=True)
    return exe


def tar_gz(exe: Path) -> Path:
    name = f"doguia-usage-{VERSION}-linux-{arch()}"
    out = DIST / f"{name}.tar.gz"

    def mode(info: tarfile.TarInfo) -> tarfile.TarInfo:
        info.uid = info.gid = 0
        info.uname = info.gname = ""
        if info.isfile():
            info.mode = 0o755 if info.name.endswith((".sh", "/doguia-usage")) else 0o644
        return info

    with tarfile.open(out, "w:gz") as tar:
        tar.add(exe, f"{name}/doguia-usage", filter=mode)
        for f in ("install.sh", "uninstall.sh", "doguia-usage.desktop"):
            tar.add(PKG / "linux" / f, f"{name}/{f}", filter=mode)
        for doc in ("README.md", "INSTALACAO.md", "REFERENCIA.md", "DOWNLOAD.md"):
            tar.add(ROOT / doc, f"{name}/{doc}", filter=mode)
    return out


def deb(exe: Path) -> Path:
    debarch = {"x64": "amd64", "arm64": "arm64"}.get(arch(), arch())
    out = DIST / f"doguia-usage_{VERSION}_{debarch}.deb"
    with tempfile.TemporaryDirectory() as t:
        root = Path(t) / "root"
        (root / "DEBIAN").mkdir(parents=True)
        (root / "usr/bin").mkdir(parents=True)
        (root / "usr/share/applications").mkdir(parents=True)
        (root / "usr/share/doc/doguia-usage").mkdir(parents=True)
        shutil.copy2(exe, root / "usr/bin/doguia-usage")
        os.chmod(root / "usr/bin/doguia-usage", 0o755)
        desktop = (PKG / "linux/doguia-usage.desktop").read_text().replace("@BIN@", "/usr/bin/doguia-usage")
        (root / "usr/share/applications/doguia-usage.desktop").write_text(desktop)
        shutil.copy2(ROOT / "README.md", root / "usr/share/doc/doguia-usage/README.md")
        shutil.copy2(ROOT / "INSTALACAO.md", root / "usr/share/doc/doguia-usage/INSTALACAO.md")
        os.chmod(root, 0o755)
        for p in root.rglob("*"):
            os.chmod(p, 0o755 if p.is_dir() or p.name == "doguia-usage" else 0o644)
        size = sum(p.stat().st_size for p in root.rglob("*") if p.is_file()) // 1024
        (root / "DEBIAN/control").write_text(
            f"Package: doguia-usage\nVersion: {VERSION}\nArchitecture: {debarch}\nMaintainer: DoguIA <https://www.doguia.com.br>\n"
            f"Installed-Size: {size}\nSection: utils\nPriority: optional\nHomepage: https://www.doguia.com.br\n"
            "Description: consumo de IA no DoguIA Display\n"
            " Envia ao DoguIA Display, pela rede local, o consumo de Claude Code, Codex,\n"
            " Antigravity, OpenCode e DeepSeek. Depois de instalar: doguia-usage configurar\n")
        for script in ("postinst", "prerm"):
            shutil.copy2(PKG / "linux" / script, root / "DEBIAN" / script)
            os.chmod(root / "DEBIAN" / script, 0o755)
        subprocess.run(["dpkg-deb", "--root-owner-group", "-Zxz", "--build", str(root), str(out)], check=True)
    return out


def macos_pkg(exe: Path) -> Path:
    out = DIST / f"doguia-usage-{VERSION}-macos-{arch()}.pkg"
    with tempfile.TemporaryDirectory() as t:
        root, scripts = Path(t) / "root", Path(t) / "scripts"
        (root / "usr/local/bin").mkdir(parents=True)
        apps = root / "Applications/DoguIA Usage"
        apps.mkdir(parents=True)
        shutil.copy2(exe, root / "usr/local/bin/doguia-usage")
        for f in (PKG / "macos").glob("*.command"):
            shutil.copy2(f, apps / f.name)
            os.chmod(apps / f.name, 0o755)
        shutil.copy2(ROOT / "INSTALACAO.md", apps / "INSTALACAO.md")
        scripts.mkdir()
        shutil.copy2(PKG / "macos/postinstall", scripts / "postinstall")
        os.chmod(scripts / "postinstall", 0o755)
        subprocess.run(["pkgbuild", "--root", str(root), "--scripts", str(scripts), "--identifier", "br.com.doguia.usage",
                        "--version", VERSION, "--install-location", "/", str(out)], check=True)
    return out


def iscc() -> str:
    for c in (shutil.which("iscc"), *(Path(os.environ.get(v, "")) / "Inno Setup 6/ISCC.exe" for v in ("ProgramFiles(x86)", "ProgramFiles"))):
        if c and Path(c).is_file():
            return str(c)
    sys.exit("Inno Setup 6 não encontrado (choco install innosetup)")


def windows_setup(exe: Path) -> Path:
    name = f"doguia-usage-{VERSION}-windows-{arch()}-setup"
    subprocess.run([iscc(), f"/DAppVer={VERSION}", f"/DBinDir={BIN}", f"/DOutDir={DIST}", f"/DOutName={name}", f"/DDocDir={ROOT}",
                    str(PKG / "windows/doguia-usage.iss")], check=True)
    return DIST / f"{name}.exe"


def installer(exe: Path) -> list:
    if sys.platform == "win32":
        return [windows_setup(exe)]
    if sys.platform == "darwin":
        return [macos_pkg(exe)]
    return [tar_gz(exe), deb(exe)]


if __name__ == "__main__":
    print(pyz())
    if "--binary" in sys.argv or "--installer" in sys.argv:
        exe = binary()
        print(exe)
        if "--installer" in sys.argv:
            for f in installer(exe):
                print(f)
