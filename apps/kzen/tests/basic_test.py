"""
testing real basic setup
"""

from config import base_config


def test_base_config():
    """stats"""
    kzen = base_config.read('kzen_config_doc')
    example_id = 'xxxxxxxxx_xxxxxE58qKQFXdh97TRfqRMpiEk0kxxxxx'

    assert len(kzen) == len(example_id), \
        "cannot read kzen_config_doc ID from base config"
