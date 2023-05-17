# License: MIT
# Copyright © {% now 'utc', '%Y' %} Frequenz Energy-as-a-Service GmbH

"""{{cookiecutter.description}}.

TODO(cookiecutter): Add a more descriptive module description.
"""
{%- if cookiecutter.type != "api" %}


# TODO(cookiecutter): Remove this function
def delete_me(*, blow_up: bool = False) -> bool:
    """Do stuff for demonstration purposes.

    Args:
        blow_up: If True, raise an exception.

    Returns:
        True if no exception was raised.

    Raises:
        RuntimeError: if blow_up is True.
    """
    if blow_up:
        raise RuntimeError("This function should be removed!")
    return True
{%- endif %}
