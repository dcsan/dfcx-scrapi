import * as React from 'react'
import {
    // useEffect,
    useState, useEffect
} from 'react';
import Select from "react-select";

import AppConfig from '../utils/AppConfig'

interface ILabel {
    label: string
    agent_path?: string
    agent_id?: string
    cname?: string
}

function Chat() {

    // const [agent_id, setAgentId] = useState()
    // const [selectedAgent, setSelectedAgent] = useState(agentOptions[0]);
    // const agentOptions = AppConfig.get('agentOptions')
    const initLoader: ILabel = { label: 'loading' }
    const [loading, setLoading] = useState(initLoader)
    const [agentData, setAgentData] = useState([loading])
    const [agentOptions, setAgentOptions] = useState([loading])
    const [selectedAgent, setSelectedAgent] = useState(loading);  // single agent

    useEffect(() => {
        AppConfig.load('agents', setAgentData)
    }, [])

    const extractId = (agentPath) => {
        if (agentPath) {
            return agentPath.split('/').pop()
        } else {
            return false
        }
    }

    useEffect(() => {
        if (!agentData) return
        // when agent is picked, gloss on some other fields for the select menu
        const opts: any = agentData.map((item: any) => {
            item.label = item.cname
            item.value = item.agent_path
            item.agent_id = item.agent_id || extractId(item.agent_path)
            return item
        })
        setAgentOptions(opts)
        // setSelectedAgent(opts[0])
        setLoading({ label: 'Select agent:' })
        // setSelectedAgent(loading)
    }, [agentData])

    // const script = document.createElement("script");
    // script.async = true;
    // document.body.appendChild(script);

    // useEffect(() => {
    //     const script = document.createElement('script');
    //     script.src = '/js/dfcx-widget.js'
    //     // script.src = "https://www.gstatic.com/dialogflow-console/fast/messenger-cx/bootstrap.js?v=1";
    //     script.async = true;
    //     console.log('adding script tag')
    //     return () => {
    //         document.body.removeChild(script);
    //     }
    // }, []);

    useEffect(() => {
        // triggered on agent change
        setTimeout(() => {
            const dfMessenger = document.querySelector('df-messenger');
            console.log('changed agent =>', selectedAgent)

            if (!dfMessenger) {
                console.warn('dom not ready yet')
                // not loaded yet
                return
            }

            dfMessenger.addEventListener('df-button-clicked', function (event) {
                console.log('df-button-clicked:', event)
            })
            dfMessenger.addEventListener('df-response-received', function (event) {
                console.log('response:', event)
            })

            const actionLink = `https://dialogflow.cloud.google.com/cx/projects/YOUR_GCP_PROJECT/locations/global/agents/${selectedAgent.agent_path}`
            // const dfMessenger = document.querySelector('df-messenger');

            const payload = [{
                "type": "info",
                "title": `agent: ${selectedAgent.label}`,
                "subtitle": "click to edit agent or chat",
                "image": {
                    "src": {
                        "rawUrl": "https://gstatic.com/dialogflow-console/common/assets/ccai-icon-family/dialogflow-cx-512-color.png"
                    }
                },
                "actionLink": actionLink
            }];

            console.log('payload', payload)
            // @ts-ignore
            dfMessenger.renderCustomCard(payload);
        }, 1000) // wait for JS script to load

        return () => {
            console.log('TODO remove event listener')
            // dfMessenger.removeEventListener('df-response-received')
        }

    }, [selectedAgent])

    const addWidget = () => {
        // setTimeout(() => {
        //     this.appendNewTagElementToDom(script);
        // }, delayTime*index);

        const inner = `
        <df-messenger
                df-cx="true"
                chat-title="${selectedAgent.cname}"
                agent-id="${selectedAgent.agent_id}"
                language-code="en"
        ></df-messenger>`
        return (
            <div>
                <div className="content" dangerouslySetInnerHTML={{ __html: inner }}> </div>
            </div>
        )
    }

    // const pickAgent = (options) => {
    //     console.log('testOne', selectedAgent)
    //     //  = selectedAgent.value
    // }

    return (
        <div className='content'>
            <h2>
                ChatWidget
            </h2>

            <div className='status-msg stacked'>
                <div>
                    agent_id: {selectedAgent.label}
                </div>
                <div>
                    agent_path: {selectedAgent.agent_path}
                </div>
            </div>

            <div className='row'>
                <Select
                    className='drop-menu'
                    defaultValue={selectedAgent}
                    onChange={setSelectedAgent}
                    options={agentOptions}
                />
            </div>
            {addWidget()}
        </div>
    )

}

export default Chat;
