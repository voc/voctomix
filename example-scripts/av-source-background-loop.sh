while true; do cat ~/bg.ts || exit 1; done |\
	ffmpeg -re -i - \
	-map 0:v \
	-c:v rawvideo \
	-pix_fmt uyvy422 \
	-f matroska \
	tcp://localhost:16000
