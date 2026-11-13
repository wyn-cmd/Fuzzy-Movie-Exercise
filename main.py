import csv
from collections import defaultdict
from fuzzywuzzy import fuzz
import requests

OMDB_API_KEY = "50569543"
OMDB_BASE_URL = "http://www.omdbapi.com/"

# Load movie data from a CSV file into a list of dictionaries
def load_movies(file_path):
    movies = []
    try:
        with open(file_path, "r", encoding="utf-8-sig") as file:
            for row in csv.DictReader(file):
                try:
                    row["year"] = int(row["year"])
                except (ValueError, TypeError):
                    pass

                row["genre"] = row["genre"].split(" | ") if row.get("genre") else []
                movies.append(row)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
    return movies

# Print formatted movie results to the console
def print_movie_results(results, header="Results"):
    if not results:
        print("\nNo movies found.")
        return

    print(f"\n{header}:\n")
    for score, movie in results:
        genre_str = ", ".join(movie["genre"])
        rating = movie.get("imdb_rating") if movie.get("imdb_rating") is not None else "N/A"
        print(f"{movie['title']}, Director: {movie['director']}, Year: {movie['year']}, Genre: {genre_str}, IMDB Rating: {rating}")

# Retrieve IMDB rating for a specific movie title via API
def get_imdb_rating(title):
    try:
        response = requests.get(
            OMDB_BASE_URL,
            params={"t": title, "apikey": OMDB_API_KEY},
            timeout=5,
        )
        if response.status_code == 200:
            data = response.json()
            rating = data.get("imdbRating")
            return float(rating) if rating and rating != "N/A" else None
    except (requests.RequestException, ValueError):
        pass
    return None

# Populate movie dictionaries in results with IMDB ratings
def fetch_imdb_ratings(results):
    for _, movie in results:
        movie["imdb_rating"] = get_imdb_rating(movie["title"])

# Determine if a search term matches a movie via field-specific or fuzzy title match
def part_matches(part, movie):
    if ":" in part:
        field, value = part.split(":", 1)
        # Strip quotes if the user wrapped the value in them
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        return field in movie and str(movie[field]).lower() == value.lower()
    
    return fuzz.partial_ratio(part.lower(), movie["title"].lower()) >= 70

# Sort movie pairs by match score in descending order
def sort_by_score(results):
    return sorted(results, key=lambda pair: pair[0], reverse=True)

# Search movies based on query terms using exact and fuzzy matching
def perform_search(query, movies):
    results = []
    query_parts = query.split()

    for movie in movies:
        match_count = 0
        for part in query_parts:
            if part_matches(part, movie):
                match_count += 1

        if match_count > 0:
            results.append((match_count, movie))

    return sort_by_score(results)

# Filter search results based on a minimum IMDB rating
def filter_by_rating(results, min_rating):
    filtered = [
        (score, movie)
        for score, movie in results
        if movie.get("imdb_rating") is not None and movie["imdb_rating"] >= min_rating
    ]
    return sort_by_score(filtered)

# Handle search logic including special commands, caching, and history
def search(query, movies, history, cache):
    normalized_query = query.lower().strip()

    if normalized_query == "exit":
        return "exit"

    if normalized_query == "last":
        if not history:
            print("No previous searches.")
        else:
            all_past_results = [res for sublist in history for res in sublist]
            print_movie_results(all_past_results, "Search History")
        return "last"

    if query in cache:
        print_movie_results(cache[query], "Results from cache")
        return None

    results = perform_search(query, movies)
    fetch_imdb_ratings(results)

    cache[query] = results
    history.append(results)

    print_movie_results(results, "Results")
    return None

# Main application loop
def main():
    movies = load_movies("movies.csv")
    if not movies:
        print("No movie data available. Exiting.")
        return

    history = []
    cache = defaultdict(list)

    print("Welcome to Jetflix Movie Search Engine!")

    while True:
        query = input("\nEnter your search terms ('exit' to quit, 'last' to see previous searches): ")
        if not query:
            continue

        if search(query, movies, history, cache) == "exit":
            break

    print("\nThank you for using Jetflix Movie Search Engine!")

if __name__ == "__main__":
    main()