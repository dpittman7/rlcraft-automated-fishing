import cv2
import numpy as np
import pyautogui
import time
from threading import Thread, Lock
from screeninfo import get_monitors

def handle_key_inputs():
    global right_key_down, left_key_down
    was_right_key_down = False
    was_left_key_down = False

    while True:
        with lock:
            if right_key_down and not was_right_key_down:
                pyautogui.keyDown('right')
                was_right_key_down = True
            elif not right_key_down and was_right_key_down:
                pyautogui.keyUp('right')
                was_right_key_down = False

            if left_key_down and not was_left_key_down:
                pyautogui.keyDown('left')
                was_left_key_down = True
            elif not left_key_down and was_left_key_down:
                pyautogui.keyUp('left')
                was_left_key_down = False

        time.sleep(0.001)

# Define the paths of the sprite templates
sprite_paths = {'fish': 'fish.png', 'green_block': 'green_block.png', 'minigame_n': 'minigame_n.png', 'minigame_d': 'minigame_d.png'}

# Load the sprite templates and store them in a dictionary along with their dimensions
sprites = {}
for name, path in sprite_paths.items():
    sprite = cv2.imread(path, 0)
    h, w = sprite.shape[:2]
    sprites[name] = (sprite, w, h)

# Find the position and dimensions of the minigame sprite on the screen
minigame_active = False
while not minigame_active:
    print('loop')
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    gray = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)


    minigame_sprite_day, w_d, h_d = sprites['minigame_d']
    result_d = cv2.matchTemplate(gray, minigame_sprite_day, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result_d)
    if (max_val) > .65:
        minigame_active = True
        x, y = max_loc[0], max_loc[1]
        width, height = w_d, h_d
    else:
        print(max_val)
    minigame_sprite_night, w_n, h_n = sprites['minigame_n']
    result_n = cv2.matchTemplate(gray, minigame_sprite_night, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result_n)
    if (max_val) > .65:
        minigame_active = True
        x, y = max_loc[0], max_loc[1]
        width, height = w_n, h_n
   
    else:
        print(max_val)



print(x,y,width,height)

# Get the coordinates of the monitor you want to capture
#monitor = get_monitors()[0]
#x, y, width, height = monitor.x, monitor.y, monitor.width, monitor.height

right_key_down = False
left_key_down = False

# Initialize threading lock
lock = Lock()

def calculate_distance(x1, x2):
    return abs(x1 - x2)

threshold = 0.6  

key_input_thread = Thread(target=handle_key_inputs)
key_input_thread.daemon = True
key_input_thread.start()

while True:
    # Capture the specified screen using the coordinates
    screenshot = pyautogui.screenshot(region=(x, y, width, height))
    screenshot_np = np.array(screenshot)
    frame = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2RGB)
    
    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    positions = {}
    
    for name, (sprite, w, h) in sprites.items():
        # Apply template matching for each sprite template
        result = cv2.matchTemplate(gray, sprite, cv2.TM_CCOEFF_NORMED)
        
        # Locate the position of the sprite
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val > threshold:
            top_left = max_loc
            bottom_right = (top_left[0] + w, top_left[1] + h)
            
            # Draw a rectangle around the detected sprite
            cv2.rectangle(frame, top_left, bottom_right, (0, 255, 0), 2)
            
            # Store the positions of the sprites
            positions[name] = (top_left, bottom_right)

    # Check the relative positions of green_block and fish and trigger the appropriate key
    if 'green_block' in positions and 'fish' in positions:
        green_block_x = positions['green_block'][0][0]
        green_block_right = positions['green_block'][1][0]
        fish_x = positions['fish'][0][0]
        fish_right = positions['fish'][1][0]
        
        # Check if the sprites are overlapped
        overlapped = not (green_block_right < fish_x or green_block_x > fish_right)
        
        
        with lock:
            if overlapped:
                if right_key_down:
                    pyautogui.keyUp('right')
                    right_key_down = False
                if left_key_down:
                    pyautogui.keyUp('left')
                    left_key_down = False
            else:
                right_key_down = green_block_x < fish_x
                left_key_down = green_block_x > fish_x

        print(left_key_down, right_key_down)
    
    # Display the result
    cv2.imshow('Detected Sprites', frame)
    
    # Break the loop if the 'ESC' key is pressed
    if cv2.waitKey(1) == 27:
        break

cv2.destroyAllWindows()

# Define a function to handle key inputs
