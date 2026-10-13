import os
import tempfile
from unittest import mock

from django.test import TestCase

from explorer.templatetags import vite


@mock.patch.object(vite.app_settings, "VITE_DEV_MODE", False)
class TestViteAssetUrls(TestCase):

    def setUp(self):
        vite.content_version.cache_clear()
        self.addCleanup(vite.content_version.cache_clear)

    def _built_file(self, content):
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        self.addCleanup(os.remove, path)
        return path

    def test_script_url_carries_content_hash(self):
        path = self._built_file(b"console.log('v1')")
        with mock.patch.object(vite.finders, "find", return_value=path) as find:
            tag = vite.get_script("main.js")
        find.assert_called_once_with(f"explorer/main.{vite.get_version()}.js")
        self.assertRegex(tag, r'src="[^"]*main\.[\d.]+\.js\?v=[0-9a-f]{12}"')

    def test_css_url_carries_content_hash(self):
        path = self._built_file(b"body{}")
        with mock.patch.object(vite.finders, "find", return_value=path):
            tag = vite.get_css_link("styles.scss")
        self.assertRegex(tag, r'href="[^"]*styles\.css\?v=[0-9a-f]{12}"')

    def test_changed_content_changes_the_url(self):
        old = self._built_file(b"old bundle")
        new = self._built_file(b"new bundle")
        with mock.patch.object(vite.finders, "find", return_value=old):
            old_tag = vite.get_script("main.js")
        vite.content_version.cache_clear()
        with mock.patch.object(vite.finders, "find", return_value=new):
            new_tag = vite.get_script("main.js")
        self.assertNotEqual(old_tag, new_tag)

    def test_missing_build_falls_back_to_unversioned_url(self):
        with mock.patch.object(vite.finders, "find", return_value=None):
            tag = vite.get_script("main.js")
        self.assertIn(f'main.{vite.get_version()}.js"', tag)
