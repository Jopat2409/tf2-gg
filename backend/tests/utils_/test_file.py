from utils.file import TempFile, ConstFile, read_or_create, read_required
import pytest
import json
import os

def test_read_or_create():
    # Test works with file that does not exist
    test1 = read_or_create("tests\\test_data\\doesnt_exist.json", {})
    assert test1 == {}
    assert os.path.isfile("tests\\test_data\\doesnt_exist.json")
    os.remove("tests\\test_data\\doesnt_exist.json")

    test2 = read_or_create("tests\\test_data\\test.json", {})
    assert "data" in test2.keys()
    assert "testvalue1" in test2["data"]
    assert "testvalue2" in test2["data"]

def test_read_required():

    # Test reading a file that does not exist returns none
    assert read_required("tests\\test_data\\lasjhfljashfkljashf.json") is None
    assert read_required("tests\\test_data\\lasjhfljashfkljashf.json", json=True) is None

    # test reading a file that does exist returns the correct data
    assert """{"data": ["testvalue1", "testvalue2"]""" in read_required("tests\\test_data\\test.json")
    assert "data" in read_required("tests\\test_data\\test.json", json=True)

    # Test reading a file with unicode characters works
    assert "Σ" in read_required("tests\\test_data\\test_utf8漢.json", encoding='utf-8')
    assert "Σ" in read_required("tests\\test_data\\test_utf8漢.json", json=True, encoding='utf-8')["data"]

    # Test incorrect encoding with different values of Throws
    with pytest.raises(LookupError):
        read_required("tests\\test_data\\test.json", encoding='aljshfkjasgfkaghslkj', throws=True)
    assert read_required("tests\\test_data\\test.json", encoding='ashfkjsaflkja', throws=False) is None

def test_tempfile():
    path = "tests\\test_data\\skibidi_test.json"
    with TempFile(path):
        assert os.path.isfile(path)
    assert not os.path.isfile(path)

    with pytest.raises(FileExistsError):
        with TempFile("tests\\test_data\\test.json"):
            pass

def test_constfile():
    path = "tests\\test_data\\test.json"
    with ConstFile(path) as f:
        test_data = f.read(json=True)
        test_data["test_removed_data"] = "Hello"

        f.write(test_data, json=True)
        assert "test_removed_data" in f.read(json=True)

    with open(path, "r") as f:
        assert "test_removed_data" not in json.load(f)

    with pytest.raises(FileNotFoundError):
        with ConstFile("data\\ssaklfjashfjkghsakjfljsahflkaj.json"):
            pass
