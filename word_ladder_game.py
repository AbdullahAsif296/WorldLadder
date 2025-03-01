import networkx as nx
import heapq
import pygame
import nltk
from nltk.corpus import words
from typing import List, Set, Dict, Tuple, Optional
import string
from collections import deque
import time
import random

class WordLadderGame:
    # Difficulty settings
    DIFFICULTY_SETTINGS = {
        "beginner": {
            "word_length_range": (3, 4),
            "banned_words": set(),
            "time_limit": float('inf'),
            "hint_limit": 5,
            "base_score": 1000,
            "optimal_path_bonus": 300,
            "time_factor": 2,      # Lower time penalty
            "move_factor": 25,     # Lower move penalty
            "hint_factor": 50      # Lower hint penalty
        },
        "advanced": {
            "word_length_range": (5, 6),
            "banned_words": set(),
            "time_limit": 300,  # 5 minutes
            "hint_limit": 3,
            "base_score": 2000,
            "optimal_path_bonus": 500,
            "time_factor": 5,      # Medium time penalty
            "move_factor": 50,     # Medium move penalty
            "hint_factor": 150     # Medium hint penalty
        },
        "challenge": {
            "word_length_range": (6, 8),
            "banned_words": set(),  # Will be populated during game start
            "time_limit": 180,  # 3 minutes
            "hint_limit": 1,
            "base_score": 3000,
            "optimal_path_bonus": 1000,
            "time_factor": 10,     # Higher time penalty
            "move_factor": 100,    # Higher move penalty
            "hint_factor": 300     # Higher hint penalty
        }
    }
    
    def __init__(self):
        # Download required NLTK data if not already downloaded
        try:
            nltk.data.find('corpora/words')
        except LookupError:
            nltk.download('words', quiet=True)
        
        # Initialize word set
        self.word_set = set(word.lower() for word in words.words() 
                           if word.isalpha() and all(c in string.ascii_lowercase for c in word))
        print(f"Loaded {len(self.word_set)} words")
        
        self.graph = nx.Graph()
        self.current_word = ""
        self.target_word = ""
        self.path_history = []
        self.start_time = None
        self.score = 0
        self.difficulty = "beginner"
        self.hints_remaining = float('inf')
        self.time_limit = float('inf')
        self.banned_words = set()
        self.base_score = 1000
        self.hints_used = 0
        
    def get_random_word(self, length: int) -> str:
        """Get a random word of specified length from the word set."""
        # Get all valid words of the specified length
        valid_words = [word for word in self.word_set 
                      if len(word) == length 
                      and word not in self.banned_words
                      and all(c in string.ascii_lowercase for c in word)]
        
        # Print debug info
        print(f"Found {len(valid_words)} valid words of length {length}")
        
        if not valid_words:
            return None
        
        # Return a random word from the valid words
        chosen_word = random.choice(valid_words)
        print(f"Chosen word: {chosen_word}")
        return chosen_word
    
    def setup_difficulty(self, difficulty: str) -> None:
        """Configure game settings based on difficulty level."""
        settings = self.DIFFICULTY_SETTINGS[difficulty]
        self.difficulty = difficulty
        self.hints_remaining = settings["hint_limit"]
        self.time_limit = settings["time_limit"]
        self.base_score = settings["base_score"]
        
        # Initialize scoring factors
        self.optimal_path_bonus = settings["optimal_path_bonus"]
        self.time_factor = settings["time_factor"]
        self.move_factor = settings["move_factor"]
        self.hint_factor = settings["hint_factor"]
        
        # Set up banned words for challenge mode
        if difficulty == "challenge":
            # Randomly select some words to ban
            word_length = random.randint(*settings["word_length_range"])
            potential_words = [w for w in self.word_set if len(w) == word_length]
            self.banned_words = set(random.sample(potential_words, 
                                                min(10, len(potential_words))))
        else:
            self.banned_words = settings["banned_words"]
    
    def is_valid_word(self, word: str) -> bool:
        """Check if a word exists in the dictionary and isn't banned."""
        word = word.lower()
        return (word in self.word_set and 
                word not in self.banned_words)
    
    def get_neighbors(self, word: str) -> Set[str]:
        """Get all possible valid words that differ by one letter."""
        neighbors = set()
        for i in range(len(word)):
            for c in string.ascii_lowercase:
                new_word = word[:i] + c + word[i+1:]
                if (new_word != word and 
                    self.is_valid_word(new_word) and 
                    new_word not in self.banned_words):
                    neighbors.add(new_word)
        return neighbors
    
    def suggest_word_pair(self, difficulty: str) -> Tuple[str, str]:
        """Suggest a valid word pair for the given difficulty."""
        settings = self.DIFFICULTY_SETTINGS[difficulty]
        
        # Set word length based on difficulty
        if difficulty == "beginner":
            word_length = random.randint(3, 4)
        elif difficulty == "advanced":
            word_length = random.randint(5, 6)
        else:  # challenge
            word_length = random.randint(6, 8)
        
        # Get all valid words of the specified length
        valid_words = [word for word in self.word_set 
                      if len(word) == word_length 
                      and word not in self.banned_words
                      and all(c in string.ascii_lowercase for c in word)]
        
        if len(valid_words) < 2:
            return None, None
        
        # Try multiple times to find a valid pair
        max_attempts = 50
        for _ in range(max_attempts):
            start_word = random.choice(valid_words)
            
            # Find potential target words at appropriate distance
            visited = {start_word}
            current_level = {start_word}
            target_distance = (
                random.randint(2, 4) if difficulty == "beginner"
                else random.randint(4, 7) if difficulty == "advanced"
                else random.randint(7, 10)
            )
            
            # BFS to find words at target distance
            for _ in range(target_distance):
                next_level = set()
                for word in current_level:
                    neighbors = self.get_neighbors(word)
                    for neighbor in neighbors:
                        if neighbor not in visited and len(neighbor) == word_length:
                            next_level.add(neighbor)
                            visited.add(neighbor)
                current_level = next_level
                if not current_level:
                    break
            
            # Choose target word from last level
            if current_level:
                potential_targets = [w for w in current_level if w != start_word]
                if potential_targets:
                    target_word = random.choice(potential_targets)
                    # Verify path exists and meets difficulty requirements
                    path = self.a_star_search(start_word, target_word)
                    if path:
                        path_length = len(path) - 1
                        if ((difficulty == "beginner" and 2 <= path_length <= 4) or
                            (difficulty == "advanced" and 4 <= path_length <= 7) or
                            (difficulty == "challenge" and path_length >= 7)):
                            return start_word, target_word
        
        return None, None
    
    def start_game(self, start_word: str, target_word: str, difficulty: str = "beginner") -> bool:
        """Initialize a new game with start and target words."""
        start_word = start_word.lower()
        target_word = target_word.lower()
        
        # Set up difficulty settings
        self.setup_difficulty(difficulty)
        
        if len(start_word) != len(target_word):
            return False
        if not (self.is_valid_word(start_word) and self.is_valid_word(target_word)):
            return False
            
        # Verify the words are appropriate for the chosen difficulty
        path = self.a_star_search(start_word, target_word)
        if not path:
            return False
            
        path_length = len(path) - 1
        if (difficulty == "beginner" and path_length > 4 or
            difficulty == "advanced" and (path_length < 4 or path_length > 7) or
            difficulty == "challenge" and path_length < 7):
            return False
            
        self.current_word = start_word
        self.target_word = target_word
        self.path_history = [start_word]
        self.start_time = time.time()
        self.score = 0
        self.hints_used = 0
        
        # Build graph for words of this length
        self.build_graph(len(start_word))
        
        return True
    
    def get_hint(self, algorithm: str = "a_star") -> Optional[str]:
        """Get the next move using the specified search algorithm.
        
        Args:
            algorithm: The search algorithm to use:
                - 'a_star': A* search (default) - balances path cost and heuristic
                - 'greedy': Greedy Best-First Search - uses only heuristic, faster but not optimal
                - 'uniform': Uniform Cost Search - uses only path cost, optimal but slower
        
        Returns:
            The next word in the optimal path, or None if no hint is available
        """
        if (self.current_word == self.target_word or 
            self.hints_remaining <= 0):
            return None
            
        self.hints_remaining -= 1
        self.hints_used += 1
        
        # Choose the appropriate search algorithm
        if algorithm == "greedy":
            path = self.greedy_best_first_search(self.current_word, self.target_word)
        elif algorithm == "uniform":
            path = self.uniform_cost_search(self.current_word, self.target_word)
        else:  # default to A*
            path = self.a_star_search(self.current_word, self.target_word)
            
        return path[1] if path and len(path) > 1 else None
    
    def calculate_score(self) -> int:
        """Calculate score based on difficulty, moves taken, time taken, and hints used.
        
        The scoring system rewards:
        - Finding the optimal path (or close to it)
        - Completing the puzzle quickly
        - Using fewer hints
        
        Each difficulty level has different weights for these factors.
        """
        time_taken = time.time() - self.start_time
        optimal_path_length = len(self.a_star_search(self.path_history[0], self.target_word)) - 1
        user_path_length = len(self.path_history) - 1
        
        # Get difficulty-specific scoring factors
        settings = self.DIFFICULTY_SETTINGS[self.difficulty]
        base_score = settings["base_score"]
        optimal_path_bonus = settings.get("optimal_path_bonus", 0)
        time_factor = settings.get("time_factor", 5)
        move_factor = settings.get("move_factor", 50)
        hint_factor = settings.get("hint_factor", 100)
        
        # Start with base score
        score = base_score
        
        # Add bonus for finding optimal or near-optimal path
        extra_moves = max(0, user_path_length - optimal_path_length)
        if extra_moves == 0:
            # Perfect path bonus
            score += optimal_path_bonus
        elif extra_moves <= 2:
            # Near-optimal path (partial bonus)
            score += int(optimal_path_bonus * (1 - extra_moves / 5))
        
        # Time component
        if self.time_limit != float('inf'):
            # For timed modes
            time_percentage = time_taken / self.time_limit
            if time_percentage < 0.5:
                # Bonus for finishing in less than half the allowed time
                time_bonus = int((0.5 - time_percentage) * base_score * 0.5)
                score += time_bonus
            elif time_percentage > 0.8:
                # Penalty for taking more than 80% of allowed time
                time_penalty = int((time_percentage - 0.8) * base_score * 0.5)
                score -= time_penalty
        else:
            # For untimed mode (beginner)
            # Mild penalty based on time, capped at 30% of base score
            time_penalty = min(int(time_taken * time_factor), int(base_score * 0.3))
            score -= time_penalty
        
        # Move efficiency component
        if extra_moves > 0:
            # Penalty for extra moves beyond optimal path
            move_penalty = extra_moves * move_factor
            score -= move_penalty
        
        # Hint usage component
        if self.hints_used > 0:
            # Progressive penalty for hints (each hint costs more)
            hint_penalty = 0
            for i in range(1, self.hints_used + 1):
                hint_penalty += hint_factor * i
            score -= hint_penalty
        
        # Ensure score doesn't go negative
        self.score = max(0, score)
        return self.score
    
    def get_time_remaining(self) -> float:
        """Get remaining time in seconds."""
        if self.start_time is None:
            return self.time_limit
        elapsed = time.time() - self.start_time
        return max(0, self.time_limit - elapsed)
    
    def is_game_over(self) -> bool:
        """Check if the game is over (either won or time limit exceeded)."""
        return (self.current_word == self.target_word or 
                self.get_time_remaining() <= 0)
    
    def build_graph(self, word_length: int) -> None:
        """Build a graph of words of specified length."""
        words_of_length = {word for word in self.word_set if len(word) == word_length}
        self.graph.clear()
        self.graph.add_nodes_from(words_of_length)
        
        for word in words_of_length:
            neighbors = self.get_neighbors(word)
            for neighbor in neighbors:
                if neighbor in words_of_length:
                    self.graph.add_edge(word, neighbor)
    
    def heuristic(self, current: str, target: str) -> int:
        """Calculate heuristic value based on letter positions in the alphabet.
        For each letter, its contribution is its position in the alphabet (A=1, B=2, ..., Z=26).
        For example, the heuristic value for "cat" is: C (3) + A (1) + T (20) = 24.
        """
        if len(current) != len(target):
            return float('inf')
        
        # Calculate the sum of letter positions for the current word
        return sum(ord(c.lower()) - ord('a') + 1 for c in current)
    
    def a_star_search(self, start: str, target: str) -> Optional[List[str]]:
        """Perform A* search to find optimal path between start and target words.
        
        A* search uses both the path cost g(n) and a heuristic h(n) to guide the search.
        The total cost function f(n) = g(n) + h(n) is used to prioritize nodes.
        
        Args:
            start: The starting word
            target: The target word
            
        Returns:
            A list representing the optimal path from start to target, or None if no path exists
        """
        if not (self.is_valid_word(start) and self.is_valid_word(target)):
            return None
            
        frontier = [(self.heuristic(start, target), 0, start, [start])]
        visited = {start: 0}
        
        while frontier:
            _, cost, current, path = heapq.heappop(frontier)
            
            if current == target:
                return path
                
            for neighbor in self.get_neighbors(current):
                new_cost = cost + 1
                if neighbor not in visited or new_cost < visited[neighbor]:
                    visited[neighbor] = new_cost
                    priority = new_cost + self.heuristic(neighbor, target)
                    heapq.heappush(frontier, (priority, new_cost, neighbor, path + [neighbor]))
        return None

    def greedy_best_first_search(self, start: str, target: str) -> Optional[List[str]]:
        """Perform Greedy Best-First Search to find a path between start and target words.
        
        Greedy Best-First Search uses only the heuristic h(n) to guide the search,
        ignoring the path cost g(n). This makes it faster but not guaranteed to find
        the optimal solution.
        
        Args:
            start: The starting word
            target: The target word
            
        Returns:
            A list representing a path from start to target, or None if no path exists
        """
        if not (self.is_valid_word(start) and self.is_valid_word(target)):
            return None
            
        frontier = [(self.heuristic(start, target), start, [start])]
        visited = {start}
        
        while frontier:
            _, current, path = heapq.heappop(frontier)
            
            if current == target:
                return path
                
            for neighbor in self.get_neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    priority = self.heuristic(neighbor, target)  # Only heuristic, no path cost
                    heapq.heappush(frontier, (priority, neighbor, path + [neighbor]))
        return None

    def uniform_cost_search(self, start: str, target: str) -> Optional[List[str]]:
        """Perform Uniform Cost Search to find shortest path between start and target words.
        
        Uniform Cost Search uses only the path cost g(n) to guide the search,
        ignoring any heuristic. This guarantees the optimal solution but may
        explore more nodes than A*.
        
        Args:
            start: The starting word
            target: The target word
            
        Returns:
            A list representing the optimal path from start to target, or None if no path exists
        """
        if not (self.is_valid_word(start) and self.is_valid_word(target)):
            return None
            
        frontier = [(0, start, [start])]  # Priority is just the path cost
        visited = {start: 0}
        
        while frontier:
            cost, current, path = heapq.heappop(frontier)
            
            if current == target:
                return path
                
            for neighbor in self.get_neighbors(current):
                new_cost = cost + 1
                if neighbor not in visited or new_cost < visited[neighbor]:
                    visited[neighbor] = new_cost
                    heapq.heappush(frontier, (new_cost, neighbor, path + [neighbor]))
        return None

    def make_move(self, new_word: str) -> bool:
        """Attempt to make a move in the game."""
        new_word = new_word.lower()
        
        if not self.is_valid_word(new_word):
            return False
        if len(new_word) != len(self.current_word):
            return False
        if sum(1 for a, b in zip(new_word, self.current_word) if a != b) != 1:
            return False
            
        self.current_word = new_word
        self.path_history.append(new_word)
        
        if new_word == self.target_word:
            self.calculate_score()
        
        return True

# Example usage
if __name__ == "__main__":
    game = WordLadderGame()
    print("Word Ladder Game - Console Test")
    start = input("Enter start word: ")
    target = input("Enter target word: ")
    
    if game.start_game(start, target):
        print(f"Game started! Transform '{start}' into '{target}'")
        while game.current_word != game.target_word:
            print(f"\nCurrent word: {game.current_word}")
            move = input("Enter your move (or 'hint a_star'/'hint greedy'/'hint uniform' for help): ")
            
            if move.startswith('hint'):
                # Parse the algorithm choice
                parts = move.split()
                algorithm = parts[1] if len(parts) > 1 else "a_star"
                hint = game.get_hint(algorithm)
                if hint:
                    print(f"Hint ({algorithm}): Try '{hint}'")
                else:
                    print("No hint available")
            elif game.make_move(move):
                print("Valid move!")
            else:
                print("Invalid move. Try again.")
        
        print(f"\nCongratulations! You won with a score of {game.score}")
        print(f"Path taken: {' -> '.join(game.path_history)}")
    else:
        print("Invalid start/target word combination.") 