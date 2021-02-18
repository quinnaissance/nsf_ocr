import re
import cv2
import sys
#import pushover # For notifications
import numpy as np
import pytesseract as tess
import stream_tools as yt


# Stream links
NSF_CHANNEL = R'https://www.youtube.com/channel/UCSUu1lih2RifWkKtDOJdsBA'
NSF_STREAMS = R'https://www.youtube.com/c/NASASpaceflightVideos/videos?view=2&live_view=501'

# Initial crop values
CROP_X = 0
CROP_Y = 68 # 68 to skip top banner
CROP_W = 250
CROP_H = 800

# Area range to filter white current status box
MIN_AREA = 4000
MAX_AREA = 10000

# OpenCV image for test purposes
PRESET_IMAGE = "nsf3.jpg"


def res_check(img,width,height): # Verify image resolution
    return img.shape[1] == width and img.shape[0] == height

# Receive target contour ndarray and img
# Input should look roughly like: [ [[x y]] [[x y]] [[x y]] [[x y]] ]
def crop_img_from_contours(array, img):
    if len(array) != 4: # Verify input is a 4-sided shape
        print("Invalid number of contour points (looking for 4)")
        return img
    # Could add verification that coordinates line up
    else:
        # Coordinates are ordered counter-clockwise starting from top left
        # (0,1),(2,3),(4,5),(6,7) where 0=2, 1=7, 3=5, 4=6
        flat = array.flatten() # Flatten into 1-dimensional list
        x = flat[0] 
        y = flat[1]
        w = flat[4] - flat[0]
        h = flat[3] - flat[1]
        cropped_img = img[y:y+h, x:x+w]
        return cropped_img

def main():
    
    # Does channel have any streams?
    if not yt.channel_is_streaming:
        print("ERROR: No streams detected on channel")
        sys.exit()

    # Find the proper stream
    # Could definitely use something smarter here, but should work for now
    stream_list = yt.list_channel_streams(NSF_STREAMS)
    target_stream = []
    for stream in stream_list:
        # Look for SN## in stream title -> get first match
        if re.search("SN[0-9]{1,2}",stream[0]) != None:
            print("MATCHING STREAM FOUND")
            target_stream.append(stream)
            break
    
    if len(target_stream) > 1:
        print("Multiple target streams detected")
        sys.exit()
    
    if len(target_stream) == 0:
        print("No matching stream found")
        sys.exit()
    
    stream_img_file = yt.get_screen_from_yt_link(target_stream[0][1])
    if stream_img_file == "":
        print("Unable to fetch image from livestream")
        sys.exit()
    
    img = cv2.imread(PRESET_IMAGE) #stream_img_file

    # Image resolution check
    if res_check(img,1920,1080) == False:
        print("Image resolution is not 1920x1080")
        sys.exit()

    # Initial rough crop
    crop_img = img[CROP_Y:CROP_Y+CROP_H, CROP_X:CROP_X+CROP_W]

    # Greyscale, threshold, then find contours
    gray = cv2.cvtColor(crop_img,cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(gray, 235, 255, cv2.THRESH_BINARY) #235,255 to isolate white
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours to find a quadrilateral with a specific area range
    target_set = [] # save ndarray of contour vertices matching certain criteria
    for i in contours:
        area = cv2.contourArea(i)
        if area > MIN_AREA and area < MAX_AREA and len(i) == 4: # Pass the area requirements
            target_set = i
            #print("Current status area: " + str(area) + " | Vertices: " + str(len(i)))
            #cv2.drawContours(crop_img, [i], -1, (25,25,255), 2) # Visualize
            break # Force maximum of 1 match
    
    # No matching item found
    if len(target_set) == 0:
        print("No matching current status box found")
        sys.exit()
    
    # Final crop
    final_crop_img = crop_img_from_contours(target_set, crop_img)

    #Show images # ! (requires OpenCV GUI)
    window_name = 'output_img'
    #cv2.imshow(window_name, img)
    #cv2.waitKey(0)
    cv2.imshow(window_name, crop_img)
    cv2.waitKey(0)
    #cv2.imshow(window_name, gray)
    #cv2.waitKey(0)
    #cv2.imshow(window_name, thresh)
    #cv2.waitKey(0)
    #cv2.imshow(window_name, thresh2)
    #cv2.waitKey(0)
    #cv2.imshow(window_name, thresh2_invert)
    #cv2.waitKey(0)
    cv2.imshow(window_name, final_crop_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # OCR
    # ! Seems to work better with black text on white bg
    ocr_text = tess.image_to_string(final_crop_img, config='--psm 7')
    ocr_clean = re.findall("[A-Z].*", ocr_text)
    if re.search("\w+",ocr_clean[0]) != None:
        print(ocr_clean[0])
    else:
        print("Unable to OCR final crop")
        sys.exit()
    
if __name__ == "__main__":
    main()
