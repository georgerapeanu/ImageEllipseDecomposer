#!/usr/bin/python3

import cv2;
import argparse;
import random;
import numpy as np;
from flask import Flask,Response,render_template,Markup;
import threading;

IMG_SIZE = (0,0);
GENERATIONS = 100000;
ATTEMPTS_PER_GENERATION = 1000;

app = Flask(__name__);

generation = 0;
output_image = None;
fullSvgString = "";

@app.route("/video_feed",methods=['GET'])
def video_feed():
  global output_image;
  ret, buffer = cv2.imencode('.png',output_image);
  response = Response(buffer.tobytes());
  response.headers['Content-Type'] = 'image/png';
  return response;

@app.route("/",methods=['GET'])
def index(): 
  return render_template('index.html',generation=generation,svgString=Markup(fullSvgString),imgSize = IMG_SIZE);

def random_ellipse(image):
  center_coordinates = (random.randrange(image.shape[1] + 1),random.randrange(image.shape[0] + 1));
  axesLength = (random.randrange(image.shape[0] + 1),random.randrange(image.shape[1] + 1));
  angle = random.randrange(360);
  startAngle = 0;
  endAngle = 360;
  color = (random.randrange(256),random.randrange(256),random.randrange(256));
  thickness = -1;
  answer = image.copy();
  answer = cv2.ellipse(answer,center_coordinates,axesLength,angle,startAngle,endAngle,color,thickness);
  svgString = '<ellipse cx="%d" cy="%d" rx="%d" ry="%d" style="fill:rgb(%d,%d,%d)" transform="rotate(%d %d %d)"></ellipse>' % (*center_coordinates,*axesLength,color[2],color[1],color[0],angle,*center_coordinates);
  return (answer,svgString);

def start_server():
  app.run(host='0.0.0.0',port='8000');
  

def dist(a,b):
  return ((a.astype(np.int32) - b.astype(np.int32)) ** 2).sum();  

svgFile = None;

def __main__():
  parser = argparse.ArgumentParser(description='Processes images to ascii');
  parser.add_argument('image_path',metavar='image_path',type=str,help='specify path to image');

  image_path = parser.parse_args().image_path;
  image = cv2.imread(image_path);

  global IMG_SIZE;
  IMG_SIZE = image.shape;

  if(image is None):
    print("image not found");
    return ;
 
  global output_image;
  output_image = my_image = np.zeros(image.shape,np.uint8);
  
  log = open(image_path + "_log.csv","w");
  global svgFile;
  svgFile = open(image_path + ".svg","w");
  svgFile.write('<svg>');

  threading.Thread(target=start_server).start();
  for gen in range(0,GENERATIONS):
    log.write("%d, %d\n" % (gen, dist(image,my_image)));
    best = my_image;
    best_dist = dist(image,my_image);
    best_svg = "";
    for attempt in range(0,ATTEMPTS_PER_GENERATION):
      tmp,svg = random_ellipse(my_image);
      tmp_dist = dist(image,tmp);
      if(tmp_dist < best_dist):
        best = tmp;
        best_dist = tmp_dist;
        best_svg = svg;
    global fullSvgString;
    fullSvgString += best_svg;
    if best_svg != "":
      svgFile.write(best_svg + "\n");
    my_image = best;
    output_image = my_image;
    global generation;
    generation = gen;
    if(gen % 1000 == 0):
      cv2.imwrite(image_path + '_generation ' + str(gen) + '.png',my_image);

try:
  __main__();
except KeyboardInterrupt:
  try:
    svgFile.write("</svg>");
  except:
    print("weird...");


