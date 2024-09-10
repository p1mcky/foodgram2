# Foodgram

**Foodgram** is a dynamic web service that allows users to create and share their own recipes with a growing community of cooking enthusiasts. Users can explore a variety of recipes, save their favorites for quick access, and stay updated on new content by subscribing to their favorite authors. In addition, the platform offers personalized features like generating downloadable shopping lists based on selected recipes, making it easy for users to plan their meals and grocery trips efficiently. Foodgram aims to foster a community of food lovers, providing them with tools to share, discover, and enjoy culinary creations.

Service available at: [https://pimcky-foodgram.hopto.org/](https://pimcky-foodgram.hopto.org/)

## Key Features

- **Create and edit recipes**: Users can add new recipes or edit their existing ones.
- **Subscriptions**: Subscribe to other users' publications to stay updated.
- **Favorites**: Save recipes to "Favorites" for quick access later.
- **Shopping List**: Generate a shopping list for the ingredients needed to prepare selected recipes (available for download).
- **Tags**: Tag recipes for easy filtering and search.

## Technologies Used

- Python
- Django
- Django REST Framework
- Docker
- PostgreSQL

## How to Run Locally

### 1. Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/lukawoy/foodgram.git
cd backend
```
### 2. Create and activate a virtual environment:
#### For Linux/macOS:
```bash
python3 -m venv env
source env/bin/activate
```
#### For Windows:
```bash
python3 -m venv env
source env/scripts/activate
```
#### 3. Upgrade pip and install dependencies:
```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```
### 4. Configure the Database:
#### Replace the DATABASES dictionary in settings.py with the following to use SQLite:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```
### 5. Apply Migrations:
```bash
python3 manage.py migrate
```
#### 6. Run the Project:
```bash
python3 manage.py runserver
```

### Here are some additional example requests and responses for the Foodgram API.

GET /api/tags/

```json
[
  {
    "id": 1,
    "name": "Завтрак",
    "slug": "breakfast"
  },
  {
    "id": 2,
    "name": "Обед",
    "slug": "lunch"
  },
  {
    "id": 3,
    "name": "Ужин",
    "slug": "dinner"
  }
]
```

POST /api/recipes/
Request:
```json
{
  "ingredients": [
    {
      "id": 1123,
      "amount": 10
    }
  ],
  "tags": [
    1,
    2
  ],
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
  "name": "string",
  "text": "string",
  "cooking_time": 1
}
```
Response:
```json
{
  "id": 0,
  "tags": [
    {
      "id": 0,
      "name": "Завтрак",
      "slug": "breakfast"
    }
  ],
  "author": {
    "email": "user@example.com",
    "id": 0,
    "username": "GSnLRUPQBao_PSNy15Ybeh6@q3JX2Txa8R2LiYq.9x-9hRRz",
    "first_name": "Вася",
    "last_name": "Иванов",
    "is_subscribed": false,
    "avatar": "https://pimcky-foodgram.hopto.org/media/users/image.png"
  },
  "ingredients": [
    {
      "id": 0,
      "name": "Картофель отварной",
      "measurement_unit": "г",
      "amount": 1
    }
  ],
  "is_favorited": true,
  "is_in_shopping_cart": true,
  "name": "string",
  "image": "https://pimcky-foodgram.hopto.org/media/recipes/images/image.png",
  "text": "string",
  "cooking_time": 1
}
```
GET /api/users/subscriptions/
```json
{
  "count": 123,
  "next": "http://foodgram.example.org/api/users/subscriptions/?page=4",
  "previous": "http://foodgram.example.org/api/users/subscriptions/?page=2",
  "results": [
    {
      "email": "user@example.com",
      "id": 0,
      "username": "Ot7O+MKK7rX+i63Hg9PxQYWB.K4YfYdomialfRjL1XvHOkiUyM@yxYe4pcTHt.uCsbzGy7z6SD2Cv9z",
      "first_name": "Вася",
      "last_name": "Иванов",
      "is_subscribed": true,
      "recipes": [
        {
          "id": 0,
          "name": "string",
          "image": "http://foodgram.example.org/media/recipes/images/image.png",
          "cooking_time": 1
        }
      ],
      "recipes_count": 0,
      "avatar": "http://foodgram.example.org/media/users/image.png"
    }
  ]
}
```
### Author
####  Suponin Kirill.