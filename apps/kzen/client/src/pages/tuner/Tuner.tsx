import * as React from 'react'
import {
    // useEffect,
    useState, useEffect
}
    from 'react';
import Select from "react-select";

import AppConfig from '../../utils/AppConfig'
import NetLib from '../../utils/NetLib'

import ItemList from './ItemList'
import BaseItem from './BaseItem'
import Snackbar from '@material-ui/core/Snackbar';
import MuiAlert from '@material-ui/lab/Alert';
import TitleBox from '../../components/TitleBox';

type Opt = {
    label: string
    value: string
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

function Alert(props) {
    return <MuiAlert elevation={6} variant="filled" {...props} />;
}


function Tuner() {
    const [msg, setMsg] = useState('loading');
    const [loading, setLoading] = useState(false)

    const loadingMsg: Opt = { label: 'select...', value: 'loading' }
    // const tempData = {item_list: ['loading']}

    //--- agent dynamic menu ----
    const [agentData, setAgentData] = useState([loadingMsg])
    const [agentOptions, setAgentOptions] = useState([loadingMsg])
    const [selectedAgent, setSelectedAgent] = useState(loadingMsg);

    // --- import data ---
    const [gdocData, setGdocData] = useState([loadingMsg])
    const [gdocOptions, setGdocOptions] = useState([loadingMsg])
    const [selectedGdoc, setSelectedGdoc] = useState(loadingMsg);

    // intents
    const [intentsData, setIntentsData] = useState(tempData)
    const [pickedIntent, setPickedIntent] = useState(-1)

    // phrases
    const [phrasesData, setPhrasesData] = useState(tempData)
    const [pickedPhrase, setPickedPhrase] = useState(-1)

    // sim
    const [simData, setSimData] = useState(tempData)
    const [pickedSim, setPickedSim] = useState(-1)

    // popover
    // const [anchorEl, setAnchorEl] = React.useState(null);
    // const popOpen = Boolean(anchorEl);

    const sample = false

    // TODO - fetch dynamic?
    useEffect(() => {
        AppConfig.load('agents', setAgentData)
        AppConfig.load('gdocs', setGdocData)
    }, [])

    useEffect(() => {
        const opts: any = agentData.map((item: any) => {
            return {
                label: item.cname,
                value: item.cname
            }
        })
        setAgentOptions(opts)
        setSelectedAgent(opts[0])
        setMsg('ready')
    }, [agentData])

    // loaded data options
    useEffect(() => {
        const opts: any = gdocData.map((item: any) => {
            return {
                label: item.cname,
                value: item.cname
            }
        })
        // console.log('update', opts)
        setGdocOptions(opts)
        // TODO - update menu
        setSelectedGdoc(opts[0])
        setMsg('ready')
    }, [gdocData])

    const loadSims = () => {
        // loads base data AND comparison import data
        const agentCname = selectedGdoc.label // FIXME - consistency
        const url = `/api/tuner/load/intents?set_name=${selectedGdoc.value}&agent=${agentCname}&sample=${sample}`
        showStatus('load Intents: ' + selectedGdoc.value, { loading: true })
        fetch(url).then(NetLib.handleResponse)
            .then(data => {
                setLoading(false)
                setIntentsData(data.result)
                console.log('status', data)
                showStatus('done', { loading: false })
                // showStatus(JSON.stringify(data, null, 2))
            });
    }

    // perform scan operation to find similar
    const scanSims = () => {
        console.log('scanSims', selectedAgent, selectedGdoc)
        const agentCname = selectedAgent.label // FIXME - consistency
        const url = `/api/tuner/scan?set_name=${selectedGdoc.value}&agent=${agentCname}&sample=${sample}`
        showStatus('scanSims: set_name' + selectedGdoc.value, { loading: true })
        fetch(url).then(NetLib.handleResponse)
            .then(data => {
                setLoading(false)
                // setSimsData(data.result)
                console.log('status', data)
                showStatus('scan complete', { loading: false })
                // showStatus(JSON.stringify(data, null, 2))
            });
    }

    // UI controls
    const pickIntent = (idx, item, itemName) => {
        console.log('pickIntent:', item)
        setPhrasesData(tempData)
        setSimData(tempData)
        setLoading(true)
        setPickedIntent(idx) // change highlight
        const agentCname = selectedAgent.label // FIXME - consistency
        const url = `/api/tuner/load/phrases?set_name=${selectedGdoc.value}&agent=${agentCname}&sample=${sample}&intent=${itemName}`
        showStatus('load phrases: ' + itemName, { loading: true })
        fetch(url).then(NetLib.handleResponse)
            .then(data => {
                console.log('loaded.data', data)
                setPhrasesData(data.result)
                showStatus('done', { loading: false })
                setLoading(false)
                // showStatus(JSON.stringify(data, null, 2))
            });
    }

    // pickPhrase - show sims
    const pickPhrase = (idx, item, itemName) => {
        setPickedPhrase(idx)
        setSimData(tempData)
        console.log('pickPhrase', item)
        const agentCname = selectedAgent.label // FIXME - consistency
        const url = `/api/tuner/load/sims?uuid=${item.uuid}&set_name=${selectedGdoc.value}&agent=${agentCname}&sample=${sample}&intent=${itemName}`
        showStatus('load sims: ' + itemName, { loading: true })
        fetch(url).then(NetLib.handleResponse)
            .then(data => {
                console.log('loaded.data', data)
                setSimData(data.result)
                showStatus('done', { loading: false })
                setLoading(false)
                // showStatus(JSON.stringify(data, null, 2))
            });
    }

    const importAgent = () => {
        console.log('imporAgent')
    }
    const importUpdate = () => {
        console.log('imporAgent')
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

    // pickPhrase - show sims
    const pickSim = (idx, _item, _itemName) => {
        setPickedSim(idx)
        // console.log('pickPhrase', item)
        // const agentCname = selectedAgent.label // FIXME - consistency
        // const url = `/api/tuner/load/sims?uuid=${item.uuid}&set_name=${selectedGdoc.value}&agent=${agentCname}&sample=${sample}&intent=${itemName}`
        // showStatus('load sims: ' + itemName )
        // fetch(url).then(NetLib.handleResponse)
        // .then(data => {
        //     console.log('loaded.data', data)
        //     setSimData(data.result)
        //     showStatus('done')
        //     // showStatus(JSON.stringify(data, null, 2))
        // });
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

    // const handlePopoverOpen = (event) => {
    //     setAnchorEl(event.currentTarget);
    // };
    //
    // const handlePopoverClose = () => {
    //     setAnchorEl(null);
    // };

    return (
        <div className='content'>
            <TitleBox info={AppConfig.page('Tuney')} />

            <div className='row-group'>
                <div className='box-label'>
                    Agent
                </div>
                <Select
                    className='drop-menu'
                    defaultValue={selectedAgent}
                    onChange={setSelectedAgent}
                    options={agentOptions}
                />
                <button className='big-button' onClick={importAgent}>importAgent</button>
            </div>

            <div className='row-group'>
                <div className='box-label'>
                    Update
                </div>
                <Select
                    className='drop-menu'
                    defaultValue={selectedGdoc}
                    onChange={setSelectedGdoc}
                    options={gdocOptions}
                />
                <button className='big-button' onClick={importUpdate}>importUpdate</button>
            </div>

            <div className='row-group'>
                <button className='big-button' onClick={scanSims}>scanSims</button>
                <button className='big-button' onClick={loadSims}>loadSims</button>
            </div>

            <div className='pick-columns'>
                <ItemList
                    title='intents'
                    fieldName='intent'
                    itemsData={intentsData}
                    pickItem={pickIntent}
                    pickedItem={pickedIntent}
                    innerItem={BaseItem}
                    activeClass='intent-picked'
                />
                <ItemList
                    title='phrases'
                    fieldName='utterance'
                    itemsData={phrasesData}
                    pickItem={pickPhrase}
                    pickedItem={pickedPhrase}
                    innerItem={BaseItem}
                    activeClass='phrase-picked'
                    showChips={true}
                />
                <ItemList
                    title='sims'
                    fieldName='text2'
                    itemsData={simData}
                    pickItem={pickSim}
                    pickedItem={pickedSim}
                    innerItem={BaseItem}
                    activeClass='phrase-picked'
                    showChips={true}
                />

            </div>
            {progBar()}

            <Snackbar
                open={loading}
                autoHideDuration={4000}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
                onClose={handleClose}>
                <div>
                    <Alert severity="info">
                        {msg}
                    </Alert>
                </div>
            </Snackbar>
        </div>
    );
}

export default Tuner;
