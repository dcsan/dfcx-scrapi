import * as React from 'react'

const ProgBar = (props) => {
    if (props.loading) {
        return(
            <div>
                <div className="progress-line"></div>
            </div>
        )
    } else {
        // fixme - empty fragment?
        return (<span></span>)
    }
}

export default ProgBar
