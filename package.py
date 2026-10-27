"""Validate core package references and build an update ZIP. Python 3.10+."""
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parent
plugin = root / 'plugin'
a = json.loads((plugin / 'plugin.json').read_text())
b = json.loads((plugin / '.codex-plugin/plugin.json').read_text())
assert a['$schema'] == 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json'
assert a['name'] == b['name'] and a['version'] == b['version']
interface = a['extensions']['com.openai']['interface']
assert interface == b['interface'], 'Synchronize both manifests'
assert len(interface['shortDescription']) <= 30
for key in ('logo', 'composerIcon'):
    asset = (plugin / interface[key]).resolve()
    assert asset.is_relative_to(plugin.resolve()) and asset.is_file(), key
assert (plugin / 'skills/instructions/SKILL.md').read_text().startswith('---\n')
output = root / 'chefbot-plugin.zip'
with ZipFile(output, 'w', ZIP_DEFLATED, strict_timestamps=False) as archive:
    for path in sorted(plugin.rglob('*')):
        if path.is_file():
            assert not path.is_symlink(), path
            archive.write(path, path.relative_to(plugin))
print(output)
