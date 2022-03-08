import * as React from 'react'
import { useState } from 'react'

import SimDetailBar from '../../components/SimDetailBar'

const colorPill = (sim) => {
    const alpha = Math.min(sim.vec, 1) // 0.5-1 => 1
    const textColor = alpha < 0.5 ? 'black' : 'white'
    const pct = Math.round(sim.vec * 100)  // map
    const pillStyle = {
        backgroundColor: `rgba(${255 * alpha}, 50, 50, ${alpha})`,
        color: textColor
    }
    // console.log('pillStyle', pillStyle)
    return (<span className='pill-shape' style={pillStyle}>{pct}%</span>)
}


const SimsTable = (props) => {
    // console.log('simsData', props.simsData)
    let lastIntent, lastText
    let simGroup, textGroup

    const [pickedIndex, setPickedIndex] = useState(0)
    const [lastKey, setLastKey] = useState('-')

    const handlePick = (idx, sim) => {
        console.log('picked', idx, sim)
        setPickedIndex(idx)
    }

    const handleAnswerChange = (event) => {
        console.log('event', event)
        switch (event.key) {
            case 'k':
                setPickedIndex(pickedIndex - 1)
                break
            case 'j':
                setPickedIndex(pickedIndex + 1)
                break
        }
        setLastKey(event.key)
    }


    const inner = props.simsData.map((sim, idx) => {
        if (sim.intent2 !== lastIntent) {
            lastIntent = sim.intent2
            lastText = "" // reset
            simGroup = <div className='intent-group'>{lastIntent}</div>
        } else {
            simGroup = React.Fragment
        }
        if (sim.text1 != lastText) {
            lastText = sim.text1
            const avg = 0 // TODO average of this group
            textGroup = <div className='text-group'>
                {lastText}
            </div>
        } else {
            textGroup = React.Fragment
        }
        const key = 'sim-' + idx
        const isPicked = idx === pickedIndex
        const details = isPicked ? <SimDetailBar sim={sim} /> : React.Fragment
        const innerClass = isPicked ? 'sim-inner picked' : 'sim-inner'
        return (
            <div
                key={key}
                className='sim-outer'
                onClick={() => handlePick(idx, sim)}
            >
                {simGroup}
                {textGroup}
                <div className={innerClass}>
                    <div className='sim-right'>
                        {sim.text2}
                        {colorPill(sim)}
                        {details}
                    </div>
                </div>
            </div>)
    })
    return (
        <div
            className='sims-table'
            onKeyDown={handleAnswerChange}
        >
            <div className='sankey-group'>{props.selection}</div>
            {inner}
        </div>
    )
}

export default SimsTable
