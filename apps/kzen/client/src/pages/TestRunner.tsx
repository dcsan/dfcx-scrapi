import React, {
    useState,
    // useEffect
} from 'react';
import Select from "react-select";
import TitleBox from '../components/TitleBox';

import AppConfig from '../utils/AppConfig'

// TODO - get this from an API which is from Sheets


function TestRunner() {

    const runTabs = AppConfig.read('runTabs')
    const sheetNames = AppConfig.read('sheetNames')

    const tabOptions = runTabs.map(elem => { return { value: elem, label: elem } })
    const sheetOptions = sheetNames.map(elem => { return { value: elem, label: elem } })
    const [loading, setLoading] = useState(false)

    const [msg, setMsg] = useState('ready');
    const [selectedOption, setSelectedOption] = useState(tabOptions[0]);
    const [selectedSheet, setSelectedSheet] = useState(sheetOptions[0]);

    const runOne = () => {
        setLoading(true)
        console.log('testOne', selectedOption)
        const tabname = selectedOption.value
        const sheet_key = selectedSheet.label  // pass the name of the sheet
        const url = `/api/testone?tabname=${tabname}&sheet_key=${sheet_key}`
        showStatus('testing: ' + url)
        fetch(url)
            .then(response => {
                console.log('raw response:', response)
                if (response.status !== 200) {
                    console.error('failed error')
                    return "FAILED: status: " + response.status
                }
                try {
                    setLoading(false)
                    return response.json()
                } catch (err) {
                    console.error('failed to parse', response)
                    return "FAILED"
                }
            })
            .then(data => showStatus(JSON.stringify(data, null, 2)));
    }


    const showStatus = (msg) => {
        setMsg(msg)
        console.log('status', msg)
    }

    const progBar = () => {
        if (loading) {
            return (
                <div>
                    <div className="progress-line"></div>
                </div>
            )
        } else {
            // fixme - empty fragment?
            return (<span></span>)
        }
    }

    return (
        <div className='content'>
            <TitleBox info={AppConfig.page('TestRunner')} />

            <div className='stacked'>

                <div className='row'>
                    <div className='box-label'>
                        sheet
                    </div>
                    <Select
                        className='drop-menu'
                        defaultValue={selectedSheet}
                        onChange={setSelectedSheet}
                        options={sheetOptions}
                    />
                </div>

                <div className='row'>
                    <div className='box-label'>
                        tab
                    </div>
                    <Select
                        className='drop-menu'
                        defaultValue={selectedOption}
                        onChange={setSelectedOption}
                        options={tabOptions}
                    />
                    <button className='big-button' onClick={runOne}>Test One</button>
                </div>

            </div>

            { progBar()}
            <div className='status-msg'>
                {msg}
            </div>

        </div>
    );
}

export default TestRunner;
