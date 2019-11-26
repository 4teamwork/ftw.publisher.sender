from ftw.builder import builder_registry
from ftw.builder.archetypes import ArchetypesBuilder
from ftw.builder.dexterity import DexterityBuilder
from ftw.publisher.sender.utils import IS_PLONE_4
import ftw.simplelayout.tests.builders  # noqa


if IS_PLONE_4:
    import ftw.contentpage.tests.builders  # noqa


class ExampleDxTypeBuilder(DexterityBuilder):
    portal_type = 'ExampleDxType'


builder_registry.register('example dx type', ExampleDxTypeBuilder)


class FormGenBuilder(ArchetypesBuilder):
    portal_type = 'FormFolder'


builder_registry.register('form folder', FormGenBuilder)


class SaveDataBuilder(ArchetypesBuilder):
    portal_type = 'FormSaveDataAdapter'


builder_registry.register('save data adapter', SaveDataBuilder)
