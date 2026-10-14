import hashlib
import json
import os
from functools import cache

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.safestring import mark_safe
from explorer import app_settings

register = template.Library()

VITE_OUTPUT_DIR = staticfiles_storage.url("explorer/")
VITE_DEV_DIR = "explorer/src/"
# Written by `vite build` (build.manifest in vite.config.mjs), keyed by source path.
VITE_MANIFEST = "manifest.json"
VITE_SERVER_HOST = getattr(settings, "VITE_SERVER_HOST", "localhost")
VITE_SERVER_PORT = getattr(settings, "VITE_SERVER_PORT", "5173")


@cache
def built_script(src: str) -> str:
    """
    Output filename of a built JS entry (e.g. "main.Bx3k9a.js"), from the Vite manifest.

    Vite content-hashes the entry filename, so every build that changes the bundle
    gets a new URL, and a host serving static files as long-lived/immutable never
    hands browsers a stale bundle. Don't version the entry with a query string
    instead: chunks import it by bare filename, and the browser would evaluate it
    twice, loading Bootstrap twice and breaking every dropdown.

    Returns the source basename when no frontend is built (no manifest); that URL
    404s in the browser, as an unbuilt frontend did before.
    """
    path = finders.find(f"explorer/{VITE_MANIFEST}")
    if not path:
        return os.path.basename(src)
    with open(path, encoding="utf-8") as f:
        return json.load(f)[src]["file"]


@cache
def content_version(file: str) -> str:
    """
    Cache-busting query string for the built stylesheet, derived from its bytes.

    The stylesheet keeps a fixed name (styles.css), so a host serving static files
    as long-lived/immutable would keep handing browsers the old one. A query string
    is safe here, unlike for JS entries, because nothing imports the stylesheet by URL.

    Returns "" when the file is not found (no frontend built, e.g. in tests);
    the URL is then the unversioned one.
    """
    path = finders.find(f"explorer/{file}")
    if not path:
        return ""
    with open(path, "rb") as f:
        return "?v=" + hashlib.sha256(f.read()).hexdigest()[:12]


def get_css_link(file: str) -> str:
    if app_settings.VITE_DEV_MODE is False:
        file = file.replace(".scss", ".css")
        base_url = f"{VITE_OUTPUT_DIR}"
        return mark_safe(f'<link rel="stylesheet" href="{base_url}{file}{content_version(file)}">')
    else:
        base_url = f"http://{VITE_SERVER_HOST}:{VITE_SERVER_PORT}/{VITE_DEV_DIR}"
    return mark_safe(f'<link rel="stylesheet" href="{base_url}{file}">')


def get_script(file: str) -> str:
    if app_settings.VITE_DEV_MODE is False:
        file = built_script(f"{VITE_DEV_DIR}{file}")
        return mark_safe(f'<script type="module" src="{VITE_OUTPUT_DIR}{file}"></script>')
    else:
        base_url = f"http://{VITE_SERVER_HOST}:{VITE_SERVER_PORT}/{VITE_DEV_DIR}"
    return mark_safe(f'<script type="module" src="{base_url}{file}"></script>')


def get_asset(file: str) -> str:
    if app_settings.VITE_DEV_MODE is False:
        return mark_safe(f"{VITE_OUTPUT_DIR}{file}")
    else:
        return mark_safe(f"http://{VITE_SERVER_HOST}:{VITE_SERVER_PORT}/{VITE_DEV_DIR}{file}")


@register.simple_tag
def vite_asset(filename: str):
    if str(filename).endswith("scss"):
        if app_settings.VITE_DEV_MODE is False:
            filename = os.path.basename(filename)
        return get_css_link(filename)
    if str(filename).endswith("js"):
        # Source-relative path (js/main.js) in both modes: the manifest is keyed by it.
        return get_script(filename)

    # Non js/scss assets respect directory structure so don't need to do the filename rewrite
    return get_asset(filename)


@register.simple_tag
def vite_hmr_client():
    if app_settings.VITE_DEV_MODE is False:
        return ""
    base_url = f"http://{VITE_SERVER_HOST}:{VITE_SERVER_PORT}/@vite/client"
    return mark_safe(f'<script type="module" src="{base_url}"></script>')
