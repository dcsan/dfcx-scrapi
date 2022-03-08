interface IBucket {
    dis_id: number
    phrases: string[]
    intents: string[]
}

interface IBucketGame {
    set_name: string
    disambigs: IBucket[]
}

const rawBuckets: IBucketGame = {
    'set_name': 'game2',
    'disambigs': [
        {
            'dis_id': 0,
            'intents': [
                'head_intent.intent1',
                'head_intent.intent2',
                'head_intent.intent3',
                'head_intent.intent4',
            ],
            'phrases': [
                'test phrase one',
                'test phrase two',
                'test phrase three',
                'test phrase four',
            ]
        },
        {
            'dis_id': 1,
            'intents': [
                'head_intent.intent1',
                'head_intent.intent2',
                'head_intent.intent3',
                'head_intent.intent4',
            ],
            'phrases': [
                'test phrase one',
                'test phrase two',
                'test phrase three',
                'test phrase four',
            ]
        },
        {
            'dis_id': 2,
            'intents': [
                'head_intent.intent1',
                'head_intent.intent2',
                'head_intent.intent3',
                'head_intent.intent4',
            ],
            'phrases': [
                'test phrase one',
                'test phrase two',
                'test phrase three',
                'test phrase four',
            ]
        },
        {
            'dis_id': 3,
            'intents': [
                'head_intent.intent1',
                'head_intent.intent2',
                'head_intent.intent3',
                'head_intent.intent4',
            ],
            'phrases': [
                'test phrase one',
                'test phrase two',
                'test phrase three',
                'test phrase four',
            ]
        },
    ]
}

export {
    rawBuckets
}

export type { IBucket, IBucketGame }
