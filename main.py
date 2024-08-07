import csv
import requests
from fuzzywuzzy import fuzz
from collections import defaultdict

# Function to load movies from a CSV file
def load_movies(file_path):
  """
  Loads movie data from a CSV file into a list of dictionaries.

  Args: file_path (str): The path to the CSV file containing movie data.

  Returns: A list of dictionaries, where each dictionary represents a movie.
  """

  movies = []
  with open(file_path, 'r', encoding='utf-8-sig') as file:
      csv_reader = csv.DictReader(file)
      for row in csv_reader:
          try:
              # Handle potential conversion errors for year
              row['year'] = int(row['year'])
          except ValueError:
              pass
          # Split genres into a list
          row['genre'] = row['genre'].split(' | ')
          movies.append(row)
  return movies

# Function to handle user search queries
def search(query, movies, history, cache):
  """
  Processes user search queries, including exit, history, displaying cached results,
  performing new searches, and fetching IMDB ratings.

  Args:
      query (str): The user's search query.
      movies (list): The list of loaded movie dictionaries.
      history (list): A list to store user search history.
      cache (defaultdict): A dictionary to cache search results.

  Returns: "exit" if the user enters 'exit', "last" if the user enters 'last', None otherwise.
  """

  if query.lower() == 'exit':
      return "exit"

  if query.lower() == 'last':
      if history:
          print('\nSearch History:\n')
          for results in history:
              for score, movie in results:
                  print(f"{movie['title']}, Director: {movie['director']}, Year: {movie['year']}, Genre: {', '.join(movie['genre'])}, IMDB Rating: {movie.get('imdb_rating', 'N/A')}")
          return "last"
      else:
          print("No previous searches.")
          return None

  if query in cache:
      results = cache[query]
      print("\nResults from cache:\n")
      for score, movie in results:
          print(f"{movie['title']}, Director: {movie['director']}, Year: {movie['year']}, Genre: {', '.join(movie['genre'])}, IMDB Rating: {movie.get('imdb_rating', 'N/A')}")
      return None

  results = perform_search(query, movies)
  fetch_imdb_ratings(results)
  cache[query] = results
  history.append(results)

  print("\nResults:\n")
  for score, movie in results:
      print(f"{movie['title']}, Director: {movie['director']}, Year: {movie['year']}, Genre: {', '.join(movie['genre'])}, IMDB Rating: {movie.get('imdb_rating', 'N/A')}")

# Function to perform movie search based on query terms
def perform_search(query, movies):
  """
  Performs movie search based on user query terms, using exact matches and fuzzy matching.

  Args:
      query (str): The user's search query.
      movies (list): The list of loaded movie dictionaries.

  Returns: A list of tuples containing score and movie dictionary for each matching movie.
  """

  results = []
  query_parts = query.split()

  for movie in movies:
      match_count = 0

      for part in query_parts:
          if ':' in part:
              # Handle field-specific searches (e.g., director:Spielberg)
              field, value = part.split(':')
              # Remove quotes from value if present
              if value.startswith('"') and value.endswith('"'):
                  value = value[1:-1]
              if field in movie and str(movie[field]).lower() == value.lower():
                  match_count += 1
          else:
              # Perform fuzzy matching (partial string matching) on title
              title = movie['title'].lower()
              part = part.lower()
              ratio = fuzz.partial_ratio(part, title)
              if ratio >= 70:
                  match_count += 1

      if match_count > 0:
          score = match_count
          results.append((score, movie))

  results.sort(key=lambda x: x[0], reverse=True)

  return results

def fetch_imdb_ratings(results):
  # Fetches IMDB ratings for search results.
  

  for score, movie in results:
      title = movie['title']
      imdb_rating = get_imdb_rating(title)
      movie['imdb_rating'] = imdb_rating

def get_imdb_rating(title):
  # Retrieves IMDB rating for a given movie title.
  

  url = f"http://www.omdbapi.com/?t={title}&i=tt3896198&apikey=50569543"
  response = requests.get(url)
  if response.status_code == 200:
      data = response.json()
      rating = data.get('imdbRating')
      if rating:
          return float(rating)
  return None

def filter_by_rating(results, min_rating):
  # Filters search results based on minimum IMDB rating.


  filtered_results = [(score, movie) for score, movie in results if movie.get('imdb_rating') and movie['imdb_rating'] >= min_rating]
  filtered_results.sort(key=lambda x: x[0], reverse=True)
  return filtered_results

def main():
  # Main program entry point.
  

  file_path = 'movies.csv'
  movies = load_movies(file_path)
  history = []
  cache = defaultdict(list)

  print("Welcome to Jetflix Movie Search Engine!")

  while True:
      query = input("\nEnter your search terms ('exit' to quit, 'last' to see previous searches): ")
      result = search(query, movies, history, cache)
      if result == "exit":
          break
      elif result == "last":
          continue

  print("\nThank you for using Jetflix Movie Search Engine!")

main()
