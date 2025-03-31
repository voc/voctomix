# https://gstreamer.freedesktop.org/documentation/video/gstvideo.html?gi-language=python


class GstVideoAlignment:
    padding_top: int
    padding_bottom: int
    padding_left: int
    padding_right: int
    stride_align: list[int]

    def reset(self) -> None: ...

def video_calculate_display_ratio(video_width: int, video_height: int, video_par_n: int, video_par_d: int, display_par_n: int, display_par_d: int) -> tuple[bool, int, int]: ...
def video_guess_framerate(duration: int) -> tuple[bool, int, int]: ...
def video_is_common_aspect_ratio(width: int, height: int, par_n: int, par_d: int) -> bool: ...

GST_META_TAG_VIDEO_COLORSPACE_STR = "colorspace"
GST_META_TAG_VIDEO_ORIENTATION_STR = "orientation"
GST_META_TAG_VIDEO_SIZE_STR = "size"
GST_META_TAG_VIDEO_STR = "video"
