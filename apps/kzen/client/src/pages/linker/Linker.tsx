import * as React from 'react'
import {
    // useEffect,
    useState, useEffect
}
    from 'react';
import Select from "react-select";
import { Chart } from "react-google-charts";

import TextField from '@material-ui/core/TextField';
// import Container from '@material-ui/core/Container';
import Button from '@material-ui/core/Button';
import Snackbar from '@material-ui/core/Snackbar';
import MuiAlert from '@material-ui/lab/Alert';

import TitleBox from '../../components/TitleBox'
import AppConfig from '../../utils/AppConfig'
import NetLib from '../../utils/NetLib'
import SimsTable from './SimsTable'
// // import ItemList from './ItemList'
// // import BaseItem from './BaseItem'
// import ItemList from "../tuner/ItemList";
// import BaseItem from "../tuner/BaseItem";

import './linker.css'

type Opt = {
    label: string
    value: string
}

type SimItem = {
    intent1?: string
    intent2?: string
    use?: number
    lev?: number
    text1?: string
    text2?: string
}

const tempData = {
    agent_name: '',
    set_name: '',
    // as sim items
    item_list: [],
    items: [
        {
            utterance: 'loading',
            intent: 'loading',
            text2: 'loading',
            intent2: 'loading',
            sim_count: 0
        }
    ]
}

const baseModelOptions: Opt[] = [
    { label: 'small', value: 'sm' },
    { label: 'medium', value: 'md' },
    { label: 'large', value: 'lg' },
    { label: 'universal SE', value: 'use' },
]

function Alert(props) {
    return <MuiAlert elevation={6} variant="filled" {...props} />;
}

