__all__ = ["BYOConfigError"]


class BYOConfigError(ValueError):
    """Subclass of ValueError with the following additional properties:
    args:
        msg:           The unformatted error message
        instance_name: The name of which VariableSource instance raised the error
    """

    def __init__(self, msg, instance):
        errmsg = f"{msg}"
        super().__init__(self, errmsg)
        self.msg = msg
        self.instance = instance.name

    def __reduce__(self):
        return self.__class__, (self.msg, self.instance)
