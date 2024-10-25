import types
from typing import Generic, Type

from src.app.views import View, GenericView
from src.app.models import Model, GenericModel


class BaseController(Generic[GenericModel, GenericView]):
    __concrete__ = {}
    _t: tuple[Type[GenericModel], Type[GenericView]]

    def __class_getitem__(cls, key_t: type):
        cache = cls.__concrete__
        if c := cache.get(key_t, None):
            return c

        cache[key_t] = c = types.new_class(
            f"{cls.__name__}[{key_t[0].__name__},{key_t[1].__name__}]",
            (cls,),
            {},
            lambda ns: ns.update(_t=key_t),
        )

        return c

    def __init__(self, model: Model, view: View) -> None:
        self.root = view.root
        self.root_view = view
        self.root_model = model
        self._m, self._v = self._t

    @property
    def view(self) -> GenericView:
        return self.root_view[self._v]

    @property
    def model(self) -> GenericModel:
        return self.root_model[self._m]
