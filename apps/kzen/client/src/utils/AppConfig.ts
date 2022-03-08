// global configs for this app
// eventually this hardwired data will be replaced with API calls

// import NetLib from './NetLib'

const configData = {
    version: "3.1.5",
    changes: 'linky UI',
    configDoc: 'https://docs.google.com/spreadsheets/d/YOURDOC',
    dashboardUrl: 'https://datastudio.google.com/c/reporting/YOUR-DS',

    // TODO - fetch from server side
    runTabs: [
        'SANDBOX',

    ],

    sheetNames: [
        'test_runs',
        'xp_tests',
    ],

    agents: [
        {
            label: 'chat',
            value: 'AGENT-ID'
        },
    ],

    testNames: [
        "test-name-xx",
    ],

    pages: [
        // {
        //     size: 6,
        //     title: "Tracky",
        //     link: "/kzen/tracker",
        //     subtitle: "track changes to an agent",
        // },
        {
            size: 6,
            title: "Grafy",
            link: "/kzen/grafy",
            subtitle: "Analyze conversation graphs",
        },

        {
            size: 6,
            title: "Tuney",
            link: "/kzen/tuner",
            subtitle: "Tune up intent and phrase conflicts",
            docs: 'https://docs.google.com/document/d/XXXX-XXXX'
        },
        {
            size: 6,
            title: "Linky",
            link: "/kzen/linker",
            subtitle: "find linked phrases across intents",
            docs: 'https://docs.google.com/document/d/XXXX-XXXX'
        },
        {
            size: 6,
            title: "Buckets",
            link: "/kzen/buckets",
            subtitle: "Move ambiguous phrases into buckets",
        },

        {
            size: 12,
            title: "BenchMarky",
            link: '/kzen/benchmark',
            subtitle: "Benchmark overall NLU performance",
            docs: 'https://docs.google.com/document/d/XXXX-XXXX'
        },
        {
            size: 12,
            title: "TestRunner",
            link: '/kzen/testrunner',
            subtitle: "Mass automated test runner for CX agents",
            docs: 'https://docs.google.com/document/d/XXXX-XXXX'
        },
        {
            size: 6,
            title: "Dumpy",
            link: '/kzen/dumpy',
            subtitle: "Import and Export intents and phrases",
        },
        {
            size: 6,
            title: "Configs",
            link: '/kzen/configs',
            subtitle: "Load agent and gdoc settings",
        },

    ],
}

const AppConfig = {

    // TODO - fetch from public at least
    // https://stackoverflow.com/questions/39686035/import-json-file-in-react/52349546#52349546

    showStatus(blob: any) {
        console.log(blob)
    },

    // pass a state modifier function
    xload(key: string, cbSetter: any) {
        const url = `/api/config/${key}`
        console.log('reloadConfig', key, url)
        fetch(url)
            .then(response => {
                console.log('response', response)
                return response.json();
            })
            .then(blob => {
                console.log('got data for ', key, '=>', blob.length)
                console.log('blob[0] ', blob[0]) // if array?
                AppConfig[key] = blob  // cache
                cbSetter(blob)
            });
    },

    load(key: string, cbSetter: any) {
        const url = `/api/config/${key}`

        fetch(url)
            .then(response => {
                // console.log('raw response:', response)
                if (response.status !== 200) {
                    console.error('failed error')
                    return "FAILED: status: " + response.status
                }
                try {
                    return response.json()
                } catch (err) {
                    console.error('failed to parse', response)
                    return "FAILED"
                }
            }
            )
            .then(blob => {
                // console.log('blob', blob )
                // console.log('data[0', blob.data[0])
                cbSetter(blob.data)
            });
    },

    // read from cache
    read(key: any) {
        const data = configData[key]
        if (!data) {
            console.error(`AppConfig could not load ${key}`)
        }
        return data
    },

    page(title: string) {
        // find an element by title
        const opts = configData.pages.filter(elem => {
            const test = elem.title.toLowerCase() == title.toLowerCase()
            return test
        })
        // console.log('opts', opts)
        if (!opts || !opts.length) {
            console.error('cannot find page:', title, 'in:', configData.pages)
            // console.log('opts', opts)
        } else {
            const page = opts.pop()
            // console.log('opts', opts, 'page', page)
            return page // take last match
        }
    }

}

export default AppConfig
