from django.utils.module_loading import import_string

from mayan.apps.storage.utils import TemporaryDirectory

from ..backends.whoosh import WhooshSearchBackend
from ..literals import DEFAULT_SEARCH_BACKEND
from ..settings import setting_backend_arguments

default_search_backend = import_string(dotted_path=DEFAULT_SEARCH_BACKEND)


class TestSearchBackend(default_search_backend):
    """
    Test search backend dynamically generated from the default search
    backend. If the default backend is the Whoosh backend, a temporary
    folder will be created to store the search index. The temporary directory
    is automatically deleted by Python when all references are removed.

    This test search backend will only perform instance indexing and
    deindexing when called from a search test. This allows using the backend
    for search tests but avoids the indexing penalty for non search tests.

    It will also automatically insert the test object into the index
    before performing a call to the `search` method.
    """
    _test_view = None

    def __init__(self, *args, **kwargs):
        kwargs = setting_backend_arguments.value.copy()

        if self._test_view:
            if issubclass(default_search_backend, WhooshSearchBackend):
                self._temporary_directory = TemporaryDirectory()
                kwargs['index_path'] = self._temporary_directory.name

        super().__init__(*args, **kwargs)

    def deindex_instance(self, instance):
        if self._test_view:
            super().deindex_instance(instance=instance)

    def index_instance(self, instance):
        if self._test_view:
            super().index_instance(instance=instance)

    def search(self, *args, **kwargs):
        if self._test_view:
            # if running as part of a search test. Index the test object
            # before executing the search method.
            if self._test_view._test_search_index_object_name:
                self.index_instance(
                    instance=getattr(
                        self._test_view,
                        self._test_view._test_search_index_object_name
                    )
                )

        return super().search(*args, **kwargs)