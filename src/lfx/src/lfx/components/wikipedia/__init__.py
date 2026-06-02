# Wikipedia 组件包，提供 Wikipedia 和 Wikidata 知识库查询功能
from .wikidata import WikidataComponent
from .wikipedia import WikipediaComponent

__all__ = ["WikidataComponent", "WikipediaComponent"]
