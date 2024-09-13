"""
This the primary class for the Mario Expert agent. It contains the logic for the Mario Expert agent to play the game and choose actions.

Your goal is to implement the functions and methods required to enable choose_action to select the best action for the agent to take.

Original Mario Manual: https://www.thegameisafootarcade.com/wp-content/uploads/2017/04/Super-Mario-Land-Game-Manual.pdf
"""

import json
import logging
import random

import cv2
from mario_environment import MarioEnvironment
from pyboy.utils import WindowEvent
import numpy as np
import math
import time

class ACTIONDURATION:
    short = 1
    medium = 6
    long = 18
    no_action = -1
class GameElements:
         #Game elements
        EMPTY = 0
        MARIO = 1
        MYSTERY = 13
        PIPE = 14
        BLOCK = 10
        GOOMBA = 15
        KOOPA = 16
        JUMPING_MOB = 18
        FLYING_MOB = 19



class MarioController(MarioEnvironment):
    """
    The MarioController class represents a controller for the Mario game environment.

    You can build upon this class all you want to implement your Mario Expert agent.

    Args:
        act_freq (int): The frequency at which actions are performed. Defaults to 10.
        emulation_speed (int): The speed of the game emulation. Defaults to 0.
        headless (bool): Whether to run the game in headless mode. Defaults to False.
    """

    def __init__(
        self,
        act_freq: int = 10,
        emulation_speed: int = 0,
        headless: bool = False,
    ) -> None:
        super().__init__(
            act_freq=act_freq,
            emulation_speed=emulation_speed,
            headless=headless,
        )

        self.act_freq = act_freq

        # Example of valid actions based purely on the buttons you can press
        valid_actions: list[WindowEvent] = [
            WindowEvent.PRESS_ARROW_DOWN,
            WindowEvent.PRESS_ARROW_LEFT,
            WindowEvent.PRESS_ARROW_RIGHT,
            WindowEvent.PRESS_ARROW_UP,
            WindowEvent.PRESS_BUTTON_A,
            WindowEvent.PRESS_BUTTON_B,
        ]

        release_button: list[WindowEvent] = [
            WindowEvent.RELEASE_ARROW_DOWN,
            WindowEvent.RELEASE_ARROW_LEFT,
            WindowEvent.RELEASE_ARROW_RIGHT,
            WindowEvent.RELEASE_ARROW_UP,
            WindowEvent.RELEASE_BUTTON_A,
            WindowEvent.RELEASE_BUTTON_B,
        ]

        self.valid_actions = valid_actions
        self.release_button = release_button

    def run_action(self, action, duration : int) -> None:
        """
        This is a very basic example of how this function could be implemented

        As part of this assignment your job is to modify this function to better suit your needs

        You can change the action type to whatever you want or need just remember the base control of the game is pushing buttons
        """

        if not isinstance(action, list):
            action = [action]

        if duration == ACTIONDURATION.no_action:
            for _ in range(self.act_freq):
                self.pyboy.tick()
            return
        
        for act in action:
            # Simply toggles the buttons being on or off for a duration of act_freq
            self.pyboy.send_input(self.valid_actions[act])
        
        for _ in range(duration):
            self.pyboy.tick()
        
        for act in action:
            self.pyboy.send_input(self.release_button[act])



