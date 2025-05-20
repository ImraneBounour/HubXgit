import os


def get_env_variable(variable_name: str):
    try:
        value = os.environ[variable_name]
        return value
    except KeyError:
        raise EnvironmentError(
            f"The environment variable '{variable_name}' is not set."
        )
