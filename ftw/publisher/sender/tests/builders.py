from ftw.builder import builder_registry
from ftw.builder.archetypes import ArchetypesBuilder
from ftw.builder.dexterity import DexterityBuilder
import ftw.simplelayout.tests.builders


try:
    import ftw.contentpage.tests.builders
except ImportError:
    # Don't bother about ftw.contentpage, since it's a legay package.
    pass


class ExampleDxTypeBuilder(DexterityBuilder):
    portal_type = 'ExampleDxType'

builder_registry.register('example dx type', ExampleDxTypeBuilder)


class FormGenBuilder(ArchetypesBuilder):
    portal_type = 'FormFolder'

builder_registry.register('form folder', FormGenBuilder)


class SaveDataBuilder(ArchetypesBuilder):
    portal_type = 'FormSaveDataAdapter'

builder_registry.register('save data adapter', SaveDataBuilder)
