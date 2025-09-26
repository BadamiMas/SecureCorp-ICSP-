function startFaceLogin() {
    const video = document.getElementById("webcam");
    video.style.display = "block"; // show preview

    // Ask for webcam access
    navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        const video = document.getElementById("webcam");
        video.style.display = "block"; // show preview
        video.srcObject = stream;

        // Wait a moment then capture a snapshot
        setTimeout(() => {
            const canvas = document.createElement("canvas");
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext("2d");
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

            // Stop webcam
            stream.getTracks().forEach(track => track.stop());

            // Convert snapshot to base64
            const imageData = canvas.toDataURL("image/jpeg");
            console.log(imageData); // should start with "data:image/jpeg;base64,"

            // Send to Flask
            fetch("{{ url_for('face_login') }}", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ image: imageData })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    window.location.href = data.redirect; // go to dashboard
                } else {
                    alert(data.message);
                }
            })
            .catch(err => {
                console.error("Error:", err);
                alert("Something went wrong with face login");
            });
        }, 2000); // wait 2s so your face is ready
    })
    .catch(err => {
        console.error("Camera error:", err);
        alert("Unable to access camera");
    });
}