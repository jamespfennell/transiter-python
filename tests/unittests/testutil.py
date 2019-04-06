import inspect
import unittest
import unittest.mock as mock

from nose.tools import nottest


@nottest
def TestCase(module):

    class ActualTestCase(unittest.TestCase):

        _importModuleDictCache = None

        def _getImportedModulesDict(self):
            if self._importModuleDictCache is None:
                self._importModuleDictCache = {}
            module_name = getattr(module, '__name__')
            if module_name not in self._importModuleDictCache:
                self._importModuleDictCache[module_name] = {}
                for name, obj in module.__dict__.items():
                    if name[:2] == '__':
                        continue
                    if inspect.ismodule(obj):
                        self._importModuleDictCache[module_name][obj.__name__] = name
            return self._importModuleDictCache[module_name]

        def mockModuleAttribute(self, variable_name):
            patcher = mock.patch.object(
                module,
                variable_name
            )
            mocked_module = patcher.start()
            self.addCleanup(patcher.stop)
            return mocked_module

        def mockImportedModule(self, imported_module):
            module_global_name = getattr(imported_module, '__name__')
            module_local_name = self._getImportedModulesDict()[module_global_name]
            return self.mockModuleAttribute(module_local_name)

    return ActualTestCase


def patch_function(func):
    string = '{}.{}'.format(func.__module__, func.__name__)
    return mock.patch(string)


