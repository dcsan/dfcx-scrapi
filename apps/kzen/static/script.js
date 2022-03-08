'use strict';

window.addEventListener('load', function () {
  console.log("Hello World!");
});

function multiTest() {
    showStatus('running multiTest 2')
    fetch('/run/multitest')
        .then(response => response.json())
        .then(data => showStatus(JSON.stringify(data, null, 2)));
}

function sysCheck() {
    console.log('running sysCheck')
    showStatus('loading')
    fetch('/syscheck')
        .then(response => response.json())
        .then(data => showStatus(JSON.stringify(data, null, 2)));

}

function showStatus(msg) {
    console.log(msg)
    document.getElementById("status-box").innerHTML=msg; 
}