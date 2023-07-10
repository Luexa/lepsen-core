__all__ = [
    "markdown_iterator",
]


from collections.abc import Iterator
from importlib.abc import Traversable


def markdown_iterator(directory: Traversable) -> Iterator[tuple[str, Traversable]]:
    """
    Iterate over Markdown files in the provided package.

    The iterator yields a tuple of each Markdown file's basename and a
    Traversable object representing a file. Note that iteration recurses into
    subdirectories of the package, so it is preferable if the package's child
    directories do not contain markdown files with the same basename.

    Arguments:
    directory -- a Traversable object representing a directory
    """
    for resource in directory.iterdir():
        if resource.is_dir():
            yield from markdown_iterator(resource)
        elif resource.suffix == ".md":
            yield resource.stem, resource
