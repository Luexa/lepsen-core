__all__ = [
    "OrderDependentFeatureDefinition",
    "FeatureDeletionAttempt",
    "ConflictingFeatureValues",
    "NontrivialFeaturePath",
    "FeatureStorage",
]


from collections.abc import Iterator, Iterable, MutableMapping
from typing import Optional, Union
from dataclasses import dataclass, field

from beet import Context

from nbtlib import (
    # NBT path data types.
    Path,
    NamedKey,

    # NBT data types.
    Base,
    Byte,
    Compound,
)

from .coerce_nbt import coerce_nbt_value, NbtCoerceable


@dataclass
class OrderDependentFeatureDefinition(KeyError):
    """
    Base class for errors caused by order-dependent operations on :class:`FeatureStorage`.
    """

    __slots__ = ("path",)

    path: Path

    def __init__(self, message: str):
        super().__init__(message)


@dataclass
class FeatureDeletionAttempt(OrderDependentFeatureDefinition):
    """
    Raised when an attempt is made to delete a feature from :class:`FeatureStorage`.

    This is not allowed as features are meant to be additive and not depend on
    the order in which they are defined.
    """

    __slots__ = ()

    def __init__(self, path: Path):
        super().__init__(
            f"Attempt to delete feature {path} from feature storage",
        )
        self.path = path


@dataclass
class ConflictingFeatureValues(OrderDependentFeatureDefinition):
    """
    Raised when an attempt is made to update an existing value in class:`FeatureStorage`.

    This is not allowed as features are meant to be additive and not depend on
    the order in which they are defined.
    """

    __slots__ = ("conflicting_path", "old_value", "new_value")

    conflicting_path: Path
    old_value: Optional[Base]
    new_value: Base

    def __init__(
        self,
        *,
        target_path: Path,
        conflicting_path: Path,
        old_value: Optional[Base],
        new_value: Base,
    ):
        base_text = f"Attempt to define a feature ({target_path!r}, {new_value!r})"
        if old_value is None:
            super().__init__(f"{base_text} over an existing feature container")
        else:
            super().__init__(
                f"{base_text} that would conflict with existing feature "
                f"({conflicting_path!r}, {old_value!r})",
            )
        self.path = target_path
        self.conflicting_path = conflicting_path
        self.old_value = old_value
        self.new_value = new_value


@dataclass
class NontrivialFeaturePath(OrderDependentFeatureDefinition):
    """
    Raised when a feature path contains compound matching or list indices.

    This is not allowed as these paths can expand to a varying number of sub-paths
    depending on the order in which feature values are defined.
    """

    __slots__ = ()

    def __init__(self, path: Path):
        super().__init__(
            "Attempt to use path containing array indices and/or compound "
            f"matches: {path}",
        )
        self.path = path


@dataclass(slots=True)
class FeatureStorage(MutableMapping[Union[str, Path], Base]):
    """
    Incrementally populated NBT compound used to generate pack metadata.

    Features are added by specifying NBT paths and corresponding values for
    each feature. To ensure that the resulting NBT compound is identical
    regardless of the order in which features are added, it is an error to
    define the same feature twice unless the existing value is identical to
    the new value (but relying on this behavior is discouraged).

    Note that no error is raised if these rules are bypassed by accessing NBT
    values directly; for this reason, it is recommended to perform all operations
    by indexing this data structure with NBT path objects or strings.

    The constructor takes an optional :class:`Context` parameter to allow for an
    instance of this class to be referenced at any point during the pipeline.
    The parameter is discarded and only serves to ensure the call signature of
    the constructor is correct.
    """

    compound: Compound
    container_paths: set[Path] = field(repr=False)

    def __init__(self, ctx: Optional[Context] = None):
        self.compound = Compound()
        self.container_paths = set()

    def __getitem__(self, key: Union[str, Path]) -> Base:
        if isinstance(key, str):
            key = Path(key)
        return self.compound[key]

    def __setitem__(self, key: Union[str, Path], value: NbtCoerceable):
        if isinstance(key, str):
            key = Path(key)

        # Paths that reference array indices or compound structures could evaluate
        # to a varying number of elements depending on the order in which features
        # are defined.
        for path_component in key:
            if not isinstance(path_component, NamedKey):
                raise NontrivialFeaturePath(key)

        # Allow simple scalars and Python lists and dictionaries to be used as
        # feature values by wrapping them as NBT tags if this has not already
        # been done.
        value = coerce_nbt_value(value)

        # An empty path refers to the top level compound, which should not be
        # overwritten under any circumstances.
        if not key:
            raise ConflictingFeatureValue(
                target_path=key,
                conflicting_path=key,
                old_value=self.compound,
                new_value=value,
            )

        # Add the feature to storage, recursively creating any missing compounds.
        # Raise an error if any feature values would conflict with each other.
        container = self.compound
        current_path = Path.from_accessors()
        num_components = len(key)
        for n, path_component in enumerate(key, start=1):
            current_path = current_path[path_component.key]
            current_item = container.get(path_component.key)
            if current_item is not None:
                is_container = current_path in self.container_paths
                if n < num_components:
                    if is_container:
                        container = current_item
                        continue
                elif is_container:
                    raise ConflictingFeatureValues(
                        target_path=key,
                        conflicting_path=current_path,
                        old_value=None,
                        new_value=value,
                    )
                elif value == current_item:
                    continue
                raise ConflictingFeatureValues(
                    target_path=key,
                    conflicting_path=current_path,
                    old_value=current_item,
                    new_value=value,
                )
            elif n < num_components:
                current_item = Compound()
                self.container_paths.add(current_path)
                container[path_component.key] = current_item
                container = current_item
            else:
                container[path_component.key] = value

    def __delitem__(self, key: Union[str, Path]):
        if isinstance(key, str):
            key = Path(key)
        raise FeatureDeletionAttempt(key)

    def __iter__(self) -> Iterator[str]:
        return iter(self.compound)

    def __len__(self) -> int:
        return len(self.compound)

    def __call__(self, feature: Union[str, Path], value: NbtCoerceable = Byte(1)):
        self[feature] = value
