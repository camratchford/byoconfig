def test_singleton_out_of_scope():
    from byoconfig.singleton import SingletonMetaclass
    from byoconfig.config import Config

    class SingletonConfigClass(Config, metaclass=SingletonMetaclass):
        class_attr_1 = 2

    singleton_out_of_scope = SingletonConfigClass(
        instance_attr_1=2, config_assign_attrs=True
    )
    assert singleton_out_of_scope.class_attr_1 == 2
    assert singleton_out_of_scope.instance_attr_1 == 2


def test_singleton_metaclass():
    from byoconfig.singleton import SingletonMetaclass
    from byoconfig.config import Config

    class SingletonConfigClass(Config, metaclass=SingletonMetaclass):
        class_attr_1 = 1

    singleton = SingletonConfigClass(instance_attr_1=1, config_assign_attrs=True)
    new_singleton = SingletonConfigClass()

    assert new_singleton.class_attr_1 == singleton.class_attr_1 == 1
    assert new_singleton.instance_attr_1 == singleton.instance_attr_1 == 1

    test_singleton_out_of_scope()
