import React, { useEffect, useState } from "react"
import TitleBox from "../../components/TitleBox"
import AppConfig from "../../utils/AppConfig"

import LinearProgress from '@material-ui/core/LinearProgress';

import { IBucket, IBucketGame } from './bucketData'

import './bucketGame.css'

const BucketChoices = ({ bucket, nextRound, userChoice, setUserChoice }) => {

    // console.log('render choices', userChoice)

    const pickBucket = (b: IBucket, idx: number) => {
        setUserChoice(idx)
        setTimeout(() => {
            nextRound()
        }, 500)
    }

    const showIntents = () => {
        if (!bucket) return
        const blocks = bucket.intents.map((intent, idx) => {
            // intent = intent.replace(/_/gim, '_ ')
            intent = intent.replace(/\./gim, '. ')
            // console.log('intent', intent)
            const parts = intent.split(' ')
            // let header, main
            // if (parts.length > 1) {
            //     header = parts.shift()
            // }
            const main = parts.join(' ')
            const isChoice = idx === userChoice
            const itemClass = isChoice ? 'bucket-intent picked' : 'bucket-intent'
            return (
                <div
                    onClick={() => pickBucket(bucket, idx)}
                    className={itemClass}>
                    {/* <div className='bucket-header'>{header}</div> */}
                    <div className='bucket-main'>{main}</div>
                </div>
            )
        })

        return (
            <div className='buckets-outer'>
                {blocks}
            </div>
        )
    }

    return (
        <div>
            { showIntents()}
        </div>
    )
}

export default BucketChoices
