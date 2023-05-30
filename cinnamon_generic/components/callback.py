from functools import partial
from pathlib import Path
from typing import Any, Dict, cast, Optional

from cinnamon_core.core.component import Component


class Callback(Component):
    """
    Generic ``Callback`` component.
    A ``Callback`` component defines execution flow hookpoints for flow customization and side effects.
    """

    def __init__(
            self,
            **kwargs
    ):
        super(Callback, self).__init__(**kwargs)
        self.component: Optional[Component] = None
        self.save_path: Optional[Path] = None

    def setup(
            self,
            component: Component,
            save_path: Path
    ):
        """
        Set-ups the ``Callback`` instance with a ``Component`` reference for quick attributes access and
        serialization save path.

        Args:
            component: a ``Component`` instance that exposes hookpoints for this ``Callback``
            save_path: path where to potentially save ``Callback`` side effects.
        """

        self.component = component
        self.save_path = save_path

    def run(
            self,
            hookpoint: Optional[str] = None,
            logs: Dict[str, Any] = None
    ):
        """
        Runs the ``Callback``'s specific hookpoint.
        If the ``Callback`` doesn't have the specified hookpoint, nothing happens.

        Args:
            hookpoint: name of the hookpoint method to invoke
            logs: optional arguments for the hookpoint
        """

        if hasattr(self, hookpoint):
            hookpoint_method = getattr(self, hookpoint)
            hookpoint_method(logs=logs)


class CallbackPipeline(Callback):
    """
    A pipeline ``Callback`` ``Component`` that executes multiple ``Callback`` in a sequential fashion.

    """

    def run(self,
            hookpoint: Optional[str] = None,
            logs: Dict[str, Any] = None
            ):
        """
        Runs each ``Callback``'s specific hookpoint.
        If a ``Callback`` doesn't have the specified hookpoint, nothing happens.

        Args:
            hookpoint: name of the hookpoint method to invoke
            logs: optional arguments for the hookpoint
        """

        for callback in self.callbacks:
            callback.run(hookpoint=hookpoint,
                         logs=logs)


def hookpoint_guard(
        func,
        hookpoint='on_fit'
):
    """
    A decorator to enable ``Callback``'s hookpointing
    Args:
        func: the function to be decorated
        hookpoint: the ``Callback``'s base hookpoint to be invoked. In particular, two different hookpoints
        will be called
        - *hookpoint*_begin
        - *hookpoint*_end

        For instance, if ``hookpoint = 'on_fit'``, the following execution flow is considered:
        - ``Callback.on_fit_begin(...)``
        - func(...)
        - ``Callback._on_fit_end(...)

    Returns:
        The decorated method with specified ``Callback``'s hookpoint.
    """

    start_hookpoint = f'{hookpoint}_begin'
    end_hookpoint = f'{hookpoint}_end'

    def func_wrap(
            *args,
            **kwargs
    ):
        callbacks = None
        if 'callbacks' in kwargs:
            callbacks = kwargs['callbacks']
            callbacks = cast(CallbackPipeline, callbacks)

        if callbacks is not None:
            callbacks.run(hookpoint=start_hookpoint)

        res = func(*args, **kwargs)

        if callbacks is not None:
            callbacks.run(hookpoint=end_hookpoint,
                          logs=res)

        return res

    return func_wrap


def guard(
        hookpoint='on_fit'
):
    """
    A decorator to mark a ``Callback`` hookpoints.

    Args:
        hookpoint: the ``Callback``'s base hookpoint to be invoked. In particular, two different hookpoints
        will be called
        - *hookpoint*_begin
        - *hookpoint*_end

        For instance, if ``hookpoint = 'on_fit'``, the following execution flow is considered:
        - ``Callback.on_fit_begin(...)``
        - func(...)
        - ``Callback._on_fit_end(...)

    Returns:
        The decorated method with specified ``Callback``'s hookpoint.
    """

    return partial(hookpoint_guard, hookpoint=hookpoint)


__all__ = ['Callback', 'CallbackPipeline', 'guard']
