import requests
from bs4 import BeautifulSoup as BS
import base64
from collections import OrderedDict
import pickle
import logging
import os
import json


logging.basicConfig(filename=os.getcwd()+'app.log', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


class FileWrite:
    fileName = os.getcwd() + "/roomdetails.pkl"
    output = open(fileName, "wb")

    def write_object_to_file(self, rooms):
        for room in rooms:
            pickle.dump(room, self.output, pickle.HIGHEST_PROTOCOL)


class PGRoom:
    """
        :type property_name = string
        :type location_name = string
        :type latitude = string
        :type longitude = string
        :type sharing_details = OrderedDict()
    """

    def __init__(self):
        self.property_name = None
        self.location_name = None
        self.latitude = None
        self.longitude = None
        self.sharing_details = OrderedDict()

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=False, indent=4)

    def __str__(self):
        return "PropertyName: " + self.property_name.strip() + "location: " + self.location_name.strip() + \
               "lat: " + self.latitude.strip() + "long: " + self.longitude.strip() + "roomDetails:" \
               + str(self.sharing_details)[11:-1]




class PGRoomUtil:
    """This is API suggest the places for given string"""
    auto_suggest_api = "https://www.nobroker.in/api/v1/localities/autocomplete/_search?hint="

    """This API gives the place details like place_id, latitude and longitude"""
    place_details_api = "https://www.nobroker.in/api/v1/localities/place_detail/"

    """This API gives the list of rooms in the selected location
        We have to give the BASE64 encoded string to the searchParam to get the result
        Fields to encode:
            1) latitude
            2) longitude
            3) Place_id
            4) PlaceName
        Sample format to encode:
            [{"lat":12.9229153,"lon":80.12745579999999,"placeId":ChIJD61KhBRfUjoR1DjOxGY6beE,"placeName":Tambaram}]
        
    """
    get_rooms_api = "https://www.nobroker.in/property/pg/bangalore/abc?searchParam="

    """Parser for Beautiful soap"""
    parser = "html.parser"



    def get_auto_suggest_details_api(self, place_id):
        """ This function returns the autosuggest API URL as a string

                :param string place_id : unique id of a place obtained by get_nearby_places function

                :return string
        """

        return self.place_details_api + place_id + "/_search"



    def get_place_details_api(self, encoded_details, page=1, property_type="pg"):

        """This function return the full URL of the place_detail API
                :return String
                :param encoded_details: Base64 encoded place details
                :param property_type: Type of property we are searching for. By default it is set to 'pg'
        """

        return self.get_rooms_api + encoded_details + "&propertyType=" + property_type + "&pageNo=" + str(page)



    def get_nearby_places(self, location):

        """
               This function suggest the different places depends on the given location.
               :param string location : location typed by user.
               :returns list[tuples], False if response status is not 200
        """

        try:
            response = requests.get(self.auto_suggest_api + location)
            #print(response.status_code)
            if not response.status_code == 200:
                logging.warning(f"response not 200 status-code {response.status_code}")
                return False

            response_json = response.json()

            root = response_json["predictions"]

            suggestions = []

            for tag in root:
                suggestions.append((tag['place_id'], tag['description'].split(",")[0]))

            return suggestions

        except KeyError as k:
            print("Can't find the place you are looking for! You can try a different place")
            #traceback.print_exc()
            logging.error(f"Exception occured because of key error {k}", exc_info=True)
            return None

        except json.JSONDecodeError:
            print("There is something gone wrong", exc_info=True)

        except requests.exceptions.ConnectionError:
            print("No internet connection")
            logging.error("No internet Connection", exc_info=True)

        except:
            logging.error("Unexcepected exception happened", exc_info=True)




    def get_place_details(self, place_id):

        """
                This function returns the details about the given place_id by parsing json

                :param string place_id : This is place_id  obtained by the get_nearby_places function

                :return list[string] This function will return False if server is busy otherwise it returns the place_details as list of list

        """

        url = self.get_auto_suggest_details_api(place_id)
        try:
            response = requests.get(url)

            if not response.status_code == 200:
                logging.warning(f"response not 200 status-code {response.status_code}")
                return False

            place_details = response.json()

            location = place_details["result"]["geometry"]["location"]
            '''
                Appending quotes ["] at the end of name and place_id because to encoding is done in that format
            '''
            name = '"' + place_details["result"]["name"] + '"'

            place_id = '"' + place_id + '"'

            return [name, location['lat'], location['lng'], place_id]

        except requests.exceptions.ConnectionError:
            print("No internet connection or server is down")
            logging.error("Exception  occured", exc_info=True)

        except KeyError:
            print("There something gone wrong")
            logging.error("Exception  occured", exc_info=True)

        except json.JSONDecodeError:
            print("There something gone wrong")
            logging.error("Exception  occured", exc_info=True)

        except:
            print("There something gone wrong")
            logging.error("Unexcepected exception happened",exc_info = True)

    def get_encodes_place_details(self, place_details):

        """

        :param list[string] place_details: This list of strings contains four strings and they are,
            1) place_name
            2) latitude
            3) longitude
            4) place_id
        :return bytes: These function return encoded place_details as a bytes
        """

        try:

            formated_place_details = '[{"lat":'+str(place_details[1])+',"lon":'+str(place_details[2]) + ',"placeId":' \
                                     + str(place_details[3])+',"placeName":'+place_details[0]+'}]'
            #print(formated_place_details)

            encoded_place_details = base64.b64encode(formated_place_details.encode())
            #print(encoded_place_details)

            return encoded_place_details

        except:
            logging.error("new exception other than expected has been occured", exc_info=True)

    def get_rooms_url(self, encoded_place_details, page=1):

        """

        :param bytes encoded_place_details: It is the encoded place_details and it is in bytes so it is prefixed with 'b'
            example :b'W3sibGF0IjoxMi'

        :param int page: It is just page number used for pagination

        :return list[string]: This function return the URL of the rooms.
        """

        try:
            encoded_place_details = str(encoded_place_details)[2:-1]

            response = requests.get(self.get_place_details_api(encoded_place_details, page))

            if not response.status_code == 200:
                logging.warning(f"response not 200 status-code {response.status_code}")
                return False

            #print(self.get_place_details_api(encoded_place_details),"giri")

            rooms_url = []

            soup = BS(response.content, features=self.parser)

            for a in soup.find_all("a", class_="card-link-detail"):
                rooms_url.append(a['href'])

            return rooms_url

        except requests.exceptions.ConnectionError:
            print("No internet connection or server is down")
            logging.error("Exception  occured", exc_info=True)

        except:
            print("There something gone wrong")
            logging.error("new exception other than expected has been occured", exc_info=True)

    def get_room_details(self, room_url):
        """

        :param string room_url: It is URL of a specific room.

        :return PGRoom: This function returns the required place details
        """
        try:

            response = requests.get(room_url)

            if not response.status_code == 200:
                logging.warning(f"response not 200 status-code {response.status_code}")
                return False

            room = response.content

            soup = BS(room, features=self.parser)

            pgroom = PGRoom()

            for tag in soup.find_all("meta", {'itemprop': ['latitude', 'longitude']}):
                if tag['itemprop'] == "latitude":
                    pgroom.latitude = tag['content'].strip()

                if tag['itemprop'] == 'longitude':
                    pgroom.longitude = tag['content'].strip()

            for tag in soup.find_all("span", class_="detail-title-border"):

                if "sharing room details" in tag.text or "single" in tag.text.split()[0].lower() or "double" in tag.text.split()[0].lower() or \
                        "three" in tag.text.split()[0].lower() or "four" in tag.text.split()[0].lower():

                    pgroom.sharing_details[tag.text.split()[0]] = 0

            i = 0
            for tag in soup.find_all("span", class_="margin-left-20"):
                keys = list(pgroom.sharing_details.keys())
                if i % 2 == 0:
                    pgroom.sharing_details[keys[i // 2]] = tag.text.strip()

                i += 1

            for tag in soup.find_all("h1", class_="detail-title-main"):
                pgroom.property_name = tag.text.strip()

            for tag in soup.find_all("h5", class_="margin-top-bottom-0"):
                pgroom.location_name = tag.text.strip()


            return pgroom

        except requests.exceptions.ConnectionError:
            print("No internet connection or server is down")
            logging.error("Exception  occured", exc_info=True)

        except:
            print("There something gone wrong")
            logging.error("new exception other than expected has been occured", exc_info=True)


print("In case of any exception logs are written on the file named 'app.log' which is in current working directory")

print("At the end of program all room details are stored in file named roomdetails.pkl which is in current working"
      " directory")

print("Type the location name to get the nearby PG room details")
location_name = input().strip()

pgroomutil = PGRoomUtil()


suggestions = pgroomutil.get_nearby_places(location_name)


if suggestions == None or suggestions == False:
    logging.error(f"Suggestions variable {suggestions}caused exeception")
    exit()


rooms = set()

end_page = 5

for place in suggestions:

    place_details = pgroomutil.get_place_details(place[0])

    print("Finished collecting place details")

    encoded_place_details = pgroomutil.get_encodes_place_details(place_details)

    for i in range(1, end_page):
        try:
            rooms_url = pgroomutil.get_rooms_url(encoded_place_details, i)
        except:
            logging.error(f"Unexpected error occured while connecting {PGRoomUtil().get_rooms_api}", exc_info=True)
            continue

        #print("Finished getting rooms url and in page number", i)
        print(rooms_url)

        if len(rooms_url) == 0:
            t = PGRoomUtil().get_place_details_api(str(encoded_place_details)[2:-1], i)
            logging.warning(f"Can't able to find any rooms in the area. The url is {t}")
            break

        for room in rooms_url:
            try:
                room_detail = pgroomutil.get_room_details(room)

            except:
                logging.warning(f"Can't able find the room details of the given room. The room url is {room}", exc_info=True)
                continue

            rooms.add(room_detail)

            print(room_detail.toJSON())

try:
    fw = FileWrite()
    fw.write_object_to_file(rooms)

except FileNotFoundError:
    logging.error("File not found", exc_info=True)

except:
    logging.error("Unexpected error happened while writing data into file", exc_info=True)


















