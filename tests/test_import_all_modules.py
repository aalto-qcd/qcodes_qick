import importlib
import pkgutil
from pathlib import Path


def import_submodules(module_name: str, module_path: Path):
    for _, name, _ in pkgutil.iter_modules([str(module_path)]):
        submodule_name = module_name + "." + name
        submodule_path = module_path / name
        importlib.import_module(submodule_name)
        if submodule_path.is_dir():
            import_submodules(submodule_name, submodule_path)


def test_import_all_modules():
    import qcodes_qick

    import_submodules("qcodes_qick", Path(qcodes_qick.__path__[0]))
