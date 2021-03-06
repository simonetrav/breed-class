# -*- coding: utf-8 -*-
"""breed_clas.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1DrgdevUsDpoi5Z6OGPgCTrvxXnC1UcxY
"""

#file unzippati caricati su google drive
#!unzip '/content/drive/My Drive/breed_class/dog-breed-identification.zip' -d 'drive/My Drive/breed_class'

#importo tensorflow su colab
import tensorflow as tf
import tensorflow_hub as hub
print(tf.__version__)
print(hub.__version__)

print('GPU', 'available yes' if tf.config.list_physical_devices('GPU') else 'not available')

#trasformiamo le immagini in tensori
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import imread
import os

labels_csv = pd.read_csv('/content/drive/My Drive/breed_class/labels.csv')

print(labels_csv.describe())

labels_csv.head()

#quante immagini ci sono di ogni razza?
labels_csv.breed.value_counts().plot.bar(figsize=(20,10))

labels_csv.breed.value_counts().median()

from IPython.display import Image
Image('/content/drive/My Drive/breed_class/train/e36f90b1dd7921dceb536c79989fe69f.jpg')

#creo lista immagini e percorsi

filenames = ['drive/My Drive/breed_class/train/' + fname + '.jpg' for fname in labels_csv['id']]

filenames[:10]

#controllo per vedere se filenames e numero immagini sono coerenti
import os
num_img= os.listdir('drive/My Drive/breed_class/train/')

if  len(num_img) == len(filenames):
  print('tutto ok')
else:
  print(f'non hanno stesso numero, le immagini sono {len(num_img)} mentre filenames è {len(filenames)}')

len(num_img)

Image(filenames[9000])

labels=labels_csv.breed.to_numpy()
labels

# controlliamo se numero labels è uguale a quello di filenames
if len(labels) == len(filenames):
  print('tutto ok')
else:
  print(f'non hanno stesso numero, le labels sono {len(labels)} mentre filenames è {len(filenames)}')

# troviamo valori unici di labels

unique_breeds = np.unique(labels)
len(unique_breeds)

# trasformiamo array categorico in booleano

bool_labels = [label == unique_breeds for label in labels]
len(bool_labels)

#trasformiamo da booleano a intero
num_labels= [label.astype(int) for label in bool_labels]
num_labels

# creiamo un set di validazione e un piccolo batch per addestramento
X = filenames
y = bool_labels

NUM_IMG = 1000 #@param {type:'slider',min:1000,max:10000,step:1000}

from sklearn.model_selection import train_test_split

X_train,X_val,y_train,y_val = train_test_split(X[:NUM_IMG],
                                               y[:NUM_IMG],
                                               test_size=0.2,
                                               random_state=42)
len(X_train),len(X_val)

#preprocessare immagini
image = imread(filenames[42])
image.shape

tf.constant(image)

IMG_SIZE=224
def process_image (image_path, img_size=IMG_SIZE):
  image = tf.io.read_file(image_path)
  image = tf.image.decode_jpeg(image,channels=3)
  image = tf.image.convert_image_dtype(image, tf.float32)
  image = tf.image.resize(image, size=[IMG_SIZE,IMG_SIZE])

  return image

def get_image_label (image_path, label):
  image = process_image(image_path)
  return image,label

(process_image(X[42]), y[42])

get_image_label(X[42],y[42])

BATCH_SIZE = 32
def create_data_batches(X,y=None, batch_size=BATCH_SIZE, valid_data=False, test_data = False):
  if test_data:
    data = tf.data.Dataset.from_tensor_slices((tf.constant(X)))
    data_batch = data.map(process_image).batch(BATCH_SIZE)
    return data_batch
  
  elif valid_data:
    data = tf.data.Dataset.from_tensor_slices((tf.constant(X),
                                               tf.constant(y)))
    data_batch = data.map(get_image_label).batch(BATCH_SIZE)

  else:
    data = tf.data.Dataset.from_tensor_slices((tf.constant(X),
                                               tf.constant(y)))
    data = data.shuffle(buffer_size=len(X))

    data = data.map(get_image_label)

    data_batch = data.batch(BATCH_SIZE)

  return data_batch

train_data = create_data_batches(X_train,y_train)
val_data = create_data_batches(X_val,y_val, valid_data=True)

train_data.element_spec, val_data.element_spec

def show_25_images (images, labels):
  plt.figure(figsize=(10,10))

  for i in range(25):
    ax = plt.subplot(5,5,i+1)
    plt.imshow(images[i])
    plt.title(unique_breeds[labels[i].argmax()])

