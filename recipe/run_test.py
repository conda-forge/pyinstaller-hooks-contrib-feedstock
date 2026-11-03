import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path
from textwrap import dedent

import certifi

with tempfile.TemporaryDirectory(prefix="certifi-pyinstaller-") as temporary_directory:
    directory = Path(temporary_directory)
    source = directory / "probe.py"
    expected_digest = hashlib.sha256(Path(certifi.where()).read_bytes()).hexdigest()
    source.write_text(
        dedent(
            f"""\
            import hashlib
            import ssl
            import sys
            from pathlib import Path

            import certifi

            bundle = Path(certifi.where()).resolve()
            bundle.relative_to(Path(sys._MEIPASS).resolve())
            assert bundle.is_file()
            assert hashlib.sha256(bundle.read_bytes()).hexdigest() == {expected_digest!r}
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.load_verify_locations(cafile=str(bundle))
            assert context.cert_store_stats()["x509_ca"] > 0
            assert len(list(Path(sys._MEIPASS).rglob("cacert.pem"))) == 1
            """
        ),
        encoding="utf-8",
    )
    for mode in ("onedir", "onefile"):
        name = f"certifi_{mode}"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                "--noconfirm",
                "--clean",
                f"--{mode}",
                "--name",
                name,
                "--distpath",
                str(directory / "dist"),
                "--workpath",
                str(directory / "build"),
                "--specpath",
                str(directory),
                str(source),
            ],
            check=True,
        )
        executable = directory / "dist"
        if mode == "onedir":
            executable /= name
        executable /= name + (".exe" if sys.platform == "win32" else "")
        subprocess.run([str(executable)], check=True)
