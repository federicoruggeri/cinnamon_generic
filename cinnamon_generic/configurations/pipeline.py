from typing import List, Optional, Type, Set, Iterable, Any

from cinnamon_core.core.configuration import Configuration


class OrderedPipelineConfig(Configuration):

    def add_pipeline_component(
            self,
            name: str,
            value: Optional[Any] = None,
            type_hint: Optional[Type] = None,
            description: Optional[str] = None,
            tags: Optional[Set[str]] = None,
            is_required: bool = False,
            build_type_hint: Optional[Type] = None,
            variants: Optional[Iterable] = None,
            order: Optional[int] = None
    ):
        tags = tags.union({'pipeline'}) if tags is not None else {'pipeline'}
        self.add_short(name=name,
                       value=value,
                       type_hint=type_hint,
                       description=description,
                       tags=tags,
                       is_required=is_required,
                       build_type_hint=build_type_hint,
                       variants=variants,
                       is_registration=True)
        if 'ordering' not in self:
            self.add_short(name='ordering',
                           value=[],
                           type_hint=List[str],
                           is_required=True,
                           description="A list of Parameter names in Configuration that point to pipeline components."
                                       "This list is used to retrieve the correct order of execution of pipeline "
                                       "components: the specified ordering in this Parameter is the execution order.")

        if order is None:
            self.ordering.append(name)
        else:
            self.ordering.insert(order, name)