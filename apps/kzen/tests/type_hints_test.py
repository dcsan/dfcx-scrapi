"""
testing type hinting
"""


def echo(msg: str):
    """simple echo"""
    assert isinstance(msg, str), 'Argument of wrong type!'
    print(msg)


def test_hints():
    """hints"""
    value: int = 10
    echo(f'value {value}')
