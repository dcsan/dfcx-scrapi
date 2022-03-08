import React, { useState } from 'react';

import AppConfig from '../utils/AppConfig'

function Config() {
    const configDoc = AppConfig.read('configDoc')
    const [msg, setMsg] = useState('ready');

    const errorLogUrl = "https://cloudlogging.app.goo.gl/SOME-KEY"
    const memoryUseUrl = 'https://pantheon.corp.google.com/appengine?project=YOUR_GCP_PROJECT&serviceId=default&graph=AE_MEMORY_USAGE'

    const refreshConfigs = () => {
        showStatus('refreshing configs...')
        fetch('/api/configs/refresh')
            .then(response => response.json())
            .then(data => showStatus(JSON.stringify(data, null, 2)));
    }

    const showStatus = (msg) => {
        setMsg(msg)
        console.log('status', msg)
    }

    const sysCheck = () => {
        console.log('running sysCheck')
        showStatus('loading')
        fetch('/api/syscheck')
            .then(response => {
                console.log('response', response)
                return response.json()
            })
            .then(data => showStatus(JSON.stringify(data, null, 2)));

    }

    return (
        <div className='content'>

            <h2>Refresh Configs</h2>
            <div>
                Pull updated configs from <a href={configDoc}>
                    this google doc
                </a>
            </div>
            <p />
            <button className='big-button' onClick={refreshConfigs}>refreshConfigs</button>

            <hr />

            <button className='big-button' onClick={sysCheck}>System Check</button>

            <div className='stacked'>
                <a target='memory' href={memoryUseUrl}>memory usage</a>
                <a target='errors' href={errorLogUrl}>error log</a>
            </div>

            <hr />
            <div className='status-msg'>
                {msg}
            </div>


        </div>
    );
}

export default Config;
