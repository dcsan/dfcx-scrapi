import React, { useEffect, useState } from "react"
import * as _ from "lodash"


import TitleBox from "../../components/TitleBox"
import AppConfig from "../../utils/AppConfig"
import LinearProgress from '@material-ui/core/LinearProgress';

import { rawBuckets, IBucket, IBucketGame } from './bucketData'

import BucketChoices from './BucketChoices'
import HelpFooter from "./HelpFooter";
import BucketPhrase from './BucketPhrase'

import './bucketGame.css'

const BucketGame = (props) => {

    const gameData: IBucketGame = rawBuckets
    const [round, setRound] = useState(-1)
    const [progress, setProgress] = useState(0)
    const totalRounds = gameData.disambigs.length
    const [userChoice, setUserChoice] = useState(0)
    const [totalChoices, setTotalChoices] = useState(0)
    const [phrase, setPhrase] = useState('')
    const [isPlaying, setPlaying] = useState(false)
    const [bucket, setBucket] = useState<IBucket | undefined>(undefined)
    const [posy, setPosy] = useState(0)
    const [picked, setPicked] = useState(false)

    // console.log('render game', { round, totalChoices })

    const startGame = () => {
        setPlaying(true)
        nextRound()
    }

    useEffect(() => {
        startGame()
    }, [])

    const nextRound = () => {
        let r = round + 1
        if (r >= totalRounds) {
            r = 0
        }
        const bb: IBucket = gameData.disambigs[r]
        bb.intents = _.shuffle(bb.intents)  // FIXME doesnt shuffle
        // bb.intents = bb.intents.slice(0, 1)
        setBucket(bb)
        const choiceCount = bb.intents.length
        setTotalChoices(choiceCount)
        setUserChoice(0)
        setProgress(100 * r / totalRounds)
        setPlaying(true)
        setRound(r)
        setPosy(0)
        setPicked(false)
        const ph = bb.phrases[0]
        setPhrase(ph)
        console.log('nextRound', { bb, c: bb.intents.length, choiceCount })
    }

    const makeChoice = () => {
        setPicked(true)
        setTimeout(nextRound, 1000)
    }

    const moveChoice = (dir: number) => {
        let newChoice = userChoice + dir
        if (newChoice >= totalChoices) newChoice = 0
        if (newChoice < 0) newChoice = totalChoices - 1
        setPosy(100 * newChoice)
        setUserChoice(newChoice)
    }

    const downHandler = (evt) => {
        console.log('key', { userChoice, c: totalChoices })
        switch (evt.code) {
            case 'Space':
            case 'Enter':
                makeChoice()
                break

            case 'ArrowUp':
                moveChoice(-1)
                break
            case 'ArrowDown':
                moveChoice(1)
                break
        }
        evt.preventDefault()
    }

    useEffect(() => {
        // console.log('add key events')
        window.addEventListener("keydown", downHandler)
        return () => {
            window.removeEventListener("keydown", downHandler);
        };
    }, [downHandler]);
    // Empty array ensures that effect is only run on mount and unmount
    // but we need the handler passed in for context

    return (
        <div className='content'>
            <TitleBox info={AppConfig.page('Buckets')} />
            <LinearProgress variant='determinate' value={progress} />

            <div className='game-board'>

                {!isPlaying &&
                    <div onClick={() => makeChoice()} className='start-button'>Start</div>
                }

                {isPlaying &&
                    <div className='buckets-board'>
                        <BucketPhrase
                            phrase={phrase}
                            posy={posy}
                            picked={picked}
                        />
                        <BucketChoices
                            bucket={bucket}
                            userChoice={userChoice}
                            setUserChoice={setUserChoice}
                            nextRound={nextRound} />
                    </div>
                }

            </div>

            <HelpFooter />

            <div className='debug-info'>
                choice: {userChoice} /
                round: {round}
            </div>

        </div>
    )
}

export default BucketGame
