import React, { useEffect, useState } from "react"

const BucketPhrase = ({ posy, picked, phrase }) => {

    var ctrans = `translateY(${posy}px)`;
    var css = {
        transform: ctrans
    }
    // console.log({ css })

    const animClass = picked ? 'slide' : ''

    return (
        <div id='phrase'
            className={animClass}
            style={css}
        >{phrase}
        </div>
    )
}

export default BucketPhrase
