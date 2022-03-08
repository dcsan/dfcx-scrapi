import React, { useRef, useEffect, useState } from "react"

import Button from '@material-ui/core/Button';
import TextField from '@material-ui/core/TextField';

import TitleBox from "../../components/TitleBox"
import AppConfig from "../../utils/AppConfig"
import NetLib from '../../utils/NetLib'

import CytoscapeComponent from 'react-cytoscapejs';

import Cytoscape from 'cytoscape';
import graphOptions from './graphOptions'
// import graphTestData from './graphTestDataV2'
import ProgBar from '../../components/ProgBar'


// import COSEBilkent from 'cytoscape-cose-bilkent';
// Cytoscape.use(COSEBilkent);

import fcose from 'cytoscape-fcose';
Cytoscape.use(fcose);

import './grafy.css'
import { useCallback } from "react";

// import fcose from 'cytoscape-fcose';

const clog = console.log

async function loadPageData(url: string, loadFlag: any, dataContainer: any) {
    // loadFlag(true)
    console.log('load', url)
    fetch(url).then(NetLib.handleResponse)
        .then(result => {
            // loadFlag(false)
            const data = result.data
            console.log('result.data', data)
            dataContainer(data)
        });
}

const tempPageData = {
    page_name: 'current page',
    no_match: 0,
    escalated: 0,
    sources: [
        { name: 'from', total: 0 }
    ],
    targets: [
        { name: 'to', total: 0 }
    ]
}

