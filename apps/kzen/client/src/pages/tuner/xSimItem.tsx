function SimItem(props) {

    // console.log('simItem', props)
    const itemClass = props.active ? 'base-inner ' + props.activeClass : 'base-inner'

    // const details = props.active ? 
    //     <div>
    //         <span className='sim-detail'>
    //             r: {props.item.ratio} | 
    //             s: {props.item.ratio_sort} | 
    //             p: {props.item.ratio_part} | 
    //         </span>
    //     </div>
    //     :
    //     <span></span>
    
    let col
    const ratio = props.item.ratio
    if (ratio > 80) col = '#ff0000'
    else if (ratio > 70) col = '#ff4444'
    else if (ratio > 60) col = '#ffAAAA'
    else col = '#DDBBBB'

    const pillStyle = {
        'backgroundColor': col
    }

    const simClass = `pill sm`

    return(
        <div className={itemClass}>
            <span className={simClass} style={ pillStyle }>
                {props.item.ratio}
            </span>
            { props.text }
        </div>
    )
}

export default SimItem;

