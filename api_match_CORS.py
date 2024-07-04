import os
from flask import Flask, request, jsonify
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from pymongo import MongoClient
import certifi
import json
from flask_cors import CORS  # Importar flask_cors

app = Flask(__name__)
CORS(app)  

# Conexión a MongoDB
mongo_churro = "mongodb+srv://user:password2@cluster0.ygthjln.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_client = MongoClient(
    mongo_churro,
    tls=True,
    tlsAllowInvalidCertificates=True,
    tlsCAFile=certifi.where()
)
db = mongo_client.user
collection = db.ponentes

# Inicializar la aplicación Flask
app = Flask(__name__)
CORS(app)  # Habilitar CORS en la aplicación Flask

# Función para calcular la similitud
def compute_similarity(embedding1, embedding2):
    embedding1 = np.array(embedding1).reshape(1, -1)
    embedding2 = np.array(embedding2).reshape(1, -1)
    return cosine_similarity(embedding1, embedding2)[0][0]

@app.route('/registro_usuarios', methods=['POST'])
def registro_usuarios():
    try:
        data = request.get_json()

        # Extracción de campos del JSON request
        attendee_id = data.get('attendee_id')
        name = data.get('name')
        surname = data.get('surname')
        password = data.get('password')
        company = data.get('company')
        job_title = data.get('job_title')
        email = data.get('email')
        phone = data.get('phone')
        linkedin = data.get('linkedin')
        subtitle = data.get('subtitle', '')
        biography = data.get('biography', '')
        skills = data.get('skills', [])
        interests = data.get('interests', [])

        # Verificar si skills e interests son cadenas y convertir a listas si es necesario
        if isinstance(skills, str):
            skills = json.loads(skills)
        if isinstance(interests, str):
            interests = json.loads(interests)

        # Combinar campos de texto para embedding
        combined_text = f"{subtitle} {biography} {' '.join(skills)}".strip()
        if not combined_text:
            combined_text = ' '.join(interests)

        # Simular generación de embeddings (reemplazar con tu lógica real)
        embeddings = np.random.randn(512).tolist()  # Ejemplo de embeddings aleatorios

        # Crear un diccionario para la nueva fila
        new_data = {
            "attendee_id": attendee_id,
            "name": name,
            "surname": surname,
            "password": password,
            "phone": phone,
            "linkedin": linkedin,
            "interests": interests,
            "company": company,
            "job_title": job_title,
            "email": email,
            "phone": phone,
            "subtitle": subtitle,
            "biography": biography,
            "skills": skills,
            "embeddings": embeddings  # Almacenar embeddings como lista
        }

        # Insertar los nuevos datos en MongoDB
        collection.insert_one(new_data)

        return jsonify({"message": "Usuario registrado exitosamente"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/similarity', methods=['POST'])
def get_similarity():
    try:
        data = request.get_json()

        # Extraer attendee_id de los datos JSON
        worker_id = str(data.get('attendee_id') or data.get('id'))

        # Convertir worker_id a entero para buscar en MongoDB
        worker = collection.find_one({"attendee_id": int(worker_id)})
        if not worker:
            return jsonify({"error": "ID de trabajador no encontrado"}), 404

        # Obtener embeddings del trabajador solicitado y convertir a lista si es necesario
        worker_embedding = worker.get('embeddings')
        if worker_embedding:
            worker_embedding = json.loads(worker_embedding)

        # Calcular similitudes
        similarities = []
        for ponente in collection.find():
            if ponente['attendee_id'] != int(worker_id):
                try:
                    # Obtener embeddings del ponente y convertir a lista si es necesario
                    ponente_embedding = ponente.get('embeddings')
                    if ponente_embedding:
                        ponente_embedding = json.loads(ponente_embedding)

                    # Calcular la similitud
                    similarity = compute_similarity(worker_embedding, ponente_embedding)
                    similarities.append({
                        "_id": ponente['attendee_id'],
                        "name": ponente['nombre'],
                        "similarity": similarity,
                        "interests": ponente['interests'],
                        "job_title": ponente['subtitle'],
                        "ProfilePic": ponente['foto']
                    })
                except Exception as e:
                    return jsonify({"error": f"Error calculando similitud para ponente {ponente['attendee_id']}: {str(e)}"}), 400

        # Ordenar por similitud y devolver los 10 más similares
        similarities = sorted(similarities, key=lambda x: x['similarity'], reverse=True)[:10]

        return jsonify(similarities), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    app.run(debug=True)