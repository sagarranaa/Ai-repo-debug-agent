import pytest

from agent.tools.file_tools import list_files, read_file


def test_lists_checkout_file():
    assert "shop/checkout.py" in list_files()


def test_reads_checkout_with_line_numbers():
    result = read_file("shop/checkout.py")

    assert result["path"] == "shop/checkout.py"
    assert "def checkout(" in result["content"]
    assert result["content"].startswith("1: ")


def test_blocks_access_outside_demo():
    with pytest.raises(ValueError, match="not allowed"):
        read_file("../.env")


def test_limits_lines_per_call():
    with pytest.raises(ValueError, match="120"):
        read_file("shop/checkout.py", start_line=1, end_line=500)