document.addEventListener("DOMContentLoaded", function () {
    const socket = new WebSocket("ws://localhost:8001/ws/terminal/");
    const term = new Terminal();
    term.open(document.getElementById('terminal'));

    term.onData(data => {
        socket.send(data);
    });

    socket.onmessage = function (event) {
        term.write(event.data);
    };
});
