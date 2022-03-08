import React, {
    // useEffect,
    useState, useEffect
}
    from 'react';

import {
    BrowserRouter as Router,
    Switch, Route, Link
} from 'react-router-dom'

import '@fontsource/roboto';
import './App.css';


import AppConfig from './utils/AppConfig'

// pages
import Benchmark from './pages/Benchmark'
import Home from './pages/home/Home'
import TestRunner from './pages/TestRunner'
import Tuner from './pages/tuner/Tuner'
import Linker from './pages/linker/Linker'
import Experiment from './pages/Experiment'
// import ChatWidget from './pages/ChatWidget'
import Configs from './pages/Config'
// import ProgBar from './components/ProgBar'
import StatusMsg from './components/StatusMsg'
import Grafy from './pages/grafy/Grafy';
import BucketGame from './pages/buckets/BucketGame'

function App() {

    const [loading, setLoading] = useState(false)
    const [msg, setMsg] = useState('ready');

    const showStatus = (msg, opts = { loading: false }) => {
        setMsg(msg)
        setLoading(opts.loading)
        console.log('status', msg)
    }

    useEffect(() => {
        // Update the document title using the browser API
        // sysCheck()
        console.log('running sysCheck')
        showStatus('loading', { loading: true })
        fetch('/api/syscheck')
            .then(response => {
                console.log('response', response)
                return response.json()
            })
            .then(data => showStatus(JSON.stringify(data, null, 2)));

    }, []);

    const appVersion = AppConfig.read('version')

    return (
        <div className="App">
            <Router>
                <div className='nav-bar'>
                    <Link to='/kzen/home'>
                        <div className='nav-button'>KZEN</div>
                    </Link>
                    <Link to='/kzen/grafy'>
                        <div className='nav-button'>Grafy</div>
                    </Link>
                    <Link to='/kzen/buckets'>
                        <div className='nav-button'>Buckets</div>
                    </Link>
                    <Link to='/kzen/linker'>
                        <div className='nav-button'>Linky</div>
                    </Link>
                    <Link to='/kzen/tuner'>
                        <div className='nav-button'>Tuney</div>
                    </Link>

                    <Link to='/kzen/benchmark'>
                        <div className='nav-button'>BenchMarky</div>
                    </Link>

                    <Link to='/kzen/testrunner'>
                        <div className='nav-button'>TestRunner</div>
                    </Link>

                    <Link to='/kzen/configs'>
                        <div className='nav-button'>Configs</div>
                    </Link>
                    <span className='version-info'>
                        v{appVersion}
                    </span>
                </div>

                <div className='main-panel'>
                    <Switch>
                        <Route path="/kzen/buckets">
                            <BucketGame />
                        </Route>
                        <Route path="/kzen/benchmark">
                            <Benchmark />
                        </Route>
                        <Route path="/kzen/testrunner">
                            <TestRunner />
                        </Route>
                        <Route path="/kzen/grafy">
                            <Grafy />
                        </Route>
                        <Route path="/kzen/tuner">
                            <Tuner />
                        </Route>
                        <Route path="/kzen/linker">
                            <Linker />
                        </Route>
                        <Route path="/kzen/experiment">
                            <Experiment />
                        </Route>
                        <Route path="/kzen/configs">
                            <Configs />
                        </Route>
                        <Route path="/">
                            <Home />
                            <StatusMsg msg={msg} />
                        </Route>

                    </Switch>

                </div>

            </Router>
        </div>
    );
}

export default App;
