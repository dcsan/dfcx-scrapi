import * as React from 'react'
import IconButton from '@material-ui/core/IconButton';
import Button from '@material-ui/core/Button';
import SkipNextIcon from '@material-ui/icons/SkipNextRounded';
import SkipPreviousIcon from '@material-ui/icons/SkipPreviousRounded';
import DeleteIcon from '@material-ui/icons/Delete';

const SimDetailBar = (props) => {
    const sim = props.sim
    console.log('sim', sim)
    const pct = (val) => {
        if (!val) return "--"
        return Math.round(val * 100)
    }

    const tinyDetails = () => {
        return (
            <div>
                <span className='tiny-pill'>vec {pct(sim.vec)}</span>
                <span className='tiny-pill'>lg {pct(sim.lg)}</span>
                <span className='tiny-pill'>md {pct(sim.md)}</span>
                <span className='tiny-pill'>sm {pct(sim.sm)}</span>
                <span className='tiny-pill'>use {pct(sim.use)}</span>
                <span className='tiny-pill'>lev {pct(sim.lev)}</span>
            </div>
        )
    }

    return (
        <div className='sim-details'>
            <Button size='small' variant='contained' startIcon={<SkipPreviousIcon />} />
            <Button size='small' variant='contained' startIcon={<DeleteIcon />} />
            <Button size='small' variant='contained' endIcon={<SkipNextIcon />} />

        </div>
    )
}

export default SimDetailBar