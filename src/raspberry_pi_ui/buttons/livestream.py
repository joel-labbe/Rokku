import json
import logging
import logging.config
import os

import yaml

from src.raspberry_pi_ui import embedded_yt, message_box
from src.raspberry_pi_ui.buttons.button import Button
from src.raspberry_pi_ui.utility import set_button_property, wait_msg


class LivestreamButton(Button):
    """A wrapper class representing the talk button widget on UI.

    Inherit from parent class Button
    """

    def __init__(self, button, pub, msg_q, camera_flags):
        """Constructor of the class, which inherit from Button class"""
        super().__init__(button, pub, msg_q, "Live Stream")

        # unique functionality flags
        self.livestream = False

        # variables to catch youtube links sent back (Strings)
        self.yt_livestream_link = None

        self.camera_flags = camera_flags

        # set up logger
        with open(
            f"{os.path.dirname(__file__)}/../../../logger_config.yaml", "r"
        ) as f:
            config = yaml.safe_load(f.read())
            logging.config.dictConfig(config)
        self.logger = logging.getLogger("LivestreamButton")

    def on_clicked(self, widget):
        """Callback when `Live Stream` button is clicked.

        This will be called on whenever the Live Stream button is clicked
        First will communicate with rpi_out to see if a clip is being
        recorded or the livestream is already on and will set the
        self.livestream flag accordingly.

        If livestreaming still, turn off livestream and close window

        If not livestreaming, send signal to livestream, open window and set self.livestream
        accordingly.
        """
        if not self.camera_flags["recording_on"]:
            self.camera_flags["livestream_on"] = True
            self.logger.info("Sending livestream ON message to rpi_out...")
            self.pub.publish(json.dumps(["livestream", True]))
            try:  # wait for rpi_out to send true msg back
                self.livestream = wait_msg(
                    "livestream", self.logger, self.msg_q
                )[1]
                # True sent back
                if self.livestream:
                    # Since rpi_out sent back true it should be livestreaming
                    self.logger.info("rpi_out is livestreaming now...")
                    # turn button to red if not already red
                    set_button_property(self, "red", "Livestreaming...")
                    try:
                        # waiting for rpi_out to send youtube playlist link
                        self.yt_livestream_link = wait_msg(
                            "yt_livestream_link",
                            self.logger,
                            self.msg_q,
                            timeout=30,
                        )[1]
                        # Does not catch if junk str was sent back
                        if type(self.yt_livestream_link) == str:
                            # display window with livestream
                            yt_window = embedded_yt.EmbeddedYT(
                                self.yt_livestream_link, "Livestream"
                            )
                            yt_window.run()
                    except IndexError:  # no message received
                        self.logger.error(
                            f"The camera is running, Mqtt broke or the YouTube Api broke. Live Stream status: rpi_in = {self.livestream}"
                        )
                        # Change flags
                        self.camera_flags["livestream_on"] = False
                        self.livestream = False
                        # Turn livestream off
                        self.pub.publish(json.dumps(["livestream", True]))
                        # Reset button to blue
                        set_button_property(self, "blue", "Livestream")
                        # Log event
                        self.logger.info("Livestream is off...")
                        # display message to try again later
                        message = message_box.MessageBox(
                            "Sorry, something broke...",
                            "Please try again later.",
                        )
                        message.run()
                elif self.livestream is None:
                    self.logger.error(
                        f"The camera is running, Mqtt broke or the YouTube Api broke. Live Stream status: rpi_in = {self.livestream}"
                    )
                    # Change flag
                    self.camera_flags["livestream_on"] = False
                    self.livestream = False
                    # display message to wait for recording to be done
                    message = message_box.MessageBox(
                        "Sorry, but...",
                        "A video is being recorded, please try again later.",
                    )
                    message.run()
                else:
                    # Change flags
                    self.camera_flags["livestream_on"] = False
                    # Log event
                    self.logger.info("Turned off rpi_out livestream...")
                    # Reset button to blue
                    set_button_property(self, "blue", "Livestream")
                    # close livestream window
                    #########################
                    #   Missing code        #
                    #########################
            except IndexError:  # no message received
                # Log event
                self.logger.error(
                    f"The camera is running, Mqtt broke or the YouTube Api broke. Live Stream status: rpi_in = {self.livestream}"
                )
                # Change flags
                self.livestream = False
                self.camera_flags["livestream_on"] = False
                # Reset button to blue
                set_button_property(self, "blue", "Livestream")
                # Log event
                self.logger.info("Livestream is off...")
                # display message saying to try again later
                message = message_box.MessageBox(
                    "Sorry, something broke...", "Please try again later."
                )
                message.run()
