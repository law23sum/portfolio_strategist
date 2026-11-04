"""Security-relevant defaults in portfolio_strategist/settings.py.

Settings are evaluated in a fresh interpreter per case so each environment can be set exactly.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase

BASE_DIR = Path(__file__).resolve().parents[3]
SETTINGS_FILE = BASE_DIR / "portfolio_strategist" / "settings.py"

PROBE = (
    "import json, django;"
    "from django.conf import settings;"
    "settings.SECRET_KEY;"  # force evaluation
    "print(json.dumps({'DEBUG': settings.DEBUG, 'ALLOWED_HOSTS': settings.ALLOWED_HOSTS,"
    " 'CORS_ALLOWED_ORIGINS': settings.CORS_ALLOWED_ORIGINS,"
    " 'CORS_ALLOW_ALL_ORIGINS': getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False),"
    " 'BREVO': settings.ANYMAIL.get('BREVO_API_KEY'),"
    " 'SECRET_KEY': settings.SECRET_KEY,"
    " 'JWT_KEY': settings.SIMPLE_JWT['SIGNING_KEY']}))"
)

_PASSTHROUGH = ("PATH", "HOME", "PYTHONPATH", "VIRTUAL_ENV", "LANG", "LC_ALL")


def load_settings(**env):
    """Return (returncode, parsed settings or None, stderr) for a clean environment plus ``env``."""
    clean = {k: os.environ[k] for k in _PASSTHROUGH if k in os.environ}
    clean["DJANGO_SETTINGS_MODULE"] = "portfolio_strategist.settings"
    clean.update(env)
    proc = subprocess.run(
        [sys.executable, "-c", PROBE], cwd=BASE_DIR, env=clean, capture_output=True, text=True, timeout=120
    )
    out = None
    if proc.returncode == 0:
        out = json.loads(proc.stdout.strip().splitlines()[-1])
    return proc.returncode, out, proc.stderr


class SecuritySettingsTests(SimpleTestCase):
    def test_secret_key_is_required_when_not_debug(self):
        code, _, err = load_settings()
        self.assertNotEqual(code, 0)
        self.assertIn("SECRET_KEY", err)
        self.assertIn("ImproperlyConfigured", err)

    def test_secret_key_is_required_when_debug_is_explicitly_false(self):
        code, _, err = load_settings(DEBUG="False")
        self.assertNotEqual(code, 0)
        self.assertIn("SECRET_KEY", err)

    def test_secret_key_comes_from_the_environment(self):
        code, cfg, err = load_settings(SECRET_KEY="unit-test-key-1")
        self.assertEqual(code, 0, err)
        self.assertEqual(cfg["SECRET_KEY"], "unit-test-key-1")

    def test_debug_defaults_to_false(self):
        code, cfg, err = load_settings(SECRET_KEY="k")
        self.assertEqual(code, 0, err)
        self.assertIs(cfg["DEBUG"], False)

    def test_debug_true_does_not_need_a_secret_key_for_local_development(self):
        code, cfg, err = load_settings(DEBUG="True")
        self.assertEqual(code, 0, err)
        self.assertIs(cfg["DEBUG"], True)
        self.assertTrue(cfg["SECRET_KEY"])

    def test_allowed_hosts_default_has_no_wildcard_and_env_overrides(self):
        _, cfg, _ = load_settings(SECRET_KEY="k")
        self.assertNotIn("*", cfg["ALLOWED_HOSTS"])
        self.assertIn("localhost", cfg["ALLOWED_HOSTS"])
        _, cfg, _ = load_settings(SECRET_KEY="k", ALLOWED_HOSTS="a.example.com,b.example.com")
        self.assertEqual(cfg["ALLOWED_HOSTS"], ["a.example.com", "b.example.com"])

    def test_cors_is_an_allowlist_never_allow_all(self):
        _, cfg, _ = load_settings(SECRET_KEY="k")
        self.assertIs(cfg["CORS_ALLOW_ALL_ORIGINS"], False)
        self.assertEqual(cfg["CORS_ALLOWED_ORIGINS"], [])  # nothing by default outside DEBUG
        _, cfg, _ = load_settings(SECRET_KEY="k", CORS_ALLOWED_ORIGINS="https://app.example.com,https://b.example.com")
        self.assertEqual(cfg["CORS_ALLOWED_ORIGINS"], ["https://app.example.com", "https://b.example.com"])
        self.assertIs(cfg["CORS_ALLOW_ALL_ORIGINS"], False)
        _, cfg, _ = load_settings(DEBUG="True")
        self.assertIs(cfg["CORS_ALLOW_ALL_ORIGINS"], False)
        self.assertTrue(all(o.startswith("http://") for o in cfg["CORS_ALLOWED_ORIGINS"]))

    def test_brevo_key_is_read_from_the_environment(self):
        _, cfg, _ = load_settings(SECRET_KEY="k")
        self.assertEqual(cfg["BREVO"], "")
        _, cfg, _ = load_settings(SECRET_KEY="k", BREVO_API_KEY="from-env")
        self.assertEqual(cfg["BREVO"], "from-env")

    def test_jwt_signing_key_defaults_to_secret_key_not_a_placeholder(self):
        _, cfg, _ = load_settings(SECRET_KEY="k-for-jwt")
        self.assertEqual(cfg["JWT_KEY"], "k-for-jwt")
        _, cfg, _ = load_settings(SECRET_KEY="k", SIMPLE_JWT_SIGNING_KEY="jwt-specific")
        self.assertEqual(cfg["JWT_KEY"], "jwt-specific")

    def test_no_credentials_are_hardcoded_in_settings_source(self):
        source = SETTINGS_FILE.read_text()
        self.assertIsNone(re.search(r"xkeysib-[0-9a-f]{20,}", source), "Brevo API key literal")
        self.assertNotIn("django-insecure-3x9N", source)
        self.assertIsNone(re.search(r"CORS_ALLOW_ALL_ORIGINS\s*=\s*True", source))


class RepositoryHygieneTests(SimpleTestCase):
    def test_gitignore_covers_key_material_and_generated_dirs(self):
        ignore = (BASE_DIR / ".gitignore").read_text().splitlines()
        for pattern in ("*.pem", "node_modules/", "static_root/", "documentation/password"):
            self.assertIn(pattern, ignore)

    def test_gitmodules_has_no_dangling_gitlink(self):
        tracked = subprocess.run(
            ["git", "ls-files", "-s"], cwd=BASE_DIR, capture_output=True, text=True
        )
        if tracked.returncode != 0:
            self.skipTest("not a git checkout")
        gitlinks = [line.split("\t", 1)[1] for line in tracked.stdout.splitlines() if line.startswith("160000")]
        gitmodules = BASE_DIR / ".gitmodules"
        declared = gitmodules.read_text() if gitmodules.exists() else ""
        for path in gitlinks:
            self.assertIn(path, declared, f"{path} is a gitlink with no .gitmodules entry")
