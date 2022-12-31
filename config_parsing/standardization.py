import re


def standardize(value: str):
    return "_".join(value.replace("-", "_").replace(":", "").replace(")", "").replace("(", "").split()).lower()


def get_class_name(value: str):
    native_class_pattern = r".*\.(\w+)'?"
    return re.match(native_class_pattern, value).group(1)
