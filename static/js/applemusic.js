
document.addEventListener("DOMContentLoaded", function () {
//document.addEventListener("musickitloaded", function () {
    console.log("DEV_TOKEN type:", typeof DEV_TOKEN);
    console.log("DEV_TOKEN len:", DEV_TOKEN?.length);
    console.log("DEV_TOKEN head:", String(DEV_TOKEN).slice(0, 20));

    MusicKit.configure({ 
       developerToken: DEV_TOKEN, app: { name: "make play list", build: "1.0" } });

    const music = MusicKit.getInstance();

    if (localStorage.getItem("userToken")) {
        music._userToken = localStorage.getItem("userToken");
        document.getElementById("log").textContent = "인증되어 있습니다.";
        document.getElementById("authorize").textContent = "Unauthorize";

        try {
            userToken = music._userToken 
            console.log("Send1 userToken:", userToken);
    
            fetch("/receive_token", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ userToken })
            })
            .then(res => res.json())
            .then(data => {
                console.log("Server response:", data);
            })
            .catch(err => console.error(err));
        } catch (err) {
            console.error("Authorization failed:", err);
        }
    }
});

document.getElementById("authorize").addEventListener("click", async function () {
    const music = MusicKit.getInstance();
    userToken = "";

    if(music.isAuthorized === true) {
        await music.unauthorize();
        document.getElementById("log").textContent = "인증되어 있지 않습니다.";
        document.getElementById("authorize").textContent = "Authorize";
        localStorage.removeItem("userToken");
    } else {
        userToken = await music.authorize();
        localStorage.setItem("userToken", userToken); 
        document.getElementById("log").textContent = "인증되어 있습니다.";
        document.getElementById("authorize").textContent = "Unauthorize";
        console.log("userToken:", userToken);
    }

    try {

        console.log("Send2 userToken:", userToken);

        fetch("/receive_token", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ userToken })
        })
        .then(res => res.json())
        .then(data => {
            console.log("Server response:", data);
        })
        .catch(err => console.error(err));
    } catch (err) {
        console.error("Authorization failed:", err);
    }
});

document.getElementById("makePlaylistButton").addEventListener("click", () => {
    
    const music = MusicKit.getInstance();
    if (music.isAuthorized === false) {
        document.getElementById("log").textContent = "사용자 인증이 필요합니다.";
        return;
    }

    document.body.classList.add("waiting");
    document.getElementById("makePlaylistButton").classList.add("waiting");

    const prompt = document.getElementById("promptInput").value;
    const count = document.getElementById("count").value;

    document.getElementById("log").textContent = prompt + " 플레이리스트 작성중..."
    
    try {

        fetch("/make_playlist", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt, count })
        })
        .then(res => res.json())
        .then(data => {
            document.body.classList.remove("waiting");
            document.getElementById("makePlaylistButton").classList.remove("waiting");
            console.log("Server response:", data);
            if (data.status === "fail") {
                document.getElementById("log").textContent = "플레이리스트 작성 실패!";
            } else if (data.status === "nolist") {
                document.getElementById("log").textContent = "추천된 곡이 없습니다. 다르게 다시 한번 입력하세요.";
            } else if (data.status === "nousertoken") {
                document.getElementById("log").textContent = "사용자 토큰이 없습니다. 먼저 인증을 해주세요.";                
            } else {
                document.getElementById("log").textContent = "플레이리스트 작성 완료!";
            }
        })
        .catch(err => console.error(err));
    } catch (err) {
        document.body.classList.remove("waiting");
        document.getElementById("makePlaylistButton").classList.remove("waiting");
        console.error("REST make playlist fail : ", err);
    }    
});


// 서버로부터 실시간 상태 수신 (SSE)
const eventSource = new EventSource("/status");

eventSource.onmessage = (event) => {
    if (event.data === "request") {
        document.getElementById("log").textContent = "chatGPT 에게 요청중...";
    } else if (event.data == "find") {
        document.getElementById("log").textContent = "Apple Music 에서 찾는중...";
    } else if (event.data == "make") {
        document.getElementById("log").textContent = "플레이리스트 작성 중...";
    }
    console.log("상태 수신:", event.data);
};

eventSource.onerror = (error) => {
    console.error("SSE 연결 오류:", error);
    eventSource.close();
};

