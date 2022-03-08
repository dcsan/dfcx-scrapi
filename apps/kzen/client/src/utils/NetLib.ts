const NetLib = {

    handleResponse (response: any) {
        console.log('raw response:', response)
        if (response.status !== 200) {
            console.error('failed error')
            return "FAILED: status: " + response.status
        }
        try {
            return response.json()
        } catch(err) {
            console.error('failed to parse', response)
            return "FAILED"
        }
    }
}

export default NetLib
