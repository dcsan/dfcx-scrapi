const graphTestDataV2 = [
    // { "group": "nodes", },
    {
        "data": {
            "cname": "BILL unexpected_charge",
            "weight": 18,
            "page": "Unexpected Charge",
            "type": "page",
            "flow": "BILL"
        }
    },
    {
        "data": {
            "cname": "BILL get_unexpected_charge",
            "weight": 3,
            "page": "Get Unexpected Charge",
            "type": "page",
            "flow": "BILL"
        }
    },
    {
        "data": {
            "cname": "BILL billing_video",
            "weight": 105,
            "page": "Billing Video",
            "type": "page",
            "flow": "BILL"
        }
    },
    {
        "data": {
            "cname": "BILL end_session",
            "weight": 87,
            "page": "End Session",
            "type": "page",
            "flow": "BILL"
        }
    },
    {
        "data": {
            "cname": "BILL bill_high_summary",
            "weight": 38,
            "page": "Bill High Summary",
            "type": "page",
            "flow": "BILL"
        }
    },
    { "group": "edges" },
    {
        "data": {
            "id": 620,
            "source": 927,
            "target": 927,
            "weight": 7,
            "label": "[7]-No Match",
            "type": "route"
        }
    },
    {
        "data": {
            "id": 621,
            "source": 927,
            "target": 929,
            "weight": 2,
            "label": "[2]-Parameter Filling",
            "type": "route"
        }
    },
    {
        "data": {
            "id": 630,
            "source": 929,
            "target": 954,
            "weight": 4,
            "label": "[4]-confirmation.no",
            "type": "route"
        }
    },
    {
        "data": {
            "id": 526,
            "source": 954,
            "target": 954,
            "weight": 8,
            "label": "[8]-No Match",
            "type": "route"
        }
    },
    {
        "data": {
            "id": 525,
            "source": 954,
            "target": 954,
            "weight": 33,
            "label": "[33]-No Input",
            "type": "route"
        }
    },
    {
        "data": {
            "id": 531,
            "source": 954,
            "target": 954,
            "weight": 1,
            "label": "[1]-hed bill_check_discount",
            "type": "route"
        }
    },
    {
        "data": {
            "id": 528,
            "source": 954,
            "target": 959,
            "weight": 3,
            "label": "[3]-confirmation.yes",
            "type": "route"
        }
    },
    {
        "data": {
            "id": 524,
            "source": 954,
            "target": 959,
            "weight": 2,
            "label": "[2]-No Input",
            "type": "route"
        }
    },
    {
        "data": {
            "id": 530,
            "source": 954,
            "target": 926,
            "weight": 1,
            "label": "[1]-support.repeat",
            "type": "route"
        }
    }
]


export default graphTestDataV2