from config.base_config import BaseConfig


testConfig: BaseConfig = {
    'debug': True,
    'gcp_project': 'CLIENTA-aam-external',
    'creds_path': 'config/dc-CLIENTA-sa1.json',
    'upstream_table_id': 'CLIENTA.upstream_table',
    'raw_table_id': 'CLIENTA.dataset.raw_table',
    'dataset': 'scoobi',

    # rename from raw -> chat_log columns
    'rename_columns': {
        'position': 'turn',
        'page_display_name': 'page',
        'intent_display_name': 'intent',
        'session_contained': 'contained',
        "session_abandoned": 'abandoned',
        "session_live_agent_handoff": 'handoff',
        "live_agent_escalation": 'escalation',
        "current_sprint_number": 'sprint_number',
        "intent_is_fallback": "fallback",
        'message_flow_display_name': 'flow',
        'intent_confidence_score': 'score',
    },

    'role_type_map': {
        'AUTOMATED_AGENT': 'AGENT',
        'END_USER': 'CUSTOMER'
    },
    'sheets': {
        'TestSheet': '1oelvCrOPyxXVXa4ovLWJkE2uNSi_54NN3Zchuj_7bZc'
    }
}
