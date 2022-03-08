import * as React from 'react'

import HelpOutlineIcon from '@material-ui/icons/HelpOutline';

import './titlebox.css'

const TitleBox = (props) => {
    const info = props.info
    return (

        <div className='title-bar'>
            <span className='title-text'>
                {info.title}
            </span>
            <span className='help-info'>
                {info.subtitle}
            </span>
            {info.docs &&
                <a href={info.docs} target='docs' className='help-button'>
                    help
                    <HelpOutlineIcon />
                </a>
            }

        </div>
    )

}

export default TitleBox
