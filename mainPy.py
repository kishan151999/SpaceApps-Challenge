import os
import sys
import logging
# --------------------------- logging variables ----------------------------#
FORMAT = '%(asctime)-15s %(levelname)-9s: %(message)s'
PATH = os.path.dirname(os.path.abspath(__file__)) + "/output.log"
COMMAND = f"echo 'Note: This log will be cleared for each run.\n'> {PATH}"
os.system(COMMAND)
logging.basicConfig(filename = PATH, level=30,format=FORMAT)
#---------------------------------------------------------------------------#
#Import custom modules
try:
    import time
    import geocoder
    from contextlib import contextmanager
    import json
    import googlemaps
    from datetime import datetime
    import speech_recognition as sr
    import pyaudio
except ImportError as error:
    logging.critical("Unable to import modules: %s",error.args)
    exit()
else:
    logging.info("Successfully imported modules")
#---------------------------------------------------------------------------#

@contextmanager
def ignore_stderr():
    '''surpress unnecessary ALAS notifications'''
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    sys.stderr.flush()
    os.dup2(devnull, 2)
    os.close(devnull)
    try:
        yield
    finally:
        os.dup2(old_stderr, 2)
        os.close(old_stderr)

def check_answer(answer):
    '''check if the user answered yes or no'''
    if answer in ['y','Y','yes','Yes','YES']:
        return True
    elif answer in ['n','N','no','No','NO']:
        return False
    else:
        return None

def listen_speech(r,mic):
    '''Listen to user speech from default mic'''
    with mic as source:
        logging.debug("Currently listening.")
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)
    return audio

def recognize_speech():
    '''voice recognition of user speech'''
    with ignore_stderr():
        r = sr.Recognizer()
        mic = sr.Microphone()
    while True:
        try:
            print("Currently listening...")
            audio = listen_speech(r,mic)
            logging.debug("Audio created")
            print("Analyzing...")
            userSpeech = r.recognize_google(audio)
            logging.debug("Successfully recognized")
            break
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as error:
            logging.warning(f"Unable to recognize user's speech: {error.args}")
            answer = input("Unable to recongize speech! Retry? (y/n)")
            if not check_answer(answer):
                return None
            else:
                logging.debug("Retrying.")

    return userSpeech


def get_location(gmaps):
    ''' Ask user to either input or speak their adress and convert it into lat,lng'''

    while True:
        print("Do you want to input your address by:")
        print("\t1. Speech, or")
        print("\t2. Typing, or")
        print("\t3. Auto detect.")
        time.sleep(1.4)
        choice = input("Your choice (1, 2 or 3): ")
        if choice != '' and choice.isdigit() and (int(choice) in [1,2,3]):
            choice = int(choice)
            break
        else:
            print("\nInput not recognized, please re-enter.")
            
        logging.debug(f"User choice: {choice}")
    
    if choice == 1:
        userAddress = recognize_speech()
        if userAddress != None:
            while True:
                print("Detected Address:")
                print(userAddress)
                answer = input("Is this your address? (y/n)")
                if check_answer(answer):
                    break
                elif not check_answer(answer):
                    answer = input("Retry? (y/n): ")
                    if check_answer(answer):
                        userAddress = recognize_speech()
                    else:
                        while True:    
                            userAddress = input("Enter your Adress: ")
                            if userAddress != '':
                                break
                        print(f"Address: {userAddress}")
        else:
            while True:    
                userAddress = input("Enter your Adress: ")
                if userAddress != '':
                    break
    elif choice == 2:     
        while True:    
            userAddress = input("Enter your Adress: ")
            if userAddress != '':
                break
    elif choice == 3:
        g = geocoder.ip('me')
        userLocation = str(g.latlng[0]) + ',' + str(g.latlng[1])
        temp = gmaps.reverse_geocode(g.latlng)
        userAddress = temp[0]['formatted_address']
        logging.debug(f"Detected user address: {userAddress}, attitude: {userLocation}")
        print(f"We have detected your address: {userAddress}")
        userInput = input("Is this correct? (y/n):")
        if check_answer(userInput):
            return userLocation, userAddress
        else:
            while True:    
                userAddress = input("Enter your Adress: ")
                if userAddress != '':
                    break

    geocodeResult = gmaps.geocode(userAddress)
    if len(geocodeResult) == 0:
        logging.error(f"Unable to recognize user Address: {userAddress}")
        print("Unable to identify address")
        exit()

    attitude = geocodeResult[0]['geometry']['location']
    userLocation = str(attitude['lat']) + ',' + str(attitude['lng'])
    logging.debug(f"Input adress: {userAddress}, attitude: {userLocation}")

    return userLocation, userAddress

def get_place_address(gmaps, locationType, userLocation):
    '''get the name and address of the nearest specified loaction type'''

    placesResult  = gmaps.places_nearby(location=userLocation, rank_by = 'distance', open_now =True , type = locationType)
    try:
        place = placesResult['results'][0] #take the first result since it is the closest
        placeID = place['place_id']
        getFields = ['name','formatted_phone_number','formatted_address']
    except Exception as error:
        print("No nearby services.")
        logging.error(f"Program exited as the following exception: {error.args}")
        exit()

    placesDetails  = gmaps.place(place_id= placeID , fields= getFields)
    placeName = placesDetails['result']['name']
    placeAddress = placesDetails['result']['formatted_address']
    logging.debug(f"Nearest Location: {placeName}; Address: {placeAddress}")

    return placeName, placeAddress


def get_direction(gmaps,userAddress,placeAddress):
    '''get all the direction from user to the desired location'''

    currentTime = datetime.now()
    logging.debug(f"Departure Time: {currentTime}")
    directions = gmaps.directions(userAddress,placeAddress,mode="driving",departure_time=currentTime)
    if len(directions) == 0:
        logging.debug("No service avaliable")
        print("Unable to locate services near you.")
        exit()
    else:
        travelTime = directions[0]['legs'][0]['duration']['text']
        distance = directions[0]['legs'][0]['distance']['text']
        startAddress = directions[0]['legs'][0]['start_address']
        logging.debug(f"Travel time: {travelTime}, Distance: {distance}")

        print(f"This service is {distance} away. It will be approximately {travelTime} drive.")
        print(f"Starting from: {startAddress}")


def main():
    print("#-----------------------------------------------------------------------------#")
    print("Find your nearest government service.")
    print("Note: This program is powered by Google service.")
    print("If you are using this program you have to accept Google's terms and conditions.")
    print("#-----------------------------------------------------------------------------#")
    time.sleep(1)
    answer = input("Continue? (y/n): ")
    if not check_answer(answer):
        logging.error("User Rejected terms and conditions.")
        exit()
    print("#-----------------------------------------------------------------------------#")
    time.sleep(0.3)
    locationType = input("What kind of service do you need? ")
    print()
    time.sleep(0.3)

    #API KEY
    API_KEY = "AIzaSyCNGdMVS7qtf6S9C730BzBt9-YcD2BhNx0"
    logging.debug(f"API key: {API_KEY}")
    # Define the Client
    gmaps = googlemaps.Client(key = API_KEY)

    #Get user Location
    userLocation, userAddress = get_location(gmaps)
    placeName, placeAddress = get_place_address(gmaps, locationType, userLocation)
    print("#-----------------------------------------------------------------------------#")
    print(f"Nearest {locationType} service: {placeName}")
    print(f"Address: {placeAddress}")

    get_direction(gmaps,userAddress,placeAddress)
    print("#-----------------------------------------------------------------------------#")
    logging.info("Address obtained")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info("User terminated.")
        print()
        exit()