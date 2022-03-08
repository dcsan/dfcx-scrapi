
const graphTestData = [
    {
        data: {
            id: 'start',
            label: "start",
            count: 50,
            color: 'green',
            // shape: 'square'
        },
    },
    {
        data: {
            id: 'bill',
            label: "bill",
            count: 2
        },
    },
    {
        data: {
            id: 'high',
            label: 'high',
            count: 2
        },
    }, {
        data: {
            id: 'charge',
            label: 'charge',
            count: 5
        }
    }, {
        data: {
            id: 'end',
            label: 'end',
            count: 10,
            color: 'red',
            // shape: 'square'
        }
    },

    // links
    {
        data: {
            source: 'start',
            target: 'bill',
            label: 'edge 1-2',
            weight: 10
        }
    }, {
        data: {
            source: 'start',
            target: 'high',
            label: 'route',
            weight: 5
        }
    }, {
        data: {
            source: 'high',
            target: 'end',
            label: 'route',
            weight: 2
        }
    }, {
        data: {
            source: 'bill',
            target: 'charge',
            label: 'route',
            weight: 2
        }
    }, {
        data: {
            source: 'charge',
            target: 'end',
            label: 'route',
            weight: 2
        }
    }, {
        data: {
            source: 'end',
            target: 'charge',
            label: 'route',
            weight: 2
        }
    }
]

export default graphTestData
