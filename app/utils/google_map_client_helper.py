import googlemaps
from pyproj import Proj, transform
import polyline
import urllib
import pandas as pd
import operator
from app.utils.app_utils import most_common


class GoogleMapsRouteHelper(object):
    """
    Google Maps wrapper
    """
    def __init__(self, api_key, bike_path_file, bike_collision_path):
        self.client = googlemaps.Client(key=api_key)
        self.GOOGLE_DIRECTION_URL = "https://www.google.com/maps/dir/?api=1&"
        self.bike_path_df = pd.read_pickle(bike_path_file)
        self.bike_collision_df = pd.read_pickle(bike_collision_path)

    def get_routes(self, start, end, mode="bicycling"):
        """ returns list of routes checking for key locations in the route """
        list_of_routes = self.client.directions(start, end, mode=mode, alternatives=True)
        url = self.GOOGLE_DIRECTION_URL + urllib.urlencode({"origin": start, "destination": end, "travelmode": mode})

        for route in list_of_routes:
            try:
                path_points = self.polyline_to_points(route["overview_polyline"]["points"])
                route["overview_points"] = path_points
            except Exception as e:
                route["overview_points"] = "Polyline cannot be decoded. Error: " + str(e)

            try:
                bike_path_perc = self.find_perc_bikeway(path_points)
                route["bike_path_perc"] = bike_path_perc
            except Exception as e:
                route["bike_path_perc"] = "Error: " + str(e)

            route["total_distance"], route["total_duration"] = self.total_time_and_distance(route["legs"])
            route["collision_counter"], route["near_miss_counter"], route["hazard_counter"], route["list_incidents"], \
                route["list_hazards"] = self.find_number_incident(path_points)

        recommended_route = self.find_best(list_of_routes)

        ranked_routes = [recommended_route]

        for route in list_of_routes:
            if route != recommended_route:
                ranked_routes.append(route)

        return ranked_routes, url

    def get_street_info(self, list_incident, list_hazard):
        list_of_streets = []

        for lat, long in list_incident:
            result = self.client.reverse_geocode(str(lat) + "," + str(long))
            if result[0]["address_components"][1]["types"][0] == "route":
                street_name = result[0]["address_components"][1]["short_name"]
            else:
                street_name = result[0]["address_components"][0]["short_name"]

            list_of_streets.append(street_name)

        incident_street = most_common(list_of_streets)

        list_of_streets = []

        for lat, long in list_hazard:
            result = self.client.reverse_geocode(str(lat) + "," + str(long))
            if result[0]["address_components"][1]["types"][0] == "route":
                street_name = result[0]["address_components"][1]["short_name"]
            else:
                street_name = result[0]["address_components"][0]["short_name"]

            list_of_streets.append(street_name)

        hazard_street = most_common(list_of_streets)

        return incident_street, hazard_street

    @staticmethod
    def polyline_to_points(encoded_polyline):
        """ decodes polyline to list of (lat, long)s """
        return polyline.decode(encoded_polyline)

    @staticmethod
    def total_time_and_distance(legs):

        total_distance = 0
        total_duration = 0

        for x in legs:
            total_distance += x["distance"]["value"]
            total_duration += x["duration"]["value"]

        return str(round(total_distance/1000.0, 1)), str(int(round(total_duration/60.0, 0)))

    def on_bikeway(self, point, x_list, y_list):
        x, y = self.lat_long_to_x_y(point)

        for p in x_list:
            if abs(x - p) < 1:
                xresult = 1
                break
            else:
                xresult = 0

        for p in y_list:
            if abs(y - p) < 1:
                yresult = 1
                break
            else:
                yresult = 0

        return xresult * yresult

    def find_perc_bikeway(self, l):
        df = self.bike_path_df

        x_list = df['POINT_X'].tolist()
        y_list = df['POINT_Y'].tolist()
        counter1 = 0
        for point in l:
            x = self.on_bikeway(point, x_list, y_list)
            counter1 += x
        p = counter1 / (len(l) * 1.0)
        return round(p * 100, 0)

    @staticmethod
    def lat_long_to_x_y((lat, long), in_init='epsg:4326', out_init='epsg:26910'):
        x, y = transform(Proj(init=in_init), Proj(init=out_init), long, lat)
        return x, y

    @staticmethod
    def incident(point, x_list, y_list):

        for p in x_list:
            if abs(point[0] - p) < 0.0001:
                xresult = 1
                break
            else:
                xresult = 0

        for p in y_list:
            if abs(point[1] - p) < 0.0001:
                yresult = 1
                break
            else:
                yresult = 0

        return xresult * yresult

    def find_number_collision(self, l):
        df = self.bike_collision_df

        df2 = df[df['TYPE'] == 'collision']
        x_list = df2['latitude'].tolist()
        y_list = df2['longitude'].tolist()
        counter = 0
        list_incident = []
        for point in l:
            x = self.incident(point, x_list, y_list)
            if x == 1:
                list_incident.append(point)
            counter += x
        return counter, list_incident

    def find_number_hazard(self, l):
        df = self.bike_collision_df

        df2 = df[df['TYPE'] == 'hazard']
        x_list = df2['latitude'].tolist()
        y_list = df2['longitude'].tolist()
        counter = 0
        list_incident = []

        for point in l:
            x = self.incident(point, x_list, y_list)
            if x == 1:
                list_incident.append(point)
            counter += x
        return counter, list_incident

    def find_number_near_miss(self, l):
        df = self.bike_collision_df

        df2 = df[df['TYPE'] == 'near_miss']
        x_list = df2['latitude'].tolist()
        y_list = df2['longitude'].tolist()
        counter = 0
        list_incident = []

        for point in l:
            x = self.incident(point, x_list, y_list)
            if x == 1:
                list_incident.append(point)
            counter += x
        return counter, list_incident

    def find_number_incident(self, l):

        collision_counter, l1 = self.find_number_collision(l)
        near_miss_counter, l2 = self.find_number_near_miss(l)
        hazard_counter, l3 = self.find_number_hazard(l)

        list_incident = l1 + l2
        list_hazard = l3
        return collision_counter, near_miss_counter, hazard_counter, list_incident, list_hazard

    @staticmethod
    def score_route(percentage, collision, hazard, near_miss):
        safety_score = percentage - (collision + hazard + near_miss)
        return safety_score

    def find_best(self, l_route):
        score_list = []
        for r in l_route:
            score = self.score_route(r['bike_path_perc'],
                                     r['bike_path_perc'],
                                     r['hazard_counter'],
                                     r['near_miss_counter'])
            score_list.append(score)
        max_index, max_value = max(enumerate(score_list), key=operator.itemgetter(1))

        return l_route[max_index]
