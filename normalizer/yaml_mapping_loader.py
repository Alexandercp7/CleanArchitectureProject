import yaml
from pathlib import Path
from normalizer.mapping_loader import MappingLoader


class YamlMappingLoader(MappingLoader):
    def __init__(self, mappings_dir: Path) -> None:
        self.mappings_dir = mappings_dir

    def load(self, source_name: str) -> dict[str, str]:
        path = self.mappings_dir / f"{source_name}.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))