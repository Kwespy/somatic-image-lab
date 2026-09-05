import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import local_server


class LocalWorkflowTests(unittest.TestCase):
    def test_invalid_selection_never_renders(self):
        with patch('local_server.screenshot') as render:
            for slug,kind,lang,variant in [('../escape','story','es',0), ('001-peter-weibel','other','es',0), ('001-peter-weibel','post','fr',0), ('001-peter-weibel','story','es',8)]:
                with self.assertRaises(ValueError):
                    local_server.render_one(slug,kind,lang,variant,Path('/tmp/unused.png'))
            render.assert_not_called()

    def test_selected_image_only(self):
        with patch('local_server.screenshot') as render:
            local_server.render_one('001-peter-weibel','post','en',0,Path('/tmp/unused.png'))
            render.assert_called_once()
            self.assertEqual(render.call_args.args[2], (1080,1350))
            self.assertIn('The Post-Media', render.call_args.args[0])

    def test_import_without_images_or_git(self):
        with tempfile.TemporaryDirectory() as folder:
            dest=Path(folder)
            for directory in ('scripts','data','assets'):
                shutil.copytree(ROOT/directory,dest/directory)
            for name in ('index.html','sitemap.xml'):
                shutil.copy2(ROOT/name,dest/name)
            for page in ROOT.glob('readings/*/index.html'):
                target=dest/page.relative_to(ROOT)
                target.parent.mkdir(parents=True)
                shutil.copy2(page,target)
            package=dest/'incoming'
            package.mkdir()
            (package/'manifest.json').write_text(json.dumps(dict(author='Local test',title_en='Local test',title_es='Prueba local',date='2026-09-05',slug='local-test',error_es='prueba',error_en='test')))
            (package/'index.html').write_text('<html><head></head><body><span>KWY-A⁰¹RTBORG</span></body></html>')
            old_count=len(json.loads((dest/'data/readings.json').read_text()))
            result=subprocess.run([sys.executable,'-B',str(dest/'scripts/add_post.py'),str(package)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual(len(json.loads((dest/'data/readings.json').read_text())),old_count+1)
            self.assertFalse(list((dest / 'readings').rglob('*.png')))
            self.assertFalse(list((dest / 'readings').rglob('*.zip')))
            self.assertFalse((dest/'.git').exists())
            self.assertIn('Sin commit ni push',result.stdout)
            new_page = next((dest / 'readings').glob('*local-test/index.html'))
            self.assertIn('/assets/favicon.svg', new_page.read_text())

if __name__ == '__main__':
    unittest.main()