const Grafy = (props) => {

    const starterSet = '0804-ffm'
    const baseThreshold = 10
    // const starterSet = 'allflows_0610'
    // const starterSet = 'allflows_0610'
    // const starterSet = 'bill_tiny'

    const [msg, setMsg] = useState('loading');
    const [graphData, setGraphData] = useState()
    const [loading, setLoading] = useState(false)
    const [setName, setSetName] = useState(starterSet)
    const [pageSet, setPageSet] = useState('BILL')
    // const [curPage, setCurPage] = useState('current page')
    const [pageData, setPageData] = useState(tempPageData)
    const [cy, setCy] = useState({})
    const [threshold, setThreshold] = useState(baseThreshold)
    const [cyReady, setCyReady] = useState(false)

    clog('refresh: setName', setName)

    const loadGraph = () => {
        // cannot pass a param its based on setName value
        const url = `/api/graph/load?set_name=${setName}&page_set=${pageSet}&threshold=${threshold}`
        showStatus('load sankey: ' + url, { loading: true })
        cyRef.current = false
        fetch(url).then(NetLib.handleResponse)
            .then(result => {
                setLoading(false)
                const data = result.data
                console.log('result.data', data)
                showStatus('setGraphData', { loading: false })
                setGraphData(data.elements)
                // setTimeout(() => {
                //     prepGraph()
                // }, 200)
                //@ts-ignore
                // setGraphData(graphTestData)
                // showStatus(JSON.stringify(data, null, 2))
            });
    }

    // const prepGraph = () => {
    //     console.log('prepCy', cy)
    //     // @ts-ignore
    //     cy.on('tap', (event: any) => {
    //         console.log('click cy', event, Date.now())
    //         console.log('target', event.target)
    //     });
    // }

    // const initCy = (cy: any) => {
    //     cy.on('add', 'node', evt => {
    //         console.log('added node', evt)
    //         cy.layout(layout).run()
    //         cy.fit()
    //     })

    //     // will attach multiple tap events
    //     cy.on('tap', (event: any) => {
    //         console.log('click cy', event, Date.now())
    //         // console.log('target', event.target)
    //     });

    //     // if (cyReady) {
    //     //     console.log('skip init', cy)
    //     //     return // somehow getting init multiple times
    //     // }

    //     // @ts-ignore
    //     console.log('initCy', cy)

    //     // @ts-ignore
    //     window.cy = cy

    //     setCy(cy)
    //     setCyReady(true)
    // }


    const cyRef = useRef<any>();
    // const cyRef = useRef<CytoscapeRef | null>();
    // const cyRef = useRef

    // cleanup cytoscape listeners on unmount
    useEffect(() => {
        return () => {
            if (cyRef.current) {
                cyRef.current.removeAllListeners();
                cyRef.current = null;
            }
        };
    }, []);

    const cyCallback = useCallback(
        (cy: any) => {
            // this is called each render of the component, don't add more listeners
            if (cyRef.current) return;

            console.log('cyCallback')
            cyRef.current = cy;

            cy.on('add', 'node', evt => {
                // console.log('added node', evt)
                // TODO - just on last node / graph complete?
                cy.layout(layout).run()
                cy.fit()
            })

            // will attach multiple tap events
            cy.on('tap', (event: any) => {
                // console.log('click cy', event, Date.now())
                pickNode(event)
                // console.log('target', event.target)
            });


            // cy.ready(...);
            // cy.on(...);
        },
        [graphData],
    );


    const pickNode = (evt: any) => {

        if (!evt.target.id) {
            // console.log('clicked bg', evt)
            return false
        }

        // fixme - threshold gets set wrong?
        const pageName = evt.target.id()
        const url = `/api/graph/page?page_name=${pageName}&set_name=${setName}&threshold=${threshold}`
        console.log('picked', pageName, setName)
        loadPageData(url, setLoading, setPageData)
    }

    // useEffect(() => {
    //     clog('auto loadGraph', setName)
    //     loadGraph()
    // }, [setName])

    const showStatus = (msg: string, opts = { loading: false }) => {
        setMsg(msg)
        setLoading(opts.loading)
        console.log('status', msg)
    }

    // https://dash.plotly.com/cytoscape/styling
    const stylesheet = [
        {
            selector: 'node',
            label: "thing",
            style: {
                'font-size': 14,
                'color': 'blue',
                label: 'data(label)',
                'background-color': 'data(color)',
                shape: 'data(shape)',
                width: 'data(weight)',
                height: 'data(weight)',
                // padding: '100px',
                // shape: 'square'
                // color: 'data(color)'
            }
        },

        {
            selector: 'edge',
            style: {
                'font-size': 8,
                'color': '#444', // text color
                'curve-style': 'bezier',
                'target-arrow-shape': 'triangle',
                'background-color': 'data(color)',
                // 'arrow-scale': 1,
                width: 'data(weight)',
                label: 'data(label)',
                // color: 'data(color)'
            }
        }
    ]

    const layout = {
        // name: 'cose-bilkent',
        name: 'fcose',
        ...graphOptions
    }

    // cy.nodes('[id = "yourId"]').style('background-color', 'desiredColor');

    const changeSet = (evt: any) => {
        const value = evt.target.value
        console.log('set', value)
        setSetName(value)
    }

    const changePageSet = (evt: any) => {
        const value = evt.target.value
        setPageSet(value)
    }

    // useEffect(() => {
    //     // @ts-ignore
    //     if (cy && cy.layout) {
    //         console.log('graphData updated')
    //         // @ts-ignore
    //         cy.layout(layout).run()
    //         // @ts-ignore
    //         cy.fit()
    //     }
    // }, [graphData])

    // cy.layout(layout).run()
    // cy.fit()

    const showLinks = (items, direction) => {
        const blocks = items.map(item => {
            return (
                <div className='link-item'>
                    <span className='link-counter'>{item.total}</span>
                    <div>{item.intent}</div>
                    <div>{item[direction]}</div>
                </div>
            )
        })
        return (
            <div>
                <div className='link-box-header'>{direction}</div>
                {blocks}
            </div>
        )
    }

    return (
        <div className='content'>
            <TitleBox info={AppConfig.page('Grafy')} />
            <div className='horiz'>
                <TextField
                    id="outlined-name"
                    label="set_name"
                    value={setName}
                    onChange={changeSet}
                    variant="outlined"
                />
                <TextField
                    id="outlined-name"
                    label="flow"
                    value={pageSet}
                    onChange={changePageSet}
                    variant="outlined"
                />
                <TextField
                    id="outlined-name"
                    label="threshold"
                    value={threshold}
                    onChange={(evt: any) => setThreshold(evt.target.value)}
                    variant="outlined"
                />
                <Button variant='contained' color='primary' onClick={loadGraph}>loadGraph</Button>
            </div>

            {loading ?
                <div>loading graph</div>
                :
                <CytoscapeComponent
                    cy={cyCallback}
                    className='cyto-box'
                    elements={graphData}
                    layout={layout}
                    stylesheet={stylesheet}
                />
            }

            <div className='page-info-box'>
                <div className='page-name'>{pageData.page_name}</div>
                <div className='page-data'>escalated {pageData.escalated}</div>
                <div className='page-data'>noMatch {pageData.no_match}</div>
                {showLinks(pageData.sources, 'source')}
                {showLinks(pageData.targets, 'target')}
            </div>

            <ProgBar loading={loading} />
        </div>

    )
}

export default Grafy
