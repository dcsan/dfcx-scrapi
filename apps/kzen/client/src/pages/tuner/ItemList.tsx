import * as React from 'react'

// usually just one of these two fields?
interface IPickItem {
    utterance?: string
    intent?: string
    intent2?: string
}


const clog = console.log


// generic ItemList
// passed in pickItem function handles selection events

function ItemList(props) {

    // console.log(`render ItemList ${props.title} => `, props )
    const fieldName = props.fieldName  // allow to render intents or phrases

    const itemsData =  props.itemsData
    const items: IPickItem[] = itemsData.item_list || []
    // console.log('props', props)
    // console.log('items', items)

    const Inner = props.innerItem

    function showList() {
        if (!items) {
            return(<div>loading</div>)
        }

        const pickItem = (idx, item) => {
            console.log('picked', idx)
            props.pickItem(idx, item, item[fieldName])
        }

        let lastItem: IPickItem = { }
        return items.map( (item, idx) => {
            // clog('item', item, idx)
            const active = props.pickedItem === idx
            const key = 'item-' + idx // FIXME - some items are not unique item[fieldName]
            const category = 'phrase'
            let separator
            if (lastItem.intent2 !== item.intent2) {
                separator = (<div className='sim-separator'>{item.intent2} </div>)
            }
            lastItem = item
            const text=item[fieldName]
            const innerOpts = {
                ...props,
                item, 
                idx, text, separator, active, category
            }
            return(
                <div key={ key }>
                    <div onClick={ () => pickItem(idx, item)} >
                        { separator }
                        <Inner { ...innerOpts } />
                    </div>
                </div>
            )
        })
    }

    return(
        <div className='third'>
            <h3>
                <span className='pill sm'>
                    { items.length }
                </span>
                { props.title }
            </h3>
            { showList() }
        </div>
    )
}

export default ItemList;
