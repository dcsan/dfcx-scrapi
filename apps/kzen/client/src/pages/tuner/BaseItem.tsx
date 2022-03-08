import React, {
    useState,
    // useEffect
} from 'react';

import { makeStyles } from '@material-ui/core/styles';
// import DeleteIcon from '@material-ui/icons/Delete';
import ToggleOn from '@material-ui/icons/ToggleOn';
import ToggleOff from '@material-ui/icons/ToggleOff';
import IconButton from '@material-ui/core/IconButton';

import SimDetailBar from '../../components/SimDetailBar'

const useStyles = makeStyles((theme) => ({
    margin: {
        margin: 0,
    },
    extendedIcon: {
        marginRight: theme.spacing(1),
    },
}));

function BaseItem(props) {
    const classes = useStyles();

    console.log('baseItem.props', props)
    // console.log('props.item', props.item)

    const [enabled, setEnabled] = useState(true)

    const itemClass = props.active ? 'vert base-inner ' + props.activeClass : 'vert base-inner'
    const textStyle = enabled ? 'enabled' : 'disabled'
    const item = props.item || {}

    // FIXME - better to make the data consistent
    const counterVal = item.ratio || item.sim_count

    const counterPill = counterVal ?
        (
            <span className='pill rcount sm'>{counterVal}</span>
        ) : ""

    const toggleMe = (event) => {
        // enabled = !enabled
        setEnabled(!enabled)
        console.log('toggled', enabled)
        event.stopPropagation()
    }

    // this will break if we have duplicates
    const item_key = props.category + props.idx

    let chips
    if (props.showChips && props.active) {
        chips = <div>
            <SimDetailBar sim={props.item} />
            <IconButton
                onClick={toggleMe}
                size='small' aria-label="delete" className={classes.margin}>
                {enabled ?
                    <ToggleOn fontSize="default" color="action" />
                    :
                    <ToggleOff fontSize="default" color="action" />
                }
            </IconButton>
        </div>
    }

    return (
        <div className={itemClass} key={item_key}>
            <div className='horiz'>
                <span className='pill lcount sm'>
                    {props.idx}
                </span>
                <div>
                    <span className={textStyle}>
                        {props.text}
                    </span>
                    {counterPill}
                </div>
            </div>
            <div className='stacked'>
                {chips}
            </div>
        </div>
    )
}

export default BaseItem;



// import Chip from '@material-ui/core/Chip';
// import { withStyles } from '@material-ui/core/styles';
// <Chip variant="outlined" size="small" label='keep' color="primary" />