"""Package source without credentials, databases, caches or build dependencies."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
root = Path(__file__).resolve().parents[1]
output = root / 'artifacts' / 'atoms-framework.zip'
excluded = {'.git','.runtime','.venv','node_modules','dist','__pycache__','.pytest_cache','artifacts','.DS_Store'}
with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if not path.is_file() or any(part in excluded for part in relative.parts):
            continue
        if path.name.startswith('.env') and path.name != '.env.example':
            continue
        if path.name in ('requirements-source.json','requirements-latest.json') or path.suffix in ('.log','.zip','.pyc','.tsbuildinfo'):
            continue
        if 'evidence' in relative.parts and path.suffix=='.txt':
            import re
            content=re.sub(r'(signature=)[0-9a-f]+',r'\1[redacted]',path.read_text(encoding='utf-8'))
            archive.writestr('atoms/'+relative.as_posix(),content)
        else:
            archive.write(path, 'atoms/' + relative.as_posix())
print(str(output))
print(f'{output.stat().st_size} bytes')
with ZipFile(output) as archive:
    names=archive.namelist()
    assert not any('/.env' == name[-5:] or '/.runtime/' in name or '/node_modules/' in name for name in names)
    print(f'{len(names)} source files; credentials and runtime data excluded')
