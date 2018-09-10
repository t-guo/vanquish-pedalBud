from flask import request
import requests
import json


class SaferWayBotActions(object):

    def __init__(self, bot, fb_verify_token, message_templates):
        self.bot = bot
        self.FB_VERIFY_TOKEN = fb_verify_token
        self.message_templates = message_templates
        self.sessions = {}

    def verify_fb_token(self, token_sent):
        """take token sent by facebook and verify it"""
        if token_sent == self.FB_VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return 'Invalid verification token'

    def ask_destination_location(self, recipient_id):

        user_first_name = self.get_user_first_name(recipient_id)

        self.bot.send_raw(
            {
                "message": {
                    "text": self.message_templates["start_message"].format(name=user_first_name),
                    "quick_replies":
                        [{"content_type": "location"}]
                },
                'recipient': {
                    'id':  recipient_id
                }
            }
        )

    def end_service(self, recipient_id):

        self.bot.send_text_message(
            recipient_id,
            self.message_templates["end_message"]
        )

    def ask_current_location(self, recipient_id):

        self.bot.send_raw(
            {
                "message": {
                    "text": "Where are we starting this trip?",
                    "quick_replies":
                        [{"content_type": "location"}]
                },
                'recipient': {
                    'id':  recipient_id
                }
            }
        )

    def ask_end_navigation(self, recipient_id):
        self.bot.send_button_message(recipient_id,
                                     self.message_templates["ask_end_message"],
                                     self.message_templates["ask_end_button"])

    def help_navigate(self, recipient_id, routes, url):

        elements = []

        for index, item in enumerate(routes):
            title = "via " + item["summary"]

            sub_text = ""
            sub_text += item["total_distance"] + "km(" + str(int(item["bike_path_perc"])) + "% bikeway)" + " | " + \
                        item["total_duration"] + "min"

            sub_text += "\nIncident (" + str(item["collision_counter"]+item["near_miss_counter"]) + ")" # - " + item["incident_street"]
            sub_text += "\nHazard (" + str(item["hazard_counter"]) + ")"# - " + item["hazard_street"]

            if index == 0:
                elements.append({
                    "title": title + "*",
                    "subtitle": sub_text,
                    "buttons": [
                        {
                            "title": "View",
                            "type": "web_url",
                            "url": url,
                            "webview_height_ratio": "tall"
                        },
                        {
                            "type": "element_share",
                        }
                    ]
                })
            else:
                elements.append(
                {
                    "title": title,
                    "subtitle": sub_text,
                    "buttons": [
                        {
                            "title": "View",
                            "type": "web_url",
                            "url": url,
                            "webview_height_ratio": "tall"
                        },
                        {
                            "type": "element_share",
                        }
                    ]
                })

        self.bot.send_generic_message(recipient_id, elements)

    def add_location_info(self, uid, location_str, location_type):
        if self.sessions.get(uid):
            self.sessions[uid][location_type] = location_str
        else:
            self.sessions[uid] = {location_type: location_str}

    def send_typing_on(self, recipient_id):
        return self.bot.send_action(recipient_id, "typing_on")

    def send_typing_off(self, recipient_id):
        return self.bot.send_action(recipient_id, "typing_off")

    def get_user_first_name(self, uid):
        user_info = requests.get(self.bot.graph_url + "/" + uid + "?access_token=" + self.bot.access_token).content

        return json.loads(user_info)["first_name"]
