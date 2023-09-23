import cv2
import numpy as np
import pyautogui
from threading import Thread, Lock, Condition

def load_sprites(sprite_paths):
    sprites = {}
    for name, path in sprite_paths.items():
        sprite = cv2.imread(path, 0)
        h, w = sprite.shape[:2]
        sprites[name] = (sprite, w, h)
    return sprites

def find_minigame_position(sprites, threshold=0.65):
    minigame_active = False
    while not minigame_active:
        screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        gray = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)

        for minigame_sprite_name in ['minigame_d', 'minigame_n']:
            minigame_sprite, w, h = sprites[minigame_sprite_name]
            result = cv2.matchTemplate(gray, minigame_sprite, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val > threshold:
                minigame_active = True
                return max_loc[0], max_loc[1], w, h

def handle_key_inputs(lock, condition):
    global right_key_down, left_key_down
    was_right_key_down = False
    was_left_key_down = False

    while True:
        with condition:
            condition.wait()  # Wait for a signal that the state has changed
            
            with lock:
                # Handle the state change
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

def minigame_handler(sprites, x, y, width, height, lock, condition, threshold=0.6):
    screenshot = pyautogui.screenshot(region=(x, y, width, height))
    screenshot_np = np.array(screenshot)
    frame = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    positions = {}

    for name, (sprite, w, h) in sprites.items():
        result = cv2.matchTemplate(gray, sprite, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val > threshold:
            top_left = max_loc
            bottom_right = (top_left[0] + w, top_left[1] + h)
            positions[name] = (top_left, bottom_right)
            cv2.rectangle(frame, top_left, bottom_right, (0, 255, 0), 2)

    if 'green_block' in positions and 'fish' in positions:
        green_block_x = positions['green_block'][0][0]
        fish_x = positions['fish'][0][0]
        
        with lock:
            global right_key_down, left_key_down
            new_right_key_down = green_block_x < fish_x
            new_left_key_down = green_block_x > fish_x
            
            if new_right_key_down != right_key_down or new_left_key_down != left_key_down:
                right_key_down = new_right_key_down
                left_key_down = new_left_key_down
                with condition:
                    condition.notify()  # Notify handle_key_inputs of a state change

    return frame

if __name__ == "__main__":
    sprite_paths = {
        'fish': 'fish.png',
        'green_block': 'green_block.png',
        'minigame_n': 'minigame_n.png',
        'minigame_d': 'minigame_d.png',
        'rod_active': 'rod_active.png',
        'rod_neutral': 'rod_neutral.png'
    }

    sprites = load_sprites(sprite_paths)
    x, y, width, height = find_minigame_position(sprites)

    right_key_down = False
    left_key_down = False
    lock = Lock()
    condition = Condition()

    key_input_thread = Thread(target=handle_key_inputs, args=(lock, condition))
    key_input_thread.daemon = True
    key_input_thread.start()

    while True:
        minigameFrame = minigame_handler(sprites, x, y, width, height, lock, condition)
        cv2.imshow('Detected Sprites', minigameFrame)
        if cv2.waitKey(1) == 27:
            break

    cv2.destroyAllWindows()