function Linker() {
    const [msg, setMsg] = useState('loading');
    const [loading, setLoading] = useState(false)
    const loadingMsg: Opt = { label: 'select...', value: 'loading' }
    const [threshold, setThreshold] = useState(0.7)

    //--- left ----
    const [leftData, setLeftData] = useState([loadingMsg])
    const [leftOptions, setLeftOptions] = useState([loadingMsg])
    const [menuLeft, setMenuLeft] = useState(loadingMsg);

    // --- right
    const [rightData, setRightData] = useState([loadingMsg])
    const [rightOptions, setRightOptions] = useState([loadingMsg])
    const [menuRight, setMenuRight] = useState(loadingMsg);

    // sankey
    // const testChartData = [
    //     ['From', 'To', 'Weight'],
    //     ['A', 'B', 5],
    //     ['A', 'C', 3],
    //     ['B', 'C', 1],
    // ]
    const baseSimsData: [SimItem] = [{}]
    const [sankeyData, setSankeyData] = useState([])
    const [sankeyReady, setSankeyReady] = useState(false)
    const [simsData, setSimsData] = useState(baseSimsData)
    const [selection, setSelection] = useState('selection') // name of picked item on sankey

    const [modelType, setModelType] = useState(baseModelOptions[1].value)

    // intents
    // const [leftData, setLeftData] = useState(tempData)
    // const [pickedIntent, setPickedIntent] = useState(-1)

    // phrases
    // const [rightData, setRightData] = useState(tempData)
    // const [pickedPhrase, setPickedPhrase] = useState(-1)

    // sim
    // const [simData, setSimData] = useState(tempData)
    // const [pickedSim, setPickedSim] = useState(-1)

    // popover
    // const [anchorEl, setAnchorEl] = React.useState(null);
    // const popOpen = Boolean(anchorEl);

    const sample = 0

    // TODO - fetch dynamic?
    useEffect(() => {
        // AppConfig.load('agents', setAgentData)
        AppConfig.load('gdocs', setLeftData)
        AppConfig.load('gdocs', setRightData)
    }, [])

    useEffect(() => {
        console.log('leftData cg=>', leftData)
        const opts: any = leftData.map((item: any) => {
            return {
                label: item.cname,
                value: item.cname
            }
        })
        setLeftOptions(opts)
        setMenuRight(opts[0])
        setMsg('ready')
    }, [leftData])

    // loaded data options
    useEffect(() => {
        const opts: any = rightData.map((item: any) => {
            return {
                label: item.cname,
                value: item.cname
            }
        })
        // console.log('update', opts)
        setRightOptions(opts)
        // TODO - update menu
        setMenuLeft(opts[0])
        setMsg('ready')
    }, [rightData])

    const loadSims = () => {
        const url = `/api/tuner/load/sankey?left=${menuLeft.value}&right=${menuRight.value}&sample=${sample}`
        showStatus('load sankey: ' + url, { loading: true })
        fetch(url).then(NetLib.handleResponse)
            .then(data => {
                setLoading(false)
                setSankeyReady(true)
                const rows = data.result
                // insert data header row required for chart type
                rows.unshift(['From', 'To', 'Count'])
                setSankeyData(rows)
                showStatus('done', { loading: false })
                // showStatus(JSON.stringify(data, null, 2))
            });
    }

    const loadSimSet = (selection, dataTable) => {
        console.log('selection', selection, dataTable)
        const leftSelection = selection[0]
        const { name } = leftSelection
        setSelection(name)
        const url = `/api/tuner/load/simset?set_name=${menuLeft.value}&left=${name}&threshold=${threshold}`
        showStatus('load sims: ' + url, { loading: true })
        fetch(url).then(NetLib.handleResponse)
            .then(data => {
                const rows = data.result
                setSimsData(rows)
                console.log('simset', rows)
                showStatus('loadSimSet.done', { loading: false })
            });
    }

    // perform scan operation to find similar
    const scanSims = () => {
        console.log('scanSims', menuRight, menuLeft)
        const url = `/api/tuner/scan?left=${menuLeft.value}&right=${menuRight.value}&threshold=${threshold}&model_type=${modelType}`
        showStatus('scanSims:' + url, { loading: true })
        fetch(url).then(NetLib.handleResponse)
            .then(data => {
                setLoading(false)
                // setSimsData(data.result)
                console.log('status', data)
                showStatus('scan complete', { loading: false })
                // showStatus(JSON.stringify(data, null, 2))
            });
    }

    const changeThreshold = (evt) => {
        setThreshold(evt.target.value)
        evt.preventDefault()
    }

    const selectModelType = (opt) => {
        console.log('setModelType', opt)
        setModelType(opt.value)
    }

    // TODO - replace with common component
    const progBar = () => {
        if (loading) {
            return (
                <div>
                    <div className="progress-line">.</div>
                </div>
            )
        } else {
            // fixme - empty fragment?
            return (<span> </span>)
        }
    }

    const showStatus = (msg: string, opts = { loading: false }) => {
        setMsg(msg)
        setLoading(opts.loading)
        console.log('status', msg)
    }

    const handleClose = (event, reason) => {
        if (reason === 'clickaway') {
            return;
        }
        setLoading(false)
    };

    // let rows = 0
    // if (sankeyReady) {
    //     rows = sankeyData.length
    // }

    return (
        <div className='content'>
            <TitleBox info={AppConfig.page('Linky')} />

            <div className='row-group'>
                <div className='box-label'>
                    left
                </div>
                <Select
                    className='drop-menu'
                    defaultValue={menuLeft}
                    onChange={setMenuLeft}
                    options={leftOptions}
                />
                <div className='box-label'>
                    right
                </div>
                <Select
                    className='drop-menu'
                    defaultValue={menuRight}
                    onChange={setMenuRight}
                    options={rightOptions}
                />
            </div>

            <div className='row-group'>
                <TextField
                    id="outlined-basic"
                    value={threshold} onChange={changeThreshold}
                    label="threshold 0-1" variant="outlined" />
                <Select
                    className='drop-menu'
                    defaultValue={'lg'}
                    onChange={selectModelType}
                    options={baseModelOptions}
                />
                <Button variant='contained' color='primary' onClick={scanSims}>scanSims</Button>
                <Button variant='contained' color='primary' onClick={loadSims}>loadSims</Button>
                <div className='info'>rows: {sankeyReady && sankeyData.length}</div>
            </div>

            { progBar()}

            <div className='linker-content'>

                {sankeyReady &&
                    <Chart
                        className='sankey-box'
                        chartType="Sankey"
                        loader={<div>Loading Chart</div>}
                        data={sankeyData}
                        options={{
                            sankey: {
                                node: {
                                    interactivity: true,
                                    width: 50
                                },
                                link: {
                                    interactivity: false
                                }
                            }
                        }}
                        rootProps={{ 'data-testid': '1' }}
                        chartEvents={[
                            {
                                eventName: 'select',
                                callback: ({ chartWrapper }) => {
                                    const chart = chartWrapper.getChart()
                                    const selection = chart.getSelection()
                                    const dataTable = chartWrapper.getDataTable()
                                    loadSimSet(selection, dataTable)
                                },
                            },
                        ]}
                    />
                }

                <SimsTable simsData={simsData} selection={selection} />
            </div>

            <Snackbar
                open={loading}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
                onClose={handleClose}>
                <div>
                    <Alert severity="info">
                        {msg}
                    </Alert>
                </div>
            </Snackbar>
        </div >
    );
}

export default Linker;
