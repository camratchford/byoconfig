import json

a_test_secret_data = {
    "test_string_key": "test",
    "test_int_key": 3,
    "test_double_key": 1.1,
    "test_dict_key": {"subkey": 1},
    "test_list_key": [1, 2, 3]
}

a_test_secret = json.dumps(a_test_secret_data)