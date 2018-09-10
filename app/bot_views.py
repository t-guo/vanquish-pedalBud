from flask import request
from app import app, bot, FB_VERIFY_TOKEN, GMAP_API_KEY, BIKE_PATH_FILE, BIKE_COLLISION_FILE
from app.utils.pedalbud_actions_helper import SaferWayBotActions
from app.utils.google_map_client_helper import GoogleMapsRouteHelper
import json
import time


message_templates = {
    "start_message":
        "Hi {name}! Let's start planning your trip. Where would you like to bike to?",

    "end_message":
        "Bye now B-)",

    "ask_end_message":
        "Would you like to end this trip? Say *done* at any time to end a trip.",

    "ask_end_button":
        [{"type": "postback", "title": "Done!", "payload": "end_navigation"}],
}

saferway_bot = SaferWayBotActions(bot, FB_VERIFY_TOKEN, message_templates)
gmaps = GoogleMapsRouteHelper(GMAP_API_KEY, BIKE_PATH_FILE, BIKE_COLLISION_FILE)


# Receive messages that Facebook sends the bot at this endpoint
@app.route("/", methods=['GET', 'POST'])
def receive_message():
    if request.method == 'GET':
        token_sent = request.args.get("hub.verify_token")

        return saferway_bot.verify_fb_token(token_sent)

    # Proceed with preparing for response
    if request.method == 'POST':
        output = request.get_json()
        for event in output['entry']:
            messaging = event['messaging']

            for x in messaging:
                recipient_id = x['sender']['id']

                app.logger.info('Message received: {}'.format(x))
                app.logger.info('Current sessions {}'.format(json.dumps(saferway_bot.sessions)))

                if x.get('message'):
                    if x['message'].get('text'):
                        message = x['message']['text']
                        if message.lower() == "done":
                            # Clear od
                            saferway_bot.send_typing_on(recipient_id)

                            saferway_bot.add_location_info(recipient_id, "", "destination")
                            saferway_bot.add_location_info(recipient_id, "", "origin")
                            time.sleep(1)

                            saferway_bot.send_typing_off(recipient_id)

                            saferway_bot.end_service(recipient_id)
                        else:

                            saferway_bot.send_typing_on(recipient_id)
                            time.sleep(1)

                            if no_user_info(saferway_bot.sessions, recipient_id):
                                saferway_bot.send_typing_off(recipient_id)
                                saferway_bot.ask_destination_location(recipient_id)

                            elif no_destination(saferway_bot.sessions, recipient_id):
                                saferway_bot.send_typing_off(recipient_id)
                                saferway_bot.ask_destination_location(recipient_id)

                            elif no_origin(saferway_bot.sessions, recipient_id):
                                saferway_bot.send_typing_off(recipient_id)
                                saferway_bot.ask_current_location(recipient_id)

                            else:
                                saferway_bot.send_typing_off(recipient_id)
                                saferway_bot.ask_end_navigation(recipient_id)

                    elif x['message'].get('attachments'):
                        for att in x['message']['attachments']:
                            if att.get('payload'):
                                if att['payload'].get('coordinates'):

                                    latlong = att['payload']['coordinates']
                                    current_location = str(latlong['lat']) + "," + str(latlong['long'])

                                    saferway_bot.send_typing_on(recipient_id)

                                    if no_user_info(saferway_bot.sessions, recipient_id):
                                        saferway_bot.add_location_info(recipient_id, current_location, "destination")
                                        saferway_bot.add_location_info(recipient_id, "", "origin")

                                    elif no_destination(saferway_bot.sessions, recipient_id):
                                        saferway_bot.add_location_info(recipient_id, current_location, "destination")

                                    elif no_origin(saferway_bot.sessions, recipient_id):
                                        saferway_bot.add_location_info(recipient_id, current_location, "origin")

                                    time.sleep(1)

                                    if (not no_destination(saferway_bot.sessions, recipient_id)) and \
                                            no_origin(saferway_bot.sessions, recipient_id):

                                        saferway_bot.send_typing_off(recipient_id)

                                        saferway_bot.ask_current_location(recipient_id)

                                    elif (not no_destination(saferway_bot.sessions, recipient_id)) and \
                                            (not no_origin(saferway_bot.sessions, recipient_id)):

                                        routes, url = gmaps.get_routes(
                                            saferway_bot.sessions[recipient_id]["origin"],
                                            saferway_bot.sessions[recipient_id]["destination"]
                                        )

                                        saferway_bot.send_typing_off(recipient_id)

                                        if len(routes) > 1:
                                            saferway_bot.bot.send_text_message(
                                                recipient_id,
                                                "Found " + str(len(routes)) + " routes, processing safety metrics..."
                                            )
                                        else:
                                            saferway_bot.bot.send_text_message(
                                                recipient_id,
                                                "Found " + str(len(routes)) + " route, processing safety metrics..."
                                            )

                                        # for route in routes:
                                        #     route["incident_street"], route["hazard_street"] = gmaps.get_street_info(
                                        #         route["list_incidents"],
                                        #         route["list_hazards"]
                                        #     )

                                        saferway_bot.help_navigate(recipient_id, routes, url)

                elif x.get('postback'):
                    if x['postback'].get('payload'):
                        if x['postback']['payload'] == "end_navigation":
                            saferway_bot.send_typing_on(recipient_id)

                            saferway_bot.add_location_info(recipient_id, "", "destination")
                            saferway_bot.add_location_info(recipient_id, "", "origin")
                            time.sleep(1)

                            saferway_bot.send_typing_off(recipient_id)

                            saferway_bot.end_service(recipient_id)

                        else:
                            pass
                    else:
                        pass

                else:
                    pass

        return "Success"


def no_user_info(sessions, recipient_id):
    return not sessions.get(recipient_id)


def no_destination(sessions, recipient_id):
    return sessions[recipient_id]["destination"] == ""


def no_origin(sessions, recipient_id):
    return sessions[recipient_id]["origin"] == ""
