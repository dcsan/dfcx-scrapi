
ESCALATE_PHRASES = [
    # "Let me get you to someone who can help",
    # "Please hold while I connect you to someone",
    # "Let me transfer you to someone who can help",
    # "Please hold while I connect you to an agent",
    # "connect you to someone",
    "someone who can help",
    "transfer you to someone",
    "connect you to an agent",
    "Please hold while I connect you",
    "Let me get you to someone who can help."
]

# transitions that should register an escalation
ESC_TRANSITIONS = [
    # TRBL
    # 'page(TRBL::(Escalate) Troubleshooting)'
    '(Escalate) Troubleshooting)'
]

# some things a user can say to escalate
# ESCALATION_UTTERANCES = [
#     "dtmf_digits_0"
# ]

# if 'parameter filling' these guess if user said operator
OPERATOR_KEYWORDS = [
    'operator',
    'representative',
    'agent',
    "dtmf_digits_0",
    'customer service',
    '0, #',
    # 'tech support',
    'support',
]

# exist in the detail field when a user succeeds
TASK_COMPLETE = [
    'user task completed',
    'Thanks for calling CLIENTB',
    'Thank you for calling CLIENTB'
]

# detail - hangup
HANGUP_PHRASES = [
    'user drop off'
]


# CHANGEME - add your vague intents here
VAGUE_INTENTS = [
    'hid.vague-intent-1',
    'hid.vague-intent-2',
    'Default Welcome Intent',
    'Operator',
]