train_images, train_labels = next(train_data.as_numpy_iterator())
len(train_images), len(train_labels)

show_25_images(train_images,train_labels)

INPUT_SHAPE = [None, IMG_SIZE, IMG_SIZE, 3]
OUTPUT_SHAPE = len(unique_breeds)
MODEL_URL = 'https://tfhub.dev/google/imagenet/mobilenet_v2_130_224/classification/4'

#funzione che crea un modello keras

def create_model (input_shape=INPUT_SHAPE, otuput_shape=OUTPUT_SHAPE, model_url=MODEL_URL):
  print ('il modello è', MODEL_URL)
  model = tf.keras.Sequential([
                               hub.KerasLayer(MODEL_URL),
                               tf.keras.layers.Dense(units=OUTPUT_SHAPE,
                                                     activation='softmax'),
  ])
  model.compile(
      loss=tf.keras.losses.CategoricalCrossentropy(),
      optimizer = tf.keras.optimizers.Adam(),
      metrics=['accuracy']
  )
  model.build(INPUT_SHAPE)
  return model

model = create_model()
model.summary()

# Commented out IPython magic to ensure Python compatibility.
#creiamo dei callabcks
# %load_ext tensorboard

import datetime

#creiamo funzione per fare tensorboard callback

def create_tf_callback ():
  logdir = os.path.join('/content/drive/My Drive/breed_class/logs',
                        datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
  return tf.keras.callbacks.TensorBoard(logdir)

early_stopping = tf.keras.callbacks.EarlyStopping(monitor='val_accuracy',
                                                  patience = 3)

#addestriamo il modello
NUM_EPOCHS=100 #@param {type:'slider', min:10, max:1000}

#funzione epr addestrare modello

def train_model ():
  
  model = create_model()
  tensorboard = create_tf_callback()
  model.fit(x=train_data,
            epochs=NUM_EPOCHS,
            validation_data = val_data,
            validation_freq = 1,
            callbacks = [tensorboard,early_stopping])
  return model

#model = train_model()
model = tf.keras.models.load_model('/content/drive/My Drive/breed_class/models/20200505-09251588670716-1000-images-Adam.h5',
                                      custom_objects={'KerasLayer':hub.KerasLayer})

# Commented out IPython magic to ensure Python compatibility.
# controlliamo i log di tensorboard

# %tensorboard --logdir /content/drive/My\ Drive/breed_class/logs

predictions = model.predict(val_data, verbose=0)
predictions

def predict_label (prediction_probabilities):

  return unique_breeds[np.argmax(prediction_probabilities)]

pred_label = predict_label (predictions[77])
pred_label

#val_data è in batch, dobbiamo spacchettarlo
def unbatchify (data):
  images_ = []
  labels_ = []
  for i,l in data.unbatch().as_numpy_iterator():
    images_.append(i)
    labels_.append(unique_breeds[np.argmax(l)])
  return images_, labels_

val_images, val_labels = unbatchify(val_data)
val_images[0],val_labels[0]

val_labels[77]

val_images[1]

def plot_pred (prediction_probabilities, labels, images, n=1):

  pred_prob, true_label, image = prediction_probabilities[n], labels[n], images[n]

  pred_label = predict_label(pred_prob)

  plt.imshow(image)
  plt.xticks([])
  plt.yticks([])

  if pred_label == true_label:
    color= 'green'
  else:
    color='red'

  plt.title ('{} {:2.0f}% {}'.format(pred_label, 
                                     np.max(pred_prob)*100, 
                                     true_label),
             color=color)

plot_pred(prediction_probabilities=predictions,
          labels=val_labels,
          images=val_images,
          n=77)

#funzione per visualizzare le prime 10 classi predette
def plot_pred_conf (prediction_probabilities, labels, n=1):
  pred_prob, true_label = prediction_probabilities[n], labels[n]

  pred_label = predict_label(pred_prob)

  top_10_pred_ind = pred_prob.argsort()[-10:][::-1]

  top_10_pred_val = pred_prob[top_10_pred_ind]

  top_10_pred_labels = unique_breeds[top_10_pred_ind]

  top_plot = plt.bar(np.arange(len(top_10_pred_labels)),
                      top_10_pred_val,
                      color='grey')
  plt.xticks(np.arange(len(top_10_pred_labels)),
             labels=top_10_pred_labels,
             rotation='vertical')
  
  if np.isin(true_label, top_10_pred_labels):
    top_plot[np.argmax(top_10_pred_labels==true_label)].set_color('green')
  else:
    pass

plot_pred_conf(prediction_probabilities=predictions,
               labels=val_labels, 
               n=9)

i_multiplier = 10
num_rows = 3
num_cols = 2
num_images = num_rows*num_cols
plt.figure(figsize=(10*num_cols, 5*num_rows))

for i in range(num_images):
  plt.subplot(num_rows, 2*num_cols, 2*i+1)
  plot_pred(prediction_probabilities=predictions,
            labels= val_labels,
            images=val_images,
            n=i+i_multiplier)
  plt.subplot(num_rows, 2*num_cols, 2*i+2)
  plot_pred_conf(prediction_probabilities=predictions,
            labels= val_labels,
            n=i+i_multiplier)
  
plt.tight_layout(h_pad=1.0)
plt.show()

def conf_matr (num_clas,predictions,gr_tr):
  matrix= np.zeros((num_clas,num_clas))
  preds=[predict_label(predictions[i]) for i in range(len(predictions))]

  for i in range(len(preds)):
    if preds[i] == gr_tr[i]:
      index=unique_breeds.tolist().index(preds[i])
      matrix[index,index]+=1
    else:
      index2=unique_breeds.tolist().index(preds[i])
      index3=unique_breeds.tolist().index(gr_tr[i])
      matrix[index2,index3]+=1

  return pd.DataFrame(matrix)

conf_matr(120,predictions,val_labels)

def save_model (model, suffix=None):
  modeldir = os.path.join(r'/content/drive/My Drive/breed_class/models', datetime.datetime.now().strftime('%Y%m%d-%H%M%s'))
  model_path = modeldir + '-' + suffix + '.h5'
  model.save(model_path)
  return model_path

def load_model (model_path):

  model = tf.keras.models.load_model(model_path,
                                      custom_objects={'KerasLayer':hub.KerasLayer})
  return model

save_model(model, suffix='1000-images-Adam')

loaded_model = load_model('/content/drive/My Drive/breed_class/models/20200505-09251588670716-1000-images-Adam.h5')

model.evaluate(val_data)

loaded_model.evaluate(val_data)

#addestriamo il modello su tutto il dataset
full_data = create_data_batches(X,y)

full_data

full_model = create_model()

# aggiungiamo dei callbacks
full_model_tensorboard = create_tf_callback()

full_model_early_stopping = tf.keras.callbacks.EarlyStopping(monitor='accuracy',
                                                            patience=3)

full_model.fit(x=full_data,
               epochs=NUM_EPOCHS,
               callbacks=[full_model_tensorboard,
                          full_model_early_stopping])

save_model(full_model, suffix='full_images')

loaded_full_model = load_model('/content/drive/My Drive/breed_class/models/20200505-11331588678400-full_images.h5')

#predire sul dataset di test
test_path = '/content/drive/My Drive/breed_class/test/'
test_filenames = [test_path + fname for fname in os.listdir(test_path)]

len(test_filenames)

test_data = create_data_batches(test_filenames, test_data=True)

test_data

test_predicitons = loaded_full_model.predict(test_data, verbose = 1)

np.savetxt('drive/My Drive/breed_class/preds_array.csv',test_predicitons, delimiter=',')

test_predictions = np.loadtxt ('drive/My Drive/breed_class/preds_array.csv', delimiter = ',')

test_predictions.shape

#prepariamo il file per caricarlo su kaggle
preds_df = pd.DataFrame(columns=['id'] + list(unique_breeds))

test_ids = [os.path.splitext(path)[0] for path in os.listdir(test_path)]

preds_df['id']= test_ids

preds_df[list(unique_breeds)] = test_predictions

preds_df.to_csv('drive/My Drive/breed_class/submission_1.csv', index = False)

# come funziona il modello con altre foto
custom_path = 'drive/My Drive/breed_class/custom_photos/'
custom_image_paths = [custom_path + fname for fname in os.listdir(custom_path)]

custom_data = create_data_batches(custom_image_paths, test_data=True)

custom_preds = loaded_full_model.predict(custom_data)

custom_preds_label = [predict_label(custom_preds[i]) for i in range(len(custom_preds))]

custom_preds_label

custom_images = []
for image in custom_data.unbatch().as_numpy_iterator():
  custom_images.append(image)

plt.figure(figsize=(10,10))
for i, im in enumerate(custom_images):
  plt.subplot(1,4, i+1)
  plt.xticks([])
  plt.yticks([])
  plt.title(custom_preds_label[i])
  plt.imshow(im)