class MarioExpert:
    """
    The MarioExpert class represents an expert agent for playing the Mario game.

    Edit this class to implement the logic for the Mario Expert agent to play the game.

    Do NOT edit the input parameters for the __init__ method.

    Args:
        results_path (str): The path to save the results and video of the gameplay.
        headless (bool, optional): Whether to run the game in headless mode. Defaults to False.
    """

    def __init__(self, results_path: str, headless=False):
        self.results_path = results_path

        self.environment = MarioController(headless=headless)

        self.video = None

    def choose_action(self):
        state = self.environment.game_state()
        frame = self.environment.grab_frame()
        game_area = self.environment.game_area()

        #actions
        move_forward_action = self.environment.valid_actions.index(WindowEvent.PRESS_ARROW_RIGHT)
        jump_action = self.environment.valid_actions.index(WindowEvent.PRESS_BUTTON_A)
        long_jump_action = [move_forward_action, jump_action]
        move_backward_action = self.environment.valid_actions.index(WindowEvent.PRESS_ARROW_LEFT)

        def get_element_positions(game_area=game_area, element=GameElements.MARIO):
            element_positions = np.argwhere(game_area == element)
            if element_positions.size > 0:
                return [(pos[1], pos[0]) for pos in element_positions]
            return []
        
        # Get the position of the elements
        mario_pos = get_element_positions(game_area, GameElements.MARIO)
        mario_x, mario_y = mario_pos[0] if mario_pos else (0,0)
        goomba_pos = get_element_positions(game_area, GameElements.GOOMBA)
        koopa_pos = get_element_positions(game_area, GameElements.KOOPA)
        pipe_pos = get_element_positions(game_area, GameElements.PIPE)
        block_pos = get_element_positions(game_area, GameElements.BLOCK)
        jumping_mob_pos = get_element_positions(game_area, GameElements.JUMPING_MOB)
        flying_mob_pos = get_element_positions(game_area, GameElements.FLYING_MOB)
        mystery_pos = get_element_positions(game_area, GameElements.MYSTERY)
        print(mystery_pos)
        mario_pov = 2

        #goomba check
        if goomba_pos:
            for goomba_x, goomba_y in goomba_pos:
                if ((mario_x + mario_pov) >= goomba_x) and (goomba_x > mario_x):
                    if abs(mario_y - goomba_y) == 1:
                        return long_jump_action, ACTIONDURATION.long
                    
        #koopa check
        if koopa_pos:
            for koopa_x, koopa_y in koopa_pos:
                if ((mario_x + mario_pov) >= koopa_x) and (koopa_x > mario_x):
                    if abs(mario_y - koopa_y) == 1:
                        return long_jump_action, ACTIONDURATION.medium
        
        #jumping_mob check
        if jumping_mob_pos:
            for jumping_mob_x, jumping_mob_y in jumping_mob_pos:
                if ((mario_x + (mario_pov + 2)) >= jumping_mob_x) and (jumping_mob_x > mario_x):
                    if abs(mario_y - jumping_mob_y) == 2:
                        return jump_action, ACTIONDURATION.medium
        
        if flying_mob_pos:
            for flying_mob_x, flying_mob_y in flying_mob_pos:
                if (mario_y - flying_mob_y) == 0:
                    return move_backward_action, ACTIONDURATION.medium
                elif ((mario_x + mario_pov + 2) >= flying_mob_x) and (flying_mob_x > mario_x):
                    return long_jump_action, ACTIONDURATION.medium
                
        #pipe check
        if pipe_pos:
            pipe_x, pipe_y = pipe_pos[0]    

            # Tall Pipe is in front of Mario with goomba on top wait for the goomba to move
            if (pipe_x == 13 and pipe_y == 7) and (goomba_x > mario_x):
                return ACTIONDURATION.no_action, ACTIONDURATION.medium

            if (mario_x + 4) == pipe_x:
                if abs(mario_y - pipe_y) <= 2:
                    return long_jump_action, ACTIONDURATION.medium      
            elif (mario_x + 2) == pipe_x:
                if abs(mario_y - pipe_y) <= 2:
                    return long_jump_action, ACTIONDURATION.medium
        
         # if hole in front of mario, long jump
        if ((mario_y + 2) < game_area.shape[0]) and ((mario_x + 2) < game_area.shape[1]):
            if game_area[mario_y + 2][mario_x + 2] == 0 and game_area[15][mario_x + 2] == 0:  # Check for a hole two steps ahead
                return long_jump_action, ACTIONDURATION.short
            
         #block check
        if block_pos:
            for block_x, block_y in block_pos:
                # Case 1: Block is directly in front of Mario (obstacle)
                if (mario_x + mario_pov) == block_x:
                    if abs(mario_y - block_y) == 1:
                        return long_jump_action, ACTIONDURATION.short     
        # time.sleep(0.1)

        # If no obstacle detected, move right
        return move_forward_action, ACTIONDURATION.medium

    def step(self):
        """
        Modify this function as required to implement the Mario Expert agent's logic.

        This is just a very basic example
        """

        # Choose an action - button press or other...
        action, duration = self.choose_action()

        # Run the action on the environment
        self.environment.run_action(action, duration)

    def play(self):
        """
        Do NOT edit this method.
        """
        self.environment.reset()

        frame = self.environment.grab_frame()
        height, width, _ = frame.shape

        self.start_video(f"{self.results_path}/mario_expert.mp4", width, height)

        while not self.environment.get_game_over():
            frame = self.environment.grab_frame()
            self.video.write(frame)

            self.step()

        final_stats = self.environment.game_state()
        logging.info(f"Final Stats: {final_stats}")

        with open(f"{self.results_path}/results.json", "w", encoding="utf-8") as file:
            json.dump(final_stats, file)

        self.stop_video()

    def start_video(self, video_name, width, height, fps=30):
        """
        Do NOT edit this method.
        """
        self.video = cv2.VideoWriter(
            video_name, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
        )

    def stop_video(self) -> None:
        """
        Do NOT edit this method.
        """
        self.video.release()
