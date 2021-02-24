# Dependencies
* Firefox
* BeautifulSoup
* selenium (with [geckodriver.exe](https://github.com/mozilla/geckodriver/releases) in PATH)
* opencv-python (using 4.5.1) __with GUI__
* youtube-dl
* ffmpeg
* pytesseract — must be with 14MB [eng.traineddata](https://github.com/tesseract-ocr/tessdata_best/blob/master/eng.traineddata) (replace the 4MB one)

# TODO List
* Account for missing checklist more dynamically
  * Add log to keep track of previous detections and calculate time since
* Use line detection instead of contours to detect the box is on screen
* Verify initial crop and min/max area values based on real data
* Add more comprehensive crop for entire checklist (can use ```cv2.vconcat```)
* Filter to check for duplicate crops (use ```cv2.compareHist``` with thresh2?)
  * Avoids running through entire thing every time
* Split checklist using ```cv2.reduce``` to read every line separately
  * Can get sequence number
* Figure out some way to share the info openly
* Add a flag to delete captured images after
* Add timeouts, exceptions & cleaner prints
* Add coordinate sorting to ```crop_img_from_contours```

## Known Issues
* Sometimes ```get_stream_screenshot``` takes excessively long; this is an ffmpeg issue that I haven't figured out yet
* There may be some issues running from a batch file due to working directories and where the images are being saved. Have to look into this more.

## Changelog
* **2021-02-23**: Added fix for case where ```findContours``` returns redundant vertices and made a couple things more streamlined