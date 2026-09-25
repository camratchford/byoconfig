import threading
import time

from byoconfig import BYOConfig, SingletonMetaclass


def test_repeated_calls_return_same_instance():
    class AppConfig(BYOConfig, metaclass=SingletonMetaclass):
        host: str = "localhost"

    assert AppConfig() is AppConfig()


def test_state_is_shared_between_calls():
    class AppConfig(BYOConfig, metaclass=SingletonMetaclass):
        host: str = "localhost"

    AppConfig().set("host", "example.com")

    assert AppConfig().get("host") == "example.com"


def test_separate_classes_have_separate_instances():
    class FirstConfig(BYOConfig, metaclass=SingletonMetaclass):
        host: str = "localhost"

    class SecondConfig(BYOConfig, metaclass=SingletonMetaclass):
        host: str = "localhost"

    assert FirstConfig() is not SecondConfig()


def test_subclass_created_after_parent_has_own_instance():
    class ParentConfig(BYOConfig, metaclass=SingletonMetaclass):
        host: str = "localhost"

    class ChildConfig(ParentConfig):
        port: int = 80

    parent = ParentConfig()
    child = ChildConfig()

    assert child is not parent
    assert isinstance(child, ChildConfig)
    assert child is ChildConfig()


def test_subclass_created_before_parent_has_own_instance():
    class ParentConfig(BYOConfig, metaclass=SingletonMetaclass):
        host: str = "localhost"

    class ChildConfig(ParentConfig):
        port: int = 80

    child = ChildConfig()
    parent = ParentConfig()

    assert child is not parent
    assert isinstance(parent, ParentConfig)
    assert not isinstance(parent, ChildConfig)


def test_init_runs_once():
    initialization_count = 0

    class CountingConfig(metaclass=SingletonMetaclass):
        def __init__(self, name):
            nonlocal initialization_count
            initialization_count += 1
            self.name = name

    first = CountingConfig("first")
    second = CountingConfig("second")

    assert initialization_count == 1
    assert second.name == "first"
    assert first is second


def test_concurrent_calls_create_one_instance():
    thread_count = 16
    initialization_count = 0
    barrier = threading.Barrier(thread_count)
    instances = []

    class SlowConfig(metaclass=SingletonMetaclass):
        def __init__(self):
            nonlocal initialization_count
            initialization_count += 1
            time.sleep(0.01)

    def create_instance():
        barrier.wait()
        instances.append(SlowConfig())

    threads = [threading.Thread(target=create_instance) for _ in range(thread_count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert initialization_count == 1
    assert len(instances) == thread_count
    assert all(instance is instances[0] for instance in instances)


def test_singleton_can_create_another_singleton_during_init():
    class DatabaseConfig(metaclass=SingletonMetaclass):
        pass

    class AppConfig(metaclass=SingletonMetaclass):
        def __init__(self):
            self.database = DatabaseConfig()

    instances = []
    thread = threading.Thread(target=lambda: instances.append(AppConfig()), daemon=True)
    thread.start()
    thread.join(timeout=2)

    assert not thread.is_alive()
    assert instances[0].database is DatabaseConfig()
