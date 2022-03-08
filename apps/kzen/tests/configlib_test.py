"""testing config lib imports"""

from config import configlib
import logging

SET_NAME = 'BILL-coreset'


def test_agents():
    """can we load agents"""
    agents = configlib.refresh_agent_configs()
    # logging.warning('agents %s', agents)
    # logging.warning('df \n %s', len(agents.get('df')))
    assert agents['agent_configs'] > 5, "expected >5 agent configs"
