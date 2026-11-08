import importlib.util
from pathlib import Path
import tempfile
import unittest
import json
import re
spec=importlib.util.spec_from_file_location("installer",Path(__file__).resolve().parents[1]/"scripts/install_skill.py")
installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)

class InstallTests(unittest.TestCase):
    def make_source(self,root):
        src=root/"source"
        for name in ("SKILL.md","agents/openai.yaml","references/adapters.md","references/workspace.md","references/effectiveness.md","references/system-research.md","VERSION","LICENSE","THIRD_PARTY_NOTICES.md","scripts/workspace.py","scripts/resolution.py","scripts/install_skill.py","modules/research.md"):
            p=src/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text("content",encoding="utf-8")
        for name in ("learning", "intelligence", "baseline", "progress", "specs", "execution", "delivery", "closeout"):
            (src / "modules" / (name+".md")).write_text("module",encoding="utf-8")
        return src
    def test_copies_runtime_and_preserves_old_notes_outside_skill_discovery(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);src=self.make_source(root);dst=root/"skills"/"installed"
            dst.mkdir(parents=True);(dst/"SKILL.md").write_text("user notes",encoding="utf-8")
            (dst/"INSTALL_MANIFEST.json").write_text(json.dumps({"files":{"SKILL.md":"unused"}}))
            r=installer.install(src,dst)
            self.assertEqual((Path(r["previous_copy"])/"SKILL.md").read_text(),"user notes")
            self.assertNotEqual(Path(r["previous_copy"]).parent,dst.parent)
            self.assertFalse((dst/"INSTALL_MANIFEST.json").exists())
            self.assertTrue((dst/"scripts/workspace.py").exists())
            self.assertTrue((dst/"scripts/resolution.py").exists())
            self.assertEqual((dst/"references/effectiveness.md").read_text(),"content")
            self.assertEqual((dst/"references/system-research.md").read_text(),"content")
    def test_missing_source_leaves_install_alone(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);dst=root/"installed";dst.mkdir();(dst/"note").write_text("keep")
            with self.assertRaises(ValueError):installer.install(root/"missing",dst)
            self.assertEqual((dst/"note").read_text(),"keep")

    def test_real_install_keeps_core_references_templates_and_licenses(self):
        source = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "kaggle-research-lab"
            installer.install(source, destination)
            documents = [destination / "SKILL.md"]
            documents += list((destination / "modules").glob("*.md"))
            documents += list((destination / "references").glob("*.md"))
            for document in documents:
                for target in re.findall(r"\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
                    if "://" in target or target.startswith("#"):
                        continue
                    path = target.split("#", 1)[0]
                    self.assertTrue((document.parent / path).exists(), f"Missing {target} from {document}")
            for template in (source / "assets").iterdir():
                self.assertEqual((destination / "assets" / template.name).read_bytes(), template.read_bytes())
            self.assertTrue((destination / "LICENSE").is_file())
            self.assertTrue((destination / "upstream/openai/yeet/LICENSE.txt").is_file())

if __name__=="__main__":unittest.main()
