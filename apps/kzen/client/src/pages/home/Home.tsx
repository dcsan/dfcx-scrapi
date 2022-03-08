import React from 'react';

import {
    Link
} from 'react-router-dom'


import AppConfig from '../../utils/AppConfig'
import { makeStyles } from '@material-ui/core/styles';
// import Paper from '@material-ui/core/Paper';
import Grid from '@material-ui/core/Grid';
// import Card from '@material-ui/core/Card';
// import CardActionArea from '@material-ui/core/CardActionArea';
// import CardActions from '@material-ui/core/CardActions';
// import CardContent from '@material-ui/core/CardContent';
// import CardMedia from '@material-ui/core/CardMedia';
// import Button from '@material-ui/core/Button';
// import HelpIcon from '@material-ui/icons/Help';
import HelpOutlineIcon from '@material-ui/icons/HelpOutline';
import IconButton from '@material-ui/core/IconButton';
// import Typography from '@material-ui/core/Typography';

import './home.css'

const useStyles = makeStyles((theme) => ({
    root: {
        flexGrow: 1,
        padding: '10px'
    },
    media: {
        height: 140,
    },
    paper: {
        padding: theme.spacing(2),
        textAlign: 'center',
        color: theme.palette.text.secondary,
        height: '100px'
    },
}));


function Home() {
    const classes = useStyles();

    const GridItem = (opts) => {
        const key = `k-${opts.title}`
        return (
            <Grid item xs={opts.size} key={key}>

                <div className='grid-box'>
                    <Link to={opts.link} className='stacked'>
                        <span className='tile-title'>
                            {opts.title}
                        </span>
                        <div>
                            {opts.subtitle}
                        </div>
                    </Link>
                    {opts.docs &&
                        <a href={opts.docs} target='docs' className='help-icon'>
                            <IconButton color="primary" component="span">
                                <HelpOutlineIcon />
                            </IconButton>
                        </a>
                    }
                </div>
            </Grid>
        )
    }

    const pages = AppConfig.read('pages')
    const gridTiles = pages.map(g => GridItem(g))

    return (
        <div className='content'>

            <div className='title'>
                <span className='h2'>
                    KZEN  v{AppConfig.read('version')}
                </span>
            </div>
            <div className={classes.root}>
                <Grid container spacing={1}>
                    {gridTiles}
                </Grid>
            </div>
        </div>
    );

}

export default Home;
