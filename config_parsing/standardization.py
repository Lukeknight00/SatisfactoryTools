def standardize(value: str):
    return "_".join(value.replace("-", "_").replace(":", "").split()).lower()
