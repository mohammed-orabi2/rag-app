from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class RetrieverConfig:
    rewritten_query: str
    """
    the query on which to invoke the retriever on
    """

    search_params: Optional[dict] = field(default_factory=dict)
    """
    - a default value of empty dict
    - The naming convention of the keys inside this dict must match LangChain’s expectations,
      because internally the 'search_kwargs' dict is passed as-is (unpacked) into the 'as_retriever()' function.

    This dict may consist of two keys:
        - 'search_type': (str) search type of the retriever
        - 'search_kwargs': (dict) keyword args for the search function of the retriever (same naming convention as langchain)
        , including 'k' and 'filter'


    The logic of the retrievers is to only apply the search parameters, not creating or altering them
    """


class RetrieverInterface(ABC):
    """
    an interface for different types of retrievers, each applying its own logic in retrieving documents.
    """

    @abstractmethod
    def invoke(self, config: RetrieverConfig):
        pass

    @abstractmethod
    def multiple_invoke(self, config: RetrieverConfig):
        pass
