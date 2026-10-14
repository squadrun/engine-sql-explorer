import json
import os
import tempfile
from unittest import mock

from django.test import TestCase

from explorer.templatetags import vite


@mock.patch.object(vite.app_settings, "VITE_DEV_MODE", False)
class TestViteAssetUrls(TestCase):

    def setUp(self):
        vite.content_version.cache_clear()
        vite.built_script.cache_clear()
        self.addCleanup(vite.content_version.cache_clear)
        self.addCleanup(vite.built_script.cache_clear)

    def _built_file(self, content):
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        self.addCleanup(os.remove, path)
        return path

    def _manifest(self, entry_file):
        return self._built_file(json.dumps({
            "explorer/src/js/main.js": {"file": entry_file, "isEntry": True},
        }).encode())

    def test_script_url_is_the_hashed_entry_from_the_manifest(self):
        path = self._manifest("main.B3nNdwUH.js")
        with mock.patch.object(vite.finders, "find", return_value=path) as find:
            tag = vite.vite_asset("js/main.js")
        find.assert_called_once_with("explorer/manifest.json")
        self.assertIn(f'src="{vite.VITE_OUTPUT_DIR}main.B3nNdwUH.js"', tag)

    def test_script_url_has_no_query_string(self):
        # Chunks import the entry by bare filename. A query string on the <script> src
        # makes it a different module URL, so the browser evaluates the entry twice.
        path = self._manifest("main.B3nNdwUH.js")
        with mock.patch.object(vite.finders, "find", return_value=path):
            tag = vite.vite_asset("js/main.js")
        self.assertNotIn("?", tag)

    def test_css_url_carries_content_hash(self):
        path = self._built_file(b"body{}")
        with mock.patch.object(vite.finders, "find", return_value=path):
            tag = vite.get_css_link("styles.scss")
        self.assertRegex(tag, r'href="[^"]*styles\.css\?v=[0-9a-f]{12}"')

    def test_changed_css_changes_the_url(self):
        old = self._built_file(b"body{color:red}")
        new = self._built_file(b"body{color:blue}")
        with mock.patch.object(vite.finders, "find", return_value=old):
            old_tag = vite.get_css_link("styles.scss")
        vite.content_version.cache_clear()
        with mock.patch.object(vite.finders, "find", return_value=new):
            new_tag = vite.get_css_link("styles.scss")
        self.assertNotEqual(old_tag, new_tag)

    def test_missing_build_falls_back_to_unhashed_url(self):
        with mock.patch.object(vite.finders, "find", return_value=None):
            script = vite.vite_asset("js/main.js")
            css = vite.get_css_link("styles.scss")
        self.assertIn(f'src="{vite.VITE_OUTPUT_DIR}main.js"', script)
        self.assertIn(f'href="{vite.VITE_OUTPUT_DIR}styles.css"', css)
