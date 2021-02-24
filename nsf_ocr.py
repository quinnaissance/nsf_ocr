import os
import sys
import re
import cv2
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

# Area range to filter current status box
MIN_AREA = 4000
MAX_AREA = 10000

# OpenCV image for test purposes
PRESET_IMG = "samples/nsf1.jpg"

# Output image GUI window name
WINDOW_NAME = 'window'

# Delete images grabbed from stream after OCRing
DELETE_OUTPUT_IMG = True

# Output filenames
OUTPUT_IMG = "" # Fetched stream screenshot
OUTPUT_MSG = "" # Final OCR output

# Clear console
def cls():
    os.system('cls')

# If the delete flag is enabled, get rid of the generated image
def image_cleanup(filename):
    if DELETE_OUTPUT_IMG and filename != "":
        if os.path.exists(filename):
            os.remove(filename)
            print(f"Output image {filename} deleted")
        else:
            print(f"Cannot locate {filename} for deletion")

# Verify image resolution
def res_check(img,width,height):
    if "numpy.ndarray" in str(type(img)):
        return img.shape[1] == width and img.shape[0] == height
    else:
        return False

# Receive target contour ndarray and img
# Input should look roughly like: [ [[x y]] [[x y]] [[x y]] [[x y]] ]
def crop_img_from_contours(array, img):
    if len(array) != 4: # Verify input is a 4-sided shape
        print("Invalid number of contour points for crop_img_from_contours (need 4)")
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
    
    # Does the channel have any streams?
    if not yt.channel_is_streaming(NSF_CHANNEL):
        print("No streams detected on channel")
        sys.exit()

    # Find the proper stream
    # Could definitely use something smarter here, but should work for now
    stream_list = yt.list_channel_streams(NSF_STREAMS)
    target_stream = []
    for stream in stream_list:
        # Look for SN## in stream title -> get first match
        if re.search("SN[0-9]{1,2}",stream[0]) != None:
            print("Matching stream found")
            target_stream.append(stream)
            break
    
    if len(target_stream) > 1:
        print("Multiple target streams detected")
        sys.exit()
    
    if len(target_stream) == 0:
        print("No matching stream found")
        sys.exit()
    
    # Get screenshot from youtube link
    stream_img_file = yt.get_screen_from_yt_link(target_stream[0][1])
    if stream_img_file == "":
        print("Unable to fetch image from livestream")
        sys.exit()
    else:
        OUTPUT_IMG = stream_img_file
        print("Output image " + OUTPUT_IMG + " created")
    
    # Load image into memory then delete the file (if desired)
    img = cv2.imread(OUTPUT_IMG) #! PRESET_IMG or OUTPUT_IMG
    image_cleanup(OUTPUT_IMG)

    # Image resolution check
    if res_check(img,1920,1080) != True:
        print("Image resolution is not 1920x1080")
        sys.exit()

    # Rough initial crop
    crop_img = img[CROP_Y:CROP_Y+CROP_H, CROP_X:CROP_X+CROP_W]

    # Greyscale, threshold, then find contours
    gray = cv2.cvtColor(crop_img,cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(gray, 235, 255, cv2.THRESH_BINARY) #235,255 to isolate white
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    #cv2.drawContours(crop_img, contours, -1, (0,0,255), 2) # Draw ALL contours

    # Filter contours to find a quadrilateral with a specific area range
    target_set = [] # save ndarray of contour vertices matching certain criteria
    for i in contours:
        area = cv2.contourArea(i)
        length = len(i)

        # Area requirements
        if area > MIN_AREA and area < MAX_AREA: 
            #cv2.drawContours(crop_img, [i], -1, (25,25,255), 1)

            # Verify quadrilateral
            if length == 4:
                target_set = i
                #print("Current status area: " + str(area) + " | Vertices: " + str(len(i)))
                break # Force maximum of 1 match
            
            # Too many vertices; filter out redundant ones
            if length > 4 and length < 14:
                epsilon_max = 0.001
                fixed = cv2.approxPolyDP(i, epsilon_max*cv2.arcLength(i,True), closed=True)
                # Keep incrementing epsilon until polygon is 4 points or it clearly isnt a square
                while len(fixed) > 4 or epsilon_max > 0.1:
                    epsilon_max += 0.001
                    fixed = cv2.approxPolyDP(i, epsilon_max*cv2.arcLength(i,True), closed=True)
                #cv2.drawContours(crop_img, [fixed], -1, (0,255,0), 1)
                if epsilon_max >= 0.1:
                    print("Detected shape is too distorted")
                    break
                else:
                    target_set = fixed
                    break

    # No matching item found
    if len(target_set) == 0:
        print("No matching current status box found")
        sys.exit()
    
    # Final crop
    if len(target_set) == 4:
        final_crop_img = crop_img_from_contours(target_set, crop_img)

    #Show images #! (requires OpenCV GUI)
    #cv2.imshow(WINDOW_NAME, img)
    #cv2.waitKey(0)
    #cv2.imshow(WINDOW_NAME, crop_img)
    #cv2.waitKey(0)
    #cv2.imshow(WINDOW_NAME, gray)
    #cv2.waitKey(0)
    #cv2.imshow(WINDOW_NAME, thresh)
    #cv2.waitKey(0)
    #cv2.imshow(WINDOW_NAME, final_crop_img)
    #cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    # OCR
    #! Seems to work better with black text on white bg
    ocr_text = tess.image_to_string(final_crop_img, config='--psm 7')
    ocr_clean = re.findall("[A-Z].*", ocr_text)
    #dict = re.findall("\w+",ocr_text)

    # Simple check that the OCR has *something* in it
    if re.search("\w+",ocr_clean[0]) != None:
        OUTPUT_MSG = ocr_clean[0]
        print("Status: " + OUTPUT_MSG)
    else:
        print("Unable to OCR final crop")
        sys.exit()

if __name__ == "__main__":
    main()
