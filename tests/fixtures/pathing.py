from pathlib import Path

this_dir = Path(__file__).parent
fixtures_dir = this_dir

byoconfig_root = this_dir.parent.parent
examples_dir = byoconfig_root / 'extras' / 'examples'

output_dir = this_dir / 'output'
