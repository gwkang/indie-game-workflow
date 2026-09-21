import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/'skills/game-ui-art-direction'
spec=importlib.util.spec_from_file_location('sample_validator',SKILL/'scripts/validate_sample_library.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class SampleLibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'library';shutil.copytree(SKILL/'assets/sample-library',self.root)
        self.data=json.loads((self.root/'manifest.json').read_text(encoding='utf-8'))
    def save(self): (self.root/'manifest.json').write_text(json.dumps(self.data),encoding='utf-8')
    def last_static(self): return next(e for e in reversed(self.data['entries']) if e['kind']=='button-shape')
    def test_real_library_and_relocated_closure(self):
        result=v.validate(self.root);self.assertEqual(17,result['entries']);self.assertFalse(result['projectApproval'])
        playful=[e['candidateSelector'] for e in self.data['entries'] if e['sampleId'].startswith('playful-ui-motion-')]
        self.assertEqual(['figure[data-motion="mechanical"]','figure[data-motion="elastic"]','figure[data-motion="sticker"]'],playful)
    def test_static_selectors_and_no_cycle_requirement(self):
        static=[e for e in self.data['entries'] if e['kind']=='button-shape']
        self.assertEqual(['#B01','#B02','#B03','#B04'],[e['candidateSelector'] for e in static])
        self.assertTrue(all('cycleSeconds' not in e['comparisonConditions'] for e in static))
        v.validate(self.root)
    def test_unknown_kind(self):
        self.data['entries'][0]['kind']='unknown';self.save()
        with self.assertRaisesRegex(v.LibraryError,'Unknown'):v.validate(self.root)
    def test_wrong_kind_and_missing_static_selectors(self):
        static=self.last_static();original=static['candidateSelector']
        for selector in ['#B99','figure[data-motion="snap"]','#B04 button','body']:
            static['candidateSelector']=selector;self.save()
            with self.subTest(selector=selector),self.assertRaisesRegex(v.LibraryError,'selector'):v.validate(self.root)
        static['candidateSelector']=original
        self.data['entries'][0]['candidateSelector']='#B01';self.save()
        with self.assertRaisesRegex(v.LibraryError,'selector'):v.validate(self.root)
    def test_static_missing_conditions(self):
        self.last_static()['comparisonConditions'].pop('label');self.save()
        with self.assertRaisesRegex(v.LibraryError,'conditions'):v.validate(self.root)
    def svg_fixture(self, addition, declared=False):
        self.data['entries']=[self.last_static()]
        e=self.data['entries'][0]
        name='button-shapes/1.0.0/B01.svg'
        p=self.root/name
        text=p.read_text(encoding='utf-8').replace('</svg>',addition+'</svg>')
        p.write_text(text,encoding='utf-8')
        e['sourceFiles'][name]=v.digest(p)
        e['provenance']['originalSourceHashes']['B01.svg']=v.digest(p)
        asset=self.root/'button-shapes/1.0.0/local.png'
        shutil.copyfile(self.root/'square-motion/1.0.0/tile.png',asset)
        if declared:
            e['sourceFiles']['button-shapes/1.0.0/local.png']=v.digest(asset)
            e['provenance']['originalSourceHashes']['local.png']=v.digest(asset)
        e['verification']['sourceFingerprint']=v.fingerprint(e['sourceFiles']);self.save()
    def test_svg_namespace_and_fragment_positive(self):
        self.assertEqual([],v.svg_references('<svg xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="face"/></defs><rect fill="url(#face)"/></svg>'))
    def test_svg_external_reference_variants(self):
        for body in ['<image href="https://example.invalid/x.png"/>', '<image xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="//example.invalid/x.png"/>', '<style>@font-face {src:url(https://example.invalid/x.woff)}</style>', '<rect style="fill:url(https://example.invalid/x.svg)"/>']:
            with self.subTest(body=body),self.assertRaisesRegex(v.LibraryError,'External SVG'):
                v.svg_references('<svg xmlns="http://www.w3.org/2000/svg">'+body+'</svg>')
    def test_svg_external_full_closure(self):
        self.svg_fixture('<image href="https://example.invalid/x.png"/>')
        with self.assertRaisesRegex(v.LibraryError,'External SVG'):v.validate(self.root)
    def test_svg_undeclared_local_reference(self):
        self.svg_fixture('<image href="local.png"/>')
        with self.assertRaisesRegex(v.LibraryError,'Undeclared'):v.validate(self.root)
    def test_svg_declared_local_reference(self):
        self.svg_fixture('<image href="local.png"/>',True)
        self.assertEqual(1,v.validate(self.root)['entries'])
    def test_svg_missing_fragment(self):
        with self.assertRaisesRegex(v.LibraryError,'fragment'):v.svg_references('<svg><rect fill="url(#missing)"/></svg>')
    def test_duplicate_identity(self):
        self.data['entries'].append(self.data['entries'][0]);self.save()
        with self.assertRaisesRegex(v.LibraryError,'duplicate'):v.validate(self.root)
    def test_missing_asset(self):
        (self.root/'square-motion/1.0.0/tile.png').unlink()
        with self.assertRaisesRegex(v.LibraryError,'Missing'):v.validate(self.root)
    def test_tamper(self):
        (self.root/'square-motion/1.0.0/gallery.js').write_text('tampered')
        with self.assertRaisesRegex(v.LibraryError,'Hash mismatch'):v.validate(self.root)
    def test_traversal_and_absolute_paths(self):
        for name in ['../outside','/absolute','C:/outside','square-motion/../outside','x\\evil','x%2fescape']:
            with self.subTest(name=name),self.assertRaises(v.LibraryError):v.local(self.root,name)
    def test_rights_pending(self):
        self.data['entries'][0]['rights']['status']='unknown';self.save()
        with self.assertRaisesRegex(v.LibraryError,'Rights'):v.validate(self.root)
    def test_review_stale(self):
        self.data['entries'][0]['verification']['sourceFingerprint']='0'*64;self.save()
        with self.assertRaisesRegex(v.LibraryError,'review'):v.validate(self.root)
    def test_external_dependency(self):
        self.data['entries'][0]['dependencies']['external']=['cdn'];self.save()
        with self.assertRaisesRegex(v.LibraryError,'dependencies'):v.validate(self.root)
    def test_undeclared_reference(self):
        e=self.data['entries'][0];e['sourceFiles'].pop('square-motion/1.0.0/tile.png');e['provenance']['originalSourceHashes'].pop('tile.png');e['verification']['sourceFingerprint']=v.fingerprint(e['sourceFiles']);self.save()
        with self.assertRaisesRegex(v.LibraryError,'Undeclared'):v.validate(self.root)
    def test_missing_selector(self):
        self.data['entries'][0]['candidateSelector']='figure[data-motion="absent"]';self.save()
        with self.assertRaisesRegex(v.LibraryError,'selector'):v.validate(self.root)
    def test_links_rejected(self):
        link=self.root/'linked'
        try:link.symlink_to(self.root/'square-motion/1.0.0/tile.png')
        except OSError:self.skipTest('Host does not allow symlink creation')
        with self.assertRaisesRegex(v.LibraryError,'Linked'):v.local(self.root,'linked')
if __name__=='__main__':unittest.main()
