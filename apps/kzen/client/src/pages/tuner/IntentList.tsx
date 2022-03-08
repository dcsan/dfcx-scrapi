

const dummyData ={
    intent_list: [],
    agent_name: '',
    set_name: ''
}

function IntentList(props) {

    // console.log('render IntentList props:', props )

    const intentsData =  props.intentsData || dummyData
    const intents: string[] = intentsData.intent_list

    function showList() {
        if (!intents) {
            return(<div>loading</div>)
        }

        const pickItem = (idx, intentName) => {
            console.log('picked', idx)
            props.pickItem(idx, intentName)
        }

        return intents.map( (intentName, idx) => {
            const key = props.category + idx
            const itemClass = props.pickedIntent === idx ? 'hot-cell picked' : 'hot-cell'
            return(
                <div 
                    key={key}
                    onClick={ () => pickItem(idx, intentName)} 
                    className={itemClass} >{intentName}</div>
            )
        })
    }

    return(
        <div className='third'>
            <h3>
                {props.title}
                <span className='pill sm'>
                    [{ intents.length }]
                </span>
            </h3>
            { showList() }
        </div>
    )
}

export default IntentList;
