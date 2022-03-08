import * as React from 'react'
import {
    // useEffect,
    useState, useEffect
}
    from 'react';

import Select from "react-select";
import TitleBox from '../components/TitleBox';

import AppConfig from '../utils/AppConfig'
import NetLib from '../utils/NetLib'

type Opt = {
    label: string
    value: string
}

function Benchmark() {
    const [loading, setLoading] = useState(false)
    const dashboardUrl = AppConfig.read('dashboardUrl')
    console.log('dashboardUrl', dashboardUrl)
    const [msg, setMsg] = useState('loading');

    const loadingMsg: Opt = { label: 'select...', value: 'loading' }

    //--- agent dynamic menu ----
    const [agentData, setAgentData] = useState([loadingMsg])
    const [agentOptions, setAgentOptions] = useState([loadingMsg])
    const [selectedAgent, setSelectedAgent] = useState(loadingMsg);

    // --- test sets dynamic menu ---
    const [gdocData, setGdocData] = useState([loadingMsg])
    const [gdocOptions, setGdocOptions] = useState([loadingMsg])
    const [selectedGdoc, setSelectedGdoc] = useState(loadingMsg);

    useEffect(() => {
        AppConfig.load('agents', setAgentData)
    }, [])
    useEffect(() => {
        AppConfig.load('gdocs', setGdocData)
    }, [])

    useEffect(() => {
        const opts: any = agentData && agentData.map((item: any) => {
            return {
                label: item.cname,
                value: item.cname
            }
        })
        setAgentOptions(opts)
        setSelectedAgent(opts[0])
        setMsg('ready')
    }, [agentData])

    useEffect(() => {
        const opts: any = gdocData && gdocData.map((item: any) => {
            return {
                label: item.cname,
                value: item.cname
            }
        })
        console.log('update', opts)
        setGdocOptions(opts)
        // TODO - update menu
        setSelectedGdoc(opts[0])
    }, [gdocData])

    const runBenchmark = () => {
        setLoading(true)
        console.log('runBenchmart', selectedAgent, selectedGdoc)
        const agentCname = selectedAgent.label // FIXME - consistency
        const url = `/api/benchmark/run?test=${selectedGdoc.value}&agent=${agentCname}`
        showStatus('running: BM check chatroom for updates/ status: \n' + url, { loading: true })
        fetch(url).then(NetLib.handleResponse)
            .then(data => {
                showStatus(JSON.stringify(data, null, 2), { loading: false })
            });
    }


    const reloadTestData = () => {
        console.log('reloadTestData', selectedGdoc)
        const url = `/api/testdata/reload?test=${selectedGdoc.value}`
        showStatus('start: reloadTestData: ' + url)
        fetch(url).then(NetLib.handleResponse)
            .then(data => showStatus(JSON.stringify(data, null, 2)));
    }


    const showStatus = (msg: string, opts = { loading: false }) => {
        setMsg(msg)
        console.log('status', msg)
        setLoading(opts.loading)
    }

    const progBar = () => {
        if (loading) {
            return (
                <div>
                    <div className="progress-line"> </div>
                </div>
            )
        } else {
            // fixme - empty fragment?
            return (<span> </span>)
        }
    }

    return (
        <div className='content'>
            <TitleBox info={AppConfig.page('BenchMarky')} />

            <div className='row-group'>
                <div className='box-label'>
                    TestSet
                </div>
                <Select
                    className='drop-menu'
                    defaultValue={selectedGdoc}
                    onChange={setSelectedGdoc}
                    options={gdocOptions}
                />
                <button className='big-button' onClick={reloadTestData}>reload Test Data</button>
            </div>

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
                <button className='big-button' onClick={runBenchmark}>run benchmark</button>
            </div>

            <a href={dashboardUrl}>Dashboard</a>

            <hr />
            <div className='status-msg'>
                {msg}
            </div>
            {progBar()}
        </div>
    );
}

export default Benchmark;
