def test_singletonness():
    """
    Any subsequent calls to SingletonConfig.__new__ should return the same instance
    """
    from byoconfig.singleton import SingletonConfig

    config = SingletonConfig()
    config.set_data({"var": "123"})

    config2 = SingletonConfig()
    # The underlying instance of config and config2 are the same instance
    assert config2.var == config.var

    config2.set_data({"var2": "abc"})
    # The properties are transitive in both directions
    assert config.var2 == "abc"


def test_singleton_scope():
    """
    Even from an entirely different scope, it should return the same instance
    """
    from byoconfig.singleton import SingletonConfig

    config = SingletonConfig()
    # Even a 2nd import should result in the same instance loaded with the previous values
    assert config.var == "123"
    assert config.var2 == "abc"


if __name__ == "__main__":
    test_singletonness()
    test_singleton_scope()
