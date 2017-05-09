from ftw.builder import builder_registry
from ftw.builder.archetypes import ArchetypesBuilder
from ftw.builder.dexterity import DexterityBuilder
import ftw.simplelayout.tests.builders


class ContentPageBuilder(ArchetypesBuilder):

    portal_type = 'ContentPage'

builder_registry.register('content page', ContentPageBuilder)


class TextBlockBuilder(ArchetypesBuilder):
    portal_type = 'TextBlock'

builder_registry.register('text block', TextBlockBuilder)


class ListingBlockBuilder(ArchetypesBuilder):
    portal_type = 'ListingBlock'

builder_registry.register('listing block', ListingBlockBuilder)


class ExampleDxTypeBuilder(DexterityBuilder):
    portal_type = 'ExampleDxType'

builder_registry.register('example dx type', ExampleDxTypeBuilder)


class FormGenBuilder(ArchetypesBuilder):
    portal_type = 'FormFolder'

builder_registry.register('form folder', FormGenBuilder)


class SaveDataBuilder(ArchetypesBuilder):
    portal_type = 'FormSaveDataAdapter'

builder_registry.register('save data adapter', SaveDataBuilder)
