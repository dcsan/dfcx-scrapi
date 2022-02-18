from config.base_config import BaseConfig


# rename from raw -> chat_log columns

sharedConfig: BaseConfig = {

    'rename_columns': {
        'page_display_name': 'page',
        'intent_display_name': 'intent',
        'message_flow_display_name': 'flow',

        # who named this stuff? ok lets keep the defaults
        # "current_sprint_number": 'sprint',
        # 'position': 'turn',

        'session_contained': 'contained',
        "session_abandoned": 'abandoned',
        "session_live_agent_handoff": 'escalated',
        "match_confidence": "confidence",

        # what is this column?
        # "live_agent_handoff": 'escalated',

        "intent_is_fallback": "fallback",
        'message_flow_display_name': 'flow',

        # CLIENT-A only
        # "current_sprint_number": 'sprint_number',
        # "live_agent_escalation": 'escalation',
        # 'intent_confidence_score': 'score',
        # 'match_confidence': 'confidence'
    },

    'reorder_columns': [
        'current_sprint_number',
        'session_id',
        'position',
        'is_start',
        'is_end',

        'use_case',
        'role',
        'flow',
        'page_source',
        'content',
        'intent_target',
        'intent_last',
        'intent_detail',
        'page_target',

        'abandoned',
        'escalated',
        'contained',

        'abandoned_check',
        'operator_check',
        'escalated_check',
        'tc_check',

        'exit',
        'detail',
        'tc',
        'reason',

        'no_input_check',
        'no_match_check',

        'page_path',
        'page_link',
        'intent',
        'match_type',
        'match_target',
        'confidence',
        'page',
    ],

    'role_type_map': {
        'AUTOMATED_AGENT': 'AGENT',
        'END_USER': 'CUSTOMER'
    },

}
