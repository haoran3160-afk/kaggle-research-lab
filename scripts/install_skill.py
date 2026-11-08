"""Install the runtime package by copying files; keep development/history in source."""
import argparse
import json
from pathlib import Path
import shutil

LEGACY_RUNTIME = {"scripts/loop.py", "scripts/evaluation.py", "scripts/github_flow.py"}

def install(source, destination):
    source, destination = source.resolve(), destination.resolve()
    if not (source / "SKILL.md").is_file():
        raise ValueError("Choose the skill source directory")
    if source == destination or source in destination.parents or destination in source.parents:
        raise ValueError("Source and destination must be separate directories")
    names = ["SKILL.md", "agents/openai.yaml", "references/adapters.md", "references/workspace.md", "references/effectiveness.md", "references/system-research.md", "VERSION", "LICENSE", "THIRD_PARTY_NOTICES.md", "scripts/workspace.py", "scripts/install_skill.py"]
    names += ["modules/" + name + ".md" for name in ("specs", "learning", "intelligence", "baseline", "research", "progress", "execution", "delivery", "closeout")]
    names += [p.relative_to(source).as_posix() for p in (source / "assets").rglob("*") if p.is_file()]
    version = (source / "VERSION").read_text(encoding="utf-8").strip()
    names += [p.relative_to(source).as_posix() for p in (source / "upstream").rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"]
    for name in names:
        if not (source / name).is_file(): raise ValueError("Missing runtime file: " + name)
    # Keep the previous installed copy for local notes and v1 recovery. No digest comparison.
    if destination.exists():
        import datetime
        backup = destination.parent.parent / "skill-backups" / (destination.name + "-backup-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(destination, backup)
        owned = set(LEGACY_RUNTIME)
        old = destination / "INSTALL_MANIFEST.json"
        if old.exists():
            owned.update(json.loads(old.read_text(encoding="utf-8" )).get("files", {}))
        elif (destination / "INSTALLATION.json").exists():
            owned.update(json.loads((destination / "INSTALLATION.json").read_text(encoding="utf-8")).get("files", []))
        for name in owned - set(names):
            target = destination / name
            if destination in target.resolve().parents and target.is_file(): target.unlink()
        if old.exists(): old.unlink()
    else:
        backup = None
    for name in names:
        target = destination / name; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source / name, target)
    (destination / "INSTALLATION.json").write_text(json.dumps({"version":version,"source":str(source),"files":names,"previous_copy":str(backup) if backup else None},ensure_ascii=False,indent=2),encoding="utf-8")
    return {"installed":str(destination),"version":version,"files":len(names),"previous_copy":str(backup) if backup else None}

if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--source",type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument("--destination",type=Path,default=Path.home()/".agents/skills/kaggle-research-lab");a=p.parse_args();print(json.dumps(install(a.source,a.destination)))
