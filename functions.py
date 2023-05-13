import numpy as np
import os
import cv2
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Load the cascade
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def get_reference_images(directory = 'images'):
    # Set up a list of reference faces
    reference_faces = []
    reference_labels = []

    # Access the directory that contains all the images folders
    for foldername in os.listdir(directory):
        # Access all the images files in each folder
        for filename in os.listdir(directory + '/' + foldername):
                # Read each face image and store it and its label in the lists
                face_image = cv2.imread(directory + '/' + foldername + '/' + filename, cv2.IMREAD_GRAYSCALE)
                reference_faces.append(face_image)
                reference_labels.append(foldername)

    # Convert the lists to arrays
    reference_faces = np.asarray(reference_faces)
    reference_labels = np.asarray(reference_labels)

    reference_faces_vector = []

    for face in reference_faces:
        reference_faces_vector.append(face.flatten())
    reference_faces_vector = np.asarray(reference_faces_vector).transpose()
    
    return reference_faces,reference_labels,reference_faces_vector


def apply_pca(reference_faces_vector):
    """
    Apply the PCA model to the referecnce faces
    
    ## Parameters 
    face_vector : contain the training images where each column contain one image of size (N^2 * 1)
    
    ## Returns
    weights : vector contain the similarity between each image and eigen vectors

    avg_face_vector : the mean image, used in testing

    eigen_faces : contain eigen vectors, used in testing
    """
    #get the mean image
    avg_face_vector = reference_faces_vector.mean(axis=1)
    avg_face_vector = avg_face_vector.reshape(reference_faces_vector.shape[0], 1)
    #subtract the mean image from the images
    normalized_face_vector = reference_faces_vector - avg_face_vector

    #calculate covariance matrix
    covariance_matrix = np.cov(np.transpose(normalized_face_vector)) 

    #get eigen values and eigen vectors
    eigen_values, eigen_vectors = np.linalg.eig(covariance_matrix)

    #select best k eigen vectors . this variable is changable according to the data set
    k = 30
    index_of_max_k_eigen_values = np.argpartition(eigen_values, -k)[-k:]
    k_eigen_vectors = []

    for i in range(len(index_of_max_k_eigen_values)):
        k_eigen_vectors.append(eigen_vectors[index_of_max_k_eigen_values[i]])

    k_eigen_vectors = np.asarray(k_eigen_vectors)

    eigen_faces = k_eigen_vectors.dot(normalized_face_vector.T)
    weights = (normalized_face_vector.T).dot(eigen_faces.T)

    return weights, avg_face_vector, eigen_faces


def recognize_face(input_img, weights, avg_face_vector, eigen_faces):
    """
    Recognize faces in test image

    ## Parameters
    test_img : image to recognize faces in , it is in gray scale

    weights : the weights resulting from PCA model

    ave_face_vector : average face from the training images

    eigen_faces : eigen vector resulting from PCA model
    
    ## Returns
    index : index of the matched image

    """
    input_img = input_img.reshape(input_img.shape[0] * input_img.shape[1], 1)
    test_normalized_face_vector = input_img - avg_face_vector
    test_weight = (test_normalized_face_vector.T).dot(eigen_faces.T)
    index = np.argmin(np.linalg.norm(test_weight - weights, axis=1))
    return index


def calculate_accuracy(reference_faces, reference_labels):

    # Split the arrays to test & train
    X_train, X_test, y_train, y_test = train_test_split(reference_faces, reference_labels, test_size=0.4, random_state=42)

    reference_faces_vector = []

    # Convert the to be trained images into a vector
    X_train = np.asarray(X_train)
    for image in X_train:
        reference_faces_vector.append(image.flatten())

    reference_faces_vector = np.asarray(reference_faces_vector)
    reference_faces_vector = reference_faces_vector.transpose()

    # Get the weights, eigen vectors and eigen values of the vector
    weights, avg_face_vector, eigen_faces = apply_pca(reference_faces_vector)

    # Recognize faces in test image 
    prediction = []
    for image in X_test:
        index = recognize_face(image, weights, avg_face_vector, eigen_faces) 
        prediction.append(y_train[index])

    prediction = np.asarray(prediction)

    # Calculate the accuracy
    accuracy = accuracy_score(y_test, prediction)

    return accuracy


def detect_faces(input_image,references,pca_parameters):

    gray_input_image = cv2.cvtColor(input_image,cv2.COLOR_BGR2GRAY)

    # Draw a bounding box around the detected face and label it with the closest reference face
    faces_detected = face_cascade.detectMultiScale(gray_input_image, scaleFactor = 1.1, minNeighbors=4)

    font_size = 30
    font_scale = min(input_image.shape[:2]) / (20 * font_size)
    thickness = max(3, int(font_scale))

    if len(faces_detected) > 0:

        for (x, y, w, h) in faces_detected:
            cropped_face_img = gray_input_image[y:y+h, x:x+w]
            resized_cropped_face_img = cv2.resize(cropped_face_img,(250,250))
            closest_idx = recognize_face(resized_cropped_face_img, pca_parameters[0], pca_parameters[1], pca_parameters[2])
            calculated_accuracy = calculate_accuracy(references[0], references[1])*100

            cv2.rectangle(input_image, (x, y), (x+w, y+h), (0, 0, 255), thickness)
            cv2.putText(input_image, f"{references[1][closest_idx]} {calculated_accuracy}%", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 255), thickness)
    return input_image

