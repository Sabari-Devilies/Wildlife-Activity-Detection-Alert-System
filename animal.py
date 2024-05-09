
from google.cloud import vision
import cv2
import os
import threading
import queue
from twilio.rest import Client

# Set up Google Cloud Vision API
vision_client = vision.ImageAnnotatorClient.from_service_account_file('plated-shelter-416602-0dc807e0ea9f.json')

# Set up Twilio
TWILIO_ACCOUNT_SID = 'ACda88b50472cdf143cdabe2f60229e157'
TWILIO_AUTH_TOKEN = 'e2ec33f1fcb5bcfed5c5f0dddf2ec031'
TWILIO_PHONE_NUMBER = '+15315354735'
TWILIO_PHONE_NUMBER1 = '+14155238886'
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Open camera or surveillance video
# Use 0 for the default camera or provide the path to your surveillance video file
video_source = 'tiger.mp4'  # Replace with the appropriate video source
cap = cv2.VideoCapture(video_source)

# List of wild animal names
wild_animals = {
    'Predators': ['lion', 'tiger', 'cheetah', 'leopard', 'jaguar', 'panther', 'wolf', 'fox', 'hyena', 'jackal', 'cougar', 'lynx', 'bobcat', 'caracal', 'puma', 'snow leopard', 'spotted hyena', 'black bear', 'grizzly bear', 'polar bear', 'red fox', 'arctic fox', 'gray wolf', 'golden jackal', 'maned wolf', 'african wild dog', 'dingo', 'clouded leopard', 'serval', 'ocelot', 'fishing cat', 'marbled cat', 'lynx', 'leopard cat', 'sand cat', 'jungle cat', 'andean mountain cat', 'margay', 'ocelot', 'pallas cat', 'servals'],
    'Extinct': ['sabertooth', 'dodo', 'woolly mammoth', 'tasmanian tiger', 'quagga', 'velociraptor', 'saber-toothed cat', 'smilodon', 'megatherium', 'irish elk', 'moa', 'passenger pigeon', 'stellers sea cow', 'great auk', 'carolina parakeet', 'thylacine', 'haast eagle', 'ivory-billed woodpecker', 'bali tiger', 'barbary lion', 'cape lion', 'caspian tiger', 'javan tiger', 'balinese tiger', 'sumatran tiger', 'pinta island tortoise', 'northern white rhinoceros', 'western black rhinoceros', 'hawaiian crow', 'formosan clouded leopard', 'quagga', 'toolache wallaby', 'tasmanian tiger', 'eastern cougar', 'bennetts wallaby', 'passenger pigeon', 'golden toad', 'carolina parakeet', 'macquaries island parakeet', 'ivory-billed woodpecker', 'pied imperial pigeon', 'spixs macaw', 'poʻouli', 'splendid poison frog', 'bluebuck', 'bubal hartebeest', 'gastric brooding frog', 'white-eyed river martin'],
    'Endangered': ['tiger', 'pangolin', 'sumatran orangutan', 'sumatran rhinoceros', 'vaquita porpoise', 'black rhinoceros', 'javan rhinoceros', 'indian elephant', 'snow leopard', 'amur leopard', 'south china tiger', 'sumatran tiger', 'malayan tiger', 'iberian lynx', 'philippine eagle', 'vaquita', 'yangtze finless porpoise'],
    'Normal': ['giraffe', 'zebra', 'rhinoceros', 'hippopotamus', 'bear', 'panda', 'koala', 'monkey', 'gorilla', 'chimpanzee', 'orangutan', 'kangaroo', 'gazelle', 'antelope', 'buffalo', 'bison', 'moose', 'deer', 'elk', 'camel', 'sloth', 'armadillo', 'platypus', 'pangolin', 'tapir', 'okapi', 'walrus', 'zebu', 'wombat', 'quokka', 'anteater', 'coati', 'elephant seal', 'seal', 'sea lion', 'walrus', 'otter', 'beaver', 'muskrat', 'porcupine', 'hedgehog', 'echidna', 'shrew', 'mole', 'squirrel', 'chipmunk', 'rabbit', 'hare', 'guinea pig', 'hamster', 'gerbil', 'rat', 'mouse', 'vole', 'lemming', 'bat', 'flying fox', 'koala', 'kangaroo', 'opossum', 'koala', 'possum', 'koala'],
}

# Flatten the categories into a single list for easy checking in the code
wild_animal_names = [animal.lower() for category, animals in wild_animals.items() for animal in animals]

# Directory to save captured images
output_directory = 'captured_images'
os.makedirs(output_directory, exist_ok=True)

# Queue for communication between video capture and processing threads
frame_queue = queue.Queue()

# Flag to indicate when to stop the threads
exit_flag = False

# Function for processing frames and detecting wildlife
def process_frames():
    global exit_flag
    while not exit_flag:
        try:
            frame = frame_queue.get(timeout=1)
        except queue.Empty:
            continue

        # Convert the frame to a format compatible with Google Cloud Vision API
        _, img_encoded = cv2.imencode('.jpg', frame)
        content = img_encoded.tobytes()

        # Perform object detection using Google Cloud Vision API
        image = vision.Image(content=content)
        response = vision_client.object_localization(image=image)

        # Check for wild animals (you may need to adjust these conditions)
        for entity in response.localized_object_annotations:
            animal_name = entity.name.lower()
            if animal_name in wild_animal_names and entity.score > 0.5:  # Adjust score threshold as needed
                # Print the detected animal and its category
                # print(f'Detected Animal: {animal_name}, Category: {get_animal_category(animal_name)}')
                send_alert(f'Detected Animal: {animal_name}, Category: {get_animal_category(animal_name)}')
                if (get_animal_category(animal_name) == "Predators"):
                    # print("High Alert Message sent to Forest Officers and Villagers /Bell rang/")
                    send_alert("⚠High Alert: Predators detected! Take action immediately")
                elif (get_animal_category(animal_name) == "Endangered"):
                    print("High Alert Message sent to Forest Officers")
                    send_alert("⚠High Alert: Endangered species detected! Take action immediately")
                elif  (get_animal_category(animal_name) == "Normal"):
                    print("Low Alert Message sent to Forest Officers")
                    send_alert("Low Alert: Normal wildlife detected")

# Function to get the category of the detected animal
def get_animal_category(animal_name):
    for category, animals in wild_animals.items():
        if animal_name in animals:
            return category
    return 'Unknown'

# Function to send SMS alerts
def send_alert(alert_message):
    # List of phone numbers to send alerts to
    to_numbers = ['+918072033891']

    # Send alert message to each phone number
    for number in to_numbers:
        # Send SMS
        twilio_client.messages.create(
            body=alert_message,
            from_=TWILIO_PHONE_NUMBER,
            to=number
        )

        # Send WhatsApp message
        twilio_client.messages.create(
            body=alert_message,
            from_='whatsapp:' + TWILIO_PHONE_NUMBER1,  
            to='whatsapp:' + number
        )

# Thread for processing frames
processing_thread = threading.Thread(target=process_frames)
processing_thread.start()

while True:
    ret, frame = cap.read()

    if not ret:
        break

    frame_queue.put(frame)

    cv2.imshow('Wildlife Detection', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Signal threads to exit
exit_flag = True

# Wait for threads to finish
processing_thread.join()

cap.release()
cv2.destroyAllWindows()





