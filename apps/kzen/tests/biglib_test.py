"""
testing real basic setup
"""

from cxutils import biglib


def test_base_config():
    """stats"""
    check = biglib.fix_timestamp('5/26/2021 19:13:00')
    assert check == '2021-05-26 19:13:00', "failed to convert timestamp"
    check1 = biglib.fix_timestamp('5/26/2021 19:13:01')
    assert check1 == '2021-05-26 19:13:01', "failed to convert timestamp"

    # when you dont get seconds :(
    check1 = biglib.fix_timestamp('5/26/2021 19:13')
    assert check1 == '2021-05-26 19:13:00', "failed to convert timestamp"

    check1 = biglib.fix_timestamp('5/26/2021 9:07')
    assert check1 == '2021-05-26 09:07:00', "failed to convert timestamp"
