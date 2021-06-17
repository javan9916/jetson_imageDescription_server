import socket 
import threading
import uuid
import os
import shutil
import sys
import jetson.inference
import jetson.utils
import argparse
import inflect

HEADER = 64
PORT = 5050
SERVER = "192.168.0.2"#socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
BUFFER_SIZE = 4096
DISCONNECT_MESSAGE = "!DISCONNECT"
SEPARATOR = "<SEP>"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
class Detection:
    def __init__(self, ClassID, Height, Width):
        self.ClassID = ClassID
        self.Height = Height
        self.Width = Width
        
def receive_file(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    try:
        #Receiving initial info about the file
        info = conn.recv(BUFFER_SIZE).decode(FORMAT)
        input_ext, filesize = info.split(SEPARATOR)
    except Exception as e:
        print(f"[CONN with {addr}]Error in the detection process.")
        print(e)
        conn.send(f"False{SEPARATOR}Error in the detecion process".encode(FORMAT))
        conn.close()
        return

    #Generate a random name for the temporal files
    rd_name = uuid.uuid1().hex
    os.makedirs(rd_name)

    input_file = f"{rd_name}/{rd_name}{input_ext}"
    output_file = f"{rd_name}/{rd_name}_inference{input_ext}"
    filesize = int(filesize)
    print(f"[CONN with {addr}]Receiving file of {filesize} bytes.")
    #Receive the data of the file
    with open(input_file, "wb") as f:
        received_data = 0
        while received_data < filesize:
            bytes_read = conn.recv(BUFFER_SIZE)
            # write to the file the bytes we just received
            f.write(bytes_read)
            received_data += len(bytes_read)
        f.close()
    print(f"[CONN with {addr}]File transfer done, init detection.")
    try:
        #Exec image detectio
        img = jetson.utils.loadImage(input_file)
        #output = jetson.utils.videoOutput(opt.output_URI, argv=sys.argv)

        # detect objects in the image (with overlay)
        detections = net.Detect(img, overlay=opt.overlay)
        jetson.utils.saveImage(output_file, img)
        # print the detections
        print("detected {:d} objects in image".format(len(detections)))
        sentence = ""
        if len(detections) > 0:
            p = inflect.engine()

            classes = []
            times = []
            labels= open("./ssd_coco_labels.txt", "r")
            for line in labels:
                classes.append(line)
                times.append(0)
            labels.close()

            visited = []

            #Fill the count of each detection
            for det in detections:
                times[det.ClassID] += 1

            #Begin sentence
            sentence = "In the image the following items were detected: "
            detCounter = 0

            #Creating the sentence
            for detection in detections:
                detCounter += 1
                if not detection in visited:
                    count = times[detection.ClassID]
                    #print("I saw ", p.number_to_words(count),p.plural(classes[detection.ClassID], count))
                    sentence += p.number_to_words(count) + " " +p.plural(classes[detection.ClassID], count) + ", "
                    #End if
                visited.append(detection)

                if detCounter == len(detections) and detCounter > 1:
                    count = times[detection.ClassID]
                    replacing = p.number_to_words(count) + " " +p.plural(classes[detection.ClassID], count) + ", "
                    sentence = sentence.replace(replacing, "")
                    sentence += "and finally " + p.number_to_words(count) + " " +p.plural(classes[detection.ClassID], count) + ", "
                    #End if
            #End for
            #Replace las colon with a dot
            sentence = sentence[:-2] + "."
        else:
            sentence = "Sorry, no items were detected in the image."
        
        #Clean sentence.
        sentence = sentence.replace("\n", "")
        #Final sentence
        print(sentence)

        print(f"[CONN with {addr}]Detection done, init file transfer.")
        #Get info of converted file and send it to client
        filesize = os.path.getsize(output_file)
        conn.send(f"True{SEPARATOR}{filesize}{SEPARATOR}{sentence}".encode(FORMAT))
        with open(output_file, "rb") as f:
            bytes_read = f.read(BUFFER_SIZE)
            while bytes_read: 
                conn.sendall(bytes_read)
                bytes_read = f.read(BUFFER_SIZE)
            f.close()
    except Exception as e:
        print(f"[CONN with {addr}]Error in the detection process.")
        print(e)
        conn.send(f"False{SEPARATOR}0{SEPARATOR}Error in the detecion process".encode(FORMAT))
    finally:   
        #Close connection to client and remove temporal files
        conn.close()
        shutil.rmtree(f"./{rd_name}")
        print(f"[CONN with {addr}]Folder was deleted and conn closed.")


def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=receive_file, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")

def main():
    print("[STARTING] Server is starting...")
    start()

# parse the command line
parser = argparse.ArgumentParser(description="Locate objects in a live camera stream using an object detection DNN.", 
                                 formatter_class=argparse.RawTextHelpFormatter, epilog=jetson.inference.detectNet.Usage() +
                                 jetson.utils.videoSource.Usage() + jetson.utils.videoOutput.Usage() + jetson.utils.logUsage())

parser.add_argument("input_URI", type=str, default="", nargs='?', help="URI of the input stream")
parser.add_argument("output_URI", type=str, default="", nargs='?', help="URI of the output stream")
parser.add_argument("--network", type=str, default="ssd-mobilenet-v2", help="pre-trained model to load (see below for options)")
parser.add_argument("--overlay", type=str, default="box,labels,conf", help="detection overlay flags (e.g. --overlay=box,labels,conf)\nvalid combinations are:  'box', 'labels', 'conf', 'none'")
parser.add_argument("--threshold", type=float, default=0.5, help="minimum detection threshold to use") 

is_headless = ["--headless"] if sys.argv[0].find('console.py') != -1 else [""]

try:
	opt = parser.parse_known_args()[0]
except:
	print("")
	parser.print_help()
	sys.exit(0)

net = jetson.inference.detectNet(opt.network, sys.argv, opt.threshold)


main()