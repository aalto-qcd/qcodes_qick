import importlib
import pkgutil
import os


def import_submodules(module_name: str, module_path: str):
    for _, name, _ in pkgutil.iter_modules([module_path]):
        submodule_name = module_name + '.' + name
        submodule_path = os.path.join(module_path, name)
        importlib.import_module(submodule_name)
        if os.path.isdir(submodule_path):
            import_submodules(submodule_name, submodule_path)


def test_import_all_modules():
    import qcodes_qick

    import_submodules("qcodes_qick", qcodes_qick.__path__[0])
