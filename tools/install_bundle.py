"""Install a locally supplied, content-locked skill bundle. Preview by default."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile


class InstallError(ValueError):
    pass


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reject_links(path):
    for item in (path, *path.parents):
        if item.is_symlink() or (hasattr(item, 'is_junction') and item.is_junction()):
            raise InstallError(f'Linked path is not supported: {item}')


def inventory(path):
    reject_links(path)
    if not path.is_dir():
        raise InstallError(f'Expected directory: {path}')
    result = {}
    for item in sorted(path.rglob('*')):
        reject_links(item)
        if item.is_file():
            result[item.relative_to(path).as_posix()] = digest(item)
    return result


def read_bundle(root):
    root = Path(root).absolute()
    reject_links(root)
    manifest = json.loads((root / 'bundle.json').read_text(encoding='utf-8'))
    lock = json.loads((root / 'bundle.lock.json').read_text(encoding='utf-8'))
    if lock.get('lockVersion') != 1 or not lock.get('entries'):
        raise InstallError('Unsupported or empty lock')
    if manifest.get('bundleVersion') != lock.get('bundleVersion'):
        raise InstallError('Manifest and lock versions differ')
    manifest_skills = manifest.get('skills')
    if not isinstance(manifest_skills, list) or len(manifest_skills) != len(set(manifest_skills)):
        raise InstallError('Manifest skills must be a unique list')
    entries, names = [], set()
    for entry in lock['entries']:
        name = entry['id']
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or name in names:
            raise InstallError(f'Invalid or duplicate skill ID: {name}')
        names.add(name)
        if entry['source'] != f'skills/{name}':
            raise InstallError(f'Unexpected source: {entry["source"]}')
        files = entry['files']
        if 'SKILL.md' not in files:
            raise InstallError(f'Missing SKILL.md: {name}')
        for relative, value in files.items():
            parts = PurePosixPath(relative)
            if (parts.is_absolute() or '..' in parts.parts or '\\' in relative
                    or ':' in relative or not re.fullmatch('[a-f0-9]{64}', value)):
                raise InstallError(f'Invalid locked file: {relative}')
        source = root / entry['source']
        if inventory(source) != files:
            raise InstallError(f'Source content differs from lock: {name}')
        entries.append((name, source.resolve(), files))
    if set(manifest_skills) != names:
        raise InstallError('Manifest and lock skill sets differ')
    source_names = {path.name for path in (root / 'skills').iterdir() if path.is_dir()}
    if source_names != names:
        raise InstallError('Source and lock skill sets differ')
    return lock, entries


def install(root, target, apply=False, mover=os.rename):
    lock, entries = read_bundle(root)
    target = Path(target).absolute()
    reject_links(target)
    target = target.resolve()
    if not target.is_dir():
        raise InstallError('Target must be an existing skill directory')
    # Never install over the source package or its ancestors/descendants.
    for _, source, _ in entries:
        if target == source or target in source.parents or source in target.parents:
            raise InstallError('Target overlaps a source skill directory')
    pending, reused = [], []
    for name, source, files in entries:
        destination = target / name
        if destination.exists() or destination.is_symlink():
            if inventory(destination) != files:
                raise InstallError(f'Existing skill differs; preserved: {name}')
            reused.append(name)
        else:
            pending.append((name, source, files))
    result = {'bundleVersion': lock['bundleVersion'], 'target': str(target),
              'reused': reused, 'install': [row[0] for row in pending],
              'status': 'preview', 'runtimeDiscovery': 'not-verified'}
    if not apply:
        return result
    guard = target / '.indie-game-install.lock'
    try:
        fd = os.open(guard, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise InstallError('Another install or stale guard exists; inspect before retry') from exc
    os.close(fd)
    committed, staging = [], None
    try:
        staging = Path(tempfile.mkdtemp(prefix='.indie-game-stage-', dir=target))
        for name, source, files in pending:
            shutil.copytree(source, staging / name)
            if inventory(staging / name) != files:
                raise InstallError(f'Staged content changed: {name}')
        for name, _, files in pending:
            destination = target / name
            if destination.exists() or destination.is_symlink():
                raise InstallError(f'Target changed during install: {name}')
            mover(staging / name, destination)
            committed.append((destination, files))
        for name, _, files in entries:
            if inventory(target / name) != files:
                raise InstallError(f'Installed verification failed: {name}')
        result['status'] = 'files-ready-activation-pending'
        return result
    except Exception as exc:
        preserved = []
        for destination, files in reversed(committed):
            # Only remove paths created by this invocation, still byte-identical.
            try:
                if inventory(destination) == files:
                    shutil.rmtree(destination)
                else:
                    preserved.append(str(destination))
            except (OSError, InstallError):
                preserved.append(str(destination))
        raise InstallError(f'Install failed: {exc}; externally changed paths preserved: {preserved}') from exc
    finally:
        if staging is not None:
            shutil.rmtree(staging)
        guard.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', required=True, type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(install(Path(__file__).resolve().parents[1], args.target, args.apply), indent=2))
    except (InstallError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.exit(1, f'{exc}\n')


if __name__ == '__main__':
    main()
